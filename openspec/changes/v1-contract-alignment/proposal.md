## Why

AI Cowork Game 当前同时存在已确认的 V1 Design Spec、早期 OpenGame baseline、旧 MVP contracts、前端 prototype store 和 C00-C19 roadmap。它们对 Agent Runtime、GDD/GameSpec、Candidate 验证、Git 版本、Release 分发和资源复用执行边界仍不一致。C00 需要把已确认的 V1 Design Spec 固定为最高产品事实源，并让后续 Change 只保留一套可执行 contract。

## What Changes

- 将 V1 定义为单用户、多 Project、Phaser 2D 浏览器游戏的产品范围；不把 survival 或某个 demo fixture 当作产品级语义。
- 冻结 Idea → GDD → GameSpec → Build → Candidate → Platform Verification → Human Play Review → Human Promote → PlayableVersion → Change/New Version → Human Publish → Release → ResourceCandidate → SavedResource → Future GameSpec/Build Context 的完整生命周期。
- 冻结 `CreatorGameSpec` 与 `RuntimeBuildSpec` 的边界、版本和转换方向。
- 冻结 GDD revision、BuildJob、BuildCandidate、VerificationResult/TestReport、PlayableVersion、Release、ResourceCandidate、SavedResource、Git checkpoint 和 working draft 的职责、ID 和 provenance 关系。
- 明确 FastAPI/API 是六类 Human Gate 的唯一业务 Owner：Confirm GDD、Confirm GameSpec、Blocking Build Decision、Human Play Review/Promote、Publish Review、Resource Review。Agent、runtime、timer 和 frontend fixture 不得自动跨越这些 Gate。
- 冻结 One Agent Runtime + Game Design/GameSpec/Game Build profiles 的 provider-neutral 边界；OpenGame、Claude SDK 或 Pi Agent 均只能通过同一 Runtime contract 接入。
- 将 `waiting_for_input`、GameSpec Amendment、Drift Detection、Assets/Code Working Draft、Restore、复杂资源匹配及 Share/Build ZIP/Source ZIP 纳入 V1 必交付范围；P0/P1 只表示 Wave 1/Wave 2 顺序，不表示延期到 V1 之后。
- 要求已选择的 SavedResource 作为 task-scoped context 真正进入 Build Agent，不允许只更新 UI 或推荐状态。
- 更新 `openspec/config.yaml` 的 V1 context 与 Human Gate 规则。
- 建立逐文件 keep/update/replace/archive 迁移矩阵，明确旧 OpenSpec baseline、JSON/OpenAPI contracts 和 prototype state 的处置。
- 将 `platform-v1-opengame-baseline` 标记为 legacy migration input；其 provider-neutral、candidate/version、run-observability 要求拆分到后续 C00-C19 Change，不再作为并行实现事实源。

## Capabilities

### New Capabilities

- `v1-contract-governance`: Defines the canonical V1 glossary, lifecycle, project scope, Human Gate ownership, GameSpec boundary, provenance rules, and migration authority used by downstream Changes.

### Modified Capabilities

无。现有 `openspec/changes/platform-v1-opengame-baseline/` 是待迁移的 active planning material，不是已归档 main capability；其处置记录在 C00 migration matrix 中。

## Impact

- 更新 `openspec/config.yaml`，使 OpenSpec context 与当前 V1 方向一致。
- 新增 C00 OpenSpec proposal、design、governance spec、tasks 和 `docs/development/V1_CONTRACT_MIGRATION_MATRIX.md`。
- 更新 Catalog、实施排期与 legacy baseline README，建立事实源、Wave 顺序和迁移路径。
- 不修改 FastAPI、SQLite、Vue、OpenGame CLI 或业务 runtime 代码；实现由后续独立 Change 承担。
