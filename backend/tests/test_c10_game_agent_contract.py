"""C10 — OpenGameAdapter must pass the shared provider-neutral contract suite.

This is the hard gate: the same assertions FakeGameAgent passes must also pass
for OpenGameAdapter. We inject a FakeProcessExecutor (C09) so the suite is
deterministic and needs no real opengame binary. The workspace is a real tmp
dir with an index.html so the adapter's artifact check can succeed.
"""

from __future__ import annotations

from pathlib import Path

from app.agents.fake_executor import FakeProcessExecutor
from app.agents.opengame_adapter import OpenGameAdapter
from app.contracts.game_agent import GameBuildRequest, WorkspaceRef
from app.contracts.gamespec import CreatorGameSpec
from tests.contract_suites.test_game_agent_contract_suite import assert_game_agent_contract


def _gamespec() -> CreatorGameSpec:
    return CreatorGameSpec.model_validate({
        "schema_version": 1,
        "title": "关系农场",
        "first_playable": {"goal": "完成一条 NPC 委托", "hypothesis": "关系反馈驱动经营"},
        "gameplay": {"core_loop": ["种植", "收获"], "actions": ["移动", "互动"]},
        "characters": {
            "player": "农场经营者", "player_actions": ["移动", "种植"],
            "npc_name": "Lucy", "npc_role": "关系对象", "npc_behaviors": ["发布委托"],
            "dialogue_states": ["陌生", "熟悉"], "world_areas": ["农场"],
            "primary_npcs": "Lucy", "relationship_growth": "完成委托提升好感",
            "favor_rules": "达到阈值进入下一阶段", "relationship_events": "达到阈值触发事件",
            "request_rewards": "完成委托获得好感",
        },
        "rules": {"progression": ["提升好感"], "completion": "完成一条委托"},
        "scope": {"included": ["一个农场"], "later": []},
        "validation": ["委托可以完成"],
    })


def test_opengame_adapter_passes_shared_provider_contract_suite(tmp_path: Path) -> None:
    # A real workspace with an index.html so the success path's artifact check passes.
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "index.html").write_text("<!doctype html><title>game</title>")

    spec = _gamespec()

    def request_factory(operation: str) -> GameBuildRequest:
        # The suite asks for "unsupported-operation" to probe the unsupported path;
        # anything else is a normal supported operation.
        return GameBuildRequest(
            project_id="project-1",
            build_id=f"build-{operation}",
            operation=operation if operation != "unsupported-operation" else "stream_assets",
            creator_game_spec=spec,
            runtime_build_spec=spec.to_runtime_build_spec(),
            workspace=WorkspaceRef(root=str(workspace), allowed_paths=["dist", "src"]),
            baseline_playable=None,
            request_text="build the game",
        )

    def factory() -> OpenGameAdapter:
        # FakeProcessExecutor returns a succeeded stream-json with a result event.
        return OpenGameAdapter(FakeProcessExecutor(outcome="succeeded"))

    assert_game_agent_contract(factory, request_factory)


def test_unproven_operations_are_unsupported(tmp_path: Path) -> None:
    """C08 capability matrix: only ``create`` has accepted real evidence. modify,
    repair, and test have no real run captured, so they MUST return the
    provider-neutral ``unsupported`` result rather than launching OpenGame.
    Guards against SUPPORTED_OPERATIONS widening without new evidence.
    """
    import asyncio

    workspace = tmp_path / "ws"
    workspace.mkdir()

    spec = _gamespec()

    def make_request(operation: str) -> GameBuildRequest:
        return GameBuildRequest(
            project_id="project-1",
            build_id=f"build-{operation}",
            operation=operation,
            creator_game_spec=spec,
            runtime_build_spec=spec.to_runtime_build_spec(),
            workspace=WorkspaceRef(root=str(workspace), allowed_paths=["dist", "src"]),
            baseline_playable=None,
            request_text="build the game",
        )

    async def exercise() -> None:
        adapter = OpenGameAdapter(FakeProcessExecutor(outcome="succeeded"))
        for operation in ("modify", "repair", "test"):
            handle = await adapter.start(make_request(operation))
            result = await adapter.result(handle)
            assert result.status == "unsupported", operation
            assert result.error is not None, operation
            assert result.error.code == "unsupported_operation", operation
            # An unsupported run must not have launched the (fake) executor.
            assert adapter._executor.runs == [], operation  # type: ignore[attr-defined]

    asyncio.run(exercise())
