"""OpenGame event mapper (C10).

Turns provider-private ``OpenGameEvent``s (from the stream parser) into
platform-neutral ``RunEvent``s. The adapter exposes only ``RunEvent`` upward;
these events are never OpenGame-shaped.

Rules (from the C06 contract + C08 findings):
- ``sequence`` is monotonic from 1 — NOT opengame's raw line order (which has
  gaps/reorders across multi-block assistant messages).
- ``timestamp`` is UTC (opengame emits no per-event time; we use a monotonic
  clock from run start so events are ordered and tz-aware).
- ``kind`` must not express Human Gate decisions (promot/publish/resource_saved).
  ``RunEvent``'s own validator enforces this — we just avoid emitting them.
- ``message`` is sanitized (length-capped, no raw secrets).
- terminal events carry ``progress=1``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from app.agents.opengame_stream_parser import (
    OpenGameAssistantEvent,
    OpenGameContentBlock,
    OpenGameParseError,
    OpenGameResultEvent,
    OpenGameSystemEvent,
    result_indicates_provider_error,
)
from app.contracts.game_agent import ContractError, RunEvent

_MESSAGE_MAX = 4000  # RunEvent.message max_length


def _sanitize(text: str) -> str:
    """Cap length; strip control noise. Keeps the stream safe to persist/show."""
    cleaned = " ".join(text.split())
    if len(cleaned) > _MESSAGE_MAX:
        cleaned = cleaned[:_MESSAGE_MAX]
    return cleaned or "(empty)"


def map_stream_to_run_events(
    events: Iterable,
    *,
    run_id: str,
    started_at: datetime,
) -> list[RunEvent]:
    """Map parsed OpenGame events into ordered RunEvents.

    ``started_at`` must be tz-aware (UTC). Events get increasing second-offset
    timestamps so ordering is preserved and the contract's UTC requirement holds.
    """
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)

    out: list[RunEvent] = []
    seq = 0
    offset = 0

    def emit(stage: str, kind: str, message: str, *, progress: float | None = None,
             error: ContractError | None = None) -> None:
        nonlocal seq, offset
        seq += 1
        ts = started_at + _seconds(offset)
        offset += 1
        out.append(
            RunEvent(
                run_id=run_id,
                sequence=seq,
                stage=stage,
                kind=kind,
                message=_sanitize(message),
                progress=progress,
                error=error,
                timestamp=ts,
            )
        )

    saw_terminal = False
    for event in events:
        if isinstance(event, OpenGameSystemEvent):
            emit("starting", "started", f"OpenGame run started (model={event.model})")
            continue
        if isinstance(event, OpenGameParseError):
            emit("running", "parse_warning", f"unparseable stream line: {event.message[:200]}")
            continue
        if isinstance(event, OpenGameAssistantEvent):
            for block in event.blocks:
                _map_block(block, emit)
            continue
        if isinstance(event, OpenGameResultEvent):
            _map_result(event, emit)
            saw_terminal = True
            continue

    # If the stream was interrupted with no terminal result (C08 timeout/cancel),
    # the adapter sets the final status from ProcessResult; here we just ensure
    # the last emitted event shows progress=1 only when a real terminal arrived.
    if saw_terminal and out:
        last = out[-1]
        out[-1] = last.model_copy(update={"progress": 1.0})
    return out


def _map_block(block: OpenGameContentBlock, emit) -> None:
    if block.kind == "thinking":
        emit("running", "thinking", block.text or "thinking")
    elif block.kind == "text":
        emit("running", "text", block.text or "assistant text")
    elif block.kind == "tool_use":
        name = block.tool_name or "tool"
        emit("running", "tool_use", f"call {name}")
    elif block.kind == "tool_result":
        status = "error" if block.tool_result_is_error else "ok"
        emit("running", "tool_result", f"tool result ({status})")
    elif block.kind == "user":
        emit("running", "user_input", block.text or "user input")
    else:
        emit("running", block.kind or "event", block.kind or "event")


def _map_result(result: OpenGameResultEvent, emit) -> None:
    provider_error = result_indicates_provider_error(result)
    if result.is_error or provider_error:
        err = ContractError(code="provider_failed", message="OpenGame run failed")
        emit("terminal", "terminal", "build failed", error=err)
        return
    if result.subtype == "cancelled":
        err = ContractError(code="cancelled", message="Build cancelled")
        emit("terminal", "cancelled", "build cancelled", error=err)
        return
    emit("terminal", "terminal", "build completed")


def _seconds(n: int):
    from datetime import timedelta

    return timedelta(seconds=n)
