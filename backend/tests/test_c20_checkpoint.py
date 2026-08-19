"""C20 line-114 — Confirm/Promote/Publish Git checkpoint wiring.

Verifies the rebaseline Aug-16 zhang item: each lifecycle gate produces a real,
immutable, recoverable Git checkpoint via ``CheckpointService`` (zhang-owned),
without modifying ``lifecycle.py`` gate bodies (zhao-owned). The four gates:

- Confirm GDD  → ``GameDesignRevision.git_commit``  + ``gdd/{rev}.json`` in the repo
- Confirm GameSpec → ``GameSpecRevision.git_commit`` + ``gamespec/{rev}.json``
- Promote      → ``PlayableVersion.git_commit`` (REAL sha, not a dummy string) +
                 ``playable/index.html`` committed + sha256 artifact_checksum
- Publish      → ``Release.git_commit`` (snapshot) + ``release-{n}`` tag

Each checkpoint round-trips (``ProjectGitService.read_file``), is idempotent
(re-confirmed → same sha), and is recoverable after a restart (fresh service on
the same repo root resolves the same commit). ``ProvenanceService.resolve_*``
verifies the on-disk commit (no silent drift).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Build,
    BuildCandidate,
    GameDesign,
    GameDesignRevision,
    GameSpecRevision,
    HumanPlayReview,
    PlayableVersion,
    Project,
    Run,
    TestReport as CandidateTestReport,
)
from app.services.checkpoint import CheckpointService
import app.services.checkpoint as checkpoint_module
from app.services.lifecycle import ProjectLifecycleService
from app.services.project_git import ProjectGitService
from app.services.provenance import ProvenanceService
from tests.test_c05_design_api import draft_payload
from tests.test_c05_gamespec_contract import valid_gamespec


@pytest.fixture
def git(tmp_path: Path) -> ProjectGitService:
    return ProjectGitService(repo_root=tmp_path / "project-repos")


def _confirmed_project(session: Session) -> str:
    lifecycle = ProjectLifecycleService(session)
    project = lifecycle.create_project("Checkpoint Garden", "A checkpoint test game")
    design = lifecycle.submit_design(project.id, draft_payload())
    # Drive readiness to "ready" so confirm_design passes (draft_payload's readiness).
    session.flush()
    revision = session.get(GameDesignRevision, design.current_revision_id)
    # Set readiness ready so confirm_design doesn't raise DesignNotReadyError.
    from app.contracts.design import DesignReadiness
    ready = DesignReadiness(status="ready", blockers=[], unresolved_decisions=[])
    import json
    revision.readiness_json = json.dumps(ready.model_dump(mode="json"), ensure_ascii=False)
    session.flush()
    lifecycle.confirm_design(project.id)
    gamespec_rev = lifecycle.create_gamespec_revision(project.id, valid_gamespec())
    session.commit()
    return project.id, gamespec_rev.id, revision.id


# --------------------------------------------------------------------------- #
# Confirm GDD
# --------------------------------------------------------------------------- #


def test_confirm_gdd_records_immutable_checkpoint(isolated_database, tmp_path: Path, git: ProjectGitService) -> None:
    with Session(isolated_database) as session:
        project_id, _, design_rev_id = _confirmed_project(session)
        sha = CheckpointService(session, git=git).confirm_gdd(project_id, design_rev_id)
        session.commit()

        rev = session.get(GameDesignRevision, design_rev_id)
        assert rev.git_commit == sha
        # Round-trip: the committed GDD content is recoverable from the sha.
        committed = git.read_file(project_id, sha, f"gdd/{design_rev_id}.json")
        assert committed == rev.content_json.encode("utf-8")
        # Tag exists.
        assert git.commit_exists(project_id, sha)


def test_confirm_gdd_is_idempotent(isolated_database, tmp_path: Path, git: ProjectGitService) -> None:
    with Session(isolated_database) as session:
        project_id, _, design_rev_id = _confirmed_project(session)
        sha1 = CheckpointService(session, git=git).confirm_gdd(project_id, design_rev_id)
        sha2 = CheckpointService(session, git=git).confirm_gdd(project_id, design_rev_id)
        session.commit()
        assert sha1 == sha2  # C20 determinism: identical content → same sha, no dup commit


# --------------------------------------------------------------------------- #
# Confirm GameSpec
# --------------------------------------------------------------------------- #


def test_confirm_gamespec_records_immutable_checkpoint(isolated_database, tmp_path: Path, git: ProjectGitService) -> None:
    with Session(isolated_database) as session:
        project_id, gamespec_rev_id, _ = _confirmed_project(session)
        # confirm_gamespec_revision requires the design confirmed first (done in helper).
        lifecycle = ProjectLifecycleService(session)
        lifecycle.confirm_gamespec_revision(project_id, gamespec_rev_id)
        sha = CheckpointService(session, git=git).confirm_gamespec(project_id, gamespec_rev_id)
        session.commit()

        rev = session.get(GameSpecRevision, gamespec_rev_id)
        assert rev.git_commit == sha
        committed = git.read_file(project_id, sha, f"gamespec/{gamespec_rev_id}.json")
        assert committed == rev.content_json.encode("utf-8")


# --------------------------------------------------------------------------- #
# Promote (real artifact checkpoint)
# --------------------------------------------------------------------------- #


def _candidate_with_artifact(
    session: Session,
    project_id: str,
    workspace_root: Path,
    artifact: bytes,
    *,
    artifact_path: str = "index.html",
    extra_files: dict[str, bytes] | None = None,
) -> BuildCandidate:
    """Build a succeeded BuildCandidate whose artifact lives in a run workspace
    (mimics C13's prepared workspace + C10/C11's real artifact_path)."""
    workspace_root.mkdir(parents=True, exist_ok=True)
    entry = workspace_root / artifact_path
    entry.parent.mkdir(parents=True, exist_ok=True)
    entry.write_bytes(artifact)
    for relative_path, content in (extra_files or {}).items():
        output = workspace_root / relative_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)
    revision = session.scalar(
        select(GameSpecRevision).where(GameSpecRevision.project_id == project_id).order_by(GameSpecRevision.revision_number.desc())
    )
    build = Build(project_id=project_id, gamespec_revision_id=revision.id, status="succeeded")
    session.add(build)
    session.flush()
    # Record the run workspace so CheckpointService can read the artifact.
    run = Run(id=f"run-{build.id}", build_id=build.id, status="succeeded", last_sequence=1,
              workspace_path=str(workspace_root), workspace_status="prepared")
    session.add(run)
    session.flush()
    candidate = BuildCandidate(project_id=project_id, build_id=build.id, status="succeeded",
                                artifact_path=artifact_path, artifact_checksum=hashlib.sha256(artifact).hexdigest(), summary="c")
    session.add(candidate)
    session.flush()
    # C14 Promote is intentionally stricter than the original C20 checkpoint
    # fixture: a candidate needs a persisted platform PASSED report and an
    # accepted Human Play Review. Seed those durable gates instead of relying on
    # the deprecated caller-supplied verdict arguments.
    candidate.test_gate_status = "ready"
    session.add(CandidateTestReport(
        candidate_id=candidate.id,
        runtime_verdict="pass",
        platform_verdict="PASSED",
        status="PASSED",
        severity="none",
        summary="fixture platform verification passed",
    ))
    session.add(HumanPlayReview(
        candidate_id=candidate.id,
        decision="accepted",
        amendment_status="not_required",
        drift_status="clear",
        notes="fixture human play review accepted",
    ))
    session.flush()
    return candidate


def test_promote_records_real_artifact_checkpoint(isolated_database, tmp_path: Path, git: ProjectGitService) -> None:
    artifact = b"<html><body><h1>real pong</h1></body></html>"
    with Session(isolated_database) as session:
        project_id, _, _ = _confirmed_project(session)
        workspace_root = tmp_path / "ws" / project_id
        candidate = _candidate_with_artifact(session, project_id, workspace_root, artifact)
        version = CheckpointService(session, git=git).promote(
            candidate.id, test_report_id="report-1", verdict="pass",
        )
        session.commit()

        # git_commit is a REAL sha (read back the artifact), not a dummy string.
        committed = git.read_file(project_id, version.git_commit, "playable/index.html")
        assert committed == artifact
        # artifact_checksum is the real sha256 of the artifact.
        assert version.artifact_checksum == hashlib.sha256(artifact).hexdigest()
        # ProvenanceService verifies the on-disk commit (no drift).
        rec = ProvenanceService(session, git=git).resolve_playable(version.id)
        assert rec.commit_sha == version.git_commit and rec.verified


def test_promote_checkpoints_complete_web_output_and_survives_workspace_deletion(
    isolated_database,
    tmp_path: Path,
    git: ProjectGitService,
) -> None:
    import shutil

    html = b"<html><img src='assets/hero.png'></html>"
    png = b"\x89PNG\r\n\x1a\nimage"
    svg = b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"
    ogg = b"OggS audio"
    font = b"wOFF font"
    with Session(isolated_database) as session:
        project_id, _, _ = _confirmed_project(session)
        workspace_root = tmp_path / "ws" / project_id
        candidate = _candidate_with_artifact(
            session,
            project_id,
            workspace_root,
            html,
            artifact_path="dist/index.html",
            extra_files={
                "dist/assets/hero.png": png,
                "dist/assets/icon.svg": svg,
                "dist/audio/theme.ogg": ogg,
                "dist/fonts/game.woff": font,
                "dist/main.js": b"console.log('game')",
                "dist/styles.css": b"body { margin: 0; }",
                "source/ignored.png": b"outside output root",
            },
        )

        version = CheckpointService(session, git=git).promote(
            candidate.id, test_report_id="report", verdict="pass",
        )
        session.commit()
        version_id = version.id
        commit = version.git_commit

    shutil.rmtree(workspace_root)

    with Session(isolated_database) as restarted:
        version = restarted.get(PlayableVersion, version_id)
        assert version is not None
        assert git.read_file(project_id, commit, "playable/index.html") == html
        assert git.read_file(project_id, commit, "playable/assets/hero.png") == png
        assert git.read_file(project_id, commit, "playable/assets/icon.svg") == svg
        assert git.read_file(project_id, commit, "playable/audio/theme.ogg") == ogg
        assert git.read_file(project_id, commit, "playable/fonts/game.woff") == font
        with pytest.raises(KeyError):
            git.read_file(project_id, commit, "playable/source/ignored.png")


def test_snapshot_policy_failure_does_not_advance_playable(
    isolated_database,
    tmp_path: Path,
    git: ProjectGitService,
    monkeypatch,
) -> None:
    monkeypatch.setattr(checkpoint_module, "MAX_PLAYABLE_FILES", 1)
    with Session(isolated_database) as session:
        project_id, _, _ = _confirmed_project(session)
        candidate = _candidate_with_artifact(
            session,
            project_id,
            tmp_path / "ws" / project_id,
            b"<html></html>",
            extra_files={"hero.png": b"png"},
        )

        with pytest.raises(ValueError, match="too many files"):
            CheckpointService(session, git=git).promote(
                candidate.id, test_report_id="report", verdict="pass",
            )

        session.refresh(candidate)
        project = session.get(Project, project_id)
        assert candidate.status == "succeeded"
        assert project is not None and project.current_playable_version_id is None


def test_snapshot_rejects_symlink_without_advancing_playable(
    isolated_database,
    tmp_path: Path,
    git: ProjectGitService,
) -> None:
    with Session(isolated_database) as session:
        project_id, _, _ = _confirmed_project(session)
        workspace = tmp_path / "ws" / project_id
        candidate = _candidate_with_artifact(session, project_id, workspace, b"<html></html>")
        target = workspace / "outside.png"
        target.write_bytes(b"png")
        (workspace / "linked.png").symlink_to(target)

        with pytest.raises(ValueError, match="symlink"):
            CheckpointService(session, git=git).promote(
                candidate.id, test_report_id="report", verdict="pass",
            )

        project = session.get(Project, project_id)
        assert candidate.status == "succeeded"
        assert project is not None and project.current_playable_version_id is None


def test_promote_without_hook_runner_still_checkpoints(isolated_database, tmp_path: Path, git: ProjectGitService) -> None:
    """Promote does NOT require the browser test hook — the checkpoint is about the
    artifact content, independent of verification (C12) which is a separate gate."""
    artifact = b"<html>plain game</html>"
    with Session(isolated_database) as session:
        project_id, _, _ = _confirmed_project(session)
        candidate = _candidate_with_artifact(session, project_id, tmp_path / "ws" / project_id, artifact)
        version = CheckpointService(session, git=git).promote(
            candidate.id, test_report_id="r", verdict="pass",
        )
        session.commit()
        assert git.read_file(project_id, version.git_commit, "playable/index.html") == artifact


# --------------------------------------------------------------------------- #
# Publish
# --------------------------------------------------------------------------- #


def test_publish_records_release_checkpoint(isolated_database, tmp_path: Path, git: ProjectGitService) -> None:
    artifact = b"<html>release</html>"
    with Session(isolated_database) as session:
        project_id, _, _ = _confirmed_project(session)
        candidate = _candidate_with_artifact(session, project_id, tmp_path / "ws" / project_id, artifact)
        version = CheckpointService(session, git=git).promote(
            candidate.id, test_report_id="r", verdict="pass",
        )
        release = CheckpointService(session, git=git).publish(version.id)
        session.commit()

        # Release.git_commit is a publish-time snapshot of the version's commit.
        assert release.git_commit == version.git_commit
        # ProvenanceService.resolve_release resolves to the same commit.
        rec = ProvenanceService(session, git=git).resolve_release(release.id)
        assert rec.commit_sha == version.git_commit and rec.verified


# --------------------------------------------------------------------------- #
# Recoverability after restart
# --------------------------------------------------------------------------- #


def test_checkpoints_recoverable_after_restart(isolated_database, tmp_path: Path, git: ProjectGitService) -> None:
    artifact = b"<html>restart</html>"
    with Session(isolated_database) as session:
        project_id, _, _ = _confirmed_project(session)
        candidate = _candidate_with_artifact(session, project_id, tmp_path / "ws" / project_id, artifact)
        version = CheckpointService(session, git=git).promote(
            candidate.id, test_report_id="r", verdict="pass",
        )
        release = CheckpointService(session, git=git).publish(version.id)
        session.commit()
        version_id, release_id, expected_sha = version.id, release.id, version.git_commit

    # Simulate a restart: fresh session + fresh services on the same repo root.
    with Session(isolated_database) as session2:
        git2 = ProjectGitService(repo_root=tmp_path / "project-repos")
        prov2 = ProvenanceService(session2, git=git2)
        rec_v = prov2.resolve_playable(version_id)
        rec_r = prov2.resolve_release(release_id)
        assert rec_v.commit_sha == expected_sha and rec_v.verified
        assert rec_r.commit_sha == expected_sha and rec_r.verified


# --------------------------------------------------------------------------- #
# Owner-boundary invariant: lifecycle.py gate bodies unchanged
# --------------------------------------------------------------------------- #


def test_lifecycle_gate_bodies_unchanged() -> None:
    """The C20 line-114 slice must NOT modify lifecycle.py gate function bodies
    (zhao-owned). This test asserts the gate functions still take the same
    signatures (no ProjectGitService param added) — a cheap structural guard."""
    import inspect
    from app.services.lifecycle import ProjectLifecycleService
    promote_sig = inspect.signature(ProjectLifecycleService.promote_candidate)
    # Still requires the caller-supplied git_commit str (CheckpointService wraps, not changes).
    assert "git_commit" in promote_sig.parameters
    publish_sig = inspect.signature(ProjectLifecycleService.publish_version)
    assert list(publish_sig.parameters)[1:] == ["version_id"]  # only self + version_id
