## Why

OpenGame is a V1 baseline, not the final Agent backend. Platform V2 must build AI Cowork Game's own domain
runtime with Claude Agent SDK while preserving the same human gates, workspace isolation, testing evidence,
and Version publication rules proven by V1.

## What Changes

- Add ClaudeAgentRuntimeAdapter as the primary runtime backend while retaining OpenGame as fallback,
  reference, and benchmark.
- Add controlled PlanningAgent, AssetAgent, CodingAgent, and TestAgent profiles/sessions with independent
  system instructions, Domain Skills, tool permissions, and workspace access.
- Map Claude SDK sessions and native events to platform runs, AgentSessions, Candidates, TestReports, and
  normalized RunEvents.
- Add platform-owned asset acceptance and structured test-report validation gates.
- Add a bounded FAIL → CodingAgent repair → TestAgent retest loop.
- Require the same user workflow to complete create game and incremental modification with Claude Runtime.
- Non-goals: using Claude only inside OpenGame, autonomous LLM business orchestration, dynamic unreviewed
  Agent creation, Agent microservices, multiple templates, and runtime LLM NPC behavior.

## Capabilities

### New Capabilities

- `claude-agent-runtime`: Claude Agent SDK integration, session lifecycle, event normalization, and backend selection.
- `domain-agent-governance`: Responsibilities, instructions, skills, tools, MCP access, and denials for four domain Agents.
- `repair-retest-workflow`: Structured TestReport validation and bounded repair/retest behavior.
- `runtime-parity-benchmark`: V1/V2 workflow parity, fallback behavior, and benchmark comparison.

### Modified Capabilities

None in this change package. V2 depends on the V1 capabilities being implemented and archived first, then
extends them through the new capabilities above without weakening their requirements.

## Impact

- Depends on `platform-v1-opengame-baseline` shared workflow, Runtime, Candidate/TestReport/Version, isolation,
  and RunEvent contracts.
- Affects FastAPI orchestration, runtime adapters, Agent profiles, tool/MCP gateways, session persistence,
  audit events, Vue run details, test evidence, and deployment secrets/configuration.
- Adds Claude Agent SDK and Claude credentials as pinned V2 dependencies.
