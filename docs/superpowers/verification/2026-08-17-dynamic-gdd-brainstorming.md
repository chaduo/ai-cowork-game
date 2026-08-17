# Dynamic Game Design Brainstorm Verification

## Automated evidence

- `backend/.venv/bin/pytest backend/tests/test_game_design_brainstorm_contract.py backend/tests/test_game_design_brainstorm_service.py backend/tests/test_openai_game_design_planner.py backend/tests/test_c05_brainstorm_api.py backend/tests/test_c05_design_api.py backend/tests/test_c05_design_revision_contract.py -q`
- `for f in frontend/tests/*.test.mjs; do node "$f"; done`
- `npm --prefix frontend run build`

The full backend suite is expected to pass except for Playwright tests when macOS blocks the bundled Chromium process with `mach_port_rendezvous ... Permission denied`; those tests require the same local browser permission setup as C10/C12.

## Real provider setup

Use backend-only environment variables. Never commit the key:

```bash
export GAME_DESIGN_PROVIDER=openai
export OPENAI_BASE_URL="https://your-openai-compatible-host/v1"
export OPENAI_API_KEY="..."
export GAME_DESIGN_MODEL="kimi-k3"
```

`cowork-real` reads these variables through `get_settings()`. If the provider is missing, the API returns `503 game_design_provider_not_configured` and the UI keeps the project in Brainstorming; it does not render the old Fixture question.

## Browser acceptance

1. Create two projects with unrelated Ideas, for example a farm and a lighthouse mystery. Confirm their first questions or choices differ.
2. Choose an option in the first project. Confirm the answer appears in the conversation and a new question is returned.
3. Use “这些都不是，我有自己的想法” and submit free text. Refresh the page and reopen the same project. Confirm the free-text decision and current question remain.
4. Close and reopen the modal while the project is still clarifying. Confirm it resumes from the persisted question instead of restarting from a Fixture.
5. Try Confirm Design before First Playable readiness. The API must return `409 design_not_ready`; the UI must remain in Brainstorming.
6. Answer the finite First Playable questions until the server reports `readiness.status = ready`. Confirm Design once. Confirm the project enters GameSpec and no Build starts automatically.
7. Remove or invalidate the provider variables and retry one turn. Confirm the UI shows the provider error and does not silently fall back to a fixed question.

## Skill boundary check

The referenced `game-brainstorm` Skill influences prompt wording and question priority only. Database revisions, provenance, readiness, Confirm GDD, Project stage, and Build gates remain platform-owned.
