"""API route definitions for lumen-workbench-ryan-vo."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...models.title import Title
from ...models.evaluation import Evaluation
from ...models.import_record import ImportRecord
from ...models.audit import AuditLog
from ...schemas.title import TitleCreate, TitleUpdate, TitleResponse
from ...schemas.evaluation import EvaluationCreate, EvaluationResponse
from ...services.import_resolver import ImportResolver
from ...services.evaluator import run_evaluation as run_eval_metrics
from ...services.advisory import build_advisor, explain_imports
from .auth import get_current_user, require_role

router = APIRouter(tags=["API"])
resolver_singleton = ImportResolver()


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
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    titles = db.execute(query).scalars().all()
    return [TitleResponse.model_validate(title) for title in titles]


@router.get("/titles/{title_id}", response_model=TitleResponse)
async def get_title(
    title_id: int,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
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
    
    # Audit log entry
    audit = AuditLog(
        action="create_title",
        entity_type="title",
        details=f"Title created: {title_data.name} by {user.get('email')}",
    )
    db.add(audit)
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
    
    update_data = title_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(title, field, value)
    
    audit = AuditLog(
        action="update_title",
        entity_type="title",
        entity_id=title_id,
        details=f"Title updated by {user.get('email')}",
    )
    db.add(audit)
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
    
    audit = AuditLog(
        action="delete_title",
        entity_type="title",
        entity_id=title_id,
        details=f"Title deleted by {user.get('email')}",
    )
    db.add(audit)
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
        imports=[
            ResolvedImportItem(
                name=imp.name,
                nid=imp.nid,
                library=imp.library,
                status=imp.status,
            )
            for imp in report.imports
        ],
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
# Domain Workflow 3: Adversarial ELF Test Case Generator
# -----------------------------------------------------------------------------

@router.post("/adversarial/generate")
async def generate_adversarial_spec(
    prefix: str = "sceKernel",
    count: int = 5,
    user: Dict[str, Any] = Depends(require_role(["operator", "admin"])),
):
    """Generate synthetic boundary test cases to probe resolver behavior."""
    items = []
    for i in range(min(max(count, 1), 50)):
        name = f"{prefix}_adversarial_sym_{i}"
        items.append({
            "name": name,
            "nid": resolver_singleton.resolve_name(name),
            "predicted_status": "unresolved" if not resolver_singleton.resolve_name(name) else "resolved",
        })
    return {"generated_count": len(items), "symbols": items}