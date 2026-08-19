import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.agents.openai_game_design_planner import OpenAICompatibleGameDesignPlanner
from app.agents.game_design_planner import GameDesignProviderError
from app.contracts.design import BrainstormQuestion
from app.contracts.design_brainstorm import BrainstormTurn


def _client(database_url: str, *, planner=None) -> TestClient:
    return TestClient(create_app(Settings(database_url=database_url, game_design_provider="fake"), game_design_planner=planner))


def _project(client: TestClient, *, key: str, idea: str) -> dict:
    return client.post(
        "/api/v1/projects",
        headers={"Idempotency-Key": key},
        json={"name": key, "original_idea": idea},
    ).json()


def test_brainstorm_start_is_idea_aware_and_restores_current_question(isolated_database) -> None:
    client = _client(str(isolated_database.url))
    first = _project(client, key="garden", idea="经营一个小农场，种植作物并扩大土地")
    second = _project(client, key="mystery", idea="探索废弃灯塔，寻找失踪船员留下的线索")

    first_turn = client.post(f"/api/v1/projects/{first['id']}/design/brainstorm", json={"action": "start"})
    second_turn = client.post(f"/api/v1/projects/{second['id']}/design/brainstorm", json={"action": "start"})

    assert first_turn.status_code == 200
    assert second_turn.status_code == 200
    first_question = first_turn.json()["next_question"]
    second_question = second_turn.json()["next_question"]
    assert first_question["id"] != second_question["id"]

    restored = _client(str(isolated_database.url)).get(f"/api/v1/projects/{first['id']}/design")
    assert restored.status_code == 200
    assert restored.json()["draft"]["clarification"]["current_question"]["id"] == first_question["id"]


def test_brainstorm_answer_is_saved_before_next_turn(isolated_database) -> None:
    client = _client(str(isolated_database.url))
    project = _project(client, key="coffee", idea="经营一家咖啡店并认识每天来店里的客人")
    started = client.post(f"/api/v1/projects/{project['id']}/design/brainstorm", json={"action": "start"}).json()
    question = started["next_question"]
    choice = question["choices"][0]

    answered = client.post(
        f"/api/v1/projects/{project['id']}/design/brainstorm",
        json={"action": "answer", "question_id": question["id"], "answer_id": choice["id"], "answer": choice["title"]},
    )

    assert answered.status_code == 200
    assert answered.json()["draft"]["decisions"][0]["provenance"] == "user_confirmed"
    assert answered.json()["next_question"] is not None


def test_brainstorm_free_text_is_persisted_as_user_decision(isolated_database) -> None:
    client = _client(str(isolated_database.url))
    project = _project(client, key="free-text", idea="一个关于修复旧火车站的游戏")
    started = client.post(f"/api/v1/projects/{project['id']}/design/brainstorm", json={"action": "start"}).json()
    question_id = started["next_question"]["id"]

    answered = client.post(
        f"/api/v1/projects/{project['id']}/design/brainstorm",
        json={"action": "free_text", "question_id": question_id, "answer": "我希望玩家通过修理和倾听乘客故事推进。"},
    )

    assert answered.status_code == 200
    decision = answered.json()["draft"]["decisions"][0]
    assert decision["answer"] == "我希望玩家通过修理和倾听乘客故事推进。"
    assert decision["answer_id"] == "free-text"


def test_unconfigured_brainstorm_provider_fails_closed(isolated_database) -> None:
    client = TestClient(create_app(Settings(database_url=str(isolated_database.url), game_design_provider="none")))
    project = _project(client, key="unconfigured", idea="一个还没有明确玩法的游戏")

    response = client.post(f"/api/v1/projects/{project['id']}/design/brainstorm", json={"action": "start"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "game_design_provider_not_configured"


def test_first_playable_readiness_allows_confirm_after_five_core_decisions(isolated_database) -> None:
    client = _client(str(isolated_database.url))
    project = _project(client, key="ready", idea="一个探索灯塔并修复旧设备的小游戏")
    turn = client.post(f"/api/v1/projects/{project['id']}/design/brainstorm", json={"action": "start"}).json()

    for _ in range(5):
        question = turn["next_question"]
        assert question is not None
        choice = question["choices"][0]
        turn = client.post(
            f"/api/v1/projects/{project['id']}/design/brainstorm",
            json={"action": "answer", "question_id": question["id"], "answer_id": choice["id"], "answer": choice["title"]},
        ).json()

    assert turn["readiness"]["status"] == "ready"
    assert turn["readiness"]["first_playable_ready"] is True
    assert turn["readiness"]["full_gdd_ready"] is False
    assert turn["next_question"] is None
    confirmed = client.post(f"/api/v1/projects/{project['id']}/design/confirm")
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"


def test_real_brainstorm_route_recovers_one_invalid_follow_up_response(isolated_database) -> None:
    class Response:
        def __init__(self, payload: dict):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(self.payload).encode()

    responses = [
        Response(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"next_question":{"id":"q1","prompt":"玩家最想获得什么体验？","choices":[]}}'
                        }
                    }
                ]
            }
        ),
        Response({"choices": [{"message": {"content": "不是 JSON"}}]}),
        Response(
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

    def opener(request, timeout):
        return responses.pop(0)

    planner = OpenAICompatibleGameDesignPlanner(
        base_url="https://example.test/v1",
        api_key="secret",
        model="test-model",
        opener=opener,
    )
    client = _client(str(isolated_database.url), planner=planner)
    project = _project(client, key="real-brainstorm-route", idea="探索一座旧灯塔")

    first = client.post(f"/api/v1/projects/{project['id']}/design/brainstorm", json={"action": "start"})
    assert first.status_code == 200
    question = first.json()["next_question"]
    second = client.post(
        f"/api/v1/projects/{project['id']}/design/brainstorm",
        json={"action": "answer", "question_id": question["id"], "answer": "探索和发现"},
    )

    assert second.status_code == 200
    assert second.json()["next_question"]["id"] == "q2"


def test_brainstorm_failure_commits_user_decision_for_continue_retry(isolated_database) -> None:
    class Planner:
        def __init__(self):
            self.calls = 0

        def plan_turn(self, project_id, draft, user_input):
            self.calls += 1
            if self.calls == 2:
                raise GameDesignProviderError("invalid brainstorm JSON (invalid_response_shape)")
            from app.agents.fake_game_design_planner import FakeGameDesignPlanner
            return FakeGameDesignPlanner().plan_turn(project_id, draft, user_input)

    planner = Planner()
    client = _client(str(isolated_database.url), planner=planner)
    project = _project(client, key="persist-before-retry", idea="探索一座旧灯塔")
    started = client.post(f"/api/v1/projects/{project['id']}/design/brainstorm", json={"action": "start"}).json()
    question = started["next_question"]

    failed = client.post(
        f"/api/v1/projects/{project['id']}/design/brainstorm",
        json={"action": "answer", "question_id": question["id"], "answer": "探索和发现"},
    )
    assert failed.status_code == 502
    saved = client.get(f"/api/v1/projects/{project['id']}/design").json()["draft"]
    assert saved["decisions"][0]["answer"] == "探索和发现"

    retried = client.post(f"/api/v1/projects/{project['id']}/design/brainstorm", json={"action": "continue"})
    assert retried.status_code == 200
    assert retried.json()["draft"]["decisions"][0]["answer"] == "探索和发现"


def test_brainstorm_planner_receives_readiness_recomputed_after_answer(isolated_database) -> None:
    class Planner:
        def plan_turn(self, project_id, draft, user_input):
            question_id = (
                "q5_completion"
                if draft.readiness.unresolved_decisions == ["completion"]
                else "q5_enemy_behavior"
            )
            question = BrainstormQuestion(id=question_id, prompt="这一局怎样结束？", choices=[])
            planned = draft.model_copy(
                update={"clarification": draft.clarification.model_copy(update={"current_question": question})}
            )
            return BrainstormTurn(draft=planned, next_question=question)

    client = _client(str(isolated_database.url), planner=Planner())
    project = _project(client, key="fresh-readiness", idea="一个小型竞技场战斗游戏")
    draft = client.get(f"/api/v1/projects/{project['id']}/design").json()["draft"]
    draft["decisions"] = [
        {
            "question_id": "q1_core_experience",
            "question": "核心体验是什么？",
            "answer_id": "combat",
            "answer": "竞技场战斗",
            "provenance": "user_confirmed",
        },
        {
            "question_id": "q2_player_action",
            "question": "玩家做什么？",
            "answer_id": "shoot",
            "answer": "移动并射击",
            "provenance": "user_confirmed",
        },
        {
            "question_id": "q3_goal",
            "question": "玩家的目标是什么？",
            "answer_id": "survive",
            "answer": "坚持一段时间",
            "provenance": "user_confirmed",
        },
    ]
    draft["clarification"] = {
        "question_index": 3,
        "status": "clarifying",
        "custom_input": "",
        "current_question": {"id": "q4_scope", "prompt": "第一版范围多大？", "choices": []},
    }
    draft["readiness"] = {
        "status": "not_ready",
        "blockers": [],
        "unresolved_decisions": ["core_experience", "player_action", "goal", "scope", "completion"],
    }
    assert client.put(f"/api/v1/projects/{project['id']}/design", json=draft).status_code == 200

    response = client.post(
        f"/api/v1/projects/{project['id']}/design/brainstorm",
        json={"action": "answer", "question_id": "q4_scope", "answer_id": "small", "answer": "单屏竞技场"},
    )

    assert response.status_code == 200
    assert response.json()["next_question"]["id"] == "q5_completion"


def test_brainstorm_budget_exhaustion_stops_without_another_provider_call(isolated_database) -> None:
    class Planner:
        def __init__(self):
            self.calls = 0

        def plan_turn(self, project_id, draft, user_input):
            self.calls += 1
            question = BrainstormQuestion(id="q6_enemy_behavior", prompt="敌人还要怎样行动？", choices=[])
            planned = draft.model_copy(
                update={"clarification": draft.clarification.model_copy(update={"current_question": question})}
            )
            return BrainstormTurn(draft=planned, next_question=question)

    planner = Planner()
    client = _client(str(isolated_database.url), planner=planner)
    project = _project(client, key="budget-stop", idea="一个小型竞技场战斗游戏")
    draft = client.get(f"/api/v1/projects/{project['id']}/design").json()["draft"]
    draft["decisions"] = [
        {
            "question_id": "q1_core_experience",
            "question": "核心体验是什么？",
            "answer_id": "combat",
            "answer": "竞技场战斗",
            "provenance": "user_confirmed",
        },
        {
            "question_id": "q2_player_action",
            "question": "玩家做什么？",
            "answer_id": "shoot",
            "answer": "移动并射击",
            "provenance": "user_confirmed",
        },
        {
            "question_id": "q3_goal",
            "question": "玩家的目标是什么？",
            "answer_id": "survive",
            "answer": "坚持一段时间",
            "provenance": "user_confirmed",
        },
        {
            "question_id": "q4_scope",
            "question": "第一版范围多大？",
            "answer_id": "small",
            "answer": "单屏竞技场",
            "provenance": "user_confirmed",
        },
    ]
    draft["clarification"] = {
        "question_index": 5,
        "status": "clarifying",
        "custom_input": "",
        "current_question": {"id": "q5_enemy_behavior", "prompt": "敌人怎样行动？", "choices": []},
    }
    assert client.put(f"/api/v1/projects/{project['id']}/design", json=draft).status_code == 200

    response = client.post(
        f"/api/v1/projects/{project['id']}/design/brainstorm",
        json={"action": "answer", "question_id": "q5_enemy_behavior", "answer_id": "charge", "answer": "近距离冲锋"},
    )

    assert response.status_code == 200
    assert response.json()["readiness"]["status"] == "blocked"
    assert response.json()["next_question"] is None
    assert planner.calls == 0
