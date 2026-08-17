import json
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
