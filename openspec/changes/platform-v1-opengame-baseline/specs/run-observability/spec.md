## Purpose

Provides durable, provider-neutral visibility and control for long-running game creation work while preserving security, retry safety, and benchmark evidence.

## ADDED Requirements

### Requirement: Durable normalized events
Every run SHALL have a stable ID and an ordered event stream containing normalized stage, backend, message, error, artifact, usage, and Candidate associations that can be recovered after reconnecting.

#### Scenario: Reconnect to a run
- **WHEN** a user reloads the page during an active or completed run
- **THEN** the platform replays events after the last acknowledged sequence without starting a duplicate run

### Requirement: Safe cancellation and retry
The platform SHALL cancel an active runtime and its child work, preserve diagnostics, and allow retry from the most recent playable Version without reusing an untrusted partial workspace.

#### Scenario: Cancel an active run
- **WHEN** the user cancels generation or build work
- **THEN** the process or container stops, the run becomes cancelled, and the playable Version remains unchanged

### Requirement: V1 benchmark evidence
The platform SHALL record duration, result, failure stage, model or runtime usage when available, and TestReport outcome for repeatable OpenGame baseline runs.

#### Scenario: Compare repeated baselines
- **WHEN** the same benchmark idea is run multiple times
- **THEN** each run exposes comparable measurements and its final Candidate or Version outcome
