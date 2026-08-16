"""OpenGame stream-json parser (C10).

Parses opengame's NDJSON ``-o stream-json`` output (one JSON object per line)
into provider-private ``OpenGameEvent`` values. These are consumed by the event
mapper, which turns them into platform-neutral ``RunEvent``s. Nothing here is
imported by upper layers — the adapter only exposes ``GameBuildResult``/``RunEvent``.

Stream-json shape (verified against the C08 fixtures):
- ``{"type":"system","subtype":"init",...}`` — run metadata (tools, model, cwd, session_id).
- ``{"type":"assistant","message":{"content":[...]}}`` — agent output; content blocks
  are ``thinking`` / ``text`` / ``tool_use`` / ``tool_result`` / ``user``.
- ``{"type":"result","subtype":"success"|"cancelled",...}`` — terminal; carries
  ``is_error`` (UNRELIABLE per C08), ``result`` text, ``usage``, ``duration_ms``.

Critical: the top-level ``result.is_error`` is NOT the same as a ``tool_result``
content block's ``is_error``. The success fixture has 3 ``is_error:true`` that come
from tool_result blocks, while the top-level result is ``is_error:false``. This
parser keeps them separate so the adapter never conflates them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class OpenGameSystemEvent:
    subtype: str
    session_id: str | None
    model: str | None
    cwd: str | None
    tools: list[str] = field(default_factory=list)


@dataclass
class OpenGameContentBlock:
    # kind ∈ thinking / text / tool_use / tool_result / user
    kind: str
    text: str = ""  # for thinking/text/user
    tool_name: str | None = None  # for tool_use
    tool_input: Any | None = None  # for tool_use
    tool_use_id: str | None = None  # for tool_use / tool_result
    tool_result_content: str = ""  # for tool_result
    tool_result_is_error: bool = False  # tool_result block's own is_error (NOT top-level)


@dataclass
class OpenGameAssistantEvent:
    session_id: str | None
    model: str | None
    blocks: list[OpenGameContentBlock] = field(default_factory=list)


@dataclass
class OpenGameResultEvent:
    subtype: str  # "success" / "cancelled" / ...
    # ⚠ UNRELIABLE: opengame wraps provider errors as is_error=false + subtype=success.
    # The adapter must NOT use this alone to decide success.
    is_error: bool
    result_text: str
    usage_input_tokens: int
    usage_output_tokens: int
    duration_ms: int | None
    num_turns: int | None


# A parsed line is exactly one of these, or a parse-error diagnostic.
@dataclass
class OpenGameParseError:
    raw_line: str
    message: str


OpenGameEvent = OpenGameSystemEvent | OpenGameAssistantEvent | OpenGameResultEvent | OpenGameParseError


def parse_stream_json_line(line: str) -> OpenGameEvent | None:
    """Parse one NDJSON line. Returns None for blank lines.

    Malformed JSON → OpenGameParseError (does not raise; the stream stays usable).
    """
    stripped = line.strip()
    if not stripped:
        return None
    try:
        obj = json.loads(stripped)
    except json.JSONDecodeError as exc:
        return OpenGameParseError(raw_line=stripped, message=str(exc))
    if not isinstance(obj, dict) or "type" not in obj:
        return OpenGameParseError(raw_line=stripped, message="missing 'type'")

    type_ = obj["type"]
    if type_ == "system":
        return _parse_system(obj)
    if type_ == "assistant":
        return _parse_assistant(obj)
    if type_ == "user":
        # OpenGame emits tool results as top-level user messages in some
        # stream-json versions; they use the same message/content shape as an
        # assistant event and are mapped to provider-neutral tool progress.
        return _parse_assistant(obj)
    if type_ == "result":
        return _parse_result(obj)
    return OpenGameParseError(raw_line=stripped, message=f"unknown type {type_!r}")


def parse_stream_json(text: str) -> list[OpenGameEvent]:
    """Parse a whole stream-json blob (NDJSON) into events, in order."""
    events: list[OpenGameEvent] = []
    for line in text.splitlines():
        event = parse_stream_json_line(line)
        if event is not None:
            events.append(event)
    return events


def _parse_system(obj: dict[str, Any]) -> OpenGameSystemEvent:
    return OpenGameSystemEvent(
        subtype=obj.get("subtype", ""),
        session_id=obj.get("session_id"),
        model=obj.get("model"),
        cwd=obj.get("cwd"),
        tools=list(obj.get("tools") or []),
    )


def _parse_assistant(obj: dict[str, Any]) -> OpenGameAssistantEvent:
    message = obj.get("message") or {}
    content = message.get("content") or []
    blocks: list[OpenGameContentBlock] = []
    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict) or "type" not in block:
                continue
            kind = block["type"]
            # thinking blocks put text under "thinking"; text/user blocks use "text".
            block_text = str(block.get("text", block.get("thinking", "")))
            blocks.append(
                OpenGameContentBlock(
                    kind=kind,
                    text=block_text,
                    tool_name=block.get("name"),
                    tool_input=block.get("input"),
                    tool_use_id=block.get("id"),
                    tool_result_content=str(block.get("content", "")),
                    tool_result_is_error=bool(block.get("is_error", False)),
                )
            )
    return OpenGameAssistantEvent(
        session_id=obj.get("session_id") or message.get("session_id"),
        model=message.get("model"),
        blocks=blocks,
    )


def _parse_result(obj: dict[str, Any]) -> OpenGameResultEvent:
    usage = obj.get("usage") or {}
    return OpenGameResultEvent(
        subtype=obj.get("subtype", ""),
        is_error=bool(obj.get("is_error", False)),
        result_text=str(obj.get("result", "")),
        usage_input_tokens=int(usage.get("input_tokens", 0) or 0),
        usage_output_tokens=int(usage.get("output_tokens", 0) or 0),
        duration_ms=obj.get("duration_ms"),
        num_turns=obj.get("num_turns"),
    )


# Marker the adapter checks for: opengame embeds provider errors as a result text
# that starts with this, even when is_error=false (C08 failure fixture).
API_ERROR_MARKER = "[API Error:"


def result_indicates_provider_error(result: OpenGameResultEvent) -> bool:
    """True when the top-level result actually reports a provider error despite
    opengame possibly labelling it success. Per C08: error text marker OR zero
    input tokens (no real model call happened)."""
    return API_ERROR_MARKER in result.result_text or result.usage_input_tokens == 0
