# AI Cowork Game V1 Full-Scope Rebaseline

> **Status:** Approved execution baseline for the 2026-08-20 demonstration.
> **Product authority:** `docs/product/AI_COWORK_GAME_V1_DESIGN_SPEC.md`.
> **Scope rule:** Design Spec P0 and P1 are both mandatory V1 deliverables. Wave labels express dependency order, not deferral.

## Goal

By 2026-08-20, demonstrate the complete persisted lifecycle with a real replaceable Agent Runtime provider:

```text
Idea → Brainstorming → GDD → GameSpec
→ Build → Candidate → Platform Verification → Human Play Review → Promote
→ Playable → Change / Assets / Code Draft → New Playable
→ Publish Review → Release → Share / Build ZIP / Source ZIP
→ Resource Review → My Resources
→ Second Project Resource Match → Build Agent Context → Candidate
```

The demonstration also covers `waiting_for_input`, GameSpec Amendment, Drift Detection, restore, three-round repair ancestry, Git checkpoints and immutable provenance.

## Global Constraints

- zhao owns product contracts, FastAPI business transitions, persistence, Vue and Human Gates.
- zhang owns OpenGame CLI/Executor/Adapter, runtime isolation, Git workspace mechanics and artifact packaging.
- One Change has one owner, one worktree, one branch and one PR.
- FastAPI owns all business gates; Vue, timers and providers never advance them implicitly.
- OpenGame is the first real Game Build provider, not product vocabulary. Shared contracts remain compatible with Claude SDK and Pi Agent providers.
- Verification is platform-owned and uses real browser evidence plus `window.__GAME_TEST__`.
- Candidate, working draft and repair attempts never mutate the current Playable before Promote.
- No Marketplace, multi-user collaboration, Unity/Godot/3D, queue, distributed worker or workflow engine.

## Completion Gates

V1 is complete only when all of the following pass:

- [ ] Confirmed GDD and GameSpec are immutable revisions with Git checkpoints.
- [ ] Real Build creates a Candidate without replacing current Playable.
- [ ] Verification records Build Check, Browser Smoke and Core Gameplay Acceptance evidence.
- [ ] `PASSED`, `PARTIAL_FAILURE`, `CRITICAL_FAILURE` and invalid evidence paths are tested.
- [ ] Human Play Review is required before Promote.
- [ ] Cancel, timeout, retry, reconnect and backend restart preserve lifecycle invariants.
- [ ] `waiting_for_input` and GameSpec Amendment survive refresh and resume through explicit decisions.
- [ ] Unresolved semantic drift blocks Promote/Publish.
- [ ] Code and Assets drafts support Diff, Apply and Discard; Apply creates a Candidate.
- [ ] Restore creates a new Candidate chain and never rewrites history.
- [ ] Publish creates an immutable Release with Play, Share, Build ZIP and Source ZIP.
- [ ] Resource Review persists SavedResources and edits.
- [ ] Accepted resources enter another Project's immutable Build Context and consumption provenance.
- [ ] Clean-database, clean-workspace browser E2E passes without frontend business fixtures.

## Daily Rhythm

```text
09:30-09:50  sync main, contract/owner gate, choose one vertical acceptance
09:50-12:30  TDD implementation block
14:00-16:20  integration and failure-path block
16:20-17:00  required review, merge, browser acceptance, evidence
19:30-21:30  only recover the day's failed gate
```

No new scope starts while the previous day's vertical gate is red.

## August 14: Contract Rebaseline And Integration Inventory

**zhao**

- [ ] Complete revised C00 artifacts, canonical Design Spec, Catalog and migration matrix.
- [ ] Inventory C01-C12 branches/worktrees/commits against `main`; record merged, review-needed and corrective status.
- [ ] Audit C05-C07/C11-C12 contracts for profiles, task-scoped context, verification severity and `needs_input`.
- [ ] Open focused corrective Change briefs instead of silently rewriting completed Change history.

**zhang**

- [ ] Reconfirm C08-C10 real OpenGame evidence against the revised provider-neutral runtime boundary.
- [ ] Identify concrete support for create/change/cancel/continuation and standardized Phaser test hook injection.

**Daily Gate**

- [ ] One authoritative product spec and one revised Change graph exist.
- [ ] Every existing C01-C12 implementation has an explicit merge/conformance status.
- [ ] No downstream implementation consumes the old V1/V2 multi-agent split as contract truth.

## August 15: Runtime Isolation, Git Foundation And Contract Corrections

**zhao**

- [ ] Complete corrective C05/C06/C07/C11/C12 contract and persistence work.
- [ ] Persist task-scoped Build Context with exact GameSpec, baseline, affected scope, resources and overrides.
- [ ] Implement Verification severity, `window.__GAME_TEST__` evidence validation and three-attempt repair ancestry.

**zhang**

- [ ] Complete C13 isolated Candidate Workspace and cancellation cleanup.
- [x] Complete C20 Project Git repository/checkpoint primitives and artifact provenance mapping. — Done 2026-08-15: `ProjectGitService` (dulwich) init/commit/tag/read primitives + content policy (reject absolute/`..`/symlink/`.git`/protected, secret-scan via `app.redaction`) + `ProvenanceService` (resolve_playable/release + compute_checksum + on-disk commit verification + drift detection). Zero migration, zero `lifecycle.py`/`models.py`/`api/` change (Git is not the business state machine). Real Promote-wiring proof: a test passes a real commit sha into `promote_candidate(git_commit=...)` unchanged. 46 C20 tests pass; offline full 198/0. The line-114 checkpoint wiring (Confirm/Promote/Publish) is a separate slice (depends C13+C14+C16).
- [ ] Make the real provider produce a Candidate that the platform browser runner can verify.

**Daily Gate**

- [ ] Confirmed GameSpec starts one real Build and creates one isolated Candidate.
- [ ] Refresh/reconnect does not create a second run.
- [ ] Verification evidence is platform-generated; runtime self-reported PASS is rejected.

## August 16: Human Play, Promote, Waiting Input And Drift

**zhao**

- [ ] Complete C14 Human Play Review plus idempotent Promote and restore-as-new-Candidate.
- [ ] Complete C15 real Build/Candidate/Playable UI with cancel, retry, reconnect and preview states.
- [ ] Complete C21 `waiting_for_input`, Blocking Build Decision, Amendment and Drift gates.

**zhang**

- [x] Finish C20 Confirm GDD/GameSpec, Promote and Publish checkpoint support. — Done 2026-08-17: `CheckpointService` (`backend/app/services/checkpoint.py`, zhang-owned) wraps the four `ProjectLifecycleService` gates WITHOUT modifying them (zhao's ownership preserved — `git diff` of `lifecycle.py` gate bodies is empty): Confirm GDD → commits `gdd/{rev}.json` + `GameDesignRevision.git_commit` + tag; Confirm GameSpec → `gamespec/{rev}.json` + `GameSpecRevision.git_commit`; Promote → imports the candidate's real artifact from the C13 run workspace into `playable/index.html`, computes sha256, overwrites `PlayableVersion.git_commit`/`artifact_checksum` with the REAL sha (replacing the pre-C20 caller-supplied dummy string); Publish → tags `release-{n}` + `Release.git_commit` snapshot. Migration `0012_c20_checkpoint` adds nullable `git_commit` to `game_design_revisions`/`game_spec_revisions`/`releases` (`playable_versions.git_commit` already existed). API `design.py` Confirm GDD/GameSpec endpoints call `CheckpointService` and surface `git_commit`. Reuse C20 `ProjectGitService`/`ProvenanceService`/`app.redaction`. 8 checkpoint tests pass (round-trip + idempotent + restart-recoverable + Release resolution + owner-boundary invariant); offline full 272/0. Promote/Publish REST endpoints deferred to C14/C16 (the `CheckpointService.promote`/`publish` helpers exist now). Branch is stacked on the unmerged C20 primitives PR.
- [ ] Add provider continuation/rebuild fallback for a resolved blocking decision.
- [ ] Required Review C14/C15/C21 failure and isolation paths.

**Daily Gate**

- [ ] Automated PASS opens Human Play Review and does not auto-Promote.
- [ ] Human Promote creates a Git-backed immutable PlayableVersion.
- [ ] A blocking design conflict survives refresh; confirmed Amendment resumes safely.
- [ ] Unresolved semantic drift is rejected by Promote.

## August 17: Release, Distribution And Resource Library

**zhao**

- [ ] Complete C16 Publish Review/Release and implementation override review.
- [ ] Complete C17 ResourceCandidate batch, Resource Review and persistent My Resources.
- [ ] Complete C18 resource reference/use/cancel provenance and first-use immutable snapshots.

**zhang**

- [ ] Complete C23 immutable Play Release, Share Link, Build ZIP and sanitized Source ZIP.
- [ ] Verify packaging cannot escape the selected Project/Release or include secrets.

**Daily Gate**

- [ ] Publish creates one immutable Release from a selected PlayableVersion.
- [ ] Share and both ZIP outputs resolve to the same Git/artifact provenance after later changes.
- [ ] Resource Review saves, ignores, undoes and edits without losing state on refresh.

## August 18: Assets, Code Drafts And Advanced Resource Build Context

**zhao**

- [ ] Complete C22 Assets and Code Working Draft UI/API with Diff, Apply and Discard.
- [ ] Route applied drafts through Candidate, Verification, Human Play Review and Promote.
- [ ] Complete C24 richer matching, parameter adaptation acceptance and task-scoped resource implementation context.

**zhang**

- [ ] Support safe asset/code draft materialization in isolated workspaces.
- [ ] Map approved resource capability, implementation refs and dependencies into the real provider request.
- [ ] Required Review C22/C24 security and provider-boundary evidence.

**Daily Gate**

- [ ] Discard leaves the current Playable and Git history unchanged.
- [ ] Apply creates a new Candidate; semantic changes enter Amendment/Drift gates.
- [ ] Project B's Candidate records actual consumption of Project A's SavedResource revision.

## August 19: Complete V1 E2E And Freeze

**Both**

- [ ] Start from clean database, clean Project workspace and fixed provider version.
- [ ] Run C19 through every lifecycle step in the Goal flow.
- [ ] Exercise cancel, timeout, retry, reconnect, restart, partial/critical verification, repair limit, waiting input, amendment rejection, drift block, restore and packaging rejection.
- [ ] Run backend unit/integration/contract tests, frontend typecheck/build and browser acceptance.
- [ ] Record commits, migrations, provider version, screenshots, API evidence, artifact checksums and recovery steps.

**18:00 Freeze Gate**

- [ ] No open Critical acceptance defect.
- [ ] No frontend fixture or FakeGameAgent is used for demonstrated business state.
- [ ] Both Projects and all immutable records survive service restart.
- [ ] Freeze demonstration commit, database migration head, provider version and recovery snapshot.

## August 20: Demonstration

- [ ] Run health, migration, disk, port, provider credential and artifact hosting checks.
- [ ] Use the frozen commit; only blocking fixes are permitted.
- [ ] Demonstrate the entire Goal flow, including one failure protection path and Project A resource reuse in Project B.
- [ ] Show Candidate versus Playable separation, Human Gates, Git/artifact provenance and immutable Release downloads.

## Stop-The-Line Rules

- A Candidate can become Playable without platform Verification and Human Play Review.
- Refresh or reconnect creates a duplicate Build.
- Failure, cancellation, draft apply or repair mutates current Playable before Promote.
- Provider events directly Confirm, Promote, Publish or Save Resource.
- Resource UI says “used” without the resource entering Build Context and Candidate provenance.
- Share/ZIP output is mutable, crosses Project boundaries or contains secrets.
- A Design Spec P1 capability is silently marked out of V1 scope.

Any rule above blocks new feature work until resolved.
