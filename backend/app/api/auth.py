"""Authentication API for lumen-workbench-ryan-vo."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from typing import Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])

security = HTTPBearer()

class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str

class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

@router.post("/login", response_model=LoginResponse)
async def login(request: Request, credentials: LoginRequest):
    """Authenticate a user and return access token."""
    # In a real implementation, this would validate credentials against OIDC
    # For demo purposes, we'll accept hardcoded credentials
    if credentials.username == "admin" and credentials.password == "admin":
        # Generate a dummy token
        token_data = {
            "sub": "admin-user",
            "role": "admin",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        # In real implementation, use JWT
        token = "mock-jwt-token"
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

@router.post("/logout")
async def logout():
    """Logout user and invalidate token."""
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user(request: Request):
    """Get current user information."""
    # In real implementation, validate token and return user info
    return {
        "id": "admin-user",
        "email": "admin@example.com",
        "name": "Admin User",
        "role": "admin"
    }