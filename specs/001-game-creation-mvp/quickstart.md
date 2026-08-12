# 快速验证指南：AI 游戏共创平台 V1/V2

**目的**：验证 Vue 3 + FastAPI MVP 能够从本地启动走到在线结项演示。

## 前置条件

- Python 3.11 或更新版本。
- Node.js 22 LTS 与 npm。
- Docker Engine、Docker Compose 和 Git。
- 通过 Playwright 安装 Chromium。
- V1：已固定版本的 OpenGame CLI/镜像。
- V2：已固定版本的 Claude Agent SDK、Claude 模型凭证和四类 Agent profile/tool policy。
- `game-template/public/placeholders/` 提供内置占位素材。

真实凭证必须保留在部署环境配置中，不得进入项目 Git、run 工作区、构建日志、生成游戏或公开
产物。

## 本地启动

### 后端

```bash
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
python backend/scripts/migrate.py
uvicorn backend.app.main:app --reload --workers 1
```

预期结果：

- 使用 [data-model.md](data-model.md) 中的精简 schema 初始化 `data/app.db`。
- 后端健康检查通过，并确认项目、工作区、产物和日志目录可写。
- Uvicorn 只使用一个 worker，因为 MVP 任务锁由单进程和 SQLite 共同保证。

### 前端

```bash
npm --prefix frontend ci
npm --prefix frontend run dev
```

预期结果：

- Vue 管理界面首先显示部署级访问码输入框。
- 解锁后，浏览器能够调用 FastAPI API 并连接 SSE 接口。
- Monaco 只为 GameSpec 和白名单游戏源码加载。

### 游戏模板

```bash
npm --prefix game-template ci
npm --prefix game-template run typecheck
npm --prefix game-template run build
npx --prefix game-template playwright install --with-deps chromium
```

预期结果：

- 固定 Phaser 3 生存游戏模板构建成功，界面不提供其他游戏类型选择。
- 内置玩家、敌人、道具、背景和 NPC 占位素材完整存在。

## 自动化检查

只运行结项闭环需要的检查：

```bash
. .venv/bin/activate
pytest backend/tests
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix game-template run typecheck
npm --prefix game-template run build
npm --prefix game-template run test:smoke
```

后端测试覆盖：

- 访问码和签名 cookie。
- SQLite 项目、run、版本与消息 repository。
- 全局单任务的 `409` 行为。
- Candidate 创建、TestReport 校验、PASS 后 Git Version 发布，以及 playable 指针保护。
- 白名单文件保存、路径穿越和受保护路径拒绝。
- OpenGameAdapter 和 ClaudeRuntimeAdapter 契约、规范化事件、超时与取消。
- Planning/Asset/Coding/Test Agent 工具权限和 Workspace 越界拒绝。
- Test FAIL → repair → retest → PASS 的次数、时间和成本限制。
- Template/Asset/Experience 晋升门禁、兼容标签、ResourceUse 和未审阅资源拒绝。
- 单次成功 Run 只能创建 Skill Candidate，不能修改 Formal Skill。
- 从最近成功 commit 执行 retry/resume。
- 失败构建保持可玩版本不变。

自动化浏览器只使用 Chromium。冒烟测试覆盖页面/canvas 启动、无阻断控制台错误、真实玩家
移动、一次 NPC 对话，以及至少一个胜利或失败结果。

## 场景一：从创意到可玩游戏

1. 使用部署访问码解锁管理页面。
2. 创建项目并提交一句有效游戏创意。
3. 通过 SSE 观察唯一 run ID、阶段和消息。
4. 查看并确认生成的 GDD。
5. 查看并确认生成的 GameSpec。
6. 让系统生成或选择素材、修改固定模板、安装 npm 依赖并构建。
7. 在 iframe 中打开游戏并完成试玩。

预期结果：

- V1 使用 OpenGame backend 完成 Candidate、构建、TestReport 和 Version 发布。
- GDD、GameSpec 和素材均经过平台门禁，Agent 无法自行跳过确认。
- 只有 PASS Candidate 成为可玩 Version。
- GDD 包含目标、核心玩法、玩家、敌人、道具、NPC、胜负条件和美术风格。
- GameSpec 通过共享 schema 校验，并包含至少一个确定性 NPC。
- 素材生成失败时，系统发出警告并使用内置占位素材，不中断整个核心流程。
- 第一个成功 Git Version 成为 `playable_version_id`，iframe 加载其产物目录。
- 玩家移动、敌人生成/追踪、生命值、道具收集、计分、NPC 对话和胜负路径均可运行。

## 场景一-B：Claude Runtime 完成同一闭环

1. 将部署配置中的 runtime backend 设为 `claude`。
2. 提交与 V1 benchmark 相同的有效创意。
3. 确认 PlanningAgent 先提交 GDD，人工确认后才提交 GameSpec。
4. 确认 AssetAgent 生成素材清单，人工接受后才启动 CodingAgent。
5. 检查 CodingAgent 只修改 Candidate Workspace 内的授权文件。
6. 检查 TestAgent 输出结构化 TestReport，平台验证 PASS 后发布 Version。
7. 提交一次增量修改，验证用户流程与 V1 相同。

预期结果：

- run 详情显示 backend、四类 Agent session、工具调用、用量和 Candidate/TestReport 关联。
- Claude 原生事件不会直接暴露给前端，而是以 RunEvent 展示。
- OpenGame 和 Claude Runtime 使用相同 GameSpec、测试和发布门禁。

## 场景二：单任务与 SSE 重连

1. 启动一个受控的长时间 AI 修改。
2. 在任务运行期间再次提交修改或 Monaco 保存。
3. 刷新浏览器并重新连接原 run。

预期结果：

- 第二个修改返回 `409 task_running`，不会进入队列。
- 页面重新加载已保存消息，并从最后 sequence 继续 SSE，且不创建新 run。
- SQLite 只保存少量用户可见消息；完整构建输出保留在 run 日志文件中。

## 场景三：AI 增量修改

1. 记录当前可玩版本和 Git commit。
2. 要求 AI 修改一个受支持的游戏规则或 NPC 对话/行为。
3. 查看版本摘要、修改文件、日志和更新后的预览。

预期结果：

- OpenGame 通过 `OpenGameAdapter`（实现 `GameAgentAdapter`）以子进程运行，并编辑复制出来的工作区。
- 修改是增量的，且仅涉及项目/模板白名单。
- 创建新 Git commit/版本；只有构建和冒烟测试通过后才更新可玩指针。

## 场景四：Monaco 编辑与构建失败

1. 在 Monaco 中打开 `game-spec.json` 或一个允许编辑的源码文件。
2. 保存有效修改并确认产生新版本/构建。
3. 在允许编辑的文件中保存一个有意制造的编译错误。
4. 查看失败 Candidate 和构建日志位置。

预期结果：

- Monaco 不提供终端或任意命令操作。
- 绝对路径、`..`、符号链接逃逸、受保护模板文件和非白名单文件均被拒绝。
- 失败 Candidate 可见，但 iframe 仍加载之前的成功产物。
- 错误输出在可获取时包含相关文件/位置，并且经过脱敏。

## 场景五：取消与简单恢复

1. 在 OpenGame 或构建工作运行时取消 run。
2. 确认子进程组/容器已经停止。
3. 对取消或失败 run 选择 retry/resume。

预期结果：

- 原 run 变为 `cancelled`，成功版本指针不变。
- 恢复创建一个关联的新 run，导出最近成功 Git commit，并从头执行原始需求。
- 不复用检查点、部分工作区或 Agent 内部状态。

## 场景六：版本恢复

1. 创建至少两个成功 Version 和一个失败 Candidate 的小型历史。
2. 选择一个已显示的成功版本并执行恢复。

预期结果：

- 每条记录展示来源、需求、摘要、修改文件、commit、构建状态、日志和产物路径。
- 恢复从所选成功 commit 创建新 commit/版本，然后重新构建和冒烟测试。
- Git 历史不被改写；恢复失败时，之前的可玩版本保持不变。

## 场景七：隔离与密钥安全

使用受控测试 fixture 尝试读取绝对宿主路径、其他项目、平台源码、凭证、受保护文件和不允许的
网络目标。

预期结果：

- 每个 Agent 只能调用自身 allowlist 中的工具和 MCP gateway。
- 尝试写业务状态、越过 Workspace 或使用未授权工具会被拒绝并生成 audit event。
- TestAgent 无权修改代码或发布 Version。
- runner 只能看到自身工作区，不能挂载可信项目 Git 仓库。
- 资源与超时限制能够停止失控任务。
- 已知测试密钥不会出现在 SQLite 消息、展示日志、Git commit 或公开产物中。
- npm/OpenGame 命令由平台固定，用户不能提供任意 shell 命令。

## 场景八：V2 修复与重测

1. 使用 Claude Runtime 创建一个可构建但会在 NPC 或胜负条件测试失败的 Candidate。
2. 确认 TestAgent 输出 FAIL TestReport 和证据。
3. 由平台启动 CodingAgent repair，而不是由 TestAgent 直接修改代码。
4. 创建新的 Candidate attempt，并由 TestAgent retest。
5. 最终 PASS 后发布 Version。

预期结果：

- repair/retest 次数不超过平台预算。
- 每个 attempt、Agent session 和 TestReport 均保留。
- 修复期间 iframe 继续展示最近成功 Version。

## 场景九：V2 可复用开发知识

1. 从一个具有有效 PASS TestReport 的成功 Version 执行人工 Template 晋升。
2. 将项目内一个已接受、来源与许可完整的 Asset 保存为 Reusable Asset。
3. 从刚完成的成功 repair run 创建 Development Experience，填写适用条件和修改摘要并人工批准。
4. 归档项目 A，顺序创建项目 B，并使用该 Template 作为兼容起点。
5. 将 Reusable Asset 复制到项目 B，触发构建并检查外观或 manifest 引用。
6. 在项目 B 发起相关修改，检查 CodingAgent 通过 `get_approved_experiences` 读取该 Experience。
7. 尝试从 Experience 创建 Skill Candidate，检查 Formal Skill 目录和注册保持不变。

预期结果：

- Template 关联来源 Version、PASS TestReport、`phaser-survival-v1` 和 GameSpec schema 版本。
- Asset 保留类型、风格、prompt、provenance、许可说明和来源 Version。
- 项目 B 获得资源副本而非项目 A 路径；Template、Asset、Experience 分别产生 ResourceUse。
- CodingAgent 看不到项目 A Workspace，只收到已批准 Experience 的结构化内容与证据引用。
- 未发布 Version、未接受 Asset、无 PASS 证据 Experience 和不兼容 capability 均被拒绝。
- 不运行向量检索、聚类、自动模板提取或自动 Skill 晋升。

## Docker Compose 在线部署

```bash
docker compose -f deploy/compose.yaml up -d --build
curl --fail https://example.test/health
```

预期结果：

- 一台 Linux 主机提供 Vue 管理页面、FastAPI API/SSE 和版本化游戏产物。
- SQLite 与 `data/projects`、`data/artifacts`、`data/resources`、`data/logs` 使用配置的持久卷。
- 容器配置重启策略、基本健康检查、资源限制和日志轮转。
- 不存在 Redis、任务队列、Kubernetes、外部数据库、多 Agent 服务或生产监控栈。

## 最终演示门禁

在 2026-08-19 前：

1. 锁定 Python、npm、OpenGame、Claude Agent SDK 和容器版本。
2. 准备一个稳定演示创意、内置占位素材和一个成功兜底游戏。
3. 连续完成三次 Chromium 演练，覆盖创意到试玩、AI 修改、Monaco 编辑、NPC 修改、失败保护
   和版本恢复。
4. 从干净浏览器验证在线网址。
5. 录制并检查完整演示视频和项目说明。
6. 使用 Claude Runtime 完成一次创建、一次增量修改和一次 FAIL → repair → retest → PASS。
7. 保留同一验收输入下的 OpenGame baseline 与 Claude Runtime 对比记录。
8. 演示一个 Template 晋升、一个 Asset 在顺序项目中复用，以及一条 Experience 被 CodingAgent 使用。

对比记录必须遵循 [runtime-benchmark.md](contracts/runtime-benchmark.md)；四类 Agent 权限按
[agent-profile-policy.md](contracts/agent-profile-policy.md) 验证，TestAgent 输出按
[test-report.schema.json](contracts/test-report.schema.json) 校验。
Reusable resource 的机器字段按
[reusable-resource.schema.json](contracts/reusable-resource.schema.json) 校验。

V1 在 OpenGame baseline 稳定后完成；V2 只有在 Claude Runtime 跑通相同工作流、修复重测和版本
发布以及三类最小资源复用后才完成。只有 OpenGame 可用不能标记最终目标完成。项目不要求三浏览器矩阵、复杂备份
演练或生产监控上线。
