# C08 Sanitized Fixture Notes

The committed stream fixtures are reviewable contract samples derived from real
OpenGame 0.6.0 observations. They are deliberately not byte-for-byte raw logs.

| Fixture | Contract observation |
|---|---|
| `success-run.stream.json` | A create run can emit init, file tool activity, and a terminal success result. |
| `failure-run.stream.json` | A provider API error can still be wrapped in `is_error: false`; do not trust that flag alone. |
| `invalid-output-run.stream.json` | A terminal success result can exist without a valid artifact or `index.html`. |
| `timeout-run.stream.json` | An externally timed-out run can end without a terminal result. |
| `cancel-run.stream.json` | A user-cancelled run can stop during tool activity without a terminal result. |

Raw captures, exit codes, stderr, and output trees belong in the ignored `raw/`
directory. Before updating a committed fixture, minimize it to the event shape
needed by a test and remove credentials, local paths, session IDs, UUIDs, private
reasoning, and unrelated provider output.

The authoritative support conclusions, including the current **unsupported**
status for modify, are in [README.md](README.md).
