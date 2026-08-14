## 1. Contract decision record

- [x] 1.1 Review the C00 Brief, Catalog sections 0-3 and all C00 input artifacts; record contradictions and final decisions in `design.md`.
- [x] 1.2 Freeze the canonical glossary and lifecycle transitions for Project, CreatorGameSpec, RuntimeBuildSpec, BuildCandidate, TestReport, PlayableVersion, Release, ResourceCandidate and SavedResource.
- [x] 1.3 Freeze Human Gate ownership and failure/restore invariants; confirm runtime/provider output is evidence only.
- [x] 1.4 Reconcile the approved 2026-08-14 V1 Design Spec and record that both P0 and P1 are mandatory V1 scope implemented as Wave 1 and Wave 2.
- [x] 1.5 Freeze the six Human Gates, one-runtime profile model, platform Verification/Human Play Review order, Git-backed content boundary and resource-assisted Build Context.

## 2. Migration and source-of-truth alignment

- [x] 2.1 Complete `docs/development/V1_CONTRACT_MIGRATION_MATRIX.md` with every listed legacy file, decision, owner, reviewer and order.
- [x] 2.2 Update `openspec/config.yaml` to describe multi-project browser artifact V1 and explicit Human Gate ownership.
- [x] 2.3 Mark `platform-v1-opengame-baseline` as legacy migration input and map its requirements to C00/C06-C19 without leaving it as an active parallel authority.
- [x] 2.4 Update Catalog C00 decision links and downstream dependency notes to point at the approved C00 artifacts.
- [ ] 2.5 Store the approved V1 Design Spec in the repository and update the source hierarchy, Catalog and August 20 schedule to reference it.
- [ ] 2.6 Extend the migration matrix for GDD revisions, Agent profiles, Verification severity/test hook, Git checkpoints, working drafts, amendments/drift, Release distribution and resource-assisted Build Context.

## 3. Contract artifacts

- [x] 3.1 Create the `v1-contract-governance` spec and validate all normative requirements and scenarios.
- [x] 3.2 Review the existing GameSpec, TestReport, RunEvent, reusable-resource and OpenAPI materials against the C00 boundary; record exact replacement owners for detailed machine schema work in the matrix.
- [x] 3.3 Run `openspec validate v1-contract-alignment` and resolve all errors or warnings that indicate duplicate capabilities or missing deltas.
- [ ] 3.4 Audit C01-C12 implementation artifacts against the revised contract and create explicit corrective Change inputs for every mismatch; do not rewrite completed Change history silently.
- [ ] 3.5 Split all remaining Wave 1 and Wave 2 work into dependency-ordered Changes with independent acceptance and browser evidence.

## 4. Human review and handoff

- [ ] 4.1 Perform the revised C00 self-review: no automatic Human Gate transition, no Candidate/ResourceCandidate conflation, no provider-specific fields in CreatorGameSpec, and no Design Spec P1 capability deferred outside V1.
- [ ] 4.2 Ask zhang to Required Review C00 and explicitly review the C08 boundary without modifying C08 implementation.
- [ ] 4.3 Commit only C00 planning/contract changes in `feature/c00-v1-contract-alignment`, push the branch and open a `[C00]` PR.
- [ ] 4.4 After approval and squash merge, update local `main`, archive/retire the legacy baseline only when the split Changes are ready, and record the C00 Gate evidence.
