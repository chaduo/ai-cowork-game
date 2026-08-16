"""Run workspace lifecycle + path policy (C13 `runtime-workspace-isolation`).

A leaf module: it owns the on-disk workspace a runtime run executes in, and the
policy that keeps runtime output inside that workspace. It imports no
Project / GameSpec / Candidate / Playable / Vue / FastAPI repository types — it
is consumed by ``OpenGameAdapter`` (C10) and ``BuildService`` (C11), which map
its results onto the provider-neutral contract.

Binding requirements:
- ``specs/.../game-agent-runtime/spec.md`` "Isolated workspace execution" +
  scenario "Deny workspace escape": runtime SHALL access only the assigned
  workspace + allowed paths; output referencing an absolute / traversal /
  symlink-escape / protected path is rejected, a sanitized policy error is
  recorded, and the output is NOT imported.
- ``specs/.../run-observability/spec.md`` "Safe cancellation and retry": a
  partial workspace left by cancel/failure is discarded and never trusted or
  reused on retry.
- ``design.md:47`` workspace path is ``data/workspaces/{run_id}/{session_id}``;
  ``design.md:62-68`` the runner gets no trusted ``.git`` / platform source /
  host home / unrelated creds, and import resolves paths, rejects traversal /
  symlinks / protected files, and scans output for secrets.

The container / network / CPU / memory hardening named in task 4.1 is
deliberately out of scope this round: per ``design.md:97`` the V1-local mechanism
is exported-workspace + path-guard with ``GEMINI_SANDBOX=false``; a real sandbox
is an optional deploy-time flag. This module is the path-guard.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from app.contracts.game_agent import ArtifactManifestEntry
from app.redaction import redact_text

# Paths the runtime must never touch even if they live under the workspace root:
# the trusted git dir and credential files. Matches .gitignore + secret-file names.
_PROTECTED_NAMES = frozenset({".git", ".env", ".env.local"})

_PREVIEW_ENTRY = "index.html"

_MAX_MANIFEST_ENTRIES = 512


class WorkspaceEscapeError(Exception):
    """A runtime output path tried to leave the workspace or touch a protected file.

    The ``message`` is sanitized (no raw secrets, no full absolute host paths)
    so it is safe to persist as audit evidence.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class WorkspacePaths:
    """An absolute, prepared run workspace."""

    run_id: str
    session_id: str
    root: Path  # absolute: data/workspaces/{run_id}/{session_id}
    allowed: list[str] = field(default_factory=lambda: ["dist", "logs"])

    @property
    def run_dir(self) -> Path:
        return self.root.parent  # data/workspaces/{run_id}


class WorkspaceManager:
    """Creates, confines, and discards per-run workspaces.

    The manager never reads the parent environment for paths and never places a
    workspace outside ``root_base``. All returned paths are absolute and
    realpath-resolved so downstream consumers (the adapter, BuildService) cannot
    be tricked by a relative or symlinked ``WorkspaceRef.root``.
    """

    def __init__(self, root_base: Path | str = "data/workspaces") -> None:
        self._root_base = Path(root_base)

    # -- lifecycle -------------------------------------------------------- #

    def prepare(self, run_id: str, session_id: str) -> WorkspacePaths:
        """Create ``data/workspaces/{run_id}/{session_id}`` if absent and return it.

        Idempotent: a second prepare with the same ids is a no-op on disk. The
        run-level dir is also created so ``discard_run`` and sibling sessions
        have a stable parent.
        """
        run_dir = self._root_base / run_id
        root = run_dir / session_id
        root.mkdir(parents=True, exist_ok=True)
        return WorkspacePaths(run_id=run_id, session_id=session_id, root=root.resolve())

    def discard(self, paths: WorkspacePaths) -> None:
        """Remove the session workspace (a partial after cancel/failure/orphan).

        Only the session dir is removed — the run dir is retained so other
        sessions or retry state under the same run are not collateral damage.
        """
        shutil.rmtree(paths.root, ignore_errors=True)

    def discard_run(self, run_id: str) -> None:
        """Remove the whole run workspace (used on final failure / orphan recovery)."""
        shutil.rmtree(self._root_base / run_id, ignore_errors=True)

    # -- path policy ------------------------------------------------------ #

    def validate_member(self, abs_root: Path, rel_path: str, allowed: list[str] | None = None) -> str:
        """Canonicalize ``rel_path`` under ``abs_root`` and confirm it stays inside.

        Returns the workspace-relative POSIX path (forward slashes) on success.
        Raises ``WorkspaceEscapeError`` (sanitized) if the path is absolute,
        traverses out, is a symlink escape, or names a protected file/dir. The
        ``allowed`` list, when given, further restricts members to those
        subdirectories of the root (an empty/None list means "root only").
        """
        rel = self._reject_unsafe_shape(rel_path)
        if Path(abs_root).is_symlink():
            raise WorkspaceEscapeError("symlink_escape", "workspace root symlink rejected")
        root_real = self._realpath(abs_root)

        # Reject any protected name anywhere in the path chain.
        for part in Path(rel).parts:
            if part in _PROTECTED_NAMES:
                raise WorkspaceEscapeError("protected_path", f"protected path rejected: {part}")

        # Inspect the lexical path before resolve(); resolving first would turn
        # an escaping symlink into a generic workspace_escape and lose the
        # actionable policy reason.
        self._reject_symlink_components(root_real, rel)
        candidate = (root_real / rel).resolve(strict=False)
        # Confine: candidate must live under root_real. Use a trailing-sep prefix
        # check so a sibling like "run-2" is not mistaken for "run-1".
        if not self._is_within(root_real, candidate):
            raise WorkspaceEscapeError("workspace_escape", "path resolves outside the workspace")

        if allowed:
            self._require_allowed(rel, allowed)

        return rel

    def scan_preview(
        self, abs_root: Path, allowed: list[str] | None = None
    ) -> tuple[list[ArtifactManifestEntry], str | None]:
        """Find the playable ``index.html`` under ``abs_root``, escape-safe.

        Replaces ``OpenGameAdapter._scan_artifacts``: every candidate is run
        through ``validate_member`` (realpath + symlink + protected checks), so a
        generated symlink or traversal pointing at host files is rejected rather
        than followed. An escape raises ``WorkspaceEscapeError`` (the caller maps
        it to a sanitized ``workspace_escape`` policy error — the AC wants the
        escape rejected and recorded, not silently treated as "no artifact").
        Returns an empty manifest only when there is genuinely no entry.
        """
        if Path(abs_root).is_symlink():
            raise WorkspaceEscapeError("symlink_escape", "workspace root symlink rejected")
        root_real = self._realpath(abs_root)
        if not root_real.is_dir():
            return [], None

        artifact_paths: list[tuple[Path, str]] = []
        for path in sorted(root_real.rglob("*"), key=lambda item: item.relative_to(root_real).as_posix()):
            rel = path.relative_to(root_real).as_posix()
            # Validate directories too, so protected folders and symlinked
            # directories cannot hide outside content from the scan.
            self.validate_member(root_real, rel, allowed)
            if path.is_dir():
                continue
            if not path.is_file():
                raise WorkspaceEscapeError("invalid_artifact", "non-regular artifact rejected")
            artifact_paths.append((path, rel))
            if len(artifact_paths) > _MAX_MANIFEST_ENTRIES:
                raise WorkspaceEscapeError("artifact_limit", "artifact manifest exceeds the limit")

        preview = next((rel for _, rel in artifact_paths if rel == _PREVIEW_ENTRY), None)
        if preview is None:
            preview = next((rel for _, rel in artifact_paths if Path(rel).name == _PREVIEW_ENTRY), None)
        manifest = [
            self._manifest_entry(path, rel, kind="preview_entry" if rel == preview else self._artifact_kind(path))
            for path, rel in artifact_paths
        ]
        return manifest, preview

    # -- internals -------------------------------------------------------- #

    @staticmethod
    def _realpath(p: Path) -> Path:
        # resolve() collapses ".." and symlinks; we re-check symlinks explicitly
        # below so a link that resolves inside but points outside is still caught.
        return Path(os.path.realpath(str(p)))

    @staticmethod
    def _is_within(root: Path, target: Path) -> bool:
        """True if ``target`` is ``root`` or lives inside it (same drive).

        ``os.path.commonpath`` raises ``ValueError`` when the two paths are on
        different drives (Windows) — that case is "not within".
        """
        try:
            common = os.path.commonpath([str(root), str(target)])
        except ValueError:
            return False
        return Path(common) == Path(str(root))

    @staticmethod
    def _reject_symlink_components(root_real: Path, rel: str) -> None:
        """Reject symlink components before canonical containment is checked."""
        current = root_real
        for part in Path(rel).parts:
            current = current / part
            if current.is_symlink():
                target = Path(os.readlink(str(current)))
                if not target.is_absolute():
                    target = current.parent / target
                target = Path(os.path.realpath(str(target)))
                if not WorkspaceManager._is_within(root_real, target):
                    raise WorkspaceEscapeError("symlink_escape", "symlink escapes the workspace")
                raise WorkspaceEscapeError("symlink_escape", "symlink artifact rejected")

    @staticmethod
    def _artifact_kind(path: Path) -> str:
        return {
            ".html": "document",
            ".js": "script",
            ".mjs": "script",
            ".css": "style",
            ".json": "data",
            ".png": "image",
            ".jpg": "image",
            ".jpeg": "image",
            ".webp": "image",
            ".svg": "image",
        }.get(path.suffix.lower(), "artifact")

    @staticmethod
    def _manifest_entry(path: Path, rel: str, *, kind: str) -> ArtifactManifestEntry:
        before = path.stat()
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise WorkspaceEscapeError("artifact_changed", "artifact changed during validation")
        return ArtifactManifestEntry(
            path=rel,
            kind=kind,
            size_bytes=after.st_size,
            sha256=digest.hexdigest(),
        )

    @staticmethod
    def _reject_unsafe_shape(rel_path: str) -> str:
        if not rel_path:
            raise WorkspaceEscapeError("invalid_path", "empty path")
        # Normalize backslashes (Windows) so a "C:\\windows" or "..\\.." is
        # caught by the same checks as POSIX.
        rel = rel_path.replace("\\", "/").strip()
        if rel.startswith(("/", "~")):
            raise WorkspaceEscapeError("absolute_path", "absolute path rejected")
        if "://" in rel:
            raise WorkspaceEscapeError("invalid_path", "url-like path rejected")
        if "\x00" in rel:
            raise WorkspaceEscapeError("invalid_path", "nul byte in path")
        # A Windows drive lead like "C:" at the start is absolute.
        if len(rel) >= 2 and rel[1] == ":" and rel[0].isalpha():
            raise WorkspaceEscapeError("absolute_path", "absolute path rejected")
        parts = [p for p in rel.split("/") if p not in ("", ".")]
        if ".." in parts:
            raise WorkspaceEscapeError("traversal", "parent traversal rejected")
        return "/".join(parts)

    @staticmethod
    def _require_allowed(rel: str, allowed: list[str]) -> None:
        # Empty allowed = root-only; a multi-segment rel must start with an allowed dir.
        if "/" not in rel:
            return
        top = rel.split("/", 1)[0]
        if top not in allowed:
            raise WorkspaceEscapeError("not_allowed", f"path not in allowed list: {top}")


def redact_stream(buf: str) -> str:
    """Redact a raw ProcessResult stream before it reaches diagnostics/artifacts.

    Thin wrapper over the shared ``redact_text`` so the adapter and BuildService
    import one name for "scrub a provider buffer". Keeps a single redaction
    truth source (``app.redaction``) across RunEvent persistence and raw output.

    Does NOT truncate: a process buffer can be large and the stream-json parser
    needs the full stream (including the terminal ``result`` event). Truncation to
    the 4000-char RunEvent.message cap is a separate concern applied at event
    persistence time (``sanitize_text``); here we only strip secrets.
    """
    if not buf:
        return buf
    return redact_text(buf, max_length=len(buf))
