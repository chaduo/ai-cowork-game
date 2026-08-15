"""C10 — event mapper tests (OpenGameEvent -> RunEvent)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.agents.opengame_event_mapper import map_stream_to_run_events
from app.agents.opengame_stream_parser import parse_stream_json

STARTED = datetime(2026, 8, 14, 12, 0, 0, tzinfo=timezone.utc)

SUCCESS_STREAM = (
    '{"type":"system","subtype":"init","session_id":"abc","model":"kimi-k3","cwd":"D:/ws","tools":[]}\n'
    '{"type":"assistant","session_id":"abc","message":{"content":[{"type":"thinking","thinking":"plan"}]}}\n'
    '{"type":"assistant","session_id":"abc","message":{"content":[{"type":"text","text":"hi"}]}}\n'
    '{"type":"result","subtype":"success","is_error":false,"result":"done",'
    '"usage":{"input_tokens":100,"output_tokens":5}}\n'
)

API_ERROR_STREAM = (
    '{"type":"system","subtype":"init","session_id":"abc","model":"kimi-k3","cwd":"D:/ws","tools":[]}\n'
    '{"type":"result","subtype":"success","is_error":false,'
    '"result":"[API Error: Connection error.]","usage":{"input_tokens":0,"output_tokens":0}}\n'
)

INTERRUPTED_STREAM = (
    '{"type":"system","subtype":"init","session_id":"abc","model":"kimi-k3","cwd":"D:/ws","tools":[]}\n'
    '{"type":"assistant","session_id":"abc","message":{"content":[{"type":"tool_use","id":"t1","name":"write_file","input":{}}]}}\n'
)


def _events(stream: str):
    return map_stream_to_run_events(parse_stream_json(stream), run_id="run-1", started_at=STARTED)


def test_sequence_is_monotonic_from_1() -> None:
    events = _events(SUCCESS_STREAM)
    assert [e.sequence for e in events] == list(range(1, len(events) + 1))


def test_timestamps_are_utc() -> None:
    events = _events(SUCCESS_STREAM)
    for e in events:
        assert e.timestamp.tzinfo is not None
        assert e.timestamp.utcoffset() is not None


def test_terminal_event_has_progress_one() -> None:
    events = _events(SUCCESS_STREAM)
    assert events[-1].progress == 1.0
    assert events[-1].stage == "terminal"


def test_kinds_contain_no_human_gate_tokens() -> None:
    events = _events(SUCCESS_STREAM)
    for e in events:
        # RunEvent's validator would have raised on construction if a gate token
        # were used; being here means none slipped through. Double-check explicitly.
        low = e.kind.lower().replace("-", "_")
        for token in ("promot", "publish", "resource_saved", "save_resource"):
            assert token not in low


def test_provider_error_mapped_to_terminal_with_error() -> None:
    events = _events(API_ERROR_STREAM)
    last = events[-1]
    assert last.stage == "terminal"
    assert last.error is not None
    assert last.error.code == "provider_failed"


def test_interrupted_stream_has_no_progress_one() -> None:
    """C08 timeout/cancel: no terminal result → last event must NOT claim progress=1."""
    events = _events(INTERRUPTED_STREAM)
    assert events[-1].progress != 1.0


def test_message_sanitized_and_nonempty() -> None:
    events = _events(SUCCESS_STREAM)
    for e in events:
        assert e.message  # non-empty
        assert len(e.message) <= 4000
