# C05 Game Design / GameSpec Flow Verification

## Scope

- Original Idea -> persisted Game Design draft -> independent Human Confirm.
- Confirmed design -> canonical CreatorGameSpec draft/revision -> independent Human Confirm.
- Relationship gameplay fields are part of the canonical GameSpec content model.
- Build start is rejected unless both design and GameSpec are confirmed and schema-valid.
- Vue screens restore drafts and confirmed revisions through the API without putting workflow metadata in GameSpec.

## Automated evidence

From the C05 worktree:

```text
backend/tests: 39 passed, 1 warning
frontend: vue-tsc -b passed
frontend: vite build passed (1662 modules transformed)
git diff --check: passed
```

Migration idempotency was verified against a fresh SQLite database. Running `alembic upgrade head` twice leaves the database at revision `0003_project_creation_idempotency` and creates the lifecycle tables only once.

The API walkthrough passed the following assertions:

- Create a project.
- Confirming GameSpec before Game Design returns `409 design_confirmation_required`.
- Save and confirm Game Design.
- Invalid GameSpec input returns `422 validation_error`.
- Save and confirm a canonical GameSpec containing relationship fields.
- A fresh TestClient can read the confirmed revision.
- Persisted content contains relationship fields and no `recommended` workflow flag.
- `ProjectLifecycleService.start_build()` starts only after confirmation (`running` in the local service).

## Manual UI acceptance

1. Start the backend from `backend/` with the C01 virtualenv and run migrations:

   ```bash
   DATABASE_URL=sqlite:///./data/app.db alembic -c alembic.ini upgrade head
   uvicorn app.main:app --reload --port 8000
   ```

2. Start the Vue prototype with `cd frontend && npm run dev`.

3. Create a project from the Idea entry. Complete the clarification flow, close the modal, refresh the browser, and reopen the same project. The saved answers and current clarification step must remain.

4. Submit the Game Design. Confirm it. Refresh Projects and reopen the project; the design remains confirmed.

5. Enter the GameSpec review. Edit a relation field such as relationship growth or favor rules, refresh, and confirm the GameSpec. The edited value must remain visible and the Build timeline may start only after confirmation succeeds.

6. Use the API or browser Network panel to verify that GameSpec payloads contain canonical content only. They must not contain `recommended`, `dismissed`, `used`, `drawer`, or resource IDs.

7. Repeat with a second project and confirm that drafts, design status, and GameSpec revisions do not leak between projects.

## Known prototype boundary

OpenGame execution and real Build artifact generation remain outside C05. This Change persists and validates the design/GameSpec contract and gates the existing prototype Build timeline; it does not implement C08/C09 execution.
