"""Evaluation schemas for lumen-workbench-ryan-vo."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class EvaluationCreate(BaseModel):
    """Schema for creating an evaluation."""
    title_id: int
    score: float = Field(..., ge=0.0, le=10.0)
    comments: Optional[str] = Field(None, max_length=2048)

class EvaluationResponse(BaseModel):
    """Schema for evaluation responses."""
    id: int
    title_id: int
    score: float
    comments: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)