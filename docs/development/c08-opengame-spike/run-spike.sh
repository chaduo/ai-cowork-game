#!/usr/bin/env bash
# C08 spike — real success fixture: generate a game, capture stream-json + stderr + exit + output tree.
# Reads credentials from ./.env.local (gitignored). NEVER hardcode the key.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$DIR/.env.local" || { echo "missing $DIR/.env.local"; exit 1; }
: "${OPENAI_API_KEY:?OPENAI_API_KEY not set in .env.local}"
: "${OPENAI_BASE_URL:=https://kspmas.ksyun.com/v1}"
: "${OPENAI_MODEL:=kimi-k3}"
export OPENAI_API_KEY OPENAI_BASE_URL OPENAI_MODEL GEMINI_SANDBOX=false

FIX_DIR="$DIR"
WS="D:/yanjiusheng/shixi/youxicehua/OpenGame/agent-test/games/spike-kimi"
cd "$WS" || { echo "cannot cd to $WS"; exit 1; }

OUT="$FIX_DIR/success-run.stream.json"
ERR="$FIX_DIR/success-run.stderr.log"

echo "=== generating (base_url=$OPENAI_BASE_URL model=$OPENAI_MODEL) ==="
opengame -p "Build a Snake clone with WASD controls and a dark theme." \
  --yolo --auth-type openai -m "$OPENAI_MODEL" -o stream-json > "$OUT" 2> "$ERR"
echo "EXIT=$?"

echo "=== stream-json line count ==="
wc -l "$OUT"
echo "=== last line (expect type:result) ==="
tail -1 "$OUT"
echo "=== first line (expect type:system) ==="
head -1 "$OUT"
echo "=== index.html generated? ==="
ls -la index.html 2>&1
echo "=== output tree (top level) ==="
ls -F 2>&1 | head -40
echo "=== stderr tail ==="
tail -15 "$ERR"
