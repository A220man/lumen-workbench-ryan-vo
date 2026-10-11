"""API route definitions for lumen-workbench-ryan-vo."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...core.nid import nid_of
from ...models.title import Title
from ...models.evaluation import Evaluation
from ...models.import_record import ImportRecord
from ...models.audit import AuditLog
from ...schemas.title import TitleCreate, TitleUpdate, TitleResponse
from ...schemas.evaluation import EvaluationCreate, EvaluationResponse
from ...services.import_resolver import ImportResolver
from ...services.evaluator import run_evaluation as run_eval_metrics
from ...services.advisory import build_advisor, explain_imports
from ...services.adversarial import AdversarialGenerator, run_stress_test
from ...services.shader_analyzer import (
    RDNA2ShaderAnalyzer,
    IRInstruction,
    ShaderAnalysisReport,
    RDNA2_ANCILLARY_LAYOUT,
)
from ...services.structurizer import CFGStructurizerAnalyzer, CFGDiagnosticReport
from .auth import get_current_user, require_role

router = APIRouter(tags=["API"])
resolver_singleton = ImportResolver()
adversarial_generator_singleton = AdversarialGenerator()
shader_analyzer_singleton = RDNA2ShaderAnalyzer()
structurizer_analyzer_singleton = CFGStructurizerAnalyzer()


class RunEvaluationRequest(BaseModel):
    title_name: Optional[str] = None
    title_id: Optional[int] = None


class ResolvedImportItem(BaseModel):
    name: str
    nid: int
    library: Optional[str] = None
    status: str


class ResolutionReportResponse(BaseModel):
    source_name: str
    needed_libraries: List[str]
    imports: List[ResolvedImportItem]
    resolved_count: int
    unresolved_count: int
    missing_module_count: int
    coverage: float
    score: int
    blockers: List[str]
    advisory: Optional[str] = None


# -----------------------------------------------------------------------------
# Titles CRUD & Search (Requires at least viewer role for GET, operator for writes)
# -----------------------------------------------------------------------------

@router.get("/titles", response_model=List[TitleResponse])
async def list_titles(
    search: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """List titles with pagination and filtering."""
    query = select(Title)
    if search:
        query = query.where(Title.name.ilike(f"%{search}%"))
    if status:
        query = query.where(Title.status == status)
    return [TitleResponse.model_validate(t) for t in db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()]


@router.get("/titles/{title_id}", response_model=TitleResponse)
async def get_title(title_id: int, db: Session = Depends(get_db), user: Dict[str, Any] = Depends(get_current_user)):
    """Get a specific title by ID."""
    title = db.get(Title, title_id)
    if not title:
        raise HTTPException(status_code=404, detail="Title not found")
    return TitleResponse.model_validate(title)


@router.post("/titles", response_model=TitleResponse, status_code=201)
async def create_title(
    title_data: TitleCreate,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["operator", "admin"])),
):
    """Create a new title (operator or admin)."""
    title = Title(**title_data.model_dump())
    db.add(title)
    db.add(AuditLog(action="create_title", entity_type="title", details=f"Title created: {title_data.name} by {user.get('email')}"))
    db.commit()
    db.refresh(title)
    return TitleResponse.model_validate(title)


@router.put("/titles/{title_id}", response_model=TitleResponse)
async def update_title(
    title_id: int,
    title_data: TitleUpdate,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["operator", "admin"])),
):
    """Update a title (operator or admin)."""
    title = db.get(Title, title_id)
    if not title:
        raise HTTPException(status_code=404, detail="Title not found")
    for field, value in title_data.model_dump(exclude_unset=True).items():
        setattr(title, field, value)
    db.add(AuditLog(action="update_title", entity_type="title", entity_id=title_id, details=f"Title updated by {user.get('email')}"))
    db.commit()
    db.refresh(title)
    return TitleResponse.model_validate(title)


@router.delete("/titles/{title_id}", status_code=204)
async def delete_title(
    title_id: int,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["admin"])),
):
    """Delete a title (admin only)."""
    title = db.get(Title, title_id)
    if not title:
        raise HTTPException(status_code=404, detail="Title not found")
    db.add(AuditLog(action="delete_title", entity_type="title", entity_id=title_id, details=f"Title deleted by {user.get('email')}"))
    db.delete(title)
    db.commit()
    return None


# -----------------------------------------------------------------------------
# Domain Workflow 1: PS5 ELF Import Resolver & Analysis
# -----------------------------------------------------------------------------

@router.post("/imports/analyze", response_model=ResolutionReportResponse)
async def analyze_imports(
    file: UploadFile = File(...),
    explain: bool = False,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Parse and resolve ELF imports from uploaded binary data.

    Executes deterministic resolution against host library export database.
    Optionally requests opt-in advisory explanation.
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    report = resolver_singleton.analyze_bytes(content, source_name=file.filename or "upload.elf")
    
    advisory_text: Optional[str] = None
    if explain:
        advisor = build_advisor()
        advisory_text = await explain_imports(report, advisor)
    
    # Persist import analysis record
    rec = ImportRecord(
        title_name=file.filename or "unknown.elf",
        status="complete" if report.score >= 50 else "needs_stubs",
        analyzed_by=user.get("email"),
        analysis_result=f"score={report.score}, coverage={report.coverage:.2f}, resolved={report.resolved_count}",
    )
    db.add(rec)
    db.commit()

    return ResolutionReportResponse(
        source_name=report.source_name,
        needed_libraries=report.needed_libraries,
        imports=[ResolvedImportItem(name=i.name, nid=i.nid, library=i.library, status=i.status) for i in report.imports],
        resolved_count=report.resolved_count,
        unresolved_count=report.unresolved_count,
        missing_module_count=report.missing_module_count,
        coverage=report.coverage,
        score=report.score,
        blockers=report.blockers,
        advisory=advisory_text,
    )


# -----------------------------------------------------------------------------
# Domain Workflow 2: Labeled Evaluation Dataset & Benchmark
# -----------------------------------------------------------------------------

@router.get("/evaluations", response_model=List[EvaluationResponse])
async def list_evaluations(
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """List historical evaluations."""
    evals = db.execute(select(Evaluation)).scalars().all()
    return [EvaluationResponse.model_validate(e) for e in evals]


@router.post("/evaluations/run")
async def run_evaluation_endpoint(
    req: RunEvaluationRequest,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["operator", "admin"])),
):
    """Run import resolver benchmark against the labeled dataset."""
    metrics = run_eval_metrics(resolver_singleton)
    
    # Record evaluation record if title provided
    if req.title_id:
        title = db.get(Title, req.title_id)
        if title:
            eval_record = Evaluation(
                title_id=title.id,
                score=round(metrics.f1 * 10, 2),
                comments=f"F1={metrics.f1:.3f}, Precision={metrics.precision:.3f}, Recall={metrics.recall:.3f}",
            )
            db.add(eval_record)
            db.commit()

    return {
        "status": "success",
        "precision": metrics.precision,
        "recall": metrics.recall,
        "f1": metrics.f1,
        "coverage": metrics.coverage,
        "true_positive": metrics.true_positive,
        "false_positive": metrics.false_positive,
        "false_negative": metrics.false_negative,
        "per_library": metrics.per_library,
    }


# -----------------------------------------------------------------------------
# Domain Workflow 3: Adversarial ELF Test Case Generator & Stress Testing
# -----------------------------------------------------------------------------

@router.post("/adversarial/generate")
async def generate_adversarial_spec(
    prefix: Optional[str] = None,
    category: Optional[str] = None,
    count: int = 5,
    user: Dict[str, Any] = Depends(require_role(["operator", "admin"])),
):
    """Generate synthetic boundary test cases to probe resolver behavior."""
    if prefix:
        items = [{
            "name": f"{prefix}_adversarial_sym_{i}",
            "nid": nid_of(f"{prefix}_adversarial_sym_{i}"),
            "predicted_status": "unresolved" if not resolver_singleton.resolve_name(f"{prefix}_adversarial_sym_{i}") else "resolved",
            "category": category or "prefix_boundary",
        } for i in range(min(max(count, 1), 50))]
    else:
        items = [{
            "name": c.symbol,
            "nid": c.nid,
            "predicted_status": c.expected_status,
            "category": c.category,
            "mutation_type": c.mutation_type,
        } for c in adversarial_generator_singleton.generate_cases(category=category, count=count)]
    return {"generated_count": len(items), "symbols": items}


@router.post("/adversarial/stress-test")
async def run_adversarial_stress_test(
    category: Optional[str] = None,
    user: Dict[str, Any] = Depends(require_role(["operator", "admin"])),
):
    """Run stress test against host export boundaries and report stability score."""
    cases = adversarial_generator_singleton.generate_cases(category=category, count=50)
    report = run_stress_test(resolver_singleton, custom_cases=cases)
    return {
        "status": "success",
        "total_cases": report.total_cases,
        "passed_cases": report.passed_cases,
        "failed_cases": report.failed_cases,
        "stability_score": report.stability_score,
        "false_positive_rate": report.false_positive_rate,
        "category_scores": report.category_scores,
        "vulnerabilities": report.vulnerabilities,
    }


# -----------------------------------------------------------------------------
# System Status & Telemetry Analytics
# -----------------------------------------------------------------------------

class StatsResponse(BaseModel):
    active_titles: int
    total_imports: int
    resolution_rate: str
    evaluation_count: int


class AnalyticsResponse(BaseModel):
    resolution_by_library: str
    performance_trend: str
    import_volume: str
    per_library: Dict[str, Dict[str, int]]
    metrics: Dict[str, float]
    adversarial_stability: Optional[str] = None
    shader_diagnostics: Optional[str] = None
    structurizer_diagnostics: Optional[str] = None


@router.get("/stats", response_model=StatsResponse)
async def get_system_stats(
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Retrieve system status metrics."""
    active_titles = db.execute(
        select(func.count(Title.id)).where(Title.status == "active")
    ).scalar() or 0

    total_imports = db.execute(
        select(func.count(ImportRecord.id))
    ).scalar() or 0

    eval_count = db.execute(
        select(func.count(Evaluation.id))
    ).scalar() or 0

    metrics = run_eval_metrics(resolver_singleton)
    res_rate_pct = f"{metrics.coverage * 100:.1f}%"

    return StatsResponse(
        active_titles=active_titles,
        total_imports=total_imports,
        resolution_rate=res_rate_pct,
        evaluation_count=eval_count,
    )


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Retrieve resolution analytics and benchmark metrics."""
    metrics = run_eval_metrics(resolver_singleton)
    stress_report = run_stress_test(resolver_singleton)
    stray_shaders = shader_analyzer_singleton.get_stray_catalog_shaders()
    deferred_count = sum(1 for s in stray_shaders if s.status == "rejected_unsupported_live_use")
    cfg_report = structurizer_analyzer_singleton.analyze_cfg(
        "issue_2642_repro",
        structurizer_analyzer_singleton.get_issue_2642_graph(),
    )
    top_lib = (
        max(metrics.per_library.items(), key=lambda x: x[1].get("tp", 0))[0]
        if metrics.per_library
        else "libkernel"
    )
    total_imports = db.execute(select(func.count(ImportRecord.id))).scalar() or 0

    return AnalyticsResponse(
        resolution_by_library=f"Lead module: {top_lib} ({metrics.per_library.get(top_lib, {}).get('tp', 0)} symbols)",
        performance_trend=f"F1={metrics.f1:.3f} (coverage {metrics.coverage * 100:.1f}%)",
        import_volume=f"{total_imports} records analyzed",
        per_library=metrics.per_library,
        metrics={
            "precision": round(metrics.precision, 4),
            "recall": round(metrics.recall, 4),
            "f1": round(metrics.f1, 4),
            "coverage": round(metrics.coverage, 4),
            "stability_score": round(stress_report.stability_score, 2),
        },
        adversarial_stability=f"{stress_report.stability_score:.1f}% stability ({stress_report.passed_cases}/{stress_report.total_cases} boundary probes)",
        shader_diagnostics=f"{deferred_count}/{len(stray_shaders)} Stray UE4 shaders deferred (issue #2548 unsupported live use)",
        structurizer_diagnostics=f"Issue #2642 repro: {cfg_report.status} ({cfg_report.current_blocks}/{cfg_report.original_blocks} blocks, budget {cfg_report.split_budget})",
    )


# -----------------------------------------------------------------------------
# Shader Recompiler Diagnostics (Issue #2548)
# -----------------------------------------------------------------------------

class ShaderAnalyzeInstruction(BaseModel):
    index: int
    opcode: str
    dest: Optional[str] = None
    sources: List[str] = Field(default_factory=list)
    bit_offset: Optional[int] = None
    bit_length: Optional[int] = None
    condition: Optional[str] = None


class ShaderAnalyzeRequest(BaseModel):
    shader_address: str = "0x200e370000"
    title_id: str = "PPSA02100"
    ancillary_vgpr: str = "v4"
    instructions: Optional[List[ShaderAnalyzeInstruction]] = None
    raw_word: Optional[int] = None


class BitfieldLayoutItem(BaseModel):
    name: str
    offset: int
    length: int
    modeled: bool
    source_builtin: Optional[str] = None
    description: str


class ShaderAnalysisResponse(BaseModel):
    shader_address: str
    title_id: str
    ancillary_vgpr: str
    has_ancillary_access: bool
    extracted_fields: List[str]
    register_reused: bool
    live_use_chain: List[str]
    unsupported_bit_access: bool
    rebuildable_pr1179: bool
    rejection_reason: Optional[str] = None
    status: str
    decoded_word: Optional[Dict[str, Any]] = None


@router.get("/shaders/rdna2-layout", response_model=List[BitfieldLayoutItem])
async def get_rdna2_layout(
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Retrieve RDNA2 packed pixel ancillary VGPR bitfield specification."""
    return [BitfieldLayoutItem(**b.__dict__) for b in RDNA2_ANCILLARY_LAYOUT]


@router.post("/shaders/analyze", response_model=ShaderAnalysisResponse)
async def analyze_shader(
    payload: ShaderAnalyzeRequest,
    user: Dict[str, Any] = Depends(require_role(["operator", "admin"])),
):
    """Analyze shader instruction stream for RDNA2 ancillary register reuse and bitfield extraction."""
    insts = [
        IRInstruction(
            index=i.index,
            opcode=i.opcode,
            dest=i.dest,
            sources=i.sources,
            bit_offset=i.bit_offset,
            bit_length=i.bit_length,
            condition=i.condition,
        )
        for i in (payload.instructions or [])
    ]
    report = shader_analyzer_singleton.analyze_ir_stream(
        shader_address=payload.shader_address,
        title_id=payload.title_id,
        instructions=insts,
        ancillary_vgpr=payload.ancillary_vgpr,
    )
    decoded = shader_analyzer_singleton.decode_word(payload.raw_word) if payload.raw_word is not None else None
    return ShaderAnalysisResponse(**report.__dict__, decoded_word=decoded)


@router.get("/shaders/stray-batch", response_model=List[ShaderAnalysisResponse])
async def get_stray_shaders_batch(
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Retrieve recompiler analysis for Stray (PPSA02100 v1.05) UE4 pixel shaders (issue #2548)."""
    return [
        ShaderAnalysisResponse(**r.__dict__, decoded_word=None)
        for r in shader_analyzer_singleton.get_stray_catalog_shaders()
    ]


# -----------------------------------------------------------------------------
# Structurizer Diagnostics (Issue #2642)
# -----------------------------------------------------------------------------

class CFGAnalyzeRequest(BaseModel):
    name: str = "custom_cfg"
    adjacency: List[List[int]]
    split_budget: Optional[int] = None


class CFGDiagnosticResponse(BaseModel):
    name: str
    original_blocks: int
    current_blocks: int
    split_budget: int
    exceeded_budget: bool
    multi_latch_loops: List[Dict[str, Any]]
    selection_conflicts: List[Dict[str, Any]]
    synthetic_chain_steps: List[str]
    infinite_recursion_detected: bool
    root_cause: Optional[str] = None
    recommendation: Optional[str] = None
    matches_issue_2642: bool
    status: str


class CFGPresetItem(BaseModel):
    id: str
    name: str
    description: str
    adjacency: List[List[int]]
    expected_status: str


@router.post("/structurizer/analyze", response_model=CFGDiagnosticResponse)
async def analyze_cfg(
    payload: CFGAnalyzeRequest,
    user: Dict[str, Any] = Depends(require_role(["operator", "admin"])),
):
    """Analyze shader control-flow graph for shared merge splitting budget exhaustion (issue #2642)."""
    report = structurizer_analyzer_singleton.analyze_cfg(
        name=payload.name,
        adj=payload.adjacency,
        custom_split_budget=payload.split_budget,
    )
    return CFGDiagnosticResponse(**report.__dict__)


@router.get("/structurizer/presets", response_model=List[CFGPresetItem])
async def get_structurizer_presets(
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Retrieve preset CFG test shapes including issue #2642 reproduction graph."""
    return [
        CFGPresetItem(
            id="issue-2642-repro",
            name="Issue #2642 Minimal Reproduction",
            description="Two-latch loop (latches 4 and 5) with nested selections (headers 2 and 3) sharing join block 4",
            adjacency=structurizer_analyzer_singleton.get_issue_2642_graph(),
            expected_status="budget_exceeded",
        ),
        CFGPresetItem(
            id="clean-baseline",
            name="Clean Structured Baseline",
            description="Single-latch reducible CFG with structured branch-join diamond",
            adjacency=structurizer_analyzer_singleton.get_clean_baseline_graph(),
            expected_status="clean",
        ),
    ]