"""C10 — stream-json parser tests (inline C08 fixture samples, no file deps)."""

from __future__ import annotations

from app.agents.opengame_stream_parser import (
    OpenGameAssistantEvent,
    OpenGameParseError,
    OpenGameResultEvent,
    OpenGameSystemEvent,
    parse_stream_json,
    parse_stream_json_line,
    result_indicates_provider_error,
)

# Minimal real samples drawn from the C08 fixtures (success/failure/timeout).

SYSTEM_INIT = (
    '{"type":"system","subtype":"init","session_id":"abc","cwd":"D:/ws",'
    '"tools":["task","read_file","write_file"],"model":"kimi-k3","permission_mode":"yolo"}'
)

ASSISTANT_THINKING = (
    '{"type":"assistant","session_id":"abc","message":{"id":"m1","type":"message",'
    '"role":"assistant","model":"kimi-k3","content":[{"type":"thinking",'
    '"thinking":"plan the game","signature":""}]}}'
)

ASSISTANT_TOOL_USE = (
    '{"type":"assistant","session_id":"abc","message":{"id":"m2","type":"message",'
    '"role":"assistant","model":"kimi-k3","content":[{"type":"tool_use","id":"t1",'
    '"name":"write_file","input":{"path":"index.html","content":"hi"}}]}}'
)

# tool_result block with its OWN is_error=true (a tool failed). This must NOT be
# confused with the top-level result is_error.
ASSISTANT_TOOL_RESULT_ERROR = (
    '{"type":"assistant","session_id":"abc","message":{"id":"m3","type":"message",'
    '"role":"assistant","model":"kimi-k3","content":[{"type":"tool_result",'
    '"tool_use_id":"t1","content":"boom","is_error":true}]}}'
)

RESULT_SUCCESS = (
    '{"type":"result","subtype":"success","session_id":"abc","is_error":false,'
    '"duration_ms":1000,"num_turns":1,"result":"done",'
    '"usage":{"input_tokens":100,"output_tokens":5}}'
)

# C08 failure fixture: provider error wrapped as success, is_error=false, usage 0.
RESULT_API_ERROR = (
    '{"type":"result","subtype":"success","session_id":"abc","is_error":false,'
    '"result":"[API Error: Connection error.]","num_turns":1,'
    '"usage":{"input_tokens":0,"output_tokens":0}}'
)


def test_parse_system_init() -> None:
    event = parse_stream_json_line(SYSTEM_INIT)
    assert isinstance(event, OpenGameSystemEvent)
    assert event.subtype == "init"
    assert event.session_id == "abc"
    assert event.model == "kimi-k3"
    assert event.cwd == "D:/ws"
    assert event.tools == ["task", "read_file", "write_file"]


def test_parse_assistant_thinking_block() -> None:
    event = parse_stream_json_line(ASSISTANT_THINKING)
    assert isinstance(event, OpenGameAssistantEvent)
    assert len(event.blocks) == 1
    assert event.blocks[0].kind == "thinking"
    assert event.blocks[0].text == "plan the game"


def test_parse_assistant_tool_use_block() -> None:
    event = parse_stream_json_line(ASSISTANT_TOOL_USE)
    assert isinstance(event, OpenGameAssistantEvent)
    assert event.blocks[0].kind == "tool_use"
    assert event.blocks[0].tool_name == "write_file"
    assert event.blocks[0].tool_use_id == "t1"


def test_tool_result_block_is_error_is_not_top_level() -> None:
    """A tool_result block's is_error must stay on the block, not leak upward."""
    event = parse_stream_json_line(ASSISTANT_TOOL_RESULT_ERROR)
    assert isinstance(event, OpenGameAssistantEvent)
    block = event.blocks[0]
    assert block.kind == "tool_result"
    assert block.tool_result_is_error is True  # the BLOCK's is_error
    assert block.tool_result_content == "boom"


def test_parse_result_success() -> None:
    event = parse_stream_json_line(RESULT_SUCCESS)
    assert isinstance(event, OpenGameResultEvent)
    assert event.subtype == "success"
    assert event.is_error is False
    assert event.usage_input_tokens == 100
    assert event.result_text == "done"


def test_provider_error_wrapped_as_success_is_detected() -> None:
    """C08 failure finding: top-level is_error=false but the result is actually an
    API error. The adapter must not trust is_error alone."""
    event = parse_stream_json_line(RESULT_API_ERROR)
    assert isinstance(event, OpenGameResultEvent)
    assert event.is_error is False  # opengame says success...
    assert result_indicates_provider_error(event) is True  # ...but it's not


def test_malformed_line_returns_parse_error_not_raise() -> None:
    event = parse_stream_json_line("not json at all")
    assert isinstance(event, OpenGameParseError)
    # A stream with one bad line still parses the rest.
    events = parse_stream_json(f"{SYSTEM_INIT}\nbroken\n{RESULT_SUCCESS}\n")
    assert len(events) == 3
    assert isinstance(events[0], OpenGameSystemEvent)
    assert isinstance(events[1], OpenGameParseError)
    assert isinstance(events[2], OpenGameResultEvent)


def test_blank_lines_skipped() -> None:
    events = parse_stream_json(f"\n{SYSTEM_INIT}\n\n")
    assert len(events) == 1


def test_stream_without_result_has_no_result_event() -> None:
    """C08 timeout/cancel fixtures: interrupted streams end with no result event."""
    events = parse_stream_json(f"{SYSTEM_INIT}\n{ASSISTANT_THINKING}\n")
    assert not any(isinstance(e, OpenGameResultEvent) for e in events)
