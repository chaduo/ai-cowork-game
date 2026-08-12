# Build Workspace Prototype Design

## Goal

Extend the existing AI Cowork Game prototype from an approved GameSpec to the
first validated playable version. The prototype must make progress,
traceability, automatic repair, and the Working Build to Playable transition
understandable without exposing implementation noise.

The flow ends at `Playable v1 · Stable`. Iteration suggestions, natural-language
modification, version restore, real agents, real Phaser builds, and editable
assets/code remain out of scope.

## Approved Journey

```text
GameSpec Confirmed
→ Build Starting
→ Foundation
→ Core Gameplay
→ NPC & Interaction
→ Presentation
→ Progression & Goal
→ Validation 7/9
→ Auto Fix
→ Validation 9/9
→ First Playable Ready
→ Playable v1 · Stable
```

An alternate deterministic fixture enters `Build Error` during Presentation.
Retry resumes Presentation without reverting Foundation or Core Gameplay.

## Workspace Structure

The existing Project Workspace shell remains unchanged:

```text
┌──────────────────────────────────────────────────────────────┐
│ Project + DESIGN ✓  GAMESPEC ✓  BUILD ●  PLAYABLE ○       │
├───────────────────┬──────────────────────────────────────────┤
│ Cowork AI         │ BUILD | PREVIEW | ASSETS | CODE         │
│ stage narrative   │                                          │
│ meaningful events │ milestone ledger + current detail        │
│ contextual input  │                                          │
└───────────────────┴──────────────────────────────────────────┘
```

The left panel explains what was completed, what is happening, and why it
matters. The right panel is the current artifact. It does not become a terminal,
agent-thought viewer, CI dashboard, or file-change feed.

## Visual Direction

- Reuse the approved Verified Workshop tokens, typography, square geometry,
  compact spacing, hairline dividers, and restrained blue accent.
- Keep system progress blue and verified results green. Human confirmation
  remains visually distinct from system validation.
- Use a full-width build ledger with one vertical trace line as the signature
  element. Milestone rows move from hollow to active to verified along this
  line, making the game appear to grow without decorative animation.
- Use no gradients, glow, excessive cards, percent progress, or terminal styling.
- The only strong transition is the final promotion from Working Build to
  Playable, expressed through the lifecycle rail, validation seal, and Preview.

## Artifact Tabs

### Build

The default tab during development. It contains:

- First Playable identity and current phase.
- Six milestone rows: Foundation, Core Gameplay, NPC & Interaction,
  Presentation, Progression & Goal, Validation.
- A focused detail region for the active milestone.
- Trace labels connecting relevant work to the confirmed GameSpec.
- Progressive disclosure for functional details and execution details.

Completed milestones stay visible and never regress after a recoverable error.

### Preview

- Before Core Gameplay: unavailable state, `Preparing runnable build…`.
- After Core Gameplay: a mock game image labelled `Working Build`, with completed
  and still-building capabilities.
- After Validation: automatically selected and labelled `Playable v1 · Stable`.

The image is a static mock. It must never imply that a real Phaser runtime exists.

### Assets

Read-only grouped gallery for characters, environment, animals, crops, and
audio. Items reveal whether they are built-in or generated mock assets. No
editing or regeneration controls are provided.

### Code

Read-only project file outline with a short explanation that source editing
becomes available after the first playable. Monaco is not loaded in this stage.

## Cowork AI Activity

The default activity level shows milestone-level outcomes. A disclosure reveals
functional details; a second `查看执行详情` disclosure reveals a small mock list of
file operations. The interface never labels this as thoughts or reasoning.

During automatic repair, the AI states the failed observable behavior, what it
is repairing, and that completed work is being preserved.

The composer remains present for workspace continuity but is disabled during
the first build with the explanation `首个版本完成后可以继续修改`.

## Traceability

The same capability must use recognizable wording in all three stages:

```text
GameSpec: Lucy 可以提供委托
Build:    NPC & Interaction → Request System
Test:     Lucy can provide a request
```

Each validation check references its source section. This is a product-level
trust mechanism, not technical metadata.

## State Model

```text
spec_confirmed
→ build_starting
→ building_foundation
→ building_core
→ building_interaction
→ building_presentation
→ building_progression
→ validating
→ auto_fixing
→ validating_complete
→ playable_ready
```

`build_error` can replace `building_presentation`. Retry returns to that phase;
completed milestones retain their state. All transitions use deterministic
timers and fixed fixtures.

## Timing

Normal milestone transitions last 700–900 ms. Validation pauses long enough to
show 7/9, the failed inheritance trigger, automatic repair, and 9/9. Reduced
motion removes animated movement but preserves state timing and labels.

Direct prototype query parameters may expose review states and the error fixture,
but no prototype controller appears in the product UI.

## Components

- `BuildWorkspaceView`: selects the active build artifact.
- `BuildMilestoneList`: ordered ledger and current milestone.
- `BuildMilestoneDetail`: human-readable capabilities and trace source.
- `ValidationPanel`: Definition of Playable checks and counts.
- `WorkingPreview`: mock preview with Working/Playable status.
- `AssetGalleryReadOnly`: grouped immutable assets.
- `CodeReadOnlyState`: bounded code placeholder.
- `BuildCoworkPanel`: build-specific stage narrative and activity disclosure.

The existing workspace header, lifecycle rail, tabs, and project identity are
reused. Build state is owned by the workspace screen and passed down as props.

## Failure UX

The deterministic error fixture fails Presentation because the Lucy asset did
not complete. The UI explains the exact failure, confirms that completed game
logic remains intact, and offers `重新尝试此阶段`. Retry does not restart the build.

Validation failures that are automatically repairable do not show a blocking
error action. They remain part of the build narrative.

## Acceptance

- The existing K01, Creative Kickoff, and GameSpec review remain functional.
- Confirming GameSpec enters the Build tab in the same workspace.
- Six milestones progress deterministically and are understandable without logs.
- Preview becomes a clearly labelled Working Build after Core Gameplay.
- Assets and Code are honest, read-only states.
- Validation visibly derives from Definition of Playable.
- The 7/9 failure, automatic repair, and 9/9 result are observable.
- A Presentation error preserves completed milestones and retries locally.
- Completion updates the lifecycle to Playable and opens `Playable v1 · Stable`.
- The browser reports no blocking console errors at the target desktop viewport.
- The prototype stops at the first stable playable and exposes no iteration loop.

## Self-review

- No placeholders or open implementation decisions remain.
- The scope ends consistently at the first stable playable.
- Candidate terminology is intentionally absent from the primary UI.
- Human confirmation and system validation remain separate concepts.
- Every failure path identifies the failed stage and recovery action.
