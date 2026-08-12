## 1. V2 Preconditions and Claude SDK Spike

- [ ] 1.1 Verify the V1 change is implemented, accepted, and archived with its contract and benchmark suites passing.
- [ ] 1.2 Spike the Python Claude Agent SDK to pin SDK/model versions and verify session lifecycle, streaming events, tool registration, usage, timeout, and cancellation.
- [ ] 1.3 Record sanitized SDK event fixtures and map every required event type to the V1 RunEvent contract.
- [ ] 1.4 Add disabled-by-default Claude runtime configuration and credential validation without exposing secrets to project workspaces.

## 2. Runtime Sessions and Event Normalization

- [ ] 2.1 Add AgentSession persistence, provider-session mapping, attempt tracking, policy version, usage, and sanitized error fields.
- [ ] 2.2 Implement ClaudeAgentRuntimeAdapter session start, status, result, cancel, and failure behavior behind the shared runtime contract.
- [ ] 2.3 Implement native Claude event normalization with run, AgentSession, Candidate, tool, parent, attempt, and usage correlation.
- [ ] 2.4 Pass recorded-event, reconnect, cancellation, provider-failure, and secret-redaction contract tests.

## 3. Agent Profiles and Tool Governance

- [ ] 3.1 Define versioned PlanningAgent, AssetAgent, CodingAgent, and TestAgent instructions, input/output schemas, Skills, model policy, timeout, and budget.
- [ ] 3.2 Implement default-deny tool gateways for workspace files, GameSpec, assets, build, browser playtest, and approved MCP integrations.
- [ ] 3.3 Enforce per-profile tool allowlists, workspace paths, input validation, output limits, and audit events independently of prompts.
- [ ] 3.4 Add negative tests for undeclared tools, MCP calls, path escape, cross-profile access, TestAgent writes, and business-state mutation attempts.

## 4. Planning and Asset Stages

- [ ] 4.1 Implement PlanningAgent GDD draft output and keep human GDD confirmation in FastAPI.
- [ ] 4.2 Implement PlanningAgent GameSpec draft/revision output with schema and fixed-scope validation after GDD confirmation.
- [ ] 4.3 Implement AssetAgent manifest proposals, source/license metadata, preview references, and placeholder fallback.
- [ ] 4.4 Implement the platform Asset Accept gate and prove CodingAgent cannot start before acceptance.

## 5. Coding, Testing, and Publication

- [ ] 5.1 Implement CodingAgent create game output as allowlisted changes in an isolated Candidate workspace.
- [ ] 5.2 Implement CodingAgent incremental modification against the selected playable Version and shared GameSpec.
- [ ] 5.3 Implement TestAgent read-only build/playtest tools and structured TestReport output.
- [ ] 5.4 Reconcile TestAgent reports with deterministic command results and evidence, rejecting incomplete or contradictory PASS claims.
- [ ] 5.5 Pass the existing V1 Candidate/TestReport/Version publication suite using Claude Runtime.

## 6. Bounded Repair and Retest

- [ ] 6.1 Implement FastAPI repair policy with attempt, elapsed-time, and cost limits.
- [ ] 6.2 Pass failed TestReport evidence to CodingAgent and create a child Candidate attempt without mutating the failed Candidate.
- [ ] 6.3 Start a new TestAgent session for retest and publish only the final platform-validated PASS Candidate.
- [ ] 6.4 Add tests for successful repair, repeated failure, invalid evidence, cancellation, budget exhaustion, and playable-Version preservation.

## 7. Runtime Parity and Operations

- [ ] 7.1 Add deployment-level backend selection for new runs while retaining OpenGame fallback and reference contract tests.
- [ ] 7.2 Extend run details to display backend, AgentSession, tool/audit events, Candidate attempts, TestReports, usage, and cost.
- [ ] 7.3 Add comparable V1/V2 benchmark reporting using the same inputs and measurement definitions.
- [ ] 7.4 Document Claude credential rotation, SDK upgrade checks, fallback activation, session failure recovery, and rollback to OpenGame.

## 8. V2 Final Acceptance

- [ ] 8.1 Complete a Claude Runtime idea → GDD confirm → GameSpec confirm → asset accept → Candidate → PASS → preview journey.
- [ ] 8.2 Complete a Claude Runtime incremental modification that publishes a new Version without changing the user workflow.
- [ ] 8.3 Complete a deliberate FAIL → CodingAgent repair → TestAgent retest → PASS journey with full traceability.
- [ ] 8.4 Verify every sampled V2 run links AgentSessions, policies, tools, Candidate attempts, TestReports, and final Version or failure outcome.
- [ ] 8.5 Confirm OpenGame still completes the V1 acceptance suite and record the final parity/benchmark review.
