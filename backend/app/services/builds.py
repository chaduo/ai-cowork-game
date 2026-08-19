"""C11 build orchestration over the provider-neutral GameAgent contract."""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.game_agent import GameAgent
from app.agents.workspace import WorkspaceManager, WorkspacePaths
from app.contracts.game_agent import (
    AffectedScope,
    AgentRunHandle,
    BuildOverride,
    ContractError,
    ContractProfile,
    GameBuildRequest,
    GameBuildResult,
    ResourceReference,
    RunEvent,
    WorkspaceRef,
)
from app.contracts.gamespec import CreatorGameSpec, RuntimeBuildSpec
from app.models import Build, BuildCandidate, BuildContext, Project, Run, new_id, utc_now
from app.repositories.runs import RUN_ACTIVE_STATUSES, RUN_EXECUTION_STATUSES, RunRepository
from app.services.lifecycle import ProjectLifecycleService


TERMINAL_EVENT_KINDS = frozenset({"completed", "cancelled", "terminal", "orphaned"})


@dataclass(frozen=True)
class BuildJob:
    build_id: str
    run_id: str


class BuildService:
    def __init__(self, session: Session, agent: GameAgent, *, workspace_manager: WorkspaceManager | None = None) -> None:
        self.session = session
        self.agent = agent
        self.lifecycle = ProjectLifecycleService(session)
        self.runs = RunRepository(session)
        # C13: owns per-run workspace creation + discard. Default roots at
        # data/workspaces (gitignored runtime data); tests inject a tmp-rooted one.
        self._workspace = workspace_manager or WorkspaceManager()
        self._handles: dict[str, AgentRunHandle] = {}

    def create_build(
        self,
        project_id: str,
        *,
        operation: str = "create",
        request_text: str = "",
        build_id: str | None = None,
        run_id: str | None = None,
        affected_scope: AffectedScope | None = None,
        resource_references: list[ResourceReference] | None = None,
        implementation_dependencies: list[str] | None = None,
        relevant_overrides: list[BuildOverride] | None = None,
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
                self._ensure_context(
                    existing,
                    affected_scope=affected_scope,
                    resource_references=resource_references,
                    implementation_dependencies=implementation_dependencies,
                    relevant_overrides=relevant_overrides,
                )
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
        self._create_context(
            build,
            affected_scope=affected_scope,
            resource_references=resource_references,
            implementation_dependencies=implementation_dependencies,
            relevant_overrides=relevant_overrides,
        )
        self.session.flush()
        return BuildJob(build.id, run.id)

    def _request_for(self, build: Build, run: Run) -> GameBuildRequest:
        project = self.session.get(Project, build.project_id)
        if project is None:
            raise ValueError("project not found")
        context = self._ensure_context(build)
        creator = CreatorGameSpec.model_validate_json(context.gamespec_snapshot_json)
        runtime = RuntimeBuildSpec.model_validate_json(context.runtime_build_spec_json)
        # C13: run against the prepared isolated workspace (absolute). Falls back
        # to a relative path only for pre-C13 runs with no persisted workspace.
        root = run.workspace_path or f"runs/{run.id}"
        return GameBuildRequest(
            project_id=context.project_id,
            build_id=build.id,
            operation=context.operation,
            creator_game_spec=creator,
            runtime_build_spec=runtime,
            workspace=WorkspaceRef(root=root, allowed_paths=["dist", "logs"]),
            baseline_playable=context.baseline_playable_version_id,
            request_text=context.request_text,
            affected_scope=AffectedScope.model_validate_json(context.affected_scope_json),
            resource_references=[ResourceReference.model_validate(item) for item in json.loads(context.resource_references_json)],
            implementation_dependencies=json.loads(context.implementation_dependencies_json),
            relevant_overrides=[BuildOverride.model_validate(item) for item in json.loads(context.relevant_overrides_json)],
            game_design_profile=ContractProfile.model_validate_json(context.game_design_profile_json),
            gamespec_profile=ContractProfile.model_validate_json(context.gamespec_profile_json),
            game_build_profile=ContractProfile.model_validate_json(context.game_build_profile_json),
        )

    def _prepare_workspace(self, run: Run) -> WorkspacePaths:
        """Create the isolated run workspace and persist its absolute path.

        Idempotent: a run with a persisted workspace_path is not re-prepared. V1
        uses one session per run (session_id = run.id); the {run_id}/{session_id}
        layout is retained for future multi-session resume.
        """
        if run.workspace_path:
            return WorkspacePaths(run_id=run.id, session_id=run.id, root=Path(run.workspace_path))
        paths = self._workspace.prepare(run.id, run.id)
        run.workspace_path = str(paths.root)
        run.workspace_status = "prepared"
        self.session.flush()
        return paths

    def _discard_workspace(self, run: Run) -> None:
        """Discard a (partial) workspace after cancel/failure/orphan and mark it.

        run-observability spec: a partial workspace is never trusted or reused on
        retry — retry gets a fresh run_id and thus a fresh workspace.
        """
        if run.workspace_path:
            self._workspace.discard_run(run.id)
        run.workspace_status = "discarded"
        self.session.flush()

    async def execute_build(self, build_id: str) -> GameBuildResult:
        build, run = self._job_records(build_id)
        if run.status == "waiting_for_input":
            return self._waiting_result(build, run)
        if run.status not in RUN_EXECUTION_STATUSES:
            return self._result_from_records(build, run)
        self._prepare_workspace(run)  # C13: isolated workspace before the agent runs
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
        self._prepare_workspace(run)  # C13: ensure a workspace exists for a fallback start
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
        parent_context = self._ensure_context(prior)
        self._copy_context(parent_context, retry)
        # C13: a fresh run_id means a fresh workspace — the prior run's partial
        # workspace was already discarded on its terminal/cancel/failure (or by
        # orphan recovery). retry never reuses a prior workspace path.
        run = self.runs.create_run(f"run-{retry.id}", retry.id)
        self.session.flush()
        return BuildJob(retry.id, run.id)

    def recover_orphaned_jobs(self) -> int:
        runs_recovered = self.runs.recover_orphaned_runs()
        builds_recovered = self.lifecycle.recover_orphaned_builds()
        # A succeeded run owns the Candidate artifact until promotion/import and
        # must survive process restarts. Only non-success terminal workspaces are
        # partial and unsafe to retain.
        lingering = self.session.scalars(
            select(Run).where(Run.workspace_status == "prepared")
        )
        for run in lingering:
            if run.status not in RUN_ACTIVE_STATUSES and run.status != "succeeded":
                self._discard_workspace(run)
        self.session.flush()
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
            # line-115: persist the OpenGame session id the adapter captured, so a
            # later resume (ContinuationService.resume_build) can re-drive the paused
            # session after the blocking decision resolves. Additive column write at
            # the existing flush; metadata is a free dict the adapter populates.
            session_id = result.metadata.get("opengame_session_id") if result.metadata else None
            if session_id:
                run.opengame_session_id = session_id
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
        if result.status == "succeeded":
            artifact_ref = result.preview_entry or (
                result.artifact_manifest[0].path if result.artifact_manifest else None
            )
            if not artifact_ref:
                raise ValueError("succeeded result requires an artifact")
            # Provider adapters may emit a generic terminal event. The platform
            # owns the success contract and must attach the artifact it scanned.
            terminal = terminal.model_copy(update={
                "stage": "complete",
                "kind": "completed",
                "progress": 1.0,
                "artifact_ref": artifact_ref,
                "error": None,
            })
        elif terminal.error is None and result.error is not None:
            # A provider's generic terminal event may omit its cause. Preserve
            # the platform decision so non-success runs remain auditable.
            terminal = terminal.model_copy(update={"error": result.error})
        self.runs.finish_run(run.id, result.status, terminal)
        diagnostics_json = json.dumps([item.model_dump(mode="json") for item in result.diagnostics], ensure_ascii=False)
        summary = "Build completed" if result.status == "succeeded" else (result.error.message if result.error else "Build failed")
        artifact_path = result.preview_entry or (result.artifact_manifest[0].path if result.artifact_manifest else None)
        artifact_checksum = next(
            (
                item.sha256
                for item in result.artifact_manifest
                if item.path == artifact_path and item.sha256
            ),
            None,
        )
        self.lifecycle.finish_build(
            build.id,
            result.status,
            summary=summary,
            artifact_path=artifact_path,
            artifact_checksum=artifact_checksum,
            failure_code=result.error.code if result.error else None,
            diagnostics_json=diagnostics_json or None,
            build_context_id=self._ensure_context(build).id,
        )
        candidate = self.session.scalar(select(BuildCandidate).where(BuildCandidate.build_id == build.id))
        if candidate is not None:
            candidate.artifact_manifest_json = (
                json.dumps(
                    [item.model_dump(mode="json") for item in result.artifact_manifest],
                    ensure_ascii=False,
                )
                if result.status == "succeeded"
                else None
            )
        # C13: a non-success run leaves a partial workspace — discard it so a
        # later retry can never trust or reuse it. A succeeded run keeps its
        # workspace (the artifact lives there until C14/C20 promote/import it).
        if result.status != "succeeded":
            self._discard_workspace(run)
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

    def _ensure_context(
        self,
        build: Build,
        *,
        affected_scope: AffectedScope | None = None,
        resource_references: list[ResourceReference] | None = None,
        implementation_dependencies: list[str] | None = None,
        relevant_overrides: list[BuildOverride] | None = None,
    ) -> BuildContext:
        context = self.session.scalar(select(BuildContext).where(BuildContext.build_id == build.id))
        if context is not None:
            return context
        return self._create_context(
            build,
            affected_scope=affected_scope,
            resource_references=resource_references,
            implementation_dependencies=implementation_dependencies,
            relevant_overrides=relevant_overrides,
        )

    def _create_context(
        self,
        build: Build,
        *,
        affected_scope: AffectedScope | None = None,
        resource_references: list[ResourceReference] | None = None,
        implementation_dependencies: list[str] | None = None,
        relevant_overrides: list[BuildOverride] | None = None,
    ) -> BuildContext:
        existing = self.session.scalar(select(BuildContext).where(BuildContext.build_id == build.id))
        if existing is not None:
            return existing
        creator = self.lifecycle.validate_gamespec_revision(build.gamespec_revision_id)
        runtime = creator.to_runtime_build_spec()
        scope = affected_scope or AffectedScope()
        resources = resource_references or []
        dependencies = implementation_dependencies or []
        overrides = relevant_overrides or []
        design_profile = ContractProfile(name="creator-game-design", version="1", capabilities=[])
        gamespec_profile = ContractProfile(name="creator-gamespec", version="1", capabilities=[])
        build_profile = ContractProfile(name="runtime-build", version="1", capabilities=[])
        gamespec_json = _canonical_json(creator.model_dump(mode="json"))
        runtime_json = _canonical_json(runtime.model_dump(mode="json"))
        scope_json = _canonical_json(scope.model_dump(mode="json"))
        resources_json = _canonical_json([item.model_dump(mode="json") for item in resources])
        dependencies_json = _canonical_json(dependencies)
        overrides_json = _canonical_json([item.model_dump(mode="json") for item in overrides])
        design_profile_json = _canonical_json(design_profile.model_dump(mode="json"))
        gamespec_profile_json = _canonical_json(gamespec_profile.model_dump(mode="json"))
        build_profile_json = _canonical_json(build_profile.model_dump(mode="json"))
        context_payload = {
            "project_id": build.project_id,
            "gamespec_revision_id": build.gamespec_revision_id,
            "gamespec_snapshot_hash": _sha256(gamespec_json),
            "runtime_build_spec_hash": _sha256(runtime_json),
            "baseline_playable_version_id": build.baseline_playable_version_id,
            "affected_scope": json.loads(scope_json),
            "resource_references": json.loads(resources_json),
            "implementation_dependencies": json.loads(dependencies_json),
            "relevant_overrides": json.loads(overrides_json),
            "game_design_profile": json.loads(design_profile_json),
            "gamespec_profile": json.loads(gamespec_profile_json),
            "game_build_profile": json.loads(build_profile_json),
            "operation": build.operation,
            "request_text": build.request_text,
        }
        context = BuildContext(
            id=new_id(),
            build_id=build.id,
            project_id=build.project_id,
            gamespec_revision_id=build.gamespec_revision_id,
            gamespec_snapshot_json=gamespec_json,
            gamespec_snapshot_hash=_sha256(gamespec_json),
            runtime_build_spec_json=runtime_json,
            runtime_build_spec_hash=_sha256(runtime_json),
            baseline_playable_version_id=build.baseline_playable_version_id,
            affected_scope_json=scope_json,
            resource_references_json=resources_json,
            implementation_dependencies_json=dependencies_json,
            relevant_overrides_json=overrides_json,
            game_design_profile_json=design_profile_json,
            gamespec_profile_json=gamespec_profile_json,
            game_build_profile_json=build_profile_json,
            operation=build.operation,
            request_text=build.request_text,
            context_hash=_sha256(_canonical_json(context_payload)),
            created_at=utc_now(),
        )
        self.session.add(context)
        self.session.flush()
        return context

    def _copy_context(self, source: BuildContext, build: Build) -> BuildContext:
        existing = self.session.scalar(select(BuildContext).where(BuildContext.build_id == build.id))
        if existing is not None:
            return existing
        context = BuildContext(
            id=new_id(),
            build_id=build.id,
            project_id=source.project_id,
            gamespec_revision_id=source.gamespec_revision_id,
            gamespec_snapshot_json=source.gamespec_snapshot_json,
            gamespec_snapshot_hash=source.gamespec_snapshot_hash,
            runtime_build_spec_json=source.runtime_build_spec_json,
            runtime_build_spec_hash=source.runtime_build_spec_hash,
            baseline_playable_version_id=source.baseline_playable_version_id,
            affected_scope_json=source.affected_scope_json,
            resource_references_json=source.resource_references_json,
            implementation_dependencies_json=source.implementation_dependencies_json,
            relevant_overrides_json=source.relevant_overrides_json,
            game_design_profile_json=source.game_design_profile_json,
            gamespec_profile_json=source.gamespec_profile_json,
            game_build_profile_json=source.game_build_profile_json,
            operation=source.operation,
            request_text=source.request_text,
            context_hash=source.context_hash,
            created_at=utc_now(),
        )
        self.session.add(context)
        self.session.flush()
        return context


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
