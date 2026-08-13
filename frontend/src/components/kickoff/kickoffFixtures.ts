import type { Choice, Decision, KickoffScenario, Question, ReadySummary } from './kickoffTypes'

const choice = (data: Choice): Choice => data

const farmCoreChoices: Choice[] = [
  choice({
    id: 'farming-first',
    number: '01',
    title: '种田养殖为主，赚钱是主线',
    description: '养殖 / 种植 → 产出 → 卖钱 → 升级 / 扩张 → 继续经营',
    impact: '经营 · 成长 · 资源规划',
    loopLabel: '经营成长',
  }),
  choice({
    id: 'relationship-first',
    number: '02',
    title: 'NPC 攻略 + 恋爱结婚更重要',
    description: '认识 NPC → 完成委托 → 提升关系 → 解锁关系事件 → 结婚',
    impact: '关系成长 · 生活模拟',
    recommended: true,
    loopLabel: '关系成长',
  }),
  choice({
    id: 'legacy-first',
    number: '03',
    title: '代际生育传承最关键',
    description: '培养孩子 → 规划能力 → 完成传承 → 下一代继承家族资产',
    impact: '长期成长 · 家族经营',
    loopLabel: '代际传承',
  }),
]

const farmFollowUps: Record<string, Question> = {
  'farming-first': {
    id: 'farm-economy',
    response: '好，经营成长是主要满足感。接下来需要确定资源循环如何持续推动农场变大。',
    prompt: '你希望经营成长主要通过什么方式推进？',
    choices: [
      choice({ id: 'season-orders', number: '01', title: '季节订单 + 设施升级', description: '完成季节订单获得资金，逐步解锁更高效的设施和作物。', impact: '目标明确 · 节奏稳定' }),
      choice({ id: 'farm-expansion', number: '02', title: '农场扩张 + 家族分工', description: '扩大土地和养殖规模，让家庭成员各自负责一条生产线。', impact: '成长明显 · 规划更强' }),
      choice({ id: 'risk-reward', number: '03', title: '资源取舍 + 市场风险', description: '根据市场变化选择投入方向，在稳定收益和高风险机会之间取舍。', impact: '策略更强 · 变化更多' }),
    ],
  },
  'relationship-first': {
    id: 'relationship-mechanic',
    response: '好，那恋爱关系就是长期主线，种田和经营主要负责为关系推进提供资源。',
    prompt: '你希望恋爱关系主要通过什么方式推进？',
    choices: [
      choice({ id: 'requests-affection', number: '01', title: '完成委托 + 好感提升', description: '完成 NPC 的任务、送礼和日常互动，逐步提高好感并解锁结婚条件。', impact: '目标明确 · 容易规划', recommended: true }),
      choice({ id: 'farm-story', number: '02', title: '经营影响 + 剧情事件', description: '农场发展会触发不同关系事件，关键选择决定关系是否继续。', impact: '叙事更强 · 分支更多' }),
      choice({ id: 'social-competition', number: '03', title: '多方竞争 + 资源取舍', description: '存在多个关系对象和竞争压力，需要分配时间和资源。', impact: '策略更强 · 复杂度更高' }),
    ],
  },
  'legacy-first': {
    id: 'legacy-mechanic',
    response: '明白，代际传承是长期目标。接下来要确定上一代的积累如何变成下一代的起点。',
    prompt: '你希望下一代主要继承什么？',
    choices: [
      choice({ id: 'assets-inherit', number: '01', title: '资产与农场设施', description: '下一代继承土地、设施和资金，把经营规模继续扩大。', impact: '成长稳定 · 经营延续' }),
      choice({ id: 'skills-inherit', number: '02', title: '技能与家族特长', description: '上一代培养的技能会转化为下一代的天赋与新玩法。', impact: '差异明显 · 长期成长' }),
      choice({ id: 'story-inherit', number: '03', title: '关系与家族故事', description: '下一代继承村庄关系和家族故事，开启新的生活目标。', impact: '叙事更强 · 情感延续' }),
    ],
  },
}

const genericCoreChoices: Choice[] = [
  choice({ id: 'challenge-first', number: '01', title: '即时操作与挑战为主', description: '玩家持续行动、应对压力，并在一次次挑战中掌握节奏。', impact: '反馈直接 · 上手明确', loopLabel: '挑战反馈' }),
  choice({ id: 'exploration-first', number: '02', title: '探索成长与收集为主', description: '玩家探索空间、发现目标并收集资源，让世界逐步展开。', impact: '发现感强 · 节奏舒展', recommended: true, loopLabel: '探索成长' }),
  choice({ id: 'character-first', number: '03', title: '角色关系与故事为主', description: '玩家通过互动和选择推进角色关系，让故事回应自己的行动。', impact: '情感投入 · 选择有意义', loopLabel: '关系叙事' }),
]

const genericFollowUps: Record<string, Question> = {
  'challenge-first': {
    id: 'challenge-pressure',
    response: '好，直接的操作反馈会是玩家留下来的原因。接下来确定挑战的压力从哪里来。',
    prompt: '挑战主要通过什么方式制造张力？',
    choices: [
      choice({ id: 'time-pressure', number: '01', title: '时间与节奏压力', description: '玩家需要在倒计时或节奏变化中做出及时决定。', impact: '紧张 · 反馈快速' }),
      choice({ id: 'enemy-pressure', number: '02', title: '敌人与空间压力', description: '敌人、地形或有限空间迫使玩家不断调整位置。', impact: '空间感 · 操作明确' }),
      choice({ id: 'resource-pressure', number: '03', title: '资源与风险压力', description: '玩家在有限资源和更高收益之间做出取舍。', impact: '策略感 · 重玩价值' }),
    ],
  },
  'exploration-first': {
    id: 'exploration-motivation',
    response: '好，探索会是玩家理解这个世界的主要方式。接下来让我们确定发现如何持续产生目标。',
    prompt: '探索如何持续给玩家新的目标？',
    choices: [
      choice({ id: 'collection-map', number: '01', title: '收集图鉴与区域解锁', description: '发现新物件和新区域，逐步完成一张可回看的世界图鉴。', impact: '目标清楚 · 完成感强' }),
      choice({ id: 'clue-story', number: '02', title: '线索与隐藏故事', description: '通过环境线索拼出世界背景，探索会不断改变玩家的理解。', impact: '沉浸更强 · 叙事驱动' }),
      choice({ id: 'upgrade-route', number: '03', title: '能力成长与路线选择', description: '探索获得新能力，解锁不同路线和更深的挑战区域。', impact: '成长明确 · 选择更多' }),
    ],
  },
  'character-first': {
    id: 'character-motivation',
    response: '明白，角色关系会是玩家继续行动的理由。接下来确定关系如何回应玩家。',
    prompt: '角色关系主要通过什么方式回应玩家？',
    choices: [
      choice({ id: 'quests-dialogue', number: '01', title: '委托与对话推进', description: '完成角色委托并通过对话了解他们，逐步解锁关系节点。', impact: '目标明确 · 节奏可控' }),
      choice({ id: 'choice-consequence', number: '02', title: '选择与后果推进', description: '玩家的重要选择会改变角色态度与后续事件。', impact: '代入更强 · 分支更多' }),
      choice({ id: 'daily-routine', number: '03', title: '日常互动与陪伴推进', description: '通过持续的日常相处，让关系在小事件中自然变化。', impact: '生活感 · 情绪细腻' }),
    ],
  },
}

const genericFallback: Question = {
  id: 'generic-follow-up',
  response: '这个方向已经清楚了。接下来确定玩家通过什么行动持续感受到它。',
  prompt: '玩家会通过什么行动持续推进这个体验？',
  choices: [
    choice({ id: 'repeat-action', number: '01', title: '重复行动，逐步掌握节奏', description: '玩家通过反复练习和反馈，把一次次行动做得更好。', impact: '上手直接 · 成长清楚' }),
    choice({ id: 'discover-action', number: '02', title: '发现目标，逐步展开世界', description: '玩家通过发现新目标和新线索，让体验不断向前展开。', impact: '探索感 · 发现驱动' }),
    choice({ id: 'choose-action', number: '03', title: '做出选择，改变后续结果', description: '玩家的决定会改变角色、空间或故事的后续方向。', impact: '参与感 · 结果可见' }),
  ],
}

const coffeeScenario: KickoffScenario = {
  id: 'coffee-shop',
  title: '咖啡店故事',
  understanding: '这是一个围绕咖啡店日常、常客故事和关系成长展开的温暖模拟游戏。',
  coreQuestion: {
    id: 'coffee-core-experience', response: '我先确认咖啡经营和人物关系谁是玩家每天回来的主要理由。',
    prompt: '玩家最主要沉浸在哪种体验？', choices: [
      choice({ id: 'coffee-relationships', number: '01', title: '经营咖啡店并认识常客', description: '接待顾客、完成订单，在日常互动中逐步了解店员与常客。', impact: '经营 · 关系成长', recommended: true, loopLabel: '关系成长' }),
      choice({ id: 'coffee-business', number: '02', title: '把咖啡店经营得更好', description: '制作饮品、服务顾客并升级店铺设施。', impact: '经营 · 升级', loopLabel: '经营成长' }),
      choice({ id: 'coffee-story', number: '03', title: '通过小故事认识每个人', description: '用对话和选择推进顾客的日常故事。', impact: '叙事 · 互动', loopLabel: '故事推进' }),
    ],
  },
  followUps: {
    'coffee-relationships': { id: 'coffee-relationship-mechanic', response: '关系成长会成为经营循环之外的长期回报。', prompt: '关系主要通过什么方式推进？', choices: [
      choice({ id: 'coffee-requests', number: '01', title: '对话与完成顾客委托', description: '完成 NPC 委托、日常互动和小事件，提升好感并解锁关系事件。', impact: '目标明确 · 容易规划', recommended: true }),
      choice({ id: 'coffee-routine', number: '02', title: '每天见面与陪伴', description: '通过持续出现和日常对话，让关系自然变化。', impact: '生活感 · 节奏舒展' }),
      choice({ id: 'coffee-choices', number: '03', title: '关键选择与剧情事件', description: '重要选择改变顾客态度和后续事件。', impact: '叙事更强 · 分支更多' }),
    ] },
  },
  genericFollowUp: { id: 'coffee-generic', response: '我们会保留咖啡经营和关系成长两条线。', prompt: '玩家会通过什么行动推进故事？', choices: [
    choice({ id: 'coffee-orders', number: '01', title: '完成订单并和 NPC 互动', description: '用每天的订单和互动推进关系。', impact: '反馈清楚' }),
    choice({ id: 'coffee-upgrades', number: '02', title: '升级店铺和菜单', description: '用经营成果解锁更多内容。', impact: '成长明确' }),
    choice({ id: 'coffee-events', number: '03', title: '触发关系事件', description: '在条件满足后进入新的角色事件。', impact: '回报具体' }),
  ] },
  buildSummary: (idea, decisions) => ({
    title: '咖啡店故事',
    summary: `一款围绕咖啡店经营、顾客故事和关系成长展开的温暖模拟游戏。${idea ? '玩家从日常订单和互动中逐步建立重要关系。' : ''}`,
    highlights: ['咖啡订单与店铺经营', '两位常客或店员 NPC', decisions[1]?.answer ?? '对话与委托推进关系'],
    coreLoop: ['接待顾客', '制作咖啡', '完成订单', '推进关系'],
    progression: ['认识常客', '提升好感', '解锁关系事件'],
  }),
}

const iterationQuestions: Record<string, Question> = {
  'npc-depth': {
    id: 'iteration-npc-depth',
    response: '那我们先把关系做得更有辨识度。',
    prompt: 'NPC 的个性主要通过什么方式被玩家记住？',
    choices: [
      choice({ id: 'npc-events', number: '01', title: '专属关系事件', description: '每个重要 NPC 都有一段只会在特定条件下触发的事件。', impact: '记忆点强 · 关系有回报' }),
      choice({ id: 'npc-contrast', number: '02', title: '性格差异与选择反应', description: '不同 NPC 会用不同方式回应玩家的行动和选择。', impact: '差异清楚 · 互动有变化' }),
      choice({ id: 'npc-routine', number: '03', title: '日常习惯与生活细节', description: '通过固定习惯和小对话，让 NPC 在日常里逐渐鲜活。', impact: '生活感 · 情绪细腻' }),
    ],
  },
  'legacy-depth': {
    id: 'iteration-legacy-depth',
    response: '那我们把家族传承的落点再明确一层。',
    prompt: '下一代最应该感受到上一代留下的什么？',
    choices: [
      choice({ id: 'legacy-assets', number: '01', title: '看得见的资产变化', description: '农场、设施或资源让下一代从更高的起点开始。', impact: '反馈直接 · 成长可见' }),
      choice({ id: 'legacy-skills', number: '02', title: '可继承的能力组合', description: '上一代的选择会影响下一代能使用的能力和路线。', impact: '策略更深 · 差异更多' }),
      choice({ id: 'legacy-story', number: '03', title: '持续展开的家族故事', description: '上一代的关系和决定会变成下一代要面对的新故事。', impact: '情感延续 · 叙事更强' }),
    ],
  },
  'farm-depth': {
    id: 'iteration-farm-depth',
    response: '那我们把经营循环的深度再往前推一步。',
    prompt: '农场经营最希望让玩家持续规划什么？',
    choices: [
      choice({ id: 'farm-layout', number: '01', title: '土地与设施布局', description: '玩家通过布局和升级，让有限空间产生更高效率。', impact: '规划感 · 变化可见' }),
      choice({ id: 'farm-market', number: '02', title: '市场与季节取舍', description: '季节和市场变化让每次投入都有不同的收益机会。', impact: '策略感 · 重玩价值' }),
      choice({ id: 'farm-labor', number: '03', title: '时间与家庭分工', description: '玩家在经营、关系和家庭安排之间分配每天的时间。', impact: '生活模拟 · 决策更多' }),
    ],
  },
  'world-tone': {
    id: 'iteration-world-tone',
    response: '那我们让世界的气质也参与到玩家的选择里。',
    prompt: '世界观氛围最希望通过什么方式被感受到？',
    choices: [
      choice({ id: 'world-season', number: '01', title: '季节与日常变化', description: '季节、天气和日常安排让世界持续有呼吸感。', impact: '沉浸感 · 节奏舒展' }),
      choice({ id: 'world-place', number: '02', title: '地点与环境细节', description: '不同地点有自己的故事、物件和可发现的细节。', impact: '探索感 · 世界更具体' }),
      choice({ id: 'world-community', number: '03', title: '村庄共同体关系', description: '村民之间的关系变化让玩家感到自己属于这个地方。', impact: '情感投入 · 关系更广' }),
    ],
  },
}

function truncate(value: string, max = 44) {
  const clean = value.replace(/\s+/g, ' ').trim()
  return clean.length > max ? `${clean.slice(0, max)}…` : clean
}

function buildFarmSummary(idea: string, decisions: Decision[]): ReadySummary {
  const first = farmCoreChoices.find((item) => item.id === decisions[0]?.answerId) ?? farmCoreChoices[1]
  const second = decisions[1]?.answer ?? '完成关键行动'
  const iteration = [...decisions].reverse().find((item) => item.questionId.startsWith('iteration-'))
  const longTerm = first.id === 'farming-first' ? '扩大农场规模' : first.id === 'legacy-first' ? '完成家族传承' : '建立重要关系'
  return {
    title: '多代田园物语',
    summary: `一款以${first.title}为主轴的多代农村生活养成游戏。玩家通过种田和养殖推进${second}，把每天的经营选择转化为${longTerm}，并让下一代继承上一代积累的家族优势。${iteration ? `当前还补充了“${iteration.answer}”方向。` : ''}`,
    highlights: [first.title, second, '种田和养殖为长期目标提供资源', iteration ? `继续完善：${iteration.answer}` : '每一代的选择都会留下可继承的变化'],
    coreLoop: ['Farm', 'Earn', first.loopLabel ?? 'Choose', 'Act', 'Grow'],
    progression: ['Marriage / Milestone', 'Inheritance', 'Next generation'],
  }
}

function buildGenericSummary(idea: string, decisions: Decision[]): ReadySummary {
  const first = genericCoreChoices.find((item) => item.id === decisions[0]?.answerId) ?? genericCoreChoices[1]
  const second = decisions[1]?.answer ?? '发现新的目标'
  const iteration = [...decisions].reverse().find((item) => item.questionId.startsWith('iteration-'))
  return {
    title: '正在成形的游戏设计',
    summary: `围绕「${truncate(idea)}」展开的游戏设计。玩家以${first.title}作为主要体验，通过${second}形成持续的行动、反馈和成长。${iteration ? `当前还补充了“${iteration.answer}”方向。` : ''}`,
    highlights: [first.title, second, first.impact ?? '玩家能清楚感受到行动带来的变化', iteration ? `继续完善：${iteration.answer}` : '后续内容围绕这条体验主线展开'],
    coreLoop: ['Enter the world', first.loopLabel ?? 'Act', 'Get feedback', 'Grow', 'Choose again'],
  }
}

export const farmScenario: KickoffScenario = {
  id: 'farm',
  title: '多代田园物语',
  understanding: '我很喜欢这个“多代家族积累”的农村养成设定！这里同时包含经营、恋爱和代际传承几个很强的方向。',
  coreQuestion: { id: 'core-experience', response: '我先从你描述的多代家族积累出发，确认玩家最主要的长期体验。', prompt: '你希望玩家最主要沉浸在哪种体验？', choices: farmCoreChoices },
  followUps: farmFollowUps,
  genericFollowUp: genericFallback,
  buildSummary: buildFarmSummary,
}

export const genericScenario: KickoffScenario = {
  id: 'generic',
  title: '正在成形的游戏设计',
  understanding: '我先把你描述的核心方向保留下来，再确认玩家最主要的体验重心。这样后面的玩法决定都会围绕你的原始创意展开。',
  coreQuestion: { id: 'generic-core-experience', response: '', prompt: '你希望玩家最主要沉浸在哪种体验？', choices: genericCoreChoices },
  followUps: genericFollowUps,
  genericFollowUp: genericFallback,
  buildSummary: buildGenericSummary,
}

export const iterationDirections: Choice[] = [
  { id: 'npc-depth', title: 'NPC 个性与关系', description: '补充关系对象、个性差异与重要事件。' },
  { id: 'legacy-depth', title: '代际传承', description: '明确下一代继承什么，以及如何开启新世代。' },
  { id: 'farm-depth', title: '农场经营深度', description: '继续细化资源、升级和经营节奏。' },
  { id: 'world-tone', title: '世界观与氛围', description: '确定村庄气质、季节感和生活节奏。' },
]

iterationQuestions.custom = {
  id: 'iteration-custom',
  response: '好，我们把你自己的想法落到一个可以验证的设计决定上。',
  prompt: '这个方向最希望改变玩家的哪一段体验？',
  choices: [
    choice({ id: 'custom-feel', number: '01', title: '让行动反馈更明确', description: '让玩家更快看到自己的决定带来了什么变化。', impact: '反馈直接 · 更容易验证' }),
    choice({ id: 'custom-depth', number: '02', title: '让成长与选择更有深度', description: '让不同路线带来更明显的长期差异。', impact: '策略更强 · 重玩价值' }),
    choice({ id: 'custom-story', number: '03', title: '让世界回应玩家', description: '让角色、环境或故事对玩家的行动做出更具体的回应。', impact: '沉浸更强 · 结果可见' }),
  ],
}

export const readySummary = buildFarmSummary('多代田园物语', [])
export { iterationQuestions }

export function resolveKickoffScenario(idea: string, templateId?: string | null): KickoffScenario {
  const source = `${templateId ?? ''} ${idea}`.toLowerCase()
  if (/种田|养殖|农场|结婚|传承|多代|农村|田园|farm|relationship/.test(source)) return farmScenario
  if (/咖啡|咖啡店|常客|coffee|cafe/.test(source)) return coffeeScenario
  return genericScenario
}

export function buildScenarioSummary(scenario: KickoffScenario, idea: string, decisions: Decision[]) {
  return scenario.buildSummary(idea, decisions)
}

export function getFollowUpQuestion(scenario: KickoffScenario, answerId?: string) {
  return (answerId && scenario.followUps[answerId]) || scenario.genericFollowUp
}
