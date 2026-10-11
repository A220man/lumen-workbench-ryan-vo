"""Authentication API for lumen-workbench-ryan-vo.

Supports:
- OIDC authorization URL generation with PKCE (S256), state and nonce
- OIDC code exchange & token validation against configured Keycloak/OIDC provider
- Local-only demo mode (explicitly refused in production)
- User session / me endpoint and logout
- Role-based authorization dependencies (viewer, operator/analyst, admin)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import jwt
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...core.config import settings
from ...core.security import (
    build_authorization_url,
    exchange_code,
    fetch_discovery,
    fetch_jwks_jwk,
    generate_nonce,
    generate_state,
    generate_verifier,
    jwk_to_pem,
    validate_id_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

# Ephemeral in-memory store for pending PKCE authorization flows (keyed by state)
_pending_states: Dict[str, Dict[str, Any]] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    role: str
    user: Dict[str, Any]


class PKCEAuthUrlResponse(BaseModel):
    authorization_url: str
    state: str


class CallbackRequest(BaseModel):
    code: str
    state: str


def create_token(user_id: str, email: str, name: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT token."""
    delta = expires_delta or timedelta(seconds=settings.session_ttl_seconds)
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "role": role,
        "iss": settings.oidc_audience or "lumen",
        "aud": settings.oidc_audience or "lumen",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            audience=settings.oidc_audience or "lumen",
            options={"verify_aud": bool(settings.oidc_audience), "verify_exp": True},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """Extract and validate user from Bearer token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


def require_role(allowed_roles: List[str]):
    """Role-based authorization dependency."""
    async def dependency(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        role = user.get("role", "viewer")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is not authorized. Required: {allowed_roles}",
            )
        return user
    return dependency


@router.get("/config")
async def get_auth_config() -> Dict[str, Any]:
    """Return public authentication configuration for frontend clients."""
    return {
        "demo_mode": settings.demo_mode,
        "oidc_enabled": settings.oidc_enabled,
        "provider_url": settings.oidc_provider_url,
        "client_id": settings.oidc_client_id,
        "default_role": settings.oidc_default_role,
        "allowed_roles": settings.oidc_allowed_roles,
    }


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """Local demo login endpoint."""
    if not settings.demo_mode:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password login is disabled. Use OIDC authorization flow.")
    if settings.is_production:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo login is disabled in production.")
    if credentials.username in ("admin", "operator", "demo", "ryan") and credentials.password == "admin":
        role = "admin" if credentials.username == "admin" else "operator"
        user_info = {"id": f"demo-{credentials.username}", "email": f"{credentials.username}@localhost", "name": f"Demo {credentials.username.title()}", "role": role}
        token = create_token(user_info["id"], user_info["email"], user_info["name"], role)
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.session_ttl_seconds),
            role=role,
            user=user_info,
        )
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.get("/authorize", response_model=PKCEAuthUrlResponse)
async def authorize(redirect_uri: Optional[str] = None):
    """Start OIDC authorization-code flow with PKCE."""
    if not settings.oidc_provider_url:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OIDC provider URL is not configured")
    target_redirect = redirect_uri or settings.oidc_redirect_uri
    state, nonce, verifier = generate_state(), generate_nonce(), generate_verifier()
    _pending_states[state] = {"nonce": nonce, "verifier": verifier, "redirect_uri": target_redirect, "created_at": datetime.now(timezone.utc)}
    try:
        discovery = await fetch_discovery(settings.oidc_provider_url)
        auth_url = build_authorization_url(discovery, settings.oidc_client_id, target_redirect, state, nonce, verifier)
        return PKCEAuthUrlResponse(authorization_url=auth_url, state=state)
    except Exception as e:
        logger.error(f"Failed to build authorization URL: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to contact OIDC provider: {str(e)}")


@router.post("/callback", response_model=LoginResponse)
async def callback(cb: CallbackRequest):
    """Handle OIDC token exchange callback."""
    pending = _pending_states.pop(cb.state, None)
    if not pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired authorization state")
    try:
        discovery = await fetch_discovery(settings.oidc_provider_url)
        token_data = await exchange_code(
            discovery, settings.oidc_client_id, settings.oidc_client_secret, pending["redirect_uri"], cb.code, pending["verifier"]
        )
        id_token = token_data.get("id_token")
        if not id_token:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Provider did not return an id_token")
        jwk = await fetch_jwks_jwk(discovery, settings.oidc_provider_url)
        claims = await validate_id_token(
            id_token, jwk_to_pem(jwk), pending["nonce"], settings.oidc_audience or settings.oidc_client_id, discovery.get("issuer", settings.oidc_provider_url)
        )
        email = claims.get("email", "user@oidc.local")
        name = claims.get("name", claims.get("preferred_username", email))
        user_id = claims.get("sub", email)
        roles = claims.get("roles", [settings.oidc_default_role])
        role = roles[0] if roles else settings.oidc_default_role
        user_info = {"id": user_id, "email": email, "name": name, "role": role}
        return LoginResponse(
            access_token=create_token(user_id, email, name, role),
            token_type="bearer",
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.session_ttl_seconds),
            role=role,
            user=user_info,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OIDC callback exchange failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Token exchange failed: {str(e)}")


@router.post("/logout")
async def logout():
    """Logout user."""
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    """Return authenticated user profile."""
    return user