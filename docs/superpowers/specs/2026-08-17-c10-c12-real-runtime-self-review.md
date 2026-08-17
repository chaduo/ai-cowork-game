# C10/C12 Real Runtime Self-Review

## Contract checks

- C10 upper layers still receive only `GameAgent`, `GameBuildResult` and
  `RunEvent`.
- C12 browser evidence is platform-owned; runtime output only supplies the
  hook response observed in a real browser.
- Fake providers are explicit test modes and are not selected by production
  `get_settings()`.
- Missing provider configuration fails closed and cannot create a successful
  Candidate.
- Artifact path is resolved against the persisted isolated Run workspace.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Chrome is unavailable in CI | Runner returns structured diagnostics; real smoke is skipped only when the executable is absent. |
| Generated games have no test hook | Platform records a failed hook and blocks `PASSED`; C10 prompt states the required contract. |
| CDP socket hangs | Every command and page wait has a bounded timeout; browser is terminated in `finally`. |
| Existing API tests depend on Fake | Fake mode remains available only when tests explicitly construct `Settings` without production providers. |
| OpenGame path differs by install | Support `OPENGAME_CLI_JS`, `realpath(opengame)`, and pinned vendor path. |

## Deliberate limitations

The hook is the game-specific test adapter. The platform does not guess
gameplay semantics from DOM text or provider logs. OpenGame must emit the hook
as part of the generated playable for a Candidate to pass C12.
