"""Runtime configuration for the Lumen Workbench.

All LLM and OIDC settings are operator-configurable via environment
variables. No real credentials are committed; .env.example documents the
blank defaults.
"""
from __future__ import annotations
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.environ.get("LUMEN_DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

LOADER_ROLE = "viewer"
OPERATOR_ROLE = "operator"
ADMIN_ROLE = "admin"

ALLOWED_HOSTS = ("127.0.0.1", "localhost", "::1")


class Settings:
    def __init__(self):
        self.database_url = os.environ.get(
            "DATABASE_URL", f"sqlite:///{DATA_DIR / 'lumen.db'}"
        )
        self.secret_key = os.environ.get("LUMEN_SECRET_KEY", "dev-insecure-change-me")
        self.session_cookie_name = "lumen_session"
        self.csrf_cookie_name = "lumen_csrf"
        self.session_ttl_seconds = 8 * 3600
        self.csrf_token_ttl = self.session_ttl_seconds

        # OIDC
        self.oidc_enabled = os.environ.get("OIDC_ENABLED", "true").lower() == "true"
        self.oidc_provider_url = os.environ.get("OIDC_PROVIDER_URL", "")
        self.oidc_client_id = os.environ.get("OIDC_CLIENT_ID", "")
        self.oidc_client_secret = os.environ.get("OIDC_CLIENT_SECRET", "")
        self.oidc_redirect_uri = os.environ.get(
            "OIDC_REDIRECT_URI", "http://127.0.0.1:8000/auth/callback"
        )
        self.oidc_allowed_roles = [
            r.strip()
            for r in os.environ.get(
                "OIDC_ALLOWED_ROLES", "viewer,operator,admin"
            ).split(",")
            if r.strip()
        ]
        self.oidc_default_role = os.environ.get("OIDC_DEFAULT_ROLE", "viewer")
        self.oidc_audience = os.environ.get("OIDC_AUDIENCE", "lumen")

        # LLM (advisory, opt-in)
        self.llm_api_key = os.environ.get("LLM_API_KEY", "")
        self.llm_provider = os.environ.get("LLM_PROVIDER", "openai-compatible")
        self.llm_model = os.environ.get("LLM_MODEL", "")
        self.llm_base_url = os.environ.get("LLM_BASE_URL", "")
        self.llm_timeout_seconds = float(os.environ.get("LLM_TIMEOUT_SECONDS", "20"))
        self.llm_max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "512"))

        # Demo mode (local development only)
        self.demo_mode = os.environ.get("LUMEN_DEMO_MODE", "false").lower() == "true"
        self.demo_user_email = os.environ.get("LUMEN_DEMO_USER_EMAIL", "demo@localhost")
        self.demo_user_name = os.environ.get("LUMEN_DEMO_USER_NAME", "Demo User")
        self.demo_user_role = os.environ.get("LUMEN_DEMO_USER_ROLE", "operator")

        # Host binding
        self.host = os.environ.get("HOST", "127.0.0.1")
        self.port = int(os.environ.get("PORT", "8000"))
        self.debug = os.environ.get("LUMEN_DEBUG", "false").lower() == "true"

    @property
    def is_production(self) -> bool:
        return self.host not in ALLOWED_HOSTS

    def assert_production_ready(self) -> None:
        if self.demo_mode:
            if self.is_production:
                raise RuntimeError(
                    "LUMEN_DEMO_MODE=true is only allowed when HOST is "
                    "127.0.0.1/localhost; refuse to start in production"
                )
            return
        if not self.oidc_enabled or not self.oidc_provider_url or not self.oidc_client_id:
            raise RuntimeError(
                "OIDC provider URL and client ID are required outside demo "
                "mode; set LUMEN_DEMO_MODE=true for local development only"
            )


settings = Settings()
