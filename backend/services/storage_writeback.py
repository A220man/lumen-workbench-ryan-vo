"""Storage image write-back cache conflict and page granularity diagnostics.
Models GPU storage texture write-back cache in AnyPS5 agc-driver,
specifically false-positive StoredOver conflicts on 64 KiB edge blocks discarding
GPU SDF font atlas results for Silksong PPSA12544 (issue #865).
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict,List,Optional,Tuple
import json

@dataclass
class CPUWriteEvent:
    address:int;size_bytes:int;generation:int;description:str

@dataclass
class StorageWritebackConfig:
    title_id:str="PPSA12544";title_name:str="Hollow Knight: Silksong (Unity TextCore)"
    texture_address:int=0x25E042000;texture_size:int=0x40000;block_size:int=65536
    page_size:int=4096;gpu_dispatch_generation:int=87617

@dataclass
class UnitDiagnostic:
    unit_id:str;guest_start:int;guest_end:int;offset_in_texture:int;size_bytes:int
    is_edge_block:bool;block_index:int;gpu_generation:int;cpu_block_stamp:int
    block_policy_stored_over:bool;page_policy_stored_over:bool;edge_reason:Optional[str]=None

@dataclass
class StorageWritebackReport:
    title_id:str;title_name:str;texture_address:int;texture_size:int;block_size:int
    page_size:int;alignment_offset:int;total_blocks_spanned:int;total_pages_spanned:int
    edge_blocks_count:int;units:List[UnitDiagnostic];block_policy_corrupted:bool
    block_policy_dropped_units:List[str];page_policy_corrupted:bool
    page_policy_dropped_units:List[str];eager_writeback_corrupted:bool
    corrupted_glyphs:List[str];warning_logged:Optional[str];root_cause:str
    recommendation:str;status:str

def _load_silksong_preset()->Tuple[StorageWritebackConfig,List[CPUWriteEvent]]:
    data_path=Path(__file__).parent.parent/"data"/"storage_writeback_preset.json"
    with data_path.open()as f:data=json.load(f)
    cfg_data=data["silksong_config"]
    cfg=StorageWritebackConfig(title_id=cfg_data["title_id"],title_name=cfg_data["title_name"],texture_address=cfg_data["texture_address"],texture_size=cfg_data["texture_size"],block_size=cfg_data["block_size"],page_size=cfg_data["page_size"],gpu_dispatch_generation=cfg_data["gpu_dispatch_generation"])
    writes=[CPUWriteEvent(**w)for w in data["cpu_writes"]]
    return cfg,writes

SILKSONG_CONFIG,SILKSONG_WRITES=_load_silksong_preset()

class StorageWritebackAnalyzer:
    """Analyzes and simulates GPU storage image write-back conflict policies."""

    @classmethod
    def get_silksong_preset(cls)->Tuple[StorageWritebackConfig,List[CPUWriteEvent]]:return SILKSONG_CONFIG,SILKSONG_WRITES

    def analyze(self,config:Optional[StorageWritebackConfig]=None,cpu_writes:Optional[List[CPUWriteEvent]]=None)->StorageWritebackReport:
        cfg=config or SILKSONG_CONFIG
        writes=cpu_writes if cpu_writes is not None else[]
        ts,tsz=cfg.texture_address,cfg.texture_size
        te,off=ts+tsz,ts%cfg.block_size
        fb,lb=ts-off,((te-1)//cfg.block_size)*cfg.block_size
        n_blks,n_pgs=((lb-fb)//cfg.block_size)+1,tsz//cfg.page_size

        bstamps:Dict[int,int]={}
        pstamps:Dict[int,int]={}
        for w in writes:
            we=w.address+w.size_bytes
            cb=(w.address//cfg.block_size)*cfg.block_size
            while cb<we:
                idx=(cb-fb)//cfg.block_size
                bstamps[idx]=max(bstamps.get(idx,0),w.generation)
                cb+=cfg.block_size
            cp=(w.address//cfg.page_size)*cfg.page_size
            while cp<we:
                pstamps[cp]=max(pstamps.get(cp,0),w.generation)
                cp+=cfg.page_size

        units,b_drop,p_drop,edges,cur=[],[],[],0,ts
        for bi in range(n_blks):
            bs,be=fb+bi*cfg.block_size,fb+(bi+1)*cfg.block_size
            us,ue=max(cur,bs),min(te,be)
            if us>=ue:continue
            usz=ue-us
            is_edge=(usz<cfg.block_size)or(us!=bs)or(ue!=be)
            if is_edge:edges+=1
            reason=(f"Head edge (+0x0..+0x{usz:x})"if bi==0 else f"Tail edge (+0x{us-ts:x}..+0x{tsz:x})")if is_edge else None
            b_gen=bstamps.get(bi,0)
            b_over=b_gen>cfg.gpu_dispatch_generation
            p_over=any(pstamps.get(p,0)>cfg.gpu_dispatch_generation for p in range(us,ue,cfg.page_size))
            uid=f"block_{bi}_{'edge' if is_edge else 'full'}_+0x{us-ts:x}"
            if b_over:b_drop.append(uid)
            if p_over:p_drop.append(uid)
            units.append(UnitDiagnostic(uid,us,ue,us-ts,usz,is_edge,bi,cfg.gpu_dispatch_generation,b_gen,b_over,p_over,reason))
            cur=ue

        b_cor=bool(b_drop)
        warn=f"[gpu] storage image 0x{ts:x}+0x{tsz:x}: guest memory changed while GPU results were pending; keeping the CPU's blocks"if b_cor else None
        return StorageWritebackReport(cfg.title_id,cfg.title_name,ts,tsz,cfg.block_size,cfg.page_size,off,n_blks,n_pgs,edges,units,b_cor,b_drop,bool(p_drop),p_drop,False,["OPTIONS_O","GAME_MARK"]if b_cor else[],warn,"64 KiB block granularity falsely treats adjacent non-overlapping CPU writes as stored-over"if b_cor else"clean","Adopt 4 KiB page granularity for StoredOver tracking, or enable APS5_EAGER_WRITEBACK=1","conflict_detected"if b_cor else"clean")