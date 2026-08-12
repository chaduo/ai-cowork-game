## Purpose

Constrains four Claude-backed domain Agents to explicit responsibilities, skills, tools, and workspaces while reserving all business gates for the deterministic platform workflow.

## ADDED Requirements

### Requirement: Four distinct Agent profiles
V2 SHALL provide PlanningAgent, AssetAgent, CodingAgent, and TestAgent as distinct controlled profiles with independent instructions, Domain Skills, input/output contracts, tool policies, and workspace permissions.

#### Scenario: Agent profile is created
- **WHEN** the platform starts a domain stage
- **THEN** it creates only the declared Agent profile with the policy and inputs approved for that stage

### Requirement: Agent responsibilities are separated
PlanningAgent SHALL produce GDD and GameSpec drafts; AssetAgent SHALL produce traceable asset proposals; CodingAgent SHALL create, modify, or repair authorized game files; TestAgent SHALL produce structured test evidence and SHALL NOT modify code.

#### Scenario: TestAgent attempts a code write
- **WHEN** TestAgent requests a source-editing tool
- **THEN** the platform denies the call, emits an audit event, and does not alter the Candidate

### Requirement: Platform owns business state
Only the deterministic platform workflow SHALL confirm GDD, confirm GameSpec, accept assets, validate TestReport PASS, and publish a Version.

#### Scenario: Agent claims a gate is complete
- **WHEN** any Agent output claims that a design, asset, test, or Version gate has been approved
- **THEN** the claim is treated as data only and the platform state remains unchanged until the authorized platform action succeeds

### Requirement: Tool and workspace least privilege
Each Agent SHALL be limited to an explicit tool and MCP allowlist plus its assigned workspace paths, and denied operations SHALL be auditable.

#### Scenario: Agent requests an undeclared MCP tool
- **WHEN** an Agent calls an MCP or platform tool outside its policy
- **THEN** the platform rejects the call and records the AgentSession, tool, reason, and attempt
