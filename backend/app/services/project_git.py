"""Project Git content store + checkpoint primitives (C20).

A leaf service: it owns the trusted per-project Git repository that holds the
immutable content history (GDD, GameSpec, code, assets, playable artifacts) and
the checkpoint primitives (commit/tag/read) over it. It imports no
Project / GameSpec / Candidate / Playable / Release / Vue / FastAPI repository
types beyond the ``project_id`` string it is keyed by — business state stays in
SQLite (catalog C20 AC: Git is NOT the business state machine).

Binding requirements:
- ``design.md:49-52``: commit *allowed files* into the trusted repo, store the
  artifact, change the playable pointer (the pointer lives in SQLite — this
  service only produces the immutable commit sha + content). Do NOT commit every
  attempt — failure history and published history stay separate, so this service
  commits only on an explicit checkpoint call, never implicitly.
- ``design.md:64``: import resolves paths, rejects traversal/symlinks/protected
  files, and scans output for secrets. This is the *content-side* guard (what
  gets committed). The *workspace-side* guard (the runtime can't reach this repo)
  is C13's; C20 only asserts the layout invariant in tests.
- catalog C20 AC: every PlayableVersion/Release resolves to an immutable commit +
  artifact, recoverable after restart. The commit sha a checkpoint returns is the
  immutable truth; ``ProvenanceService`` (C20) verifies it on disk on resolve.

Driver: dulwich (pure-Python Git) — no system-git subprocess per commit, cross-
platform, deterministic. See pyproject.toml.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dulwich.objects import Blob, Tree, Commit
from dulwich.repo import Repo

from app.redaction import redact_text

# Controlled file layout: only these top-level content directories may be
# committed. A checkpoint caller writes files under one of these; anything else
# is rejected so the repo cannot become a dumping ground for arbitrary runtime
# output. The repo itself lives outside any run workspace (C13 invariant).
ALLOWED_TOP_DIRS = frozenset({"gdd", "gamespec", "src", "assets", "playable"})

# Files the trusted repo must never contain even if a caller asks. Matches the
# .gitignore secret-file set + the git internals.
_PROTECTED_NAMES = frozenset({".git", ".env", ".env.local", "credentials.json", "secrets.json"})
_PROTECTED_SUFFIXES = (".key", ".pem")


class ContentPolicyError(ValueError):
    """A file the caller tried to commit is outside the allowlist or carries a secret.

    The message is sanitized (no raw content), so it is safe to surface as a
    diagnostic / audit reason.
    """


@dataclass(frozen=True)
class ProjectRepo:
    project_id: str
    path: Path  # absolute: data/project-repos/{project_id}


@dataclass(frozen=True)
class GitFileEntry:
    path: str
    size_bytes: int


class ProjectGitService:
    """Owns the trusted per-project Git repository and checkpoint primitives.

    The repo root is configurable (default ``data/project-repos``); the per-project
    path is ``{root}/{project_id}`` so it is deterministic and recoverable after a
    restart without a DB column (same pattern as C13's ``data/workspaces``).
    """

    def __init__(self, repo_root: Path | str = "data/project-repos") -> None:
        self._root = Path(repo_root)

    # -- lifecycle --------------------------------------------------------- #

    def init_project(self, project_id: str) -> ProjectRepo:
        """Create the per-project repo if absent and return it. Idempotent."""
        if not project_id:
            raise ValueError("project_id is required")
        repo_path = self._root / project_id
        repo_path.mkdir(parents=True, exist_ok=True)
        if not (repo_path / ".git").exists():
            Repo.init(str(repo_path))
        return ProjectRepo(project_id=project_id, path=repo_path.resolve())

    # -- checkpoints ------------------------------------------------------- #

    def commit(
        self,
        project_id: str,
        *,
        message: str,
        files: dict[str, bytes],
    ) -> str:
        """Commit ``files`` (rel_path -> content) into the project repo.

        Returns the commit sha. Only allowlisted content paths are accepted
        (``ContentPolicyError`` otherwise); committed text is scanned for secrets.
        Content-addressed determinism: if the resulting tree is identical to the
        current HEAD tree, no new commit is made and the existing HEAD sha is
        returned (no empty/duplicate commits — failure history and published
        history stay separate, per design.md:52).
        """
        if not message:
            raise ValueError("commit message is required")
        normalized = self._normalize_files(files)
        repo_path = self._root / project_id
        repo = Repo(str(repo_path))
        try:
            return self._commit(repo, message, normalized)
        finally:
            repo.close()

    def tag(self, project_id: str, *, name: str, sha: str) -> None:
        """Create an immutable tag ``name`` -> ``sha``. Human-readable checkpoint."""
        if not name or not sha:
            raise ValueError("tag name and sha are required")
        repo_path = self._root / project_id
        repo = Repo(str(repo_path))
        try:
            tag_ref = f"refs/tags/{name}"
            existing = repo.get_refs().get(tag_ref.encode())
            target = sha.encode()
            if existing == target:
                return  # idempotent: same tag -> same sha
            if existing is not None:
                raise ContentPolicyError(f"tag already exists with a different target: {name}")
            repo.refs[tag_ref.encode()] = target
        finally:
            repo.close()

    def read_file(self, project_id: str, sha: str, rel_path: str) -> bytes:
        """Fetch ``rel_path`` as of commit ``sha`` (provenance recovery)."""
        self._validate_member(rel_path)
        repo_path = self._root / project_id
        repo = Repo(str(repo_path))
        try:
            try:
                obj = repo.get_object(sha.encode())
            except KeyError as exc:
                raise ValueError(f"commit not found: {sha}") from exc
            if not isinstance(obj, Commit):
                raise ValueError(f"not a commit: {sha}")
            tree = repo.get_object(obj.tree)
            blob = self._lookup_path(repo, tree, rel_path)
            if blob is None:
                raise KeyError(f"file not in commit {sha}: {rel_path}")
            return blob.data
        finally:
            repo.close()

    def list_files(
        self,
        project_id: str,
        sha: str,
        prefix: str | None = None,
    ) -> list[GitFileEntry]:
        """List blobs in an immutable commit without checking out its tree."""

        normalized_prefix: str | None = None
        if prefix is not None:
            self._validate_member(prefix)
            normalized_prefix = prefix.replace("\\", "/").strip().strip("/")

        repo_path = self._root / project_id
        repo = Repo(str(repo_path))
        try:
            try:
                commit = repo.get_object(sha.encode())
            except KeyError as exc:
                raise ValueError(f"commit not found: {sha}") from exc
            if not isinstance(commit, Commit):
                raise ValueError(f"not a commit: {sha}")
            root = repo.get_object(commit.tree)
            if not isinstance(root, Tree):
                raise ValueError(f"commit has no tree: {sha}")

            entries: list[GitFileEntry] = []

            def walk(tree: Tree, parent: str = "") -> None:
                for entry in tree.iteritems(name_order=True):
                    name = entry.path.decode("utf-8")
                    path = f"{parent}/{name}" if parent else name
                    obj = repo.get_object(entry.sha)
                    if isinstance(obj, Tree):
                        walk(obj, path)
                    elif isinstance(obj, Blob):
                        if normalized_prefix is None or path == normalized_prefix or path.startswith(f"{normalized_prefix}/"):
                            entries.append(GitFileEntry(path=path, size_bytes=len(obj.data)))

            walk(root)
            return sorted(entries, key=lambda item: item.path)
        finally:
            repo.close()

    def commit_exists(self, project_id: str, sha: str) -> bool:
        """True if ``sha`` is a real commit object in the project repo (drift check)."""
        repo_path = self._root / project_id
        if not (repo_path / ".git").exists():
            return False
        repo = Repo(str(repo_path))
        try:
            try:
                obj = repo.get_object(sha.encode())
            except KeyError:
                return False
            return isinstance(obj, Commit)
        finally:
            repo.close()

    # -- internals --------------------------------------------------------- #

    def _normalize_files(self, files: dict[str, bytes]) -> list[tuple[str, bytes]]:
        out: list[tuple[str, bytes]] = []
        for rel_path, content in files.items():
            self._validate_member(rel_path)
            self._scan_for_secrets(rel_path, content)
            # Normalize separators so the tree builder splits on "/" regardless of
            # whether the caller passed POSIX "/" or Windows "\\" paths.
            out.append((rel_path.replace("\\", "/").strip(), content))
        return out

    def _commit(self, repo: Repo, message: str, files: list[tuple[str, bytes]]) -> str:
        # Build a nested tree from the committed files (clean-tree model: each
        # checkpoint is exactly the files passed, not a merge with prior state —
        # failure history and published history stay separate per design.md:52).
        store = repo.object_store
        new_tree = self._build_nested_tree(store, files)

        # Determinism: identical tree -> return existing HEAD sha, no new commit.
        head_ref = repo.get_refs().get(b"refs/heads/master") or repo.get_refs().get(b"refs/heads/main")
        if head_ref is not None:
            head_commit = store[head_ref]
            if isinstance(head_commit, Commit) and head_commit.tree == new_tree.id:
                return head_ref.decode("ascii")

        commit = Commit()
        commit.tree = new_tree.id
        commit.author = commit.committer = b"ai-cowork-game <noreply@ai-cowork-game.local>"
        commit.message = message.encode("utf-8")
        # Deterministic commit metadata: no parent + zero timestamp keeps the sha
        # content-addressed (same tree -> same sha), so identical checkpoints are
        # stable and recoverable. A real author/committer timestamp would make the
        # sha depend on wall-clock time and break determinism + replay.
        commit.commit_time = 0
        commit.commit_timezone = 0
        commit.author_time = 0
        commit.author_timezone = 0
        if head_ref is not None:
            commit.parents = [head_ref]
        store.add_object(commit)

        # Advance the default branch (dulwich init creates "master"; use refs/heads/master).
        repo.refs[b"refs/heads/master"] = commit.id
        return commit.id.decode("ascii")

    @staticmethod
    def _build_nested_tree(store, files: list[tuple[str, bytes]]) -> Tree:
        """Build a nested Tree (subtrees per directory) from ``files``.

        dulwich ``Tree.add`` takes a single path component and ``Tree.id`` is
        computed from its entries, so subtrees must be built **bottom-up**: a
        directory's id is only final once all its children are added, and the
        parent must capture that final id. ``playable/index.html`` becomes
        subtree ``playable`` (id final after ``index.html`` is added) -> blob
        ``index.html``, never a flat entry with a slash in its name.
        """
        # 1. Nest files into a dir tree: {dir: {name: blob_content | subdict}}.
        root_dict: dict[str, object] = {}
        for rel_path, content in files:
            parts = rel_path.split("/")
            node = root_dict
            for part in parts[:-1]:
                node = node.setdefault(part, {})  # type: ignore[assignment]
            node[parts[-1]] = content

        # 2. Build trees bottom-up so each subtree id is final before its parent
        #    captures it.
        def build_tree(node: dict[str, object]) -> Tree:
            tree = Tree()
            for name, value in node.items():
                key = name.encode("utf-8")
                if isinstance(value, bytes):
                    blob = Blob.from_string(value)
                    store.add_object(blob)
                    tree[key] = (0o100644, blob.id)
                else:
                    subtree = build_tree(value)
                    store.add_object(subtree)
                    tree[key] = (0o040000, subtree.id)
            return tree

        root_tree = build_tree(root_dict)
        store.add_object(root_tree)
        return root_tree

    def _lookup_path(self, repo: Repo, tree, rel_path: str):
        parts = rel_path.split("/")
        current = tree
        for part in parts:
            mode, sha = current[part.encode("utf-8")]
            obj = repo.get_object(sha)
            from dulwich.objects import Tree as _Tree
            if isinstance(obj, _Tree):
                current = obj
                continue
            return obj
        return None

    @staticmethod
    def _validate_member(rel_path: str) -> None:
        if not rel_path:
            raise ContentPolicyError("empty path")
        rel = rel_path.replace("\\", "/").strip()
        if rel.startswith(("/", "~")):
            raise ContentPolicyError("absolute path rejected")
        if "://" in rel:
            raise ContentPolicyError("url-like path rejected")
        if "\x00" in rel:
            raise ContentPolicyError("nul byte in path")
        if len(rel) >= 2 and rel[1] == ":" and rel[0].isalpha():
            raise ContentPolicyError("absolute path rejected")
        parts = [p for p in rel.split("/") if p not in ("", ".")]
        if ".." in parts:
            raise ContentPolicyError("parent traversal rejected")
        if not parts:
            raise ContentPolicyError("empty path")
        # Protected names anywhere in the chain.
        for part in parts:
            if part in _PROTECTED_NAMES:
                raise ContentPolicyError(f"protected path rejected: {part}")
        if any(parts[-1].endswith(suf) for suf in _PROTECTED_SUFFIXES):
            raise ContentPolicyError("protected suffix rejected")
        # Top-level dir must be in the allowlist.
        if parts[0] not in ALLOWED_TOP_DIRS:
            raise ContentPolicyError(f"path not in allowed content dirs: {parts[0]}")

    @staticmethod
    def _scan_for_secrets(rel_path: str, content: bytes) -> None:
        # Scan text-ish content for secret patterns. Binary content (decode
        # errors) is skipped — secrets live in text; a binary blob that happens
        # to contain the bytes is not a credential leak vector into the repo.
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            return
        redacted = redact_text(text, max_length=len(text))
        if redacted != text:
            raise ContentPolicyError(f"committed content contains a secret pattern: {rel_path}")
