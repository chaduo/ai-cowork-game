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
