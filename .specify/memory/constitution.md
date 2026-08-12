<!--
Sync Impact Report
- Version change: 1.1.1 -> 1.2.0
- Modified sections:
  - Agent Runtime Roadmap（增加 V2 可复用开发知识最低门禁）
- Added principles:
  - XIII. 只有经过验证和审阅的开发知识才能复用
- Added sections: none
- Removed sections: none
- Follow-up TODOs: none
-->

# AI Cowork Game Constitution

## Core Principles

### I. 端到端可演示优先

每次迭代必须产生用户可实际验证的结果。第一阶段的核心闭环必须覆盖：用户输入游戏
创意、AI 生成简版 GDD、生成结构化 GameSpec、生成或接入基础美术素材、基于固定
Phaser 模板生成游戏、自动构建、浏览器在线试玩、用户通过 AI 修改游戏或直接修改
源码，以及重新构建并试玩新版本。不能进入或直接提升该闭环可靠性的功能，不得优先于
核心流程开发。该原则确保两人团队在有限周期内始终拥有可展示、可反馈的成果。

### II. 严格控制 MVP 范围

第一阶段必须限定为单用户、任一时刻一个活动游戏项目和一种固定的 Phaser 2D 俯视角生存游戏模板；
仅支持基础角色、敌人、道具、背景、至少一个具有基础行为和对话的 NPC、AI 修改游戏、
用户直接修改 GameSpec 或源码、自动构建与在线预览，以及项目版本与回退。任何新增功能
必须在需求或设计文档中说明其对结项核心闭环的直接价值，否则不得进入第一阶段。
明确的范围边界是按期交付和保持系统可运行的前提。

### III. AI 与用户共同编辑同一个项目

AI 修改和用户对 GameSpec 或源码的修改必须作用于同一个持久化游戏项目，并共享同一
版本历史；不得生成彼此隔离、无法继续编辑的结果。AI 必须读取当前项目状态，在现有
GameSpec、代码和素材基础上进行增量修改；除首次创建或经用户明确确认的重置外，不得
每次重新生成整个项目。该原则保证共创过程连续，并避免覆盖用户工作。

### IV. Agent Runtime 必须分阶段且可替换

平台业务层不得直接依赖特定模型、CLI 或 Agent 的内部实现。Platform V1 必须以
`OpenGameAdapter` 作为 `GameAgentAdapter` 的首个实现，用于建立端到端基线。Platform V2
必须以 Claude Agent SDK 构建平台自己的领域 Agent Runtime，并成为主要后端；OpenGame
继续作为 fallback、reference 和 benchmark baseline。两种后端必须共享 GameSpec、Workspace、
Candidate、Version、TestReport 和 RunEvent 等平台契约。替换运行时不得要求重写平台核心
业务状态机；契约变更必须包含兼容性说明和适配器级测试。

### V. AI 执行必须隔离

AI 生成代码、修改文件、安装依赖和执行命令必须发生在独立工作目录及受限执行环境中。
默认禁止访问用户主目录、宿主机凭证、其他游戏项目、平台服务端源码和无关网络资源；任何
例外必须按最小权限原则显式授权并留有审计记录。API Key 和其他密钥不得写入生成代码、
构建日志或公开游戏产物。安全与数据保护要求不得因演示期限或功能便利而降低。

### VI. 全过程可观察、可取消、可恢复

每次 AI 运行必须具有唯一 run ID，并持久记录当前执行阶段、用户原始需求、运行时后端、
Agent 类型、Agent session、模型、AI 消息、工具调用、构建日志、开始与结束时间、运行结果、
失败原因、生成产物、模型用量和可获取的成本。运行时原生事件必须转换为平台 RunEvent，
不得由前端直接依赖供应商事件格式。长时间任务必须支持取消；失败必须返回明确错误，并允许
安全重试、修复或重新测试。取消、重试和恢复不得破坏最近一个构建成功的版本。

### VII. 每次修改必须版本化

首次生成、AI 修改和用户对 GameSpec 或源码的修改必须先形成可追溯 Candidate。Candidate
可经历构建、测试、修复和重新测试；只有构建成功且结构化 TestReport 为 PASS 的 Candidate
才能发布为不可变 Version。每个 Candidate 和 Version 必须记录来源、用户需求、修改文件、
GameSpec 快照、运行时与 Agent session、构建测试状态、生成时间和产物。失败 Candidate 必须
保留诊断信息，但不得替换当前可玩 Version。

### VIII. 可玩性是完成标准

生成代码不得等同于完成。Candidate 只有同时通过以下检查才能发布为 Version：项目文件生成
完成、依赖安装成功、TypeScript 检查或生产构建通过、游戏页面可启动、页面无阻断运行的
控制台错误、玩家可移动、核心游戏循环可运行，并且至少一个胜利或失败条件可触发。验证
结果必须形成结构化 TestReport 并关联到具体 Candidate；任一检查失败时必须进入失败或受控
repair/retest 流程，且不得发布为当前 Version。TestAgent 无权自行发布 Version。

### IX. NPC 能力保持结构化和可控

第一阶段 NPC 必须由结构化配置和确定性行为驱动，游戏运行期间不得调用大模型。NPC 可
支持名称与角色定位、精灵或基础外观、初始位置、站立、巡逻或逃跑等有限行为、玩家靠近
触发对话，以及 AI 或用户修改行为参数、对话、配置或源码。复杂记忆、开放式实时对话和
自主决策不得进入第一阶段，以确保行为可测试、成本可控且演示稳定。

### X. 需求和产物必须可追溯

每个游戏版本必须能够追溯到原始游戏创意、生成的 GDD、GameSpec、后续用户修改要求、
AI 代码修改、用户手工源码修改、使用的素材、Agent 与模型配置及构建结果。系统必须能够
说明版本产生的原因、变更内容和执行主体。追溯记录必须使用稳定标识关联项目、run、版本
和产物，不得仅依赖易丢失的界面消息。

### XI. 成本和复杂度必须受控

所有 Agent 运行必须记录耗时、模型调用次数、重试次数和可获取的成本信息。V1 核心闭环稳定
运行前不得引入 V2 多领域 Agent Runtime；V2 只能在复用 V1 平台契约和质量门禁的前提下引入
PlanningAgent、AssetAgent、CodingAgent 和 TestAgent。四者是由 FastAPI 确定性编排的受控
Agent profile/session，不要求拆为微服务，也不得演化为 LLM 自由编排。分布式任务系统、复杂
微服务和其他高维护成本组件仍需提供明确收益并通过评审。

### XII. 在线交付优先

最终成果必须通过公开或指定网址访问，并提供可重复的部署步骤。交付必须清楚标明 V1
OpenGame baseline 与 V2 Claude Agent Runtime 的完成状态。最终目标不能以“只有 OpenGame
可用”宣告完成；同一平台工作流必须能使用 Claude Runtime 完成创建、增量修改、失败修复、
构建、playtest、结构化报告和 Version 发布。每个里程碑必须保留可演示的稳定版本和证据。

### XIII. 只有经过验证和审阅的开发知识才能复用

成功开发产物可以成为平台资源，但复用资格必须由证据和人工门禁决定。Reusable Template
必须来自已发布 Version，且只能用于兼容的固定 Phaser 生存游戏能力；Development Experience
必须引用成功构建或 repair run、PASS TestReport 和适用范围；Reusable Asset 必须已被用户接受，
并保留类型、风格、来源、prompt、许可说明和来源 Version。任何复用必须记录目标项目和使用的
资源版本。单次成功 Run 不得自动修改 Formal Skill；经验只能先形成 Skill Candidate，经独立审阅
和验证后才能晋升。自动模板提取、向量检索、经验聚类和自动 Skill 晋升不属于强制范围。

## Agent Runtime Roadmap

- **Platform V1 — OpenGame Baseline**：FastAPI 通过 `GameAgentAdapter` 调用
  `OpenGameAdapter`，验证 GameSpec → Coding → Candidate → Build → Test → Version，建立
  OpenGame benchmark 并验证 Phaser 游戏领域能力。
- **Platform V2 — Claude Agent Runtime**：FastAPI 确定性编排 PlanningAgent、AssetAgent、
  CodingAgent 和 TestAgent；各 Agent 使用独立 system instructions、Domain Skills、工具权限、
  MCP/平台工具、隔离 Workspace 与共享 GameSpec。V2 必须集成 Claude Agent SDK，并以 Claude
  Runtime adapter 作为主要后端。
- FastAPI 必须拥有 GDD Confirm、GameSpec Confirm、Asset Accept、Candidate 状态、Test PASS
  和 Version Publish 等平台业务状态的唯一决定权。LLM 和 Agent 只能提交结构化结果，不能
  自行推进这些门禁。
- V2 必须支持 create game、incremental modify、repair、build、playtest、结构化 TestReport、
  session/run 映射、事件规范化和 Candidate/Version 集成。
- V2 必须至少演示：一个成功 Version 经人工门禁晋升为 Reusable Template；一个已接受 Asset
  保存为 Reusable Asset 并在另一个顺序创建的隔离项目中复用；一条有成功证据的开发或修复经验
  进入可用状态并可由 CodingAgent 读取。
- 两名开发者应在 2026-08-19 前尽量完成 V2 全部门禁；若未全部通过，必须保留可演示的 V1
  稳定基线并如实标记 V2 未完成项，不能降低安全、测试或发布门禁，也不能以 fallback 冒充完成。

## MVP 与技术约束

- 第一阶段唯一游戏运行时必须为 Phaser，游戏类型必须为 2D 俯视角生存游戏，生成过程
  必须基于受控的固定模板。
- 产品界面仍只维护一个活动项目；为验证跨项目资源复用，可以归档当前项目后顺序创建第二个
  隔离演示项目。不得因此引入并发多项目管理、多用户协作、多模板选择或资源市场。
- V1 不得提前实现 V2 多领域 Agent Runtime；整个路线图不得实现 Unity、3D 游戏、多种游戏模板、
  LLM 自由编排、实时大模型 NPC、多人
  协作、复杂动画系统、完整音乐生成、社区与作品市场，以及复杂账号或权限系统。
- GameSpec 必须采用结构化、可验证且可版本化的表示，并作为 AI、源码和可运行游戏之间的
  核心可追溯产物。
- 素材必须记录来源、授权或生成方式；缺少可确认使用权的素材不得进入公开交付产物。
- 所有设计取舍必须适配两名开发者的交付能力；V1 与 V2 必须分别定义验收门禁和里程碑，不能
  通过牺牲 V1 可运行基线来制造未经验证的 V2 表面集成。

## 开发流程与质量门禁

- 每项需求必须在规格中标明其对应的核心闭环步骤、可验证验收标准和范围归属；范围外需求
  必须延期，除非先通过 Constitution 修订或明确替换同等工作量的既有范围。
- 设计和任务拆分必须先覆盖最短可运行纵向闭环，再扩展体验、兼容性或可选能力。
- 涉及 `GameAgentAdapter`、版本恢复、执行隔离或构建发布的变更，必须具备契约测试或集成
  测试；游戏成功状态必须通过自动化构建检查和浏览器运行验证共同确认。
- 代码评审必须检查安全边界、版本完整性、追溯数据、失败恢复、成本记录和 MVP 范围；任何
  不符合项必须在合并前解决，或记录经批准的限时例外、责任人和到期日。
- 每次可演示里程碑必须保留最近一个稳定版本及其部署产物，并执行取消、失败和回退路径的
  验证，避免演示依赖未验证的最新构建。

## Governance

本 Constitution 是 AI Cowork Game 后续规格、设计、任务和实现的最高项目治理依据。发生
冲突时必须依次遵循：安全与数据保护、可运行和可恢复、端到端结项闭环、用户体验、扩展性、
非必要功能。较低优先级目标不得削弱较高优先级要求。

修订必须提交书面提案，说明变更动机、受影响原则、对现有规格和实现的影响、迁移方案及
版本号变更，并由两名第一阶段开发者共同批准。若紧急安全修订无法事先取得共同批准，必须
先采取最小化风险的临时措施，并在下一次评审中补齐批准和迁移记录。

Constitution 使用语义化版本：删除原则、降低强制性或作出不兼容治理重定义时递增主版本；
新增原则、章节或实质性扩展规则时递增次版本；不改变治理含义的澄清或文字修正递增补丁
版本。所有受影响的规格、计划和任务必须在修订时完成一致性检查或列出明确迁移事项。

每个功能规格、实现计划、任务清单和代码评审都必须执行 Constitution 合规检查。无法满足
原则的方案必须被拒绝，除非修订 Constitution 或获得带责任人、理由和截止日期的临时例外；
安全与数据保护原则不得豁免。项目在每个可演示里程碑和结项发布前必须再次完成合规审查。

**Version**: 1.2.0 | **Ratified**: 2026-08-07 | **Last Amended**: 2026-08-10
