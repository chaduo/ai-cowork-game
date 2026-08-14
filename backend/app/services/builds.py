"""C11 build orchestration over the provider-neutral GameAgent contract."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.game_agent import GameAgent
from app.contracts.game_agent import AgentRunHandle, ContractError, GameBuildRequest, GameBuildResult, RunEvent, WorkspaceRef
from app.models import Build, GameDesign, Project, Run
from app.repositories.runs import RUN_ACTIVE_STATUSES, RUN_EXECUTION_STATUSES, RunRepository
from app.services.lifecycle import ProjectLifecycleService


TERMINAL_EVENT_KINDS = frozenset({"completed", "cancelled", "terminal", "orphaned"})


@dataclass(frozen=True)
class BuildJob:
    build_id: str
    run_id: str


class BuildService:
    def __init__(self, session: Session, agent: GameAgent) -> None:
        self.session = session
        self.agent = agent
        self.lifecycle = ProjectLifecycleService(session)
        self.runs = RunRepository(session)
        self._handles: dict[str, AgentRunHandle] = {}

    def create_build(
        self,
        project_id: str,
        *,
        operation: str = "create",
        request_text: str = "",
        build_id: str | None = None,
        run_id: str | None = None,
    ) -> BuildJob:
        if build_id:
            existing = self.session.get(Build, build_id)
            if existing is not None:
                if existing.project_id != project_id:
                    raise ValueError("build id already belongs to another project")
                existing_run = self.session.scalar(select(Run).where(Run.build_id == existing.id))
                if run_id and existing_run and existing_run.id != run_id:
                    raise ValueError("build id already belongs to another run")
                if existing_run is None:
                    existing_run = self.runs.create_run(run_id or f"run-{existing.id}", existing.id)
                return BuildJob(existing.id, existing_run.id)

        project = self.session.get(Project, project_id)
        if project is None:
            raise ValueError("project not found")
        build = self.lifecycle.start_build(
            project_id,
            build_id=build_id,
            operation=operation,
            request_text=request_text,
        )
        stable_run_id = run_id or f"run-{build.id}"
        run = self.runs.create_run(stable_run_id, build.id)
        self.session.flush()
        return BuildJob(build.id, run.id)

    def _request_for(self, build: Build, run: Run) -> GameBuildRequest:
        project = self.session.get(Project, build.project_id)
        if project is None:
            raise ValueError("project not found")
        design = self.session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
        if design is None or design.status != "confirmed":
            raise ValueError("build requires confirmed Game Design")
        creator = self.lifecycle.validate_gamespec_revision(build.gamespec_revision_id)
        return GameBuildRequest(
            project_id=project.id,
            build_id=build.id,
            operation=build.operation,
            creator_game_spec=creator,
            runtime_build_spec=creator.to_runtime_build_spec(),
            workspace=WorkspaceRef(root=f"runs/{run.id}", allowed_paths=["dist", "logs"]),
            baseline_playable=build.baseline_playable_version_id,
            request_text=build.request_text,
        )

    async def execute_build(self, build_id: str) -> GameBuildResult:
        build, run = self._job_records(build_id)
        if run.status == "waiting_for_input":
            return self._waiting_result(build, run)
        if run.status not in RUN_EXECUTION_STATUSES:
            return self._result_from_records(build, run)
        request = self._request_for(build, run)
        try:
            handle = await self.agent.start(request)
            self._handles[build.id] = handle
            return await self._consume_agent(build, run, handle)
        except Exception as error:
            result = GameBuildResult(
                status="failed",
                diagnostics=[],
                metadata={"orchestrator": "build-service"},
                error=ContractError(code="agent_start_failed", message=str(error)),
            )
            return self._persist_result(build, run, result, None)

    async def cancel_build(self, build_id: str) -> GameBuildResult:
        build, run = self._job_records(build_id)
        if run.status not in RUN_ACTIVE_STATUSES:
            return self._result_from_records(build, run)
        self.runs.request_cancel(run.id)
        handle = self._handles.get(build.id)
        try:
            if handle is None:
                handle = await self.agent.start(self._request_for(build, run))
                self._handles[build.id] = handle
            await self.agent.cancel(handle)
            return await self._consume_agent(build, run, handle)
        except Exception as error:
            result = GameBuildResult(
                status="cancelled",
                diagnostics=[],
                metadata={"orchestrator": "build-service"},
                error=ContractError(code="cancel_failed", message=str(error)),
            )
            return self._persist_result(build, run, result, None)

    def retry_build(self, build_id: str) -> BuildJob:
        prior = self.session.get(Build, build_id)
        if prior is None:
            raise ValueError("build not found")
        retry = self.lifecycle.retry_build(build_id)
        run = self.runs.create_run(f"run-{retry.id}", retry.id)
        self.session.flush()
        return BuildJob(retry.id, run.id)

    def recover_orphaned_jobs(self) -> int:
        runs_recovered = self.runs.recover_orphaned_runs()
        builds_recovered = self.lifecycle.recover_orphaned_builds()
        return max(runs_recovered, builds_recovered)

    async def _consume_agent(self, build: Build, run: Run, handle: AgentRunHandle) -> GameBuildResult:
        terminal: RunEvent | None = None
        pending_event: RunEvent | None = None
        async for event in self.agent.stream_events(handle, after_sequence=0):
            normalized = event.model_copy(update={"run_id": run.id, "sequence": run.last_sequence + 1})
            if normalized.kind in TERMINAL_EVENT_KINDS:
                terminal = normalized
            elif normalized.kind in {"build.needs_input", "build_needs_input", "needs_input", "waiting_for_input"}:
                pending_event = normalized
            else:
                self.runs.append_event(normalized)
        result = await self.agent.result(handle)
        if result.status == "waiting_for_input":
            if pending_event is None or result.pending_decision is None:
                raise ValueError("waiting_for_input result is missing its pending decision event")
            self.runs.mark_waiting_for_input(run.id, pending_event, result.pending_decision)
            self.session.flush()
            return result
        return self._persist_result(build, run, result, terminal)

    def _persist_result(
        self,
        build: Build,
        run: Run,
        result: GameBuildResult,
        provider_terminal: RunEvent | None,
    ) -> GameBuildResult:
        if result.status == "waiting_for_input":
            raise ValueError("waiting_for_input must be persisted with its pending decision event")
        now = datetime.now(timezone.utc)
        terminal = provider_terminal or RunEvent(
            run_id=run.id,
            sequence=run.last_sequence + 1,
            stage="complete" if result.status == "succeeded" else "terminal",
            kind="completed" if result.status == "succeeded" else ("cancelled" if result.status == "cancelled" else "terminal"),
            message="Build completed" if result.status == "succeeded" else (result.error.message if result.error else "Build finished"),
            progress=1 if result.status == "succeeded" else None,
            artifact_ref=result.preview_entry,
            error=result.error,
            timestamp=now,
        )
        self.runs.finish_run(run.id, result.status, terminal)
        diagnostics_json = json.dumps([item.model_dump(mode="json") for item in result.diagnostics], ensure_ascii=False)
        summary = "Build completed" if result.status == "succeeded" else (result.error.message if result.error else "Build failed")
        artifact_path = result.preview_entry or (result.artifact_manifest[0].path if result.artifact_manifest else None)
        self.lifecycle.finish_build(
            build.id,
            result.status,
            summary=summary,
            artifact_path=artifact_path,
            failure_code=result.error.code if result.error else None,
            diagnostics_json=diagnostics_json or None,
        )
        self.session.flush()
        self._handles.pop(build.id, None)
        return result

    def _job_records(self, build_id: str) -> tuple[Build, Run]:
        build = self.session.get(Build, build_id)
        if build is None:
            raise ValueError("build not found")
        run = self.session.scalar(select(Run).where(Run.build_id == build.id).order_by(Run.created_at.desc()))
        if run is None:
            raise ValueError("run not found")
        return build, run

    @staticmethod
    def _result_from_records(build: Build, run: Run) -> GameBuildResult:
        if run.status == "succeeded":
            return GameBuildResult(status="succeeded", preview_entry=None, metadata={"build_id": build.id})
        status = run.status if run.status in {"failed", "cancelled", "timed_out", "invalid_output", "unsupported"} else "failed"
        return GameBuildResult(
            status=status,
            metadata={"build_id": build.id},
            error=ContractError(code=run.failure_code or "build_not_active", message=run.failure_message or "Build is not active"),
        )

    def _waiting_result(self, build: Build, run: Run) -> GameBuildResult:
        pending = self.runs.get_pending_decision(run.id)
        if pending is None:
            return GameBuildResult(
                status="failed",
                metadata={"build_id": build.id},
                error=ContractError(code="missing_pending_decision", message="Waiting run has no pending decision"),
            )
        return GameBuildResult(
            status="waiting_for_input",
            metadata={"build_id": build.id},
            pending_decision=pending,
        )
