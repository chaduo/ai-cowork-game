## Why

Platform V1 must establish a working, measurable vertical slice before the project invests in its final Claude
Agent Runtime. OpenGame provides the first runtime implementation and a benchmark for the shared workflow,
Phaser domain behavior, isolation, testing, and safe version publication.

## What Changes

- Introduce a deterministic FastAPI workflow from confirmed GameSpec through coding, Candidate creation,
  build, structured playtest, and immutable Version publication.
- Introduce a provider-neutral GameAgent Runtime contract with OpenGameAdapter as the first implementation.
- Separate mutable/failable Candidates from published Git-backed Versions.
- Normalize OpenGame process output into platform RunEvents and persist run/workspace/candidate relationships.
- Protect the current playable Version when generation, build, test, cancellation, or retry fails.
- Capture repeatable OpenGame baseline metrics for later comparison with Platform V2.
- Non-goals: Claude Agent SDK integration, multiple domain Agent profiles, LLM-driven orchestration,
  multi-user support, multiple game templates, and runtime LLM NPC behavior.

## Capabilities

### New Capabilities

- `game-creation-workflow`: Human-gated idea, GDD, GameSpec, asset, coding, test, preview, and modification flow.
- `game-agent-runtime`: Provider-neutral runtime behavior plus the V1 OpenGameAdapter baseline.
- `candidate-version-lifecycle`: Candidate build/test/failure semantics and PASS-only Version publication.
- `run-observability`: Normalized events, cancellation, retry, isolation, and benchmark evidence.

### Modified Capabilities

None. This is the first OpenSpec baseline.

## Impact

- Affects the FastAPI workflow, SQLite schema, runtime adapter, isolated runner, Git repository service,
  Phaser template tests, SSE contract, Vue review/status/history views, and deployment configuration.
- Adds OpenGame CLI as a pinned V1 dependency via a `vendor/opengame` git submodule pointing at
  `https://github.com/CodingZY/OpenGame` commit `c54307e` (`opengame` v0.6.0); the main repo stores only the
  submodule pointer, never the OpenGame source. The previously-attached `test/agent-game-forge` submodule is
  removed — it was mislabeled as "OpenGame" but is an unrelated project (0x0funky's Agent Game Forge daemon)
  and not the Adapter target. See `docs/development/c08-opengame-spike/` for the resolved version, non-interactive
  invocation, and stream-json output contract.
- Establishes contracts that Platform V2 must reuse; V2 implementation must not begin by bypassing or
  replacing these publication and safety gates.
