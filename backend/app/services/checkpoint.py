"""C20 line-114 — Git checkpoints for Confirm GDD/GameSpec, Promote and Publish.

A zhang-owned wrapper over zhao's ``ProjectLifecycleService`` gates. It does NOT
modify the gate functions (zhao's ownership / the business state machine stays
in SQLite); it records an immutable Git content checkpoint *after* each gate
using the C20 primitives (``ProjectGitService`` commit/tag, ``ProvenanceService``
checksum/resolve) and persists the commit sha on the new provenance columns.

Binding requirements:
- Catalog C20 AC: every confirmed GDD/GameSpec, promoted PlayableVersion, and
  published Release resolves to an immutable commit + artifact, recoverable after
  restart. Git is NOT the business state machine — the lifecycle gate still owns
  the transition; this service only adds the content checkpoint.
- design.md:49-52 — commit allowed files into the trusted repo; do not commit
  every attempt (checkpoints are explicit, at the gates).
- Owner split — zhang owns Git content versioning; zhao owns the lifecycle
  services. ``CheckpointService`` is zhang's; ``lifecycle.py`` gate bodies unchanged.

The content is committed under the C20 ``ALLOWED_TOP_DIRS`` layout: ``gdd/``,
``gamespec/``, ``playable/``. Commits are content-addressed and deterministic
(C20), so re-confirming identical content returns the same sha (idempotent).
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Build,
    BuildCandidate,
    GameDesignRevision,
    GameSpecRevision,
    PlayableVersion,
    Release,
    Run,
)
from app.services.lifecycle import ProjectLifecycleService
from app.services.project_git import ProjectGitService
from app.services.provenance import ProvenanceService

_PLACEHOLDER_COMMIT = "pending-checkpoint"

PLAYABLE_OUTPUT_EXTENSIONS = frozenset({
    ".html", ".css", ".js", ".mjs", ".json", ".wasm",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg",
    ".mp3", ".ogg", ".wav", ".m4a", ".aac", ".flac",
    ".woff", ".woff2", ".ttf", ".otf",
})
MAX_PLAYABLE_FILES = 500
MAX_PLAYABLE_FILE_BYTES = 20 * 1024 * 1024
MAX_PLAYABLE_TOTAL_BYTES = 100 * 1024 * 1024
_PROTECTED_OUTPUT_NAMES = frozenset({".git", ".env", ".env.local", "credentials.json", "secrets.json"})
_PROTECTED_OUTPUT_SUFFIXES = (".key", ".pem")


class CheckpointService:
    """Records immutable Git checkpoints at the Confirm/Promote/Publish gates.

    ``session`` is the SQLite session; ``git`` is the ``ProjectGitService`` whose
    repo root the checkpoints live under (default ``data/project-repos``); tests
    inject a tmp-rooted one. The lifecycle service is constructed internally
    (zhao's gates are called unchanged).
    """

    def __init__(self, session: Session, *, git: ProjectGitService | None = None) -> None:
        self.session = session
        self._git = git or ProjectGitService()
        self._lifecycle = ProjectLifecycleService(session)
        self._provenance = ProvenanceService(session, git=self._git)

    # -- Confirm GDD ------------------------------------------------------- #

    def confirm_gdd(self, project_id: str, revision_id: str) -> str:
        """Record the GDD checkpoint after the lifecycle gate confirmed it.

        Commits ``gdd/{revision_id}.json`` (the confirmed GDD content), persists
        the sha on ``GameDesignRevision.git_commit``, and tags ``gdd-{number}``.
        Idempotent: identical content re-confirmed returns the same sha (C20
        determinism) and is a no-op on the row + tag.
        """
        revision = self.session.get(GameDesignRevision, revision_id)
        if revision is None or revision.project_id != project_id:
            raise ValueError("design revision not found")
        if revision.status != "confirmed":
            raise ValueError("design revision is not confirmed")
        self._git.init_project(project_id)
        sha = self._git.commit(
            project_id,
            message=f"confirm GDD revision {revision.revision_number}",
            files={f"gdd/{revision.id}.json": revision.content_json.encode("utf-8")},
        )
        revision.git_commit = sha
        self.session.flush()
        self._git.tag(project_id, name=f"gdd-{revision.revision_number}", sha=sha)
        return sha

    # -- Confirm GameSpec -------------------------------------------------- #

    def confirm_gamespec(self, project_id: str, revision_id: str) -> str:
        """Record the GameSpec checkpoint after the lifecycle gate confirmed it.

        Commits ``gamespec/{revision_id}.json``, persists the sha on
        ``GameSpecRevision.git_commit``, and tags ``gamespec-{number}``.
        """
        revision = self.session.get(GameSpecRevision, revision_id)
        if revision is None or revision.project_id != project_id:
            raise ValueError("gamespec revision not found")
        if revision.status != "confirmed":
            raise ValueError("gamespec revision is not confirmed")
        self._git.init_project(project_id)
        sha = self._git.commit(
            project_id,
            message=f"confirm GameSpec revision {revision.revision_number}",
            files={f"gamespec/{revision.id}.json": revision.content_json.encode("utf-8")},
        )
        revision.git_commit = sha
        self.session.flush()
        self._git.tag(project_id, name=f"gamespec-{revision.revision_number}", sha=sha)
        return sha

    # -- Promote ----------------------------------------------------------- #

    def promote(
        self,
        candidate_id: str,
        *,
        test_report_id: str,
        verdict: str,
    ) -> PlayableVersion:
        """Promote a Candidate AND record its real artifact checkpoint.

        Calls zhao's ``lifecycle.promote_candidate`` (the business transition —
        creates the PlayableVersion, updates the playable pointer), then imports
        the candidate's real artifact into the trusted repo: reads the artifact
        from the run workspace (``Run.workspace_path`` from C13), commits it under
        ``playable/index.html``, computes its sha256, and overwrites the version's
        ``git_commit`` / ``artifact_checksum`` with the real values. The lifecycle
        signature still requires a ``git_commit`` arg (backward compat) — a
        placeholder is passed and replaced here with the real sha.
        """
        candidate = self.session.get(BuildCandidate, candidate_id)
        if candidate is None:
            raise ValueError("candidate not found")
        if candidate.status == "promoted":
            return self._lifecycle.promote_candidate(candidate.id, git_commit=_PLACEHOLDER_COMMIT)
        if candidate.status != "succeeded":
            raise ValueError("only a succeeded candidate can be promoted")

        files = self.collect_candidate_output(candidate)
        artifact_bytes = files["playable/index.html"]
        self._git.init_project(candidate.project_id)
        sha = self._git.commit(
            candidate.project_id,
            message=f"promote candidate {candidate.id}",
            files=files,
        )
        checksum = self._sha256_bytes(artifact_bytes)

        # Snapshot validation and checkpointing happen before this business gate,
        # so a bad runtime tree cannot advance the current Playable pointer.
        version = self._lifecycle.promote_candidate(
            candidate_id,
            test_report_id=test_report_id,
            verdict=verdict,
            git_commit=sha,
            artifact_checksum=checksum,
        )
        version.git_commit = sha
        version.artifact_checksum = checksum
        version.artifact_path = "playable/index.html"
        self.session.flush()
        self._git.tag(candidate.project_id, name=f"playable-{version.number}", sha=sha)
        return version

    # -- Publish ----------------------------------------------------------- #

    def publish(self, version_id: str) -> Release:
        """Publish a PlayableVersion AND record its release checkpoint.

        Calls zhao's ``lifecycle.publish_version`` (the business transition —
        creates the Release), then tags ``release-{number}`` pointing at the
        version's ``git_commit`` and persists that sha on ``Release.git_commit`` so
        a Release resolves to an immutable commit (a publish-time snapshot), not
        only transitively via its PlayableVersion.
        """
        release = self._lifecycle.publish_version(version_id)
        if release.git_commit:
            # C16's lifecycle snapshot already carries the real commit. Ensure
            # the human-readable tag exists as well, without creating a second
            # commit or Release on retries.
            self._git.init_project(release.project_id)
            self._git.tag(
                release.project_id,
                name=f"release-{release.number}",
                sha=release.git_commit,
            )
            return release  # already checkpointed (idempotent)
        version = self.session.get(PlayableVersion, version_id)
        if version is None or not version.git_commit:
            raise ValueError("playable version has no git checkpoint to publish")
        self._git.tag(version.project_id, name=f"release-{release.number}", sha=version.git_commit)
        release.git_commit = version.git_commit
        self.session.flush()
        return release

    # -- internals --------------------------------------------------------- #

    def collect_candidate_output(self, candidate: BuildCandidate) -> dict[str, bytes]:
        """Collect a bounded, browser-runnable output tree for an immutable checkpoint."""

        rel = candidate.artifact_path or "index.html"
        run = self.session.scalar(
            select(Run).where(Run.build_id == candidate.build_id).order_by(Run.created_at.desc())
        )
        entry_candidates: list[Path] = []
        if run is not None and run.workspace_path:
            entry_candidates.append(Path(run.workspace_path) / rel)
        entry_candidates.append(Path(rel))

        entry = next((path for path in entry_candidates if path.is_file()), None)
        if entry is None:
            raise ValueError(
                f"candidate artifact not found on disk: {rel} "
                f"(looked in run workspace and cwd)"
            )
        if entry.is_symlink():
            raise ValueError("playable output symlink rejected")
        output_root = entry.parent.resolve()
        if output_root.is_symlink():
            raise ValueError("playable output root symlink rejected")

        accepted: list[tuple[Path, str, int]] = []
        total_bytes = 0
        for path in sorted(output_root.rglob("*"), key=lambda item: item.relative_to(output_root).as_posix()):
            relative = path.relative_to(output_root)
            if path.is_symlink():
                raise ValueError(f"playable output symlink rejected: {relative.as_posix()}")
            if not path.is_file():
                continue
            if any(part in _PROTECTED_OUTPUT_NAMES for part in relative.parts) or path.name.endswith(_PROTECTED_OUTPUT_SUFFIXES):
                raise ValueError(f"protected playable output rejected: {relative.as_posix()}")
            if any(part.startswith(".") for part in relative.parts):
                continue
            if path.suffix.lower() not in PLAYABLE_OUTPUT_EXTENSIONS:
                continue
            size = path.stat().st_size
            if size > MAX_PLAYABLE_FILE_BYTES:
                raise ValueError(f"playable output file exceeds 20 MiB: {relative.as_posix()}")
            accepted.append((path, relative.as_posix(), size))
            total_bytes += size
            if len(accepted) > MAX_PLAYABLE_FILES:
                raise ValueError(f"playable output has too many files (max {MAX_PLAYABLE_FILES})")
            if total_bytes > MAX_PLAYABLE_TOTAL_BYTES:
                raise ValueError("playable output exceeds 100 MiB")

        files = {f"playable/{relative}": path.read_bytes() for path, relative, _ in accepted}
        entry_relative = entry.resolve().relative_to(output_root).as_posix()
        entry_key = f"playable/{entry_relative}"
        if entry_key not in files or Path(entry_relative).name != "index.html":
            raise ValueError("playable output requires an index.html entry")
        if entry_key != "playable/index.html":
            files["playable/index.html"] = files.pop(entry_key)
        return files

    @staticmethod
    def _sha256_bytes(data: bytes) -> str:
        import hashlib
        return hashlib.sha256(data).hexdigest()
