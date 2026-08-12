import type { ConfirmedGameDesign } from '../kickoff/kickoffTypes'
import type { GameSpecModel, SpecContext } from './workspaceTypes'

export const specContexts: Record<SpecContext['key'], SpecContext> = {
  target: { key: 'target', label: 'First Playable Target', path: ['GameSpec', 'Build Target'] },
  gameplay: { key: 'gameplay', label: 'Gameplay', path: ['GameSpec', 'Gameplay'] },
  characters: { key: 'characters', label: 'NPC / Lucy', path: ['GameSpec', 'World & Characters', 'Lucy'] },
  rules: { key: 'rules', label: 'Rules & Progression', path: ['GameSpec', 'Rules & Progression'] },
  scope: { key: 'scope', label: 'First Playable Scope', path: ['GameSpec', 'MVP Scope'] },
  validation: { key: 'validation', label: 'Definition of Playable', path: ['GameSpec', 'Validation'] },
}

export function createDemoConfirmedDesign(): ConfirmedGameDesign {
  return {
    originalIdea: '我想做一个种田、养殖、赚钱、攻略 NPC、结婚并让下一代继承家业的农村养成游戏。',
    projectTitle: '多代田园物语',
    scenarioId: 'farm',
    decisions: [
      { questionId: 'core-experience', question: '你希望玩家最主要沉浸在哪种体验？', response: '确认核心体验。', answerId: 'relationship-first', answer: 'NPC 攻略 + 恋爱结婚更重要' },
      { questionId: 'relationship-mechanic', question: '你希望恋爱关系主要通过什么方式推进？', response: '确认关系推进方式。', answerId: 'requests-affection', answer: '完成委托 + 好感提升' },
    ],
    summary: {
      title: '多代田园物语',
      summary: '一款以 NPC 关系成长和恋爱结婚为长期主线的多代农村生活养成游戏。',
      highlights: ['NPC 委托 + 好感成长', '种田和养殖提供关系资源', '下一代继承家族资产'],
      coreLoop: ['Farm', 'Earn', 'Complete Requests', 'Build Relationship'],
      progression: ['Marriage', 'Inheritance', 'Next generation'],
    },
  }
}

export function createResourceReuseConfirmedDesign(): ConfirmedGameDesign {
  return {
    originalIdea: '我想做一个经营咖啡店、认识常客，并通过日常互动发展人物关系的温暖故事游戏。',
    projectTitle: '咖啡店故事',
    scenarioId: 'coffee-shop',
    decisions: [
      { questionId: 'core-experience', question: '玩家最重要的体验是什么？', response: '确认核心体验。', answerId: 'coffee-relationships', answer: '经营咖啡店并认识常客' },
      { questionId: 'relationship-mechanic', question: '关系如何推进？', response: '确认关系推进方式。', answerId: 'conversation-tasks', answer: '对话与完成顾客任务' },
    ],
    summary: {
      title: '咖啡店故事',
      summary: '一款围绕咖啡店经营、顾客故事和日常关系成长展开的温暖模拟游戏。',
      highlights: ['咖啡订单与店铺经营', 'Emily 与 Alex 的人物关系', '日常互动触发角色事件'],
      coreLoop: ['接待顾客', '制作咖啡', '获得收入', '改善店铺'],
      progression: ['认识常客', '发展关系', '解锁人物事件'],
    },
  }
}

export function createGameSpecFixture(design: ConfirmedGameDesign): GameSpecModel {
  if (design.scenarioId === 'coffee-shop') {
    return {
      title: '咖啡店故事',
      draftLabel: 'Draft · v1',
      buildTarget: {
        goal: '做出一个可以完成咖啡订单、认识店员与常客，并看到关系变化的第一版可玩闭环。',
        hypothesis: '验证日常经营与人物关系是否能共同驱动玩家继续营业。',
      },
      gameplay: { coreLoop: ['接待顾客', '制作咖啡', '获得收入', '改善店铺'], actions: ['移动', '接受订单', '制作咖啡', '交付饮品', '与 NPC 对话'] },
      characters: {
        player: '咖啡店经营者', playerActions: ['移动', '制作咖啡', '接待顾客', '对话'],
        npcName: 'Emily 与 Alex', npcRole: '店员与常客',
        npcBehaviors: ['Emily 协助店内工作', 'Alex 定期来店', '与玩家进行日常对话'], dialogueStates: ['认识', '熟悉'],
        worldAreas: ['咖啡店营业区', '吧台与制作区', '顾客座位区'],
        primaryNpcs: 'Emily 是店员，Alex 是常客。',
        relationshipGrowth: '玩家可以通过对话和完成任务提升 NPC 关系。',
        favorRules: '',
        relationshipEvents: '达到一定关系后触发新的角色事件。',
        requestRewards: '',
      },
      rules: { progression: ['完成订单', '获得收入', '改善店铺', '认识更多顾客'], completion: '完成 3 个订单并达到 100 金币，结束当天营业。' },
      scope: { included: ['1 间咖啡店', '3 种咖啡订单', 'Emily 与 Alex', '基础经营反馈', '1 个关系事件'], later: ['更多店铺区域', '完整菜单', '更多常客', '分支人物剧情'] },
      validation: ['玩家可以接受并完成订单', '咖啡制作过程可以完成', '收入会正确增加', 'Emily 与 Alex 可以互动', '关系事件可以触发', '当天营业有明确结束状态'],
      updatedSections: [],
    }
  }

  if (design.scenarioId !== 'farm') {
    return {
      title: design.projectTitle,
      draftLabel: 'Draft · v1',
      buildTarget: {
        goal: `做出一个能够验证“${design.summary.highlights[0] ?? '核心体验'}”的完整 2D 可玩闭环。`,
        hypothesis: '验证玩家是否能理解主要目标，并通过重复行动获得清楚的反馈。',
      },
      gameplay: { coreLoop: design.summary.coreLoop, actions: ['移动', '探索', '收集', '互动', '完成目标'] },
      characters: {
        player: '游戏主角', playerActions: ['移动', '探索', '互动'], npcName: '向导 NPC', npcRole: '提供目标与反馈',
        npcBehaviors: ['固定区域活动', '与玩家对话', '发布目标', '根据进度改变对话'], dialogueStates: ['初识', '熟悉'],
        worldAreas: ['1 个主要场景', '玩家活动区', 'NPC 活动区', '目标区域'],
        primaryNpcs: '向导 NPC 会为玩家提供目标。', relationshipGrowth: '完成目标后逐步建立关系。', favorRules: '', relationshipEvents: '推进目标后触发新的对话。', requestRewards: '',
      },
      rules: { progression: ['完成行动', '获得反馈', '推进目标', '触发完成状态'], completion: '完成主要目标并触发明确的结束状态。' },
      scope: { included: ['单个主要场景', '核心移动与互动', '1 个主要 NPC', '1 条完整目标链', '明确完成状态'], later: ['多地图', '更多 NPC', '复杂剧情分支', '深度成长系统'] },
      validation: ['玩家可以移动', '主要交互可以触发', 'NPC 能提供目标', '目标完成后状态会更新', '存在明确完成状态', '无阻塞性运行错误'],
      updatedSections: [],
    }
  }

  return {
    title: '多代田园物语',
    draftLabel: 'Draft · v1',
    buildTarget: {
      goal: '做出一个可以完整体验“经营资源 → 完成 NPC 委托 → 提升关系 → 达成关系目标”的 2D 可玩闭环。',
      hypothesis: '验证 NPC 关系成长是否真的能驱动玩家持续经营农场。',
    },
    gameplay: {
      coreLoop: ['Farm', 'Earn Resources', 'Accept Request', 'Complete Request', 'Gain Favor', 'Unlock Event'],
      actions: ['移动', '种植', '收获', '出售', '与 NPC 对话', '接受委托', '提交物品', '赠送礼物'],
    },
    characters: {
      player: '农场经营者',
      playerActions: ['移动', '种植', '收获', '互动', '完成委托'],
      npcName: 'Lucy',
      npcRole: '主要关系对象',
      npcBehaviors: ['固定区域活动', '与玩家对话', '发布委托', '接受任务物品', '根据好感变化对话'],
      dialogueStates: ['陌生', '熟悉'],
      worldAreas: ['1 个农场区域', '种植区', '动物区', 'NPC 活动区', '简单交易点'],
      primaryNpcs: 'Lucy 是主要关系对象。', relationshipGrowth: '完成 Lucy 的委托和互动可以提升好感。', favorRules: '好感会推动关系阶段变化。', relationshipEvents: '达到关系阶段后解锁特殊事件。', requestRewards: '完成委托会获得好感。',
    },
    rules: {
      progression: ['经营资源', '完成 NPC 委托', '获得 Favor', '关系等级提升', '解锁特殊事件', '达到关系目标'],
      completion: '完成最终关系委托，并达到目标关系等级。',
    },
    scope: {
      included: ['单个农场场景', '种植 / 收获', '基础经济系统', '1 个核心 NPC', 'NPC 委托', 'Favor 成长', '关系完成事件', '简化代际传承结局'],
      later: ['多地图', '多关系 NPC', '完整婚后生活', '完整多代角色成长', '深度育种', '大型剧情分支'],
    },
    validation: ['玩家可以移动', '可以种植并收获一种作物', '作物可以兑换资源', 'Lucy 可以提供至少一个委托', '完成委托能够提高 Favor', 'Favor 达标后出现关系完成事件', '游戏存在明确完成状态', '页面刷新后可以重新启动', '无阻塞性运行错误'],
    updatedSections: [],
  }
}
