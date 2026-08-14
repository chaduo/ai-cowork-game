#!/usr/bin/env bash
# C08 spike — probe: validate ksyun endpoint + kimi-k3 + stream-json format.
# Reads credentials from ./.env.local (gitignored). NEVER hardcode the key.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$DIR/.env.local" || { echo "missing $DIR/.env.local"; exit 1; }
: "${OPENAI_API_KEY:?OPENAI_API_KEY not set in .env.local}"
: "${OPENAI_BASE_URL:=https://kspmas.ksyun.com/v1}"
: "${OPENAI_MODEL:=kimi-k3}"
export OPENAI_API_KEY OPENAI_BASE_URL OPENAI_MODEL GEMINI_SANDBOX=false

WS="D:/yanjiusheng/shixi/youxicehua/OpenGame/agent-test/games/spike-kimi"
cd "$WS" || { echo "cannot cd to $WS"; exit 1; }

echo "=== opengame probe (1 turn, stream-json, model=$OPENAI_MODEL) ==="
timeout 120 opengame -p "Reply with exactly the word READY and nothing else." \
  --yolo --auth-type openai -m "$OPENAI_MODEL" --max-session-turns 1 -o stream-json 2>&1 | head -40
echo "=== probe finished (pipe exit=${PIPESTATUS[0]}) ==="
