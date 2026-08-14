#!/usr/bin/env bash
# C08 fixture — CANCEL: opengame runs ~15s (into the file-writing phase), then the
# user cancels (process tree killed). Same mechanism as timeout; the distinction is
# semantic + captured evidence: cancel happens mid-work after useful progress, timeout
# is an external deadline. This fixture shows an interrupted stream mid-work.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
. "$DIR/.env.local" || { echo "missing $DIR/.env.local"; exit 1; }
: "${OPENAI_API_KEY:?set in .env.local}"
: "${OPENAI_BASE_URL:=https://kspmas.ksyun.com/v1}"
: "${OPENAI_MODEL:=kimi-k3}"
export OPENAI_API_KEY OPENAI_BASE_URL OPENAI_MODEL GEMINI_SANDBOX=false

FIX_DIR="$DIR"
WS_WIN='D:\yanjiusheng\shixi\youxicehua\OpenGame\agent-test\games\spike-cancel'
mkdir -p "D:/yanjiusheng/shixi/youxicehua/OpenGame/agent-test/games/spike-cancel" 2>/dev/null
OUT_WIN='D:\yanjiusheng\shixi\youxicehua\xiaozuhuibao\docs\development\c08-opengame-spike\cancel-run.stream.json'
ERR_WIN='D:\yanjiusheng\shixi\youxicehua\xiaozuhuibao\docs\development\c08-opengame-spike\cancel-run.stderr.log'
: > "D:/yanjiusheng/shixi/youxicehua/xiaozuhuibao/docs/development/c08-opengame-spike/cancel-run.stream.json"
: > "D:/yanjiusheng/shixi/youxicehua/xiaozuhuibao/docs/development/c08-opengame-spike/cancel-run.stderr.log"

NODE='D:\Program Files (x86)\nodejs\node.exe'
CLI='D:\Program Files (x86)\nodejs\node_global\node_modules\@opengame\opengame\dist\cli.js'
WAIT=15
echo "=== cancel fixture: node cli.js, cancel (kill tree) after ${WAIT}s of work ==="

powershell -NoProfile -Command "
\$env:OPENAI_API_KEY='$OPENAI_API_KEY'; \$env:OPENAI_BASE_URL='$OPENAI_BASE_URL';
\$env:OPENAI_MODEL='$OPENAI_MODEL'; \$env:GEMINI_SANDBOX='false'
\$args = '\"$CLI\" -p \"Build a Snake clone with WASD controls and a dark theme.\" --yolo --auth-type openai -m $OPENAI_MODEL -o stream-json'
\$p = Start-Process -FilePath '$NODE' -ArgumentList \$args -WorkingDirectory '$WS_WIN' -RedirectStandardOutput '$OUT_WIN' -RedirectStandardError '$ERR_WIN' -PassThru -NoNewWindow
Write-Host \"node PID=\$(\$p.Id)\"
Start-Sleep -Seconds $WAIT
Write-Host \"--- user cancels at this point (kill tree) ---\"
taskkill /T /F /PID \$p.Id 2>\$null | Out-Null
\$p.WaitForExit(3000) | Out-Null
Write-Host \"EXIT=\$(\$p.ExitCode)\"
" 2>&1 | head -8

OUT="$FIX_DIR/cancel-run.stream.json"
echo "=== stream-json line count (interrupted mid-work) ==="
wc -l "$OUT"
echo "=== event types captured ==="
grep -oE '"type":"[a-z_]+"' "$OUT" 2>&1 | sort | uniq -c
echo "=== contains a result event? (expect none — cancelled) ==="
grep -c '"type":"result"' "$OUT" 2>&1
echo "=== tool_use events before cancel ==="
grep -c '"type":"tool_use"' "$OUT" 2>&1
echo "=== last 2 lines ==="
tail -2 "$OUT"
echo "=== partial output tree (files written before cancel) ==="
ls -F "D:/yanjiusheng/shixi/youxicehua/OpenGame/agent-test/games/spike-cancel" 2>&1
