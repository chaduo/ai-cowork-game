## Purpose

Defines the canonical V1 product and platform contract so downstream Changes share one lifecycle, explicit human gates, provider-neutral design boundary, and traceable project/resource provenance.

## ADDED Requirements

### Requirement: Canonical V1 lifecycle

The platform SHALL use distinct Project, GDD revision, CreatorGameSpec revision, BuildJob, BuildCandidate, VerificationResult/TestReport, PlayableVersion, Release, ResourceCandidate and SavedResource concepts with the lifecycle `Idea → GDD Confirm → GameSpec Confirm → Build → Candidate → Platform Verification → Human Play Review → Human Promote → PlayableVersion → Change/New Version → Human Publish → Release → Resource Review → SavedResource → Future GameSpec/Build Context`.

#### Scenario: Candidate is not playable automatically

- **WHEN** a runtime produces a successful build artifact
- **THEN** the platform creates or updates a BuildCandidate and does not update the current PlayableVersion until platform verification, Human Play Review and explicit Human Promote are accepted.

#### Scenario: Release is not a build result

- **WHEN** a user publishes a selected PlayableVersion
- **THEN** the platform creates an immutable Release with source provenance and does not mutate the source PlayableVersion.

### Requirement: Explicit Human Gate ownership

FastAPI/API actions SHALL be the only business owner of Confirm GDD, Confirm GameSpec, Blocking Build Decision, Candidate/test verdict acceptance, Human Play Review/Promote, Publish Review and Resource Review save/ignore decisions. Runtime output, Agent sessions, timers and frontend fixtures SHALL NOT perform these transitions.

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

### Requirement: Provider-neutral runtime profiles

V1 SHALL expose one provider-neutral Agent Runtime contract with Game Design, GameSpec and Game Build profiles. OpenGame, Claude SDK and Pi Agent integrations SHALL be replaceable providers behind capability declarations, while platform Verification SHALL remain outside the Agent Runtime.

#### Scenario: Runtime provider changes

- **WHEN** a supported runtime provider replaces another provider for a profile
- **THEN** Project lifecycle state, Human Gates, Candidate/Playable semantics and platform Verification contracts remain unchanged.

### Requirement: Task-scoped build context

Each build SHALL persist an immutable task-scoped context containing the exact confirmed GameSpec, base Playable when present, affected scope, accepted resource references and implementation dependencies, relevant overrides and Candidate Workspace. Selecting a SavedResource SHALL NOT be considered applied until the build context contains its reference and provenance.

#### Scenario: Resource-assisted build

- **WHEN** a user accepts a compatible SavedResource for a Project and starts a build
- **THEN** the Game Build profile receives the resource reference and approved implementation context, and the resulting Candidate records whether and how the resource was consumed.

### Requirement: Platform verification and Human Play Review

The platform SHALL validate every Candidate using Build Check, Browser Smoke and Core Gameplay Acceptance evidence. Verdicts SHALL distinguish `PASSED`, `PARTIAL_FAILURE` and `CRITICAL_FAILURE`; runtime self-reporting SHALL NOT establish a verdict. Automated repair SHALL create traceable Candidate attempts and SHALL stop after at most three repair rounds. Human Play Review SHALL be required before Promote.

#### Scenario: Candidate passes automated checks

- **WHEN** all required platform evidence is valid and the Candidate verdict is `PASSED`
- **THEN** the Candidate becomes available for Human Play Review but does not become the current Playable automatically.

#### Scenario: Automated repair limit

- **WHEN** three repair rounds have completed without a valid `PASSED` Candidate
- **THEN** the platform stops automatic repair, retains every attempt and evidence record, and requires explicit user action.

### Requirement: Git-backed content and isolated working drafts

The platform SHALL store workflow state and pointers in the database while storing confirmed GDD/GameSpec content, game code and assets in Git-backed project workspaces. Confirm GDD, Confirm GameSpec, Promote and Publish SHALL create traceable checkpoints. Assets and Code edits SHALL use isolated working drafts with Diff and Apply/Discard; applying a draft SHALL create a Candidate rather than mutate the current Playable.

#### Scenario: Code draft is applied

- **WHEN** a user reviews and applies a Code Working Draft
- **THEN** the platform creates a new Candidate linked to the draft and stable baseline, runs verification, and leaves the current Playable unchanged until Promote.

### Requirement: Amendment and drift gates

The platform SHALL classify changes as implementation-only or design-semantic. A design-semantic change discovered during build SHALL create a GameSpec Amendment Draft and SHALL require Human Confirm before Promote. Unresolved semantic drift or unreviewed publish-relevant implementation overrides SHALL block Promote or Release.

#### Scenario: Build discovers a design decision

- **WHEN** the runtime cannot continue without changing confirmed game semantics
- **THEN** the Build enters `waiting_for_input`, records a GameSpec Amendment Draft, and resumes only through an explicit Blocking Build Decision.

### Requirement: Complete V1 release distribution

Publish Review SHALL create an immutable Release from a selected PlayableVersion with Git and artifact provenance. V1 SHALL expose a Play Release, Share Link, Build ZIP and Source ZIP, and a later game change SHALL NOT mutate an existing Release or its downloads.

#### Scenario: Published release is downloaded later

- **WHEN** a user opens or downloads a previously published Release after newer PlayableVersions exist
- **THEN** the Share Link, Build ZIP and Source ZIP resolve to the immutable content and provenance of that Release.

### Requirement: V1 wave completeness

Design Spec P0 and P1 capabilities SHALL both be delivered in V1. Wave labels SHALL define dependency order only and SHALL NOT be used to remove `waiting_for_input`, GameSpec Amendment, Drift Detection, working drafts, restore, richer resource matching or release distribution from V1 acceptance.

#### Scenario: Wave 1 is complete

- **WHEN** the core vertical lifecycle passes its acceptance gate
- **THEN** the roadmap continues through all Wave 2 acceptance gates before V1 is declared complete.

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
