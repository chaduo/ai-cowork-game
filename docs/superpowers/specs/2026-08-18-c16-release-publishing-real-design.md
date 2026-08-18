# C16 Real Release Publishing Design

**Date:** 2026-08-18
**Status:** Approved for implementation
**Change:** C16 — `release-publishing`

## Goal

把已 Promote 的 `PlayableVersion` 通过一个明确的 Human Publish Gate 冻结为可恢复、不可被后续开发修改的 `Release`。发布结果必须记录真实 provenance，并为后续 C17 创建一个诚实的 release-scoped resource extraction batch。

## Product Decisions

- Publish 只接受当前 Project 已存在的 `PlayableVersion`；默认目标是当前 Playable。
- 打开 Publish Review 不产生业务记录，也不改变 Project stage。
- 只有用户点击“发布 Release”才创建 Release。
- 重复提交同一个 Playable 返回原 Release，不更新名称、说明或 provenance。
- Publish 失败不修改 Playable，也不创建半成品 Release。
- Release 保存发布时的名称、说明、Playable、Game Design revision、GameSpec revision、artifact path/checksum 和 Git checkpoint。
- Release 后续不会跟随新的 GameSpec、Playable 或 Project 名称变化。
- 发布完成后创建一个 `resource_extraction_batches` 记录。C16 只记录 `empty` 或 `ready` 的批次状态与数量；不伪造候选资源。C17 再向批次写入真实 `ResourceCandidate`。
- 不新增 Vue Router、Pinia、队列、worker 或 backend API client runtime dependency。

## Backend Boundary

### Persistent records

`Release` 增加不可变字段：

- `name`
- `description`
- `game_design_revision_id`
- `gamespec_revision_id`
- `artifact_path`
- `artifact_checksum`

`ResourceExtractionBatch` 是 C16/C17 的边界记录：

- `id`, `release_id`（unique）, `status` (`empty`/`ready`/`failed`）
- `candidate_count`, `error_code`, `created_at`, `updated_at`

### REST contract

- `GET /api/v1/projects/{project_id}/publish-review`
  - 返回 `eligible`, `reason`, 默认目标 Playable、下一 Release number、Game Design/GameSpec revision provenance，以及当前已有 Release。
  - 没有当前 Playable 时返回 `eligible: false`，使用稳定的错误原因，不创建 draft。
- `GET /api/v1/projects/{project_id}/releases`
  - 返回按 number 降序的完整 Release records 和 extraction batch summary。
- `GET /api/v1/projects/{project_id}/releases/{release_id}`
  - 返回单个不可变 Release detail。
- `POST /api/v1/projects/{project_id}/releases`
  - body: `playable_version_id`, `name`, `description`。
  - 只在 current Playable、Git/artifact provenance 完整时通过。
  - 同一 Playable 重复发布返回原 Release；新 Release 使用事务内递增 number，并创建一条 extraction batch。

错误均使用已有 API error envelope：`publish_review_unavailable`、`release_not_found`、`release_publish_failed`。

## Frontend Integration

- 保留现有 `ReleaseReviewModal`、`ReleaseDetailDrawer` 和视觉语言，仅把 local timer publish 替换为 API 状态。
- `ProjectSession` 保留纯 UI 的 `releasePhase`/modal draft；已发布 Release 列表与 extraction batch 从后端恢复。
- 远程项目打开 Workspace 时加载 releases；刷新不重新 Publish，也不显示默认的伪造 pending count。
- Publish Review 的资格、来源和错误来自后端；按钮只触发显式 POST。
- Demo `?screen=publish` 可以继续作为视觉演示入口，但不冒充真实远程 Project 数据。

## Invariants

1. 没有 current Playable 不能 Publish。
2. Publish Review 不创建 Release。
3. Release 的来源字段在创建时固定，后续 Playable/Spec 修改不改变旧 Release。
4. 重复 Publish 同一 Playable 是幂等的。
5. Publish 失败不改变 `Project.current_playable_version_id`。
6. 空 extraction batch 显示 0，不显示“发现 N 项”。

## Verification

- Backend migration upgrades cleanly and is repeatable.
- API tests cover unavailable review, successful publish, duplicate publish, immutable snapshot, failed publish protection and empty batch.
- Frontend tests cover API mapping, release list hydration and zero pending resource count.
- `cd frontend && npx vue-tsc -b && npx vite build` passes.
- Browser acceptance covers Playable → Publish Review → edit name/description → Publish → Release detail → refresh → same Release.
