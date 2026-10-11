"""PKCE / OIDC protocol helpers.

Only the token-shaped prefix is redacted; the rest of the error message
(e.g. which endpoint was hit) is preserved for debugging.
"""
from __future__ import annotations

import re
TOKEN_PATTERN = re.compile(
    r"(?i)"
    r"(authorization[:\s]+bearer\s+|api[_-]?key[:=\s]+|bearer[:=\s]+|token[:=\s]+|password[:=\s]+|secret[:=\s]+)"
    r"([A-Za-z0-9_\-\.]{8,})"
)


def redact(text: str) -> str:
    """Redact any credential-like ``key: value`` occurrences."""
    if not text:
        return text
    return TOKEN_PATTERN.sub(r"\1[REDACTED]", text)