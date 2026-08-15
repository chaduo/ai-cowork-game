"""C13 — WorkspaceManager path policy, lifecycle, and redaction unit tests.

These are the "audit tests" of task 4.2 plus the workspace-lifecycle and
cancel/retry-no-partial behavior of task 4.1. They run on Windows (the dev box)
so drive-letter and backslash cases are covered.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from app.agents.workspace import (
    WorkspaceEscapeError,
    WorkspaceManager,
    redact_stream,
)
from app.redaction import redact_text


# --------------------------------------------------------------------------- #
# path policy: deny workspace escape (game-agent-runtime spec scenario)
# --------------------------------------------------------------------------- #


@pytest.fixture
def ws(tmp_path: Path) -> tuple[WorkspaceManager, Path]:
    mgr = WorkspaceManager(root_base=tmp_path / "data" / "workspaces")
    root = mgr.prepare("run-1", "sess-1").root
    (root / "dist").mkdir()
    (root / "dist" / "index.html").write_text("<!doctype html><title>g</title>")
    return mgr, root


def test_validate_accepts_root_relative_member(ws) -> None:
    _, root = ws
    assert WorkspaceManager().validate_member(root, "index.html") == "index.html"


def test_validate_accepts_allowed_subdir_member(ws) -> None:
    _, root = ws
    assert WorkspaceManager().validate_member(root, "dist/index.html", ["dist"]) == "dist/index.html"


def test_validate_rejects_allowed_violation(ws) -> None:
    _, root = ws
    # "logs/index.html" is not in the allowed list ["dist"].
    with pytest.raises(WorkspaceEscapeError) as exc:
        WorkspaceManager().validate_member(root, "logs/index.html", ["dist"])
    assert exc.value.code == "not_allowed"


@pytest.mark.parametrize(
    "bad",
    [
        "/etc/passwd",            # absolute POSIX
        "~/secrets",              # home lead
        "file:///x",              # url-like
        "../escape.html",         # parent traversal
        "dist/../../escape.html", # traversal after a valid prefix
        "a/../..",                # traversal via collapse
        "\x00evil",               # nul byte
    ],
)
def test_validate_rejects_escape_shapes(ws, bad) -> None:
    _, root = ws
    with pytest.raises(WorkspaceEscapeError) as exc:
        WorkspaceManager().validate_member(root, bad)
    assert exc.value.code in {"absolute_path", "traversal", "invalid_path"}


@pytest.mark.skipif(sys.platform != "win32", reason="drive-letter absolute path is Windows")
def test_validate_rejects_windows_drive_absolute(ws) -> None:
    _, root = ws
    with pytest.raises(WorkspaceEscapeError) as exc:
        WorkspaceManager().validate_member(root, "C:/Windows/System32/drivers/etc/hosts")
    assert exc.value.code == "absolute_path"


@pytest.mark.skipif(sys.platform != "win32", reason="backslash path is Windows")
def test_validate_handles_backslash_separator(ws) -> None:
    _, root = ws
    assert WorkspaceManager().validate_member(root, "dist\\index.html", ["dist"]) == "dist/index.html"


def test_validate_rejects_protected_paths(ws) -> None:
    _, root = ws
    for protected in (".git/HEAD", ".env", ".env.local", "dist/.git/config"):
        with pytest.raises(WorkspaceEscapeError) as exc:
            WorkspaceManager().validate_member(root, protected)
        assert exc.value.code == "protected_path"


def _require_symlink_privilege(tmp_path: Path) -> Path:
    """Create a throwaway symlink to check the OS allows it; skip if not.

    Windows needs admin or Developer Mode to create symlinks (WinError 1314).
    The rejection logic is still exercised on POSIX; on a locked-down Windows
    box we skip the creation-based tests rather than report false failures.
    """
    probe = tmp_path / "_priv_probe_target"
    probe.write_text("x")
    try:
        link = tmp_path / "_priv_probe_link"
        os.symlink(probe, link)
    except OSError:
        pytest.skip("creating symlinks requires privilege on this OS (WinError 1314)")
    return probe


def test_validate_rejects_symlink_escape(ws, tmp_path: Path) -> None:
    outside = _require_symlink_privilege(tmp_path)
    _, root = ws
    outside.write_text("host secret")
    link = root / "dist" / "evil.html"
    os.symlink(outside, link)
    with pytest.raises(WorkspaceEscapeError) as exc:
        WorkspaceManager().validate_member(root, "dist/evil.html", ["dist"])
    assert exc.value.code == "symlink_escape"


def test_scan_preview_finds_root_entry(tmp_path: Path) -> None:
    mgr = WorkspaceManager(root_base=tmp_path / "ws")
    root = mgr.prepare("r", "s").root
    (root / "index.html").write_text("<html></html>")
    entries, preview = mgr.scan_preview(root, ["dist"])
    assert preview == "index.html"
    assert entries and entries[0].kind == "preview_entry"


def test_scan_preview_finds_subdir_entry(tmp_path: Path) -> None:
    mgr = WorkspaceManager(root_base=tmp_path / "ws")
    root = mgr.prepare("r", "s").root
    (root / "dist").mkdir()
    (root / "dist" / "index.html").write_text("<html></html>")
    entries, preview = mgr.scan_preview(root, ["dist"])
    assert preview == "dist/index.html"
    assert entries


def test_scan_preview_rejects_symlink_entry(tmp_path: Path) -> None:
    _require_symlink_privilege(tmp_path)
    mgr = WorkspaceManager(root_base=tmp_path / "ws")
    root = mgr.prepare("r", "s").root
    outside = tmp_path / "host.html"
    outside.write_text("host")
    # A symlinked index.html at root pointing outside must be rejected as an
    # escape (sanitized policy error), not silently treated as "no artifact".
    os.symlink(outside, root / "index.html")
    with pytest.raises(WorkspaceEscapeError) as exc:
        mgr.scan_preview(root, ["dist"])
    assert exc.value.code == "symlink_escape"


def test_scan_preview_empty_when_no_entry(tmp_path: Path) -> None:
    mgr = WorkspaceManager(root_base=tmp_path / "ws")
    root = mgr.prepare("r", "s").root
    entries, preview = mgr.scan_preview(root, ["dist"])
    assert entries == [] and preview is None


# --------------------------------------------------------------------------- #
# workspace lifecycle (run-observability spec: partial not reused on retry)
# --------------------------------------------------------------------------- #


def test_prepare_is_idempotent(tmp_path: Path) -> None:
    mgr = WorkspaceManager(root_base=tmp_path / "ws")
    p1 = mgr.prepare("r", "s")
    p2 = mgr.prepare("r", "s")
    assert p1.root == p2.root
    assert p1.root.is_dir()


def test_prepare_separates_sessions_under_one_run(tmp_path: Path) -> None:
    mgr = WorkspaceManager(root_base=tmp_path / "ws")
    p1 = mgr.prepare("r", "s1")
    p2 = mgr.prepare("r", "s2")
    assert p1.run_dir == p2.run_dir
    assert p1.root != p2.root
    assert p1.root.is_dir() and p2.root.is_dir()


def test_discard_removes_session_keeps_run_dir(tmp_path: Path) -> None:
    mgr = WorkspaceManager(root_base=tmp_path / "ws")
    p = mgr.prepare("r", "s")
    (p.root / "index.html").write_text("partial")
    mgr.discard(p)
    assert not p.root.exists()
    assert p.run_dir.is_dir()  # run dir retained for siblings/retry


def test_discard_run_removes_everything(tmp_path: Path) -> None:
    mgr = WorkspaceManager(root_base=tmp_path / "ws")
    p = mgr.prepare("r", "s")
    mgr.discard_run("r")
    assert not p.run_dir.exists()


def test_retry_gets_fresh_workspace_not_prior_partial(tmp_path: Path) -> None:
    """run-observability: retry must not reuse an untrusted partial workspace."""
    mgr = WorkspaceManager(root_base=tmp_path / "ws")
    first = mgr.prepare("r1", "s1")
    (first.root / "partial.html").write_text("partial from cancelled run")
    mgr.discard(first)  # cancel discards the partial session
    # Retry = new run_id + new session_id -> brand new, empty workspace.
    retry = mgr.prepare("r2", "s1")
    assert retry.root != first.root
    assert not (retry.root / "partial.html").exists()
    assert retry.root.is_dir()


# --------------------------------------------------------------------------- #
# secret redaction on raw buffers (design.md: scan output for secrets)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "raw,marker",
    [
        ("got Bearer abc123 here", "abc123"),
        ("api-key=sk-live-12345 done", "sk-live-12345"),
        ("token=secrettoken x", "secrettoken"),
        ("using sk-proj-abcdefghij", "sk-proj-abcdefghij"),
    ],
)
def test_redact_strips_secret_not_marker(raw, marker) -> None:
    redacted = redact_text(raw)
    assert marker not in redacted
    assert "[REDACTED]" in redacted


def test_redact_stream_matches_redact_text() -> None:
    raw = "OPENAI_API_KEY=sk-test123 in stdout"
    assert redact_stream(raw) == redact_text(raw)
    assert "sk-test123" not in redact_stream(raw)


def test_redact_stream_does_not_truncate_large_buffer() -> None:
    # A provider buffer can be large; redaction must not cap it (the stream-json
    # parser needs the full stream, including the terminal result event).
    big = "x" * 10000 + " sk-leak123 " + "y" * 10000
    redacted = redact_stream(big)
    assert len(redacted) == len(big)  # no truncation
    assert "sk-leak123" not in redacted


# Adapter-level escape → invalid_output and raw-stream redaction tests live in
# test_c13_adapter_workspace.py (they depend on the adapter's hardened _build_result).
