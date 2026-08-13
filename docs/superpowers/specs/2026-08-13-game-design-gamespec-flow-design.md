# C05 Game Design / GameSpec Flow Design

## Goal

把 Project 的 Original Idea 经过可恢复 clarification 和两次 Human Confirm，生成可持久化、可校验的 canonical CreatorGameSpec，并作为后续 RuntimeBuildSpec mapping 的输入。

## Boundaries

- `GameDesign` 保存创意澄清草稿、选择、输入和确认状态。
- `GameSpecRevision` 保存 canonical CreatorGameSpec JSON、revision、校验结果和确认状态。
- `ProjectLifecycleService` 是设计确认、GameSpec revision、schema validation 和 Build gate 的唯一业务边界。
- Vue `projectStore` 只保存短期界面状态；recommended/dismissed/used、drawer、resource id 等资源复用工作流状态不得进入 canonical GameSpec。

## Canonical CreatorGameSpec

`content_json` 由 Pydantic contract 校验，最小结构固定为：

```json
{
  "schema_version": 1,
  "title": "多代田园物语",
  "first_playable": {
    "goal": "...",
    "hypothesis": "..."
  },
  "gameplay": {"core_loop": [], "actions": []},
  "characters": {
    "player": "...",
    "npc_name": "...",
    "npc_role": "...",
    "npc_behaviors": [],
    "dialogue_states": [],
    "world_areas": [],
    "primary_npcs": "...",
    "relationship_growth": "...",
    "favor_rules": "...",
    "relationship_events": "...",
    "request_rewards": "..."
  },
  "rules": {"progression": [], "completion": "..."},
  "scope": {"included": [], "later": []},
  "validation": []
}
```

`CreatorGameSpec` 不包含资源 workflow metadata，也不包含 UI drawer 状态。

## Persistence and API

复用 C02 的 `GameDesign` 与 `GameSpecRevision` 表，使用 `content_json` 保存经过 schema 校验的 payload。新增 API：

```text
GET   /api/v1/projects/{project_id}/design
PUT   /api/v1/projects/{project_id}/design
POST  /api/v1/projects/{project_id}/design/confirm
GET   /api/v1/projects/{project_id}/gamespec
PUT   /api/v1/projects/{project_id}/gamespec
POST  /api/v1/projects/{project_id}/gamespec/confirm
```

设计草稿更新是幂等的；GameSpec 更新生成下一 revision。确认会 supersede 旧确认 revision。不存在 Project、缺少 Game Design、invalid schema、未确认前置条件均返回统一 API error envelope。

## Confirm and Build Invariants

1. Game Design 必须先提交并 Human Confirm。
2. GameSpec 必须 schema valid 且 Human Confirm。
3. 未满足上述任一条件，`start_build` 拒绝并保持 Project current playable 不变。
4. Game Design Confirm 和 GameSpec Confirm 独立持久化、独立可恢复。
5. `CreatorGameSpec -> RuntimeBuildSpec` mapping 只读取 canonical fields；mapping contract 测试保证资源 workflow 字段不会泄漏。

## Frontend Mapping

- clarification UI 继续复用 `CreativeKickoffModal`，保存选择和输入并在重新进入 Project 时恢复。
- GameSpec UI 继续复用 `GameSpecDocument`、`SpecContext` 和现有中文优先布局。
- 增加纯函数 `GameSpecModel -> CreatorGameSpec` 与 `CreatorGameSpec -> GameSpecModel`；页面视觉不重做。
- `projectStore` 仅协调 UI loading/error/selected context，不成为 canonical confirmation truth。

## Testing

- Pydantic schema accepts valid Chinese prototype payload and rejects missing relationship fields.
- Design draft save/restore and independent confirmation API tests.
- GameSpec revision creation, validation, confirmation, supersede tests.
- Build gate tests for unconfirmed design, invalid spec and confirmed spec.
- Mapping contract tests for prototype fields and RuntimeBuildSpec input.
- Frontend typecheck, production build and manual acceptance for refresh/reopen/confirm flows.

## Out of Scope

OpenGame prompts, Build execution, resource extraction, resource matching metadata persistence, Pinia, Vue Router, workflow engine, queue, worker and backend API beyond this flow.
