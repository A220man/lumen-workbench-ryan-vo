import pytest
from backend.app.api.auth import create_token, decode_token
from backend.core.security import (
    generate_state,
    generate_nonce,
    generate_verifier,
    generate_challenge,
)
from backend.core.redaction import redact


def test_pkce_helpers():
    """Verify PKCE parameters and RFC 7636 challenge generation."""
    state = generate_state()
    nonce = generate_nonce()
    verifier = generate_verifier()
    challenge = generate_challenge(verifier)

    assert len(state) >= 16
    assert len(nonce) >= 16
    assert len(verifier) >= 32
    assert len(challenge) > 0
    # S256 challenge is deterministic for the same verifier
    assert generate_challenge(verifier) == challenge


def test_redaction_removes_sensitive_data():
    """Verify credentials and secret values are masked."""
    secret_str = "Authorization: Bearer my-secret-token-12345"
    redacted = redact(secret_str)
    assert "[REDACTED]" in redacted
    assert "my-secret-token-12345" not in redacted


def test_token_creation_and_decoding():
    """Verify JWT token encoding and roundtrip claims extraction."""
    token = create_token("user-1", "user@test.local", "Test User", "operator")
    claims = decode_token(token)
    assert claims["sub"] == "user-1"
    assert claims["email"] == "user@test.local"
    assert claims["role"] == "operator"


def test_unauthenticated_requests_rejected(client):
    """Verify unauthenticated requests to protected endpoints return 401."""
    res = client.get("/api/v1/titles")
    assert res.status_code == 401

    res = client.post("/api/v1/evaluations/run", json={})
    assert res.status_code == 401


def test_role_denial_for_insufficient_privileges(client):
    """Verify role-based authorization rejects lower roles on administrative/operator endpoints."""
    # Create viewer token
    viewer_token = create_token("v-1", "viewer@test.local", "Viewer", "viewer")
    headers = {"Authorization": f"Bearer {viewer_token}"}

    # Viewer can read titles
    get_res = client.get("/api/v1/titles", headers=headers)
    assert get_res.status_code == 200

    # Viewer cannot create titles (requires operator or admin)
    post_res = client.post(
        "/api/v1/titles",
        json={"name": "Forbidden Title", "description": "Should fail", "status": "draft"},
        headers=headers,
    )
    assert post_res.status_code == 403


def test_demo_login_flow(client):
    """Verify demo login succeeds for demo accounts and issues valid bearer token."""
    res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "admin"

    # Profile endpoint using the issued token
    auth_headers = {"Authorization": f"Bearer {data['access_token']}"}
    me_res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@localhost"


def test_demo_login_invalid_credentials(client):
    """Verify demo login rejects bad credentials."""
    res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert res.status_code == 401
