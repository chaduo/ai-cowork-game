# V1 Contract Migration Matrix

> C00 产物。这里记录旧 artifact 的唯一处置，避免 Catalog、Prototype、OpenSpec baseline、旧 API/JSON Schema 形成第二套事实源。

## Canonical ownership after C00

| 内容 | C00 当前权威 | 后续 machine contract owner |
|---|---|---|
| V1 glossary / lifecycle / Human Gate / provenance | `openspec/changes/v1-contract-alignment/` | archive 后进入 `openspec/specs/v1-contract-governance/` |
| CreatorGameSpec / RuntimeBuildSpec behavior | C00 boundary + C05 OpenSpec | C05 schema and mapping contract |
| GameAgent provider-neutral boundary | C00 boundary + C06 OpenSpec | C06/C10 adapter contract |
| RunEvent | C00 ownership rule | C07 schema and event mapper |
| BuildCandidate / TestReport / PlayableVersion | C00 ownership rule | C02/C06/C11-C14 schemas and APIs |
| Release / ResourceCandidate / SavedResource | C00 ownership rule | C16-C18 schemas and APIs |
| OpenGame CLI invocation | C00 provider boundary only | C08 spike evidence and C09 executor contract |

## File-by-file disposition

| Existing artifact | Decision | Canonical replacement / action | Owner | Reviewer | Order |
|---|---|---|---|---|---|
| `docs/development/V1_CHANGE_CATALOG.md` | keep/update | Roadmap and Change boundaries; link C00 decision and matrix; not machine schema | zhao | zhang | C00 now |
| `openspec/config.yaml` | update | Multi-project browser artifact V1 context and Human Gate rules | zhao | zhang | C00 now |
| `openspec/changes/platform-v1-opengame-baseline/` | split/legacy | Migrate useful requirements to C00, C06-C19; mark README legacy; archive after split Changes are approved | zhao | zhang | C00 then C06-C19 |
| `openspec/changes/platform-v2-claude-agent-runtime/` | keep/defer | V2-only planning; must consume approved V1 contracts and not redefine them | zhao | zhang | after V1 |
| `specs/001-game-creation-mvp/spec.md` | keep as historical / replace requirements | Product history and V2 material; downstream V1 implementation cites C00-C19, not this mixed document | zhao | zhang | C00 mark, later split |
| `specs/001-game-creation-mvp/data-model.md` | update by slices | C02/C16-C18 replace tables; project_id required; separate candidate/resource repositories | zhao | zhang | C02 then C16-C18 |
| `specs/001-game-creation-mvp/contracts/gamespec.schema.json` | replace | C05 creates `creator-game-spec` and `runtime-build-spec`; old fixed survival schema is not normative | zhao | zhang | C05 |
| `specs/001-game-creation-mvp/contracts/openapi.yaml` | update/replace by slices | C01-C07 and C11-C18 add real multi-project APIs; old single-project endpoints are migration input | zhao | zhang | C01-C18 |
| `specs/001-game-creation-mvp/contracts/test-report.schema.json` | update | C06/C12 align Candidate/TestReport IDs, evidence and platform verdict | zhao | zhang | C06/C12 |
| `specs/001-game-creation-mvp/contracts/run-event.schema.json` | keep/update | C06/C07 provider-neutral normalized event contract | zhao | zhang | C06/C07 |
| `specs/001-game-creation-mvp/contracts/game-agent-adapter.md` | keep/update | C06/C09/C10 provider-neutral adapter, OpenGame-specific details only below adapter | zhao | zhang | C06/C09/C10 |
| `specs/001-game-creation-mvp/contracts/reusable-resource.schema.json` | replace | C17 creates separate ResourceCandidate/SavedResource schemas; old template/experience/asset union is legacy | zhao | zhang | C17 |
| `specs/001-game-creation-mvp/contracts/agent-profile-policy.md` | defer/update | V2 policy only; must not define V1 business gates | zhao | zhang | V2 |
| `specs/001-game-creation-mvp/contracts/runtime-benchmark.md` | keep/update | C08/C19 benchmark evidence; no lifecycle ownership | zhang | zhao | C08/C19 |
| `frontend/src/stores/projectStore.ts` | keep as prototype reference / replace | C03-C18 migrate business mutations to FastAPI; no backend code imports fixture store | zhao | zhang | C03-C18 |
| `frontend/src/components/workspace/workspaceTypes.ts` | keep as UI reference / map | C05/C15/C18 map ViewModel to API DTO; workflow state stays out of CreatorGameSpec | zhao | zhang | C05/C15/C18 |
| `docs/superpowers/verification/2026-08-12-project-lifecycle-verification.md` | keep as prototype evidence | C19 writes separate real backend/OpenGame evidence; this file cannot prove E2E | zhao | zhang | C19 |

## Downstream rule

Before any C01-C19 implementation, the Change Brief must name the matrix row and canonical contract it consumes. If a row is still `legacy` or `replace` without an approved replacement, the Change is `Blocked` rather than an invitation to invent a parallel schema.
