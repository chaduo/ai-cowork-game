# Dynamic GDD Brainstorming Design

**Status:** Approved for implementation
**Scope:** C05 corrective: replace the real-project fixed kickoff questionnaire with a provider-neutral, recoverable Game Design Brainstorm loop.

## Goal

Make Game Design help a creator clarify the most important missing decision in their own Idea. Each turn produces one question, a small set of contextual choices, or a free-text path; the resulting GDD draft and readiness state are persisted before the next turn. Confirm GDD remains a separate FastAPI-owned Human Gate.

## Current Gap

The current real Project flow resolves `farm`, `coffee-shop`, or `generic` fixtures in Vue and reads fixed questions from `kickoffFixtures.ts`. Persistence and confirmation are real, but the questioning layer does not inspect the evolving design state.

## Design

### Provider-neutral planner boundary

Add a `GameDesignPlanner` protocol with one operation:

```text
plan_turn(project_id, draft, user_input) -> BrainstormTurn
```

`BrainstormTurn` contains the updated `CreatorGameDesignDraft` and either the next `BrainstormQuestion` or a ready state. The planner never confirms GDD, changes Project stage, starts Build, or writes Git checkpoints.

Production `OpenAICompatibleGameDesignPlanner` calls the configured `/chat/completions` endpoint using backend-only credentials and validates the JSON response with strict Pydantic contracts. Its system instruction requires Chinese-first creator language, one highest-priority design gap, 2-4 choices, optional free input, a minimum-buildable scope, and no provider/workflow state. If a real Project has no configured provider, the API fails closed with a structured 503; it never falls back to the old fixture questionnaire.

Tests inject `FakeGameDesignPlanner`. It is a test double, not a runtime fallback for a configured real Project. If the production provider is not configured, the API returns a structured 503 and the UI stays in the brainstorming state with an actionable error.

### Persistence and API

Extend `ClarificationState` with the current question so a refresh can resume without re-invoking the provider. Add:

```text
POST /api/v1/projects/{project_id}/design/brainstorm
```

The request carries `start`, `answer`, `free_text`, or `continue` plus the current question id and answer. The endpoint loads the latest draft, invokes the planner, saves a new GameDesign revision, and returns the normal DesignResponse plus the next question. Existing `/design`, `/design/confirm`, and revision/checkpoint behavior remain unchanged.

### Vue interaction

`CreativeKickoffModal` renders the server question when a real backend Project is present. Choice cards and the existing free-text control submit a planner turn; the modal emits the returned draft for local session synchronization. The old deterministic fixture path remains only for explicitly offline/demo sessions. The parent still owns API error display and calls Confirm GDD only after the planner reports `readiness.status = ready`.

### Design-state ownership and provenance

The persisted GDD draft is the only design truth. Summary text, the current question, and readiness details are projections of that draft and are never edited as independent truths. The draft stores decisions with provenance (`user_confirmed` or `ai_inferred`) and a stable decision id. Replacing a decision creates a new revision with a superseding reference; it does not mutate an old revision.

The planner is split into narrow responsibilities at the service boundary: a reducer applies a user answer, a finite gap policy selects the next blocking category, the provider planner proposes wording/options, a projector builds the creator-facing summary, and a deterministic readiness gate decides whether First Playable requirements are met. None of these components can Confirm GDD, change Project stage, create GameSpec, or start Build.

The gap policy is finite and ordered: core experience, player action, goal, feedback, progression, V1 scope, and completion condition. One turn may ask one blocking question. The server applies a six-turn budget and stops when all First Playable fields are covered or two consecutive turns add no new user-confirmed information. `first_playable_ready` is independent from `full_gdd_ready`; lore, exhaustive content, and polish do not block the first playable.

### Readiness

The planner can report blockers and unresolved decisions. The UI shows a light readiness summary; the server rejects Confirm GDD unless readiness is `ready` and the current revision is valid. Confirmed revisions remain immutable; editing after confirmation creates a new draft revision.

## Acceptance

1. Two unrelated Ideas receive different first questions or choices based on their content; no scenario id is required for real Projects.
2. A free-text answer is included in the next planner turn and appears in the saved GDD draft/summary.
3. Refreshing during clarification restores the persisted question, decisions, and readiness without losing the turn.
4. A not-ready draft cannot confirm; a ready draft can confirm exactly once and receives a GDD Git checkpoint.
5. Provider errors are visible and do not silently start GameSpec or Build.
6. A real Project without provider credentials returns a structured configuration error and never renders a fixture question.
7. The planner contract can later be implemented by Claude SDK, Pi Agent, or another provider without changing Vue or FastAPI gate ownership.

## Out of Scope

- Automatic Confirm GDD or GameSpec.
- Provider-specific commands in CreatorGameDesignDraft.
- OpenGame build execution, asset generation, or a workflow engine.
- A standalone full-page GDD editor; Final GDD Review remains the next UI refinement.
