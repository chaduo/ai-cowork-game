import asyncio
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.contracts.game_agent import (
    AgentRunHandle,
    AffectedScope,
    ArtifactManifestEntry,
    BuildOverride,
    ContractProfile,
    ContractError,
    GameBuildRequest,
    GameBuildResult,
    PendingDecision,
    ResourceReference,
    RunEvent,
    WorkspaceRef,
)
from app.agents.fake_game_agent import FakeGameAgent
from tests.contract_suites.test_game_agent_contract_suite import assert_game_agent_contract
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
        affected_scope=AffectedScope(sections=["gameplay", "characters"], description="关系玩法 first playable"),
        resource_references=[ResourceReference(
            resource_id="relationship-system",
            resource_revision="resource-v1",
            source_project_id="project-source",
            source_release_id="release-1",
            snapshot_hash="a" * 64,
            role="characters",
        )],
        relevant_overrides=[BuildOverride(
            key="relationship.max_favor",
            value=100,
            source="user",
            provenance="gamespec-draft-v2",
        )],
        game_design_profile=ContractProfile(name="creator-game-design", version="1", capabilities=["clarification"]),
        gamespec_profile=ContractProfile(name="creator-gamespec", version="1", capabilities=["relationship"]),
        game_build_profile=ContractProfile(name="runtime-build", version="1", capabilities=["create", "modify"]),
    )


def test_game_build_request_contains_provider_neutral_inputs() -> None:
    request = valid_request()

    assert request.operation == "create"
    assert request.runtime_build_spec.project_title == "关系农场"
    assert request.workspace.root == "/tmp/run-1"
    assert request.affected_scope.sections == ["gameplay", "characters"]
    assert request.resource_references[0].source_project_id == "project-source"
    assert request.relevant_overrides[0].provenance == "gamespec-draft-v2"
    assert request.game_build_profile.version == "1"


def test_game_build_request_defaults_context_for_legacy_callers() -> None:
    request = valid_request().model_copy(update={
        "affected_scope": AffectedScope(),
        "resource_references": [],
        "relevant_overrides": [],
    })

    assert request.affected_scope.sections == []
    assert request.resource_references == []
    assert request.relevant_overrides == []
    assert request.game_design_profile.name
    assert request.gamespec_profile.name
    assert request.game_build_profile.name


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


def test_game_build_result_waiting_for_input_is_non_terminal() -> None:
    result = GameBuildResult(
        status="waiting_for_input",
        pending_decision=PendingDecision(
            decision_id="decision-1",
            prompt="选择关系反馈方式",
            input_type="choice",
            options=["心形", "进度条"],
        ),
    )

    assert result.status == "waiting_for_input"
    assert result.pending_decision is not None
    assert result.pending_decision.decision_id == "decision-1"


def test_waiting_for_input_requires_a_pending_decision() -> None:
    with pytest.raises(ValidationError):
        GameBuildResult(status="waiting_for_input")


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


def test_run_event_requires_timezone_aware_timestamp() -> None:
    with pytest.raises(ValidationError):
        RunEvent(
            run_id="run-1",
            sequence=1,
            stage="building",
            kind="progress",
            message="进行中",
            progress=0.5,
            artifact_ref=None,
            error=None,
            timestamp=datetime(2026, 8, 14, 12, 0),
        )


def test_run_event_rejects_resource_save_gate_equivalent() -> None:
    with pytest.raises(ValidationError):
        RunEvent(
            run_id="run-1",
            sequence=1,
            stage="finished",
            kind="resource-save-complete",
            message="资源已保存",
            progress=1,
            artifact_ref=None,
            error=None,
            timestamp=datetime.now(timezone.utc),
        )


def test_run_event_needs_input_requires_stable_decision_id() -> None:
    event = RunEvent(
        run_id="run-1",
        sequence=1,
        stage="building",
        kind="build.needs_input",
        message="需要选择关系反馈方式",
        progress=None,
        artifact_ref=None,
        error=None,
        timestamp=datetime.now(timezone.utc),
        decision_id="decision-1",
    )

    assert event.decision_id == "decision-1"

    invalid = event.model_dump(mode="json")
    invalid["decision_id"] = None
    with pytest.raises(ValidationError):
        RunEvent.model_validate(invalid)


def test_contract_models_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        AgentRunHandle(run_id="run-1", build_id="build-1", provider_session_id="secret")


def run_async(coroutine):
    return asyncio.run(coroutine)


async def collect_events(agent: FakeGameAgent, handle: AgentRunHandle):
    return [event async for event in agent.stream_events(handle)]


def test_fake_agent_returns_deterministic_success_and_ordered_events() -> None:
    agent = FakeGameAgent()
    handle = run_async(agent.start(valid_request()))

    events = run_async(collect_events(agent, handle))
    result = run_async(agent.result(handle))

    assert handle.run_id == "fake-run-1"
    assert [event.sequence for event in events] == [1, 2, 3]
    assert result.status == "succeeded"
    assert result.preview_entry == "dist/index.html"


def test_fake_agent_passes_shared_provider_contract_suite() -> None:
    def request_factory(operation: str) -> GameBuildRequest:
        actual_operation = "stream_assets" if operation == "unsupported-operation" else operation
        return valid_request().model_copy(update={"operation": actual_operation})

    assert_game_agent_contract(FakeGameAgent, request_factory)


def test_fake_agent_returns_unsupported_for_unknown_operation() -> None:
    agent = FakeGameAgent()
    request = valid_request().model_copy(update={"operation": "stream_assets"})
    handle = run_async(agent.start(request))

    result = run_async(agent.result(handle))

    assert result.status == "unsupported"
    assert result.error is not None
    assert result.error.code == "unsupported_operation"


def test_fake_agent_cancel_produces_cancelled_result_and_terminal_event() -> None:
    agent = FakeGameAgent()
    handle = run_async(agent.start(valid_request()))
    run_async(agent.cancel(handle))

    result = run_async(agent.result(handle))
    events = run_async(collect_events(agent, handle))

    assert result.status == "cancelled"
    assert events[-1].kind == "cancelled"
    assert events[-1].error is not None
    assert events[-1].error.code == "cancelled"


def test_fake_agent_can_pause_for_input_without_terminal_error() -> None:
    agent = FakeGameAgent(outcome_by_operation={"create": "waiting_for_input"})
    handle = run_async(agent.start(valid_request()))

    result = run_async(agent.result(handle))
    events = run_async(collect_events(agent, handle))

    assert result.status == "waiting_for_input"
    assert result.pending_decision is not None
    assert result.pending_decision.decision_id == "decision-create-1"
    assert events[-1].kind == "build.needs_input"
    assert events[-1].decision_id == "decision-create-1"


@pytest.mark.parametrize("status", ["timed_out", "invalid_output", "failed"])
def test_fake_agent_maps_provider_outcomes_to_standard_results(status: str) -> None:
    agent = FakeGameAgent(outcome_by_operation={"create": status})
    handle = run_async(agent.start(valid_request()))

    result = run_async(agent.result(handle))

    assert result.status == status
    assert result.error is not None
