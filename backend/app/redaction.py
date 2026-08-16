"""Shared secret-redaction utilities (C13).

One truth source for the patterns that scrub secrets out of provider output and
run diagnostics. ``app/repositories/runs.py`` (RunEvent persistence) and
``app/agents/`` (raw ProcessResult buffers, workspace import scanning) both
redact through ``redact_text`` so a provider line that leaks a key in stdout is
scrubbed before it can reach a Diagnostic, an event record, or audit evidence.

Patterns cover the credential shapes observed in the OpenGame spike:
- ``Bearer <token>``
- ``api[_-]?key|token|secret|password = <value>``
- ``sk-<opaque>``
"""

from __future__ import annotations

import re

REDACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)\bBearer\s+[^\s,;]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+"), "token=[REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]+\b"), "[REDACTED]"),
)


def redact_text(value: str, *, max_length: int = 4000) -> str:
    """Strip credential-shaped substrings from ``value`` then cap its length.

    Order is deliberate: redact first (so the cap never truncates a pattern mid-
    secret and leaves a fragment), then truncate. A non-string or empty input is
    returned unchanged (callers pass str).
    """
    if not value:
        return value
    sanitized = value
    for pattern, replacement in REDACTION_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized[:max_length]
