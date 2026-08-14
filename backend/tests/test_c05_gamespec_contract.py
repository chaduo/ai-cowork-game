import pytest
from pydantic import ValidationError

from app.contracts.gamespec import CreatorGameSpec


def valid_gamespec() -> dict:
    return {
        "schema_version": 1,
        "title": "多代田园物语",
        "first_playable": {
            "goal": "完成一条 NPC 委托并看到关系事件",
            "hypothesis": "关系反馈会驱动玩家继续经营农场",
        },
        "gameplay": {
            "core_loop": ["种植", "收获", "完成委托", "提升好感"],
            "actions": ["移动", "种植", "与 NPC 对话"],
        },
        "characters": {
            "player": "农场经营者",
            "player_actions": ["移动", "种植", "互动"],
            "npc_name": "Lucy",
            "npc_role": "主要关系对象",
            "npc_behaviors": ["发布委托", "根据关系阶段改变对话"],
            "dialogue_states": ["陌生", "熟悉", "亲近"],
            "world_areas": ["农场", "NPC 活动区"],
            "primary_npcs": "Lucy 是主要关系对象。",
            "relationship_growth": "完成委托和互动会提升好感。",
            "favor_rules": "好感达到阈值后进入下一阶段。",
            "relationship_events": "达到阈值后触发关系事件。",
            "request_rewards": "完成委托获得好感奖励。",
        },
        "rules": {"progression": ["提升好感", "解锁事件"], "completion": "完成关系委托"},
        "scope": {"included": ["一个农场", "一个 NPC"], "later": ["更多地图"]},
        "validation": ["委托可以完成", "关系事件可以触发"],
    }


def test_creator_gamespec_accepts_prototype_relationship_payload() -> None:
    spec = CreatorGameSpec.model_validate(valid_gamespec())

    assert spec.schema_version == 1
    assert spec.characters.relationship_growth == "完成委托和互动会提升好感。"
    assert spec.to_runtime_build_spec().first_playable_goal == "完成一条 NPC 委托并看到关系事件"


def test_creator_gamespec_requires_all_relationship_fields() -> None:
    payload = valid_gamespec()
    del payload["characters"]["relationship_events"]

    with pytest.raises(ValidationError):
        CreatorGameSpec.model_validate(payload)


def test_creator_gamespec_rejects_resource_workflow_state() -> None:
    payload = valid_gamespec()
    payload["recommended"] = True
    payload["characters"]["resource_id"] = "relationship-system"

    with pytest.raises(ValidationError):
        CreatorGameSpec.model_validate(payload)
