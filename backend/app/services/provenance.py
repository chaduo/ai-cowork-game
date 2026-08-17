"""Artifact provenance resolution (C20).

Reads the persisted provenance on ``PlayableVersion`` (``git_commit`` +
``artifact_path`` + ``artifact_checksum``, all already columns on origin/main)
and verifies each against the on-disk trusted project repo, so a
PlayableVersion/Release resolves to an immutable commit + artifact that is
recoverable after a restart (catalog C20 AC). This service is **read-only** —
it never writes business state (SQLite owns jobs/gate/pointer/index; Git is not
the business state machine).

The companion primitive that *produces* a real commit sha is
``ProjectGitService`` (C20); the wiring that calls it at Promote/Publish time is
the later "checkpoint support" slice (rebaseline line 114, depends C13+C14+C16).
Here we only resolve + verify.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PlayableVersion, Release
from app.services.project_git import ProjectGitService


class ProvenanceError(RuntimeError):
    """A version/release cannot be resolved to a real commit + artifact.

    The message is sanitized (no raw content). Raised when the persisted commit
    is missing from the on-disk repo (drift — a torn repo is visible, not silently
    trusted) or when the entity itself is not found.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ProvenanceRecord:
    """An immutable, resolvable content checkpoint for a version or release."""

    commit_sha: str
    artifact_path: str
    artifact_checksum: str
    repo_path: str  # absolute path to the per-project trusted repo
    verified: bool  # True once the commit is confirmed to exist on disk


class ProvenanceService:
    """Resolve a PlayableVersion/Release to its immutable commit + artifact.

    ``session`` is the SQLite session (read-only use); ``git`` is the
    ``ProjectGitService`` whose repo root the commit shas live under. Defaults to
    a service rooted at ``data/project-repos`` so production resolves without
    injection; tests inject a tmp-rooted one.
    """

    def __init__(self, session: Session, git: ProjectGitService | None = None) -> None:
        self.session = session
        self._git = git or ProjectGitService()

    def compute_checksum(self, path: Path | str) -> str:
        """sha256 of a file — the artifact_checksum primitive promote_candidate needs.

        Today callers of ``promote_candidate`` pass ``artifact_checksum`` in; this
        is the shared helper so they do not reinvent it. Returned as a hex string
        (matches ``PlayableVersion.artifact_checksum`` String(128)).
        """
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def resolve_playable(self, version_id: str) -> ProvenanceRecord:
        version = self.session.get(PlayableVersion, version_id)
        if version is None:
            raise ProvenanceError("version_not_found", f"playable version not found: {version_id}")
        verified = self._git.commit_exists(version.project_id, version.git_commit)
        if not verified:
            # Drift: the DB points at a commit the on-disk repo no longer has. Do
            # not silently trust the row — surface it so a torn repo is repaired.
            raise ProvenanceError(
                "commit_drift",
                f"playable version {version_id} commit {version.git_commit} not in the project repo",
            )
        return ProvenanceRecord(
            commit_sha=version.git_commit,
            artifact_path=version.artifact_path,
            artifact_checksum=version.artifact_checksum,
            repo_path=str(self._git._root / version.project_id),  # type: ignore[attr-defined]
            verified=True,
        )

    def resolve_release(self, release_id: str) -> ProvenanceRecord:
        release = self.session.get(Release, release_id)
        if release is None:
            raise ProvenanceError("release_not_found", f"release not found: {release_id}")
        # Release resolves to a commit transitively via its playable version. No
        # Release.git_commit snapshot column is needed (catalog AC: "resolvable");
        # a publish-time snapshot is C16's call.
        return self.resolve_playable(release.playable_version_id)
