## Purpose

Ensures the final Claude Runtime proves the same user-visible workflow and safety guarantees as the OpenGame baseline while producing comparable quality and execution evidence.

## ADDED Requirements

### Requirement: Workflow parity
Claude Runtime SHALL complete idea planning, human confirmations, asset review, game creation, Candidate build/test, preview, incremental modification, and Version publication through the same platform actions used by V1.

#### Scenario: User changes runtime backend
- **WHEN** the configured backend changes from OpenGame to Claude before a new run
- **THEN** the user performs the same confirmation, review, preview, modification, and history actions

### Requirement: V2 success journey
V2 SHALL demonstrate one complete game creation, one incremental modification, and one test failure followed by repair, retest, PASS, and Version publication using Claude Runtime.

#### Scenario: Mandatory V2 demonstration
- **WHEN** the final V2 acceptance suite runs
- **THEN** all three journeys complete with traceable AgentSessions, Candidates, TestReports, and final Version outcomes

### Requirement: Comparable benchmark evidence
The platform SHALL report backend, duration, result, failure stage, usage and cost when available, repair attempts, and TestReport outcome for the same recorded benchmark inputs.

#### Scenario: Review runtime comparison
- **WHEN** an operator compares V1 and V2 benchmark runs
- **THEN** the measurements use the same definitions and link to the supporting run evidence
