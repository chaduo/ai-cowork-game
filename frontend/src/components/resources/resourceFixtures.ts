import type { ResourceCandidate } from './resourceTypes'
import type { ProjectSession } from '../../stores/projectStore'
import type { ReleaseRecord } from '../workspace/releaseTypes'

export function createResourceCandidates(session: ProjectSession, release: ReleaseRecord): ResourceCandidate[] {
  const provenance = {
    projectName: session.spec.title,
    releaseVersion: `Release v${release.version}`,
    playableVersion: `Playable v${release.basedOnPlayable}`,
    gameSpecVersion: `GameSpec v${release.basedOnGameSpec}`,
  }
  const checks = { boundaryChecked: true, projectSpecificContentRemoved: true, parameterizable: true }
  return [
    {
      id: 'relationship-system', name: 'NPC 关系系统', type: 'gameplay', status: 'pending', recommendation: 'recommended', cardSummary: 'NPC 委托 · 好感成长 · 关系事件',
      summary: '把 NPC 委托、好感增长和关系事件整理成一套以后可以继续使用的关系玩法。',
      reuseReason: '它和当前农场玩法绑定得不深，可以复用于恋爱、经营、角色扮演和生活模拟等包含 NPC 关系成长的游戏。AI 建议保留关系状态、好感阈值和事件触发方式，把具体角色与农场内容留在原游戏中。',
      reusableFor: ['RPG', '恋爱', '模拟经营', '生活模拟'], removedProjectContent: ['Lucy', '农场', '农作物'],
      included: ['NPC 委托与好感规则', '关系阶段', '关系事件触发'], excluded: ['Lucy 这个具体角色', '农场经营系统', '农作物素材'],
      configurableFields: [
        { name: '目标 NPC', defaultValue: '可替换', description: '绑定目标项目中的任意结构化 NPC。' },
        { name: '好感阈值', defaultValue: '30 / 50 / 80', description: '达到对应数值后进入新的关系阶段。' },
        { name: '任务奖励', defaultValue: '好感 +5', description: '调整每次完成委托增加的好感。' },
        { name: '关系事件', defaultValue: '开启', description: '允许阈值触发结构化事件。' },
      ], provenance, extractionChecks: checks,
      matchSignals: { section: 'characters', signals: ['委托', '好感', '关系', 'NPC'] },
      reuseDefaults: {
        favorMin: 0,
        favorMax: 100,
        thresholds: [30, 50, 80],
        requestReward: 5,
        importantEventReward: 10,
      },
    },
    {
      id: 'favor-hud', name: '好感心形 UI', type: 'ui', status: 'pending', recommendation: 'worth_saving', cardSummary: '关系数值 · 心形进度 · 变化反馈',
      summary: '用于展示角色好感变化的心形进度 UI，让玩家能直接看到关系成长。',
      reuseReason: '它只需要一个关系数值就可以工作，不依赖农场玩法，可以复用于亲密度、声望和伙伴关系等系统。AI 建议保留心形显示、数值反馈和变化动画，把角色头像、行为和任务逻辑留在原游戏中。',
      reusableFor: ['关系进度', '声望系统', '伙伴亲密度'], removedProjectContent: ['Lucy 头像', '当前任务文案'],
      included: ['心形进度条', '好感数值显示', '数值变化反馈'], excluded: ['Lucy 头像', 'NPC 行为', '任务逻辑'],
      configurableFields: [
        { name: '最大好感值', defaultValue: '100', description: '进度条的最大状态值。' },
        { name: '显示样式', defaultValue: '心形', description: '也可以改为普通进度条。' },
        { name: '显示数值', defaultValue: '开启', description: '同时呈现当前值与最大值。' },
        { name: '变化反馈', defaultValue: '轻微跳动', description: '好感改变时的短暂反馈。' },
      ], provenance, extractionChecks: checks,
    },
    {
      id: 'rural-ui-kit', name: '田园 UI 套件', type: 'visual', status: 'pending', recommendation: 'adjust_first', cardSummary: '面板 · 按钮 · 工具栏 · 对话框',
      summary: '一组统一的田园像素风界面素材，包括面板、按钮、工具栏、对话框、背包格子和状态条。',
      reuseReason: '这些界面已经形成统一的视觉语言，而且不依赖某个角色或具体玩法。以后制作新的田园、经营或模拟类游戏时，可以直接作为界面起点，减少重复设计和生成。',
      reusableFor: ['乡村模拟', '像素 RPG', '经营游戏'], removedProjectContent: ['多代田园物语标题', 'Lucy 头像'],
      included: ['木质面板', '按钮样式', '工具栏', '对话框', '背包格子', '状态条'], excluded: ['玩法逻辑', 'NPC 角色', '农作物素材'],
      configurableFields: [
        { name: '整体色调', defaultValue: '暖木色', description: '可以调整为偏暖或偏深。' },
        { name: '按钮尺寸', defaultValue: '中', description: '适配不同页面的操作密度。' },
        { name: '像素比例', defaultValue: '2 倍', description: '适配不同游戏分辨率。' },
      ], provenance, extractionChecks: checks,
    },
  ]
}
