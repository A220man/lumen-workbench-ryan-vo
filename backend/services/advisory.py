"""Advisory explanations grounded in actual records.

LLM explanations are opt-in and clearly labeled. They are grounded in the
import analysis and title status history; if the provider fails, the error
is surfaced (never a fabricated successful response).
"""
from __future__ import annotations

from typing import Optional

from ..core.config import settings
from ..core.redaction import redact
from .provider import LLMProvider, LLMError


_DEFAULT_BASE_URLS = {"anthropic": "https://api.anthropic.com", "gemini": "https://generativelanguage.googleapis.com"}
_DEFAULT_MODELS = {"anthropic": "claude-3-5-sonnet-20241022", "gemini": "gemini-1.5-flash"}


def build_advisor(system: Optional[str] = None) -> Optional[LLMProvider]:
    """Build an LLM provider from operator settings, or None if disabled."""
    if not settings.llm_api_key:
        return None
    provider = settings.llm_provider
    base_url = settings.llm_base_url or _DEFAULT_BASE_URLS.get(provider, "https://api.openai.com")
    model = settings.llm_model or _DEFAULT_MODELS.get(provider, "gpt-4o-mini")
    return LLMProvider(provider, model, base_url, settings.llm_api_key, timeout=int(settings.llm_timeout_seconds))


SYSTEM_PROMPT = (
    "You are an advisory engine for a PS5-to-Linux/Windows porting workbench. "
    "Explain import-resolution results and startup-stop patterns. "
    "Never invent symbols or titles not present in the provided records. "
    "Keep explanations short and grounded."
)


async def explain_imports(report, advisor: Optional[LLMProvider]) -> str:
    """Return an advisory explanation of an import-resolution report."""
    if advisor is None:
        return "LLM advisory disabled: set LLM_API_KEY to enable explanations."
    prompt = (
        "Grounded records:\n"
        f"source={report.source_name}\n"
        f"needed_libraries={report.needed_libraries}\n"
        f"resolved={report.resolved_count} unresolved={report.unresolved_count} "
        f"missing_modules={report.missing_module_count}\n"
        f"blockers={report.blockers}\n"
        "Explain in two sentences what these results mean for porting this title."
    )
    try:
        text = await advisor.complete(SYSTEM_PROMPT, prompt)
    except LLMError as e:
        return f"LLM provider error: {redact(str(e))}"
    except Exception as e:
        return f"LLM provider error: {redact(str(e))}"
    return f"[ADVISORY] {text.strip()}"


async def generate_advisory(report) -> str:
    """Build an advisor from operator settings and explain an import report.

    Returns a grounded advisory explanation, or a disabled notice when no
    LLM_API_KEY is configured. Provider errors are surfaced (never fabricated).
    """
    advisor = build_advisor()
    return await explain_imports(report, advisor)