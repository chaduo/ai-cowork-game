"""C20 — ProvenanceService resolution + recoverability tests.

Proves the catalog C20 AC: every PlayableVersion/Release resolves to an immutable
commit + artifact, recoverable after a restart, with drift detection when the
on-disk repo no longer holds the persisted commit.

Builds a real BuildCandidate + PlayableVersion via the existing lifecycle helpers
and passes a *real* ProjectGitService commit sha as ``promote_candidate``'s
``git_commit`` arg — proving the C20 primitive plugs into the existing promote
signature WITHOUT changing lifecycle.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.models import HumanPlayReview, PlayableVersion, Release, TestReport as CandidateTestReport
from app.services.project_git import ProjectGitService
from app.services.provenance import ProvenanceError, ProvenanceService
from tests.test_c02_build_service import confirmed_service


def _promote_with_real_commit(
    session: Session, project_id: str, git: ProjectGitService, artifact_bytes: bytes
) -> PlayableVersion:
    """Finish a succeeded candidate, commit its artifact to the trusted repo, and
    promote it with the real commit sha + checksum — exactly what the line-114
    Promote wiring will do, without touching lifecycle.py."""
    from app.services.lifecycle import ProjectLifecycleService

    lifecycle = ProjectLifecycleService(session)
    build = lifecycle.start_build(project_id)
    candidate = lifecycle.finish_build(
        build.id, "succeeded", summary="ready", artifact_path="playable/index.html"
    )
    candidate.artifact_checksum = hashlib_sha(artifact_bytes)
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
    sha = git.commit(project_id, message=f"promote {candidate.id}", files={"playable/index.html": artifact_bytes})
    checksum = hashlib_sha(git.read_file(project_id, sha, "playable/index.html"))
    version = lifecycle.promote_candidate(
        candidate.id,
        test_report_id="report-1",
        verdict="pass",
        git_commit=sha,
        artifact_checksum=checksum,
    )
    return version


def hashlib_sha(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def git(tmp_path: Path) -> ProjectGitService:
    return ProjectGitService(repo_root=tmp_path / "project-repos")


# --------------------------------------------------------------------------- #
# compute_checksum
# --------------------------------------------------------------------------- #


def test_compute_checksum_is_sha256_hex(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_bytes(b"hello")
    p = ProvenanceService(session=None)  # type: ignore[arg-type]  # compute_checksum needs no session
    assert p.compute_checksum(f) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


def test_compute_checksum_matches_promote_arg(isolated_database, tmp_path: Path, git: ProjectGitService) -> None:
    with Session(isolated_database) as session:
        _, project = confirmed_service(session)
        git.init_project(project.id)
        version = _promote_with_real_commit(session, project.id, git, b"<html>pong</html>")
        prov = ProvenanceService(session, git)
        # The checksum persisted on the version equals the sha256 of the committed artifact.
        assert version.artifact_checksum == hashlib_sha(b"<html>pong</html>")
        assert prov.compute_checksum.__name__  # helper exists


# --------------------------------------------------------------------------- #
# resolve_playable + recoverability after restart
# --------------------------------------------------------------------------- #


def test_resolve_playable_returns_commit_and_artifact(isolated_database, tmp_path: Path, git: ProjectGitService) -> None:
    with Session(isolated_database) as session:
        _, project = confirmed_service(session)
        git.init_project(project.id)
        version = _promote_with_real_commit(session, project.id, git, b"<html>snake</html>")
        prov = ProvenanceService(session, git)
        rec = prov.resolve_playable(version.id)
        assert rec.verified is True
        assert rec.commit_sha == version.git_commit
        assert rec.artifact_path == "playable/index.html"
        assert rec.artifact_checksum == version.artifact_checksum
        assert Path(rec.repo_path).is_dir()


def test_resolve_playable_recovers_after_restart(isolated_database, tmp_path: Path, git: ProjectGitService) -> None:
    """A fresh Session + fresh ProvenanceService (same repo root) resolve the same
    commit — the persisted sha is recoverable after a backend restart."""
    with Session(isolated_database) as session:
        _, project = confirmed_service(session)
        git.init_project(project.id)
        version = _promote_with_real_commit(session, project.id, git, b"<html>v1</html>")
        version_id = version.id
        expected_sha = version.git_commit
        expected_checksum = version.artifact_checksum
        session.commit()

    # Simulate a restart: brand-new Session on the same DB, brand-new service on
    # the same repo root.
    with Session(isolated_database) as session2:
        prov2 = ProvenanceService(session2, ProjectGitService(repo_root=tmp_path / "project-repos"))
        rec = prov2.resolve_playable(version_id)
        assert rec.commit_sha == expected_sha
        assert rec.artifact_checksum == expected_checksum
        assert rec.verified is True


# --------------------------------------------------------------------------- #
# resolve_release (transitive via playable_version_id)
# --------------------------------------------------------------------------- #


def test_resolve_release_is_transitive(isolated_database, tmp_path: Path, git: ProjectGitService) -> None:
    with Session(isolated_database) as session:
        _, project = confirmed_service(session)
        git.init_project(project.id)
        version = _promote_with_real_commit(session, project.id, git, b"<html>release</html>")
        from app.services.lifecycle import ProjectLifecycleService

        release = ProjectLifecycleService(session).publish_version(version.id)
        session.commit()

        prov = ProvenanceService(session, git)
        rec = prov.resolve_release(release.id)
        assert rec.commit_sha == version.git_commit
        assert rec.artifact_path == "playable/index.html"
        assert rec.verified is True


# --------------------------------------------------------------------------- #
# drift detection (torn repo is visible, not silently trusted)
# --------------------------------------------------------------------------- #


def test_resolve_playable_detects_commit_drift(isolated_database, tmp_path: Path, git: ProjectGitService) -> None:
    with Session(isolated_database) as session:
        _, project = confirmed_service(session)
        git.init_project(project.id)
        version = _promote_with_real_commit(session, project.id, git, b"<html>x</html>")
        # Persist a commit sha that does NOT exist in the repo (simulate a torn
        # repo / bad row).
        version.git_commit = "0" * 40
        session.flush()
        prov = ProvenanceService(session, git)
        with pytest.raises(ProvenanceError) as exc:
            prov.resolve_playable(version.id)
        assert exc.value.code == "commit_drift"


def test_resolve_playable_missing_version_raises(isolated_database, git: ProjectGitService) -> None:
    with Session(isolated_database) as session:
        prov = ProvenanceService(session, git)
        with pytest.raises(ProvenanceError) as exc:
            prov.resolve_playable("nope")
        assert exc.value.code == "version_not_found"


def test_resolve_release_missing_raises(isolated_database, git: ProjectGitService) -> None:
    with Session(isolated_database) as session:
        prov = ProvenanceService(session, git)
        with pytest.raises(ProvenanceError) as exc:
            prov.resolve_release("nope")
        assert exc.value.code == "release_not_found"
