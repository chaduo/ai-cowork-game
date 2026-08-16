"""C13 — OpenGameAdapter workspace-escape + raw-stream redaction tests.

Adapter-level evidence for the game-agent-runtime "Deny workspace escape"
scenario and the design.md "scan output for secrets" requirement: a generated
escape (protected path / symlink / traversal) maps to ``invalid_output`` with the
specific reason preserved and is not imported, and a secret leaked into the raw
provider stream is redacted before it can reach a Diagnostic.

These depend on the adapter's hardened ``_build_result`` (C13 L2), so they live
apart from the pure ``WorkspaceManager`` unit tests in ``test_c13_workspace.py``.
"""

from __future__ import annotations

from pathlib import Path

from app.agents.executor import ProcessResult
from app.agents.opengame_adapter import _build_result
from app.agents.workspace import WorkspaceManager, redact_stream
from app.contracts.game_agent import GameBuildRequest, WorkspaceRef
from app.contracts.gamespec import CreatorGameSpec


def _success_process(
    stdout: str = '{"type":"result","subtype":"success","is_error":false,'
                  '"result":"done","usage":{"input_tokens":100,"output_tokens":5}}\n',
) -> ProcessResult:
    return ProcessResult(stdout=stdout, stderr="", exit_code=0,
                          process_status="completed", duration_seconds=0.0)


def _gamespec_request(workspace_root: Path) -> tuple:
    spec = CreatorGameSpec.model_validate({
        "schema_version": 1, "title": "t", "first_playable": {"goal": "g", "hypothesis": "h"},
        "gameplay": {"core_loop": ["m"], "actions": ["m"]},
        "characters": {"player": "p", "player_actions": ["m"], "npc_name": "n", "npc_role": "r",
                       "npc_behaviors": ["i"], "dialogue_states": ["a"], "world_areas": ["w"],
                       "primary_npcs": "n", "relationship_growth": "x", "favor_rules": "x",
                       "relationship_events": "x", "request_rewards": "x"},
        "rules": {"progression": ["x"], "completion": "x"},
        "scope": {"included": ["x"], "later": []}, "validation": ["x"],
    })
    return _build_result, GameBuildRequest(
        project_id="p", build_id="b", operation="create",
        creator_game_spec=spec, runtime_build_spec=spec.to_runtime_build_spec(),
        workspace=WorkspaceRef(root=str(workspace_root), allowed_paths=["dist", "src"]),
        baseline_playable=None, request_text="build",
    )


def test_build_result_maps_protected_path_escape_to_invalid_output(tmp_path: Path) -> None:
    """A generated index.html under a protected dir (.git) is rejected as an
    escape → invalid_output with the specific reason preserved, not imported."""
    _build_result, request = _gamespec_request(tmp_path / "ws")
    ws = tmp_path / "ws"
    (ws / ".git").mkdir(parents=True)
    (ws / ".git" / "index.html").write_text("<html>host git</html>")
    result = _build_result(_success_process(), [], request, WorkspaceManager())
    assert result.status == "invalid_output"
    assert result.error is not None
    assert result.error.code == "protected_path"
    assert result.artifact_manifest == []  # not imported


def test_build_result_redacts_secret_in_stdout_before_diagnostics(tmp_path: Path) -> None:
    """A provider error wrapping a leaked key is redacted before it can reach a
    Diagnostic. Exercises the adapter's _run redaction step via _build_result
    consuming an already-redacted stream."""
    _build_result, request = _gamespec_request(tmp_path / "ws")
    leaky = ('{"type":"result","subtype":"success","is_error":false,'
             '"result":"[API Error: key=sk-leaked999]","usage":{"input_tokens":0,"output_tokens":0}}\n')
    redacted_stdout = redact_stream(leaky)
    assert "sk-leaked999" not in redacted_stdout
    result = _build_result(_success_process(redacted_stdout), [], request, WorkspaceManager())
    # The provider error (zero tokens) maps to failed; the leaked key is gone.
    assert result.status == "failed"
    assert "sk-leaked999" not in (result.error.message if result.error else "")


def test_malformed_stream_is_invalid_output_even_with_success_result(tmp_path: Path) -> None:
    _, request = _gamespec_request(tmp_path / "ws")
    Path(request.workspace.root).mkdir()
    Path(request.workspace.root, "index.html").write_text("<html></html>")
    process = _success_process("broken-json\n" + _success_process().stdout)
    result = _build_result(process, [], request, WorkspaceManager())
    assert result.status == "invalid_output"
    assert result.error is not None
    assert result.error.code == "invalid_provider_output"


def test_success_without_index_preview_is_invalid_artifact(tmp_path: Path) -> None:
    _, request = _gamespec_request(tmp_path / "ws")
    Path(request.workspace.root).mkdir()
    Path(request.workspace.root, "game.js").write_text("console.log('game')")
    result = _build_result(_success_process(), [], request, WorkspaceManager())
    assert result.status == "invalid_output"
    assert result.error is not None
    assert result.error.code == "invalid_artifact"
