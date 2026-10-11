"""Title schemas for lumen-workbench-ryan-vo."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

class TitleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"

class TitleCreate(BaseModel):
    """Schema for creating a title."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    status: TitleStatus = TitleStatus.DRAFT

class TitleUpdate(BaseModel):
    """Schema for updating a title."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    status: Optional[TitleStatus] = None

class TitleResponse(BaseModel):
    """Schema for title responses."""
    id: int
    name: str
    description: Optional[str]
    status: TitleStatus
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)