## Context

V2 depends on the implemented and archived V1 workflow, runtime boundary, isolation model, normalized events,
Candidate/TestReport/Version lifecycle, and OpenGame benchmark. See proposal.md for motivation. It adds Claude
Agent SDK without transferring business-state ownership to the SDK or Agents.

The principal trust boundaries are Agent-to-tool, Agent-to-workspace, provider-event-to-platform-event, and
TestAgent-report-to-publication. Claude credentials remain deployment secrets and are not placed in project
workspaces.

## Goals / Non-Goals

**Goals:**

- Implement ClaudeAgentRuntimeAdapter as the primary backend using Python alongside FastAPI.
- Define four least-privilege Agent profiles with typed inputs and outputs.
- Persist run/session mapping and normalize all SDK activity into V1 RunEvents.
- Add platform-controlled asset acceptance, TestReport validation, and bounded repair/retest.
- Prove workflow parity and retain OpenGame fallback/benchmark behavior.

**Non-Goals:**

- Four Agent services, autonomous handoffs, or Agents that create new Agents.
- Giving Claude tools that directly confirm, accept, publish, or mutate platform database state.
- Provider-native events in frontend contracts.
- Replacing deterministic build/browser evidence with model judgment.

## Decisions

### Use Python Claude Runtime inside the FastAPI modular monolith

The adapter manages SDK sessions asynchronously within the backend process boundary while execution tools run
in isolated containers/workspaces. This keeps cancellation, event persistence, state transitions, and session
mapping in one language and transaction boundary.

Alternative: a TypeScript or separate Agent service. Rejected because it adds another deployment and failure
boundary without a V2 requirement.

### Model each domain Agent as a versioned profile and session

Each profile includes system instructions, Domain Skill references, typed input/output schemas, tool/MCP
allowlists, workspace paths, model policy, timeout, and budget. FastAPI creates sessions in a fixed stage order.

Alternative: one general Agent with every tool. Rejected because responsibility separation, auditability, and
least privilege are mandatory capabilities.

### Do not expose business-state mutation tools

PlanningAgent submits drafts; AssetAgent submits a manifest proposal; CodingAgent submits file changes;
TestAgent submits evidence. Human/API actions and deterministic platform validation advance gates.

Alternative: expose `confirm_gdd`, `accept_assets`, or `publish_version` as Agent tools. Rejected because an LLM
could bypass human review or safety checks.

### Put tools behind typed platform gateways

Filesystem, GameSpec validation, asset operations, build, browser playtest, and approved MCP integrations are
registered per profile. Gateways enforce path canonicalization, input schemas, timeouts, output limits, audit
events, and secret redaction independently of the model.

Alternative: rely only on prompt instructions. Rejected because prompts are not authorization boundaries.

### Normalize SDK events at the adapter boundary

Every native message, tool request/result, usage record, artifact, and error maps to a versioned RunEvent with
backend, AgentSession, Candidate, attempt, and parent correlation where available. Raw provider events may be
kept in restricted diagnostics but are not user-facing contracts.

Alternative: store and stream SDK events directly. Rejected because it couples storage/UI to one SDK and may
leak provider-specific or sensitive data.

### Repair is a bounded platform loop with new Candidate attempts

The platform validates TestReport, decides whether budget allows repair, starts CodingAgent with the failed
evidence, creates a child Candidate attempt, then starts a new TestAgent session. Agents cannot recurse or
self-schedule.

Alternative: let CodingAgent and TestAgent converse until satisfied. Rejected because termination, cost,
evidence, and Candidate ancestry would be uncontrolled.

## Risks / Trade-offs

- [SDK API or event schema changes] → pin the SDK, isolate provider mapping, and maintain adapter contract
  fixtures against recorded sanitized events.
- [Agent permissions are accidentally broad] → default deny, versioned policies, negative contract tests, and
  audit every denied invocation.
- [Session resumption is unreliable] → persist provider session IDs but treat them as an optimization; recover
  from stable platform artifacts and Candidates rather than claiming unsafe continuation.
- [Four sessions increase cost and latency] → use stage-specific model/budget policies, skip no required gates,
  and report parity metrics against OpenGame.
- [TestAgent hallucinates evidence] → reconcile every report with deterministic tool outputs and evidence paths.
- [V2 work destabilizes V1] → keep runtime selection configured per new run and retain the OpenGame contract
  suite and playable artifact rollback.

## Migration Plan

1. Require V1 shared contracts and baseline acceptance to pass before provider integration.
2. Add AgentSession persistence and versioned profile/tool-policy configuration behind disabled Claude runtime.
3. Implement SDK session lifecycle and RunEvent normalization with recorded fixtures.
4. Add PlanningAgent and AssetAgent gates, then CodingAgent Candidate output.
5. Add TestAgent TestReport plus negative evidence validation.
6. Add bounded repair/retest and runtime parity acceptance journeys.
7. Enable Claude as primary for new runs while retaining OpenGame fallback.
8. Roll back by selecting OpenGame for subsequent runs; existing Candidates, Versions, and events remain valid.

## Open Questions

- The exact pinned Claude Agent SDK and Claude model versions will be selected during the first V2 spike.
- Initial repair attempt, time, and cost limits may be tuned from V1/V2 benchmark evidence without changing
  the bounded-loop requirement.
