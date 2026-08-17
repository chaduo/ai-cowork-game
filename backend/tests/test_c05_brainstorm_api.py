from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


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
    assert turn["next_question"] is None
    confirmed = client.post(f"/api/v1/projects/{project['id']}/design/confirm")
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"
