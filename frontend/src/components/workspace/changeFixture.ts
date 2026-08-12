import type { ChangePhase, ChangePlan, ChangeProgressStatus, ChangeSource } from './changeTypes'

export const nextStepDirections = [
  {
    id: 'relationship', title: '加强 NPC 关系反馈', icon: 'heart', recommended: true,
    description: '让好感成长更容易被感知。', points: ['增加心形好感条', '增加关系事件', '强化 Favor 变化反馈'],
  },
  {
    id: 'farming', title: '优化经营体验', icon: 'wheat', recommended: false,
    description: '让种植循环获得更清楚的反馈。', points: ['加强作物成长表现', '调整经营节奏', '增加收获反馈'],
  },
  {
    id: 'visual', title: '提升视觉表现', icon: 'palette', recommended: false,
    description: '进一步统一农场、界面和角色表现。', points: ['统一农场画面', '整理 UI 层级', '增强动画反馈'],
  },
]

const sharedReused = ['农场场景', '玩家角色', 'Lucy 角色素材', '农作物素材', '种植系统', '经济系统', 'NPC 委托', 'BGM / 音效']

export function createChangePlan(source: ChangeSource, request?: string): ChangePlan {
  if (source === 'natural_language') {
    return {
      id: 'change-favor-rate', source, sourceLabel: '自己描述',
      originalRequest: request || 'Lucy 的好感度增长太慢了，每次任务从 +5 改成 +10。',
      summary: '调整 Lucy 好感增长速度',
      interpretation: '让每次委托带来的关系成长更明显，同时保留现有委托与视觉素材。',
      changeTypes: ['Parameter'],
      changes: [{ id: 'favor-rate', title: '委托 Favor 奖励', userType: '数值调整', current: '每次完成委托 +5', next: '每次完成委托 +10' }],
      affected: [
        { label: 'GameSpec', detail: '委托奖励参数', technicalScope: 'GameSpec / Relationship / requestReward' },
        { label: '游戏逻辑', detail: 'Favor 奖励读取', technicalScope: 'Gameplay / Favor Rules' },
        { label: 'Validation', detail: '奖励数值与回归检查', technicalScope: 'Validation / Relationship' },
      ],
      reused: sharedReused,
      requiresBuild: true, requiresValidation: true,
      buildReason: 'Favor 奖励会影响运行中的关系规则，因此需要构建新的工作版本并重新验证。',
      scopeExpected: ['GameSpec / Relationship', 'Gameplay / Favor Rules', 'Validation / Relationship'],
      progress: createProgress('更新 Favor 奖励', '确认关系 UI 无需修改'),
      changedChecks: [
        { id: 'favor-reward', label: '完成委托后 Favor 增加 10' },
        { id: 'favor-display', label: 'Favor 数值在界面中正确显示' },
      ],
      regressionChecks: createRegressionChecks(),
    }
  }

  if (source === 'suggested_next_step' && request === '优化经营体验') {
    return {
      id: 'change-farming-feedback', source, sourceLabel: '推荐的下一步',
      originalRequest: request,
      summary: '优化经营体验',
      interpretation: '缩短第一轮作物等待时间，并让成熟与收获反馈更容易被看见。',
      changeTypes: ['Parameter', 'Visual'],
      changes: [
        { id: 'crop-duration', title: '作物成长节奏', userType: '数值调整', current: '第一轮成熟需要 60 秒', next: '第一轮成熟需要 45 秒' },
        { id: 'harvest-feedback', title: '收获反馈', userType: '视觉表现', next: '成熟时强化描边，收获时显示短暂产出反馈' },
      ],
      affected: [
        { label: 'GameSpec', detail: '作物成长参数', technicalScope: 'GameSpec / Farming' },
        { label: '游戏逻辑', detail: '成长计时读取', technicalScope: 'Gameplay / Farming Rules' },
        { label: '界面', detail: '成熟与收获反馈', technicalScope: 'UI / Farming Feedback' },
        { label: 'Validation', detail: '经营循环与回归检查', technicalScope: 'Validation / Farming' },
      ],
      reused: sharedReused,
      requiresBuild: true, requiresValidation: true,
      buildReason: '成长参数和运行时反馈均会改变游戏内容，因此需要构建新的工作版本并重新验证。',
      scopeExpected: ['GameSpec / Farming', 'Gameplay / Farming Rules', 'UI / Farming Feedback'],
      progress: createProgress('更新作物成长参数', '更新成熟与收获反馈'),
      changedChecks: [
        { id: 'crop-duration', label: '第一轮作物在 45 秒后成熟' },
        { id: 'harvest-feedback', label: '成熟与收获反馈正确显示' },
      ],
      regressionChecks: createRegressionChecks(),
    }
  }

  if (source === 'suggested_next_step' && request === '提升视觉表现') {
    return {
      id: 'change-visual-cohesion', source, sourceLabel: '推荐的下一步',
      originalRequest: request,
      summary: '提升视觉表现',
      interpretation: '统一农场 HUD 的信息层级，并强化已有动作反馈；不重新生成角色或场景素材。',
      changeTypes: ['Visual'],
      changes: [
        { id: 'hud-hierarchy', title: '界面层级', userType: '视觉表现', current: '状态信息权重接近', next: '强化核心状态，降低辅助信息的视觉权重' },
        { id: 'action-feedback', title: '动作反馈', userType: '视觉表现', next: '使用现有素材增加种植与收获的短暂反馈' },
      ],
      affected: [
        { label: 'GameSpec', detail: '界面表现配置', technicalScope: 'GameSpec / Presentation' },
        { label: '界面', detail: 'HUD 与动作反馈', technicalScope: 'UI / Game Feedback' },
        { label: 'Validation', detail: '可读性与玩法回归检查', technicalScope: 'Validation / Presentation' },
      ],
      reused: sharedReused,
      requiresBuild: true, requiresValidation: true,
      buildReason: '运行中的界面表现会变化，因此复用现有素材后重新构建并验证工作版本。',
      scopeExpected: ['GameSpec / Presentation', 'UI / Game Feedback', 'Validation / Presentation'],
      progress: createProgress('确认玩法逻辑保持不变', '更新 HUD 与动作反馈'),
      changedChecks: [
        { id: 'hud-hierarchy', label: '核心状态具有清楚的信息层级' },
        { id: 'action-feedback', label: '种植与收获反馈正确显示' },
      ],
      regressionChecks: createRegressionChecks(),
    }
  }

  return {
    id: 'change-relationship-feedback', source, sourceLabel: source === 'gamespec_direct_edit' ? 'GameSpec 直接修改' : '推荐的下一步',
    originalRequest: request || '加强 NPC 关系反馈',
    summary: '加强 NPC 关系反馈',
    interpretation: '好感达到 30 时触发关系事件，并增加一个更明显的心形好感条。',
    changeTypes: ['Gameplay', 'Visual'],
    changes: [
      { id: 'relationship-event', title: '关系规则', userType: '玩法规则', current: '通过多个委托持续积累 Favor', next: 'Favor ≥ 30 → 触发关系成长事件' },
      { id: 'favor-hud', title: '关系反馈', userType: '视觉表现', next: '增加心形 Favor Bar，Favor 改变时同步更新' },
    ],
    affected: [
      { label: 'GameSpec', detail: '关系规则', technicalScope: 'GameSpec / Relationship' },
      { label: '游戏逻辑', detail: 'Favor / Relationship Event', technicalScope: 'Gameplay / Relationship Rules' },
      { label: '界面', detail: 'Relationship HUD', technicalScope: 'UI / Relationship HUD' },
      { label: 'Validation', detail: '重新验证关系反馈', technicalScope: 'Validation / Relationship' },
    ],
    reused: sharedReused,
    requiresBuild: true, requiresValidation: true,
    buildReason: '玩法规则会影响运行中的游戏，因此需要创建工作版本、完整构建并验证；当前 Playable v1 会安全保留。',
    scopeExpected: ['GameSpec / Relationship', 'Gameplay / Relationship Rules', 'UI / Relationship HUD'],
    progress: createProgress('更新关系规则', '更新好感 UI'),
    changedChecks: [
      { id: 'relationship-trigger', label: 'Favor 达到 30 时触发关系事件' },
      { id: 'favor-hud-refresh', label: '心形好感条正确显示并随 Favor 更新' },
    ],
    regressionChecks: createRegressionChecks(),
  }
}

function createProgress(gameplayLabel: string, visualLabel: string) {
  return [
    { id: 'prepare' as const, label: '准备当前稳定版本', detail: '从 Playable v1 创建隔离的工作版本。' },
    { id: 'reuse' as const, label: '复用未受影响内容', detail: '继续使用农场、角色、系统和音频。' },
    { id: 'gameplay' as const, label: gameplayLabel, detail: '只更新 ChangePlan 中声明的关系规则。' },
    { id: 'visual' as const, label: visualLabel, detail: '更新关系反馈，现有角色素材继续复用。' },
    { id: 'scope' as const, label: '修改范围检查', detail: '确认修改只发生在预期范围。' },
    { id: 'build' as const, label: '构建工作版本', detail: '重新构建完整运行版本。' },
    { id: 'validation' as const, label: '修改验证', detail: '验证新行为并检查旧玩法没有退化。' },
  ]
}

function createRegressionChecks() {
  return [
    { id: 'quest', label: 'NPC 委托仍然正常' },
    { id: 'favor', label: 'Favor 仍然可以正常增加' },
    { id: 'farming', label: '种植 / 收获循环正常' },
    { id: 'startup', label: '游戏可以正常启动' },
  ]
}

const activeStep: Partial<Record<ChangePhase, number>> = {
  preparing_working_build: 0,
  reusing_unaffected_content: 1,
  applying_gameplay_change: 2,
  applying_visual_change: 3,
  checking_scope: 4,
  scope_violation: 4,
  building_working_version: 5,
  validating_change: 6,
  auto_fixing_change: 6,
  validation_complete_change: 7,
  playable_v2_ready: 7,
  version_history: 7,
}

export function getChangeStepStatus(index: number, phase: ChangePhase): ChangeProgressStatus {
  const active = activeStep[phase] ?? -1
  if (phase === 'scope_violation' && index === 4) return 'failed'
  if (index < active || active === 7) return 'completed'
  if (index === active) return 'active'
  return 'upcoming'
}

export function isChangeBuildPhase(phase: ChangePhase): boolean {
  return (activeStep[phase] ?? -1) >= 0 && !['playable_v2_ready', 'version_history'].includes(phase)
}
