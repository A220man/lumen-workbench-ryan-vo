"""API route definitions for lumen-workbench-ryan-vo."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...core.nid import nid_of
from ...models.title import Title
from ...models.evaluation import Evaluation
from ...models.import_record import ImportRecord
from ...models.audit import AuditLog
from ...schemas.title import TitleCreate, TitleUpdate, TitleResponse
from ...schemas.evaluation import EvaluationResponse
from ...services.import_resolver import ImportResolver
from ...services.evaluator import run_evaluation as run_eval_metrics
from ...services.advisory import build_advisor, explain_imports
from ...services.adversarial import AdversarialGenerator, run_stress_test
from ...services.shader_analyzer import RDNA2ShaderAnalyzer, IRInstruction, RDNA2_ANCILLARY_LAYOUT
from ...services.structurizer import CFGStructurizerAnalyzer
from ...services.storage_writeback import StorageWritebackAnalyzer, StorageWritebackConfig, CPUWriteEvent
from .auth import get_current_user, require_role

router = APIRouter(tags=["API"])
resolver_singleton = ImportResolver()
adversarial_generator_singleton = AdversarialGenerator()
shader_analyzer_singleton = RDNA2ShaderAnalyzer()
structurizer_analyzer_singleton = CFGStructurizerAnalyzer()
storage_writeback_analyzer_singleton = StorageWritebackAnalyzer()

class RunEvaluationRequest(BaseModel):
    title_name: Optional[str] = None; title_id: Optional[int] = None

class ResolvedImportItem(BaseModel):
    name: str; nid: int; library: Optional[str] = None; status: str

class ResolutionReportResponse(BaseModel):
    source_name: str; needed_libraries: List[str]; imports: List[ResolvedImportItem]; resolved_count: int; unresolved_count: int; missing_module_count: int; coverage: float; score: int; blockers: List[str]; advisory: Optional[str] = None

@router.get("/titles", response_model=List[TitleResponse])
async def list_titles(search: Optional[str] = None, status: Optional[str] = None, page: int = 1, page_size: int = 20, db: Session = Depends(get_db), user: Dict[str, Any] = Depends(get_current_user)):
    q = select(Title)
    if search: q = q.where(Title.name.ilike(f"%{search}%"))
    if status: q = q.where(Title.status == status)
    return [TitleResponse.model_validate(t) for t in db.execute(q.offset((page - 1) * page_size).limit(page_size)).scalars().all()]

@router.get("/titles/{title_id}", response_model=TitleResponse)
async def get_title(title_id: int, db: Session = Depends(get_db), user: Dict[str, Any] = Depends(get_current_user)):
    if not (t := db.get(Title, title_id)): raise HTTPException(404, "Title not found")
    return TitleResponse.model_validate(t)

@router.post("/titles", response_model=TitleResponse, status_code=201)
async def create_title(data: TitleCreate, db: Session = Depends(get_db), user: Dict[str, Any] = Depends(require_role(["operator", "admin"]))):
    t = Title(**data.model_dump()); db.add(t)
    db.add(AuditLog(action="create_title", entity_type="title", details=f"Title created: {data.name} by {user.get('email')}"))
    db.commit(); db.refresh(t); return TitleResponse.model_validate(t)

@router.put("/titles/{title_id}", response_model=TitleResponse)
async def update_title(title_id: int, data: TitleUpdate, db: Session = Depends(get_db), user: Dict[str, Any] = Depends(require_role(["operator", "admin"]))):
    if not (t := db.get(Title, title_id)): raise HTTPException(404, "Title not found")
    for f, v in data.model_dump(exclude_unset=True).items(): setattr(t, f, v)
    db.add(AuditLog(action="update_title", entity_type="title", entity_id=title_id, details=f"Title updated by {user.get('email')}"))
    db.commit(); db.refresh(t); return TitleResponse.model_validate(t)

@router.delete("/titles/{title_id}", status_code=204)
async def delete_title(title_id: int, db: Session = Depends(get_db), user: Dict[str, Any] = Depends(require_role(["admin"]))):
    if not (t := db.get(Title, title_id)): raise HTTPException(404, "Title not found")
    db.add(AuditLog(action="delete_title", entity_type="title", entity_id=title_id, details=f"Title deleted by {user.get('email')}"))
    db.delete(t); db.commit(); return None

@router.post("/imports/analyze", response_model=ResolutionReportResponse)
async def analyze_imports(file: UploadFile = File(...), explain: bool = False, db: Session = Depends(get_db), user: Dict[str, Any] = Depends(get_current_user)):
    content = await file.read()
    if not content: raise HTTPException(400, "Empty file uploaded")
    rep = resolver_singleton.analyze_bytes(content, source_name=file.filename or "upload.elf")
    adv = await explain_imports(rep, build_advisor()) if explain else None
    rec = ImportRecord(title_name=file.filename or "unknown.elf", status="complete" if rep.score >= 50 else "needs_stubs", analyzed_by=user.get("email"), analysis_result=f"score={rep.score}, coverage={rep.coverage:.2f}, resolved={rep.resolved_count}")
    db.add(rec); db.commit()
    return ResolutionReportResponse(source_name=rep.source_name, needed_libraries=rep.needed_libraries, imports=[ResolvedImportItem(name=i.name, nid=i.nid, library=i.library, status=i.status) for i in rep.imports], resolved_count=rep.resolved_count, unresolved_count=rep.unresolved_count, missing_module_count=rep.missing_module_count, coverage=rep.coverage, score=rep.score, blockers=rep.blockers, advisory=adv)

@router.get("/evaluations", response_model=List[EvaluationResponse])
async def list_evaluations(db: Session = Depends(get_db), user: Dict[str, Any] = Depends(get_current_user)):
    return [EvaluationResponse.model_validate(e) for e in db.execute(select(Evaluation)).scalars().all()]

@router.post("/evaluations/run")
async def run_evaluation_endpoint(req: RunEvaluationRequest, db: Session = Depends(get_db), user: Dict[str, Any] = Depends(require_role(["operator", "admin"]))):
    m = run_eval_metrics(resolver_singleton)
    if req.title_id and (t := db.get(Title, req.title_id)):
        db.add(Evaluation(title_id=t.id, score=round(m.f1 * 10, 2), comments=f"F1={m.f1:.3f}, Precision={m.precision:.3f}, Recall={m.recall:.3f}"))
        db.commit()
    return {"status": "success", **m.__dict__}

@router.post("/adversarial/generate")
async def generate_adversarial_spec(prefix: Optional[str] = None, category: Optional[str] = None, count: int = 5, user: Dict[str, Any] = Depends(require_role(["operator", "admin"]))):
    if prefix:
        items = [{"name": f"{prefix}_adversarial_sym_{i}", "nid": nid_of(f"{prefix}_adversarial_sym_{i}"), "predicted_status": "unresolved" if not resolver_singleton.resolve_name(f"{prefix}_adversarial_sym_{i}") else "resolved", "category": category or "prefix_boundary"} for i in range(min(max(count, 1), 50))]
    else:
        items = [{"name": c.symbol, "nid": c.nid, "predicted_status": c.expected_status, "category": c.category, "mutation_type": c.mutation_type} for c in adversarial_generator_singleton.generate_cases(category=category, count=count)]
    return {"generated_count": len(items), "symbols": items}

@router.post("/adversarial/stress-test")
async def run_adversarial_stress_test(category: Optional[str] = None, user: Dict[str, Any] = Depends(require_role(["operator", "admin"]))):
    rep = run_stress_test(resolver_singleton, custom_cases=adversarial_generator_singleton.generate_cases(category=category, count=50))
    return {"status": "success", **rep.__dict__}

@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db), user: Dict[str, Any] = Depends(get_current_user)):
    active = db.execute(select(func.count(Title.id)).where(Title.status == "active")).scalar() or 0
    total = db.execute(select(func.count(ImportRecord.id))).scalar() or 0
    evals = db.execute(select(func.count(Evaluation.id))).scalar() or 0
    m = run_eval_metrics(resolver_singleton)
    return {"active_titles": active, "total_imports": total, "resolution_rate": f"{m.coverage * 100:.1f}%", "evaluation_count": evals}

@router.get("/analytics")
async def get_analytics(db: Session = Depends(get_db), user: Dict[str, Any] = Depends(get_current_user)):
    m = run_eval_metrics(resolver_singleton)
    stress = run_stress_test(resolver_singleton)
    stray = shader_analyzer_singleton.get_stray_catalog_shaders()
    cfg = structurizer_analyzer_singleton.analyze_cfg("issue_2642_repro", structurizer_analyzer_singleton.get_issue_2642_graph())
    swb = storage_writeback_analyzer_singleton.analyze()
    top_lib = max(m.per_library.items(), key=lambda x: x[1].get("tp", 0))[0] if m.per_library else "libkernel"
    total = db.execute(select(func.count(ImportRecord.id))).scalar() or 0
    return {
        "resolution_by_library": f"Lead module: {top_lib} ({m.per_library.get(top_lib, {}).get('tp', 0)} symbols)",
        "performance_trend": f"F1={m.f1:.3f} (coverage {m.coverage * 100:.1f}%)",
        "import_volume": f"{total} records analyzed",
        "per_library": m.per_library,
        "metrics": {"precision": round(m.precision, 4), "recall": round(m.recall, 4), "f1": round(m.f1, 4), "coverage": round(m.coverage, 4), "stability_score": round(stress.stability_score, 2)},
        "adversarial_stability": f"{stress.stability_score:.1f}% stability ({stress.passed_cases}/{stress.total_cases} boundary probes)",
        "shader_diagnostics": f"{sum(1 for s in stray if s.status == 'rejected_unsupported_live_use')}/{len(stray)} Stray UE4 shaders deferred (issue #2548 unsupported live use)",
        "structurizer_diagnostics": f"Issue #2642 repro: {cfg.status} ({cfg.current_blocks}/{cfg.original_blocks} blocks, budget {cfg.split_budget})",
        "storage_writeback_diagnostics": f"Silksong (issue #865): {swb.status} ({len(swb.block_policy_dropped_units)} 64K edge drops vs 0 at 4K page granularity)",
    }

class ShaderAnalyzeInstruction(BaseModel):
    index: int; opcode: str; dest: Optional[str] = None; sources: List[str] = []; bit_offset: Optional[int] = None; bit_length: Optional[int] = None; condition: Optional[str] = None

class ShaderAnalyzeRequest(BaseModel):
    shader_address: str = "0x200e370000"; title_id: str = "PPSA02100"; ancillary_vgpr: str = "v4"; instructions: Optional[List[ShaderAnalyzeInstruction]] = None; raw_word: Optional[int] = None

@router.get("/shaders/rdna2-layout")
async def get_rdna2_layout(user: Dict[str, Any] = Depends(get_current_user)):
    return [b.__dict__ for b in RDNA2_ANCILLARY_LAYOUT]

@router.post("/shaders/analyze")
async def analyze_shader(payload: ShaderAnalyzeRequest, user: Dict[str, Any] = Depends(require_role(["operator", "admin"]))):
    insts = [IRInstruction(i.index, i.opcode, i.dest, i.sources, i.bit_offset, i.bit_length, i.condition) for i in (payload.instructions or [])]
    rep = shader_analyzer_singleton.analyze_ir_stream(payload.shader_address, payload.title_id, insts, payload.ancillary_vgpr)
    res = rep.__dict__.copy()
    res["decoded_word"] = shader_analyzer_singleton.decode_word(payload.raw_word) if payload.raw_word is not None else None
    return res

@router.get("/shaders/stray-batch")
async def get_stray_shaders_batch(user: Dict[str, Any] = Depends(get_current_user)):
    return [r.__dict__ for r in shader_analyzer_singleton.get_stray_catalog_shaders()]

class CFGAnalyzeRequest(BaseModel):
    name: str = "custom_cfg"; adjacency: List[List[int]]; split_budget: Optional[int] = None

@router.post("/structurizer/analyze")
async def analyze_cfg(payload: CFGAnalyzeRequest, user: Dict[str, Any] = Depends(require_role(["operator", "admin"]))):
    return structurizer_analyzer_singleton.analyze_cfg(payload.name, payload.adjacency, payload.split_budget).__dict__

@router.get("/structurizer/presets")
async def get_structurizer_presets(user: Dict[str, Any] = Depends(get_current_user)):
    return [
        {"id": "issue-2642-repro", "name": "Issue #2642 Minimal Reproduction", "description": "Two-latch loop with nested selections sharing join block 4", "adjacency": structurizer_analyzer_singleton.get_issue_2642_graph(), "expected_status": "budget_exceeded"},
        {"id": "clean-baseline", "name": "Clean Structured Baseline", "description": "Single-latch reducible CFG with structured diamond", "adjacency": structurizer_analyzer_singleton.get_clean_baseline_graph(), "expected_status": "clean"},
    ]

class CPUWriteEventItem(BaseModel):
    address: int; size_bytes: int; generation: int; description: str

class StorageSimulateRequest(BaseModel):
    title_id: str = "PPSA12544"; title_name: str = "Hollow Knight: Silksong (Unity TextCore)"; texture_address: int = 0x25E042000; texture_size: int = 0x40000; block_size: int = 65536; page_size: int = 4096; gpu_dispatch_generation: int = 87617; cpu_writes: Optional[List[CPUWriteEventItem]] = None

@router.post("/storage-writeback/simulate")
async def simulate_storage_writeback(payload: StorageSimulateRequest, user: Dict[str, Any] = Depends(require_role(["operator", "admin"]))):
    cfg = StorageWritebackConfig(payload.title_id, payload.title_name, payload.texture_address, payload.texture_size, payload.block_size, payload.page_size, payload.gpu_dispatch_generation)
    writes = [CPUWriteEvent(w.address, w.size_bytes, w.generation, w.description) for w in payload.cpu_writes] if payload.cpu_writes is not None else None
    rep = storage_writeback_analyzer_singleton.analyze(cfg, writes)
    d = rep.__dict__.copy()
    d.update({"texture_address": hex(rep.texture_address), "texture_size": hex(rep.texture_size), "alignment_offset": hex(rep.alignment_offset), "units": [u.__dict__ for u in rep.units]})
    return d

@router.get("/storage-writeback/presets")
async def get_storage_writeback_presets(user: Dict[str, Any] = Depends(get_current_user)):
    return [
        {"id": "silksong-sdf-atlas", "name": "Silksong SDF Font Atlas (Issue #865)", "description": "Unaligned 512x512 R8 texture at 0x25e042000 dropped by 64 KiB block StoredOver", "texture_address": 0x25E042000, "texture_size": 0x40000, "expected_status": "conflict_detected"},
        {"id": "aligned-baseline", "name": "Aligned 64 KiB Texture Baseline", "description": "64 KiB aligned texture with no adjacent sharing allocations", "texture_address": 0x25E040000, "texture_size": 0x40000, "expected_status": "clean"},
    ]
