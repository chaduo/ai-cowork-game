# C02 Project Lifecycle Domain Verification

## Scope

C02 adds persistence and domain transition boundaries for Project, GameDesign,
GameSpecRevision, Build, BuildCandidate, PlayableVersion, and Release. It does not add
Vue behavior, OpenGame execution, build execution, SSE, resources, queues, workers, or a
TestReport table.

## Fresh Evidence

```text
../platform-backend-foundation/backend/.venv/bin/pytest backend/tests -q
20 passed, 1 warning

DATABASE_URL=sqlite:///.../.db alembic -c backend/alembic.ini upgrade head
DATABASE_URL=sqlite:///.../.db alembic -c backend/alembic.ini upgrade head
migration_tables =
['alembic_version', 'build_candidates', 'builds', 'game_designs',
 'game_spec_revisions', 'playable_versions', 'projects', 'releases']

cd frontend && npx vue-tsc -b && npx vite build
exit 0
```

The existing FastAPI TestClient compatibility warning is non-failing and comes from the
installed dependency layer.

## Covered Invariants

- Project stage is derived; no `stage` column is persisted.
- GameSpec revisions are immutable records with per-project revision numbers.
- Only confirmed GameSpec revisions can start a Build.
- A Project has at most one active Build guard.
- Build completion creates a Candidate and clears only its matching active guard.
- Candidate creation never updates `current_playable_version_id`.
- Failed/cancelled/orphaned Builds do not create PlayableVersion or Release.
- Promotion requires an explicit `pass` verdict and updates the current playable pointer atomically.
- Publish is a separate explicit action for the current PlayableVersion.
- Retry creates a new Build with `parent_build_id` and an incremented attempt.
- Recovery marks unfinished Builds orphaned, clears matching guards, and is idempotent.
- Two Projects keep independent active Build guards.

## Known Boundary

C02 service methods currently use a caller-owned SQLAlchemy Session. C03+ API changes should
wrap each mutation in the C01 transaction boundary and expose domain errors through the C01
error envelope. C12 will provide the persisted TestReport and validation gate; C02 accepts its
opaque PASS authorization without owning that table.
