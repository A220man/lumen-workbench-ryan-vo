"""Import record schemas for lumen-workbench-ryan-vo."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ImportRecordCreate(BaseModel):
    """Schema for creating an import record."""
    title_name: str = Field(..., min_length=1, max_length=255)


class ImportRecordResponse(BaseModel):
    """Schema for import record responses."""
    id: int
    title_name: str
    status: str
    imported_at: datetime
    analyzed_by: Optional[str]
    analysis_result: Optional[str]

    model_config = ConfigDict(from_attributes=True)