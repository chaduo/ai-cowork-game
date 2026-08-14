# C08 Success Fixture — Real Game Generation (kimi-k3)

> 采集日期 2026-08-14 · 真实端到端生成，非 Fake。
> OpenGame: leigest519/OpenGame fork CodingZY/OpenGame @ commit `c54307e`, `opengame` 0.6.0
> Endpoint: `https://kspmas.ksyun.com/v1` (OpenAI-compatible) · Model: `kimi-k3`

## Files

| file | content |
|---|---|
| `success-run.stream.json` | 完整 NDJSON 事件流（67 行），真实生成的全过程 |
| `../README.md` | C08 spike 总文档（版本锁定、调用、配置、stream-json 结构） |

## Run metadata

| 项 | 值 |
|---|---|
| cwd (run workspace) | `D:/yanjiusheng/shixi/youxicehua/OpenGame/agent-test/games/spike-kimi` |
| prompt | `Build a Snake clone with WASD controls and a dark theme.` |
| flags | `--yolo --auth-type openai -m kimi-k3 -o stream-json` |
| env | `OPENAI_BASE_URL=https://kspmas.ksyun.com/v1` `GEMINI_SANDBOX=false` |
| exit code | `0` |
| turns | `18` |
| duration | 216570 ms (≈3.6 min) |
| token usage | input 427011 / output 16298 / cache_read 343149 / total 443309 |
| session_id | `caaabd89-4c97-4461-8882-4c561a0e7955` |
| result.is_error | `false` (success) |

## Generated artifact tree (cwd)

```
spike-kimi/
├── index.html      1345 B   Neon Snake 页面（中文 UI, canvas 600×600）
├── main.js          366 行  游戏逻辑（24×24 网格 / WASD+方向键 / 加速 / 最高分 localStorage）
├── style.css       225 行  深色霓虹主题
└── test/
    └── smoke.cjs     59 行  DOM 桩冒烟测试
```

## Verification (artifact 真实可用)

- `node --check main.js` → 语法 OK
- `node test/smoke.cjs` → `SMOKE_OK: main.js 加载、初始化、首帧渲染均无异常` (exit 0)
- `index.html` 存在且引用 `main.js`/`style.css`，可直接双击打开运行
- agent 自述：纯原生 HTML/CSS/JS，零依赖，无需构建

## stream-json event breakdown (67 lines)

```
1  type:system     (subtype:init — tools list, model, cwd)
45 type:assistant  (含 message: 16 thinking + 12 text + 20 tool_use + 20 tool_result + 20 user)
1  type:result     (subtype:success, is_error:false, usage, duration)
```

事件类型与 `integration-tests/json-output.test.ts` 一致：`system` / `assistant` / `result`。
`assistant.message.content[]` 的 block 类型：`thinking` / `text` / `tool_use` / `tool_result` / `user`。
这正是 **OpenGameAdapter 要消费 → 归一化成供应商无关 RunEvent**（spec §5）的原始流。

## 对 C06/C10 的契约要点（从真实流提炼）

- `system.init` 携带 `tools[]`、`model`、`cwd`、`session_id`、`permission_mode`、`qwen_code_version` → 可映射 RunEvent 的 run 元信息。
- `assistant.message.content[]` 的 `tool_use`（name+input）/ `tool_result`（content）→ agent 工作步骤，映射 RunEvent 的 stage/type。
- `thinking` block → 可映射为 RunEvent 的 `level: debug` 或单独 stage（产品层是否暴露 thinking 由 zhao 定）。
- `result` 是终结事件：`is_error` 定 success/fail，`usage` 含 token（计费/成本透明，spec §10），`duration_ms`。
- `num_turns` 可用于超时/成本控制（对应 C09 timeout / `--max-session-turns`）。

## 待补 fixtures

- [ ] failure-run.stream.json：agent 失败结束（`result.is_error:true` 或 exit≠0）
- [ ] cancel-run.stream.json：运行中中断（kill 进程树）的输出
- [ ] invalid-output：产出缺 index.html / 非法路径 / partial artifact 的情况
- [ ] timeout：`--max-session-turns` 触顶或 C09 Executor 超时

---

## 补充 fixtures（2026-08-14 采集，真实 opengame run）

四份剩余 C08 交付物已补齐，均为真实 `opengame` 调用（model `kimi-k3`）。采集脚本：`run-failure.sh` / `run-timeout.sh` / `run-cancel.sh` / `run-invalid-output.sh`。

### failure-run.stream.json（provider 连接失败）

- **触发**：`OPENAI_BASE_URL` 指向不存在的端点（`https://kspmas.invalid-endpoint-xyz.local/v1`），强制 provider 连接错误。
- **结果**：3 行 = system init → assistant text `"[API Error: Connection error.]"` → result。
- **关键契约发现 ⚠️**：opengame 把 provider 错误**包成 `subtype:success`、`is_error:false`**，错误文本塞进 `result.result` 字段，`usage` 全 0（input/output tokens 都 0），exit 0。**`result.is_error` 不可信**——OpenGameAdapter（C10）不能只靠 `is_error` 判失败，必须额外检查：`result.result` 含 `[API Error: ...]`、`usage.input_tokens==0`、无 artifact。这是 `failed` 状态在 opengame 0.6.0 的真实形态。
- **output tree**：空（无 artifact）。

### invalid-output-run.stream.json（成功标记但零 artifact）

- **触发**：prompt 明确要求"只解释、不写任何文件"，agent 遵从，输出文本提问后正常结束。
- **结果**：4 行 = system + 2 assistant（thinking + text）+ result（`is_error:false`，success）。
- **关键契约发现 ⚠️**：run 报 `success` 但**产出零 artifact（无 index.html、无任何文件）**。这是 `invalid_output` 的真实形态——`result.is_error:false` 但工作目录无有效产物。OpenGameAdapter 必须校验 artifact 存在性，不能信 `is_error`。
- **output tree**：空。

### timeout-run.stream.json（外部超时杀进程）

- **触发**：正常 prompt，PowerShell 启动 node cli.js，12 秒后 `taskkill /T /F` 杀整进程树（模拟 C09 Executor 超时——opengame 无内置 timeout）。
- **结果**：1 行 = system init，**无 result 事件**（进程被外部终止，未产出终结事件）。
- **关键契约要点**：timeout 在 stream-json 层面 = **流被截断、无 `type:result` 终结事件**。C09 Executor 超时杀进程后，OpenGameAdapter 观察到"无 result + 进程被杀" → 映射为 `GameBuildStatus.timed_out`。output tree 已有部分文件（index.html/game.js/style.css）——说明 agent 在被杀前已写文件，但产物不完整 → 不得作为 Playable。
- **output tree**：index.html + game.js + style.css（partial，不可用）。
- **采集机制**：`Start-Process -RedirectStandardOutput` 实时落盘 + `taskkill /T /F` 杀树（git-bash `$!` 拿不到真实 node PID，必须用 PowerShell 拿 `Start-Process` 的 `-PassThru` PID）。

### cancel-run.stream.json（用户中途取消）

- **触发**：正常 prompt，PowerShell 启动 node cli.js，15 秒后 `taskkill /T /F` 杀树（语义=用户在 agent 工作中主动取消，区别于 timeout 的外部截止）。
- **结果**：3 行 = system + assistant（thinking：分析任务、规划工作流）+ assistant（tool_use：`classify_game_type`），**无 result 事件**。
- **关键契约要点**：cancel 在 stream-json 层面 = **流被截断在工具调用中、无 `type:result`**。与 timeout 输出形态相似（都是无 result 的中断流），区别在**触发语义**和**中断时机**（cancel 在有用工作之后、timeout 在截止前）。C09/C10 需靠 Executor 层的触发原因（timeout vs cancel API 调用）区分 `timed_out` vs `cancelled`，而非靠 stream-json 内容本身区分。
- **output tree**：空（agent 还在分类阶段，未写文件）。

### 跨 fixture 的契约要点汇总（给 C09/C10）

1. **`result.is_error` 不可信**（failure 证明）：opengame 把 provider 错误包成 success。判失败要靠 `[API Error:...]` 文本 + `usage.input_tokens==0` + 无 artifact。
2. **`success` 不等于有产物**（invalid-output 证明）：run 报 success 但零文件。OpenGameAdapter 必须独立校验 artifact 存在性。
3. **timeout/cancel 在 stream-json 层无终结事件**（timeout/cancel 证明）：无 `type:result` = 被中断。`timed_out` vs `cancelled` 的区分**不能靠 stream 内容**，必须靠 Executor 层的触发原因（C09 知道是 timeout 到期还是 cancel API 调用），C10 据此映射 `GameBuildStatus`。
4. **被中断时可能有 partial artifact**（timeout 证明）：杀进程时 agent 可能已写部分文件。C13 隔离/Candidate 导入必须拒绝 partial 产物，不得当 Playable。
5. **进程树取消机制**：Windows 上 `taskkill /T /F /PID <真实node PID>` 可杀整树；C09 Executor 在 Windows 用同机制，Linux 用 `os.killpg`。git-bash `$!` 不可靠，要用能拿真实 PID 的方式。
