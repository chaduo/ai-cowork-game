## Purpose

Defines the canonical V1 product and platform contract so downstream Changes share one lifecycle, explicit human gates, provider-neutral design boundary, and traceable project/resource provenance.

## ADDED Requirements

### Requirement: Canonical V1 lifecycle

The platform SHALL use distinct Project, Game Design, CreatorGameSpec, BuildCandidate, TestReport, PlayableVersion, Release, ResourceCandidate and SavedResource concepts with the lifecycle `Project → GameSpec Confirm → BuildCandidate → TestReport PASS → Human Promote → PlayableVersion → Human Publish → Release → ResourceCandidate → SavedResource`.

#### Scenario: Candidate is not playable automatically

- **WHEN** a runtime produces a successful build artifact
- **THEN** the platform creates or updates a BuildCandidate and does not update the current PlayableVersion until a valid TestReport PASS and explicit Human Promote action are accepted.

#### Scenario: Release is not a build result

- **WHEN** a user publishes a selected PlayableVersion
- **THEN** the platform creates an immutable Release with source provenance and does not mutate the source PlayableVersion.

### Requirement: Explicit Human Gate ownership

FastAPI/API actions SHALL be the only business owner of design confirmation, Candidate/test verdict acceptance, Human Promote, Human Publish and Resource Review save/ignore decisions. Runtime output, Agent sessions, timers and frontend fixtures SHALL NOT perform these transitions.

#### Scenario: Runtime reports success

- **WHEN** an Agent or runtime emits a success event
- **THEN** the event is stored as evidence and the platform waits for its own validation and explicit user action before advancing a Human Gate.

#### Scenario: User leaves and returns

- **WHEN** a user navigates away during a pending gate and later returns
- **THEN** the server-owned pending state remains unchanged and no automatic transition occurs.

### Requirement: Multi-project isolation

The platform SHALL support multiple Projects for one user, and every project-scoped run, Candidate, TestReport, PlayableVersion, Release and resource extraction record SHALL be associated with exactly one Project.

#### Scenario: Two Projects coexist

- **WHEN** Project A and Project B both have runs or versions
- **THEN** reading or mutating Project A cannot change Project B's current playable pointer, releases, candidates or design revisions.

### Requirement: CreatorGameSpec and RuntimeBuildSpec boundary

The platform SHALL treat CreatorGameSpec as the provider-neutral, product-owned and versioned final game design, and RuntimeBuildSpec as a validated derived build input. CreatorGameSpec SHALL NOT contain provider commands, workspace paths, runtime session IDs, Candidate/Resource IDs or UI workflow state.

#### Scenario: Runtime mapping

- **WHEN** a confirmed CreatorGameSpec is submitted to a selected runtime
- **THEN** the platform validates and derives a RuntimeBuildSpec without rewriting the CreatorGameSpec or inserting provider-specific workflow state into it.

### Requirement: Candidate and resource schema separation

BuildCandidate and ResourceCandidate SHALL use different schemas, repositories and APIs. SavedResource SHALL be created only from a reviewed ResourceCandidate and SHALL retain release-scoped provenance.

#### Scenario: Resource extraction after publish

- **WHEN** a Release produces reusable material
- **THEN** the platform creates a Release-scoped ResourceCandidate batch and does not represent those items as BuildCandidates.

#### Scenario: Save resource

- **WHEN** a user explicitly saves a pending ResourceCandidate
- **THEN** the platform creates or updates a SavedResource with source Project, PlayableVersion, Release and evidence references, without changing the source Release artifact.

### Requirement: Immutable provenance and failure safety

PlayableVersion and Release records SHALL be immutable, and failed, cancelled, invalid or incomplete Candidates SHALL NOT replace the current PlayableVersion or mutate an existing Release. Restore SHALL create a new Candidate chain.

#### Scenario: Failed candidate

- **WHEN** build, test, cancellation or import validation fails for a Candidate
- **THEN** the Candidate retains sanitized diagnostics while the current PlayableVersion and existing Releases remain unchanged.

#### Scenario: Restore history

- **WHEN** a user requests restore of an earlier PlayableVersion
- **THEN** the platform creates a new Candidate referencing the selected version and leaves all historical versions and releases intact.

### Requirement: Contract migration has one authority

Each legacy contract or planning artifact SHALL have one keep, update, replace or archive decision with an owner, reviewer and order recorded in the C00 migration matrix. Downstream Changes SHALL cite the approved canonical artifact rather than the legacy baseline.

#### Scenario: Downstream Change starts

- **WHEN** a downstream Change begins implementation
- **THEN** its brief and OpenSpec artifacts identify the matrix row and canonical contract it consumes, and do not introduce a second conflicting definition.

