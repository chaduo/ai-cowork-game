## Purpose

Defines a provider-neutral execution boundary and the OpenGame baseline needed to create and modify game Candidates without coupling platform business state to one Agent implementation.

## ADDED Requirements

### Requirement: Provider-neutral runtime contract
The platform SHALL invoke game creation and modification through a runtime contract that returns structured status, events, artifacts, usage, and errors without exposing provider-native behavior to the user workflow.

#### Scenario: Replace a runtime backend
- **WHEN** a conforming runtime implementation replaces OpenGame
- **THEN** the platform workflow, Candidate lifecycle, and publication gates operate without provider-specific changes

### Requirement: OpenGame baseline
Platform V1 SHALL use a pinned OpenGameAdapter implementation to complete create game and incremental modification flows and retain the resulting measurements as a benchmark.

#### Scenario: Create with OpenGame
- **WHEN** the confirmed GameSpec and accepted assets are submitted to the V1 runtime
- **THEN** OpenGame modifies only the authorized workspace and returns a Candidate result through the shared contract

### Requirement: Isolated workspace execution
The runtime SHALL access only the assigned project workspace, allowed paths, approved environment values, and fixed commands, and SHALL NOT access the trusted repository, platform source, host credentials, or other projects.

#### Scenario: Deny workspace escape
- **WHEN** runtime output references an absolute path, traversal path, symlink escape, or protected file
- **THEN** the platform rejects the output, records a sanitized policy error, and does not import it
