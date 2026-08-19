# Playable Asset Gallery Design

## Goal

Replace the mock Assets workspace with a read-only inventory of real image, audio, and font files from the current immutable Playable Version. Images must render as actual thumbnails. Missing assets must produce an honest empty state.

This is the first slice of the V1 Assets Workspace. It does not add generation, upload, replacement, drafts, Diff, Apply, or Discard.

## Current Gap

- `AssetGalleryReadOnly.vue` synthesizes cards from project and NPC names and always uses `/farm-game-preview.png`.
- Build artifacts are addressed by an entry file such as `dist/index.html`.
- Promote currently records one entry file as `playable/index.html`; sibling image, audio, font, CSS, and JavaScript files are not checkpointed.
- Playable preview and asset access therefore still depend on the mutable run workspace.

The gallery cannot be trustworthy until Promote checkpoints the complete web output rooted at the entry file's parent directory.

## Chosen Architecture

### Immutable Web Output Snapshot

At Promote, the platform resolves the Candidate entry file inside its recorded run workspace. The entry file's parent directory is the web output root. The platform walks that directory without following symlinks and creates a clean Git checkpoint under `playable/`.

For example:

```text
run workspace/dist/index.html       -> playable/index.html
run workspace/dist/assets/hero.png  -> playable/assets/hero.png
run workspace/dist/audio/theme.ogg  -> playable/audio/theme.ogg
```

The snapshot accepts browser runtime files and asset files only:

- Runtime: `.html`, `.css`, `.js`, `.mjs`, `.json`, `.wasm`
- Images: `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.svg`
- Audio: `.mp3`, `.ogg`, `.wav`, `.m4a`, `.aac`, `.flac`
- Fonts: `.woff`, `.woff2`, `.ttf`, `.otf`

Hidden files, protected credential names, source maps, and unsupported files are excluded. Any symlink, resolved path escape, protected file, secret-bearing text file, missing entry file, more than 500 accepted files, a file larger than 20 MiB, or a snapshot larger than 100 MiB rejects Promote without changing the current Playable pointer.

The Promote API uses `CheckpointService` so the Git commit and checksum come from trusted server-side content. The existing request shape remains compatible, but a client-provided Git commit is not content truth.

### Git Inventory

`ProjectGitService` gains a read-only tree listing operation scoped to a project and commit. The operation returns normalized file paths and byte sizes without checking out the repository.

The asset service filters that immutable listing to files below `playable/` with supported image, audio, and font extensions. It derives a fixed MIME type from the extension and never trusts uploaded metadata.

### HTTP API

Two endpoints are added:

```text
GET /api/v1/projects/{project_id}/playable-versions/{version_id}/assets
GET /api/v1/projects/{project_id}/playable-versions/{version_id}/assets/content?path={relative_path}
```

The inventory returns:

```json
{
  "version_id": "...",
  "git_commit": "...",
  "assets": [
    {
      "path": "assets/hero.png",
      "name": "hero.png",
      "kind": "image",
      "mime_type": "image/png",
      "size_bytes": 1234,
      "content_url": "/api/v1/.../assets/content?path=assets%2Fhero.png"
    }
  ]
}
```

Both endpoints verify that the Project and Playable Version match. Content paths are relative to `playable/`, normalized by the Git content policy, and restricted to inventory-supported extensions. A path cannot select another project, commit, top-level directory, or disk file.

Asset responses use `X-Content-Type-Options: nosniff`, an immutable ETag based on commit and path, and long-lived immutable caching. SVG responses also use a restrictive Content Security Policy. The frontend renders SVG only through `<img>`, never injects SVG markup into the DOM.

### Frontend Workspace

The Assets tab requests the current Playable Version's inventory when a real backend project and Playable Version exist.

The workspace has four explicit states:

- Loading: stable skeleton tiles.
- Ready: grouped Images, Audio, and Fonts sections.
- Empty: explains that this Playable contains no independent asset files.
- Error: shows a concise error and a retry command.

Image cards use the immutable content URL in `<img>` and preserve aspect ratio with `object-fit: contain`. GIF remains animated. Clicking an image opens a focused preview dialog with filename, path, format, and size. Audio files use native controls. Font files show metadata only in this slice.

The mock `/farm-game-preview.png` cards and synthetic NPC asset names are removed from the Playable Assets path.

## Legacy Behavior

Existing Playable Versions whose checkpoint contains only `playable/index.html` return an empty asset list. The platform does not infer Canvas objects, parse Base64 data URLs, or claim embedded code is a separate asset.

Existing versions without a resolvable server-side Git checkpoint return a typed `playable_assets_unavailable` error. They do not fall back to mutable run workspaces.

## Failure And Transaction Behavior

- Snapshot validation happens before the lifecycle Promote transition.
- A snapshot policy failure leaves the Candidate and current Playable unchanged.
- Git checkpoint creation and SQLite Promote are coordinated by `CheckpointService`; API failures roll back SQLite state and never accept the caller's commit as provenance.
- Inventory failure does not affect preview, Build, Candidate, Human Review, or Promote state.
- A broken individual image produces a card-level unavailable state while other assets remain visible.

## Testing

Backend tests cover:

- Recursive snapshot of an entry file plus PNG, SVG, GIF, audio, font, CSS, and JavaScript siblings.
- Stable Git listing and content reads after deleting the run workspace.
- Rejection of symlinks, traversal, protected files, file-count limit, per-file limit, and total-size limit.
- Project/version isolation, unsupported path rejection, MIME types, cache headers, and SVG policy.
- Legacy `index.html`-only empty inventory.

Frontend contract and build tests cover:

- API response mapping and encoded content URLs.
- Loading, populated, empty, error, retry, image preview, audio, and font states.
- Removal of mock asset generation.
- Production typecheck and build.

## Acceptance

1. Promote a fixture containing real PNG, SVG, GIF, audio, and font files.
2. Open the current Playable's Assets tab and see the real images as thumbnails.
3. Delete the source run workspace and restart the backend.
4. Confirm inventory and content still load from the immutable Playable commit.
5. Confirm a legacy HTML-only Playable shows the honest empty state.
6. Confirm cross-project and unsafe asset paths are rejected.

