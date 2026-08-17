"""Real-browser CandidateTestRunner (rebaseline Aug-15 zhang item 3).

Drives a real headless Chromium (Playwright) against a BuildCandidate's
``index.html`` artifact and collects the platform-mandated
``REQUIRED_EVIDENCE`` — ``browser_started`` / ``console`` / ``core_input`` /
``gameplay`` / ``completion`` / ``phaser_hook`` — as raw ``CandidateTestEvidence``
for ``CandidateTestService`` to turn into a platform TestReport. It never assigns
a platform verdict; the platform re-derives PASSED/PARTIAL_FAILURE/CRITICAL_FAILURE
from the evidence (C12 contract).

``window.__GAME_TEST__`` (Product Spec §22; design.md:57 "the Phaser template
exposes a read-only test bridge") is the only acceptable gameplay proof — the
runner does NOT screenshot-guess. An instrumented game with a valid hook yields
``passed`` gameplay evidence and a ``PASSED`` report; a real OpenGame game that
lacks the hook yields ``phaser_hook`` failed + core_gameplay ``missing`` and the
platform returns ``CRITICAL_FAILURE`` (spec-correct: no hook = no gameplay proof).

Playwright is imported lazily so importing this module (and the offline test
suite) does not require the browser; only ``run()`` needs it.

Sanitization: every ``observed`` string is scrubbed with ``app.redaction.redact_text``
so a key leaked into a console error never lands in evidence.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from app.agents.candidate_test_runner import EVIDENCE_GROUPS, REQUIRED_EVIDENCE
from app.contracts.game_agent import Diagnostic
from app.contracts.test_report import CandidateTestEvidence, RuntimeTestResult
from app.models import BuildCandidate
from app.redaction import redact_text

PHASER_TEST_HOOK = "window.__GAME_TEST__"

# A small init script that runs before the page's own scripts so the runner can
# observe ``window.__GAME_TEST__`` the moment the game sets it (read-only — it
# never creates the hook; a real instrumented game provides it). It stashes the
# hook and a log of console messages for the runner to read back.
_INIT_SCRIPT = """
window.__CANDIDATE_PROBE__ = { hook: null, consoleErrors: [] };
try {
  Object.defineProperty(window, '__GAME_TEST__', {
    configurable: true,
    get() { return window.__CANDIDATE_PROBE__.hook; },
    set(v) {
      window.__CANDIDATE_PROBE__.hook = v;
      if (v && typeof v.onReady === 'function') { try { v.onReady(); } catch (e) {} }
    },
  });
} catch (e) {}
"""

# Probe the hook surface the runner reads back. Returns a dict the runner maps to
# evidence; never throws (the runner treats a thrown probe as "hook invalid").
_PROBE_JS = """
() => {
  const p = window.__CANDIDATE_PROBE__ || { hook: null, consoleErrors: [] };
  const h = p.hook;
  if (!h || typeof h !== 'object') {
    return { present: false, consoleErrors: (p.consoleErrors || []).slice(0, 5) };
  }
  const has = (k) => typeof h[k] === 'function' || h[k] !== undefined;
  return {
    present: true,
    hasState: has('state'),
    hasTrigger: has('trigger'),
    hasIsComplete: has('isComplete'),
    state: (typeof h.state === 'function') ? (h.state() ?? null) : (h.state ?? null),
    consoleErrors: (p.consoleErrors || []).slice(0, 5),
  };
}
"""


class BrowserCandidateTestRunner:
    """Real-browser CandidateTestRunner backed by Playwright headless Chromium.

    ``artifact_root`` resolves the candidate's relative ``artifact_path`` to an
    absolute ``file://`` URL. Tests inject ``browser_launch`` (a callable returning
    an awaitable context manager, like Playwright's ``async_playwright``) so the
    runner can be exercised without the real browser; production leaves it None and
    Playwright is imported lazily on first ``run()``.
    """

    def __init__(
        self,
        *,
        artifact_root: Path | str | None = None,
        browser_launch: Callable[[], Awaitable] | None = None,
        headless: bool = True,
    ) -> None:
        self._artifact_root = Path(artifact_root) if artifact_root else None
        self._browser_launch = browser_launch
        self._headless = headless

    async def run(self, candidate: BuildCandidate) -> RuntimeTestResult:
        index_url = self._resolve_url(candidate)
        evidence: list[CandidateTestEvidence] = []
        diagnostics: list[Diagnostic] = []
        artifact_ref = candidate.artifact_path or "index.html"

        async with self._launch() as (browser, page):
            await page.add_init_script(_INIT_SCRIPT)
            console_errors: list[str] = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            load_error: str | None = None
            try:
                await page.goto(index_url, wait_until="load", timeout=15_000)
            except Exception as exc:  # noqa: BLE001 — surfaced as browser_started failure
                load_error = str(exc)

            # browser_started
            evidence.append(self._evidence(
                candidate, "browser_started",
                "passed" if load_error is None else "failed",
                "page loads without a navigation error",
                "page loaded" if load_error is None else f"load failed: {self._sanitize(load_error)}",
                artifact_ref,
            ))

            # console
            if console_errors:
                evidence.append(self._evidence(
                    candidate, "console", "failed",
                    "no error-level console messages during load",
                    f"console error: {self._sanitize(console_errors[0])}",
                    artifact_ref,
                ))
                diagnostics.append(Diagnostic(level="error", code="console_error", message="Console reported an error"))
            else:
                evidence.append(self._evidence(
                    candidate, "console", "passed",
                    "no error-level console messages during load",
                    "no console errors", artifact_ref,
                ))

            # phaser_hook + core_gameplay
            probe = await self._safe_probe(page)
            hook_present = bool(probe.get("present"))
            hook_valid = hook_present and probe.get("hasState") and probe.get("hasTrigger") and probe.get("hasIsComplete")

            evidence.append(self._evidence(
                candidate, "phaser_hook",
                "passed" if hook_valid else "failed",
                f"{PHASER_TEST_HOOK} present with state/trigger/isComplete",
                f"hook valid (state/trigger/isComplete)" if hook_valid
                else ("hook present but incomplete" if hook_present else f"{PHASER_TEST_HOOK} unavailable"),
                artifact_ref,
                details={"test_hook": PHASER_TEST_HOOK, "hook_validated": bool(hook_valid)} if hook_valid else {},
            ))

            if hook_valid:
                # Drive the hook: trigger a test action, then read state + completion.
                drove = await self._drive_hook(page)
                evidence.append(self._evidence(
                    candidate, "core_input", "passed" if drove["triggered"] else "failed",
                    "hook.trigger() applies a test action",
                    drove["triggered_obs"], artifact_ref,
                ))
                evidence.append(self._evidence(
                    candidate, "gameplay", "passed" if drove["state_changed"] else "failed",
                    "hook.state() reflects the triggered action",
                    drove["state_obs"], artifact_ref,
                ))
                evidence.append(self._evidence(
                    candidate, "completion", "passed" if drove["complete"] else "failed",
                    "hook.isComplete() reports the completion condition",
                    drove["complete_obs"], artifact_ref,
                ))
            else:
                # No valid hook → core_gameplay is missing, not guessed. The
                # platform verdict then returns CRITICAL_FAILURE (spec-correct).
                for kind in ("core_input", "gameplay", "completion"):
                    evidence.append(self._evidence(
                        candidate, kind, "missing",
                        f"{kind} observed via {PHASER_TEST_HOOK}",
                        f"{PHASER_TEST_HOOK} unavailable — {kind} cannot be verified",
                        artifact_ref,
                    ))

        verdict = "pass" if all(item.status == "passed" for item in evidence) else "fail"
        return RuntimeTestResult(verdict=verdict, evidence=evidence, diagnostics=diagnostics)

    # -- internals --------------------------------------------------------- #

    def _resolve_url(self, candidate: BuildCandidate) -> str:
        rel = candidate.artifact_path or "index.html"
        if self._artifact_root is None:
            # A bare relative path — treat it as already resolvable (caller set up
            # the cwd). Most callers pass artifact_root.
            path = Path(rel)
        else:
            path = self._artifact_root / rel
        return path.resolve().as_uri()

    async def _safe_probe(self, page) -> dict:
        try:
            result = await page.evaluate(_PROBE_JS)
            return result if isinstance(result, dict) else {}
        except Exception:  # noqa: BLE001
            return {}

    async def _drive_hook(self, page) -> dict:
        """Trigger the hook's test action and read state + completion back."""
        js = """
        () => {
          const h = window.__CANDIDATE_PROBE__ && window.__CANDIDATE_PROBE__.hook;
          if (!h) { return { triggered: false, triggeredObs: 'hook missing', stateObs: '', complete: false, completeObs: '' }; }
          let before = '';
          try { before = JSON.stringify(typeof h.state === 'function' ? h.state() : h.state); } catch (e) { before = String(e); }
          try { if (typeof h.trigger === 'function') { h.trigger(); } } catch (e) { return { triggered: false, triggeredObs: 'trigger threw: ' + e, stateObs: before, complete: false, completeObs: '' }; }
          let after = '';
          try { after = JSON.stringify(typeof h.state === 'function' ? h.state() : h.state); } catch (e) { after = String(e); }
          let complete = false; let completeObs = '';
          try { complete = typeof h.isComplete === 'function' ? !!h.isComplete() : !!h.isComplete; completeObs = String(complete); } catch (e) { completeObs = 'isComplete threw: ' + e; }
          return { triggered: true, triggeredObs: 'trigger applied', stateObs: before + ' -> ' + after, complete, completeObs };
        }
        """
        try:
            result = await page.evaluate(js)
            if not isinstance(result, dict):
                result = {}
        except Exception as exc:  # noqa: BLE001
            result = {"triggered": False, "triggeredObs": f"evaluate threw: {exc}", "stateObs": "", "complete": False, "completeObs": ""}
        return {
            "triggered": bool(result.get("triggered")),
            "triggered_obs": self._sanitize(str(result.get("triggeredObs", ""))),
            "state_changed": bool(result.get("triggered")) and str(result.get("stateObs", "")) != "",
            "state_obs": self._sanitize(str(result.get("stateObs", ""))),
            "complete": bool(result.get("complete")),
            "complete_obs": self._sanitize(str(result.get("completeObs", ""))),
        }

    @staticmethod
    def _evidence(
        candidate: BuildCandidate,
        kind: str,
        status: str,
        expected: str,
        observed: str,
        artifact_ref: str,
        *,
        details: dict | None = None,
    ) -> CandidateTestEvidence:
        group = EVIDENCE_GROUPS.get(kind, "core_gameplay")
        detail: dict = {"check_group": group}
        if kind == "phaser_hook" and details:
            detail.update(details)
        return CandidateTestEvidence(
            kind=kind,
            status=status,  # type: ignore[arg-type]
            source="platform",  # the browser runner is platform-owned, not the runtime provider
            severity="critical",
            expected=expected,
            observed=BrowserCandidateTestRunner._sanitize(observed),
            artifact_ref=artifact_ref,
            details=detail,
        )

    @staticmethod
    def _sanitize(text: str) -> str:
        # Never persist a leaked credential that surfaced in a console error /
        # hook observation. Keep the 4000-char evidence cap (the contract field).
        return redact_text(text, max_length=4000)

    @asynccontextmanager
    async def _launch(self) -> AsyncIterator[tuple[object, object]]:
        """Yield ``(browser, page)`` from a Playwright session.

        ``browser_launch`` (injected) is a zero-arg callable returning an async
        context manager (Playwright's ``async_playwright()``). Lazy-imported when
        None so module import needs no browser.
        """
        if self._browser_launch is not None:
            pw = await self._browser_launch()
        else:
            from playwright.async_api import async_playwright
            pw = await async_playwright().start()

        try:
            browser = await pw.chromium.launch(headless=self._headless)
        except Exception:
            await pw.stop()
            raise
        try:
            page = await browser.new_page()
            yield browser, page
        finally:
            await browser.close()
            await pw.stop()
