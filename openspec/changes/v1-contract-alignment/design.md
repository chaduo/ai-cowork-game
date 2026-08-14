## Context

See `proposal.md` for the motivation. C01-C12 have started establishing the real FastAPI, SQLite, Project, GameSpec, RunEvent, Build and Candidate foundations in feature worktrees, while the canonical planning artifacts still describe the repository as frontend-only. The confirmed V1 Design Spec expands the executable V1 contract beyond the earlier C00-C19 wording, so the plan must be rebased without treating implemented code as a competing source of truth.

## Goals / Non-Goals

**Goals:**

- Establish one provider-neutral V1 vocabulary and state machine for all remaining and corrective V1 Changes.
- Keep product-owned design data separate from runtime/provider execution input.
- Preserve explicit human control at all six Design Spec gates, including blocking build decisions and Human Play Review.
- Make multi-project isolation and cross-project SavedResource provenance testable.
- Make GDD/GameSpec revisions, Git checkpoints, working drafts, verification evidence, Release outputs and resource-assisted builds traceable.
- Give every legacy artifact one migration destination and one owner.

**Non-Goals:**

- Implementing the backend, database, runtime, CLI, browser test runner or UI.
- Choosing concrete OpenGame command flags before the C08 spike evidence.
- Selecting Claude SDK, Pi Agent or OpenGame as the permanent product vocabulary; providers remain replaceable.
- Introducing a generic workflow engine or changing the existing frontend prototype behavior.

## Decisions

### 1. Normative source hierarchy

The approved `docs/product/AI_COWORK_GAME_V1_DESIGN_SPEC.md` is the highest product authority. The aligned Catalog owns roadmap and Change boundaries; approved OpenSpec artifacts own each Change's normative contract. Machine-readable contracts remain under `specs/001-game-creation-mvp/contracts/` until a later restructuring is explicitly approved. Implemented code, the frontend prototype, old baseline and old contracts are conformance evidence, not alternative product authorities.

This keeps the current repository layout stable while preventing three competing contract directories.

### 2. V1 product scope

V1 supports one user, multiple isolated Projects and Phaser 2D browser games. The platform contract requires a validated browser-playable artifact with a known entry point, build/test evidence and provenance. It does not require one genre or survival rules. A demo may use a fixed fixture/capability profile, but that fixture is not the canonical product vocabulary.

The C08 spike may report that the current OpenGame runtime supports a narrower capability profile. Such a provider limitation is recorded in the adapter capability response, not silently promoted into `CreatorGameSpec` or the global V1 product scope.

### 3. Canonical design/build boundary

`CreatorGameSpec` is product-owned, provider-neutral, human-readable and versioned with a Project's confirmed design. It describes the intended final game: metadata, gameplay, characters/entities, world, rules/progression, visual direction, scope and validation intent. It never contains runtime command flags, workspace paths, provider session IDs, Candidate IDs, Resource IDs, drawer state or recommendation decisions.

`RuntimeBuildSpec` is a validated, immutable build input derived from a confirmed `CreatorGameSpec`, accepted assets and a selected runtime capability profile. It may contain normalized runtime settings, artifact entry expectations, allowed paths and adapter-facing values. It is not edited directly by the creator and never becomes the source of product design truth.

### 4. Candidate/version/release/resource separation

`BuildCandidate` is an attempt snapshot produced by a build or change run. Platform Verification evaluates it through Build Check, Browser Smoke and Core Gameplay Acceptance using standardized evidence such as `window.__GAME_TEST__`. `PASSED`, `PARTIAL_FAILURE` and `CRITICAL_FAILURE` are platform verdicts; a runtime cannot self-certify them. Auto-repair may create at most three traceable Candidate attempts. A verified Candidate still requires Human Play Review before Human Promote creates an immutable `PlayableVersion`. Human Publish creates an immutable `Release` from a selected PlayableVersion.

`ResourceCandidate` is a Release-scoped extraction result and uses its own schema, repository and lifecycle. `SavedResource` is a global library entity created only by the Resource Review Human Gate. A saved resource retains source Release, PlayableVersion, Project and evidence provenance; editing its display name/description does not rewrite the source artifact.

### 5. Human Gate ownership

FastAPI/API actions are the only business transitions for Confirm GDD, Confirm GameSpec, Blocking Build Decision, platform verdict acceptance, Human Play Review/Promote, Publish Review, and Resource Save/Ignore. Runtime output can provide evidence, structured inference and proposed changes, but cannot invoke these transitions. The frontend renders server state and sends explicit user actions; timers and fixture callbacks cannot advance a persisted business state.

### 6. Runtime profiles and task-scoped context

V1 uses one provider-neutral Agent Runtime contract with Game Design, GameSpec and Game Build profiles. OpenGameAdapter is the first build provider used for integration evidence, but Claude SDK and Pi Agent may implement the same capability contract without changing product state. Verification remains platform-owned and is not an Agent profile.

Every run receives task-scoped context only: the exact confirmed GDD/GameSpec revision, base Playable, affected scope, accepted resource references and implementation dependencies, relevant overrides, and isolated Candidate Workspace. Resource selection is not complete until these references are present in the immutable build input and observable provenance.

### 7. Git, working drafts and semantic safety

SQLite owns workflow state, pointers, jobs and indexes. Git owns confirmed GDD/GameSpec content, code, assets and immutable checkpoints. Confirm GDD, Confirm GameSpec, Promote and Publish create traceable checkpoints. Assets and Code edits occur in working drafts with Diff plus Apply/Discard; Apply creates a Candidate and never mutates the stable Playable directly.

Implementation-only changes may proceed through verification. Design-semantic changes require a confirmed GameSpec Amendment before Promote. Drift Detection and Publish Review surface relevant implementation overrides; unresolved semantic drift blocks Promote or Release.

### 8. Wave ordering is not scope deferral

All Design Spec P0 and P1 capabilities are V1 deliverables. Wave 1 establishes the main vertical lifecycle. Wave 2 completes `waiting_for_input`, amendments, drift, restore, Assets/Code drafts, richer matching, Git-backed provenance and Share/ZIP distribution. A capability may move between waves for dependency reasons, but may not be removed from V1 without a new approved product decision.

### 9. ID and provenance rules

Every persisted entity has a stable opaque ID. Candidate, TestReport, PlayableVersion, Release, ResourceCandidate and SavedResource retain direct foreign-key provenance to the Project and their immediate source. Immutable records reference the exact design/spec revision, runtime build input, parent Candidate/Version, evidence and artifact checksum where applicable. Restore creates a new Candidate chain; it never rewrites history.

### 10. Legacy baseline disposition

`platform-v1-opengame-baseline` is split and superseded as a planning source. Its useful concepts map to C00 governance, C06/C07 contracts, C08/C09 runtime spike/executor, C10 adapter, C11-C15 candidate/test/promotion flow and C19 evidence. Its README is marked legacy, and it must be archived after the split Changes are approved. No new implementation task may cite it as an independent source of truth.

## Risks / Trade-offs

- [OpenGame only supports a narrower game profile] → expose a capability/profile constraint at RuntimeBuildSpec mapping and C08 evidence; do not change the product glossary silently.
- [Keeping the historical `specs/001-game-creation-mvp/contracts/` path causes confusion] → use the migration matrix and update each file's header/owner before consumers are implemented.
- [Multiple Projects increase isolation surface] → make `project_id` mandatory on all project-scoped records and add cross-project repository tests in C02/C19.
- [A provider emits a success event before platform validation] → treat provider output as untrusted evidence and require platform TestReport validation plus explicit Human Gate actions.
- [The expanded V1 exceeds the original August 20 budget] → preserve complete V1 scope, execute in dependency-ordered waves, and expose daily stop-the-line gates rather than silently dropping P1.
- [Working draft or repair corrupts the stable game] → isolate every Candidate workspace and require verification plus explicit Promote before updating the current Playable pointer.
- [Old baseline remains visible in OpenSpec list] → mark it legacy now and archive it only after the split capability Changes are ready; block implementation that cites the legacy directory directly.

## Migration Plan

1. Land C00 governance artifacts, config context and the migration matrix.
2. For each downstream Change, update only the contract files assigned by the matrix before implementation.
3. Audit already implemented C01-C12 behavior against the revised governance contract; create focused corrective Changes instead of rewriting history or silently mutating closed acceptance criteria.
4. Complete Wave 1: GDD/GameSpec, real Build, Candidate, platform verification, Human Play Review/Promote, Playable iteration, Publish/Release, Resource Review/library and resource-assisted Build Context.
5. Complete Wave 2: waiting-for-input, amendments, drift, Git checkpoints, Assets/Code drafts, restore, richer matching and full Share/ZIP distribution.
6. Run a clean two-Project end-to-end rehearsal that validates provider replacement boundaries, Git/artifact provenance and every Human Gate.
7. Archive the legacy baseline and historical contracts after all replacement artifacts are reviewed; never delete historical evidence before the replacement is merged.

## Open Questions

无。C00 的范围、主要边界和迁移处置必须在本 Change Review 前关闭；C08 的具体 CLI 命令和 runtime capability 只作为 C00 已定义边界下的 provider evidence。
