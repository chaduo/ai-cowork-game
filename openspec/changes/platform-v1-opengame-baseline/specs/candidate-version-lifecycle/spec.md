## Purpose

Separates untrusted or failing game changes from immutable published history so generation and testing failures can never replace the last known playable game.

## ADDED Requirements

### Requirement: Candidate precedes Version
Every generated, AI-modified, user-edited, repaired, or restored change SHALL create a Candidate before it can create a Version.

#### Scenario: Candidate is not yet published
- **WHEN** a change has produced files but has not passed build and playtest
- **THEN** it is visible as a Candidate and does not change the playable Version

### Requirement: PASS-only publication
The platform SHALL publish an immutable Git-backed Version only when the Candidate build succeeds and a complete, evidence-backed TestReport is validated as PASS by the platform.

#### Scenario: Publish a valid Candidate
- **WHEN** all required TestReport checks pass with accepted evidence
- **THEN** the platform atomically creates the Version, stores its artifact, and updates the playable pointer

#### Scenario: Reject an incomplete PASS
- **WHEN** a TestReport claims PASS but omits a required check or evidence
- **THEN** the platform marks the report invalid and does not publish a Version

### Requirement: Failure preserves the playable Version
Failed, cancelled, incomplete, or invalid Candidates SHALL retain sanitized diagnostics and SHALL NOT alter the current playable Version or artifact.

#### Scenario: Build failure
- **WHEN** a Candidate build fails
- **THEN** the user can inspect the Candidate failure while the previous playable game remains available
