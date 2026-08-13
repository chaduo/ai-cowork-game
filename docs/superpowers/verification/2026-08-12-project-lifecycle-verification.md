# Project Lifecycle Prototype Verification

## State ownership

- `frontend/src/stores/projectStore.ts` is the single in-memory business store for projects, GameSpec lifecycle phases, Playable versions, Releases, release-scoped resource batches, and the global saved resource library.
- Store timers are keyed by project id and job key. Leaving `K02ProjectWorkspace` does not cancel generation, build, change, publish, or resource-save work.
- Components retain only interaction state such as active tabs, selected sections, drawers, modals, and short visual feedback timers.
- `App.vue` owns only the surface (`projects`, `workspace`, `resources`, `review`) and demo bootstrap parsing. It does not own project or resource fixtures.
- `playableVersions[]` and `releases[]` are the persisted prototype histories. Current values are derived from the last record in each list.

## Verified lifecycle story

1. A farm idea is confirmed through Kickoff and creates a real project session.
2. GameSpec generation and confirmation move the session into Build; the first completed build appends Playable v1.
3. Controlled Change appends a new Playable version. Version restore clones the target snapshot into a new restore version.
4. Publishing creates a Release with real design/spec/playable provenance and a release-scoped candidate batch.
5. Resource Review reads that batch directly. Human save moves the candidate into the global `savedResources` library after the store save timer completes.
6. A second coffee project created through the normal Projects/Kickoff flow reads the same global library. Structured relationship fields produce a recommendation; using the resource changes only relationship fields, while cancel restores the immutable first-use relationship snapshot.
7. My Resources reads the same store collection, supports search/category/detail/edit, and edits are reflected in saved cards and detail.

## Demo smoke

These deterministic entry points were requested from the App bootstrap and all returned HTTP 200 from the local Vite server:

`gamespec`, `build`, `change`, `publish`, `resource-reuse`, `resources`, `my-resources`.

The browser click-level acceptance checklist could not be executed in this environment because no Playwright or Browser connector is available. The source paths, state transitions, and build output were inspected instead; this is the remaining verification limitation.

## Final commands

```bash
cd frontend
npx vue-tsc -b
npx vite build
```

Both commands pass on the final implementation.

## Deliberately deferred

- Backend persistence or database Project / Version / Release records
- Semantic or LLM resource matching
- Real OpenGame runtime and real resource code/asset injection
- Team permissions, marketplace, or shared team library
- Upload/download and resource management administration
- AI resource parameter mapping into a live runtime
