"""C10 — real OpenGameAdapter smoke (catalog AC: "real run passes through create flow,
without touching the Project repository").

Uses the real AsyncSubprocessExecutor + the real opengame CLI. Credentials come
from backend/tests/.env.local (gitignored) or env vars — never hardcoded, never
committed. Skipped if opengame or credentials are unavailable.

Async lifecycle: start / stream_events / result MUST share one event loop. The
adapter's ``start`` schedules the run as a background task on the current loop
(``asyncio.ensure_future``); if start ran in its own ``asyncio.run`` that loop
would tear down and cancel the run before it finished, and the later stream/result
calls would hang forever on the run's ``finished`` event. So the whole flow runs
inside a single ``asyncio.run`` — the same shape as the shared contract suite and
the FastAPI app's long-lived loop.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

import pytest

from app.agents.opengame_adapter import OpenGameAdapter
from app.agents.subprocess_executor import AsyncSubprocessExecutor
from app.contracts.game_agent import GameBuildRequest, WorkspaceRef
from app.contracts.gamespec import CreatorGameSpec

_ENV_LOCAL = Path(__file__).parent / ".env.local"


def _creds() -> dict[str, str]:
    creds: dict[str, str] = {}
    if _ENV_LOCAL.is_file():
        for line in _ENV_LOCAL.read_text().splitlines():
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


def _gamespec() -> CreatorGameSpec:
    return CreatorGameSpec.model_validate({
        "schema_version": 1, "title": "smoke",
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


creds = _creds()
has_opengame = bool(_cli_js())
has_creds = bool(creds.get("OPENAI_API_KEY") and creds.get("OPENAI_BASE_URL"))


@pytest.mark.skipif(
    not (has_opengame and has_creds),
    reason="opengame not installed or OPENAI_API_KEY/OPENAI_BASE_URL not in backend/tests/.env.local or env",
)
def test_opengame_adapter_real_create_flow(workspace: Path) -> None:
    """A real OpenGameAdapter create run produces a standard GameBuildResult + events.

    The real provider may succeed, fail, or produce invalid output; we assert the
    adapter ran the real flow and returned a standard result with an event stream —
    not a specific status. Artifact validation must run against the real workspace.
    """

    async def run_once() -> tuple:
        adapter = OpenGameAdapter(
            AsyncSubprocessExecutor(),
            model=creds.get("OPENAI_MODEL", "kimi-k3"),
            openai_api_key=creds["OPENAI_API_KEY"],
            openai_base_url=creds["OPENAI_BASE_URL"],
            sandbox=False,
            timeout_seconds=300,
            opengame_cli_js=_cli_js(),
        )
        request = GameBuildRequest(
            project_id="smoke-proj", build_id="smoke-build", operation="create",
            creator_game_spec=_gamespec(),
            runtime_build_spec=_gamespec().to_runtime_build_spec(),
            workspace=WorkspaceRef(root=str(workspace), allowed_paths=["dist", "src"]),
            baseline_playable=None,
            request_text="Build a simple Pong clone with paddle controls.",
        )
        handle = await adapter.start(request)
        events = [event async for event in adapter.stream_events(handle)]
        result = await adapter.result(handle)
        return result, events

    result, events = asyncio.run(run_once())

    # Standard result, not a raw provider object.
    assert result.status in {"succeeded", "failed", "invalid_output", "timed_out", "cancelled"}
    # A real run emits at least a starting event.
    assert len(events) >= 1
    assert events[0].sequence == 1
    # If it succeeded, the adapter must have found a real artifact (not from log keywords).
    if result.status == "succeeded":
        assert result.preview_entry is not None
        assert (workspace / result.preview_entry).exists()
