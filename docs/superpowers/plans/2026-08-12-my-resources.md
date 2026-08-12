# 我的资源 Implementation Plan

**Goal:** Add a connected saved-resource Gallery and Detail experience to the
existing AI Cowork Game prototype.

**Architecture:** `App.vue` owns saved resources and top-level view state.
`MyResources.vue` owns local browsing state. Review and saved detail share
resource data, previews, detail content, and metadata editing while retaining
separate action surfaces.

**Tech Stack:** Vue 3, TypeScript, Lucide Vue, existing CSS tokens and static
game preview asset.

## Tasks

1. Extend resource fixtures with saved-library fixtures and concise card copy.
2. Add shared `ResourceMetadataEditor` and `ResourceDetailContent` components,
   then migrate Resource Review to them without changing its decisions.
3. Add `ResourceGalleryCard` with compact type-specific preview variants.
4. Add `SavedResourceDetail` with shared detail body and edit-only action.
5. Add `MyResources` with local query, category, selection, and empty state.
6. Promote saved-resource data and top-level navigation state to `App.vue`.
7. Add Projects / 我的资源 entry points to Projects, Workspace, and Review.
8. Add responsive styles using the existing design tokens and component shapes.
9. Run `npm run build` and browser-verify every requested interaction, state
   connection, edit synchronization, and responsive layout.
