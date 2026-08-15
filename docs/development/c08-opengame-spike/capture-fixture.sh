#!/usr/bin/env bash
# Capture raw C08 evidence locally. Raw output is ignored; committed fixtures are
# separately minimized and sanitized before review.
set -euo pipefail

SCENARIO="${1:-}"
case "$SCENARIO" in
  success|failure|invalid-output|timeout|cancel) ;;
  *) echo "usage: $0 success|failure|invalid-output|timeout|cancel" >&2; exit 2 ;;
esac

REPO_ROOT="$(git rev-parse --show-toplevel)"
CLI="${OPENGAME_CLI_JS:-$REPO_ROOT/vendor/opengame/dist/cli.js}"
NODE_BIN="${NODE_BIN:-$(command -v node || true)}"
MODEL="${OPENAI_MODEL:-kimi-k3}"
RAW_DIR="$REPO_ROOT/docs/development/c08-opengame-spike/raw"
WORKSPACE="$(mktemp -d "${TMPDIR:-/tmp}/opengame-c08-${SCENARIO}.XXXXXX")"
OUT="$RAW_DIR/${SCENARIO}.stream.json"
ERR="$RAW_DIR/${SCENARIO}.stderr.log"

trap 'rm -rf "$WORKSPACE"' EXIT
test -n "$NODE_BIN" || { echo "node is required" >&2; exit 1; }
test -f "$CLI" || {
  echo "missing pinned CLI: $CLI" >&2
  echo "run: git submodule update --init vendor/opengame" >&2
  echo "then: (cd vendor/opengame && npm ci && npm run build)" >&2
  exit 1
}
test -n "${OPENAI_API_KEY:-}" || { echo "OPENAI_API_KEY is required" >&2; exit 1; }
test -n "${OPENAI_BASE_URL:-}" || { echo "OPENAI_BASE_URL is required" >&2; exit 1; }
mkdir -p "$RAW_DIR"

PROMPT="Build a Snake clone with WASD controls and a dark theme."
if [[ "$SCENARIO" == "invalid-output" ]]; then
  PROMPT="Describe a deliberately oversized online RPG prototype and ask for scope confirmation. Do not write files."
fi

COMMAND=(
  "$NODE_BIN" "$CLI" -p "$PROMPT" --yolo --auth-type openai
  -m "$MODEL" -o stream-json
)

set +e
if [[ "$SCENARIO" == "failure" ]]; then
  (
    cd "$WORKSPACE"
    OPENAI_BASE_URL="https://invalid-opengame-provider.local/v1" \
      exec "${COMMAND[@]}" >"$OUT" 2>"$ERR"
  )
  STATUS=$?
elif [[ "$SCENARIO" == "timeout" || "$SCENARIO" == "cancel" ]]; then
  (cd "$WORKSPACE" && exec "${COMMAND[@]}" >"$OUT" 2>"$ERR") &
  PID=$!
  WAIT_SECONDS=12
  [[ "$SCENARIO" == "cancel" ]] && WAIT_SECONDS=15
  sleep "$WAIT_SECONDS"
  kill "$PID" 2>/dev/null
  wait "$PID"
  STATUS=$?
else
  (cd "$WORKSPACE" && "${COMMAND[@]}" >"$OUT" 2>"$ERR")
  STATUS=$?
fi
set -e

printf '%s\n' "$STATUS" >"$RAW_DIR/${SCENARIO}.exit-code"
find "$WORKSPACE" -type f -print | sed "s#${WORKSPACE}#<WORKSPACE>#g" \
  >"$RAW_DIR/${SCENARIO}.output-tree.txt"
echo "captured raw evidence in $RAW_DIR (exit=$STATUS)"
