"""Authentication API for lumen-workbench-ryan-vo."""
from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import jwt
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...core.config import settings
from ...core.security import (
    build_authorization_url, exchange_code, fetch_discovery, fetch_jwks_jwk,
    generate_nonce, generate_state, generate_verifier, jwk_to_pem, validate_id_token,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)
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
    delta = expires_delta or timedelta(seconds=settings.session_ttl_seconds)
    payload = {
        "sub": user_id, "email": email, "name": name, "role": role,
        "iss": settings.oidc_audience or "lumen", "aud": settings.oidc_audience or "lumen",
        "iat": datetime.now(timezone.utc), "exp": datetime.now(timezone.utc) + delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")

def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(
            token, settings.secret_key, algorithms=["HS256"], audience=settings.oidc_audience or "lumen",
            options={"verify_aud": bool(settings.oidc_audience), "verify_exp": True},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid or expired token: {str(e)}", headers={"WWW-Authenticate": "Bearer"})

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing authorization bearer token", headers={"WWW-Authenticate": "Bearer"})
    return decode_token(credentials.credentials)

def require_role(allowed_roles: List[str]):
    async def dependency(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        role = user.get("role", "viewer")
        if role not in allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Role '{role}' is not authorized. Required: {allowed_roles}")
        return user
    return dependency

@router.get("/config")
async def get_auth_config() -> Dict[str, Any]:
    return {
        "demo_mode": settings.demo_mode, "oidc_enabled": settings.oidc_enabled,
        "provider_url": settings.oidc_provider_url, "client_id": settings.oidc_client_id,
        "default_role": settings.oidc_default_role, "allowed_roles": settings.oidc_allowed_roles,
    }

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    if not settings.demo_mode: raise HTTPException(400, "Password login is disabled. Use OIDC authorization flow.")
    if settings.is_production: raise HTTPException(403, "Demo login is disabled in production.")
    if credentials.username in ("admin", "operator", "demo", "ryan") and credentials.password == "admin":
        role = "admin" if credentials.username == "admin" else "operator"
        user_info = {"id": f"demo-{credentials.username}", "email": f"{credentials.username}@localhost", "name": f"Demo {credentials.username.title()}", "role": role}
        token = create_token(user_info["id"], user_info["email"], user_info["name"], role)
        return LoginResponse(access_token=token, token_type="bearer", expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.session_ttl_seconds), role=role, user=user_info)
    raise HTTPException(401, "Invalid credentials")

@router.get("/authorize", response_model=PKCEAuthUrlResponse)
async def authorize(redirect_uri: Optional[str] = None):
    if not settings.oidc_provider_url: raise HTTPException(503, "OIDC provider URL is not configured")
    trg = redirect_uri or settings.oidc_redirect_uri
    state, nonce, verifier = generate_state(), generate_nonce(), generate_verifier()
    _pending_states[state] = {"nonce": nonce, "verifier": verifier, "redirect_uri": trg, "created_at": datetime.now(timezone.utc)}
    try:
        disc = await fetch_discovery(settings.oidc_provider_url)
        return PKCEAuthUrlResponse(authorization_url=build_authorization_url(disc, settings.oidc_client_id, trg, state, nonce, verifier), state=state)
    except Exception as e:
        logger.error(f"Failed to build authorization URL: {e}")
        raise HTTPException(502, f"Failed to contact OIDC provider: {str(e)}")

@router.post("/callback", response_model=LoginResponse)
async def callback(cb: CallbackRequest):
    pending = _pending_states.pop(cb.state, None)
    if not pending: raise HTTPException(400, "Invalid or expired authorization state")
    try:
        disc = await fetch_discovery(settings.oidc_provider_url)
        tdata = await exchange_code(disc, settings.oidc_client_id, settings.oidc_client_secret, pending["redirect_uri"], cb.code, pending["verifier"])
        id_token = tdata.get("id_token")
        if not id_token: raise HTTPException(502, "Provider did not return an id_token")
        jwk = await fetch_jwks_jwk(disc, settings.oidc_provider_url)
        claims = await validate_id_token(id_token, jwk_to_pem(jwk), pending["nonce"], settings.oidc_audience or settings.oidc_client_id, disc.get("issuer", settings.oidc_provider_url))
        email = claims.get("email", "user@oidc.local")
        name = claims.get("name", claims.get("preferred_username", email))
        user_id = claims.get("sub", email)
        role = claims.get("roles", [settings.oidc_default_role])[0]
        user_info = {"id": user_id, "email": email, "name": name, "role": role}
        return LoginResponse(access_token=create_token(user_id, email, name, role), token_type="bearer", expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.session_ttl_seconds), role=role, user=user_info)
    except HTTPException: raise
    except Exception as e:
        logger.error(f"OIDC callback exchange failed: {e}")
        raise HTTPException(500, f"Token exchange failed: {str(e)}")

@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    return user