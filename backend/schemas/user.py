"""User schemas for lumen-workbench-ryan-vo."""
from pydantic import BaseModel, Field, EmailStr
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
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.ANALYST

class UserResponse(BaseModel):
    """Schema for user responses."""
    id: int
    email: EmailStr
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True