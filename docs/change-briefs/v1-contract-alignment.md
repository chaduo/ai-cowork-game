# Change: v1-contract-alignment

## 1. Metadata

**Change ID:** C00
**Owner:** zhao
**Reviewer:** zhang（Required Review）
**Priority:** P0
**Depends On:** 无
**Status:** In Progress

## 2. Goal

冻结 AI Cowork Game V1 的术语、生命周期、范围和跨模块 contract，消除 Catalog、Prototype、现有 OpenSpec baseline、OpenAPI、JSON Schema 与前端状态模型之间的冲突，使 C01-C19 可以基于同一套事实源并行开发。

## 3. Background

当前仓库同时存在早期 `platform-v1-opengame-baseline`、`specs/001-game-creation-mvp/contracts`、前端 prototype 状态和新的 C00-C19 计划。它们对 Project 数量、固定游戏范围、Version/Playable/Release、Candidate/ResourceCandidate 和 Human Gate 的命名与职责并不完全一致。

C00 是后续真实后端和 OpenGame 集成的前置合同工作。V1 先使用 OpenGameAdapter，V2 以后替换为 Claude Agent Runtime；因此 provider-neutral 的平台 contract 必须先冻结，OpenGame-specific 行为只能留在 Executor/Adapter 边界内。

## 4. User / System Flow

```text
Catalog + existing OpenSpec + API/JSON contracts + current frontend state
↓
C00 repository audit and contradiction log
↓
zhao decisions on glossary, scope, ownership, migration and gates
↓
canonical V1 OpenSpec/config/contracts and file-by-file migration matrix
↓
zhang Required Review
↓
C01-C19 consume the approved contract; no duplicate baseline remains
```

## 5. In Scope

- [ ] 冻结 Idea → Project → Game Design → GameSpec → BuildCandidate → TestReport PASS → Human Promote → PlayableVersion → Human Publish → Release → ResourceCandidate → Resource Review → SavedResource 的生命周期语义。
- [ ] 冻结 V1 的多 Project 范围、固定 runtime/game output 能力边界、V1/V2 非目标和真实 OpenGame 的位置。
- [ ] 冻结 `CreatorGameSpec` 与 `RuntimeBuildSpec` 的职责、来源、版本化和转换边界。
- [ ] 冻结 `BuildCandidate`、`TestReport`、`PlayableVersion`、`Release`、`ResourceCandidate`、`SavedResource` 的职责、ID、provenance 和 Human Gate ownership。
- [ ] 审核 `platform-v1-opengame-baseline`，记录 update / split / sync / archive 的单一处置，不保留重叠事实源。
- [ ] 审核 `specs/001-game-creation-mvp/contracts/`、`data-model.md`、`openapi.yaml`、frontend store/types 和历史 verification artifacts。
- [ ] 生成逐文件迁移矩阵：现有 artifact、canonical 替代项、keep/update/replace/archive、Owner、Required Reviewer 和执行顺序。
- [ ] 更新 C00 所需的 OpenSpec proposal/design/specs/tasks；只做 contract/planning 文档，不实现业务代码。

## 6. Out of Scope

- 不实现 FastAPI、SQLite migration、repository、service 或 API handler。
- 不实现 OpenGame CLI、Executor、Adapter、workspace isolation 或真实 build。
- 不修改 Vue 页面、前端状态管理或视觉结构。
- 不引入 Pinia、Vue Router、workflow engine、queue、分布式 worker 或新的 runtime dependency。
- 不实现 C01-C19 的业务功能；它们只消费 C00 批准后的 contract。
- 不在 C00 中决定未经过 zhao/zhang 共同确认的 provider-specific CLI 细节；这属于 C08 spike evidence。

## 7. Inputs

### Repository artifacts

```text
docs/development/V1_CHANGE_CATALOG.md
openspec/config.yaml
openspec/changes/platform-v1-opengame-baseline/
specs/001-game-creation-mvp/contracts/
specs/001-game-creation-mvp/data-model.md
frontend/src/stores/projectStore.ts
frontend/src/components/workspace/workspaceTypes.ts
docs/superpowers/verification/2026-08-12-project-lifecycle-verification.md
```

### Decision constraints

```text
FastAPI owns business lifecycle and Human Gates.
BuildCandidate is not PlayableVersion.
ResourceCandidate is not BuildCandidate.
Agent/provider output cannot directly Promote or Publish.
Failed or cancelled Candidate cannot replace current PlayableVersion.
V1 uses OpenGameAdapter; V2 runtime must consume the same provider-neutral contracts.
```

## 8. Outputs

```text
openspec/changes/v1-contract-alignment/proposal.md
openspec/changes/v1-contract-alignment/design.md
openspec/changes/v1-contract-alignment/specs/**/*.md
openspec/changes/v1-contract-alignment/tasks.md

docs/development/V1_CHANGE_CATALOG.md updates or decision links
openspec/config.yaml updates
file-by-file migration matrix
explicit decision log for all C00 open questions
```

## 9. Interfaces / Contracts

### Consumes

```text
Current V1 Catalog and lifecycle direction
Existing OpenSpec baseline artifacts
Existing GameSpec, reusable-resource, run-event and test-report schemas
Existing project lifecycle frontend types/store as migration evidence only
```

### Produces

```text
Canonical glossary and lifecycle state machine
Canonical CreatorGameSpec / RuntimeBuildSpec boundary
Canonical Candidate/TestReport/PlayableVersion/Release/Resource provenance rules
Human Promote / Human Publish ownership rules
Migration and deprecation map
Contract-sensitive dependency order for C01-C19
```

### Must Not Depend On

```text
Concrete OpenGame CLI flags as normative platform API
Vue component-local state as business truth
Frontend fixtures as backend contract
Agent/provider-native events as lifecycle mutations
```

## 10. Acceptance Criteria

### AC1 — Glossary and lifecycle are unambiguous

**Given** the Catalog, existing baseline and current contracts use overlapping lifecycle names

**When** C00 artifacts are reviewed

**Then** every lifecycle entity has one canonical name, one purpose, one owner, allowed transitions and a stable relationship to Project, Build and Release.

### AC2 — Human Gates are explicit

**Given** runtime output can report success or failure

**When** a Candidate reaches build/test/publish boundaries

**Then** only the platform/API and explicit human actions can Promote or Publish; no Agent, timer, provider event or frontend fixture can perform either gate.

### AC3 — GameSpec boundary is frozen

**Given** CreatorGameSpec describes final game design and RuntimeBuildSpec describes an executable build input

**When** a consumer Change reads the C00 contract

**Then** it can determine ownership, validation, versioning, conversion direction and fields that must not contain UI workflow state.

### AC4 — Baseline has one disposition

**Given** `platform-v1-opengame-baseline` overlaps with the C00-C19 direction

**When** C00 is approved

**Then** the baseline is explicitly updated, split, synced or archived, with no second implementation fact source left active.

### AC5 — Migration is actionable

**Given** legacy OpenAPI, JSON Schema, data model, OpenSpec and frontend artifacts exist

**When** C01-C19 start

**Then** each relevant file has a keep/update/replace/archive decision, an owner, a reviewer and an execution order.

### AC6 — Scope is safe for parallel work

**Given** zhang is independently running the C08 OpenGame CLI spike

**When** C00 is reviewed

**Then** C00 freezes provider-neutral boundaries and records which CLI capability decisions must wait for C08 evidence, without modifying or owning C08 implementation files.

## 11. Verification

- [ ] `openspec validate v1-contract-alignment` passes after all requested artifacts exist.
- [ ] No unresolved C00 open question remains without an explicit owner and decision date.
- [ ] `rg` finds no duplicate canonical names with conflicting definitions across the approved artifacts.
- [ ] zhang reviews C00 artifacts and confirms the C08 boundary is not overwritten.
- [ ] The final PR contains only C00 planning/contract changes and documentation; no business implementation files.
