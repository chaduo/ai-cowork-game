# C08 OpenGame CLI Spike — Version Lock, Invocation & Config

> Owner: zhang · Change: C08 `opengame-cli-spike` · 采集日期 2026-08-14
> 目标 OpenGame = **leigest519/OpenGame**（仓库 spec `specs/001-game-creation-mvp/research.md` §6 第 119 行认定的唯一 OpenGame）。
> **重要更正：** 上一轮 spike 误把 git submodule `test/agent-game-forge`（0x0funky，HTTP daemon 形态）当成 OpenGame，结论"从包 CLI 改为包 daemon + run"是错的，已撤回。该子模块不是 Adapter 目标，**已于本次变更（feature/c08-opengame-cli-spike）从主仓库移除**，由 `vendor/opengame`（CodingZY/OpenGame @ c54307e）取代。本文件记录对**正确对象**的 spike。

---

## 1. 版本锁定（C08 交付物 #1）

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/leigest519/OpenGame |
| 锁定 commit | `c54307efe1dab927e7fc52dbb92af6b3df1d1c66`（main，2026-04-22，作者 YelonLFT） |
| 版本号 | `opengame` `0.6.0`（`opengame --version` → `0.6.0`） |
| 形态 | **真 CLI**，`bin.opengame = dist/cli.js`，npm 包 `@opengame/opengame` |
| 运行时 | Node.js ≥20（本机 v20.20.1 ✓） |
| sandbox 镜像 | `ghcr.io/leigest519/opengame:0.6.0`（Docker/Podman，spec §8 隔离用） |
| 本地安装位置 | `D:/yanjiusheng/shixi/youxicehua/OpenGame`（主仓库同级目录，外部工具不入主仓库 git） |

### 安装方式（可重复）

```bash
git clone --depth 1 https://github.com/leigest519/OpenGame.git   # main HEAD 即 c54307e
cd OpenGame
npm install          # 仓库自带 node_modules/ 与 dist/，install 主要是补全/link
npm link             # 把 opengame 装到全局 PATH
opengame --version   # → 0.6.0
```
- `dist/cli.js`（15.8MB esbuild bundle）由作者提交，clone 即有，**无需 `npm run build`** 也可直接 `node dist/cli.js`。
- `npm link` 后 `opengame` 在全局 PATH：`D:\Program Files (x86)\nodejs\node_global\opengame(.cmd)`。

### Windows 已知坑（与 codex 同源，记录备用）

`opengame` link 到带空格的 `node_global`。若将来由 Python `asyncio.subprocess` 以全路径 + shell spawn，可能触发同款空格截断 bug。Adapter 实现时优先用**裸名 `opengame`**（让 cmd.exe 走 PATH 解析），或确保 spawn 不带空格全路径。spike 阶段用全局 PATH 调用不受影响。

---

## 2. 调用语法（C08 交付物 #2）

### 基本调用（README "Quick Start"）

```bash
# 在一个空游戏文件夹里跑（cwd = 游戏工作区）
mkdir -p games/my-game && cd games/my-game
opengame -p "Build a Snake clone with WASD controls and a dark theme." --yolo
# 完成后在该目录得到 index.html
```

### 非交互 / 可编程模式（Adapter 实际要用的方式）

```bash
opengame \
  -p "<GameSpec prompt>" \
  --yolo \
  --auth-type openai \
  --openai-api-key "$OPENAI_API_KEY" \
  --openai-base-url "$OPENAI_BASE_URL" \
  -m "$OPENAI_MODEL" \
  --input-format stream-json \
  -o stream-json
```

关键 flag（来自 `opengame --help`）：

| flag | 作用 | Adapter 意义 |
|---|---|---|
| `-p, --prompt <text>` | 一句话 prompt（GameSpec 输入） | GameBuildRequest.prompt |
| `-y, --yolo` / `--approval-mode yolo` | 自动批准所有工具（含 shell） | 非交互必须，否则会卡在确认 |
| `--approval-mode` | `plan`/`default`/`auto-edit`/`yolo` | headless 默认自动升到 auto-edit（可写文件），shell 需 yolo |
| `--auth-type` | `openai`/`anthropic`/`qwen-oauth`/`gemini`/`vertex-ai` | 金山云 OpenAI 兼容端点用 `openai` |
| `--openai-api-key` | API key | 也可用环境变量（见 §3） |
| `--openai-base-url` | OpenAI base URL（自定义端点） | 金山云端点；CLI flag 优先于环境变量 |
| `-m, --model` | 模型 id | GameCoder-27B / 端点支持的模型 |
| `-o, --output-format` | `text`/`json`/`stream-json` | **`stream-json` = C06 要归一化成 RunEvent 的原始事件流** |
| `--input-format` | `text`/`stream-json` | 配合 `-o stream-json` 做全可编程 |
| `--include-partial-messages` | stream-json 含 partial 消息 | 流式进度 |
| `-s, --sandbox` / `--sandbox-image` | Docker/Podman 隔离 | spec §8 隔离；`GEMINI_SANDBOX=false` 关闭 |
| `-c/--continue` / `-r/--resume <id>` | 恢复会话 | spec §7：从最近成功 Version 重跑，不复用中间态 |
| `--max-session-turns` | 最大轮数 | 成本/超时控制 |
| `--allowed-tools` / `--exclude-tools` | 工具白/黑名单 | C13 隔离边界 |
| `--experimental-skills` | 开启 Skills | Template Skill + Debug Skill |

### cwd 约定（对应 spec §3 / §8）

- **cwd = 当前 run 的 workspace**：spec §3 `data/workspaces/{run_id}/{agent_session_id}/`。
- README 明确"Create an empty folder for your new game"再跑——每 run 独立目录，与 C13 隔离对齐。
- 若 cwd 在仓库外，需 `GAME_TEMPLATES_DIR` / `GAME_DOCS_DIR` 指向 OpenGame 仓库内模板（README 备注）。spike 阶段在仓库内 `agent-test/games/` 下跑最简单。

---

## 3. 配置语法（C08 交付物 #3）

OpenGame 三种配置途径，优先级 CLI flag > 环境变量 > settings.json：

- **User settings**：`~/.qwen/settings.json`
- **Project settings**：`<cwd>/.qwen/settings.json`
- （目录名 `.qwen` 是上游 qwen-code 遗留，将来迁 `.opengame`）

### 主 LLM（OpenAI 兼容）——环境变量方式（README "Authentication"）

```bash
export OPENAI_API_KEY="sk-..."          # 必填
export OPENAI_BASE_URL="https://kspmas.ksyun.com/v1"   # 自定义端点（OpenAI SDK 自动补 /chat/completions）
export OPENAI_MODEL="<model-id>"         # 端点支持的模型
```
- base_url 取到 `/v1` 为止，**不要**带 `/chat/completions`（SDK 自动补全）。
- 也可用 CLI flag `--openai-api-key` / `--openai-base-url` 覆盖。

### 资产生成 provider（图片/视频/音频/推理）——独立配置

```bash
export OPENGAME_IMAGE_PROVIDER=tongyi        # tongyi | doubao | openai-compat
export OPENGAME_IMAGE_API_KEY=sk-...
# OPENGAME_REASONING_* / OPENGAME_VIDEO_* / OPENGAME_AUDIO_* 同理
```
- **没配资产 key 时回退占位素材**（spec §9："失败时复制模板内置占位素材并记录 `builtin_placeholder` 来源"）。因此只给主 LLM key 也能跑通端到端，素材用占位——适合 spike。

### sandbox

```bash
# 本地无 Docker：关掉 sandbox
export GEMINI_SANDBOX=false
# 或用 Docker：
# GEMINI_SANDBOX=docker opengame ...  （需 build sandbox 镜像）
```

### 完整配置参考
- `docs/users/configuration/api-keys.md`（OpenAI / fal.ai / OpenRouter / DashScope / Doubao）
- `.env.example`（复制粘贴模板）
- 启动时会打印一行 provider-status banner，可确认各 modality 是否接通。

---

## 4. stream-json 事件结构（来自 `integration-tests/json-output.test.ts`，无需联网即可确定）

`opengame ... -o stream-json` 输出 **NDJSON**（每行一个 JSON 对象）。这是 OpenGameAdapter 要消费、并归一化成 RunEvent 的原始流。已确认的消息类型：

| `type` | 字段 | 说明 |
|---|---|---|
| `system` | `subtype`, `session_id` | 会话开始/元信息 |
| `assistant` | `message`, `session_id` | agent 输出（含文本 + 工具调用） |
| `result` | `is_error`, `result`, 可选 `stats` | 最后一条，结束标志。`is_error=false` ⇒ 成功；`stats` 含用量 |

对照 C06 要冻结的供应商无关 RunEvent（spec §5：`sequence / run_id / stage / type / level / message / timestamp / progress`）：Adapter 把上面的 `system/assistant/result` 映射成 RunEvent 的 stage/type，把 `session_id` 映射成 `agent_session_id`（spec §3 `data/workspaces/{run_id}/{agent_session_id}/`）。

`-o json`（非 stream）则返回一个 JSON **数组**，最后一条仍是 `type: "result"`。

---

## 5. 真实 success fixture ✅ (2026-08-14)

真实端到端生成已跑通（详见 `success-fixture-README.md`）：

| 项 | 值 |
|---|---|
| 端点 | `https://kspmas.ksyun.com/v1`（OpenAI 兼容） |
| 模型 | `kimi-k3`（用 `-m` flag 显式传；仅靠 `OPENAI_MODEL` 环境变量会被回退到默认 `glm-5.2`） |
| prompt | `Build a Snake clone with WASD controls and a dark theme.` |
| flags | `--yolo --auth-type openai -m kimi-k3 -o stream-json`，`GEMINI_SANDBOX=false` |
| 结果 | exit `0`，18 turns，216s，`result.is_error:false` |
| artifact | `index.html` + `main.js`(366 行) + `style.css`(225 行) + `test/smoke.cjs`，真实可玩 |
| 验证 | `node --check main.js` OK；`node test/smoke.cjs` → `SMOKE_OK` |
| fixture | `success-run.stream.json`（67 行 NDJSON，完整事件流） |

stream-json 实测事件：1 `system` + 45 `assistant`（16 thinking / 12 text / 20 tool_use / 20 tool_result）+ 1 `result`(success)。`assistant.message.content[]` block 类型 = thinking/text/tool_use/tool_result/user。

**仍待补**：failure / cancel / invalid-output / timeout fixtures（见 `success-fixture-README.md` 末尾）。

### 本地复跑方式（key 走环境变量，绝不落盘/提交）

```bash
cd D:/yanjiusheng/shixi/youxicehua/OpenGame/agent-test/games/<new-game-dir>
OPENAI_API_KEY="sk-..." OPENAI_BASE_URL="https://kspmas.ksyun.com/v1" \
  GEMINI_SANDBOX=false \
  opengame -p "<prompt>" --yolo --auth-type openai -m kimi-k3 -o stream-json > out.json
```
（`probe-spike.sh` / `run-spike.sh` 脚本可复用，从 `.env.local` 读 key——该文件已 gitignore，跑完即删。）

---

## 5. 对 C09/C10/Adapter 的落地结论

- **包 CLI，不是 daemon。** 计划原文"包 CLI"正确；上轮"改 daemon"结论作废。
- **OpenGameAdapter 是 Python 组件**，在 FastAPI `backend/`（spec §2/§6），用 `asyncio.subprocess` spawn `opengame`（spec §6 资料链接 = Python asyncio subprocess）。**不是 Node。**
- **Adapter 职责**：spawn `opengame`（cwd=run workspace，`-o stream-json`）→ 读 stream-json → 归一化成供应商无关 RunEvent（spec §5）→ 返回 exit code + artifact 路径。不解析 stdout 自由文本。
- **它是 `GameAgentAdapter` 接口的 V1 实现**（spec §6：稳定边界叫 `GameAgentAdapter`，V1=`OpenGameAdapter`，V2=`ClaudeRuntimeAdapter`）。换 provider 不动上层。
- **Human Gate**：FastAPI 控制业务阶段，Adapter/LLM 不替人按 Promote/Publish（spec §6/§7）。

---

## 附：上轮（测错对象）的归档

`./_wrong-target-agent-game-forge-daemon/` 下保留了上轮对 `agent-game-forge`（0x0funky daemon，已从主仓库移除）的 fixture 和旧 README，**仅作"抓 SSE/stdout/stderr/exit code/output tree"的方法参考**，不再是任何 Adapter 目标。本次 spike 实际使用的是 `D:/yanjiusheng/shixi/youxicehua/OpenGame` 这个同级 clone（origin 指向 CodingZY/OpenGame）；后续 spike 与 Adapter 集成统一改用主仓库的 `vendor/opengame` submodule。
