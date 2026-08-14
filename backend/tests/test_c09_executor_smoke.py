"""C09 — real OpenGame smoke (catalog AC: "use the C08-pinned command for a real
Executor smoke, without touching the Project repository").

Two layers:
1. No-credential smoke (default): run ``opengame --help`` through the executor and
   assert spawn / cwd / env / exit_code / stdout are real. Skipped if opengame is
   not installed.
2. Full-generation smoke (opt-in via credentials): run a real ``opengame -p ... -o
   stream-json`` generation. Credentials are read from ``backend/tests/.env.local``
   (gitignored) or env vars — NEVER hardcoded, NEVER committed. Skipped if missing.

The executor is invoked with ``node`` on opengame's ``dist/cli.js`` directly to
avoid the Windows ``.cmd`` shim (``create_subprocess_exec`` does not use PATHEXT,
and ``shell=True`` is forbidden by the contract).
"""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

import pytest

from app.agents.subprocess_executor import AsyncSubprocessExecutor


def _node() -> str:
    node = shutil.which("node")
    return node or ""


def _opengame_cli_js() -> str | None:
    """Find opengame's dist/cli.js. Prefer the globally npm-link'd install."""
    candidates = [
        # global npm link target on this machine
        r"D:\Program Files (x86)\nodejs\node_global\node_modules\@opengame\opengame\dist\cli.js",
    ]
    # Also try to resolve from the opengame on PATH -> its package dir.
    og = shutil.which("opengame")
    if og:
        # opengame is a .cmd shim; its package lives in node_modules/@opengame/opengame
        shim_dir = os.path.dirname(os.path.realpath(og))
        candidates.append(
            os.path.join(shim_dir, "node_modules", "@opengame", "opengame", "dist", "cli.js")
        )
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


def run_async(coro):
    return asyncio.run(coro)


has_node = bool(_node())
has_opengame = bool(_opengame_cli_js())

# Credentials for the full-generation smoke: from backend/tests/.env.local or env.
_ENV_LOCAL = Path(__file__).parent / ".env.local"


def _load_creds() -> dict[str, str]:
    creds: dict[str, str] = {}
    if _ENV_LOCAL.is_file():
        for line in _ENV_LOCAL.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip()
    # env vars take precedence
    for k in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"):
        if os.environ.get(k):
            creds[k] = os.environ[k]
    return creds


creds = _load_creds()
has_creds = bool(creds.get("OPENAI_API_KEY") and creds.get("OPENAI_BASE_URL"))


@pytest.mark.skipif(not (has_node and has_opengame), reason="node/opengame not installed")
def test_opengame_help_runs_through_executor(workspace) -> None:
    """No-credential smoke: opengame --help via the executor returns real output + exit 0."""
    executor = AsyncSubprocessExecutor()
    result = run_async(
        executor.run(
            command=_node(),
            arguments=[_opengame_cli_js(), "--help"],
            cwd=str(workspace),
            approved_env={},
            timeout=30,
        )
    )
    assert result.process_status == "completed"
    assert result.exit_code == 0
    assert "opengame" in result.stdout.lower()


@pytest.mark.skipif(
    not (has_node and has_opengame and has_creds),
    reason="node/opengame not installed or OPENAI_API_KEY/OPENAI_BASE_URL not in backend/tests/.env.local or env",
)
def test_opengame_real_generation_smoke(workspace) -> None:
    """Full-generation smoke: a real opengame run produces a completed result with
    system + result stream-json events (matches the C08 success fixture shape).
    """
    executor = AsyncSubprocessExecutor()
    approved_env = {
        "OPENAI_API_KEY": creds["OPENAI_API_KEY"],
        "OPENAI_BASE_URL": creds["OPENAI_BASE_URL"],
        "GEMINI_SANDBOX": "false",
    }
    if "OPENAI_MODEL" in creds:
        approved_env["OPENAI_MODEL"] = creds["OPENAI_MODEL"]
    result = run_async(
        executor.run(
            command=_node(),
            arguments=[
                _opengame_cli_js(),
                "-p", "Build a Pong clone with paddle controls and a dark theme.",
                "--yolo", "--auth-type", "openai",
                "-m", creds.get("OPENAI_MODEL", "kimi-k3"),
                "-o", "stream-json",
            ],
            cwd=str(workspace),
            approved_env=approved_env,
            timeout=300,
        )
    )
    assert result.process_status == "completed"
    assert result.exit_code == 0
    # C08 success fixture: stream-json contains system + result events.
    assert '"type":"system"' in result.stdout
    assert '"type":"result"' in result.stdout
