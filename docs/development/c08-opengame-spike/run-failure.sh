#!/usr/bin/env bash
# C08 fixture — FAILURE: a real opengame run that ends in provider failure.
# Strategy: point OPENAI_BASE_URL at a non-existent endpoint so the provider call fails
# fast with a connection error — a genuine `failed` outcome (not a faked one).
# Reads credentials from ./.env.local (gitignored) but OVERRIDES base_url to break it.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
. "$DIR/.env.local" || { echo "missing $DIR/.env.local"; exit 1; }
: "${OPENAI_API_KEY:?set in .env.local}"
: "${OPENAI_MODEL:=kimi-k3}"
# Override base_url to a non-existent host to force a real provider connection failure.
export OPENAI_API_KEY OPENAI_MODEL GEMINI_SANDBOX=false
export OPENAI_BASE_URL="https://kspmas.invalid-endpoint-xyz.local/v1"

FIX_DIR="$DIR"
WS="D:/yanjiusheng/shixi/youxicehua/OpenGame/agent-test/games/spike-failure"
rm -rf "$WS"; mkdir -p "$WS"; cd "$WS" || { echo "cannot cd"; exit 1; }

OUT="$FIX_DIR/failure-run.stream.json"
ERR="$FIX_DIR/failure-run.stderr.log"
: > "$OUT"; : > "$ERR"

echo "=== failure fixture: non-existent provider endpoint (forced connection failure) ==="
echo "model=$OPENAI_MODEL  base_url=$OPENAI_BASE_URL (intentionally broken)"
opengame -p "Build a Snake clone with WASD controls." \
  --yolo --auth-type openai -m "$OPENAI_MODEL" -o stream-json > "$OUT" 2> "$ERR"
echo "EXIT=$?"

echo "=== line count ==="
wc -l "$OUT"
echo "=== last line (result? is_error?) ==="
tail -1 "$OUT"
echo "=== result is_error / subtype ==="
tail -1 "$OUT" | grep -oE '"is_error":(true|false)|"subtype":"[a-z_]+"'
echo "=== error text in stream (API error?) ==="
grep -oE '"text":"\[[A-Za-z ]+Error[^"]*"' "$OUT" 2>&1 | head -3
echo "=== output tree (none expected) ==="
ls -F 2>&1
echo "=== stderr tail ==="
tail -8 "$ERR"
