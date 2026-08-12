# GameSpec Resource Reuse Implementation Plan

**Goal:** Add contextual saved-resource reuse to the existing GameSpec review
flow without adding a new Workspace or changing the confirmation/Build state
machine.

**Architecture:** `App.vue` passes the existing saved relationship resource into
the same `K02ProjectWorkspace`. Workspace owns recommendation/drawer/use state
and the immutable relationship snapshot. `GameSpecModel` stores only final
relationship design fields, while `GameSpecDocument` renders the Section and
emits user intent.

**Tech Stack:** Vue 3, TypeScript, Lucide Vue, existing resource fixtures,
`ResourcePreview.vue`, Workspace CSS tokens, deterministic local state.

## Task 1: Relationship Content Model and Coffee Fixture

**Files:**
- Modify: `frontend/src/components/workspace/workspaceTypes.ts`
- Modify: `frontend/src/components/workspace/gameSpecFixture.ts`
- Modify: `frontend/src/App.vue`

1. Add `primaryNpcs`, `relationshipGrowth`, `favorRules`,
   `relationshipEvents`, and `requestRewards` as final-design fields under
   `GameSpecModel.characters`.
2. Populate existing farm and generic fixtures without changing their visible
   project identity.
3. Add deterministic `createResourceReuseConfirmedDesign()` and coffee-shop
   output in `createGameSpecFixture()`.
4. Route `?screen=resource-reuse` into the existing `K02ProjectWorkspace` and
   pass the saved `relationship-system` resource as a prop.
5. Run `npm run build` and verify TypeScript identifies any unpopulated fixture.

## Task 2: Inline Recommendation and Used State

**Files:**
- Create: `frontend/src/components/workspace/ResourceReuseRecommendation.vue`
- Modify: `frontend/src/components/workspace/GameSpecDocument.vue`

1. Add a focused recommendation component with resource/source/reason copy,
   Ignore, View, and Use events.
2. Render it only inside the characters Section when state is `recommended`.
3. Render exactly one aligned used-state bar when state is `used` with View and
   Cancel events.
4. Render explicit coffee relationship fields below the status/recommendation.
5. Keep the existing Section adjustment button and emit its current context.

## Task 3: Reuse-Specific Resource Drawer

**Files:**
- Create: `frontend/src/components/workspace/ResourceReuseDrawer.vue`
- Modify: `frontend/src/components/resources/ResourcePreview.vue`

1. Build a right drawer with overlay, focusable Close control, scrollable body,
   and fixed footer actions.
2. Reuse `ResourcePreview.vue` in compact drawer mode for the three gameplay
   evidence cards.
3. Render definition, current-design fit, included capabilities only,
   configurable fields, and provenance.
4. Exclude resource extraction boundaries and project-specific excluded items.
5. Emit Close and Use events; disable Use after the resource is applied.

## Task 4: Workspace State, Apply, and Immutable Restore

**Files:**
- Modify: `frontend/src/screens/K02ProjectWorkspace.vue`

1. Add local `recommended | dismissed | used` and drawer state, guarded by the
   resource-reuse fixture and available resource.
2. Define a relationship-only snapshot type and `relationshipSnapshot` ref.
3. On first Use, deep-clone current relationship fields only when the snapshot
   is still `null`; never replace it later.
4. Apply deterministic coffee-adapted values, mark the characters Section
   updated, show light feedback, close the drawer, and do not change phase.
5. On Cancel, restore only relationship fields from the frozen snapshot and
   return state to `recommended`.
6. Wire GameSpec events and mount the drawer at Workspace level.

## Task 5: Workspace-Aligned Visual Design

**Files:**
- Modify: `frontend/src/style.css`

1. Style the contextual recommendation as a quiet blue inset inside the
   characters Section.
2. Style the single used-state bar and a short green content feedback.
3. Style explicit relationship rows to follow existing GameSpec typography and
   left alignment.
4. Style the right drawer using existing resource provenance, preview, and
   button language without nested cards.
5. Add responsive rules for narrower Workspace widths and reduced motion.

## Task 6: Verification

**Files:** none

1. Run `npm run build` for Vue TypeScript and production Vite output.
2. Browser-check default recommendation and Ignore.
3. Browser-check Drawer labels, included-only content, and provenance.
4. Use from inline and Drawer; verify coffee context changes in place and no
   Build phase starts.
5. Verify exactly one used-state bar, View after use, Cancel restore, and reuse.
6. Modify another Section, cancel reuse, and verify the unrelated edit remains.
7. Confirm GameSpec and verify the existing confirmation flow proceeds.
8. Check desktop/narrow viewport overflow and browser console errors.
