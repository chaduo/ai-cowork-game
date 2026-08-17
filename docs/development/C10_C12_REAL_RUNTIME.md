# C10/C12 Real Runtime Verification

This is the manual path for real data. It does not use `FakeGameAgent`,
`FakeCandidateTestRunner`, frontend fixtures, or hand-written database rows.

## 1. Configure real providers

```bash
cd /Users/zhaozhuo/workspace/explore/ai-cowork-game/backend
source .venv/bin/activate

export GAME_AGENT_PROVIDER=opengame
export CANDIDATE_TEST_PROVIDER=chrome
export OPENGAME_CLI_JS="$(realpath "$(command -v opengame)")"
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://.../v1"
export OPENAI_MODEL="kimi-k3"
export DATABASE_URL="sqlite:///./data/manual-real-runtime.db"
```

`GAME_AGENT_PROVIDER=opengame` and `CANDIDATE_TEST_PROVIDER=chrome` are
fail-closed production settings. If either provider is unavailable, the API
returns a structured failure; it never silently switches to Fake.

## 2. Prepare the database and start the API

```bash
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```bash
curl http://127.0.0.1:8000/healthz
```

## 3. Real lifecycle

Use the browser UI to create a Project, finish Game Design and confirm a
GameSpec. Start one Build and wait for its persisted `build_id` to reach a
terminal state. Then query the Build API and copy its real `candidate_id`:

```bash
curl http://127.0.0.1:8000/api/v1/builds/<BUILD_ID>
```

Run platform verification against that Candidate:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/candidates/<CANDIDATE_ID>/test
```

For a valid OpenGame artifact the response must contain platform-owned
evidence for `browser_started`, `console`, `core_input`, `gameplay`,
`completion` and `phaser_hook`, with `platform_verdict=PASSED` and
`test_gate_status=ready`. The Candidate HTML must expose:

```js
window.__GAME_TEST__ = {
  version: 1,
  ready: true,
  run: async (check) => ({ passed: true, observed: "..." })
}
```

The hook must perform the named check against actual game state. Returning a
hardcoded PASS is recorded as runtime evidence but does not satisfy the
platform contract.

## 4. C14 Human Gate and Restore

```bash
curl -X POST http://127.0.0.1:8000/api/v1/candidates/<CANDIDATE_ID>/human-play-review \
  -H 'Content-Type: application/json' \
  -d '{"decision":"accepted","notes":"Played the real build"}'

curl -X POST http://127.0.0.1:8000/api/v1/candidates/<CANDIDATE_ID>/promote \
  -H 'Content-Type: application/json' \
  -d '{"git_commit":"<REAL_PROJECT_COMMIT>"}'

curl http://127.0.0.1:8000/api/v1/projects/<PROJECT_ID>/playable-versions

curl -X POST \
  http://127.0.0.1:8000/api/v1/projects/<PROJECT_ID>/playable-versions/<VERSION_ID>/restore
```

Restore must return a new `candidate_id` with `test_gate_status=untested`.
The original current Playable and version history must remain unchanged until
the restored Candidate is tested, reviewed and promoted.

## 5. Real browser smoke test

The focused smoke is opt-in because it starts a local Chrome process:

```bash
cd /Users/zhaozhuo/workspace/explore/ai-cowork-game
RUN_REAL_BROWSER_SMOKE=1 backend/.venv/bin/pytest \
  backend/tests/test_c10_c12_real_runtime.py -q
```

The normal test suite keeps this smoke skipped when Chrome is unavailable or
when the opt-in variable is absent. C10 credentialed OpenGame smoke tests are
also opt-in and never use committed credentials.
