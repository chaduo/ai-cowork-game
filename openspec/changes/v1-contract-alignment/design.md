## Context

See `proposal.md` for the motivation. The repository is currently a frontend prototype plus planning/contracts; no FastAPI or SQLite implementation exists yet. The old OpenGame baseline and `specs/001-game-creation-mvp/contracts/` contain useful material but assume a single active project, a fixed Phaser survival game, and a Version-centered flow that does not match the aligned V1 roadmap.

## Goals / Non-Goals

**Goals:**

- Establish one provider-neutral V1 vocabulary and state machine before C01-C19 implementation.
- Keep product-owned design data separate from runtime/provider execution input.
- Preserve explicit human control at design, candidate promotion, release publishing and resource saving gates.
- Make multi-project isolation and cross-project SavedResource provenance testable.
- Give every legacy artifact one migration destination and one owner.

**Non-Goals:**

- Implementing the backend, database, runtime, CLI, browser test runner or UI.
- Choosing concrete OpenGame command flags before the C08 spike evidence.
- Designing V2 Claude Agent profiles beyond preserving the provider-neutral boundary.
- Introducing a generic workflow engine or changing the existing frontend prototype behavior.

## Decisions

### 1. Normative source hierarchy

The aligned Catalog is the roadmap and Change boundary. Approved OpenSpec artifacts for the current Change are normative for that Change. After C00 archive, the canonical governance capability becomes the main OpenSpec reference; machine-readable contracts remain under `specs/001-game-creation-mvp/contracts/` until a later repository restructuring is explicitly approved. The frontend prototype, old baseline and old contracts are migration evidence only.

This keeps the current repository layout stable while preventing three competing contract directories.

### 2. V1 product scope

V1 supports one user and multiple isolated Projects. The platform contract requires a validated browser-playable artifact with a known entry point, build/test evidence and provenance. It does not require one genre, survival rules or Phaser as a product-level invariant. A demo may use a fixed fixture/capability profile, but that fixture is not the canonical product vocabulary.

The C08 spike may report that the current OpenGame runtime supports a narrower capability profile. Such a provider limitation is recorded in the adapter capability response, not silently promoted into `CreatorGameSpec` or the global V1 product scope.

### 3. Canonical design/build boundary

`CreatorGameSpec` is product-owned, provider-neutral, human-readable and versioned with a Project's confirmed design. It describes the intended final game: metadata, gameplay, characters/entities, world, rules/progression, visual direction, scope and validation intent. It never contains runtime command flags, workspace paths, provider session IDs, Candidate IDs, Resource IDs, drawer state or recommendation decisions.

`RuntimeBuildSpec` is a validated, immutable build input derived from a confirmed `CreatorGameSpec`, accepted assets and a selected runtime capability profile. It may contain normalized runtime settings, artifact entry expectations, allowed paths and adapter-facing values. It is not edited directly by the creator and never becomes the source of product design truth.

### 4. Candidate/version/release/resource separation

`BuildCandidate` is an attempt snapshot produced by a build or change run. `TestReport` evaluates one Candidate. A valid PASS makes a Candidate eligible for Promote; it does not mutate the current Playable. Human Promote creates an immutable `PlayableVersion`. Human Publish creates an immutable `Release` from a selected PlayableVersion.

`ResourceCandidate` is a Release-scoped extraction result and uses its own schema, repository and lifecycle. `SavedResource` is a global library entity created only by the Resource Review Human Gate. A saved resource retains source Release, PlayableVersion, Project and evidence provenance; editing its display name/description does not rewrite the source artifact.

### 5. Human Gate ownership

FastAPI/API actions are the only business transitions for GDD Confirm, GameSpec Confirm, Candidate/Test verdict acceptance, Human Promote, Human Publish, and Resource Save/Ignore. Runtime output can provide evidence and a proposed result, but cannot invoke these transitions. The frontend renders server state and sends explicit user actions; timers and fixture callbacks cannot advance a persisted business state.

### 6. ID and provenance rules

Every persisted entity has a stable opaque ID. Candidate, TestReport, PlayableVersion, Release, ResourceCandidate and SavedResource retain direct foreign-key provenance to the Project and their immediate source. Immutable records reference the exact design/spec revision, runtime build input, parent Candidate/Version, evidence and artifact checksum where applicable. Restore creates a new Candidate chain; it never rewrites history.

### 7. Legacy baseline disposition

`platform-v1-opengame-baseline` is split and superseded as a planning source. Its useful concepts map to C00 governance, C06/C07 contracts, C08/C09 runtime spike/executor, C10 adapter, C11-C15 candidate/test/promotion flow and C19 evidence. Its README is marked legacy, and it must be archived after the split Changes are approved. No new implementation task may cite it as an independent source of truth.

## Risks / Trade-offs

- [OpenGame only supports a narrower game profile] → expose a capability/profile constraint at RuntimeBuildSpec mapping and C08 evidence; do not change the product glossary silently.
- [Keeping the historical `specs/001-game-creation-mvp/contracts/` path causes confusion] → use the migration matrix and update each file's header/owner before consumers are implemented.
- [Multiple Projects increase isolation surface] → make `project_id` mandatory on all project-scoped records and add cross-project repository tests in C02/C19.
- [A provider emits a success event before platform validation] → treat provider output as untrusted evidence and require platform TestReport validation plus explicit Human Gate actions.
- [Old baseline remains visible in OpenSpec list] → mark it legacy now and archive it only after the split capability Changes are ready; block implementation that cites the legacy directory directly.

## Migration Plan

1. Land C00 governance artifacts, config context and the migration matrix.
2. For each downstream Change, update only the contract files assigned by the matrix before implementation.
3. C01-C05 establish Project and CreatorGameSpec persistence; C06-C10 establish runtime-neutral contracts and the real OpenGame boundary.
4. C11-C18 implement Candidate, TestReport, PlayableVersion, Release and Resource entities in their own repositories and APIs.
5. C19 runs a clean two-Project end-to-end rehearsal and validates provenance.
6. Archive the legacy baseline and historical contracts after all replacement artifacts are reviewed; never delete historical evidence before the replacement is merged.

## Open Questions

无。C00 的范围、主要边界和迁移处置必须在本 Change Review 前关闭；C08 的具体 CLI 命令和 runtime capability 只作为 C00 已定义边界下的 provider evidence。
