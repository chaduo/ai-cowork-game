import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from app.agents.game_design_planner import GameDesignProviderError, GameDesignProviderNotConfigured
from app.agents.openai_game_design_planner import OpenAICompatibleGameDesignPlanner
from app.contracts.design import CreatorGameDesignDraft, DesignReadiness
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


def test_provider_parses_json_surrounded_by_explanatory_text() -> None:
    content = (
        "我先整理这一轮结果：\n"
        '{"draft":{"summary":{"title":"灯塔","summary":"探索灯塔","highlights":[],"core_loop":[],"progression":[]}},'
        '"next_question":{"id":"exploration-core_experience","prompt":"玩家最想获得什么体验？","choices":[]}}\n'
        "以上只是一轮设计建议。"
    )

    turn = _provider(content).plan_turn("project", _draft(), BrainstormInput(action="start"))

    assert turn.draft.original_idea == "一个探索灯塔的游戏"
    assert turn.draft.summary.summary == "探索灯塔"
    assert turn.next_question is not None


def test_provider_accepts_multisegment_text_content_and_partial_draft() -> None:
    content = [
        {"type": "text", "text": '{"draft":{"project_title":"新的灯塔"},'},
        {
            "type": "text",
            "text": '"next_question":{"id":"exploration-goal","prompt":"玩家要达成什么目标？","choices":[]}}',
        },
    ]

    planner = OpenAICompatibleGameDesignPlanner(
        base_url="https://example.test/v1",
        api_key="secret",
        model="test-model",
        opener=lambda request, timeout: _Response({"choices": [{"message": {"content": content}}]}),
    )

    turn = planner.plan_turn("project", _draft(), BrainstormInput(action="start"))

    assert turn.draft.project_title == "新的灯塔"
    assert turn.draft.original_idea == "一个探索灯塔的游戏"
    assert turn.next_question is not None
    assert turn.next_question.id == "exploration-goal"


def test_provider_reads_reasoning_content_when_message_content_is_empty() -> None:
    content = '{"next_question":{"id":"exploration-goal","prompt":"玩家下一步做什么？","choices":[]}}'
    planner = OpenAICompatibleGameDesignPlanner(
        base_url="https://example.test/v1",
        api_key="secret",
        model="kimi-k3",
        opener=lambda request, timeout: _Response(
            {"choices": [{"message": {"content": "", "reasoning_content": content}}]}
        ),
    )

    turn = planner.plan_turn("project", _draft(), BrainstormInput(action="answer", question_id="q1", answer="探索"))

    assert turn.next_question is not None
    assert turn.next_question.id == "exploration-goal"


def test_provider_normalizes_follow_up_question_options_with_nulls() -> None:
    content = (
        '{"draft":{"summary":{"title":"灯塔","summary":"探索灯塔","highlights":null,"core_loop":[],"progression":[]}},'
        '"next_question":{"id":"exploration-goal","prompt":"玩家要达成什么目标？",'
        '"options":[{"id":"repair","label":"修复灯塔","description":null,"recommended":"false"}]}}'
    )

    turn = _provider(content).plan_turn("project", _draft(), BrainstormInput(action="answer", question_id="exploration-core_experience", answer="探索和发现"))

    assert turn.next_question is not None
    assert turn.next_question.choices[0].title == "修复灯塔"
    assert turn.next_question.choices[0].description == ""
    assert turn.next_question.choices[0].recommended is False


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


def test_provider_prompt_requests_incremental_brainstorm_payload() -> None:
    captured: dict = {}

    def opener(request, timeout):
        captured.update(json.loads(request.data.decode()))
        return _Response(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"next_question":{"id":"q","prompt":"下一步是什么？","choices":[]}}'
                        }
                    }
                ]
            }
        )

    planner = OpenAICompatibleGameDesignPlanner(
        base_url="https://example.test/v1",
        api_key="secret",
        model="test-model",
        opener=opener,
    )
    planner.plan_turn("project", _draft(), BrainstormInput(action="start"))

    system_prompt = captured["messages"][0]["content"]
    assert "draft 可省略" in system_prompt
    assert "不要输出 decisions/readiness/original_idea" in system_prompt
    assert '"next_question":{"id":"...","prompt":"..."' in system_prompt


def test_provider_input_names_the_next_blocking_decision() -> None:
    captured: dict = {}

    def opener(request, timeout):
        captured.update(json.loads(request.data.decode()))
        return _Response(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"next_question":{"id":"q5_completion","prompt":"这一局怎样结束？","choices":[]}}'
                        }
                    }
                ]
            }
        )

    planner = OpenAICompatibleGameDesignPlanner(
        base_url="https://example.test/v1",
        api_key="secret",
        model="test-model",
        opener=opener,
    )
    draft = _draft().model_copy(
        update={
            "readiness": DesignReadiness(
                status="not_ready",
                blockers=[],
                unresolved_decisions=["completion"],
                first_playable_ready=False,
                full_gdd_ready=False,
            )
        }
    )

    planner.plan_turn("project", draft, BrainstormInput(action="continue"))

    provider_input = json.loads(captured["messages"][1]["content"])
    assert provider_input["next_blocking_decision"] == "completion"


def test_kimi_provider_request_uses_only_supported_completion_fields() -> None:
    captured: list[dict] = []

    def opener(request, timeout):
        captured.append(json.loads(request.data.decode()))
        return _Response({"choices": [{"message": {"content": "{}"}}]})

    planner = OpenAICompatibleGameDesignPlanner(
        base_url="https://example.test/v1",
        api_key="secret",
        model="kimi-k3",
        opener=opener,
    )
    with pytest.raises(GameDesignProviderError):
        planner.plan_turn("project", _draft(), BrainstormInput(action="start"))

    assert "thinking" not in captured[0]
    assert captured[0]["stream"] is False
    assert captured[0]["max_tokens"] >= 2048
    assert captured[0]["temperature"] == 1


def test_provider_rejects_malformed_json() -> None:
    with pytest.raises(GameDesignProviderError, match="invalid brainstorm JSON"):
        _provider("not json").plan_turn("project", _draft(), BrainstormInput(action="start"))


def test_provider_repairs_one_invalid_turn_response() -> None:
    responses = [
        _Response({"choices": [{"message": {"content": "我先想想，但没有按 JSON 返回"}}]}),
        _Response(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"next_question":{"id":"q2","prompt":"玩家下一步做什么？","choices":[]}}'
                        }
                    }
                ]
            }
        ),
    ]
    calls: list[dict] = []

    def opener(request, timeout):
        calls.append(json.loads(request.data.decode()))
        return responses.pop(0)

    planner = OpenAICompatibleGameDesignPlanner(
        base_url="https://example.test/v1",
        api_key="secret",
        model="test-model",
        opener=opener,
    )

    turn = planner.plan_turn("project", _draft(), BrainstormInput(action="answer", question_id="q1", answer="探索"))

    assert len(calls) == 2
    assert "无法解析" in calls[1]["messages"][0]["content"]
    assert turn.next_question is not None
    assert turn.next_question.id == "q2"


def test_provider_accepts_nested_output_content_segments() -> None:
    responses = [
        _Response(
            {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {
                                    "type": "output_text",
                                    "content": '{"next_question":{"id":"q2","prompt":"玩家下一步做什么？","choices":[]}}',
                                }
                            ]
                        }
                    }
                ]
            }
        ),
    ]
    calls: list[dict] = []

    def opener(request, timeout):
        calls.append(json.loads(request.data.decode()))
        return responses.pop(0)

    planner = OpenAICompatibleGameDesignPlanner(
        base_url="https://example.test/v1",
        api_key="secret",
        model="test-model",
        opener=opener,
    )

    turn = planner.plan_turn("project", _draft(), BrainstormInput(action="continue"))

    assert len(calls) == 1
    assert turn.next_question is not None
    assert turn.next_question.id == "q2"


def test_provider_retries_one_transient_timeout() -> None:
    calls = 0

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("provider response was slow")
        return _Response(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"next_question":{"id":"q2","prompt":"玩家下一步做什么？","choices":[]}}'
                        }
                    }
                ]
            }
        )

    planner = OpenAICompatibleGameDesignPlanner(
        base_url="https://example.test/v1",
        api_key="secret",
        model="test-model",
        opener=opener,
    )

    turn = planner.plan_turn("project", _draft(), BrainstormInput(action="continue"))

    assert calls == 2
    assert turn.next_question is not None
    assert turn.next_question.id == "q2"


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
