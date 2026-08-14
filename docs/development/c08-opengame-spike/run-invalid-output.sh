#!/usr/bin/env bash
# C08 fixture — INVALID-OUTPUT: a run that completes but produces no index.html artifact.
# Strategy: ask the agent to ONLY explain (no files), so the output tree lacks index.html.
# Reads credentials from ./.env.local (gitignored). NEVER hardcode the key.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
. "$DIR/.env.local" || { echo "missing $DIR/.env.local"; exit 1; }
: "${OPENAI_API_KEY:?set in .env.local}"
: "${OPENAI_BASE_URL:=https://kspmas.ksyun.com/v1}"
: "${OPENAI_MODEL:=kimi-k3}"
export OPENAI_API_KEY OPENAI_BASE_URL OPENAI_MODEL GEMINI_SANDBOX=false

FIX_DIR="$DIR"
WS="D:/yanjiusheng/shixi/youxicehua/OpenGame/agent-test/games/spike-invalid-output"
rm -rf "$WS"; mkdir -p "$WS"; cd "$WS" || { echo "cannot cd"; exit 1; }

OUT="$FIX_DIR/invalid-output-run.stream.json"
ERR="$FIX_DIR/invalid-output-run.stderr.log"

echo "=== invalid-output fixture: prompt forbids writing files ==="
echo "model=$OPENAI_MODEL"
# Ask for explanation only, explicitly forbid creating any files.
opengame -p "Explain in prose how to draw a moving square on an HTML5 canvas using requestAnimationFrame. Do NOT create, write, or edit any files. Do NOT scaffold a project. Output only your explanation as text." \
  --yolo --auth-type openai -m "$OPENAI_MODEL" -o stream-json > "$OUT" 2> "$ERR"
echo "EXIT=$?"

echo "=== line count ==="
wc -l "$OUT"
echo "=== last line (result?) ==="
tail -1 "$OUT"
echo "=== result is_error / subtype ==="
tail -1 "$OUT" | grep -oE '"is_error":(true|false)|"subtype":"[a-z_]+"'
echo "=== output tree (expect NO index.html) ==="
ls -F 2>&1
echo "=== index.html present? ==="
ls index.html 2>&1 || echo "(NO index.html = invalid output, as intended)"
echo "=== stderr tail ==="
tail -8 "$ERR"
