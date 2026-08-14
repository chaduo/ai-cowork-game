from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.contracts.game_agent import (
    AgentRunHandle,
    ArtifactManifestEntry,
    ContractError,
    GameBuildRequest,
    GameBuildResult,
    RunEvent,
    WorkspaceRef,
)
from app.contracts.gamespec import CreatorGameSpec


def valid_gamespec() -> CreatorGameSpec:
    return CreatorGameSpec.model_validate({
        "schema_version": 1,
        "title": "关系农场",
        "first_playable": {
            "goal": "完成一条 NPC 委托并看到关系事件",
            "hypothesis": "关系反馈会驱动玩家继续经营农场",
        },
        "gameplay": {"core_loop": ["种植", "收获"], "actions": ["移动", "互动"]},
        "characters": {
            "player": "农场经营者",
            "player_actions": ["移动", "种植"],
            "npc_name": "Lucy",
            "npc_role": "关系对象",
            "npc_behaviors": ["发布委托"],
            "dialogue_states": ["陌生", "熟悉"],
            "world_areas": ["农场"],
            "primary_npcs": "Lucy",
            "relationship_growth": "完成委托提升好感",
            "favor_rules": "达到阈值进入下一阶段",
            "relationship_events": "达到阈值触发事件",
            "request_rewards": "完成委托获得好感",
        },
        "rules": {"progression": ["提升好感"], "completion": "完成一条委托"},
        "scope": {"included": ["一个农场"], "later": []},
        "validation": ["委托可以完成"],
    })


def valid_request() -> GameBuildRequest:
    spec = valid_gamespec()
    return GameBuildRequest(
        project_id="project-1",
        build_id="build-1",
        operation="create",
        creator_game_spec=spec,
        runtime_build_spec=spec.to_runtime_build_spec(),
        workspace=WorkspaceRef(root="/tmp/run-1", allowed_paths=["dist", "src"]),
        baseline_playable=None,
        request_text="创建第一版可试玩版本",
    )


def test_game_build_request_contains_provider_neutral_inputs() -> None:
    request = valid_request()

    assert request.operation == "create"
    assert request.runtime_build_spec.project_title == "关系农场"
    assert request.workspace.root == "/tmp/run-1"


def test_game_build_result_accepts_success_and_structured_artifacts() -> None:
    result = GameBuildResult(
        status="succeeded",
        artifact_manifest=[
            ArtifactManifestEntry(path="dist/index.html", kind="preview_entry", size_bytes=1200),
        ],
        preview_entry="dist/index.html",
        diagnostics=[],
        metadata={"backend": "fake"},
        error=None,
    )

    assert result.status == "succeeded"
    assert result.artifact_manifest[0].path == "dist/index.html"


def test_game_build_result_accepts_standard_unsupported_status() -> None:
    result = GameBuildResult(
        status="unsupported",
        artifact_manifest=[],
        preview_entry=None,
        diagnostics=[],
        metadata={},
        error=ContractError(code="unsupported_operation", message="modify is not supported"),
    )

    assert result.status == "unsupported"
    assert result.error is not None
    assert result.error.code == "unsupported_operation"


def test_run_event_rejects_progress_outside_zero_to_one() -> None:
    with pytest.raises(ValidationError):
        RunEvent(
            run_id="run-1",
            sequence=1,
            stage="building",
            kind="progress",
            message="完成",
            progress=1.1,
            artifact_ref=None,
            error=None,
            timestamp=datetime.now(timezone.utc),
        )


def test_run_event_rejects_human_gate_decisions() -> None:
    with pytest.raises(ValidationError):
        RunEvent(
            run_id="run-1",
            sequence=1,
            stage="finished",
            kind="published",
            message="已发布",
            progress=1,
            artifact_ref=None,
            error=None,
            timestamp=datetime.now(timezone.utc),
        )


def test_contract_models_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        AgentRunHandle(run_id="run-1", build_id="build-1", provider_session_id="secret")
