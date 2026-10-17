from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...models.audit import AuditLog
from ...models.evaluation import Evaluation
from ...models.title import Title
from ...schemas import (
    EvaluationResponse,
    ResolvedImportItem,
    ResolutionReportResponse,
    TitleCreate,
    TitleHistoryItem,
    TitleResponse,
    TitleUpdate,
)
from ...services.adversarial import AdversarialGenerator, run_stress_test
from ...services.evaluator import run_evaluation as run_eval_metrics
from ...services.first_light_diagnostic import get_first_light_diagnostic
from ...services.import_resolver import ImportResolver
from ...services.shader_analyzer import (
    IRInstruction,
    RDNA2ShaderAnalyzer,
    RDNA2_ANCILLARY_LAYOUT,
)
from ...services.structurizer import CFGStructurizerAnalyzer
from ...services.storage_writeback import StorageWritebackAnalyzer, StorageWritebackConfig
from ...services.title_registry import TitleService
from .auth import get_current_user, require_role

class RunEvaluationRequest(BaseModel):
    title_name: Optional[str] = None; title_id: Optional[int] = None
class CFGAnalyzeRequest(BaseModel):
    name: str = "custom_cfg"; adjacency: List[List[int]]; split_budget: Optional[int] = None
class ShaderAnalyzeInstruction(BaseModel):
    index: int; opcode: str; dest: Optional[str] = None; sources: List[str] = []
    bit_offset: Optional[int] = None; bit_length: Optional[int] = None; condition: Optional[str] = None
class ShaderAnalyzeRequest(BaseModel):
    shader_address: str = "0x200e370000"; title_id: str = "PPSA02100"; ancillary_vgpr: str = "v4"
    instructions: Optional[List[ShaderAnalyzeInstruction]] = None; raw_word: Optional[int] = None
class CPUWriteEventItem(BaseModel):
    address: int; size_bytes: int; generation: int; description: str
class StorageSimulateRequest(BaseModel):
    title_id: str = "PPSA12544"; title_name: str = "Hollow Knight: Silksong (Unity TextCore)"
    texture_address: int = 0x25E042000; texture_size: int = 0x40000; block_size: int = 65536
    page_size: int = 4096; gpu_dispatch_generation: int = 87617; cpu_writes: Optional[List[CPUWriteEventItem]] = None
class StopPRItem(BaseModel):
    number: int; url: str; commit: str; merged: bool; description: str
class StartupStopItem(BaseModel):
    index: int; description: str; error_text: str; shader_cache_misses: Optional[int]
    prs: List[StopPRItem]; verified: bool; notes: str = ""
class FirstLightReportResponse(BaseModel):
    title_id: str; title_name: str; version: str; stops: List[StartupStopItem]
    current_stop: int; passed_stops: int; failed_stops: int; status: str
    regression_detected: bool; regression_details: List[str]
class FirstLightAnalyzeRequest(BaseModel):
    applied_prs: Optional[List[int]] = None

def _load_api_presets() -> Dict[str, Any]:
    data_path = Path(__file__).parent.parent.parent / "data" / "api_presets.json"
    with data_path.open() as f:
        return json.load(f)


API_PRESETS = _load_api_presets()
router = APIRouter(tags=["API"])
resolver_singleton = ImportResolver()
adversarial_generator_singleton = AdversarialGenerator()
shader_analyzer_singleton = RDNA2ShaderAnalyzer()
structurizer_analyzer_singleton = CFGStructurizerAnalyzer()
storage_writeback_analyzer_singleton = StorageWritebackAnalyzer()
first_light_diagnostic_singleton = get_first_light_diagnostic()


@router.get("/titles", response_model=List[TitleResponse])
async def list_titles(
    search: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    svc = TitleService(db)
    items = svc.list(limit=page_size, offset=(page - 1) * page_size, status=status)
    if search:
        items = [i for i in items if search.lower() in i.name.lower()]
    return [TitleResponse.model_validate(i) for i in items]


@router.get("/titles/ppsa/{ppsa_id}", response_model=TitleResponse)
async def get_title_by_ppsa(
    ppsa_id: str, db: Session = Depends(get_db), user: Dict[str, Any] = Depends(get_current_user)
):
    svc = TitleService(db)
    t = svc.get_by_ppsa(ppsa_id)
    if not t:
        raise HTTPException(404, "Title not found")
    return TitleResponse.model_validate(t)


@router.get("/titles/{title_id}", response_model=TitleResponse)
async def get_title(
    title_id: int, db: Session = Depends(get_db), user: Dict[str, Any] = Depends(get_current_user)
):
    svc = TitleService(db)
    t = svc.get(title_id)
    if not t:
        raise HTTPException(404, "Title not found")
    return TitleResponse.model_validate(t)


@router.post("/titles", response_model=TitleResponse, status_code=201)
async def create_title(
    data: TitleCreate,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["operator", "admin"])),
):
    svc = TitleService(db)
    t = svc.create(data)
    db.add(AuditLog(action="create_title", entity_type="title", details=f"Title created: {data.name} by {user.get('email')}"))
    db.commit()
    db.refresh(t)
    return TitleResponse.model_validate(t)


@router.put("/titles/{title_id}", response_model=TitleResponse)
async def update_title(
    title_id: int,
    data: TitleUpdate,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["operator", "admin"])),
):
    svc = TitleService(db)
    t = svc.update(title_id, data)
    if not t:
        raise HTTPException(404, "Title not found")
    db.add(AuditLog(action="update_title", entity_type="title", entity_id=title_id, details=f"Title updated by {user.get('email')}"))
    db.commit()
    db.refresh(t)
    return TitleResponse.model_validate(t)


@router.delete("/titles/{title_id}", status_code=204)
async def delete_title(
    title_id: int,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["admin"])),
):
    svc = TitleService(db)
    t = svc.get(title_id)
    if not t:
        raise HTTPException(404, "Title not found")
    db.add(AuditLog(action="delete_title", entity_type="title", entity_id=title_id, details=f"Title deleted by {user.get('email')}"))
    db.delete(t)
    db.commit()
    return None


@router.get("/titles/{title_id}/history", response_model=List[TitleHistoryItem])
async def get_title_history(
    title_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    svc = TitleService(db)
    hist = svc.history(title_id, limit=limit)
    return [
        TitleHistoryItem(
            id=h.id,
            title_id=h.title_id,
            previous_status=h.previous_status,
            new_status=h.new_status,
            changed_by=h.changed_by,
            changed_at=h.changed_at.isoformat(),
            notes=h.notes,
        )
        for h in hist
    ]


@router.post("/imports/analyze", response_model=ResolutionReportResponse)
async def analyze_imports(
    file: UploadFile = File(...),
    explain: bool = False,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    content = await file.read()
    rep = resolver_singleton.analyze_bytes(content, source_name=file.filename or "upload")
    adv = None
    if explain:
        from ...services.advisory import generate_advisory
        adv = await generate_advisory(rep)
    return ResolutionReportResponse(
        source_name=rep.source_name,
        needed_libraries=rep.needed_libraries,
        imports=[
            ResolvedImportItem(name=i.name, nid=i.nid, library=i.library, status=i.status)
            for i in rep.imports
        ],
        resolved_count=rep.resolved_count,
        unresolved_count=rep.unresolved_count,
        missing_module_count=rep.missing_module_count,
        coverage=rep.coverage,
        score=rep.score,
        blockers=rep.blockers,
        advisory=adv,
    )


@router.get("/evaluations", response_model=List[EvaluationResponse])
async def list_evaluations(
    db: Session = Depends(get_db), user: Dict[str, Any] = Depends(get_current_user)
):
    return [EvaluationResponse.model_validate(e) for e in db.execute(select(Evaluation)).scalars().all()]


@router.post("/evaluations/run")
async def run_evaluation_endpoint(
    req: RunEvaluationRequest,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["operator", "admin"])),
):
    m = run_eval_metrics(resolver_singleton)
    eval_record = Evaluation(
        title_id=req.title_id or 1,
        score=round(m.f1 * 100, 1),
        comments=f"Auto-evaluation: precision={m.precision:.3f}, recall={m.recall:.3f}, coverage={m.coverage:.3f}",
    )
    db.add(eval_record)
    db.commit()
    return {"status": "success", **m.__dict__}


@router.post("/adversarial/generate")
async def generate_adversarial_spec(
    prefix: Optional[str] = None,
    category: Optional[str] = None,
    count: int = 5,
    user: Dict[str, Any] = Depends(require_role(["operator", "admin"])),
):
    all_items = adversarial_generator_singleton.generate_cases(category=category, count=100)
    items = [i for i in all_items if i.symbol.startswith(prefix)] if prefix else all_items
    return {
        "generated_count": len(items[:count]),
        "symbols": [
            {
                "name": c.symbol,
                "nid": c.nid,
                "predicted_status": c.expected_status,
                "category": c.category,
                "mutation_type": c.mutation_type,
            }
            for c in items[:count]
        ],
    }


@router.post("/adversarial/stress-test")
async def run_adversarial_stress_test(
    category: Optional[str] = None,
    user: Dict[str, Any] = Depends(require_role(["operator", "admin"])),
):
    rep = run_stress_test(
        resolver_singleton,
        custom_cases=adversarial_generator_singleton.generate_cases(category=category, count=50),
    )
    return {"status": "success", **rep.__dict__}


@router.get("/stats")
async def get_system_stats(
    db: Session = Depends(get_db), user: Dict[str, Any] = Depends(get_current_user)
):
    active = db.execute(select(func.count(Title.id)).where(Title.status == "active")).scalar() or 0
    total = db.execute(select(func.count(Title.id))).scalar() or 0
    m = run_eval_metrics(resolver_singleton)
    evals = db.execute(select(func.count(Evaluation.id))).scalar() or 0
    return {
        "active_titles": active,
        "total_imports": total,
        "resolution_rate": f"{m.coverage * 100:.1f}%",
        "evaluation_count": evals,
    }


@router.get("/analytics")
async def get_analytics(
    db: Session = Depends(get_db), user: Dict[str, Any] = Depends(get_current_user)
):
    m = run_eval_metrics(resolver_singleton)
    rep = run_stress_test(resolver_singleton)
    total = db.execute(select(func.count(Title.id))).scalar() or 0
    return {
        "resolution_by_library": ", ".join(
            f"{lib}: {v['tp']}/{v['tp'] + v['fn']}" for lib, v in m.per_library.items()
        ),
        "performance_trend": "stable",
        "import_volume": str(total),
        "per_library": {
            lib: {"tp": v["tp"], "fp": v["fp"], "fn": v["fn"]} for lib, v in m.per_library.items()
        },
        "metrics": {
            "precision": m.precision,
            "recall": m.recall,
            "f1": m.f1,
            "coverage": m.coverage,
        },
        "adversarial_stability": f"stability: {rep.stability_score:.1f}%",
        "shader_diagnostics": "26 UE4 shaders register reuse (#2548)",
        "structurizer_diagnostics": "Issue #2642 CFG budget exhaustion",
        "storage_writeback_diagnostics": "Silksong PPSA12544 edge block corruption (#865)",
    }


@router.get("/shaders/rdna2-layout")
async def get_rdna2_layout(user: Dict[str, Any] = Depends(get_current_user)):
    return [b.__dict__ for b in RDNA2_ANCILLARY_LAYOUT]


@router.post("/shaders/analyze")
async def analyze_shader(
    payload: ShaderAnalyzeRequest, user: Dict[str, Any] = Depends(require_role(["operator", "admin"]))
):
    insts = [
        IRInstruction(i.index, i.opcode, i.dest, i.sources, i.bit_offset, i.bit_length, i.condition)
        for i in (payload.instructions or [])
    ]
    res = shader_analyzer_singleton.analyze_ir_stream(
        payload.shader_address, payload.title_id, insts, payload.ancillary_vgpr
    )
    if payload.raw_word is not None:
        res.decoded_word = shader_analyzer_singleton.decode_word(payload.raw_word)
    return res.__dict__


@router.get("/shaders/stray-batch")
async def get_stray_shaders_batch(user: Dict[str, Any] = Depends(get_current_user)):
    return [r.__dict__ for r in shader_analyzer_singleton.get_stray_catalog_shaders()]


@router.post("/structurizer/analyze")
async def analyze_cfg(
    payload: CFGAnalyzeRequest, user: Dict[str, Any] = Depends(require_role(["operator", "admin"]))
):
    return structurizer_analyzer_singleton.analyze_cfg(payload.name, payload.adjacency, payload.split_budget).__dict__


@router.get("/structurizer/presets")
async def get_structurizer_presets(user: Dict[str, Any] = Depends(get_current_user)):
    return API_PRESETS["structurizer_presets"]


@router.post("/storage-writeback/simulate")
async def simulate_storage_writeback(
    payload: StorageSimulateRequest, user: Dict[str, Any] = Depends(require_role(["operator", "admin"]))
):
    from ...services.storage_writeback import CPUWriteEvent

    cfg = StorageWritebackConfig(
        payload.title_id,
        payload.title_name,
        payload.texture_address,
        payload.texture_size,
        payload.block_size,
        payload.page_size,
        payload.gpu_dispatch_generation,
    )
    if payload.cpu_writes:
        writes = [CPUWriteEvent(w.address, w.size_bytes, w.generation, w.description) for w in payload.cpu_writes]
    else:
        _, writes = storage_writeback_analyzer_singleton.get_silksong_preset()
    rep = storage_writeback_analyzer_singleton.analyze(config=cfg, cpu_writes=writes)
    return rep.__dict__


@router.get("/storage-writeback/presets")
async def get_storage_writeback_presets(user: Dict[str, Any] = Depends(get_current_user)):
    return API_PRESETS["storage_writeback_presets"]


@router.get("/first-light/stops", response_model=List[StartupStopItem])
async def get_first_light_stops(user: Dict[str, Any] = Depends(get_current_user)):
    stops = first_light_diagnostic_singleton.get_all_stops()
    return [
        StartupStopItem(
            index=s.index,
            description=s.description,
            error_text=s.error_text,
            shader_cache_misses=s.shader_cache_misses,
            prs=[
                StopPRItem(
                    number=pr.number,
                    url=pr.url,
                    commit=pr.commit,
                    merged=pr.merged,
                    description=pr.description,
                )
                for pr in s.prs
            ],
            verified=s.verified,
            notes=s.notes,
        )
        for s in stops
    ]


@router.get("/first-light/presets")
async def get_first_light_presets(user: Dict[str, Any] = Depends(get_current_user)):
    return first_light_diagnostic_singleton.get_presets()


@router.post("/first-light/analyze", response_model=FirstLightReportResponse)
async def analyze_first_light(
    payload: FirstLightAnalyzeRequest, user: Dict[str, Any] = Depends(get_current_user)
):
    report = first_light_diagnostic_singleton.analyze_sequence(payload.applied_prs)
    return FirstLightReportResponse(
        title_id=report.title_id,
        title_name=report.title_name,
        version=report.version,
        stops=[
            StartupStopItem(
                index=s.index,
                description=s.description,
                error_text=s.error_text,
                shader_cache_misses=s.shader_cache_misses,
                prs=[
                    StopPRItem(
                        number=pr.number,
                        url=pr.url,
                        commit=pr.commit,
                        merged=pr.merged,
                        description=pr.description,
                    )
                    for pr in s.prs
                ],
                verified=s.verified,
                notes=s.notes,
            )
            for s in report.stops
        ],
        current_stop=report.current_stop,
        passed_stops=report.passed_stops,
        failed_stops=report.failed_stops,
        status=report.status,
        regression_detected=report.regression_detected,
        regression_details=report.regression_details,
    )