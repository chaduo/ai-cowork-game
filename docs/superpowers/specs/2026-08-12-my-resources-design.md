# 我的资源 Design

## Scope

Add a cross-project `我的资源` experience to the current Vue prototype. It is
the creator's accumulated reusable work, not a marketplace, file manager, or
administration surface. Version one supports Gallery, search, category filters,
saved-resource detail, and metadata editing only.

## Navigation

- Add `Projects` and `我的资源` to the existing global headers.
- `我的资源` is a top-level App view, alongside Projects and Workspace.
- Keep the current local view switching in `App.vue`; do not add Vue Router.
- Gallery and detail share the same top-level resource page. Detail returns to
  Gallery without losing search or category state.

## Shared Prototype State

- `App.vue` owns the saved-resource array for the page lifecycle.
- `MyResources.vue` owns only query, category, and selected detail state.
- Resource Review results are merged into the saved-resource array when the
  user returns from Review.
- Detail metadata edits emit to `App.vue`, which updates name and description.
  Leaving and reopening `我的资源` therefore preserves the edits.
- No Pinia, backend, Resource API, LLM call, or persistent storage is added.

## Gallery

The page opens with `我的资源`, the provided explanation, a search field, and
four categories: 全部、玩法、UI、美术. Cards contain only a real preview,
name, type, one-line content summary, and source project.

Preview language stays specific to each resource:

- Gameplay shows a compact crop of the current farm game with Lucy's request,
  visible favor feedback, and NPC interaction.
- UI shows the heart UI itself over a muted game scene.
- Visual shows a small material board with panel, button, toolbar, and dialogue
  samples.

## Shared Detail Structure

Extract a shared `ResourceDetailContent` component used by both Review and
saved-resource detail. It renders title, type, description, definition, AI reuse
reason, `ResourcePreview`, content boundaries, configurable fields, and
provenance using the existing Resource Review styles.

Review supplies decision actions and uses `会一起保存 / 不会一起保存`.
Saved-resource detail supplies only `编辑信息` and uses `资源内容 / 包含内容 /
不包含`. The metadata editor remains a shared component so edit behavior and
copy stay consistent.

## Visual Direction

Use the established canvas `#f2f5f3`, white surfaces `#ffffff`, ink `#17211f`,
accent blue `#176fa6`, verified green `#16765e`, and existing Chinese body,
display, and mono font roles. Cards use the current 6px radius and quiet border
rather than marketplace-style elevation. The signature element is the varied
preview band: each card visibly carries a piece of the original game rather than
an abstract category icon.

## Empty and Responsive States

- Search and category filters compose; show a lightweight directional empty
  state when no resource matches.
- Use three columns on wide screens, two on medium screens, and one on mobile.
- Keep navigation, search, filters, cards, detail, and edit dialog keyboard
  accessible with visible focus.

## Verification

Run the existing production build, then browser-check search, each category,
empty results, Gallery to Detail and back, all three previews, editing, Gallery
sync after editing, Review save to Gallery, page re-entry, and desktop/mobile
layout.
