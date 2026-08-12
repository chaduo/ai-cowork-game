# OpenGame / Claude Runtime 统一基准契约

## 目的

同一 FastAPI Workflow 使用完全相同的输入和发布门禁比较 `OpenGameAdapter` 与
`ClaudeRuntimeAdapter`。基准用于回归、风险判断和结项说明，不用于放宽任一后端的质量门禁。

## 固定输入

- 一个冻结的中文游戏创意及其人工确认 GDD。
- 一个通过同一 schema/语义校验的 GameSpec，包含固定 seed 和至少一个 NPC。
- 同一套已接受素材；外部生成不可用时，两边都使用相同占位素材。
- 一条规则增量修改、一条 NPC 修改，以及一个会触发可修复测试失败的 fixture。
- 同一 Phaser 模板 commit、Node/npm lockfile、Docker runner 和 Chromium 测试。

## 每次记录

| 字段 | 说明 |
|------|------|
| `benchmarkId` / `runId` / `backend` | 基准、运行和后端标识 |
| `templateCommit` / `inputHash` | 模板与输入一致性 |
| `operation` | `create`, `modify`, `repair_retest` |
| `status` / `failedStage` | 最终状态与失败阶段 |
| `durationMs` / `stageDurations` | 总耗时和各平台阶段耗时 |
| `modelCalls` / `inputTokens` / `outputTokens` / `costText` | 可获得的用量成本 |
| `repairAttempts` | 平台批准的修复次数 |
| `candidateId` / `testReportId` / `versionId` | 全链路关联 |
| `testVerdict` / `failedChecks` | 统一 TestReport 结果 |
| `templateId` / `reusableAssetId` / `experienceId` | V2 最小复用资源证据；不计为后端性能优势 |

## 执行规则

1. V1 OpenGame baseline 连续执行三次 `create`，并至少执行一次 `modify`。
2. V2 至少执行一次 `create`、一次 `modify` 和一次 `repair_retest`。
3. 两种后端不得修改测试、模板核心契约或人工确认结果；失败必须保留原始事实。
4. 发布成功率只统计有效 PASS TestReport；fallback 结果不能记到另一个 backend 名下。
5. 结项报告并列展示结果和已知限制，不要求 Claude 在速度或成本上胜过 OpenGame。
6. V2 额外记录 Template 晋升、Asset 跨顺序项目复制和 Experience 被 CodingAgent 读取的
   ResourceUse；这些平台动作不混入 OpenGame/Claude 生成耗时比较。
