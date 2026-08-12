import type { BuildEvent, BuildMilestone, BuildMilestoneId, BuildPhase, MilestoneStatus, ValidationCheck } from './buildTypes'

export const buildMilestones: BuildMilestone[] = [
  {
    id: 'foundation', number: '01', title: 'Foundation', summary: '建立可以运行的游戏基础。',
    completedMessage: '游戏骨架已经可以运行，接下来开始实现核心经营玩法。',
    features: ['游戏场景', '玩家角色', '基础移动', '摄像机', '基础 UI'],
    gameSpecSource: 'Build Target · 2D First Playable',
    executionDetails: ['Created game scene shell', 'Connected player input', 'Added camera and HUD layer'],
  },
  {
    id: 'core', number: '02', title: 'Core Gameplay', summary: '跑通第一版农场经营循环。',
    completedMessage: '核心经营循环已经跑通。',
    features: ['玩家移动', '耕地', '播种', '生长', '收获', '出售', 'Money'],
    gameSpecSource: 'Core Gameplay · Farm → Harvest → Sell',
    executionDetails: ['Added crop growth states', 'Connected harvest inventory', 'Connected market exchange'],
  },
  {
    id: 'interaction', number: '03', title: 'NPC & Interaction', summary: '让 Lucy 的委托真正推动关系成长。',
    completedMessage: 'Lucy 的对话、委托和 Favor 循环已经完成。',
    features: ['Lucy NPC', 'NPC 对话', '接受委托', '提交物品', 'Favor', '关系等级'],
    gameSpecSource: 'World & Characters · Lucy',
    executionDetails: ['Added Lucy interaction zone', 'Connected request completion', 'Added relationship state changes'],
  },
  {
    id: 'presentation', number: '04', title: 'Presentation', summary: '把基础素材、声音和界面接入游戏。',
    completedMessage: '第一版场景、角色、作物和声音已经装配完成。',
    features: ['农场背景', '玩家 Sprite', 'Lucy', '动物与作物', 'UI Panel', 'BGM 与反馈音效'],
    gameSpecSource: 'Art Direction · Rural Life',
    executionDetails: ['Loaded 9 visual assets', 'Connected 3 audio assets', 'Applied HUD presentation'],
  },
  {
    id: 'progression', number: '05', title: 'Progression & Goal', summary: '把功能串成一个有完成目标的游戏。',
    completedMessage: '经营、关系目标和代际结局已经连成完整流程。',
    features: ['Favor progression', 'Relationship milestone', 'Marriage condition', 'Inheritance condition', 'Generation change', 'Win state'],
    gameSpecSource: 'Rules & Progression · Completion',
    executionDetails: ['Connected favor thresholds', 'Added relationship completion event', 'Added inheritance and win transitions'],
  },
  {
    id: 'validation', number: '06', title: 'Validation', summary: '按照已确认的 Playable 标准逐项验证。',
    completedMessage: '9 项可玩性标准已经全部通过。',
    features: ['真实输入检查', '经营闭环检查', 'NPC 委托检查', '目标与结局检查', '运行错误检查'],
    gameSpecSource: 'Definition of Playable · 9 checks',
    executionDetails: ['Started deterministic playtest', 'Recorded validation evidence', 'Prepared stable preview artifact'],
  },
]

export const validationChecks: ValidationCheck[] = [
  { id: 'move', label: '玩家可以移动', source: 'Core Gameplay' },
  { id: 'plant', label: '可以种植一种作物', source: 'Definition of Playable' },
  { id: 'harvest', label: '作物可以成熟并收获', source: 'Definition of Playable' },
  { id: 'earn', label: '作物可以兑换资源', source: 'Rules & Progression' },
  { id: 'request', label: 'Lucy 可以提供委托', source: 'World & Characters' },
  { id: 'favor', label: '完成委托能够提高 Favor', source: 'Rules & Progression' },
  { id: 'relationship', label: 'Favor 达标后出现关系事件', source: 'Definition of Playable' },
  { id: 'inheritance', label: '代际传承能够正确触发', source: 'First Playable Scope' },
  { id: 'complete', label: '游戏存在明确完成状态', source: 'Definition of Playable' },
]

export const buildEvents: BuildEvent[] = [
  { id: 'foundation', milestone: 'foundation', label: '完成游戏基础', detail: '场景、玩家移动、摄像机和基础 UI 已经可以运行。' },
  { id: 'core', milestone: 'core', label: '完成核心经营循环', detail: '耕地、播种、成长、收获和出售已经连通。' },
  { id: 'interaction', milestone: 'interaction', label: '加入 Lucy 与关系系统', detail: '对话、委托、物品提交和 Favor 状态已经连通。' },
  { id: 'presentation', milestone: 'presentation', label: '装配游戏表现', detail: '角色、场景、作物、动物、界面和声音已经加入。' },
  { id: 'progression', milestone: 'progression', label: '完成目标与代际流程', detail: '关系目标、传承条件和最终完成状态已经串联。' },
  { id: 'validation', milestone: 'validation', label: '完成可玩性验证', detail: 'Definition of Playable 的 9 项检查全部通过。' },
]

const activeOrder: Record<BuildPhase, number> = {
  build_starting: 0,
  building_foundation: 0,
  building_core: 1,
  building_interaction: 2,
  building_presentation: 3,
  build_error: 3,
  building_progression: 4,
  validating: 5,
  auto_fixing: 5,
  validating_complete: 5,
  playable_ready: 6,
}

export function getMilestoneStatus(id: BuildMilestoneId, phase: BuildPhase): MilestoneStatus {
  const index = buildMilestones.findIndex((milestone) => milestone.id === id)
  const active = activeOrder[phase]
  if (phase === 'build_error' && index === active) return 'failed'
  if (index < active || phase === 'playable_ready') return 'completed'
  if (index === active) return 'active'
  return 'upcoming'
}

export function getCompletedEvents(phase: BuildPhase): BuildEvent[] {
  return buildEvents.filter((event) => getMilestoneStatus(event.milestone, phase) === 'completed')
}

export function isWorkingPreviewAvailable(phase: BuildPhase): boolean {
  return activeOrder[phase] >= 2
}
