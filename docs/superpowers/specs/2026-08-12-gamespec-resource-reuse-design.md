# GameSpec Resource Reuse Design

## Goal

Integrate a deterministic saved-resource recommendation into the existing
GameSpec review flow. AI suggests the creator's saved `NPC 关系系统` directly
inside the relevant relationship Section; the creator can inspect it in a
drawer, use it to enrich the current Draft, undo the use, and continue the
existing GameSpec confirmation flow.

## Entry and Fixture

- Keep the existing `K02ProjectWorkspace` and its state machine.
- Add `?screen=resource-reuse` as a deterministic demo entry.
- The entry uses a `咖啡店故事` confirmed-design/GameSpec fixture with Emily and
  Alex as current-project NPCs.
- The recommended resource comes from the same `App.vue` `savedResources` array
  used by `我的资源`; no duplicate resource record is created in the Workspace.
- Existing `?screen=gamespec` continues to use the farm fixture.

## State Ownership

`K02ProjectWorkspace.vue` owns all reuse workflow state:

- `reuseState: recommended | dismissed | used`
- `reuseDrawerOpen: boolean`
- selected resource id/reference
- one-time relationship snapshot
- short visual-feedback state

No recommendation, dismissal, drawer, resource id, or used-state field is added
to `GameSpecModel`.

`GameSpecModel.characters` gains only explicit final-design content fields:

- `primaryNpcs`
- `relationshipGrowth`
- `favorRules`
- `relationshipEvents`
- `requestRewards`

These fields describe the current GameSpec regardless of how the content was
created and remain editable through the existing Section adjustment flow.

## Immutable Undo Boundary

Immediately before the first resource use, Workspace captures a deep-cloned,
one-time snapshot of only the NPC/relationship fields. Once created, the
snapshot is never recalculated from the adapted GameSpec, even if the creator
later modifies the adapted Section.

Cancel Use restores only those relationship fields from the immutable snapshot.
It does not replace the entire GameSpec and therefore preserves edits made to
gameplay, rules, scope, validation, or any other Section.

## Inline Recommendation

The recommendation appears once inside the `NPC 与关系` Section, near the
relationship content it can improve. It contains:

- `发现一个可能适合的已有资源`
- resource name and source project
- a plain-language explanation of why the capability matches the current Draft
- `查看资源` and `使用这个资源`
- an icon-only Ignore control with an accessible label

Ignore changes the local state to `dismissed`, hides the card for the current
Workspace lifecycle, and does not alter `我的资源`.

## Resource Drawer

The drawer overlays the current Workspace without navigation and reuses
`ResourcePreview.vue`, resource configuration data, provenance styles, and the
existing resource palette. It deliberately has reuse-specific information:

1. 这是什么
2. 为什么适合当前设计
3. 在原游戏中的表现
4. 包含内容
5. 以后可以调整
6. 来源

It never shows extraction exclusions, Lucy/farm boundary copy, candidate
language, dependency/import/package terminology, or Review actions. Footer
actions are `关闭` and `使用这个资源`; after use the primary action becomes a
disabled `已使用` state.

## Applying the Resource

Using the resource does not navigate, configure parameters, call a backend, or
start Build. It adapts the relationship Section in place while preserving the
coffee-shop context:

- Emily remains the clerk and Alex remains the regular customer.
- Relationship growth uses NPC requests and interactions.
- Favor defaults to 0-100 with key nodes 30 / 60 / 80.
- Relationship events trigger at key nodes.
- Ordinary requests grant +5 and important events grant +10.

The resource supplies a reusable relationship structure; no Lucy, farm, crop,
or strawberry task content enters the current Draft.

## Used State and Feedback

After use, the recommendation is replaced by one unified status bar aligned
with the Section body:

- `已使用 NPC 关系系统`
- `已根据当前咖啡店设计适配`
- `查看资源`
- `取消使用`

No title badge or duplicate source note is added. A short green-tinted entrance
on the status bar and Section body communicates that the Draft changed. Reduced
motion removes the transition.

Cancel Use restores the immutable relationship snapshot, removes the status
bar, and returns the recommendation to `recommended`. Reusing remains possible.

## Existing GameSpec Flow

- Existing Section adjustment remains available after use; no field is locked.
- Existing `确认 GameSpec` behavior and confirmation phase remain unchanged.
- Resource reuse changes only the current Draft and never invokes Build.
- A quiet note states this explicitly near the recommendation/status surface.

## Visual Direction

Reuse the current Workspace canvas, document typography, 4-6px control radius,
blue recommendation color, and verified green used state. The recommendation
should read as contextual AI assistance rather than a system notification. The
single signature is its transformation in the same physical location from a
blue contextual suggestion into a green applied-state bar while the content
below becomes more specific.

## Verification

Verify recommendation, dismissal, drawer contents, drawer use, inline use,
single status bar, adapted coffee-shop content, no legacy project content,
cancel restore, reuse after cancel, drawer after use, unrelated Section edits
surviving cancel, no Build on use, existing GameSpec confirmation, production
build/typecheck, console health, and responsive layout.
