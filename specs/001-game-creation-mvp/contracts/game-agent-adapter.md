# GameAgentAdapter 契约 v2

**目的**：使 FastAPI 业务工作流不依赖 OpenGame 或 Claude Agent SDK 的供应商实现，同时允许
Platform V1 建立 OpenGame baseline，Platform V2 使用 Claude Runtime 成为主要后端。

## 平台所有权

FastAPI 是唯一业务状态机，负责创建 run/session、推进阶段和裁决门禁。Runtime 或 Agent 不得
自行确认 GDD、确认 GameSpec、接受素材、判定 Test PASS 或发布 Version。

```text
FastAPI Workflow
├── OpenGameAdapter                 # V1, fallback, reference, benchmark
└── ClaudeRuntimeAdapter            # V2 primary
    ├── PlanningAgent
    ├── AssetAgent
    ├── CodingAgent
    └── TestAgent
```

## 稳定 Adapter 接口

```python
class GameAgentAdapter(Protocol):
    async def plan_gdd(self, command: PlanGddCommand) -> AgentSessionHandle: ...
    async def plan_gamespec(self, command: PlanGameSpecCommand) -> AgentSessionHandle: ...
    async def create_assets(self, command: AssetCommand) -> AgentSessionHandle: ...
    async def create_game(self, command: CreateGameCommand) -> AgentSessionHandle: ...
    async def modify_game(self, command: ModifyGameCommand) -> AgentSessionHandle: ...
    async def repair_candidate(self, command: RepairCommand) -> AgentSessionHandle: ...
    async def test_candidate(self, command: TestCommand) -> AgentSessionHandle: ...
    async def resume_from_version(self, command: ResumeCommand) -> AgentSessionHandle: ...
    async def stream_events(self, handle: AgentSessionHandle) -> AsyncIterator[RuntimeEvent]: ...
    async def get_status(self, handle: AgentSessionHandle) -> RuntimeStatus: ...
    async def cancel(self, handle: AgentSessionHandle) -> None: ...
    async def get_result(self, handle: AgentSessionHandle) -> AgentResult: ...
```

`OpenGameAdapter` 可以把多个方法映射到同一个外部能力，但必须返回相同的结构化结果。
`ClaudeRuntimeAdapter` 必须使用相应的领域 Agent profile/session，不能用一个无限权限通用 Agent
代替四种角色。平台代码只依赖 `GameAgentAdapter`；Runtime 是实现属性，不另建一套平行接口。
`AgentResult` 必须统一携带状态、产物引用和结构化错误；Adapter 不得要求业务层解析原始 stdout
或供应商异常。`resume_from_version` 只接收平台准备好的成功 Version 工作区，不表示续接供应商
session 或阶段检查点。

## 通用命令上下文

| 字段 | 含义 |
|------|------|
| `run_id` | 平台 run ID |
| `agent_session_id` | 平台预先创建的 session ID |
| `project_id` | 项目 ID |
| `runtime_backend` | `opengame` 或 `claude` |
| `workspace_path` | Agent 唯一可访问的项目目录 |
| `baseline_version_id` | 干净稳定基线 |
| `candidate_id` | 当前 Candidate，规划阶段可为空 |
| `gamespec_path` | 已确认 GameSpec 相对路径 |
| `allowed_paths` | 可读写路径策略 |
| `allowed_tools` | 可调用工具/MCP allowlist |
| `timeout_seconds` | 强制超时 |
| `budget` | 调用、token、成本与 repair attempt 上限 |
| `approved_experience_ids` | 平台筛选后允许 CodingAgent 只读的经验；默认空列表 |

## Agent Profiles

### PlanningAgent

- 输入：创意、已确认 GDD（生成 GameSpec 时）、固定游戏范围。
- 输出：`GddDraft` 或 `GameSpecDraft`、范围诊断和假设。
- 禁止：源码写入、素材接受、测试裁决和版本发布。

### AssetAgent

- 输入：已确认 GameSpec、素材策略和占位素材目录。
- 输出：`AssetManifestDraft`、来源/授权说明和预览引用。
- 禁止：自动接受素材、修改平台源码和版本发布。

### CodingAgent

- 输入：已确认 GameSpec、已接受素材、基线 Version、用户修改或 TestReport 失败证据。
- 输出：允许路径内的源文件变更、修改摘要和 Candidate metadata。
- 禁止：修改业务状态、扩大路径权限、自行宣布测试成功。

### TestAgent

- 输入：只读 Candidate、测试策略和确定性测试工具。
- 输出：结构化 TestReport。
- 禁止：修改代码、降低必需检查、触发 repair 或发布 Version。

## TestReport

```python
class CheckResult(BaseModel):
    check_id: Literal[
        "build", "page_load", "console_errors", "player_movement",
        "enemy_loop", "item_collection", "npc_interaction", "game_outcome"
    ]
    status: Literal["pass", "fail"]
    evidence: list[str]
    message: str | None = None

class TestReport(BaseModel):
    candidate_id: str
    agent_session_id: str | None = None
    attempt: int
    checks: list[CheckResult]
    failed_checks: list[str]
    verdict: Literal["pass", "fail", "invalid"]
    created_at: datetime
```

Python model 使用 snake_case，API/JSON 按 schema alias 输出 camelCase。平台必须验证八个
`check_id` 各出现且只出现一次、证据路径、`failed_checks` 一致性和真实命令退出码。缺少任一必需项的 PASS 报告按
`invalid` 处理。只有平台验证后的 PASS 才能触发 Version Publish。

## RunEvent 规范化

Adapter 必须将供应商原生事件转换为 [run-event.schema.json](run-event.schema.json)，并填充可用的
`agentType`、`agentSessionId`、`backend`、`toolName`、`toolCallId`、`candidateId`、`attempt` 和
usage。原始 stdout、Claude SDK event 或工具参数不得直接返回前端；持久化前执行长度限制、
路径清洗和密钥脱敏。

## OpenGameAdapter

- 通过 `asyncio.create_subprocess_exec` 调用固定版本 OpenGame CLI，禁止 `shell=True`。
- 使用显式参数、固定工作目录、环境变量白名单、超时和进程组取消。
- 建立 V1 create/modify/build/test baseline，并输出 benchmark 数据。
- V2 上线后继续作为 fallback/reference backend，不删除契约测试。

## ClaudeRuntimeAdapter

- 使用 Claude Agent SDK 的 `ClaudeSDKClient` 创建与平台 `agent_session_id` 一一映射的受控 session；
  一次性无工具规划允许在 Adapter 内使用 `query()`。
- 每个 Agent profile 使用独立 system instructions、Domain Skills、工具 allowlist 和 Workspace 权限。
- `allowed_tools` 仅表示自动批准，不视为工具隔离；实现必须再使用 `disallowed_tools`、
  `can_use_tool` 或 `PreToolUse` 拒绝策略，并以 Docker 挂载和路径白名单兜底。
- MCP 只能通过平台批准的 gateway 注册；业务状态写操作不作为 Agent 工具暴露。
- SDK session 中断时保留映射、事件和 Candidate；是否重试由 FastAPI 决定。
- Claude 原生事件只能经规范化层进入 RunEvent 和 usage 记录。

## Repair 与恢复

- `repair_candidate` 接收失败 Candidate 和有效 TestReport，创建新的 Candidate attempt。
- repair 次数、时长与成本由 FastAPI budget 限制；Agent 不能自行循环。
- retry/resume 默认从最近成功 Version 和原始需求创建新 run。
- restore 从用户选择的成功 Version 创建 Candidate，重新构建测试后发布新 Version。

## 必要契约测试

- OpenGame 与 Claude Runtime 均通过统一 create/modify/repair/test 契约测试。
- 四类 Claude Agent 的禁止工具、越界路径和业务状态写入均被拒绝并记录 audit event。
- 原生事件稳定转换为 RunEvent，session/run/candidate 关联完整。
- TestReport 缺项、伪造证据或命令失败时不能发布 Version。
- cancel 终止 session/进程/容器，终止后不得继续产生可接受事件。
- 已知测试密钥不会出现在事件、日志、TestReport 或产物中。
- Fake Runtime 无需修改 FastAPI 工作流即可通过同一套平台测试。

各 Agent 的具体 instruction、Skill、工具/MCP 权限见
[agent-profile-policy.md](agent-profile-policy.md)；TestReport 的机器边界见
[test-report.schema.json](test-report.schema.json)。
