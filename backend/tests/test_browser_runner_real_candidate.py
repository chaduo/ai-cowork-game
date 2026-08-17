"""Rebaseline Aug-15 zhang item 3 — real provider Candidate + real browser runner.

"Make the real provider produce a Candidate that the platform browser runner can
verify." This drives the real BrowserCandidateTestRunner (Playwright headless
Chromium) against two real artifacts and proves both spec-correct outcomes
through CandidateTestService → a standard platform TestReport:

1. Instrumented game (exposes window.__GAME_TEST__) → all evidence passed →
   platform verdict PASSED + test_gate_status "ready" (a Candidate the platform
   CAN verify).
2. Real OpenGameAdapter (kimi-k3) → a real generated index.html. A real OpenGame
   game lacks the test hook → phaser_hook failed + core_gameplay missing →
   platform verdict CRITICAL_FAILURE (the spec-correct gate: no hook = no
   gameplay proof, no screenshot-guessing, runtime cannot self-certify).

Gated on opengame + credentials + Playwright's Chromium; skips honestly otherwise
(like the C10/C13 smokes). Credentials come from backend/tests/.env.local
(gitignored) — never committed.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.browser_test_runner import BrowserCandidateTestRunner
from app.models import Build, BuildCandidate, GameSpecRevision
from app.services.candidate_tests import CandidateTestService
from app.services.lifecycle import ProjectLifecycleService
from tests.test_c05_design_api import draft_payload
from tests.test_c05_gamespec_contract import valid_gamespec

_FIXTURE_INSTRUMENTED = Path(__file__).parent / "fixtures" / "instrumented_game" / "index.html"
_FIXTURE_PLAIN = Path(__file__).parent / "fixtures" / "plain_game" / "index.html"


def _creds() -> dict[str, str]:
    creds: dict[str, str] = {}
    env_local = Path(__file__).parent / ".env.local"
    if env_local.is_file():
        for line in env_local.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip()
    for k in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"):
        if os.environ.get(k):
            creds[k] = os.environ[k]
    return creds


def _cli_js() -> str | None:
    candidates = [
        r"D:\Program Files (x86)\nodejs\node_global\node_modules\@opengame\opengame\dist\cli.js",
    ]
    og = shutil.which("opengame")
    if og:
        shim_dir = os.path.dirname(os.path.realpath(og))
        candidates.append(os.path.join(shim_dir, "node_modules", "@opengame", "opengame", "dist", "cli.js"))
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


def _playwright_ready() -> bool:
    try:
        from playwright.async_api import async_playwright  # noqa: F401
    except Exception:
        return False
    return True


creds = _creds()
has_creds = bool(creds.get("OPENAI_API_KEY") and creds.get("OPENAI_BASE_URL"))
has_opengame = bool(_cli_js())
has_playwright = _playwright_ready()


def _confirmed_project(session: Session) -> str:
    lifecycle = ProjectLifecycleService(session)
    project = lifecycle.create_project("Browser-Runner Game", "A game for browser verification")
    lifecycle.submit_design(project.id, draft_payload())
    lifecycle.confirm_design(project.id)
    revision = lifecycle.create_gamespec_revision(project.id, valid_gamespec())
    lifecycle.confirm_gamespec_revision(project.id, revision.id)
    session.commit()
    return project.id


def _make_candidate(session: Session, project_id: str, *, artifact_path: str) -> BuildCandidate:
    revision = session.scalar(
        select(GameSpecRevision)
        .where(GameSpecRevision.project_id == project_id)
        .order_by(GameSpecRevision.revision_number.desc())
    )
    build = Build(project_id=project_id, gamespec_revision_id=revision.id, status="succeeded")
    session.add(build)
    session.flush()
    candidate = BuildCandidate(
        project_id=project_id, build_id=build.id, status="succeeded",
        artifact_path=artifact_path, summary="candidate",
    )
    session.add(candidate)
    session.flush()
    return candidate


# --------------------------------------------------------------------------- #
# Scenario 1 — instrumented game → PASSED / ready
# --------------------------------------------------------------------------- #


@pytest.mark.skipif(not has_playwright, reason="Playwright Chromium not installed (run: uv run playwright install chromium)")
def test_instrumented_game_passes_platform_verification(isolated_database, tmp_path: Path) -> None:
    with Session(isolated_database) as session:
        project_id = _confirmed_project(session)
        # Copy the committed instrumented fixture into a tmp artifact root so the
        # runner resolves it via file:// (artifact_path is relative to that root).
        art_root = tmp_path / "ws"
        art_root.mkdir()
        (art_root / "index.html").write_text(_FIXTURE_INSTRUMENTED.read_text(encoding="utf-8"), encoding="utf-8")
        candidate = _make_candidate(session, project_id, artifact_path="index.html")

        runner = BrowserCandidateTestRunner(artifact_root=art_root)
        report = asyncio.run(CandidateTestService(session, runner).test_candidate(candidate.id))
        session.commit()

        assert report.platform_verdict == "PASSED"
        assert report.status == "PASSED"
        assert report.severity == "none"
        assert session.get(BuildCandidate, candidate.id).test_gate_status == "ready"
        assert {item.kind for item in report.evidence} == {
            "build_check", "browser_started", "console", "core_input", "gameplay", "completion", "phaser_hook",
        }
        hook = next(item for item in report.evidence if item.kind == "phaser_hook")
        assert json.loads(hook.details_json or "{}").get("hook_validated") is True


# --------------------------------------------------------------------------- #
# Scenario 2 — a provider-style Candidate WITHOUT the test hook → CRITICAL_FAILURE
# (deterministic stand-in for a real OpenGame build's plain index.html; the real
# OpenGame run is scenario 3, gated and skip-safe when the build is flaky)
# --------------------------------------------------------------------------- #


@pytest.mark.skipif(not has_playwright, reason="Playwright Chromium not installed (run: uv run playwright install chromium)")
def test_provider_candidate_without_hook_is_critical_failure(isolated_database, tmp_path: Path) -> None:
    """A real-provider-style Candidate (plain game, no window.__GAME_TEST__) is
    verified by the browser runner and rejected with CRITICAL_FAILURE: no hook =
    no gameplay proof, and the platform never screenshot-guesses."""
    with Session(isolated_database) as session:
        project_id = _confirmed_project(session)
        art_root = tmp_path / "ws"
        art_root.mkdir()
        (art_root / "index.html").write_text(_FIXTURE_PLAIN.read_text(encoding="utf-8"), encoding="utf-8")
        candidate = _make_candidate(session, project_id, artifact_path="index.html")

        runner = BrowserCandidateTestRunner(artifact_root=art_root)
        report = asyncio.run(CandidateTestService(session, runner).test_candidate(candidate.id))
        session.commit()

        # All six required runner evidence kinds present; phaser_hook failed; the
        # platform verdict is CRITICAL_FAILURE (no hook = no gameplay proof).
        assert {item.kind for item in report.evidence} == {
            "build_check", "browser_started", "console", "core_input", "gameplay", "completion", "phaser_hook",
        }
        hook = next(item for item in report.evidence if item.kind == "phaser_hook")
        assert hook.status == "failed"
        for kind in ("core_input", "gameplay", "completion"):
            ev = next(item for item in report.evidence if item.kind == kind)
            assert ev.status == "missing"
        assert report.platform_verdict == "CRITICAL_FAILURE"
        assert session.get(BuildCandidate, candidate.id).test_gate_status != "ready"


# --------------------------------------------------------------------------- #
# Scenario 3 — the REAL OpenGame provider → browser runner (gated, skip-safe)
# --------------------------------------------------------------------------- #


@pytest.mark.skipif(
    not (has_playwright and has_opengame and has_creds),
    reason="needs Playwright Chromium + opengame + OPENAI_API_KEY/OPENAI_BASE_URL in backend/tests/.env.local",
)
def test_real_opengame_candidate_runs_through_browser_runner(isolated_database, tmp_path: Path) -> None:
    """The literal rebaseline item: the real OpenGame provider produces a
    Candidate and the real browser runner verifies it. A real OpenGame game has
    no window.__GAME_TEST__ so — when the build produces a playable artifact —
    the runner returns phaser_hook failed and the platform CRITICAL_FAILURE.
    Real builds are flaky, so if the provider did not produce an artifact this
    skips rather than report a false CRITICAL_FAILURE (the deterministic
    no-hook path is scenario 2)."""
    from app.agents.opengame_adapter import OpenGameAdapter
    from app.agents.subprocess_executor import AsyncSubprocessExecutor

    with Session(isolated_database) as session:
        project_id = _confirmed_project(session)
        ws_root = tmp_path / "ws"
        ws_root.mkdir()
        adapter = OpenGameAdapter(
            AsyncSubprocessExecutor(),
            model=creds.get("OPENAI_MODEL", "kimi-k3"),
            openai_api_key=creds["OPENAI_API_KEY"],
            openai_base_url=creds["OPENAI_BASE_URL"],
            sandbox=False,
            timeout_seconds=300,
            opengame_cli_js=_cli_js(),
        )

        async def build_and_collect():
            # start / stream_events / result MUST share one event loop — the
            # adapter's background _run task is scheduled on the current loop and
            # cannot survive a loop tear-down between asyncio.run calls (same
            # lifecycle lesson as test_c10_opengame_adapter_smoke).
            handle = await adapter.start(_build_request(project_id, ws_root))
            events = [event async for event in adapter.stream_events(handle)]
            result = await adapter.result(handle)
            return events, result

        events, result = asyncio.run(build_and_collect())

        # The real provider must produce a playable artifact for the browser to
        # verify; if it didn't (failed/invalid), skip rather than report a false
        # CRITICAL_FAILURE that is really a provider failure.
        if result.status != "succeeded" or not result.preview_entry:
            pytest.skip(f"real OpenGame build did not produce a playable artifact (status={result.status})")

        artifact = ws_root / result.preview_entry
        assert artifact.exists(), f"real artifact not on disk: {artifact}"
        candidate = _make_candidate(session, project_id, artifact_path=result.preview_entry)

        runner = BrowserCandidateTestRunner(artifact_root=ws_root)
        report = asyncio.run(CandidateTestService(session, runner).test_candidate(candidate.id))
        session.commit()

        # All six required runner evidence kinds present; phaser_hook failed; the
        # platform verdict is CRITICAL_FAILURE (no hook = no gameplay proof).
        assert {item.kind for item in report.evidence} == {
            "build_check", "browser_started", "console", "core_input", "gameplay", "completion", "phaser_hook",
        }
        hook = next(item for item in report.evidence if item.kind == "phaser_hook")
        assert hook.status == "failed"
        assert report.platform_verdict == "CRITICAL_FAILURE"
        assert session.get(BuildCandidate, candidate.id).test_gate_status != "ready"


def _build_request(project_id: str, ws_root: Path):
    from app.contracts.game_agent import GameBuildRequest, WorkspaceRef
    from app.contracts.gamespec import CreatorGameSpec

    spec = CreatorGameSpec.model_validate({
        "schema_version": 1, "title": "browser-runner",
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
    return GameBuildRequest(
        project_id=project_id, build_id="browser-runner-build", operation="create",
        creator_game_spec=spec, runtime_build_spec=spec.to_runtime_build_spec(),
        workspace=WorkspaceRef(root=str(ws_root), allowed_paths=["dist", "src"]),
        baseline_playable=None, request_text="Build a simple Pong clone with paddle controls.",
    )
