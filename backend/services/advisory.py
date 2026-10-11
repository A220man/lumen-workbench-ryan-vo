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


def build_advisor(system: Optional[str] = None) -> Optional[LLMProvider]:
    """Build an LLM provider from operator settings, or None if disabled."""
    if not settings.llm_api_key:
        return None
    provider = settings.llm_provider
    model = settings.llm_model
    base_url = settings.llm_base_url
    if not base_url:
        if provider == "openai-compatible":
            base_url = "https://api.openai.com"
        elif provider == "anthropic":
            base_url = "https://api.anthropic.com"
        elif provider == "gemini":
            base_url = "https://generativelanguage.googleapis.com"
        else:
            base_url = "https://api.openai.com"
    if not model:
        if provider == "openai-compatible":
            model = "gpt-4o-mini"
        elif provider == "anthropic":
            model = "claude-3-5-sonnet-20241022"
        elif provider == "gemini":
            model = "gemini-1.5-flash"
        else:
            model = "gpt-4o-mini"
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