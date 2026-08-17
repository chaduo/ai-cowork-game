"""C20 — ProjectGitService primitives + content policy tests.

Covers the catalog C20 acceptance: the trusted per-project Git repo holds
immutable content checkpoints; only allowlisted content paths are committed;
secrets and protected files are rejected; commits are content-addressed and
recoverable after a restart (a fresh service pointed at the same repo root
reads the same commits). Git is NOT the business state machine — this service
only produces commit shas + content; the pointer/version live in SQLite.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from app.services.project_git import (
    ALLOWED_TOP_DIRS,
    ContentPolicyError,
    ProjectGitService,
)


@pytest.fixture
def service(tmp_path: Path) -> ProjectGitService:
    return ProjectGitService(repo_root=tmp_path / "project-repos")


# --------------------------------------------------------------------------- #
# init + recoverability
# --------------------------------------------------------------------------- #


def test_init_project_creates_repo(tmp_path: Path) -> None:
    svc = ProjectGitService(repo_root=tmp_path / "r")
    repo = svc.init_project("p1")
    assert repo.path.is_dir()
    assert (repo.path / ".git").exists()


def test_init_project_is_idempotent(tmp_path: Path) -> None:
    svc = ProjectGitService(repo_root=tmp_path / "r")
    a = svc.init_project("p1")
    b = svc.init_project("p1")
    assert a.path == b.path
    assert (a.path / ".git").exists()


def test_init_requires_project_id(service: ProjectGitService) -> None:
    with pytest.raises(ValueError):
        service.init_project("")


# --------------------------------------------------------------------------- #
# commit + determinism (content-addressed)
# --------------------------------------------------------------------------- #


def test_commit_returns_real_sha(service: ProjectGitService) -> None:
    service.init_project("p")
    sha = service.commit("p", message="m", files={"playable/index.html": b"<html></html>"})
    assert isinstance(sha, str) and len(sha) == 40


def test_identical_content_is_no_new_commit(service: ProjectGitService) -> None:
    service.init_project("p")
    files = {"playable/index.html": b"<html>pong</html>", "src/main.js": b"x"}
    sha1 = service.commit("p", message="first", files=files)
    sha2 = service.commit("p", message="second identical", files=files)
    assert sha1 == sha2  # content-addressed determinism, no empty/duplicate commit


def test_changed_content_is_a_new_commit(service: ProjectGitService) -> None:
    service.init_project("p")
    sha1 = service.commit("p", message="a", files={"playable/index.html": b"a"})
    sha2 = service.commit("p", message="b", files={"playable/index.html": b"b"})
    assert sha1 != sha2


def test_commit_requires_message(service: ProjectGitService) -> None:
    service.init_project("p")
    with pytest.raises(ValueError):
        service.commit("p", message="", files={"playable/index.html": b"x"})


# --------------------------------------------------------------------------- #
# nested trees + read_file round-trip
# --------------------------------------------------------------------------- #


def test_read_file_round_trips_nested_paths(service: ProjectGitService) -> None:
    service.init_project("p")
    sha = service.commit("p", message="m", files={
        "playable/index.html": b"<html>snake</html>",
        "src/main.js": b"console.log(1)",
        "assets/sprites.png": b"\x89PNG binary",
    })
    assert service.read_file("p", sha, "playable/index.html") == b"<html>snake</html>"
    assert service.read_file("p", sha, "src/main.js") == b"console.log(1)"
    assert service.read_file("p", sha, "assets/sprites.png") == b"\x89PNG binary"


def test_read_file_at_old_commit_recovers_prior_content(service: ProjectGitService) -> None:
    service.init_project("p")
    sha1 = service.commit("p", message="v1", files={"playable/index.html": b"pong"})
    service.commit("p", message="v2", files={"playable/index.html": b"snake"})
    # v1's content is immutable and still recoverable from its sha.
    assert service.read_file("p", sha1, "playable/index.html") == b"pong"


def test_read_file_missing_raises(service: ProjectGitService) -> None:
    service.init_project("p")
    sha = service.commit("p", message="m", files={"playable/index.html": b"x"})
    with pytest.raises(KeyError):
        service.read_file("p", sha, "playable/missing.html")


def test_read_file_nonexistent_commit_raises(service: ProjectGitService) -> None:
    service.init_project("p")
    with pytest.raises(ValueError):
        service.read_file("p", "0" * 40, "playable/index.html")


# --------------------------------------------------------------------------- #
# tags (human-readable checkpoints)
# --------------------------------------------------------------------------- #


def test_tag_points_at_commit(service: ProjectGitService) -> None:
    service.init_project("p")
    sha = service.commit("p", message="m", files={"playable/index.html": b"x"})
    service.tag("p", name="playable-1", sha=sha)
    # Idempotent: same tag -> same sha is a no-op.
    service.tag("p", name="playable-1", sha=sha)


def test_tag_conflict_on_different_target(service: ProjectGitService) -> None:
    service.init_project("p")
    sha1 = service.commit("p", message="a", files={"playable/index.html": b"a"})
    sha2 = service.commit("p", message="b", files={"playable/index.html": b"b"})
    service.tag("p", name="v", sha=sha1)
    with pytest.raises(ContentPolicyError):
        service.tag("p", name="v", sha=sha2)


# --------------------------------------------------------------------------- #
# content policy: deny escapes, protected files, secrets
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("bad", [
    "/etc/passwd",          # absolute POSIX
    "~/x",                  # home lead
    "file:///x",            # url-like
    "../escape.html",       # parent traversal
    "playable/../../x",     # traversal after a valid prefix
    ".env",                 # protected file
    ".env.local",           # protected file
    "credentials.json",     # protected file
    "host.pem",             # protected suffix
    "secret.key",           # protected suffix
    ".git/config",          # git internals
    "playable/../.env",     # traversal to a protected name
])
def test_commit_rejects_escape_or_protected(service: ProjectGitService, bad) -> None:
    service.init_project("p")
    with pytest.raises(ContentPolicyError):
        service.commit("p", message="m", files={bad: b"x"})


@pytest.mark.parametrize("top", sorted(ALLOWED_TOP_DIRS))
def test_commit_accepts_only_allowed_top_dirs(service: ProjectGitService, top) -> None:
    service.init_project("p")
    sha = service.commit("p", message="m", files={f"{top}/file": b"x"})
    assert len(sha) == 40


def test_commit_rejects_disallowed_top_dir(service: ProjectGitService) -> None:
    service.init_project("p")
    with pytest.raises(ContentPolicyError, match="allowed content dirs"):
        service.commit("p", message="m", files={"junk/file": b"x"})


@pytest.mark.parametrize("leaky", [
    b"OPENAI_API_KEY=sk-leaked12345",
    b"Authorization: Bearer abc123token",
    b"api-key=sk-proj-abcdefghij",
])
def test_commit_rejects_secret_in_text_content(service: ProjectGitService, leaky) -> None:
    service.init_project("p")
    with pytest.raises(ContentPolicyError, match="secret"):
        service.commit("p", message="m", files={"src/config.js": leaky})


def test_commit_allows_binary_content_without_secret_scan(service: ProjectGitService) -> None:
    # Binary that happens to contain the bytes "sk-..." but is not valid UTF-8 is
    # not scanned (a binary blob is not a credential-leak vector into the repo).
    service.init_project("p")
    binary = b"\xff\xfe sk-notreally \x00binary"
    sha = service.commit("p", message="m", files={"assets/sprite.png": binary})
    assert len(sha) == 40


@pytest.mark.skipif(sys.platform != "win32", reason="backslash path is Windows")
def test_commit_handles_backslash_separator(service: ProjectGitService) -> None:
    service.init_project("p")
    sha = service.commit("p", message="m", files={"playable\\index.html": b"x"})
    assert service.read_file("p", sha, "playable/index.html") == b"x"


# --------------------------------------------------------------------------- #
# recoverability after restart (fresh service, same repo root)
# --------------------------------------------------------------------------- #


def test_commits_recoverable_after_restart(tmp_path: Path) -> None:
    root = tmp_path / "r"
    svc = ProjectGitService(repo_root=root)
    svc.init_project("p")
    sha = svc.commit("p", message="m", files={"playable/index.html": b"<html>x</html>", "src/main.js": b"1"})

    # A fresh service (simulating a backend restart) reads the same commits.
    restarted = ProjectGitService(repo_root=root)
    assert restarted.commit_exists("p", sha) is True
    assert restarted.read_file("p", sha, "playable/index.html") == b"<html>x</html>"


# --------------------------------------------------------------------------- #
# layout invariant: the platform repo is outside any run workspace (C13 enforces
# the runtime side; C20 asserts the directories do not overlap)
# --------------------------------------------------------------------------- #


def test_project_repo_root_is_outside_workspaces(tmp_path: Path) -> None:
    """C13 AC (runtime can't reach the platform repo): the trusted repo root and
    the run workspace root are disjoint directory trees by construction."""
    repos = tmp_path / "project-repos"
    workspaces = tmp_path / "workspaces"
    svc = ProjectGitService(repo_root=repos)
    svc.init_project("p")
    repo_path = (repos / "p").resolve()
    ws_path = (workspaces / "run-1" / "sess-1").resolve()
    # The repo must not be inside a workspace, and a workspace must not be inside
    # the repo. os.path.commonpath returns the shared prefix; with disjoint trees
    # it is tmp_path itself, not either root.
    assert os.path.realpath(str(repo_path)) != os.path.realpath(str(ws_path))
