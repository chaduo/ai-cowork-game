# Resource Review Workspace v3 Implementation Plan

**Goal:** Align the existing Resource Review prototype with the approved
two-column, Chinese-first reference interaction.

**Architecture:** Keep the existing screen and component boundaries. The screen
owns deterministic candidate status and navigation; the detail component owns
metadata editing; the preview component renders type-specific evidence.

**Tech Stack:** Vue 3, TypeScript, Lucide Vue, existing global CSS and static
farm preview asset.

## Tasks

1. Update fixtures so names, descriptions, boundaries, and configurable fields
   are Chinese-first and match the approved resource concepts.
2. Keep the Workspace header, move `返回工作区` into the left rail, and retain
   the two-column layout at every review state.
3. Replace automatic next-item selection with Undo and explicit Next actions.
4. Reorder detail content to the required always-expanded information sequence.
5. Render concrete gameplay snapshots, the UI itself, and visual asset
   thumbnails for the three resource types.
6. Make the Human Gate a sticky/fixed bottom row within the center pane.
7. Replace the standalone completion screen with a lightweight inline banner.
8. Run `npm run build` and browser-verify the complete interaction path at
   desktop and narrow viewport sizes.
