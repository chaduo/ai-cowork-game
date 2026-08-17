"""Real Chrome-based Candidate verification without a browser dependency.

The runner speaks the small subset of Chrome DevTools Protocol needed by C12
over a standard-library WebSocket client. It deliberately returns runtime
evidence only; CandidateTestService remains the platform verdict authority.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.candidate_test_runner import EVIDENCE_GROUPS, REQUIRED_EVIDENCE, CandidateTestRunner
from app.contracts.game_agent import Diagnostic
from app.contracts.test_report import CandidateTestEvidence, RuntimeTestResult
from app.models import BuildCandidate, Run


def _hook_result(value: object) -> tuple[bool, str]:
    if not isinstance(value, dict):
        return False, "test hook did not return a result"
    if value.get("passed") is not True:
        return False, str(value.get("observed") or "test hook reported failure")
    return True, str(value.get("observed") or "test hook passed")


class ChromeCandidateTestRunner(CandidateTestRunner):
    def __init__(
        self,
        session: Session,
        *,
        executable: str | None = None,
        timeout_seconds: float = 30,
    ) -> None:
        self.session = session
        self.executable = executable or self.find_browser()
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def find_browser() -> str | None:
        candidates = [
            os.getenv("CHROME_EXECUTABLE"),
            shutil.which("google-chrome"),
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
        ]
        return next((path for path in candidates if path and Path(path).is_file()), None)

    async def run(self, candidate: BuildCandidate) -> RuntimeTestResult:
        run = self.session.scalar(select(Run).where(Run.build_id == candidate.build_id).order_by(Run.created_at.desc()))
        artifact_ref = candidate.artifact_path or ""
        if run is None or not run.workspace_path:
            return self._unavailable_result(candidate, "candidate run has no isolated workspace", "workspace_missing")
        root = Path(run.workspace_path).resolve()
        artifact = self._resolve_artifact(root, artifact_ref)
        if artifact is None:
            return self._unavailable_result(candidate, "candidate artifact is outside its run workspace", "artifact_escape")
        if not self.executable:
            return self._unavailable_result(candidate, "Chrome/Chromium executable is not configured", "chrome_not_found")
        return await asyncio.to_thread(self._run_browser, artifact, artifact_ref)

    @staticmethod
    def _resolve_artifact(root: Path, artifact_ref: str) -> Path | None:
        if not artifact_ref or artifact_ref.startswith(("/", "~")) or "://" in artifact_ref:
            return None
        relative = PurePosixPath(artifact_ref)
        if ".." in relative.parts or relative.suffix.lower() != ".html":
            return None
        candidate = (root / Path(*relative.parts)).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return None
        return candidate if candidate.is_file() else None

    def _run_browser(self, artifact: Path, artifact_ref: str) -> RuntimeTestResult:
        browser: _ChromeProcess | None = None
        evidence: list[CandidateTestEvidence] = []
        diagnostics: list[Diagnostic] = []
        try:
            browser = _ChromeProcess(self.executable or "", artifact.as_uri(), self.timeout_seconds)
            client = browser.connect()
            client.call("Page.enable")
            client.call("Runtime.enable")
            client.call("Log.enable")
            client.call("Page.navigate", {"url": artifact.as_uri()})
            loaded = client.wait_for_event("Page.loadEventFired", self.timeout_seconds)
            evidence.append(self._evidence(
                "browser_started",
                "passed" if loaded else "failed",
                "HTML artifact loads in a real browser",
                "Page.loadEventFired received" if loaded else "Page load timed out",
                artifact_ref,
            ))

            console_errors = client.console_errors()
            evidence.append(self._evidence(
                "console",
                "failed" if console_errors else "passed",
                "No browser console errors or uncaught exceptions",
                "; ".join(console_errors[:4]) if console_errors else "No console errors observed",
                artifact_ref,
            ))

            hook = client.evaluate_json(
                "JSON.stringify((() => { const h = window.__GAME_TEST__; return "
                "{exists: !!h, version: h && h.version, ready: h && h.ready === true, "
                "hasRun: !!(h && typeof h.run === 'function')}; })())"
            )
            hook_valid = isinstance(hook, dict) and hook.get("exists") and hook.get("version") == 1 and hook.get("ready") and hook.get("hasRun")
            evidence.append(self._evidence(
                "phaser_hook",
                "passed" if hook_valid else "failed",
                "window.__GAME_TEST__ version 1 is ready and callable",
                json.dumps(hook, ensure_ascii=False) if hook is not None else "test hook is unavailable",
                artifact_ref,
                details={"test_hook": "window.__GAME_TEST__", "hook_validated": bool(hook_valid)},
            ))

            client.dispatch_key("ArrowRight")
            for check in ("core_input", "gameplay", "completion"):
                raw = client.evaluate_json(
                    "(async () => { const h = window.__GAME_TEST__; "
                    f"if (!h || typeof h.run !== 'function') return {{passed:false, observed:'missing test hook'}}; "
                    f"return JSON.stringify(await h.run({json.dumps(check)})); }})()"
                )
                passed, observed = _hook_result(raw)
                evidence.append(self._evidence(
                    check,
                    "passed" if passed else "failed",
                    f"Game test hook {check} passes against the running game",
                    observed,
                    artifact_ref,
                    details={"check_group": EVIDENCE_GROUPS[check]},
                ))
        except Exception as exc:
            diagnostics.append(Diagnostic(level="error", code="browser_verification_failed", message=str(exc)))
            existing = {item.kind for item in evidence}
            for kind in REQUIRED_EVIDENCE:
                if kind not in existing:
                    evidence.append(self._evidence(
                        kind,
                        "missing",
                        f"Platform browser check {kind} completes",
                        "Browser verification did not produce evidence",
                        artifact_ref,
                        details={"check_group": EVIDENCE_GROUPS[kind]},
                    ))
        finally:
            if browser is not None:
                browser.close()
        return RuntimeTestResult(
            verdict="pass" if evidence and all(item.status == "passed" for item in evidence) else "fail",
            evidence=evidence,
            diagnostics=diagnostics,
        )

    @staticmethod
    def _evidence(kind: str, status: str, expected: str, observed: str, artifact_ref: str, *, details: dict | None = None) -> CandidateTestEvidence:
        return CandidateTestEvidence(
            kind=kind,
            status=status,
            source="platform",
            severity="critical",
            expected=expected,
            observed=observed,
            artifact_ref=artifact_ref,
            details=details or {"check_group": EVIDENCE_GROUPS[kind]},
        )

    def _unavailable_result(self, candidate: BuildCandidate, message: str, code: str) -> RuntimeTestResult:
        artifact_ref = candidate.artifact_path or "dist/index.html"
        return RuntimeTestResult(
            verdict="fail",
            diagnostics=[Diagnostic(level="error", code=code, message=message)],
            evidence=[self._evidence(
                kind,
                "failed" if kind == "browser_started" else "missing",
                f"Platform browser check {kind} completes",
                message,
                artifact_ref,
            ) for kind in REQUIRED_EVIDENCE],
        )


class _ChromeProcess:
    def __init__(self, executable: str, url: str, timeout: float) -> None:
        self.executable = executable
        self.url = url
        self.timeout = timeout
        self.profile = Path(tempfile.mkdtemp(prefix="ai-cowork-chrome-"))
        self.port = self._free_port()
        self.process: subprocess.Popen | None = None

    @staticmethod
    def _free_port() -> int:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def connect(self) -> "_CdpClient":
        self.process = subprocess.Popen(
            [
                self.executable,
                "--headless=new",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--remote-allow-origins=*",
                f"--remote-debugging-port={self.port}",
                f"--user-data-dir={self.profile}",
                self.url,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/list", timeout=0.5) as response:
                    targets = json.loads(response.read().decode("utf-8"))
                target = next((item for item in targets if item.get("webSocketDebuggerUrl")), None)
                if target:
                    return _CdpClient(target["webSocketDebuggerUrl"], self.timeout)
            except (OSError, ValueError):
                time.sleep(0.05)
        raise TimeoutError("Chrome DevTools target did not start")

    def close(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        try:
            self.profile.rmdir()
        except OSError:
            shutil.rmtree(self.profile, ignore_errors=True)


class _CdpClient:
    def __init__(self, url: str, timeout: float) -> None:
        parsed = urllib.parse.urlparse(url)
        self.host = parsed.hostname or "127.0.0.1"
        self.port = parsed.port or 9222
        self.path = parsed.path or "/"
        self.timeout = timeout
        self.sock: socket.socket | None = None
        self.next_id = 1
        self.events: list[dict] = []

    def _connect(self) -> None:
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {self.path} HTTP/1.1\r\nHost: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        ).encode("ascii")
        self.sock.sendall(request)
        response = self._read_until(b"\r\n\r\n")
        if b" 101 " not in response:
            raise ConnectionError("Chrome DevTools WebSocket handshake failed")

    def _read_until(self, marker: bytes) -> bytes:
        assert self.sock is not None
        data = b""
        while marker not in data:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("Chrome DevTools socket closed")
            data += chunk
        return data

    def _send(self, payload: str) -> None:
        assert self.sock is not None
        body = payload.encode("utf-8")
        mask = os.urandom(4)
        size = len(body)
        if size < 126:
            header = bytes([0x81, 0x80 | size])
        elif size < 65536:
            header = bytes([0x81, 0x80 | 126]) + struct.pack(">H", size)
        else:
            header = bytes([0x81, 0x80 | 127]) + struct.pack(">Q", size)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(body))
        self.sock.sendall(header + mask + masked)

    def _recv(self) -> tuple[int, bytes]:
        assert self.sock is not None
        first_two = self._recv_exact(2)
        opcode = first_two[0] & 0x0F
        masked = bool(first_two[1] & 0x80)
        size = first_two[1] & 0x7F
        if size == 126:
            size = struct.unpack(">H", self._recv_exact(2))[0]
        elif size == 127:
            size = struct.unpack(">Q", self._recv_exact(8))[0]
        mask = self._recv_exact(4) if masked else b""
        body = self._recv_exact(size)
        if masked:
            body = bytes(value ^ mask[index % 4] for index, value in enumerate(body))
        return opcode, body

    def _recv_exact(self, size: int) -> bytes:
        assert self.sock is not None
        data = b""
        while len(data) < size:
            chunk = self.sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Chrome DevTools socket closed")
            data += chunk
        return data

    def _message(self) -> dict:
        opcode, body = self._recv()
        if opcode == 0x9:
            self._send_pong(body)
            return self._message()
        if opcode == 0x8:
            raise ConnectionError("Chrome DevTools socket closed")
        return json.loads(body.decode("utf-8"))

    def _send_pong(self, body: bytes) -> None:
        assert self.sock is not None
        mask = os.urandom(4)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(body))
        self.sock.sendall(bytes([0x8A, 0x80 | len(body)]) + mask + masked)

    def call(self, method: str, params: dict | None = None) -> dict:
        if self.sock is None:
            self._connect()
        command_id = self.next_id
        self.next_id += 1
        self._send(json.dumps({"id": command_id, "method": method, "params": params or {}}))
        while True:
            message = self._message()
            if message.get("id") == command_id:
                if "error" in message:
                    raise RuntimeError(str(message["error"]))
                return message.get("result", {})
            self.events.append(message)

    def wait_for_event(self, method: str, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for index, message in enumerate(self.events):
                if message.get("method") == method:
                    self.events.pop(index)
                    assert self.sock is not None
                    self.sock.settimeout(self.timeout)
                    return True
            remaining = max(0.05, deadline - time.monotonic())
            assert self.sock is not None
            self.sock.settimeout(remaining)
            try:
                self.events.append(self._message())
            except socket.timeout:
                break
        assert self.sock is not None
        self.sock.settimeout(self.timeout)
        return False

    def evaluate_json(self, expression: str) -> object | None:
        result = self.call("Runtime.evaluate", {
            "expression": expression,
            "awaitPromise": True,
            "returnByValue": True,
        })
        remote = result.get("result", {})
        if remote.get("subtype") == "error" or "exceptionDetails" in result:
            return None
        value = remote.get("value")
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def dispatch_key(self, key: str) -> None:
        self.call("Input.dispatchKeyEvent", {"type": "keyDown", "key": key})
        self.call("Input.dispatchKeyEvent", {"type": "keyUp", "key": key})

    def console_errors(self) -> list[str]:
        errors: list[str] = []
        for message in self.events:
            method = message.get("method")
            params = message.get("params", {})
            if method == "Runtime.exceptionThrown":
                errors.append(params.get("exceptionDetails", {}).get("text", "uncaught exception"))
            elif method == "Runtime.consoleAPICalled" and params.get("type") in {"error", "assert"}:
                errors.append("console." + str(params.get("type")))
            elif method == "Log.entryAdded" and params.get("entry", {}).get("level") == "error":
                errors.append(params.get("entry", {}).get("text", "browser log error"))
        return errors

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None
