import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from app.agents.game_design_planner import GameDesignProviderError, GameDesignProviderNotConfigured
from app.agents.openai_game_design_planner import OpenAICompatibleGameDesignPlanner
from app.contracts.design import CreatorGameDesignDraft
from app.contracts.design_brainstorm import BrainstormInput


class _Response:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def _draft() -> CreatorGameDesignDraft:
    return CreatorGameDesignDraft(
        original_idea="一个探索灯塔的游戏",
        project_title="灯塔",
        scenario_id="generic",
        summary={"title": "灯塔", "summary": "探索灯塔", "highlights": [], "core_loop": [], "progression": []},
    )


def _provider(content: str):
    return OpenAICompatibleGameDesignPlanner(
        base_url="https://example.test/v1",
        api_key="secret",
        model="test-model",
        opener=lambda request, timeout: _Response(
            {"choices": [{"message": {"content": content}}]}
        ),
    )


def test_provider_parses_fenced_json_without_leaking_credentials() -> None:
    content = """```json
    {"draft":{"original_idea":"一个探索灯塔的游戏","project_title":"灯塔","scenario_id":"generic","summary":{"title":"灯塔","summary":"探索灯塔","highlights":[],"core_loop":[],"progression":[]},"decisions":[],"clarification":{"question_index":0,"status":"clarifying","custom_input":""},"readiness":{"status":"not_ready","blockers":[],"unresolved_decisions":[]}},"next_question":{"id":"exploration-core_experience","prompt":"玩家最想获得什么体验？","choices":[]}}
    ```"""

    turn = _provider(content).plan_turn("project", _draft(), BrainstormInput(action="start"))

    assert turn.next_question is not None
    assert turn.next_question.id == "exploration-core_experience"


def test_provider_uses_compatible_json_instruction_without_response_format_extension() -> None:
    captured: dict = {}

    def opener(request, timeout):
        captured.update(json.loads(request.data.decode()))
        return _Response({"choices": [{"message": {"content": "{}"}}]})

    planner = OpenAICompatibleGameDesignPlanner(
        base_url="https://example.test/v1",
        api_key="secret",
        model="test-model",
        opener=opener,
    )
    with pytest.raises(GameDesignProviderError):
        planner.plan_turn("project", _draft(), BrainstormInput(action="start"))

    assert "response_format" not in captured


def test_kimi_provider_request_disables_thinking_and_sets_completion_mode() -> None:
    captured: dict = {}

    def opener(request, timeout):
        captured.update(json.loads(request.data.decode()))
        return _Response({"choices": [{"message": {"content": "{}"}}]})

    planner = OpenAICompatibleGameDesignPlanner(
        base_url="https://example.test/v1",
        api_key="secret",
        model="kimi-k3",
        opener=opener,
    )
    with pytest.raises(GameDesignProviderError):
        planner.plan_turn("project", _draft(), BrainstormInput(action="start"))

    assert captured["thinking"] == {"type": "disabled"}
    assert captured["stream"] is False
    assert captured["max_tokens"] >= 2048


def test_provider_rejects_malformed_json() -> None:
    with pytest.raises(GameDesignProviderError, match="invalid brainstorm JSON"):
        _provider("not json").plan_turn("project", _draft(), BrainstormInput(action="start"))


def test_provider_requires_credentials() -> None:
    planner = OpenAICompatibleGameDesignPlanner(base_url=None, api_key=None, model="test")

    with pytest.raises(GameDesignProviderNotConfigured):
        planner.plan_turn("project", _draft(), BrainstormInput(action="start"))

def test_provider_maps_http_error_to_safe_error() -> None:
    def fail(request, timeout):
        raise HTTPError(request.full_url, 401, "unauthorized", {}, None)

    planner = OpenAICompatibleGameDesignPlanner(base_url="https://example.test", api_key="secret", model="test", opener=fail)

    with pytest.raises(GameDesignProviderError, match="HTTP 401"):
        planner.plan_turn("project", _draft(), BrainstormInput(action="start"))


def test_provider_includes_sanitized_http_error_detail() -> None:
    def fail(request, timeout):
        body = b'{"error":{"message":"unsupported field sk-secret-value"}}'
        raise HTTPError(request.full_url, 400, "bad request", {}, BytesIO(body))

    planner = OpenAICompatibleGameDesignPlanner(base_url="https://example.test", api_key="secret", model="test", opener=fail)

    with pytest.raises(GameDesignProviderError) as raised:
        planner.plan_turn("project", _draft(), BrainstormInput(action="start"))

    assert "unsupported field" in str(raised.value)
    assert "sk-secret-value" not in str(raised.value)
