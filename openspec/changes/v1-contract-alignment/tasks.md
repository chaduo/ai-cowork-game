## 1. Contract decision record

- [x] 1.1 Review the C00 Brief, Catalog sections 0-3 and all C00 input artifacts; record contradictions and final decisions in `design.md`.
- [x] 1.2 Freeze the canonical glossary and lifecycle transitions for Project, CreatorGameSpec, RuntimeBuildSpec, BuildCandidate, TestReport, PlayableVersion, Release, ResourceCandidate and SavedResource.
- [x] 1.3 Freeze Human Gate ownership and failure/restore invariants; confirm runtime/provider output is evidence only.

## 2. Migration and source-of-truth alignment

- [x] 2.1 Complete `docs/development/V1_CONTRACT_MIGRATION_MATRIX.md` with every listed legacy file, decision, owner, reviewer and order.
- [x] 2.2 Update `openspec/config.yaml` to describe multi-project browser artifact V1 and explicit Human Gate ownership.
- [x] 2.3 Mark `platform-v1-opengame-baseline` as legacy migration input and map its requirements to C00/C06-C19 without leaving it as an active parallel authority.
- [x] 2.4 Update Catalog C00 decision links and downstream dependency notes to point at the approved C00 artifacts.

## 3. Contract artifacts

- [x] 3.1 Create the `v1-contract-governance` spec and validate all normative requirements and scenarios.
- [x] 3.2 Review the existing GameSpec, TestReport, RunEvent, reusable-resource and OpenAPI materials against the C00 boundary; record exact replacement owners for detailed machine schema work in the matrix.
- [x] 3.3 Run `openspec validate v1-contract-alignment` and resolve all errors or warnings that indicate duplicate capabilities or missing deltas.

## 4. Human review and handoff

- [x] 4.1 Perform C00 self-review: no automatic Promote/Publish, no Candidate/ResourceCandidate conflation, no fixed survival contradiction, no provider-specific fields in CreatorGameSpec.
- [ ] 4.2 Ask zhang to Required Review C00 and explicitly review the C08 boundary without modifying C08 implementation.
- [ ] 4.3 Commit only C00 planning/contract changes in `feature/c00-v1-contract-alignment`, push the branch and open a `[C00]` PR.
- [ ] 4.4 After approval and squash merge, update local `main`, archive/retire the legacy baseline only when the split Changes are ready, and record the C00 Gate evidence.
