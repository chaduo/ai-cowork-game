# AI Cowork Game V1/V2 两人共同审阅指南

**审阅目标**：在生成任务清单和开始编码之前，由两名开发者共同确认 V1 OpenGame baseline、
V2 Claude Agent Runtime、关键语义、验收方式与交付节奏。

**建议时长**：90 分钟

**完成标志**：本文末尾的“共同确认结论”和“Go/No-Go 清单”全部填写完成。

## 阅读原则

- 重点审阅用户价值、流程、边界、失败处理和可验证结果，不逐字讨论措辞。
- 英文固定标题、API 字段、枚举、文件路径和代码标识不需要翻译或逐项争论。
- 任何新增功能都必须说明它如何直接保护结项核心闭环；否则放入结项后清单。
- 发现冲突时遵循 Constitution 优先级：安全与数据保护、可运行和可恢复、端到端闭环、用户
  体验、扩展性、非必要功能。
- 会上必须形成明确结论、负责人和截止日期，不使用“之后再看”作为审阅结果。

## 两人角色

审阅时使用“主讲人 + 质疑人”模式，每个主题交换一次角色。

| 角色 | 责任 |
|------|------|
| 开发者 A | 主讲用户流程、前端、在线体验和演示脚本；质疑后端复杂度与时间风险 |
| 开发者 B | 主讲后端、Agent、Docker、Git 版本和失败恢复；质疑交互完整性与验收可见性 |
| 两人共同 | 决定范围取舍、接口语义、成功标准、负责人和截止日期 |

如果实际分工不同，可直接修改上表；重要的是每个主题必须有人主讲，也必须有人从失败角度挑战。

## 文档地图

| 顺序 | 文档 | 建议时间 | 主要问题 | 审阅产出 |
|------|------|----------|----------|----------|
| 1 | [constitution.md](../../.specify/memory/constitution.md) | 5 分钟 | 哪些原则绝不能为了赶进度牺牲？ | 冲突优先级一致 |
| 2 | [spec.md](spec.md) | 20 分钟 | 用户到底能完成什么，哪些明确不做？ | MVP 范围签字 |
| 3 | [plan.md](plan.md) | 20 分钟 | Vue/FastAPI 单体是否足够简单并覆盖闭环？ | 架构和目录确认 |
| 4 | [data-model.md](data-model.md) | 10 分钟 | Git 版本、成功指针、失败恢复是否无歧义？ | 版本语义确认 |
| 5 | [game-agent-adapter.md](contracts/game-agent-adapter.md) 与 [agent-profile-policy.md](contracts/agent-profile-policy.md) | 10 分钟 | 两种 Adapter 与四类 Agent 权限是否可实现？ | 最早验证项确认 |
| 6 | [openapi.yaml](contracts/openapi.yaml) | 5 分钟 | 前后端关键动作是否都有接口？ | 接口缺口清单 |
| 7 | [quickstart.md](quickstart.md) | 15 分钟 | 每个演示动作能否被重复验证？ | 验收与演示脚本确认 |
| 8 | 本指南 | 5 分钟 | 谁在什么日期前交付什么？ | Go/No-Go 结论 |

`research.md` 用于追溯技术决策理由，不建议在第一次会议中逐段阅读。出现技术争议时再打开
[research.md](research.md) 对应章节。

统一性能和可靠性对比只审阅 [runtime-benchmark.md](contracts/runtime-benchmark.md) 的输入与字段；
不在评审会上争论哪一个后端理论上更强。

## 第一关：范围与演示闭环

两人共同逐项回答“是/否”：

- [ ] 用户能从一句创意开始，而不是从上传现有工程开始。
- [ ] GDD 与 GameSpec 都能查看和确认。
- [ ] 素材生成失败时使用内置占位素材，仍能完成演示。
- [ ] 固定模板包含玩家移动、敌人生成/追踪、生命值、道具、计分和胜负条件。
- [ ] 至少一个 NPC 具有名称、定位、外观、位置、确定性行为和对话。
- [ ] 用户能通过 AI 增量修改现有项目。
- [ ] 用户能通过 Monaco 修改 GameSpec 或白名单源码。
- [ ] 每次修改创建 Candidate 并重新构建；通过门禁后才发布 Version。
- [ ] 构建失败时，iframe 继续展示最近成功版本。
- [ ] 用户能恢复一个成功版本。
- [ ] 在线系统和完整演示视频都属于结项完成条件。
- [ ] 成功 Version、accepted Asset 和成功 Experience 能经过人工门禁成为可复用资源。
- [ ] 归档项目 A 后可顺序创建项目 B，且产品任一时刻仍只有一个活动项目。

必须明确拒绝：

- [ ] Unity、3D、多模板和多游戏类型。
- [ ] LLM 自由编排、动态创建未审阅 Agent、Agent 微服务、多用户协作、社区和市场。
- [ ] 实时大模型 NPC、开放式对话和复杂记忆。
- [ ] 在线终端、任意命令和完整 IDE。
- [ ] Redis、任务队列、微服务、Kubernetes 和复杂账号权限。
- [ ] 三浏览器自动化、生产级监控和复杂备份平台。
- [ ] 自动模板提取、向量检索、经验聚类、自动 Skill 晋升和资源市场。

**本关结论**：

```text
范围是否冻结：是 / 否
若否，唯一待处理问题：
负责人：
最晚决定日期：
```

## 第二关：关键产品语义

### GDD 与 GameSpec

- GDD 未确认前不得生成 GameSpec。
- GameSpec 未确认前不得生成游戏代码。
- Monaco 修改 GameSpec 后必须再次校验并构建。
- 不支持的创意或修改必须明确拒绝，不能静默生成另一种游戏。

### 单任务

- 全平台任一时刻只有一个活动任务。
- 新任务遇到活动任务时返回 `409 task_running`，不排队。
- 刷新页面只是重连 SSE，不得重复启动任务。

### 版本与恢复

- `latest_candidate_id` 表示最新候选/编辑快照。
- `playable_version_id` 表示最近构建和结构化测试成功的 Version。
- 失败 Candidate 可以保留诊断，但不能改变 `playable_version_id`。
- retry/resume 从最近成功 commit 创建新 run，并从头执行原需求。
- restore 从用户选择的成功 commit 创建新版本，不改写 Git 历史。

### 素材回退

- 外部素材成功：记录为 `generated` 或 `integrated`。
- 外部素材失败：记录警告并使用 `builtin_placeholder`。
- 占位素材是正式 MVP 回退路径，不算演示失败。

**本关需要两人明确说出并接受的一句话**：

> 失败恢复不是断点续跑，而是从最近成功版本重新执行；素材失败可以使用内置占位素材继续。

### V1/V2 Runtime

- V1 使用 OpenGameAdapter 建立可运行 baseline 和 benchmark。
- V2 使用 Claude Agent SDK，实现 PlanningAgent、AssetAgent、CodingAgent 和 TestAgent。
- 四类 Agent 是受控 profile/session，不是四个微服务，也不能自行编排业务阶段。
- FastAPI 独占 GDD Confirm、GameSpec Confirm、Asset Accept、Test PASS 和 Version Publish。
- OpenGame 在 V2 保留为 fallback/reference/benchmark；只有 OpenGame 可用不代表 V2 完成。
- Candidate 可失败和修复；只有有效 PASS TestReport 才能发布不可变 Version。
- Template、Experience 和 Reusable Asset 都必须人工批准并保留来源证据。
- CodingAgent 只能读取 `available` Experience；单次成功 Run 不能自动修改 Formal Skill。

## 第三关：技术方案

| 决策 | 已确认 | 需要验证的风险 |
|------|--------|----------------|
| Vue 3 + TypeScript + Vite 前端 | [ ] | Monaco 加载与 iframe 预览是否可在同一页面稳定工作 |
| FastAPI + Python 3.11+ 后端 | [ ] | 单 worker 与长任务取消是否符合预期 |
| 标准库 sqlite3 + 显式 SQL | [ ] | 事务能否可靠保护 active run 与 playable 指针 |
| 每项目独立目录 + Git commit | [ ] | 工作区导出/导入是否不会暴露可信 `.git` |
| Python GameAgentAdapter | [ ] | OpenGameAdapter 的真实参数、输出、退出码和取消方式 |
| Claude Agent SDK + Python Runtime | [ ] | session 生命周期、流式事件、取消与工具权限能否满足契约 |
| 四类 Agent profile/tool policy | [ ] | 禁止工具、Workspace 越界和业务状态写入是否可被可靠拒绝 |
| Candidate + TestReport + Version | [ ] | 缺项 PASS、修复 attempt 和发布事务是否无歧义 |
| Reusable Resource Catalog | [ ] | 跨顺序项目复制、证据门禁和 ResourceUse 是否可验证 |
| FastAPI SSE + EventSource | [ ] | 刷新重连是否补发少量遗漏消息 |
| Docker 隔离工作区 | [ ] | 安装依赖所需网络与密钥注入边界 |
| 单 Chromium Playwright 冒烟 | [ ] | 如何稳定触发移动、NPC 对话和胜负条件 |
| 单 Linux + Docker Compose | [ ] | 主机是否能启动受限 run 容器并持久化数据 |

OpenGame 接入必须是最早的技术验证项之一。两人需要在开始大量界面开发前确认：

1. 能从子进程启动真实 OpenGame。
2. 能指定工作目录并让它修改固定模板。
3. 能读取足够的 stdout/stderr 形成阶段日志。
4. 能在超时或取消时停止进程和子进程。
5. 能获得修改文件或明确错误。

任一项不成立时，必须立刻记录降级方案，不能等到演示前处理。

Claude Runtime 进入实现前还必须确认：

1. Claude Agent SDK 能创建、取消并追踪与平台 session 一一映射的执行。
2. 四类 Agent 能分别加载独立 system instructions、Skills 和 tool allowlist。
3. Claude 原生事件能够稳定转换为 RunEvent，而不让前端依赖 SDK 格式。
4. TestAgent 能输出结构化 TestReport，平台能拒绝缺项或无证据的 PASS。
5. FAIL → CodingAgent repair → TestAgent retest 由 FastAPI 驱动并受预算限制。

## 第四关：安全与失败路径

- [ ] OpenGame、npm 和构建只在 run 工作区执行。
- [ ] 执行容器看不到平台源码、其他项目、用户主目录和宿主凭证。
- [ ] 密钥不会写入 Git、构建日志或公开产物。
- [ ] Monaco 后端白名单拒绝绝对路径、`..`、符号链接逃逸和受保护文件。
- [ ] 页面不提供终端或任意命令输入。
- [ ] 取消 run 后没有遗留 OpenGame 子进程或构建容器。
- [ ] npm 安装失败、TypeScript 失败、页面启动失败和冒烟失败都会保留成功版本。
- [ ] 后端重启时，未终结 run 会被标记失败，并允许从最近成功版本重试。

**安全阻塞项**：任何可能让生成代码访问宿主凭证、平台源码或其他项目的问题都必须在实现前
解决，不能作为结项后优化。

## 第五关：验收与演示

共同对照 [quickstart.md](quickstart.md)，确认演示至少包括：

1. 输入一句创意。
2. 查看并确认 GDD。
3. 查看并确认 GameSpec。
4. 观察 AI 阶段、状态和日志。
5. 使用生成或占位素材完成构建。
6. 在 iframe 中试玩完整生存循环和 NPC 对话。
7. 通过 AI 修改规则或 NPC，并试玩新版本。
8. 通过 Monaco 修改白名单源码，并重新构建。
9. 演示一次构建失败，证明旧版本仍可玩。
10. 恢复一个成功历史版本。
11. 切换 Claude Runtime，复现创建和增量修改闭环。
12. 演示 Test FAIL、CodingAgent repair、TestAgent retest 和最终 PASS。
13. 晋升 Template、跨顺序项目复用 Asset，并让 CodingAgent 读取一条成功 Experience。

冒烟测试只需要 Chromium，但必须稳定验证：

- [ ] 页面和 canvas 已启动。
- [ ] 没有阻断控制台错误。
- [ ] 玩家能够移动。
- [ ] NPC 对话能够触发。
- [ ] 至少一个胜利或失败条件能够触发。

## 建议时间线

| 日期 | 必须完成的结果 | 建议负责人 |
|------|----------------|------------|
| 08-10 | V1/V2 文档、Adapter 和发布语义冻结 | 两人 |
| 08-11 | FakeAdapter 跑通人工门禁和 Candidate → TestReport → Version | 两人联合 |
| 08-12 | Phaser 模板、Docker build 和 Chromium gate | 游戏/测试负责人 |
| 08-13 | 真实 OpenGame baseline 与三次 benchmark | Runtime 负责人 |
| 08-14 | Claude SDK session/event/tool policy spike + Planning/Asset | Claude Runtime 负责人 |
| 08-15 | CodingAgent create/modify 与 Candidate | Runtime/游戏负责人 |
| 08-16 | TestAgent 与 FAIL → repair → retest → PASS | 测试负责人 |
| 08-17 | V2 统一基准、Template/Asset/Experience 复用和完成状态评审 | 两人 |
| 08-18 | 在线部署、三次演练、录制与说明文档 | 两人 |
| 08-19 | 汇报缓冲；冻结功能并归档证据 | 两人 |

负责人必须替换成真实姓名或固定代号，不能一直保留“A/B 分工”。

## 决策记录

会议中遇到分歧时填表；不要只写在聊天记录里。

| ID | 主题 | 可选方案 | 最终决定 | 理由 | 负责人 | 截止日期 |
|----|------|----------|----------|------|--------|----------|
| D-01 | | | | | | |
| D-02 | | | | | | |
| D-03 | | | | | | |
| D-04 | | | | | | |
| D-05 | | | | | | |

## 共同确认结论

```text
MVP 范围已冻结：是 / 否
Vue 3 + FastAPI 技术栈已确认：是 / 否
OpenGame 子进程适配边界已确认：是 / 否
Claude Agent SDK 为 V2 强制交付已确认：是 / 否
四类 Agent 权限边界已确认：是 / 否
FastAPI 独占业务状态机已确认：是 / 否
Candidate/TestReport/Version 语义已确认：是 / 否
单任务且不排队已确认：是 / 否
失败从最近成功版本重跑已确认：是 / 否
素材失败使用占位素材已确认：是 / 否
单 Chromium 冒烟范围已确认：是 / 否
2026-08-19 在线系统与视频交付已确认：是 / 否
V2 三类可复用资源最低演示已确认：是 / 否
单次 Run 不会自动修改 Formal Skill：是 / 否

开发者 A：____________  日期：____________
开发者 B：____________  日期：____________
```

## Go/No-Go 清单

只有全部满足时才生成 `tasks.md` 并进入实现：

- [ ] 两人均完整阅读 spec 和 plan。
- [ ] 所有范围分歧已有最终结论。
- [ ] OpenGame 和 Claude SDK spike 的负责人及最晚完成日期已确定。
- [ ] V1/V2 分别具有可独立验收的完成标准。
- [ ] 四类 Agent 的 system instructions、Skills 和工具权限有明确负责人。
- [ ] Candidate/TestReport/Version 与 repair/retest 语义没有歧义。
- [ ] Template/Experience/Reusable Asset 的来源证据、人工门禁和跨项目隔离没有歧义。
- [ ] 前端、后端、游戏模板、部署和演示视频均有负责人。
- [ ] 失败保护与恢复语义没有歧义。
- [ ] 安全边界没有待定的高风险问题。
- [ ] 首个纵向闭环的完成日期已确定。
- [ ] 功能冻结、部署、演练和录制日期已确定。
- [ ] 两人同意结项前不新增非必要功能。

若任一项未满足，结论为 **No-Go**：先解决该项，再进入实现。全部满足后结论为 **Go**，下一步
使用 `$speckit-tasks` 将 V1 baseline 与 V2 Claude Runtime 拆成依赖明确、可分工和可验收的任务。
