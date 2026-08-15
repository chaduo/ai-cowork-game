"""C10 — replay the real C08 fixtures through the adapter's status decision.

This is the deterministic, zero-token half of task 4.4: feed the five stream-json
fixtures actually captured during the C08 spike (success / failure / invalid
output / timeout / cancel) through ``parse_stream_json`` + ``_build_result`` and
assert each maps to the provider-neutral ``GameBuildStatus`` it was captured to
prove. This locks the C08 load-bearing mapping rules:

- ``result.is_error`` is unreliable (failure fixture is ``is_error:false`` yet a
  provider error → ``failed``);
- success ≠ has artifact (invalid-output fixture is ``is_error:false`` but wrote
  no ``index.html`` → ``invalid_output``);
- timed_out vs cancelled come from the executor trigger, not stream content
  (both fixtures have NO ``result`` event; the status comes from
  ``ProcessResult.process_status``).

Fixtures live in ``docs/development/c08-opengame-spike/`` (committed). The real
stdout is the fixture text; the surrounding ``ProcessResult`` (exit code,
process_status) is what C09 would have produced for that outcome.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.agents.opengame_adapter import _build_result
from app.agents.executor import ProcessResult
from app.agents.workspace import WorkspaceManager
from app.contracts.game_agent import GameBuildRequest, WorkspaceRef
from app.contracts.gamespec import CreatorGameSpec
from app.agents.opengame_stream_parser import parse_stream_json

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "docs" / "development" / "c08-opengame-spike"


def _gamespec() -> CreatorGameSpec:
    return CreatorGameSpec.model_validate({
        "schema_version": 1, "title": "fixture replay",
        "first_playable": {"goal": "play", "hypothesis": "fun"},
        "gameplay": {"core_loop": ["move"], "actions": ["move"]},
        "characters": {"player": "p", "player_actions": ["move"], "npc_name": "n",
                       "npc_role": "r", "npc_behaviors": ["idle"], "dialogue_states": ["a"],
                       "world_areas": ["w"], "primary_npcs": "n",
                       "relationship_growth": "x", "favor_rules": "x",
                       "relationship_events": "x", "request_rewards": "x"},
        "rules": {"progression": ["x"], "completion": "x"},
        "scope": {"included": ["x"], "later": []}, "validation": ["x"],
    })


def _load(name: str) -> str:
    path = _FIXTURE_DIR / f"{name}.stream.json"
    assert path.is_file(), f"missing C08 fixture: {path}"
    return path.read_text(encoding="utf-8")


def _request(workspace: Path) -> GameBuildRequest:
    return GameBuildRequest(
        project_id="proj", build_id="build", operation="create",
        creator_game_spec=_gamespec(),
        runtime_build_spec=_gamespec().to_runtime_build_spec(),
        workspace=WorkspaceRef(root=str(workspace), allowed_paths=["dist", "src"]),
        baseline_playable=None, request_text="build the game",
    )


# (fixture name, process_status, exit_code, write index.html, expected status, expected error code)
_CASES = [
    ("success-run", "completed", 0, True, "succeeded", None),
    ("failure-run", "completed", 0, False, "failed", "provider_failed"),
    ("invalid-output-run", "completed", 0, False, "invalid_output", "invalid_output"),
    ("timeout-run", "timed_out", None, False, "timed_out", "timeout"),
    ("cancel-run", "cancelled", None, False, "cancelled", "cancelled"),
]


@pytest.mark.parametrize("fixture,process_status,exit_code,write_index,expected,expected_code", _CASES)
def test_build_result_maps_c08_fixture_to_status(
    tmp_path: Path,
    fixture: str,
    process_status: str,
    exit_code: int | None,
    write_index: bool,
    expected: str,
    expected_code: str | None,
) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    if write_index:
        (workspace / "index.html").write_text("<!doctype html><title>game</title>", encoding="utf-8")

    process = ProcessResult(
        stdout=_load(fixture),
        stderr="",
        exit_code=exit_code,
        process_status=process_status,
        duration_seconds=0.0,
    )
    events = parse_stream_json(process.stdout)
    result = _build_result(process, [], _request(workspace), WorkspaceManager())

    assert result.status == expected
    if expected_code is None:
        assert result.error is None
    else:
        assert result.error is not None
        assert result.error.code == expected_code

    # A succeeded result must point at a real playable artifact on disk (C08: never
    # infer success from log keywords alone).
    if expected == "succeeded":
        assert result.preview_entry is not None
        assert (workspace / result.preview_entry).exists()
        assert result.artifact_manifest
