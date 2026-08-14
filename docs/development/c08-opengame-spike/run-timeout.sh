#!/usr/bin/env bash
# C08 fixture — TIMEOUT: opengame started via node cli.js, killed after ~12s.
# PowerShell Start-Process with -RedirectStandardOutput writes each line to the file
# as it arrives (real-time flush), so killing the tree leaves the captured stream-json
# intact up to the kill point. Gets the real node PID for /T tree-kill.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
. "$DIR/.env.local" || { echo "missing $DIR/.env.local"; exit 1; }
: "${OPENAI_API_KEY:?set in .env.local}"
: "${OPENAI_BASE_URL:=https://kspmas.ksyun.com/v1}"
: "${OPENAI_MODEL:=kimi-k3}"
export OPENAI_API_KEY OPENAI_BASE_URL OPENAI_MODEL GEMINI_SANDBOX=false

FIX_DIR="$DIR"
WS_WIN='D:\yanjiusheng\shixi\youxicehua\OpenGame\agent-test\games\spike-timeout'
mkdir -p "D:/yanjiusheng/shixi/youxicehua/OpenGame/agent-test/games/spike-timeout" 2>/dev/null
OUT_WIN='D:\yanjiusheng\shixi\youxicehua\xiaozuhuibao\docs\development\c08-opengame-spike\timeout-run.stream.json'
ERR_WIN='D:\yanjiusheng\shixi\youxicehua\xiaozuhuibao\docs\development\c08-opengame-spike\timeout-run.stderr.log'
: > "D:/yanjiusheng/shixi/youxicehua/xiaozuhuibao/docs/development/c08-opengame-spike/timeout-run.stream.json"
: > "D:/yanjiusheng/shixi/youxicehua/xiaozuhuibao/docs/development/c08-opengame-spike/timeout-run.stderr.log"

NODE='D:\Program Files (x86)\nodejs\node.exe'
CLI='D:\Program Files (x86)\nodejs\node_global\node_modules\@opengame\opengame\dist\cli.js'
WAIT=12
echo "=== timeout fixture: node cli.js, kill tree after ${WAIT}s ==="

powershell -NoProfile -Command "
\$env:OPENAI_API_KEY='$OPENAI_API_KEY'; \$env:OPENAI_BASE_URL='$OPENAI_BASE_URL';
\$env:OPENAI_MODEL='$OPENAI_MODEL'; \$env:GEMINI_SANDBOX='false'
\$args = '\"$CLI\" -p \"Build a Snake clone with WASD controls and a dark theme.\" --yolo --auth-type openai -m $OPENAI_MODEL -o stream-json'
\$p = Start-Process -FilePath '$NODE' -ArgumentList \$args -WorkingDirectory '$WS_WIN' -RedirectStandardOutput '$OUT_WIN' -RedirectStandardError '$ERR_WIN' -PassThru -NoNewWindow
Write-Host \"node PID=\$(\$p.Id)\"
Start-Sleep -Seconds $WAIT
Write-Host \"killing tree after ${WAIT}s\"
taskkill /T /F /PID \$p.Id 2>\$null | Out-Null
\$p.WaitForExit(3000) | Out-Null
Write-Host \"EXIT=\$(\$p.ExitCode)\"
" 2>&1 | head -8

OUT="$FIX_DIR/timeout-run.stream.json"
echo "=== stream-json line count (interrupted) ==="
wc -l "$OUT"
echo "=== event types captured ==="
grep -oE '"type":"[a-z_]+"' "$OUT" 2>&1 | sort | uniq -c
echo "=== contains a result event? (expect none — timed out) ==="
grep -c '"type":"result"' "$OUT" 2>&1
echo "=== last 2 lines ==="
tail -2 "$OUT"
echo "=== partial output tree ==="
ls -F "D:/yanjiusheng/shixi/youxicehua/OpenGame/agent-test/games/spike-timeout" 2>&1
