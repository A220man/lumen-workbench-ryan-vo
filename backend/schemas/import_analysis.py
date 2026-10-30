"""Import analysis schemas for lumen-workbench-ryan-vo."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


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


class TitleHistoryItem(BaseModel):
    id: int
    title_id: int
    previous_status: Optional[str]
    new_status: str
    changed_by: str
    changed_at: str


class ImportAnalysisResponse(BaseModel):
    id: int
    title_name: str
    imported_at: str
    analyzed_by: Optional[str]


class ImportRecordResponse(BaseModel):
    """Schema for import record responses."""
    id: int
    title_name: str
    status: str
    imported_at: datetime
    analyzed_by: Optional[str]
    analysis_result: Optional[str]

    model_config = ConfigDict(from_attributes=True)
