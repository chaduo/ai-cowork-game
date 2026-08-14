# C12 Candidate Test Gate Verification

## Automated evidence

- C12 service and repair tests: `10 passed, 1 warning`.
- C12 API tests: `4 passed, 1 warning`.
- Full backend regression: `96 passed, 1 warning`.
- Frontend: `npm --prefix frontend run build` passed (`vue-tsc -b` and Vite build).
- Fresh SQLite migration smoke reached `0006_candidate_test_gate` and exposed both `test_reports` and `test_evidence` tables.

## Gate behavior verified

- Complete deterministic evidence marks Candidate `test_gate_status=ready` and stores a platform PASS report.
- Runtime-only PASS, missing evidence, and contradictory claims become `invalid` and cannot become ready.
- Console and completion failures become platform `fail` and Candidate `failed`.
- Failed Build or missing artifact becomes an immutable invalid report.
- Repeating the test request returns the same report; no second report/evidence set is created.
- Repair creates a new Candidate attempt with `parent_candidate_id`; the old failed Candidate and report remain unchanged.
- Project current playable pointer is unchanged across pass, fail and invalid test outcomes.

## Boundary review

- C12 consumes a provider-neutral runner contract and deterministic fake fixtures only.
- No Playwright, browser driver, OpenGame subprocess, queue, worker, Promote, PlayableVersion, Release, or Workspace UI was added.
- C14 will consume `test_gate_status=ready` for the Human Promote gate.
