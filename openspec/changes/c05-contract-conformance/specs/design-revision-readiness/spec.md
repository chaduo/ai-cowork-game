## Purpose

This capability makes collaborative Game Design durable and reviewable by preserving immutable GDD revisions, explicit clarification/readiness state, and separate human confirmation before a CreatorGameSpec may be built.

## ADDED Requirements

### Requirement: Immutable GDD revisions

The platform SHALL persist each submitted Game Design draft as a project-scoped revision with a stable revision number and SHALL never overwrite the content of a confirmed revision. A later edit SHALL create a new draft revision.

#### Scenario: Edit after GDD confirmation

- **WHEN** a user edits a previously confirmed Game Design
- **THEN** the platform creates a new draft revision and leaves the confirmed revision content, number and confirmation timestamp unchanged

#### Scenario: Repeated save of the same draft

- **WHEN** a user submits a draft twice without changing its content
- **THEN** the platform returns the existing current draft or creates an equivalent new draft according to the API idempotency contract, but never mutates a confirmed revision

### Requirement: Clarification and readiness persistence

The platform SHALL persist clarification answers, unresolved decisions, readiness status and readiness blockers with the current Game Design revision. Readiness SHALL be one of `not_ready`, `ready` or `blocked`, and a blocked or unresolved design SHALL survive refresh and resume.

#### Scenario: Resume unresolved clarification

- **WHEN** a user leaves a project with an unanswered clarification question and later requests its Game Design
- **THEN** the response contains the same pending question/decision and readiness blockers

#### Scenario: Ready design

- **WHEN** all required clarification and design decisions are resolved and the draft satisfies the design contract
- **THEN** the platform reports readiness `ready` and exposes the draft as eligible for Confirm GDD

### Requirement: Explicit Confirm GDD gate

FastAPI SHALL own Confirm GDD. Confirm GDD SHALL reject missing, invalid, blocked or non-current drafts and SHALL atomically mark exactly one GDD revision as confirmed for the project.

#### Scenario: Confirm blocked design

- **WHEN** a user confirms a draft whose readiness is `blocked` or `not_ready`
- **THEN** the API returns a conflict describing the readiness blocker and does not change the confirmed revision

#### Scenario: Confirm ready design

- **WHEN** a user confirms the current valid draft with readiness `ready`
- **THEN** the API marks that revision confirmed, preserves its content immutably and returns its revision metadata

### Requirement: Versioned CreatorGameSpec provenance

Each CreatorGameSpec revision SHALL remain provider-neutral and SHALL record the confirmed GDD revision from which it was generated or submitted. CreatorGameSpec SHALL NOT contain provider commands, workspace paths, Candidate/Resource IDs or UI workflow state.

#### Scenario: GameSpec revision records source GDD

- **WHEN** a CreatorGameSpec draft is saved after a confirmed GDD exists
- **THEN** the revision stores the source GDD revision identity and the exact spec content snapshot

#### Scenario: GameSpec without confirmed GDD

- **WHEN** a user saves or confirms a GameSpec before Confirm GDD
- **THEN** saving may remain a draft if the API contract permits it, but confirmation and Build eligibility are rejected until a confirmed GDD exists

### Requirement: Independent GameSpec confirmation

GameSpec confirmation SHALL remain a distinct Human Gate from Confirm GDD. Confirming a GDD SHALL NOT automatically confirm a GameSpec, and confirming a GameSpec SHALL NOT mutate the GDD content.

#### Scenario: GDD confirmation does not confirm GameSpec

- **WHEN** a user confirms a ready GDD
- **THEN** the latest GameSpec remains draft or missing until the user explicitly confirms it

#### Scenario: Confirm invalid GameSpec

- **WHEN** the latest GameSpec fails canonical schema validation
- **THEN** confirmation returns a validation error and no confirmed GameSpec revision is created
