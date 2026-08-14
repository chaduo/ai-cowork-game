# Cancel Build and Return to GameSpec Design

## Goal

取消首个 First Playable Build 后，Workspace 返回可编辑的 GameSpec Review，而不是停留在一个独立的 `build_cancelled` 页面阶段。用户可以调整现有 GameSpec，或不修改内容直接重新确认并创建新的 Build。

## Root Cause

当前 Prototype 把 `build_cancelled` 同时当作 Build 终态和 Workspace 页面阶段。取消虽然停止了 timer，但 Workspace 仍选择 BUILD tabs、Build Cowork panel 和 Build artifact，因此用户会停在“准备 Build / Build Cancelled”上下文中，无法自然返回规格编辑与确认流程。

Build 状态和 Project/Workspace 阶段应分开：真实后端中的 Build record 可以保持 `cancelled`，但没有 current Playable 的 Project 应回到 GameSpec 阶段。

## State Transition

```text
build_starting / building_* / validating / auto_fixing
  -> Human Cancel
  -> clear generation and build jobs
  -> no PlayableVersion created
  -> preserve current GameSpec content
  -> Workspace phase = review
  -> active artifact = gamespec
```

用户随后可以：

1. 选择 GameSpec Section 并修改，然后重新确认。
2. 不修改 GameSpec，直接再次执行原有“确认规格并开始构建”Human Gate。

## UI Behavior

- 取消按钮只在首个 Build 仍可取消的运行阶段显示。
- 点击后立即切换到 GAME SPEC，不保留独立的取消完成页。
- Cowork 消息追加“构建已取消。当前 GameSpec 保持不变，可以调整后重新确认。”
- GameSpec 使用现有 Review 和 Confirm UI，不新增“查看构建进度”或“重新构建”专用按钮。
- Projects 列表从领域状态派生为 `GameSpec`，不继续显示 `Building` 或新增 `Build 已取消` 顶层阶段。

## State Ownership

- `projectStore.cancelBuild()` 负责停止 Prototype 的 generation/build jobs，并把 Workspace phase 恢复为 `review`。
- `K02ProjectWorkspace` 只负责在取消成功后选择 `gamespec` tab。
- 不保留 `build_cancelled` 作为 `BuildPhase`。
- 未来真实后端仍应保留不可变的 cancelled Build/Run 记录；该记录不能让 Project 永久停留在 Build 阶段。

## Scope

本次只修正首个 First Playable Build 的取消体验。Controlled Change 继续遵循现有规则：应用修改前可以取消 Change Request，应用后中途取消由 C15 真实 Build API 集成单独处理。

## Verification

- 从 `?screen=build` 点击取消，页面立即显示 GameSpec Review。
- 等待超过原 Build timeline 总时长，状态仍保持 GameSpec，不创建 Playable。
- 不修改 GameSpec 重新确认后可以重新进入 Build。
- 修改 GameSpec 后重新确认也能进入 Build。
- 返回 Projects 显示 `GameSpec`。
- `npx vue-tsc -b` 与 `npx vite build` 通过。

## Non-goals

- 不新增真实 FastAPI cancel endpoint。
- 不改变 Controlled Change 的取消规则。
- 不新增 Build 历史 UI、失败详情或确认弹窗。
- 不引入新的依赖或状态管理框架。
