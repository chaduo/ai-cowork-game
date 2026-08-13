## Why

AI Cowork Game 当前同时存在早期 OpenGame baseline、旧 MVP contracts、前端 prototype store 和新的 C00-C19 roadmap。它们对 Project 数量、固定游戏类型、GameSpec、Candidate/Version/Release 和资源复用的边界不一致，已经无法安全支持后续真实后端和 OpenGame 并行开发。C00 需要在任何业务实现开始前冻结唯一的 V1 事实源。

## What Changes

- 将 V1 定义为单用户、多 Project、固定浏览器可交付物的产品范围；不把 survival 或 Phaser 作为产品级强制语义。
- 冻结 Idea → Project → Game Design → GameSpec → BuildCandidate → TestReport PASS → Human Promote → PlayableVersion → Human Publish → Release → ResourceCandidate → SavedResource 的生命周期。
- 冻结 `CreatorGameSpec` 与 `RuntimeBuildSpec` 的边界、版本和转换方向。
- 冻结 BuildCandidate、TestReport、PlayableVersion、Release、ResourceCandidate、SavedResource 的职责、ID 和 provenance 关系。
- 明确 FastAPI/API 是所有 Human Gate 的唯一业务 Owner；Agent、runtime、timer 和 frontend fixture 不得自动 Promote、Publish 或保存资源。
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
- 更新 Catalog 与 legacy baseline README，建立事实源和迁移顺序。
- 不修改 FastAPI、SQLite、Vue、OpenGame CLI 或业务 runtime 代码；这些属于 C01-C19。
