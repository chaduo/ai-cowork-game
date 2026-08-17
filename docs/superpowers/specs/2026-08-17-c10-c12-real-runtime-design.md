# C10/C12 Real Runtime Verification — Design Spec

Date: 2026-08-17
Status: Approved implementation direction
Scope: Backend runtime wiring and platform browser verification

## Goal

Make manual builds use the real OpenGame adapter and make Candidate testing use
a real local Chrome browser, while preserving provider-neutral C10/C12
contracts and keeping Fake implementations available only through explicit
test injection.

## Runtime selection

`Settings` gains explicit `game_agent_provider` and `candidate_test_provider`
values. `get_settings()` defaults to `opengame` and `chrome`; tests that call
`Settings(database_url=...)` retain an explicit fake test mode for isolation.
Production provider selection never silently falls back to Fake.

OpenGame runtime configuration reads the pinned CLI path, model, timeout and
OpenAI-compatible credentials from environment-backed settings. Missing
configuration returns a provider-neutral failed `GameBuildResult` with code
`opengame_not_configured`; it does not spawn a process or fabricate a
successful Candidate.

## C10 changes

- Resolve the real CLI path through `realpath(opengame)` and an explicit
  `OPENGAME_CLI_JS` override.
- Add a standard hook requirement to the provider prompt:
  `window.__GAME_TEST__ = { version: 1, ready: true, run(check) }`.
- Keep all provider-specific parsing inside `OpenGameAdapter`.
- Copy the artifact manifest SHA-256 into the Candidate through BuildService;
  no frontend metadata is accepted as provenance.

## C12 browser runner

`ChromeCandidateTestRunner` implements the existing `CandidateTestRunner`
protocol without a new runtime dependency. It launches the configured Chrome
binary with a temporary profile, connects to the Chrome DevTools Protocol using
Python stdlib sockets, and closes the browser in `finally`.

For the Candidate's isolated Run workspace it:

1. resolves and validates the HTML artifact stays inside the workspace;
2. waits for the page load event and captures console errors/exceptions;
3. verifies the hook shape and `version == 1` in the page context;
4. dispatches a real keyboard input and invokes `run("core_input")`;
5. invokes `run("gameplay")` and `run("completion")` and validates returned
   `{passed: true, observed?: string}` results.

The runner emits only `CandidateTestEvidence`; `CandidateTestService` remains
the sole owner of platform verdict calculation. Missing Chrome, invalid hook,
console errors, failed checks, timeout and artifact escape become evidence or
diagnostics and never become `PASSED`.

## Non-goals

No Playwright/Selenium dependency, no provider-specific types in the service,
no frontend changes, no automatic Human Gate transitions, and no trust in
runtime log keywords.
