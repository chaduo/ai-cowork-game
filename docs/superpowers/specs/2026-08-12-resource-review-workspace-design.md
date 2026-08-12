# Resource Review Workspace v3 Design

## Scope

Incrementally adapt the existing Resource Review page to the approved
`resource_review_final_v6.html` direction. The page remains a deterministic
front-end prototype entered from the published Release state. It does not add a
Resource Library, extraction backend, LLM call, or persistence beyond the
current page lifecycle.

## Workspace Integration

- Keep the existing AI Cowork Game Workspace header, project identity, Release
  provenance, route entry, and parent-owned local state.
- Use two columns only: a resource list on the left and one detail surface in
  the center. Do not add a third inspector or preview rail.
- Put `返回工作区` at the top of the resource list so review is always
  interruptible. Pending resources remain pending when the user returns.
- Use Chinese-first product copy. Do not expose new concepts such as Candidate,
  Resource Preview, Reusable Resource, or a standalone Review completion page.

## Information Architecture

Every selected resource shows its complete evidence without a disclosure:

1. 这是什么
2. 为什么 AI 认为它值得复用
3. 当前游戏中的表现 / 资源预览
4. 会一起保存
5. 不会一起保存
6. 以后可以调整
7. 来源

Gameplay resources show three concrete moments from the current game: NPC
request, visible favor increase, and unlocked relationship event. UI resources
show the UI itself over the current game scene. Visual resources show a grid of
actual material thumbnails rather than a textual inventory.

## Human Gate

- The bottom action bar stays visible while the detail content scrolls.
- Pending actions are `忽略`, `编辑信息`, and `保存为资源`.
- Editing changes name and description only and never saves the resource.
- Save and Ignore leave the current resource selected.
- A processed resource offers Undo and, when another pending resource exists,
  an explicit `查看下一项` action.
- After all resources are processed, keep the same two-column workspace and
  show a light inline completion banner. Do not navigate to a separate page.

## State

- Candidate status remains `pending | saving | saved | ignored`.
- Save may use a short deterministic local timer for visible feedback.
- Undo changes `saved` or `ignored` back to `pending`.
- Next selects the next pending item in list order and is always user-triggered.
- Returning emits cloned candidate state to the existing parent screen.

## Visual Direction

Reuse existing Workspace tokens: white work surfaces, cool gray-green canvas,
blue selection, green completed state, amber pending state, compact Chinese
typography, and restrained square-cornered controls. The memorable element is
the evidence strip for gameplay resources: three framed snapshots of the same
farm world show the reusable behavior as it actually appears in play.

## Verification

Run the existing production build. Browser-check desktop and narrow viewports,
then exercise Edit, Save, Ignore, Undo, Next, Return, and all-processed states.
