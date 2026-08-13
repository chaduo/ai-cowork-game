<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import {
  ArrowDown,
  ArrowRight,
  Check,
  FolderOpen,
  Gamepad2,
  Lightbulb,
  X,
} from 'lucide-vue-next'
import CreativeKickoffModal from '../components/kickoff/CreativeKickoffModal.vue'
import type { ConfirmedGameDesign } from '../components/kickoff/kickoffTypes'
import type { ProjectSession } from '../stores/projectStore'

const props = defineProps<{ projects: ProjectSession[] }>()
const emit = defineEmits<{ enterWorkspace: [design: ConfirmedGameDesign]; openProject: [projectId: string]; resources: [] }>()

type GameTemplate = {
  id: string
  title: string
  description: string
  tags: string[]
  image: string
  initialIdea: string
  alt: string
}

const templates: GameTemplate[] = [
  {
    id: 'survival-escape',
    title: '深夜逃生',
    description: '在场景中移动，躲避不断追踪你的敌人，坚持到倒计时结束。',
    tags: ['移动', '敌人追踪', '生命值'],
    image: '/templates/template-survival.png',
    initialIdea: '做一个玩家需要在封闭场景中躲避敌人追踪，并坚持到倒计时结束的 2D 生存游戏。',
    alt: '橙猫在厨房躲避扫地机器人的俯视角生存游戏',
  },
  {
    id: 'coin-rush',
    title: '金币大搜集',
    description: '探索场景并收集目标物品，在规定时间内达到指定分数。',
    tags: ['收集', '计分', '倒计时'],
    image: '/templates/template-collect.png',
    initialIdea: '做一个玩家在热闹的露天集市探索并收集金币，在倒计时结束前达到目标分数的 2D 游戏。',
    alt: '角色在露天集市沿路线收集金币的俯视角游戏',
  },
  {
    id: 'arena-guard',
    title: '竞技场守卫',
    description: '移动并攻击不断靠近的敌人，在生命值耗尽之前尽可能击败它们。',
    tags: ['攻击', '敌人', '生命值'],
    image: '/templates/template-arena.png',
    initialIdea: '做一个小小守卫在竞技场中移动和攻击机械敌人，并努力守住生命值的 2D 战斗游戏。',
    alt: '橙色守卫在石制竞技场迎战机械敌人的俯视角游戏',
  },
  {
    id: 'mystic-forest',
    title: '神秘森林',
    description: '探索一个小型世界，与 NPC 对话并找到隐藏目标。',
    tags: ['探索', 'NPC', '对话'],
    image: '/templates/template-forest.png',
    initialIdea: '做一个小狐狸探索神秘森林、与向导 NPC 对话，并找到隐藏遗迹目标的 2D 冒险游戏。',
    alt: '小狐狸在森林中与猫头鹰向导交谈并寻找隐藏目标的游戏',
  },
]

const idea = ref('')
const selectedTemplateId = ref<string | null>(null)
const error = ref<string | null>(null)
const templateFlash = ref(false)
const kickoffStarted = ref(false)
const kickoffOpen = ref(false)
const kickoffIdea = ref('')
const creatorRef = ref<HTMLElement | null>(null)
const templateSectionRef = ref<HTMLElement | null>(null)
const ideaInputRef = ref<HTMLTextAreaElement | null>(null)
const createButtonRef = ref<HTMLButtonElement | null>(null)
const forceMockError = new URLSearchParams(window.location.search).get('kickoffError') === '1'

const selectedTemplate = computed(() =>
  templates.find((template) => template.id === selectedTemplateId.value) ?? null,
)
const canCreate = computed(() => idea.value.trim().length > 0)
const projects = computed(() => [...props.projects].sort((left, right) => right.updatedAt - left.updatedAt))

function projectStage(project: ProjectSession): string {
  if (project.releases.length > 0) return 'Released'
  if (project.playableVersions.length > 0) return 'Playable'
  if (project.phase.includes('build') || project.phase.includes('change')) return 'Building'
  return 'GameSpec'
}

function relativeUpdatedAt(updatedAt: number): string {
  const elapsedMinutes = Math.max(0, Math.floor((Date.now() - updatedAt) / 60_000))
  if (elapsedMinutes < 1) return '刚刚更新'
  if (elapsedMinutes < 60) return `${elapsedMinutes} 分钟前更新`
  const elapsedHours = Math.floor(elapsedMinutes / 60)
  if (elapsedHours < 24) return `${elapsedHours} 小时前更新`
  return `${Math.floor(elapsedHours / 24)} 天前更新`
}

function scrollToTemplates() {
  templateSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  window.setTimeout(() => {
    templateFlash.value = true
    window.setTimeout(() => (templateFlash.value = false), 520)
  }, 430)
}

async function chooseTemplate(template: GameTemplate) {
  selectedTemplateId.value = template.id
  idea.value = template.initialIdea
  error.value = null
  creatorRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  await nextTick()
  window.setTimeout(() => {
    ideaInputRef.value?.focus()
    ideaInputRef.value?.setSelectionRange(idea.value.length, idea.value.length)
  }, 480)
}

function clearTemplate() {
  selectedTemplateId.value = null
  ideaInputRef.value?.focus()
}

async function createProject() {
  if (!canCreate.value) return
  error.value = null
  const nextIdea = idea.value.trim()
  if (kickoffStarted.value && nextIdea !== kickoffIdea.value) {
    kickoffOpen.value = false
    kickoffStarted.value = false
    await nextTick()
  }
  if (!kickoffStarted.value) {
    kickoffIdea.value = nextIdea
    kickoffStarted.value = true
  }
  kickoffOpen.value = true
}

async function closeKickoff() {
  kickoffOpen.value = false
  await nextTick()
  createButtonRef.value?.focus()
}

function enterWorkspace(design: ConfirmedGameDesign) {
  window.setTimeout(() => emit('enterWorkspace', design), 900)
}

function onIdeaKeydown(event: KeyboardEvent) {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault()
    createProject()
  }
}
</script>

<template>
  <div class="k01-page">
    <header class="k01-header">
      <a class="k01-brand" href="#creator" aria-label="AI Cowork Game 首页">
        <span class="k01-brand-mark"><Gamepad2 :size="18" stroke-width="1.8" /></span>
        <span>AI Cowork Game</span>
      </a>
      <nav class="k01-global-nav" aria-label="全局导航"><button class="active" type="button"><FolderOpen :size="16" />Projects</button><button type="button" @click="$emit('resources')">我的资源</button></nav>
    </header>

    <main>
      <section v-if="projects.length" class="project-list" aria-labelledby="project-list-title">
        <div class="project-list-heading"><div><span>MY PROJECTS</span><h2 id="project-list-title">我的项目</h2></div><strong>{{ projects.length }}</strong></div>
        <div class="project-list-items">
          <button v-for="project in projects" :key="project.id" class="project-list-item" type="button" @click="$emit('openProject', project.id)">
            <span class="project-list-icon"><Gamepad2 :size="17" /></span>
            <span class="project-list-copy"><strong>{{ project.design.projectTitle }}</strong><small>{{ relativeUpdatedAt(project.updatedAt) }}</small></span>
            <span class="project-list-stage">{{ projectStage(project) }}</span>
            <ArrowRight :size="16" />
          </button>
        </div>
      </section>

      <section id="creator" ref="creatorRef" class="creator-hero" aria-labelledby="creator-title">
        <div class="creator-index" aria-hidden="true"><span>01</span><i></i><span>IDEA</span></div>
        <h1 id="creator-title">把一个想法，变成可玩的游戏</h1>
        <p class="creator-subtitle">描述你想做的游戏，我们会和你一起完成设计、开发和试玩。</p>

        <form class="idea-creator" @submit.prevent="createProject">
          <div class="idea-surface" :class="{ 'has-value': idea.trim() }">
            <textarea
              ref="ideaInputRef"
              v-model="idea"
              aria-label="你想做一个什么游戏？"
              placeholder="例如：做一个橘猫在深夜厨房收集食材，同时躲避巡逻厨师的 2D 游戏……"
              rows="5"
              @keydown="onIdeaKeydown"
            ></textarea>
            <div class="idea-surface-foot">
              <span><Lightbulb :size="14" />角色、玩法、世界观，想到什么就写什么。</span>
              <kbd>⌘ ↵</kbd>
            </div>
          </div>

          <div v-if="selectedTemplate" class="template-origin">
            <span><Check :size="14" />创意起点：{{ selectedTemplate.title }}</span>
            <button type="button" title="移除模板起点" aria-label="移除模板起点" @click="clearTemplate"><X :size="14" /></button>
          </div>

          <p class="template-path">
            直接描述你的游戏，或者
            <button type="button" @click="scrollToTemplates">从模板开始</button>
          </p>

          <button ref="createButtonRef" class="create-game-action" type="submit" :disabled="!canCreate">
            <span>创建游戏</span>
            <ArrowRight :size="17" />
          </button>

          <p v-if="error" class="create-error" role="alert">{{ error }}</p>
        </form>

        <button class="template-scroll-cue" type="button" @click="scrollToTemplates">
          找点灵感 <ArrowDown :size="15" />
        </button>
      </section>

      <section
        id="templates"
        ref="templateSectionRef"
        class="template-gallery"
        :class="{ flash: templateFlash }"
        aria-labelledby="template-title"
      >
        <div class="template-heading">
          <div>
            <span class="template-kicker">PROMPT STARTERS</span>
            <h2 id="template-title">从模板开始</h2>
            <p>不知道从哪里开始？选择一个玩法模板，在它的基础上继续创作。</p>
          </div>
          <span class="template-count">4 个创意起点</span>
        </div>

        <div class="template-grid">
          <button
            v-for="template in templates"
            :key="template.id"
            class="game-template-card"
            :class="{ selected: selectedTemplateId === template.id }"
            type="button"
            @click="chooseTemplate(template)"
          >
            <span class="template-preview">
              <img :src="template.image" :alt="template.alt" />
              <span v-if="selectedTemplateId === template.id" class="selected-mark"><Check :size="15" />已选</span>
            </span>
            <span class="template-card-body">
              <strong>{{ template.title }}</strong>
              <span class="template-description">{{ template.description }}</span>
              <span class="template-tags">
                <span v-for="tag in template.tags" :key="tag">{{ tag }}</span>
              </span>
              <span class="use-template">使用此模板 <ArrowRight :size="14" /></span>
            </span>
          </button>
        </div>
      </section>
    </main>

    <CreativeKickoffModal
      v-if="kickoffStarted"
      :open="kickoffOpen"
      :original-idea="kickoffIdea"
      :template-id="selectedTemplateId"
      :force-mock-error="forceMockError"
      @close="closeKickoff"
      @confirmed="enterWorkspace"
    />
  </div>
</template>
