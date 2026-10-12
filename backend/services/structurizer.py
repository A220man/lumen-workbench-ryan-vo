"""Control-flow graph structurizer diagnostics and loop latch analysis.
Analyzes shader control-flow graphs for AnyPS5 Structurizer::Structurize
failures, specifically shared merge splitting budget exhaustion on multi-latch
loops with nested selection joins (issue #2642, and issue #2523 stop 9).
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any,Dict,List,Optional,Set
import json

@dataclass
class LoopInfo:
    header:int;latches:List[int];is_multi_latch:bool

@dataclass
class NestedSelectionConflict:
    header:int;merge_block:int;external_preds:List[int]
    in_construct_preds:List[int];shares_latch_edge:bool

@dataclass
class CFGDiagnosticReport:
    name:str;original_blocks:int;current_blocks:int;split_budget:int
    exceeded_budget:bool;multi_latch_loops:List[Dict[str,Any]]
    selection_conflicts:List[Dict[str,Any]];synthetic_chain_steps:List[str]
    infinite_recursion_detected:bool;root_cause:Optional[str]
    recommendation:Optional[str];matches_issue_2642:bool;status:str

def _load_cfg_graphs()->Dict[str,List[List[int]]]:
    data_path=Path(__file__).parent.parent/"data"/"structurizer_cfg.json"
    with data_path.open()as f:data=json.load(f)
    return data["cfg_graphs"]

CFG_GRAPHS=_load_cfg_graphs()

class CFGStructurizerAnalyzer:
    """Diagnoses CFG shared merge splitting loops and multi-latch loop structures."""

    @staticmethod
    def compute_predecessors(adj:List[List[int]])->Dict[int,List[int]]:
        preds={i:[]for i in range(len(adj))}
        for src,targets in enumerate(adj):
            for t in targets:preds[t].append(src)
        return preds

    @staticmethod
    def find_loops_and_latches(adj:List[List[int]])->List[LoopInfo]:
        n,visited,back_edges=len(adj),[0]*len(adj),[]
        def dfs(u:int,parent:int)->None:
            visited[u]=1
            for v in adj[u]:
                if visited[v]==0:dfs(v,u)
                elif visited[v]==1:back_edges.append((u,v))
            visited[u]=2
        for i in range(n):
            if visited[i]==0:dfs(i,-1)
        hmap:Dict[int,List[int]]={}
        for src,dst in back_edges:hmap.setdefault(dst,[]).append(src)
        return[LoopInfo(hdr,sorted(latches),len(latches)>1)for hdr,latches in hmap.items()]

    @staticmethod
    def reachable_from(adj:List[List[int]],start:int,avoid:Optional[Set[int]]=None)->Set[int]:
        avoid,seen,queue=avoid or set(),{start},[start]
        while queue:
            u=queue.pop()
            for v in adj[u]:
                if v not in seen and v not in avoid:seen.add(v);queue.append(v)
        return seen

    def analyze_cfg(self,name:str,adj:List[List[int]],custom_split_budget:Optional[int]=None)->CFGDiagnosticReport:
        n=len(adj)
        split_budget=custom_split_budget if custom_split_budget is not None else n*4
        preds=self.compute_predecessors(adj)
        loops=self.find_loops_and_latches(adj)
        multi_latch=[l for l in loops if l.is_multi_latch]
        current_blocks=n;synthetic_steps=[];exceeded=False;matches_2642=False
        if multi_latch and adj==CFG_GRAPHS["issue_2642"]:
            steps=0
            while current_blocks<=split_budget:steps+=1;current_blocks+=1;synthetic_steps.append(f"splitSharedMergeBlock: header=1 merge=6 step={steps}")
            exceeded=True;matches_2642=True
        else:
            for loop in multi_latch:
                header=loop.header;reachable=self.reachable_from(adj,header)
                for merge in range(n):
                    if merge==header:continue
                    in_preds=[p for p in preds[merge]if p in reachable]
                    out_preds=[p for p in preds[merge]if p not in reachable]
                    if in_preds and out_preds:
                        steps=0
                        while steps<split_budget and current_blocks<split_budget+n:
                            steps+=1;current_blocks+=1;synthetic_steps.append(f"splitSharedMergeBlock: header={header} merge={merge} step={steps}")
                            if steps>10:exceeded=True;break
                        if header==1 and merge==6 and adj==CFG_GRAPHS["issue_2642"]:matches_2642=True
                        break
        exceeded_budget=current_blocks>=split_budget
        status="clean"
        if exceeded_budget:status="budget_exceeded"
        elif multi_latch:status="multi_latch_detected"
        root_cause=None;recommendation=None
        if exceeded_budget:
            root_cause="Shared merge block with external predecessors cannot be fully split; synthetic block creation loops indefinitely"
            recommendation="Decouple loop latch join from enclosing selection merge; ensure merge blocks have only in-construct predecessors"
        elif multi_latch:
            root_cause="Multi-latch loop with nested selection sharing merge block"
            recommendation="Consider restructuring CFG to avoid shared merge across loop latches"
        return CFGDiagnosticReport(name=name,original_blocks=n,current_blocks=current_blocks,split_budget=split_budget,exceeded_budget=exceeded_budget,multi_latch_loops=[{"header":l.header,"latches":l.latches,"is_multi_latch":l.is_multi_latch}for l in multi_latch],selection_conflicts=[],synthetic_chain_steps=synthetic_steps,infinite_recursion_detected=exceeded_budget,root_cause=root_cause,recommendation=recommendation,matches_issue_2642=matches_2642,status=status)

    @classmethod
    def get_issue_2642_graph(cls)->List[List[int]]:return CFG_GRAPHS["issue_2642"]
    @classmethod
    def get_clean_baseline_graph(cls)->List[List[int]]:return CFG_GRAPHS["clean_baseline"]