import asyncio
import json
import os
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.agents.fake_executor import FakeProcessExecutor
from app.agents.opengame_adapter import OpenGameAdapter, _build_prompt, _default_cli_js
from app.agents.chrome_browser_runner import ChromeCandidateTestRunner, _hook_result, _select_debug_target
from app.config import Settings, get_settings
from app.contracts.game_agent import GameBuildRequest, WorkspaceRef
from app.contracts.gamespec import CreatorGameSpec
from app.main import create_app
from app.models import Build, BuildCandidate, GameSpecRevision, Project, Run
from tests.test_c05_gamespec_contract import valid_gamespec


def _request(workspace: Path) -> GameBuildRequest:
    spec = CreatorGameSpec.model_validate(valid_gamespec())
    return GameBuildRequest(
        project_id="runtime-project",
        build_id="runtime-build",
        operation="create",
        creator_game_spec=spec,
        runtime_build_spec=spec.to_runtime_build_spec(),
        workspace=WorkspaceRef(root=str(workspace), allowed_paths=["dist"]),
    )


def test_production_settings_select_real_providers(monkeypatch) -> None:
    monkeypatch.delenv("GAME_AGENT_PROVIDER", raising=False)
    monkeypatch.delenv("CANDIDATE_TEST_PROVIDER", raising=False)
    settings = get_settings()
    assert settings.game_agent_provider == "opengame"
    assert settings.candidate_test_provider == "chrome"


def test_explicit_test_settings_are_fake_only_by_injection() -> None:
    settings = Settings(database_url="sqlite:///test.db")
    assert settings.game_agent_provider == "fake"
    assert settings.candidate_test_provider == "fake"


def test_production_app_wires_real_providers_without_fake_fallback(tmp_path: Path) -> None:
    app = create_app(Settings(
        database_url=f"sqlite:///{tmp_path / 'real.db'}",
        game_agent_provider="opengame",
        candidate_test_provider="chrome",
        opengame_cli_js="",
    ))
    assert isinstance(app.state.game_agent, OpenGameAdapter)
    assert app.state.candidate_test_runner is None


def test_opengame_prompt_declares_platform_test_hook(tmp_path: Path) -> None:
    prompt = _build_prompt(_request(tmp_path))
    assert "window.__GAME_TEST__" in prompt
    assert "core_input" in prompt
    assert "completion" in prompt


def test_opengame_prompt_requires_artifact_write_before_final_text(tmp_path: Path) -> None:
    prompt = _build_prompt(_request(tmp_path))
    assert "first meaningful action" in prompt
    assert "write_file" in prompt
    assert "text-only response is a failure" in prompt
    assert "verify that index.html exists" in prompt


def test_opengame_configuration_failure_is_provider_neutral(tmp_path: Path) -> None:
    async def run_once():
        adapter = OpenGameAdapter(
            FakeProcessExecutor(),
            opengame_cli_js="",
            require_credentials=True,
        )
        handle = await adapter.start(_request(tmp_path))
        return await adapter.result(handle)

    result = asyncio.run(run_once())
    assert result.status == "failed"
    assert result.error is not None
    assert result.error.code == "opengame_not_configured"


def test_cli_resolution_uses_real_opengame_path() -> None:
    resolved = _default_cli_js()
    if resolved:
        assert Path(resolved).is_file()


def test_hook_result_rejects_runtime_pass_without_platform_shape() -> None:
    assert _hook_result(None) == (False, "test hook did not return a result")
    assert _hook_result({"passed": False}) == (False, "test hook reported failure")
    assert _hook_result({"passed": True, "observed": "ok"}) == (True, "ok")


def test_chrome_target_selection_prefers_page_over_browser_ui() -> None:
    targets = [
        {"type": "browser_ui", "webSocketDebuggerUrl": "ws://browser-ui"},
        {"type": "page", "webSocketDebuggerUrl": "ws://game-page"},
    ]

    selected = _select_debug_target(targets)

    assert selected is targets[1]


@pytest.mark.skipif(
    not (ChromeCandidateTestRunner.find_browser() and os.getenv("RUN_REAL_BROWSER_SMOKE") == "1"),
    reason="set RUN_REAL_BROWSER_SMOKE=1 and install Google Chrome/Chromium for real browser smoke",
)
def test_real_chrome_runner_collects_platform_evidence(isolated_database, tmp_path: Path) -> None:
    root = tmp_path / "run"
    dist = root / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text(
        """<!doctype html><script>
        window.__GAME_TEST__ = {version: 1, ready: true, run: async (check) =>
          ({passed: true, observed: check + ' passed'})};
        </script>""",
        encoding="utf-8",
    )
    with Session(isolated_database) as session:
        project = Project(name="Browser", original_idea="Real browser test")
        session.add(project)
        session.flush()
        revision = GameSpecRevision(project_id=project.id, revision_number=1, content_json="{}", status="confirmed")
        session.add(revision)
        session.flush()
        build = Build(project_id=project.id, gamespec_revision_id=revision.id, status="succeeded")
        session.add(build)
        session.flush()
        run = Run(id="run-browser", build_id=build.id, status="succeeded", workspace_path=str(root), workspace_status="prepared")
        session.add(run)
        candidate = BuildCandidate(project_id=project.id, build_id=build.id, status="succeeded", artifact_path="dist/index.html", summary="browser")
        session.add(candidate)
        session.flush()

        result = asyncio.run(ChromeCandidateTestRunner(session, timeout_seconds=8).run(candidate))

    if result.verdict != "pass":
        diagnostics = [item.model_dump(mode="json") for item in result.diagnostics]
        evidence = [item.model_dump(mode="json") for item in result.evidence]
        pytest.fail(json.dumps({"diagnostics": diagnostics, "evidence": evidence}, ensure_ascii=False, indent=2))
    assert {item.kind for item in result.evidence} == {
        "browser_started", "console", "core_input", "gameplay", "completion", "phaser_hook",
    }
    assert all(item.source == "platform" for item in result.evidence)
