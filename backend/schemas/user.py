"""User schemas for lumen-workbench-ryan-vo."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ANALYST = "analyst"
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"

class UserCreate(BaseModel):
    """Schema for creating a user."""
    email: str = Field(..., min_length=3, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.ANALYST

class UserResponse(BaseModel):
    """Schema for user responses."""
    id: int
    email: str
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True