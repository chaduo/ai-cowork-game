## Purpose

Defines the mandatory Claude Agent SDK runtime, its platform session mapping, normalized events, and coexistence with the OpenGame fallback established in Platform V1.

## ADDED Requirements

### Requirement: Claude Runtime is the V2 primary backend
Platform V2 SHALL integrate Claude Agent SDK as the primary Game Agent Runtime and SHALL NOT be considered complete when only OpenGame can execute the platform workflow.

#### Scenario: Create with Claude Runtime
- **WHEN** the deployment selects the Claude backend and a user submits a valid idea
- **THEN** the same platform workflow completes through Claude-backed domain Agent sessions

### Requirement: Session and event mapping
The platform SHALL map every Claude SDK session to one platform run and AgentSession and SHALL normalize native messages, tool calls, usage, artifacts, and errors into RunEvents before persistence or display.

#### Scenario: Trace a Claude tool call
- **WHEN** a Claude Agent invokes an approved tool
- **THEN** the run history identifies the AgentSession, tool, Candidate or planning artifact, attempt, and normalized result

### Requirement: OpenGame remains available
The platform SHALL retain OpenGame as a fallback, reference, and benchmark backend using the V1 contracts and publication gates.

#### Scenario: Claude backend is unavailable
- **WHEN** Claude Runtime cannot start before project mutation begins
- **THEN** an authorized operator can select the OpenGame fallback without changing the user workflow or weakening publication checks
