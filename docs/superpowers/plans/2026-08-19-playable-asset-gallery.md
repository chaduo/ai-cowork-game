# Playable Asset Gallery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist a Candidate's complete browser output at Promote and show the current Playable's real image, audio, and font files in a read-only Assets workspace.

**Architecture:** `CheckpointService` validates and commits the Candidate entry directory as an immutable `playable/` tree before advancing the lifecycle gate. `ProjectGitService` exposes commit-tree listing, while a focused Playable asset service and API provide an allowlisted inventory and immutable content bytes. Vue loads that inventory for the current remote Playable and renders real image thumbnails, audio controls, font metadata, and honest loading/empty/error states.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, Dulwich, pytest, Vue 3, TypeScript, Vite, Node test runner.

## Global Constraints

- FastAPI remains the sole owner of Promote and all Human Gates.
- The current Playable pointer MUST NOT change when snapshot validation or checkpoint creation fails.
- Snapshot limits are 500 accepted files, 20 MiB per file, and 100 MiB total.
- Supported runtime extensions are `.html`, `.css`, `.js`, `.mjs`, `.json`, and `.wasm`.
- Supported image extensions are `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, and `.svg`.
- Supported audio extensions are `.mp3`, `.ogg`, `.wav`, `.m4a`, `.aac`, and `.flac`.
- Supported font extensions are `.woff`, `.woff2`, `.ttf`, and `.otf`.
- Asset content MUST come from the Playable Version's immutable Git commit, never a mutable run workspace.
- The first slice is read-only and MUST NOT add generation, upload, replacement, drafts, Diff, Apply, or Discard.

---

### Task 1: Immutable Playable Output Snapshot

**Files:**
- Modify: `backend/app/services/project_git.py`
- Modify: `backend/app/services/checkpoint.py`
- Modify: `backend/tests/test_c20_project_git.py`
- Modify: `backend/tests/test_c20_checkpoint.py`

**Interfaces:**
- Produces: `GitFileEntry(path: str, size_bytes: int)`.
- Produces: `ProjectGitService.list_files(project_id: str, sha: str, prefix: str | None = None) -> list[GitFileEntry]`.
- Produces: `CheckpointService.collect_candidate_output(candidate: BuildCandidate) -> dict[str, bytes]` as an internal snapshot boundary.
- Consumes: persisted `Run.workspace_path`, `BuildCandidate.artifact_path`, and existing `ProjectGitService.commit` content policy.

- [ ] **Step 1: Add failing Git tree-listing tests**

Add tests that commit nested files and assert deterministic normalized output:

```python
entries = git.list_files(project_id, sha, prefix="playable/")
assert [(item.path, item.size_bytes) for item in entries] == [
    ("playable/assets/hero.png", 3),
    ("playable/index.html", 4),
]
```

Also assert an unknown commit raises `ValueError` and an invalid prefix raises `ContentPolicyError`.

- [ ] **Step 2: Run the focused Git tests and confirm RED**

Run: `/Users/zhaozhuo/workspace/explore/ai-cowork-game/backend/.venv/bin/pytest -q backend/tests/test_c20_project_git.py`

Expected: FAIL because `GitFileEntry` and `list_files` do not exist.

- [ ] **Step 3: Implement recursive immutable tree listing**

Add the immutable value type and a Dulwich tree walk:

```python
@dataclass(frozen=True)
class GitFileEntry:
    path: str
    size_bytes: int

def list_files(self, project_id: str, sha: str, prefix: str | None = None) -> list[GitFileEntry]:
    ...
```

Validate a supplied prefix with `_validate_member`, recurse only through `Tree` objects, record only `Blob` entries, normalize paths with `/`, filter by prefix, and return entries sorted by path.

- [ ] **Step 4: Add failing recursive Promote snapshot tests**

Extend `_candidate_with_artifact` to create `dist/index.html` and sibling files. Assert Promote commits:

```python
assert git.read_file(project_id, version.git_commit, "playable/index.html") == html
assert git.read_file(project_id, version.git_commit, "playable/assets/hero.png") == png
assert git.read_file(project_id, version.git_commit, "playable/audio/theme.ogg") == ogg
```

Delete the workspace after Promote and assert the same reads still pass. Add isolated tests for symlink rejection, more than 500 accepted files, a file over 20 MiB, a total over 100 MiB using patched constants, protected filenames, and missing entry files. In every rejection case assert `project.current_playable_version_id is None` and `candidate.status == "succeeded"`.

- [ ] **Step 5: Run the focused checkpoint tests and confirm RED**

Run: `/Users/zhaozhuo/workspace/explore/ai-cowork-game/backend/.venv/bin/pytest -q backend/tests/test_c20_checkpoint.py`

Expected: sibling file assertions fail because only `index.html` is committed; policy cases fail because the lifecycle currently advances before snapshot validation.

- [ ] **Step 6: Implement bounded output collection before Promote**

Define extension sets and exact limits in `checkpoint.py`. Resolve the Candidate entry with `WorkspaceManager.validate_member`, use the entry parent as output root, walk without following symlinks, reject any symlink encountered, skip hidden and unsupported regular files, and enforce count/size limits before reading all bytes.

Map every accepted relative path to `playable/{relative_path}`. Require the mapped entry file to be `playable/index.html`. Call `ProjectGitService.commit` before `ProjectLifecycleService.promote_candidate`, then pass the real commit and an SHA-256 checksum of `playable/index.html` into the lifecycle gate. A content commit without a SQLite reference is harmless if the subsequent lifecycle gate rejects, while advancing SQLite before a failed snapshot is forbidden.

- [ ] **Step 7: Run Task 1 tests and commit**

Run:

```bash
/Users/zhaozhuo/workspace/explore/ai-cowork-game/backend/.venv/bin/pytest -q backend/tests/test_c20_project_git.py backend/tests/test_c20_checkpoint.py
```

Expected: PASS.

Commit:

```bash
git add backend/app/services/project_git.py backend/app/services/checkpoint.py backend/tests/test_c20_project_git.py backend/tests/test_c20_checkpoint.py
git commit -m "feat: checkpoint complete playable output"
```

---

### Task 2: Immutable Playable Assets API

**Files:**
- Create: `backend/app/services/playable_assets.py`
- Modify: `backend/app/api/playables.py`
- Modify: `backend/tests/test_c14_api.py`
- Create: `backend/tests/test_playable_assets_api.py`

**Interfaces:**
- Produces: `PlayableAsset(path: str, name: str, kind: Literal["image", "audio", "font"], mime_type: str, size_bytes: int)`.
- Produces: `PlayableAssetService.list_assets(version: PlayableVersion) -> list[PlayableAsset]`.
- Produces: `PlayableAssetService.read_asset(version: PlayableVersion, relative_path: str) -> tuple[PlayableAsset, bytes]`.
- Produces: `GET /api/v1/projects/{project_id}/playable-versions/{version_id}/assets`.
- Produces: `GET /api/v1/projects/{project_id}/playable-versions/{version_id}/assets/content?path=...`.
- Consumes: `request.app.state.project_git`, `PlayableVersion.git_commit`, and Task 1 `list_files`/`read_file`.

- [ ] **Step 1: Write failing API inventory and content tests**

Create a real project Git fixture containing `playable/index.html`, two images, audio, font, CSS, and an unsupported file. Seed a Playable Version with that real commit and assert:

```python
inventory = client.get(f"/api/v1/projects/{project_id}/playable-versions/{version_id}/assets")
assert inventory.status_code == 200
assert [item["kind"] for item in inventory.json()["assets"]] == ["image", "image", "audio", "font"]

content = client.get(
    f"/api/v1/projects/{project_id}/playable-versions/{version_id}/assets/content",
    params={"path": "assets/hero.png"},
)
assert content.content == png
assert content.headers["content-type"] == "image/png"
assert content.headers["x-content-type-options"] == "nosniff"
assert "immutable" in content.headers["cache-control"]
```

Cover HTML-only empty inventory, SVG Content Security Policy, path traversal, unsupported extensions, mismatched project/version, missing commit, missing blob, and another project's path.

- [ ] **Step 2: Run the new API tests and confirm RED**

Run: `/Users/zhaozhuo/workspace/explore/ai-cowork-game/backend/.venv/bin/pytest -q backend/tests/test_playable_assets_api.py`

Expected: 404 because the routes do not exist.

- [ ] **Step 3: Implement the focused asset service**

Use fixed extension maps:

```python
IMAGE_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
}
```

Add equivalent audio and font maps. Inventory only `playable/` entries, expose paths relative to that prefix, and reject empty, absolute, dot-segment, backslash, URL-like, or unsupported paths before calling `read_file`.

- [ ] **Step 4: Add the API routes and trusted Promote wiring**

Add Pydantic inventory response models and return `Response(content=bytes, media_type=asset.mime_type)` for content. Set:

```python
headers = {
    "Cache-Control": "public, max-age=31536000, immutable",
    "ETag": f'"{version.git_commit}:{sha256(path.encode()).hexdigest()}"',
    "X-Content-Type-Options": "nosniff",
}
```

For SVG, also set `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; sandbox`.

Change the Promote endpoint to construct `CheckpointService(session, git=request.app.state.project_git)` and return its version. Keep accepting the existing request body for frontend compatibility, but do not pass its commit into lifecycle state.

Update `test_c14_api.py` to seed a real run workspace and injected `ProjectGitService`; assert the returned commit is a real server-generated SHA and remains idempotent.

- [ ] **Step 5: Run Task 2 tests and commit**

Run:

```bash
/Users/zhaozhuo/workspace/explore/ai-cowork-game/backend/.venv/bin/pytest -q backend/tests/test_playable_assets_api.py backend/tests/test_c14_api.py backend/tests/test_c20_checkpoint.py
```

Expected: PASS.

Commit:

```bash
git add backend/app/services/playable_assets.py backend/app/api/playables.py backend/tests/test_playable_assets_api.py backend/tests/test_c14_api.py
git commit -m "feat: expose immutable playable assets"
```

---

### Task 3: Real Read-Only Assets Workspace

**Files:**
- Create: `frontend/src/contracts/playableAssets.ts`
- Create: `frontend/tests/playableAssets.test.mjs`
- Modify: `frontend/src/api/client.ts`
- Rewrite: `frontend/src/components/workspace/AssetGalleryReadOnly.vue`
- Modify: `frontend/src/screens/K02ProjectWorkspace.vue`
- Modify: `frontend/src/style.css`

**Interfaces:**
- Produces: `PlayableAssetResponse` and `PlayableAssetInventoryResponse` API types.
- Produces: `listPlayableAssets(projectId: string, versionId: string) -> Promise<PlayableAssetInventoryResponse>`.
- Produces: `groupPlayableAssets(assets: PlayableAssetResponse[]) -> { images; audio; fonts }`.
- Consumes: `session.backendProjectId` and `session.remoteBuild?.playableVersion?.version_id`.

- [ ] **Step 1: Write failing frontend contract tests**

Add tests for stable grouping, case-insensitive display names, byte-size formatting, and safe API URL preservation:

```javascript
const grouped = groupPlayableAssets([
  { path: 'assets/hero.png', name: 'hero.png', kind: 'image', mime_type: 'image/png', size_bytes: 1024, content_url: '/api/v1/content?path=assets%2Fhero.png' },
  { path: 'audio/theme.ogg', name: 'theme.ogg', kind: 'audio', mime_type: 'audio/ogg', size_bytes: 2048, content_url: '/api/v1/content?path=audio%2Ftheme.ogg' },
])
assert.equal(grouped.images[0].content_url.includes('%2F'), true)
assert.equal(formatAssetSize(1024), '1 KB')
```

- [ ] **Step 2: Run the contract test and confirm RED**

Run: `node --test frontend/tests/playableAssets.test.mjs`

Expected: module-not-found for `playableAssets.ts`.

- [ ] **Step 3: Implement API types and pure view mapping**

Add exact response interfaces in `client.ts`, implement the GET call with encoded project/version ids, and add pure grouping/formatting helpers in `playableAssets.ts`. Do not reconstruct content URLs on the client; use the server-provided immutable URL.

- [ ] **Step 4: Rewrite the gallery with explicit states**

The component accepts:

```typescript
const props = defineProps<{
  projectId: string | null
  versionId: string | null
  projectTitle: string
}>()
```

On mount and whenever both ids change, load the inventory with a monotonic request token so stale responses cannot replace a newer version. Render:

- Loading skeletons with stable tile dimensions.
- Images using `<img :src="asset.content_url" :alt="asset.name">` and a card-level error fallback.
- A native `<audio controls preload="metadata">` per audio file.
- Font file metadata rows.
- An empty state when all groups are empty.
- An inline error with a retry button.
- A `dialog`-style image preview overlay closed by its icon button, backdrop, or Escape.

Remove synthetic Character/Environment/Gameplay Object groups and every `/farm-game-preview.png` reference from this component.

- [ ] **Step 5: Wire the current remote Playable and responsive styling**

Pass `session.backendProjectId` and `session.remoteBuild?.playableVersion?.version_id` from `K02ProjectWorkspace.vue`. Keep the Assets tab available during existing Build/Change phases, but show the honest no-Playable state until a version is promoted.

Use the existing restrained workspace palette. Image tiles use a fixed `aspect-ratio: 4 / 3`, `object-fit: contain`, and at most four columns. Collapse to two and one column at existing tablet/mobile breakpoints. Do not nest cards or introduce decorative gradients.

- [ ] **Step 6: Run Task 3 tests and build, then commit**

Run:

```bash
node --test frontend/tests/*.test.mjs
npm run build
```

Expected: all contract tests pass and Vite production build exits 0.

Commit:

```bash
git add frontend/src/contracts/playableAssets.ts frontend/tests/playableAssets.test.mjs frontend/src/api/client.ts frontend/src/components/workspace/AssetGalleryReadOnly.vue frontend/src/screens/K02ProjectWorkspace.vue frontend/src/style.css
git commit -m "feat: display real playable assets"
```

---

### Task 4: Full Regression And Acceptance Evidence

**Files:**
- Modify only if a regression test exposes a defect in Task 1-3 files.

**Interfaces:**
- Consumes all Task 1-3 interfaces.
- Produces verification evidence for the branch handoff.

- [ ] **Step 1: Run the complete backend suite with real browser permission**

Run: `/Users/zhaozhuo/workspace/explore/ai-cowork-game/backend/.venv/bin/pytest -q backend/tests`

Expected: 0 failures; existing Playwright skips remain environment-dependent.

- [ ] **Step 2: Run all frontend contracts and production build**

Run:

```bash
node --test frontend/tests/*.test.mjs
npm run build
```

Expected: 0 test failures and Vite exits 0.

- [ ] **Step 3: Verify repository scope and diff quality**

Run:

```bash
git diff --check
git status --short
git log --oneline --decorate -5
```

Expected: no whitespace errors; only intentional generated test data may remain untracked and MUST NOT be committed.

- [ ] **Step 4: Review acceptance requirements against evidence**

Confirm the tests prove recursive image/audio/font snapshot, thumbnail content delivery, post-workspace-deletion reads, legacy empty state, and unsafe/cross-project rejection. Record any unverified manual browser behavior explicitly instead of claiming it passed.
