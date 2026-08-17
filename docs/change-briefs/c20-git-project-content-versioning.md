# Change: c20-git-project-content-versioning

## 1. Metadata

**Change ID:** C20
**Owner:** zhang
**Reviewer:** zhao（Required Review）
**Priority:** P0
**Depends On:** C02（PlayableVersion/Release/BuildCandidate 模型，已合并）；C13（contract：workspace 隔离保证 runtime 碰不到平台仓库 —— 本切片只复用该保证，不依赖 C13 代码）
**Status:** Implemented on `feature/c20-git-project-content-versioning`（rebaseline line 95 切片：primitives + mapping；line 114 wiring 另行切片）

## 2. Goal

建立 Project Git 内容事实源与可追踪 checkpoint 原语，使 GDD/GameSpec/代码/素材/Playable/Release 可恢复且不与数据库工作流状态混淆。本切片交付 rebaseline line 95：**Project Git repository/checkpoint primitives and artifact provenance mapping**。

## 3. In Scope

- `ProjectGitService`（dulwich）：per-project 仓库初始化（`data/project-repos/{project_id}`）、受控文件布局（`gdd/`/`gamespec/`/`src/`/`assets/`/`playable/`）、commit/tag/read_file 原语；内容寻址确定性（同内容不重复 commit）。
- 内容策略：拒绝绝对/`..`/symlink/`.git`/受保护文件（`.env*`/`*.key`/`*.pem`/credentials/secrets）；提交文本经 `app.redaction` 扫描密钥，命中则拒绝。
- `ProvenanceService`（只读）：`compute_checksum`(sha256) + `resolve_playable(version_id)`（读 `PlayableVersion.git_commit/artifact_path/artifact_checksum` + 磁盘验证 commit 存在，漂移报错）+ `resolve_release(release_id)`（经 `playable_version_id` 传递解析）。
- 单一脱敏真相源 `app/redaction.py`（C13 流脱敏 + C20 内容扫描共用；与 C13 的副本内容一致，先落地 main 者为准，合并为 no-op）。

## 4. Out of Scope

- **line 114 checkpoint wiring**（Confirm GDD/GameSpec、Promote、Publish checkpoint 接入 lifecycle gate）—— 依赖 C13（workspace import）+ C14（Promote 创建 PlayableVersion）+ C16（Publish/Release），另行切片。
- `Release.git_commit` 发布快照列 —— 属 C16（Release owner）；C20 传递解析已满足"可解析"AC。
- workspace→trusted-repo 的 **import 桥**（design.md:64 完整）—— line 114 切片。
- Vue UI、部署打包、容器/网络硬隔离（C13 deferred）。

## 5. Acceptance Criteria

### AC1 — Git 不是业务状态机
**Given** 一次 checkpoint
**When** `ProjectGitService.commit` 被调用
**Then** 它只返回不可变 commit sha + 内容；jobs/gate/pointer/index 仍在 SQLite（`lifecycle.py`/`models.py`/`api/` 未改）。

### AC2 — 每个 PlayableVersion/Release 可解析到不可变 commit + artifact，重启可恢复
**Given** 一个 promoted PlayableVersion（其 `git_commit` 为 `ProjectGitService` 真实 commit）
**When** `ProvenanceService.resolve_playable` / `resolve_release` 被调用（含重启后新 Session/新服务实例）
**Then** 返回 commit sha + artifact_path + checksum 且 `verified=True`（磁盘 commit 存在）。

### AC3 — runtime 无权访问平台仓库
**Given** 受信任仓库在 `data/project-repos/`，run workspace 在 `data/workspaces/`（C13）
**When** 布局检查
**Then** 两棵树不相交（C13 隔离保证；C20 在测试中断言该不变量）。

### AC4 — 漂移可见，不被静默信任
**Given** DB 记录的 commit 在磁盘仓库中不存在
**When** resolve
**Then** 抛 `ProvenanceError(commit_drift)`，不返回虚假 verified。

### AC5 — 拒绝逃逸/受保护/含密内容
**Given** commit 传入绝对/`..`/symlink/`.git`/受保护文件名，或文本含 `sk-…`/`Bearer`/`api-key=…`
**When** commit
**Then** 抛 `ContentPolicyError`，不入库。

## 6. Implementation evidence (2026-08-15)

- `backend/app/services/project_git.py`：`ProjectGitService`（dulwich 0.25.2）init_project/commit/tag/read_file/commit_exists；嵌套树自底向上构建（修正 dulwich `Tree.id` 随内容变动的坑）；确定性 commit（零时间戳 + 内容寻址 → 同内容同 sha）；`_validate_member` + `_scan_for_secrets`（复用 `app.redaction`）。
- `backend/app/services/provenance.py`：`ProvenanceService` compute_checksum(sha256) + resolve_playable/release（磁盘验证 + 漂移检测）；`ProvenanceRecord` 只读 dataclass。
- `backend/app/redaction.py`：单一脱敏真相源（与 C13 副本一致；先落地 main 者为准）。
- `backend/pyproject.toml`：+ `dulwich>=0.21`。
- 测试：`test_c20_project_git.py`（38：init/commit/tag/read/确定性/路径策略/密钥扫描/重启恢复/布局不变量）、`test_c20_provenance.py`（8：resolve/restart 恢复/Release 传递/漂移/missing）。
- 验证：离线全量 198 passed / 1 skipped / 0 failed；C20 零迁移、零 `models.py`/`migrations/`/`lifecycle.py`/`api/` 改动（`git diff --stat origin/main..HEAD` 仅新文件 + pyproject + 2 docs）。
- 真实 Promote 插入证明：测试把 `ProjectGitService` 真实 commit sha 作为 `promote_candidate(git_commit=...)` 参数传入，**不改 `lifecycle.py`** 即证明原语可接入（line 114 wiring 再接线）。

## 7. line-114 wiring slice (2026-08-17) — Confirm/Promote/Publish checkpoints

- `backend/app/services/checkpoint.py`：`CheckpointService`（zhang-owned）包装 4 个 `ProjectLifecycleService` gate，**不改 gate 函数体**（`git diff` of `lifecycle.py` 为空，owner 边界保持）：Confirm GDD/GameSpec → commit `gdd/{rev}.json`/`gamespec/{rev}.json` + 记 `git_commit` + tag；Promote → 从 C13 run workspace 读真 artifact → commit `playable/index.html` + sha256 checksum + 覆写 `PlayableVersion.git_commit`/`artifact_checksum` 为真 sha（替代 pre-C20 的调用方 dummy 字符串）；Publish → tag `release-{n}` + `Release.git_commit` 快照。
- migration `0012_c20_checkpoint`：`game_design_revisions`/`game_spec_revisions`/`releases` 加 nullable `git_commit`（`playable_versions.git_commit` 已存在）。
- API `design.py` Confirm GDD/GameSpec 端点调 `CheckpointService` + 响应带 `git_commit`。
- 测试 `test_c20_checkpoint.py`（8）：4 gate round-trip + 幂等 + 重启可恢复 + Release 解析 + owner 边界不变量；离线全量 272 passed / 0 failed。
- Promote/Publish REST 端点 deferred 到 C14/C16（`CheckpointService.promote`/`publish` helper 已就绪，C14/C16 端点调之即可）。本切片堆在未合并的 C20 primitives PR 之上。
