## Context

The repository currently contains planning artifacts but no application implementation. V1 must create a
working baseline across the Vue admin, FastAPI workflow, SQLite metadata, isolated execution, per-project Git,
Phaser build/playtest, and public preview. See proposal.md for motivation.

The key trust boundary is between the trusted platform repository/state and an untrusted run workspace.
OpenGame, package installation, generated code, and browser tests execute only against an exported workspace.

## Goals / Non-Goals

**Goals:**

- Establish one provider-neutral runtime boundary and an OpenGame implementation.
- Make workflow state explicit and recoverable without a workflow engine or message broker.
- Separate Candidate attempts from immutable published Versions.
- Produce platform-validated structured TestReports and comparable baseline evidence.
- Preserve a playable Version across every failure and cancellation path.

**Non-Goals:**

- Claude SDK integration or domain Agent profiles.
- General checkpoint/resume, queues, multiple workers, or distributed execution.
- Multiple projects, templates, browsers, or user accounts.

## Decisions

### FastAPI owns a persisted deterministic state machine

FastAPI advances explicit stages and writes each transition in SQLite. Human gates are API actions, not
runtime output. A SQLite transaction guards the single active run and publication pointer.

Alternative: let OpenGame run the end-to-end business flow. Rejected because confirmations, failure recovery,
and publication would become provider-specific and could not be reused by V2.

### Runtime contract returns sessions, events, and structured results

The backend defines commands for planning-compatible creation, modification, repair-compatible diagnostics,
testing, cancellation, status, and results. OpenGameAdapter maps its actual supported commands into this
contract and reports unsupported operations explicitly.

Alternative: import OpenGame internals. Rejected to keep version pinning, cancellation, and replacement at a
process boundary.

### Candidate and Version are separate persisted entities

A run writes to `data/workspaces/{run_id}/{session_id}` and snapshots a Candidate under a Candidate-specific
path. Candidates retain build/test state and repair ancestry. Only a validated PASS transaction imports
allowed files into the trusted Git repository, creates a Version, stores its artifact, and changes the
playable pointer.

Alternative: commit every attempt as a Version. Rejected because failure history and published history need
different invariants and user meaning.

### Platform validates deterministic test evidence

The Phaser template exposes a read-only test bridge. A fixed Chromium suite produces required check results
and evidence. The platform validates report completeness and actual command exits before accepting PASS.

Alternative: trust runtime text saying the game works. Rejected because generated code is not completion.

### Workspace is exported and imported through allowlists

The runner receives no trusted `.git`, platform source, host home, or unrelated credentials. Import resolves
paths, rejects traversal/symlinks/protected files, validates GameSpec, and scans logs/output for secrets.

Alternative: let the runtime work directly in the project repository. Rejected because cancellation or
malicious generated commands could corrupt trusted history.

## Risks / Trade-offs

- [OpenGame CLI shape differs from assumptions] → implement a spike first, pin a version, and keep a Fake
  Runtime contract suite so platform work can proceed.
- [Single-process run coordination is interrupted by restart] → persist active run, mark orphaned runs failed
  on startup, and allow clean retry from the playable Version.
- [Browser gameplay tests are flaky] → use a deterministic seed, test bridge, fixed viewport, and evidence per
  check; never lower the publication gate to hide flakes.
- [Dependency installation needs network] → use an approved registry policy and cache while retaining
  workspace/container isolation.
- [Candidate storage grows] → acceptable for the small demo scope; cleanup policy is deferred until measured.

## Migration Plan

1. Create the shared schemas and Fake Runtime contract suite.
2. Add SQLite migrations for runs, events, Candidates, TestReports, and Versions.
3. Build the deterministic workflow and isolated runner around Fake Runtime.
4. Prove the Phaser Candidate → build → TestReport → Version vertical slice.
5. Integrate pinned OpenGameAdapter and capture baseline runs.
6. Add Vue workflow/review/history surfaces and deployment packaging.
7. Roll back by keeping the last published artifact and disabling new runs; Candidate failures never require
   rewriting Git history.

## Open Questions

- The exact pinned OpenGame CLI version and non-interactive argument format will be fixed by the first spike.
- Benchmark idea fixtures may change without changing the runtime or publication contracts.
