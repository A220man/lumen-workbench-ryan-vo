"""Import record schemas for lumen-workbench-ryan-vo."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ImportRecordCreate(BaseModel):
    """Schema for creating an import record."""
    title_name: str = Field(..., min_length=1, max_length=255)
    version: Optional[str] = Field(None, max_length=50)
    file_path: Optional[str] = Field(None, max_length=512)

class ImportRecordResponse(BaseModel):
    """Schema for import record responses."""
    id: int
    title_name: str
    version: Optional[str]
    file_path: Optional[str]
    status: str
    imported_at: datetime
    analyzed_by: Optional[str]
    analysis_result: Optional[str]

    class Config:
        from_attributes = True