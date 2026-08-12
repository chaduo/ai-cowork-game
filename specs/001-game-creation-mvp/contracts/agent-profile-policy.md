# Claude Agent Profile 权限契约

本文定义 V2 四类 Agent 的最小权限。FastAPI 选择 profile、创建 session、提供输入并验证输出；
Agent 不得创建下一业务阶段，也不得调用确认、接受、裁决或发布操作。

## 共同强制规则

- 每个 session 只挂载 `data/workspaces/{run_id}/{agent_session_id}`，不得看到可信 Git 仓库、平台
  源码、其他 workspace、宿主主目录或凭证目录。
- SDK `allowed_tools` 只用于自动批准，不能作为工具可见性或安全边界。Adapter 必须同时配置
  `disallowed_tools`，并通过 `can_use_tool` 或 `PreToolUse` 对工具名、规范化路径和参数逐次校验。
- 自定义工具使用进程内 SDK MCP server；外部 MCP 必须在部署配置中按名称和版本批准。Agent
  不得动态注册 MCP server。
- `confirm_gdd`、`confirm_gamespec`、`accept_assets`、`set_test_verdict`、`publish_version` 和任意
  SQLite/Git 指针写入永不作为 Agent 工具暴露。`promote_template`、`promote_asset`、
  `approve_experience` 和 `promote_skill` 同样不对 Agent 暴露。
- 所有工具调用先产生审计 RunEvent；拒绝、超时和越界必须产生 `audit` 或 `error` 事件。

## Profile Matrix

| Profile | System instruction 目标 | Domain Skills | 允许的 Workspace 能力 | 允许的平台/MCP 工具 | 明确禁止 |
|---------|-------------------------|---------------|--------------------------|----------------------|----------|
| PlanningAgent | 只在固定 2D 生存模板内把创意整理为 GDD 或 GameSpec draft | `gdd-planning`, `gamespec-authoring`, `mvp-scope-check` | 只读创意、已确认 GDD、schema 和模板能力清单；不得写源码 | `submit_gdd_draft`, `submit_gamespec_draft`, `validate_gamespec_draft` | Write/Edit/Bash、素材接受、Candidate、测试和发布 |
| AssetAgent | 为已确认 GameSpec 生成可审阅素材清单，失败时选择占位素材 | `asset-manifest`, `asset-license-trace`, `placeholder-fallback` | 只读 GameSpec；仅写 `assets/staging/**` 与 draft manifest | `generate_asset`, `inspect_asset`, `submit_asset_manifest_draft` | 任意网络、自动接受素材、源码/业务状态/Git 写入 |
| CodingAgent | 在稳定 Version 基线上创建、增量修改或按 TestReport 修复 Candidate | `phaser-survival-coding`, `gamespec-safe-edit`, `candidate-repair` | 读项目；仅写 `game-spec.json`, `assets/manifest.json`, `src/game/**`, `src/npc/**`, `public/game-assets/**` | `read_workspace_file`, `apply_workspace_patch`, `validate_gamespec`, `get_approved_experiences`, `request_candidate_build`, `submit_change_summary` | 来源项目 Workspace、平台源码、构建配置、测试桥、任意 shell/网络、资源晋升、测试裁决和发布 |
| TestAgent | 对只读 Candidate 执行固定构建与 Chromium playtest并提交证据 | `phaser-playtest`, `test-report-authoring` | Candidate 和测试产物只读；不得写项目文件 | `run_fixed_build`, `run_chromium_playtest`, `read_test_evidence`, `submit_test_report` | Write/Edit、通用 Bash、repair、降低检查项、业务状态和发布 |

## 结构化输入输出

- PlanningAgent 输出 `GddDraft` 或符合 GameSpec schema 的 `GameSpecDraft`。
- AssetAgent 输出 `AssetManifestDraft`，每项包含 `id`、`kind`、相对路径、来源、许可说明和预览。
- CodingAgent 输出变更摘要、修改文件相对路径和 Candidate 提交请求；平台自行创建 Candidate。
- `get_approved_experiences` 只按固定 capability/tag 返回 `available` Experience 的结构化字段和
  PASS 证据引用，并为当前 run 写入 ResourceUse；不返回来源 Workspace 或任意原始日志。
- TestAgent 输出符合 [test-report.schema.json](test-report.schema.json) 的报告；平台复核固定命令退出码、
  检查完整性和证据路径后才形成最终 verdict。

## 策略版本与变更

每个 profile 使用稳定 `tool_policy_id` 和 instruction/skill 版本。任何新增工具、路径或 MCP 权限
必须由两名开发者评审，并补充拒绝测试；不得在运行中由模型扩大权限。
