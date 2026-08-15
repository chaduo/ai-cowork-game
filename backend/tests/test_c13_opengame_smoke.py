"""C13 — real isolated- workspace smoke (rebaseline daily gate).

"Confirmed GameSpec starts one real Build and creates one isolated Candidate."

This drives the full BuildService → real OpenGameAdapter path against the real
opengame CLI and asserts the C13 isolation contract: the run executes inside the
prepared per-run workspace (``data/workspaces/{run_id}/{session_id}`` layout, here
rooted under a tmp dir), the imported artifact is a validated path under that
workspace (no escape), and a non-success run's partial workspace is discarded.

Credentials come from backend/tests/.env.local (gitignored) or env vars — never
hardcoded, never committed. Skipped if opengame or credentials are unavailable.
Async start/stream/result share one event loop (the adapter's background task
cannot survive a loop tear-down — see test_c10_opengame_adapter_smoke).
"""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.agents.opengame_adapter import OpenGameAdapter
from app.agents.subprocess_executor import AsyncSubprocessExecutor
from app.agents.workspace import WorkspaceManager
from app.models import Run
from app.services.builds import BuildService
from tests.test_c10_opengame_adapter_smoke import _cli_js, _creds
from tests.test_c11_build_orchestration import confirmed_project

creds = _creds()
has_opengame = bool(_cli_js())
has_creds = bool(creds.get("OPENAI_API_KEY") and creds.get("OPENAI_BASE_URL"))


@pytest.mark.skipif(
    not (has_opengame and has_creds),
    reason="opengame not installed or OPENAI_API_KEY/OPENAI_BASE_URL not in backend/tests/.env.local or env",
)
def test_c13_real_build_uses_prepared_isolated_workspace(isolated_database, tmp_path: Path) -> None:
    """A real create run via BuildService+OpenGameAdapter runs inside the prepared
    per-run workspace; on success the artifact is a validated path under it, on
    non-success the partial workspace is discarded."""

    async def run_once(session: Session, service: BuildService, build_id: str):
        return await service.execute_build(build_id)

    with Session(isolated_database) as session:
        project = confirmed_project(session)
        ws_root = tmp_path / "ws"
        adapter = OpenGameAdapter(
            AsyncSubprocessExecutor(),
            model=creds.get("OPENAI_MODEL", "kimi-k3"),
            openai_api_key=creds["OPENAI_API_KEY"],
            openai_base_url=creds["OPENAI_BASE_URL"],
            sandbox=False,
            timeout_seconds=300,
            opengame_cli_js=_cli_js(),
            workspace_manager=WorkspaceManager(root_base=ws_root),
        )
        service = BuildService(session, adapter, workspace_manager=WorkspaceManager(root_base=ws_root))
        job = service.create_build(project.id, build_id="b-c13-real", run_id="run-c13-real")
        result = asyncio.run(run_once(session, service, job.build_id))
        run = session.get(Run, job.run_id)

        # The run executed inside a prepared per-run workspace under ws_root.
        assert run.workspace_path is not None
        assert str(ws_root) in run.workspace_path  # under the prepared root
        expected = ws_root / "run-c13-real" / "run-c13-real"
        assert Path(run.workspace_path).resolve() == expected.resolve()

        if result.status == "succeeded":
            # The platform-validated artifact lives under the workspace (no escape).
            assert run.workspace_status == "prepared"  # success keeps the workspace
            assert result.preview_entry is not None
            artifact = Path(run.workspace_path) / result.preview_entry
            assert artifact.exists(), f"artifact not in workspace: {artifact}"
        else:
            # A non-success real run leaves a partial workspace — discarded, not reused.
            assert run.workspace_status == "discarded"
            assert not Path(run.workspace_path).exists()
