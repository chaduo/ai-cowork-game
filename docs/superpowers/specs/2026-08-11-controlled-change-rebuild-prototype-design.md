# Controlled Change & Rebuild Prototype Design

## Goal

Extend the existing workspace from `Playable v1 · Stable` through one safe,
traceable change cycle that ends at `Playable v2 · Stable` and Version History.
The prototype proves that AI can recommend a useful next direction, explain its
interpretation and impact, reuse unaffected work, validate scope, protect the
current playable, repair a failed check, and publish only after validation.

The implementation uses deterministic local fixtures and timers. It does not
connect OpenGame, an LLM, Git, a backend, a real build, Phaser, or asset tools.

## Approved Journey

```text
Playable v1 · Stable
→ recommendations or free-form change
→ Change Request
→ analysis
→ interpretation + affected + reuse
→ human gate
→ Working Build beside stable v1
→ reuse unaffected content
→ gameplay change
→ visual change
→ scope check
→ build working version
→ change validation + regression validation
→ one Favor HUD failure
→ automatic repair
→ all 6 checks pass
→ Playable v2 · Stable
→ Version History
```

The flow stops at Version History. Restore, a second recommendation cycle,
asset-specific editing, Monaco, and real execution remain out of scope.

## Architecture

The existing Project Workspace remains the only shell. A dedicated controlled
change state module owns the new phases and fixed `ChangePlan`; it does not reuse
the first-build milestone model because the user questions are different.

```text
K02ProjectWorkspace
├── existing GameSpec and First Build flows
├── controlled change state/timers
├── ControlledChangeCoworkPanel
└── artifact workspace
    ├── ChangeAnalysisPanel
    ├── ChangeBuildProgress
    ├── ChangeValidationPanel
    ├── change-aware BuildPreview
    └── VersionHistoryDrawer
```

Recommendation selection, free-form language, and a future direct GameSpec edit
all create the same `ChangePlan` shape. The prototype implements the first two
entry points and includes `gamespec_direct_edit` in the source type so the UI
does not require another build system later.

## Visual Direction

- Reuse all Verified Workshop tokens, typography, dimensions, and the existing
  360px Cowork panel.
- New interface copy is Chinese-first and uses normal body sizes for analysis,
  affected scope, reuse scope, and validation results.
- Human confirmation uses the existing approval cyan. System validation uses
  verified green. Working activity remains blue. Blocking scope violations use
  red only in the failed row and recovery notice.
- The signature element is a two-track safety strip:

```text
当前稳定版本  Playable v1 · 稳定   始终可试玩
工作版本      正在加入关系反馈      修改范围受控
```

- Do not use gradients, glow, chat bubbles, dashboards, raw file trees, Git
  terminology, Candidate terminology, or decorative AI effects.

## Recommendation Gate

After the first playable passes, the left Cowork panel summarizes the working
loop and shows three compact stacked direction cards:

1. 加强 NPC 关系反馈, marked `AI 推荐`.
2. 优化经营体验.
3. 提升视觉表现.

A free-form composer remains available. `先继续试玩` collapses the cards and
keeps Preview unchanged; a weak `推荐下一步` action can reopen them. A choice
only creates a Change Request and never implies a roadmap.

## Change Analysis

The main workspace switches to a `修改` artifact after a request. Analysis first
shows the interpreted user goals and user-facing type labels `玩法规则` and
`视觉表现`. It then presents:

- The concrete rule and HUD changes.
- Affected artifact rows: GameSpec, game logic, UI, and Validation.
- Reused content rows: farm scene, player, Lucy sprite, crops, economy, quests,
  and audio.
- A build strategy notice explaining that the full runtime is rebuilt while
  unaffected content is reused and Playable v1 remains safe.

Technical scope is available only through `查看修改范围`. The human gate has
`取消` and `应用修改`; it is not a modal and does not auto-apply.

## Working Build

After confirmation, the two-track safety strip remains at the top. Preview
continues to display `Playable v1 · Stable`; it does not display incomplete
changes. The change artifact shows a change-specific ledger:

```text
准备当前稳定版本
复用未受影响内容
更新关系规则
更新好感 UI
修改范围检查
构建工作版本
修改验证
```

Each active/completed row explains the user-facing outcome. The scope check is
the product representation of allowlist plus diff validation. A deterministic
`scopeError=1` fixture blocks on an unexpected change and only offers
`重新生成修改`; it never offers an unsafe continue action.

## Validation

Validation has two explicit groups:

- 本次修改, 2 checks.
- 回归检查, 4 checks.

The first pass fails only the Favor HUD refresh. The Cowork panel explains the
observable failure and automatic repair. After the repair all 6 checks pass;
only then does the stable pointer change from v1 to v2.

## Preview and Versions

During the Working Build, Preview remains v1 and shows a compact working-status
notice. At success it becomes `Playable v2 · Stable`, adds the heart Favor bar
to the mock HUD, and states that v1 is preserved in history.

The Version History drawer contains only:

- v2, current and stable, NPC relationship feedback enhancement.
- v1, previous stable, initial playable.

There is no Restore button and no follow-on recommendation cycle.

## State Model

```text
showing_recommendations
playing_v1
change_requested
analyzing_change
change_review
preparing_working_build
reusing_unaffected_content
applying_gameplay_change
applying_visual_change
checking_scope
scope_violation
building_working_version
validating_change
auto_fixing_change
validation_complete_change
playable_v2_ready
version_history
```

All transitions are deterministic. Scope retry restarts the working changes
from the last stable v1 baseline. Cancellation is available only before the
human applies the change.

## Acceptance

- Existing K01, Kickoff, GameSpec, First Build, and First Validation still work.
- First Playable completion triggers optional recommendations in the Cowork panel.
- Recommendation and free-form requests converge into one ChangePlan flow.
- Change Analysis makes interpretation, affected content, reuse, and build
  strategy explicit before the human gate.
- Playable v1 remains visible and stable through every Working Build phase.
- Scope violation blocks the flow and preserves v1.
- Validation visibly separates changed behavior from regressions.
- The deterministic Favor HUD failure is automatically repaired.
- Only 6/6 PASS changes the Preview and stable version to v2.
- Version History shows consistent v2/v1 provenance and no Restore action.
- No prohibited backend, Agent, Git, build, code editor, or second iteration is added.

## Self-review

- No placeholders or ambiguous artifact ownership remain.
- The first-build and change-build progress models remain separate.
- All entry points converge before analysis.
- The stable version transition occurs only after validation.
- The normal, skip, free-form, scope-error, repair, and history states are covered.
