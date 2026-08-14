# AI Cowork Game V1 Change Catalog

> 状态：`Explore Ready`。本文件是 V1 roadmap、Change 边界和 OpenSpec Explore 的统一输入，
> 不是已经冻结的领域 Spec，也不能替代每个 Change 的 proposal/spec/design/tasks。

## 0. 如何使用本文件

### 0.1 当前仓库事实

截至 2026-08-13：

- `frontend/` 是 Vue 3 + TypeScript + Vite 的前端 Prototype。
- Prototype 已跑通以下产品行为：
  `Idea → Game Design → GameSpec → Build → Playable → Change → Version Restore → Publish → Release → Resource Review → 我的资源 → 新项目资源复用`。
- Prototype 的业务状态位于 `frontend/src/stores/projectStore.ts`，使用 deterministic local state 和 timers；它是交互行为参考，不是 V1 持久化架构。
- 主应用尚无 FastAPI、SQLite、BuildService、真实 artifact hosting 或 OpenGame runtime 实现。
- `openspec/changes/platform-v1-opengame-baseline/`、`openspec/config.yaml` 和 `specs/001-game-creation-mvp/contracts/` 是重要设计材料，但其中的单项目限制、固定 survival 范围、GameSpec schema 和自动 publication 语义与当前 Prototype 不完全一致。

### 0.2 事实源优先级

在 V1 alignment change 完成前，按以下优先级处理冲突：

1. 本文件中的已对齐 V1 产品语义与架构边界。
2. 当前 Prototype 中已经确认的用户行为和 Human Gate。
3. 经双方 Required Review 冻结后的 OpenSpec capability specs 与 JSON/OpenAPI contracts。
4. 现有 `platform-v1-opengame-baseline`、旧 `specs/001-game-creation-mvp` 和 Prototype 内部类型，作为待迁移材料而非自动真相源。

OpenSpec Explore 的第一项工作必须是显式列出冲突并决定更新、替换、sync 或 archive 哪一份旧 artifact；不得静默选择。

### 0.3 Catalog、OpenSpec 与 Superpowers

```text
V1 Change Catalog
        ↓ 选择一个 Change
Change Brief / OpenSpec Explore
        ↓
proposal + specs + design + tasks
        ↓ Human Review
Superpowers implementation plan
        ↓
Implementation + Verification + PR
```

- Catalog 回答 roadmap、Owner、依赖和 Change 边界。
- OpenSpec 是单个 Change 的需求、设计和 contract 事实源。
- Superpowers 负责实施计划、TDD、执行、review 和 verification。
- 禁止让 OpenSpec apply 与 Superpowers 同时负责同一份代码实现。
- 不要把 C01-C19 一次性创建为一个巨型 OpenSpec Change。

---

## 1. 已对齐的 V1 产品与领域语义

### 1.1 V1 产品范围

V1 支持：

- 单用户、多个 Project。
- Idea、Game Design、GameSpec 的独立 Human Gate。
- 使用 OpenGame 生成真实浏览器游戏 artifact。
- BuildCandidate 与当前 Playable 同时存在；失败不影响当前 Playable。
- 用户 Promote BuildCandidate 后才创建 PlayableVersion。
- 用户单独 Publish PlayableVersion 后才创建 Release。
- Release 后产生 ResourceCandidate batch；用户审核后保存到“我的资源”。
- 新项目可获得已保存玩法/UI/美术资源的确定性推荐；V1 只做明确 contract/规则匹配，不做语义 LLM 匹配。

V1 不支持：

- 多用户、团队权限和协作编辑。
- Marketplace、社区资源和团队资源库。
- 自研多 Agent runtime；它属于 V2。
- 分布式 worker、消息队列和通用 workflow engine。
- 任意游戏引擎或任意 runtime；V1 使用固定的浏览器游戏交付约束和 OpenGameAdapter。
- Agent 直接确认设计、Promote Playable、Publish Release 或保存资源。

### 1.2 唯一生命周期

```text
Project Created
      ↓
Game Design Draft ── Human Confirm
      ↓
GameSpec Draft ───── Human Confirm
      ↓
Build / OpenGame Run
      ↓
BuildCandidate
      ↓ build + TestReport PASS
Ready to Promote ─── Human Promote
      ↓
PlayableVersion
      ↓ optional Change / Restore creates a new BuildCandidate
Publish Draft ────── Human Publish
      ↓
Release
      ↓
ResourceCandidate Batch ── Human Save / Ignore
      ↓
SavedResource Library
```

关键规则：

1. `BuildCandidate`、`PlayableVersion`、`Release`、`ResourceCandidate` 是四个不同实体。
2. Build 成功只产生 BuildCandidate；Test PASS 只使其可 Promote，不自动更新 Playable。
3. Promote 创建不可变 PlayableVersion，并更新 Project 的 current playable pointer。
4. Publish 从指定 PlayableVersion 创建不可变 Release；后续 Change 不修改旧 Release。
5. Resource Review 的 Candidate 是 Release 内容提取候选，不是 BuildCandidate。
6. 失败、取消、不完整或非法结果不会改变 current Playable 或任何 Release。
7. Restore 不改写历史；它以旧 PlayableVersion 为输入创建新的 BuildCandidate，通过相同 gate 后成为新 PlayableVersion。

### 1.3 项目阶段与子状态

`Project.stage` 只用于 Projects 列表和顶层导航，建议值：

```text
design | gamespec | building | candidate_review | playable | released | attention
```

Build、Run、Game Design、GameSpec、Release、Resource Review 分别拥有自己的细粒度状态。禁止把所有 UI phase 塞进一个长期持久化枚举，也禁止仅依靠前端组件状态表示业务进度。

### 1.4 GameSpec 边界

V1 必须冻结一个 canonical backend GameSpec schema。当前三套结构不得继续并行演进：

- Prototype `GameSpecModel` 是创作者友好的编辑 ViewModel。
- `specs/001-game-creation-mvp/contracts/gamespec.schema.json` 是旧固定 survival runtime schema。
- Catalog 旧版最低字段列表不是正式 schema。

推荐边界：

```text
CreatorGameSpec (provider-neutral, product-owned)
        ↓ validated adapter mapping
RuntimeBuildSpec (OpenGame / fixed runtime input)
```

CreatorGameSpec 至少表达 metadata、build target、gameplay、characters/entities、world、rules/progression、visual direction、scope 和 validation；具体字段及版本兼容规则由 C05 冻结。OpenGame-specific prompt、命令、文件路径不得进入 CreatorGameSpec。

---

## 2. 架构边界

```text
Vue
 ↓ REST + SSE
FastAPI Application / Human Gates
 ↓
Domain Services + Repositories
 ↓
BuildService ──────────────→ Candidate / Test / Playable / Release Services
 ↓ GameAgent Contract
OpenGameAdapter
 ↓
OpenGameExecutor
 ↓ isolated workspace
OpenGame CLI
```

必须满足：

- FastAPI 是持久化业务状态与所有 Human Gate 的唯一 Owner。
- Vue 不根据 provider 日志自行推进业务状态。
- BuildService 只能依赖 GameAgent Contract，不能调用 OpenGame CLI。
- OpenGameAdapter 不修改 Project、PlayableVersion、Release 或资源库。
- Executor 不知道 Project、GameSpec、Candidate、Playable、Vue 或 FastAPI 业务模型。
- Runtime output 必须经过路径、安全、artifact 和 TestReport 校验后才能进入受信任状态。
- V2 替换 runtime 时，上层流程和 Candidate/Playable/Release gate 不应重写。

---

## 3. 角色分工

| 领域 | zhao | zhang |
|---|---|---|
| 产品流程与 Human Gate | Owner | Required Review |
| Vue 前端 | Owner | Review / 辅助 |
| FastAPI Application / API | Owner | Review |
| Domain Schema / Repositories | Owner | Required Review |
| GameSpec Contract | Owner | Required Review |
| BuildService | Owner | Required Review |
| GameAgent / RunEvent Contract | Owner | Required Review |
| OpenGame CLI Spike | Review | Owner |
| OpenGameExecutor | Review | Owner |
| OpenGameAdapter | Review | Owner |
| OpenGame Output / Event Mapping | Review | Owner |
| Runtime Isolation / Safety | Required Review | Owner |
| Candidate / TestReport Gate | Owner | Required Review |
| Playable / Release / Resource | Owner | Review |
| E2E 联调 | Owner | Required Review |
| Demo / V1 Release | Owner | 配合 |

协作规则：

- 每个 Change 只有一个写入 Owner；Reviewer 可以贡献测试或建议，但不形成双 DRI。
- Contract Change 必须由另一方 Required Review 后冻结。
- 同一核心 contract 未冻结时，不允许两条依赖分支各自修改它。
- zhao 拥有产品状态机与上层 contract，zhang 拥有 OpenGame/runtime 实现；边界通过 contract tests 对接。

---

## 4. V1 Change Catalog

状态初始均为 `Backlog`；只有依赖满足且对应 OpenSpec artifact 通过 Human Review 后才能进入 `Ready`。

| ID | Change | Owner | Reviewer | Depends On | 可并行说明 |
|---|---|---|---|---|---|
| C00 | `v1-contract-alignment` | zhao | **zhang Required Review** | 无 | 与 C08 CLI spike 并行 |
| C01 | `platform-backend-foundation` | zhao | zhang | C00 | 与 C08 并行 |
| C02 | `project-lifecycle-domain` | zhao | **zhang Required Review** | C00, C01 | 与 C08/C09 并行 |
| C03 | `create-project-flow` | zhao | zhang | C02 | 可与 C04 部分并行 |
| C04 | `projects-list` | zhao | zhang | C02 | 可与 C03/C05 并行 |
| C05 | `game-design-gamespec-flow` | zhao | **zhang Required Review** | C02, C03 | UI/API 可纵向推进 |
| C06 | `game-agent-contract` | zhao | **zhang Required Review** | C00, C05 schema freeze | 与 C07 event schema/fixtures 并行 |
| C07 | `run-event-observability` | zhao | **zhang Required Review** | C01, C06 | zhang 可并行做 mapper fixtures |
| C08 | `opengame-cli-spike` | zhang | **zhao Required Review** | 无 | 从第一天开始 |
| C09 | `opengame-process-executor` | zhang | zhao | C08 | 与 C01-C05 并行 |
| C10 | `opengame-agent-adapter` | zhang | **zhao Required Review** | C06, C09 | 与 C11 Fake Agent 编排并行 |
| C11 | `build-job-orchestration` | zhao | **zhang Required Review** | C02, C06, C07 | 先用 Fake Agent |
| C12 | `candidate-test-gate` | zhao | **zhang Required Review** | C02, C11 | zhang 并行 isolation |
| C13 | `runtime-workspace-isolation` | zhang | **zhao Required Review** | C08, C09 | 与 C11/C12 并行 |
| C14 | `playable-version-promotion` | zhao | **zhang Required Review** | C12 | 与 C10 hardening 并行 |
| C15 | `workspace-build-preview` | zhao | zhang | C07, C11, C12 | 可先用 contract fixtures |
| C16 | `release-publishing` | zhao | zhang | C14 | 与 C13 并行 |
| C17 | `resource-review-library` | zhao | zhang | C16 | Resource reuse 后置 |
| C18 | `cross-project-resource-reuse` | zhao | **zhang Required Review** | C05, C17 | 与部署准备部分并行 |
| C19 | `game-creation-e2e-release` | zhao | **zhang Required Review** | C01-C18 | 最终集成 |

---

## 5. Change 定义

### C00 — `v1-contract-alignment`

**Goal**

消除当前 Catalog、Prototype、OpenSpec baseline、OpenAPI 和 JSON Schema 之间的冲突，冻结 V1 glossary、范围和迁移策略。

**In Scope**

- 冻结本文件第 1 节的生命周期语义。
- 冻结 V1 多项目范围和固定 runtime/game output 约束。
- 决定 canonical CreatorGameSpec 与 RuntimeBuildSpec 的边界。
- 对齐 BuildCandidate、TestReport、PlayableVersion、Release、ResourceCandidate、SavedResource。
- 审核 `platform-v1-opengame-baseline`：决定更新/split/sync/archive，不创建第二套重叠实现事实源。
- 列出旧 `specs/001-game-creation-mvp/contracts` 的 keep/replace/migrate 清单。
- 产出逐文件迁移矩阵：现有 artifact、权威替代项、Owner、Required Reviewer、执行顺序。

**Out of Scope**

- 业务代码、数据库 migration、OpenGame 执行、Vue 修改。

**Acceptance**

- 没有同名异义或异名同义的版本实体。
- Human Promote 与 Human Publish gate 明确。
- canonical schemas 和 artifact ownership 有明确路径与版本策略。
- 现有 baseline change 的处置被记录且不再与新 Change 重叠。
- 所有遗留 OpenSpec/config/contracts 都有 keep/update/replace/archive 的单一处置，不保留“以后再看”的并行事实源。

### C01 — `platform-backend-foundation`

**Goal**

建立 FastAPI + SQLite 的最小可测试后端基础，使后续 Change 不再自行发明目录、事务和错误格式。

**In Scope**

- Python/FastAPI 项目结构、配置、SQLite migrations、repository transaction 基础。
- 统一 API error envelope、ID/time conventions、测试数据库和 health endpoint。
- Vue dev proxy/API client 的最小入口，不迁移具体业务页面。

**Out of Scope**

- Project 领域表、Build、OpenGame、SSE、部署生产配置。

**Acceptance**

- 后端可启动、migration 可重复执行、测试环境隔离。
- health/API error contract 有自动测试。
- 不引入 workflow engine、queue 或分布式 worker。

### C02 — `project-lifecycle-domain`

**Goal**

实现 Project、设计确认、Build、BuildCandidate、PlayableVersion、Release 的持久化关系和唯一状态转换边界。

**In Scope**

- Project、GameDesign、GameSpec revision、Build、BuildCandidate、PlayableVersion、Release 的 schema/repository/service boundary。
- 顶层 Project stage 派生规则、current playable pointer、active build guard。
- 成功、失败、取消、重试和后端重启后的状态不变量。

**Out of Scope**

- Vue 视觉、AI/OpenGame、具体 Build 执行、资源提取。

**Acceptance**

- BuildCandidate 不会直接覆盖 current Playable。
- 失败/取消不改变 current Playable 或 Release。
- active build 并发规则和 orphan recovery 明确且有 repository tests。
- Project stage 从领域状态派生，不保存重复 UI truth。

### C03 — `create-project-flow`

**Goal**

用户从一句 Idea 创建真实持久化 Project，并进入 Game Design。

**In Scope**

- Idea 校验、幂等/重复提交策略、Project create API、稳定 project id、Original Idea 保存。
- K01 创建后打开对应 Project，不依赖 local fixture。

**Out of Scope**

- Game Design 生成、GameSpec、Build、OpenGame。

**Acceptance**

- 空 Idea 被拒绝；重复提交不会制造异常或重复业务状态。
- 刷新后 Project 与 Original Idea 仍存在。
- 成功后进入该 Project 的 Game Design，而不是预置 demo session。

### C04 — `projects-list`

**Goal**

Projects 页面展示并恢复多个真实 Project。

**In Scope**

- 项目列表 API、打开项目、派生 stage/current playable/latest release/updatedAt。
- 空态、加载失败和项目不存在状态。

**Out of Scope**

- 项目编辑/删除/归档、权限、团队共享。

**Acceptance**

- 页面无项目 fixture；刷新后列表一致。
- 多 Project 状态互不污染。
- 列表 stage 与 Workspace 实际业务状态一致。

### C05 — `game-design-gamespec-flow`

**Goal**

把 Original Idea 经过可恢复 clarification 和 Human Confirm 生成 canonical CreatorGameSpec，并支持查看、编辑和独立确认。

**In Scope**

- Game Design/GDD draft、clarification、choice/input、confirm API。
- CreatorGameSpec schema、generation、revision、validation、confirm API。
- Prototype 中已确认的中文优先 GameSpec 信息结构和关系资源所需明确字段。
- CreatorGameSpec → RuntimeBuildSpec mapping contract 的输入侧。

**Out of Scope**

- OpenGame prompt、Build 执行、资源 workflow metadata 写入 GameSpec。

**Acceptance**

- clarification 和草稿刷新后可恢复。
- Game Design 与 GameSpec 分别需要 Human Confirm。
- 未确认或 schema invalid 的 GameSpec 不能 Build。
- GameSpec 不含 recommended/dismissed/used、drawer、resource id 等 UI workflow state。
- canonical schema 与 Prototype ViewModel/旧 runtime schema 的 mapping 有 contract tests。

### C06 — `game-agent-contract`

**Goal**

冻结 BuildService 与 Game runtime 的 provider-neutral contract。

**Contract 最低内容**

```text
GameBuildRequest:
  project_id, build_id, operation, creator_game_spec,
  runtime_build_spec, workspace, baseline_playable, request_text

GameBuildResult:
  status, artifact_manifest, preview_entry,
  diagnostics, metadata, error

RunEvent:
  run_id, sequence, stage, kind, message,
  progress, artifact_ref, error, timestamp
```

**Acceptance**

- BuildService 不知道 OpenGame 类型/命令/日志格式。
- OpenGameAdapter 和 FakeGameAgent 通过同一 contract suite。
- Provider event 不能直接表达“已 Promote/已 Publish/已保存资源”。
- 取消、timeout、invalid output 和 unsupported operation 有标准结果。

### C07 — `run-event-observability`

**Goal**

提供可持久化、可重连、顺序稳定的 RunEvent 与 SSE，使刷新页面不会重复启动 Build。

**In Scope**

- Run/Event repository、sequence、REST status、SSE replay/reconnect。
- sanitized diagnostics、terminal event、取消/断连行为。

**Out of Scope**

- OpenGame 原始日志解析、Workspace UI、BuildCandidate promotion。

**Acceptance**

- 相同 run 的事件顺序稳定且可从 last sequence 重放。
- 刷新/重连不创建新 run。
- terminal state 与 DB 一致；不虚构 provider 未确认的成功。

**C07 implementation boundary (2026-08-14)**

- `RunRepository` owns idempotent run creation, exact event sequence, sanitization, terminal transitions,
  cancellation requests, and orphan recovery.
- REST status, JSON replay, SSE replay/reconnect, and cancellation are exposed under `/api/v1/runs`.
- C11 remains responsible for connecting BuildService/GameAgent execution to these repository methods; C07 does
  not parse OpenGame logs, create Candidates, or promote Versions.

### C08 — `opengame-cli-spike`

**Goal**

用最小真实实验冻结 OpenGame V1 版本、非交互命令、输入输出、工作目录、取消和失败行为。

**Deliverables**

- 固定版本与安装方式。
- create/modify 命令矩阵及可用性结论。
- stdout/stderr/exit code/output tree fixtures。
- timeout/cancel/invalid output 样本。
- 对 C06/C09/C10 的 contract 建议，不提交产品业务实现。

**Acceptance**

- 所有 Adapter 假设均有真实 CLI evidence。
- Unsupported 能力明确，不用模拟成功掩盖。
- spike 可重复，且不改 OpenGame 内核。

### C09 — `opengame-process-executor`

**Goal**

可靠、安全地执行已固定版本的 OpenGame CLI。

**Input/Output**

```text
input: command, arguments, cwd, approved_env, timeout
output: stdout, stderr, exit_code, process_status, duration
```

**Acceptance**

- 指定 cwd/env 正确；stdout/stderr/exit code 真实可得。
- timeout/cancel 终止 child process tree，状态不会伪装成功。
- Executor 不依赖 Project、GameSpec、Candidate、Playable、Vue 或 FastAPI repository。
- 命令和 env 使用 allowlist，不接受任意前端输入。

### C10 — `opengame-agent-adapter`

**Goal**

把标准 GameBuildRequest 映射为 OpenGame 执行，并标准化 artifact、diagnostics 和 RunEvent。

**In Scope**

- Creator/Runtime spec 输入映射、Executor 调用、输出目录识别、artifact manifest、preview entry、错误与事件映射。
- 使用 C08 fixtures 建立 parser/mapper contract tests。

**Out of Scope**

- Project DB、BuildRepository、Promote、Publish、Vue、资源提取。

**Acceptance**

- 合法请求产生标准结果；非零退出、缺少 entry、路径逃逸和非法 artifact 返回标准失败。
- Adapter 不暴露 OpenGame-specific 类型给上层。
- 不从日志关键字单独推断最终 Build success。

### C11 — `build-job-orchestration`

**Goal**

通过 GameAgent Contract 管理 Build record 和 run，从 confirmed GameSpec 创建 BuildCandidate。

**In Scope**

- POST/query/cancel/retry Build、single active build rule、BuildService、FakeGameAgent integration。
- confirmed spec 和 baseline Playable 固定为 build input。
- GameBuildResult 成功后创建 BuildCandidate；失败保留 diagnostics。

**Out of Scope**

- subprocess、OpenGame 日志解析、TestReport 判定、Promote、Workspace UI。

**Acceptance**

- 每次 Build 有稳定 build/run id；重复请求和并发规则可测试。
- BuildService 只调用 GameAgent Contract。
- 成功只创建 BuildCandidate；失败/取消不修改 current Playable。
- 后端重启不会让 run 永久卡在 running。

**C11 implementation evidence (2026-08-14)**

- `BuildService` persists the confirmed GameSpec revision, baseline playable pointer, operation and request text before invoking the C06 `GameAgent` contract.
- `FakeGameAgent` is the deterministic provider used by the C11 service/API tests; no OpenGame subprocess or log parser is included.
- Stable `build_id`/`run_id`, single-active-build guard, retry ancestry, cancellation, terminal diagnostics and orphan recovery are covered by `backend/tests/test_c11_build_orchestration.py` and `backend/tests/test_c11_build_api.py`.
- Success creates a `BuildCandidate` only; no code in C11 changes `Project.current_playable_version_id`, creates a `PlayableVersion`, or publishes a `Release`.

### C12 — `candidate-test-gate`

**Goal**

构建和验证 BuildCandidate，生成由平台校验的 TestReport，并只把合格 Candidate 标记为 Ready to Promote。

**In Scope**

- artifact build、浏览器启动、console、核心输入/玩法/完成条件检查。
- TestReport schema、evidence、pass/fail/invalid、repair ancestry。
- 平台验证 evidence 完整性，不信任 runtime 自报 PASS。

**Acceptance**

- 缺少证据、矛盾报告或 build failure 不能 Ready to Promote。
- repair 创建新 Candidate attempt，不覆盖旧失败记录。
- 测试失败不影响 current Playable。

**C12 implementation evidence (2026-08-14)**

- `TestReport` and immutable `TestEvidence` records are persisted by migration `0006_candidate_test_gate`; BuildCandidate stores `test_gate_status`, `parent_candidate_id`, and `attempt`.
- `CandidateTestService` computes the authoritative platform verdict from required browser, console, input, gameplay and completion evidence. Runtime PASS alone cannot produce `ready`.
- Deterministic `FakeCandidateTestRunner` covers pass, missing evidence, contradiction, console failure, completion failure and runtime-only PASS without adding Playwright or OpenGame runtime dependencies.
- Repair links a new C11 retry Candidate to a failed/invalid parent without overwriting the parent; C12 never changes `current_playable_version_id`, creates PlayableVersion, publishes Release, or adds Workspace UI.
- C12 service/API tests cover 10 gate/repair cases and 4 API cases; full backend regression is recorded in the verification artifact.

### C13 — `runtime-workspace-isolation`

**Goal**

隔离 OpenGame 和生成代码，使其只能访问指定 run workspace 与批准环境。

**In Scope**

- workspace export/import allowlist、path canonicalization、symlink/traversal/protected path rejection。
- 非 root、时间/资源/输出限制、network/env policy、secret redaction。

**Acceptance**

- runtime 看不到受信任 `.git`、平台源码、host credential 或其他 Project。
- 非法路径和 symlink 被拒绝并产生 sanitized audit evidence。
- cancel/failure 后 partial workspace 不被下一次 retry 信任复用。

### C14 — `playable-version-promotion`

**Goal**

用户把 Ready BuildCandidate Promote 为新的不可变 PlayableVersion，并支持安全 Restore。

**In Scope**

- Promote API/Human Gate、current playable pointer、immutable version metadata/artifact provenance。
- version history、restore-as-new-candidate。

**Acceptance**

- TestReport 非 PASS 或 Candidate 非 ready 时拒绝 Promote。
- Promote 原子创建 PlayableVersion 并更新 pointer；重复请求幂等。
- Restore 不 reset/改写历史，并经过 Candidate/Test gate。

### C15 — `workspace-build-preview`

**Goal**

Workspace 使用真实 API、SSE 和 artifact URL 显示 Build、BuildCandidate、当前 Playable 与失败恢复。

**In Scope**

- Build status/progress、cancel/retry、Candidate preview、Playable preview、Promote gate、history/restore 状态。
- 离开 Workspace 后后台 Build 继续，返回后从 API 恢复。

**Acceptance**

- UI 不解析 OpenGame 原始日志、不使用 fixture artifact。
- Build 进行/失败时仍可查看 current Playable。
- Build 完成显示 Candidate，不自动当作 Playable。
- 刷新/返回不会重复启动 Build。

### C16 — `release-publishing`

**Goal**

用户把指定 PlayableVersion 发布为不可变 Release，并保留真实 provenance。

**In Scope**

- Release draft/review/publish/error/retry、name/description、based-on references、Release detail。
- Publish 后触发 release-scoped ResourceCandidate extraction job/batch creation。

**Acceptance**

- 只有现存 PlayableVersion 可以 Publish；重复提交不创建重复 Release。
- Release 不被后续 Playable Change 修改。
- Publish failure 不影响 Playable。
- batch 为空时不显示虚假 pending count。

### C17 — `resource-review-library`

**Goal**

把 Release-scoped ResourceCandidate 经 Human Gate 保存为全局 SavedResource，并提供“我的资源”体验。

**In Scope**

- 玩法/UI/美术三类候选；真实 provenance；save/ignore/undo；pending 保留。
- 我的资源 gallery/search/filter/detail；编辑名称和说明。
- 保存/编辑结果持久化，页面往返不丢失。

**Acceptance**

- Resource Review 不克隆第二份 Candidate 业务真相。
- 保存或忽略后不自动跳下一项；用户主动下一项且可撤销。
- 编辑名称/说明同步到 detail/gallery。
- `BuildCandidate` 与 `ResourceCandidate` 在 API/schema/命名上不可混淆。

### C18 — `cross-project-resource-reuse`

**Goal**

在新 Project 的 GameSpec 中推荐并使用已保存资源，同时保持 GameSpec 与 UI workflow state 分离。

**In Scope**

- SavedResource compatibility/match contract、推荐/dismiss/use/cancel workflow state。
- 关系类资源的 machine-readable defaults 和 first-use immutable relationship snapshot。
- provenance 和使用记录。

**Out of Scope**

- LLM semantic matching、真正代码注入、复杂参数映射、Marketplace。

**Acceptance**

- 匹配仅读取显式结构化字段；无匹配不推荐。
- dismissed 在导航和普通 revision 后保持。
- use 只改资源声明拥有的 GameSpec 字段；cancel 只恢复这些字段。
- resource id、recommended/dismissed/used 和 drawer state 不写进 CreatorGameSpec。

### C19 — `game-creation-e2e-release`

**Goal**

在干净环境证明真实 V1 闭环，不依赖 Fake Agent 或前端 fixture。

**Required Flow**

```text
Idea → Game Design → GameSpec → OpenGame Build
→ BuildCandidate → TestReport PASS → Human Promote
→ PlayableVersion → Human Publish → Release
→ Resource Review → SavedResource
→ 新 Project GameSpec 推荐/使用 SavedResource
```

**Acceptance**

- 至少两个真实 Project，状态互不污染；全局资源库共享。
- 实际调用固定版本 OpenGame，产生真实 preview entry/artifact。
- Candidate、TestReport、PlayableVersion、Release provenance 可追踪。
- failure/cancel/retry/refresh 均不破坏 current Playable。
- typecheck、unit、integration、contract、browser E2E、clean-environment build 全部通过。
- 记录完整 setup、recovery、health、artifact hosting 和 demo rehearsal 证据。

---

## 6. 并行执行波次

```text
Wave 0
  zhao:  C00 Contract Alignment
  zhang: C08 OpenGame CLI Spike

Wave 1
  zhao:  C01 Backend Foundation → C02 Domain
  zhang: C09 Executor

Wave 2
  zhao:  C03 Create + C04 Projects + C05 Design/GameSpec
  zhang: C10 Adapter skeleton / fixtures（等待 C06 contract freeze 后接入）

Wave 3
  zhao:  C06 Contract → C07 Events → C11 Build with Fake Agent
  zhang: C10 Real Adapter → C13 Isolation

Wave 4
  zhao:  C12 Test Gate → C14 Promotion → C15 Workspace
  zhang: C10/C13 hardening + contract/integration tests

Wave 5
  zhao:  C16 Release → C17 Resources → C18 Reuse
  zhang: runtime failure/cancel/security verification

Wave 6
  zhao:  C19 E2E / Demo Owner
  zhang: C19 Required Review / runtime diagnostics
```

允许的 Change 内并行：

- 前端可以在 API/Event contract 冻结后用 fixtures 开发，但 fixture 必须由正式 schema 生成。
- Adapter parser/event mapper 可以用 C08 的真实输出 fixtures 提前开发。
- BuildService 可以先通过 FakeGameAgent contract suite 开发，不等待真实 OpenGame。
- Runtime isolation 可以与上层 orchestration 并行，只通过 executor/workspace contract 接触。

禁止的并行：

- C00 未冻结时分别修改 Candidate/Version/Release 或 GameSpec 语义。
- C06 未冻结时 BuildService 和 Adapter 各自定义 GameAgent 类型。
- 两个 Change 同时拥有同一 database migration、public API schema 或核心 contract。
- C19 之前用 Fake Agent 结果宣称 V1 E2E 完成。

---

## 7. Change 状态与 Ready Gate

状态：

```text
Backlog → Explore → Proposed → Ready → In Progress → Review → Done
                                  ↘ Blocked
```

进入 `Ready` 必须满足：

- Owner/Reviewer 已确定，Required Review 标注清楚。
- 依赖 Change 已 Done 或其 public contract 已经双方冻结。
- Change Brief、proposal、specs、design、tasks 已完成 Human Review。
- In/Out of Scope、inputs/outputs、state changes、error cases、AC 可测试。
- 没有与现有 OpenSpec/contract 重叠的未决事实源。
- 分支与 PR 边界明确；一个 Change 默认一个 feature branch/PR。

进入 `Done` 必须满足：

- 实现与 OpenSpec 一致，所有关键 AC 有测试或明确 verification evidence。
- Unit/Integration/Contract/Typecheck/Build/相关 Browser E2E 通过。
- 无 Out of Scope 实现、无 provider-specific 类型越界、无虚假成功状态。
- Required Reviewer Approved，PR merged to `main`。
- OpenSpec 可 archive；如实现中变更了 contract，artifact 已先更新并重新 Review。

---

## 8. 交给 OpenSpec Explore 的推荐输入

### 8.1 第一次：只做 C00 对齐

```text
@openspec-explore

Explore C00 `v1-contract-alignment`.

Read:
- docs/development/V1_CHANGE_CATALOG.md
- openspec/config.yaml
- openspec/changes/platform-v1-opengame-baseline/
- specs/001-game-creation-mvp/contracts/
- specs/001-game-creation-mvp/data-model.md
- frontend/src/stores/projectStore.ts
- frontend/src/components/workspace/workspaceTypes.ts
- docs/superpowers/verification/2026-08-12-project-lifecycle-verification.md

Treat V1_CHANGE_CATALOG.md sections 0-3 as the intended aligned direction,
but verify them against the repository and surface remaining contradictions.

Do not implement and do not create a proposal yet.

Return:
1. final glossary and lifecycle state machine;
2. V1 scope/non-goals;
3. canonical CreatorGameSpec vs RuntimeBuildSpec boundary;
4. Human Promote and Human Publish gate ownership;
5. keep/replace/migrate decision for existing OpenSpec and contracts;
6. file-by-file migration matrix with owner, reviewer, and order;
7. corrected capability/change boundaries and public contracts;
8. explicit decisions still requiring zhao/zhang approval.
```

### 8.2 后续：一次只 Explore 一个 Change

```text
@openspec-explore

Explore CXX `<change-name>` from docs/development/V1_CHANGE_CATALOG.md.

Read the CXX section, completed dependency OpenSpec artifacts, and the current code paths it replaces.
Use the Catalog as roadmap context; use approved dependency contracts as normative inputs.

Do not expand into sibling Changes.
Do not implement.

Return:
- clarified Goal / In Scope / Out of Scope;
- inputs, outputs, state transitions, error cases;
- Given/When/Then acceptance scenarios;
- public contract changes;
- test strategy;
- dependency and parallel-work risks;
- whether the Change is ready for `/opsx:propose`.
```

### 8.3 Explore 之后

- C00 结论先更新本 Catalog、`openspec/config.yaml` 与相关 baseline artifacts，并由 zhang Required Review。
- C00 canonical contract、迁移矩阵和旧 baseline 处置记录位于 `openspec/changes/v1-contract-alignment/` 与 `docs/development/V1_CONTRACT_MIGRATION_MATRIX.md`；后续 Change 不得把 legacy baseline 当作第二套事实源。
- 单个 CXX Explore 清晰后，使用 `docs/development/CHANGE_BRIEF_TEMPLATE.md` 写 Change Brief。
- 再执行 `/opsx:propose <change-name>`，Human Review 后才进入 Superpowers implementation planning。

---

## 9. Open Questions（必须在 C00 关闭）

1. V1 固定浏览器游戏 capability 的准确边界：是否仍限定 top-down，还是仅限定 Phaser/browser artifact contract。
2. CreatorGameSpec canonical schema 的字段、版本号和兼容策略。
3. OpenGame 是否可靠支持 incremental modify；若不支持，V1 Change 是否使用 rebuild-from-playable fallback。
4. PlayableVersion artifact 是 Git-backed source + immutable built artifact，还是只要求 immutable artifact/provenance。
5. Release 与 PlayableVersion 是否共享同一 artifact，仅增加发布 metadata，还是复制到 release artifact namespace。
6. ResourceCandidate extraction V1 是 deterministic rules、人工标记，还是允许非阻塞 AI suggestion；无论哪种都不能自动保存。
7. V1 runtime isolation 的本地实现方式和可接受平台限制。

以上问题关闭前，C00 之外的 contract-sensitive Change 不得进入 `Ready`。
