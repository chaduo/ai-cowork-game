# C08 OpenGame CLI Spike

> Owner: zhang · Change: C08 `opengame-cli-spike` · Updated: 2026-08-15

This report records what V1 can safely rely on from the real OpenGame CLI. It
separates provider observations from platform guarantees. A provider message or
zero exit code never promotes a candidate, publishes a release, or saves a
resource.

## Pinned Runtime

| Item | Value |
|---|---|
| Canonical source | `vendor/opengame` git submodule |
| Upstream | `leigest519/OpenGame` via the `CodingZY/OpenGame` fork |
| Commit | `c54307efe1dab927e7fc52dbb92af6b3df1d1c66` |
| CLI entry | `vendor/opengame/dist/cli.js` |
| Observed version | `0.6.0` |
| Runtime | Node.js 20 or newer |

Prepare a clean checkout with:

```bash
git submodule update --init vendor/opengame
(cd vendor/opengame && npm ci && npm run build)
node vendor/opengame/dist/cli.js --help
```

The adapter invokes the JavaScript entry directly. It does not depend on a
machine-global `opengame`, an npm link, a shell shim, or a developer-specific
checkout. The pinned source commit does not contain `dist/cli.js`; the explicit
install and build step above is required once per clean checkout.

## Provider Contract Observed

The non-interactive create invocation is:

```bash
node vendor/opengame/dist/cli.js \
  -p "<RuntimeBuildSpec prompt>" \
  --yolo \
  --auth-type openai \
  -m "$OPENAI_MODEL" \
  -o stream-json
```

The process cwd is the isolated run workspace. Credentials and provider URL are
inherited through the executor's approved environment allowlist; they are not
embedded in arguments or evidence. Output is NDJSON containing `system`,
`assistant`, and usually a terminal `result` event.

## Capability Conclusions

| Operation | Conclusion | Evidence boundary |
|---|---|---|
| create | **Supported and observed.** A real run produced an `index.html` game artifact. | Sanitized `success-run.stream.json`; raw evidence remains local. |
| modify | **Unsupported for V1 until a baseline-playable modify run is captured.** Resume flags exist, but flag presence is not proof of the required modify semantics. | No accepted real modify evidence yet. |
| cancel | **Supported by the platform executor.** An interrupted provider stream may end without `result`. | `cancel-run.stream.json` plus C09 process-tree tests. |
| timeout | **Supported by the platform executor.** Timeout can leave partial files and no `result`; those files are never a valid candidate. | `timeout-run.stream.json` plus C09 process-tree tests. |
| invalid output | **Observed.** OpenGame can report success while producing no valid preview entry. | `invalid-output-run.stream.json`; artifact validation remains mandatory. |
| unsupported operation | **Standardized.** Operations outside create, and modify until proven, must return the provider-neutral `unsupported` result rather than guessing provider behavior. | C06 contract suite. |

These conclusions deliberately do not mark modify as done. C10 must reject or
standardize unsupported operations until new real evidence changes this matrix.

## Failure Semantics

OpenGame 0.6.0 can emit an API error inside a `result` whose `is_error` is false
and whose process exit code is zero. It can also finish without creating
`index.html`. Therefore C09/C10 must combine:

- executor status and exit code;
- terminal event presence;
- sanitized diagnostics;
- the artifact manifest and preview-entry validation.

Cancel and timeout look alike in provider output: both may be truncated streams
without a terminal event. Their status comes from the executor trigger, never
from invented provider meaning. Killing and reaping the process tree is verified
by C09 automated tests on supported platforms.

## Evidence Policy

`capture-fixture.sh` runs against the pinned submodule and writes raw captures to
the ignored `raw/` directory. Raw output can contain local paths, provider text,
session identifiers, and other sensitive metadata, so it must not be committed.

The committed `*-run.stream.json` files are minimized, sanitized derivatives
that preserve only contract-relevant event shapes. They intentionally omit
session IDs, UUIDs, local paths, private reasoning blocks, and credentials.

Run a local capture only after exporting credentials:

```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://provider.example/v1"
export OPENAI_MODEL="kimi-k3"
docs/development/c08-opengame-spike/capture-fixture.sh success
```

The portable capture helper records evidence; it is not the production process
supervisor. C09's `AsyncSubprocessExecutor` owns timeout, cancellation, process
tree termination, bounded diagnostics, and incremental output delivery.

## C09/C10 Handoff

- C09 resolves `vendor/opengame/dist/cli.js` first and uses an explicit override
  only for diagnostics or controlled tests.
- C09 starts the process without a shell and streams complete stdout/stderr lines.
- C10 maps OpenGame events into the provider-neutral C06 contract.
- Build success creates only a `BuildCandidate`; Human Promote and Publish remain
  platform actions outside the provider.
- A credentialed create smoke is optional in CI and must report a skip honestly
  when credentials are absent.
