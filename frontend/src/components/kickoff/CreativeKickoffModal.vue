<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { ArrowRight, Check, X } from 'lucide-vue-next'
import ChoiceCard from './ChoiceCard.vue'
import ChoiceQuestion from './ChoiceQuestion.vue'
import ConfirmationState from './ConfirmationState.vue'
import DesignReadySummary from './DesignReadySummary.vue'
import KickoffMessage from './KickoffMessage.vue'
import RetryState from './RetryState.vue'
import ThinkingIndicator from './ThinkingIndicator.vue'
import { buildScenarioSummary, getFollowUpQuestion, iterationDirections, iterationQuestions, resolveKickoffScenario } from './kickoffFixtures'
import type { Choice, ConfirmedGameDesign, Decision, KickoffPhase, Question } from './kickoffTypes'
import type { CreatorGameDesignDraft } from '../../contracts/creatorGameDesign'

const props = withDefaults(
  defineProps<{
    open: boolean
    originalIdea: string
    templateId?: string | null
    forceMockError?: boolean
    initialDraft?: CreatorGameDesignDraft | null
  }>(),
  { forceMockError: false, initialDraft: null },
)

const emit = defineEmits<{
  close: []
  confirmed: [design: ConfirmedGameDesign]
  draftUpdated: [draft: CreatorGameDesignDraft]
}>()

const phase = ref<KickoffPhase>('clarifying')
const questionIndex = ref(0)
const decisions = ref<Decision[]>([])
const bodyRef = ref<HTMLElement | null>(null)
const dialogRef = ref<HTMLElement | null>(null)
const closeButtonRef = ref<HTMLButtonElement | null>(null)
const hasUsedMockError = ref(false)
const iterationNote = ref<string | null>(null)
const iterationDirection = ref<Choice | null>(null)
const pendingTransition = ref<'next-question' | 'ready' | null>(null)
let activeTimer: number | null = null

const scenario = computed(() => resolveKickoffScenario(props.originalIdea, props.templateId))
const currentQuestion = computed(() => {
  if (questionIndex.value === 0) return scenario.value.coreQuestion
  return getFollowUpQuestion(scenario.value, decisions.value[0]?.answerId)
})
const iterationQuestion = computed(() => iterationQuestions[iterationDirection.value?.id ?? ''] ?? iterationQuestions.custom)
const readySummary = computed(() => buildScenarioSummary(scenario.value, props.originalIdea, decisions.value))
const statusLabel = computed(() => {
  if (phase.value === 'ready' || phase.value === 'iterating') return 'GAME DESIGN READY'
  if (phase.value === 'confirmed' || phase.value === 'confirming') return 'DESIGN CONFIRMATION'
  return '正在完善游戏设计'
})

function restoreDraft(draft: CreatorGameDesignDraft | null) {
  if (!draft) return
  decisions.value = draft.decisions.map((decision) => ({
    questionId: decision.question_id,
    question: decision.question,
    response: decision.response,
    answerId: decision.answer_id,
    answer: decision.answer,
  }))
  questionIndex.value = draft.clarification.question_index
  iterationNote.value = draft.clarification.custom_input || null
  phase.value = draft.clarification.status === 'ready'
    ? 'ready'
    : draft.clarification.status === 'iterating'
      ? 'iterating'
      : draft.clarification.status === 'confirmed'
        ? 'confirmed'
        : 'clarifying'
}

function currentDraft(): CreatorGameDesignDraft {
  const status = phase.value === 'ready' || phase.value === 'confirmed'
    ? 'ready'
    : phase.value === 'iterating' || phase.value === 'iterating-question'
      ? 'iterating'
      : 'clarifying'
  return {
    schema_version: 1,
    original_idea: props.originalIdea,
    project_title: scenario.value.title,
    scenario_id: scenario.value.id,
    summary: {
      title: readySummary.value.title,
      summary: readySummary.value.summary,
      highlights: [...readySummary.value.highlights],
      core_loop: [...readySummary.value.coreLoop],
      progression: [...(readySummary.value.progression ?? [])],
    },
    decisions: decisions.value.map((decision) => ({
      question_id: decision.questionId,
      question: decision.question,
      response: decision.response,
      answer_id: decision.answerId,
      answer: decision.answer,
    })),
    clarification: {
      question_index: questionIndex.value,
      status,
      custom_input: iterationNote.value ?? '',
    },
  }
}

function clearTimer() {
  if (activeTimer !== null) window.clearTimeout(activeTimer)
  activeTimer = null
}

async function scrollToLatest() {
  await nextTick()
  bodyRef.value?.scrollTo({ top: bodyRef.value.scrollHeight, behavior: 'smooth' })
}

function scheduleTransition(target: 'next-question' | 'ready') {
  clearTimer()
  pendingTransition.value = target
  phase.value = 'thinking'
  scrollToLatest()
  activeTimer = window.setTimeout(() => {
    if (props.forceMockError && !hasUsedMockError.value) {
      hasUsedMockError.value = true
      phase.value = 'error'
      scrollToLatest()
      return
    }
    finishTransition()
  }, 820)
}

function finishTransition() {
  if (pendingTransition.value === 'next-question') {
    questionIndex.value = 1
    phase.value = 'clarifying'
  } else {
    phase.value = 'ready'
  }
  pendingTransition.value = null
  scrollToLatest()
}

function chooseAnswer(choice: Choice) {
  const question = currentQuestion.value
  decisions.value.push({ questionId: question.id, question: question.prompt, response: question.response, answerId: choice.id, answer: choice.title })
  scheduleTransition(questionIndex.value === 0 ? 'next-question' : 'ready')
}

function retry() {
  phase.value = 'thinking'
  scrollToLatest()
  clearTimer()
  activeTimer = window.setTimeout(finishTransition, 720)
}

function startIteration() {
  iterationDirection.value = null
  phase.value = 'iterating'
  scrollToLatest()
}

function chooseIterationDirection(choice: Choice) {
  iterationDirection.value = choice
  phase.value = 'iterating-question'
  scrollToLatest()
}

function chooseIterationAnswer(choice: Choice) {
  const question = iterationQuestion.value
  decisions.value.push({ questionId: question.id, question: question.prompt, response: question.response, answerId: choice.id, answer: choice.title })
  iterationNote.value = `${iterationDirection.value?.title ?? '继续完善'}：${choice.title}`
  scheduleTransition('ready')
}

function confirmDesign() {
  phase.value = 'confirming'
  scrollToLatest()
  clearTimer()
  activeTimer = window.setTimeout(() => {
    phase.value = 'confirmed'
    emit('confirmed', {
      originalIdea: props.originalIdea,
      projectTitle: scenario.value.title,
      scenarioId: scenario.value.id,
      summary: readySummary.value,
      decisions: decisions.value.map((decision) => ({ ...decision })),
    })
    scrollToLatest()
  }, 820)
}

function closeModal() {
  if (phase.value === 'confirming') return
  emit('close')
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open) closeModal()
  if (event.key !== 'Tab' || !props.open || !dialogRef.value) return
  const focusable = [...dialogRef.value.querySelectorAll<HTMLElement>('button:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')]
  if (!focusable.length) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(
  () => props.open,
  (open) => {
    document.body.style.overflow = open ? 'hidden' : ''
    if (open) {
      restoreDraft(props.initialDraft)
      window.addEventListener('keydown', handleKeydown)
      nextTick(() => {
        closeButtonRef.value?.focus()
        if (decisions.value.length === 0) bodyRef.value?.scrollTo({ top: 0 })
        else scrollToLatest()
      })
    } else {
      window.removeEventListener('keydown', handleKeydown)
    }
  },
  { immediate: true },
)

watch(
  [phase, questionIndex, decisions, iterationNote],
  () => {
    if (props.open && phase.value !== 'confirmed') emit('draftUpdated', currentDraft())
  },
  { deep: true },
)

onBeforeUnmount(() => {
  clearTimer()
  document.body.style.overflow = ''
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="kickoff-modal">
      <div v-if="open" class="kickoff-overlay">
        <section
          ref="dialogRef"
          class="kickoff-dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="kickoff-title"
          aria-describedby="kickoff-status"
        >
          <header class="kickoff-header">
            <div>
              <span class="kickoff-eyebrow">CREATIVE KICKOFF</span>
              <h2 id="kickoff-title">一起把游戏想清楚</h2>
            </div>
            <div class="kickoff-header-meta">
              <span id="kickoff-status" class="kickoff-status" :class="{ ready: phase === 'ready' }">
                <Check v-if="phase === 'ready'" :size="13" />{{ statusLabel }}
              </span>
              <span class="kickoff-project-name">{{ scenario.title }}</span>
              <button ref="closeButtonRef" type="button" :disabled="phase === 'confirming'" title="关闭" aria-label="关闭创意启动对话" @click="closeModal">
                <X :size="18" />
              </button>
            </div>
          </header>

          <div ref="bodyRef" class="kickoff-body">
            <div v-if="phase === 'confirming' || phase === 'confirmed'" class="confirmation-wrap">
              <ConfirmationState :confirming="phase === 'confirming'" />
            </div>

            <div v-else class="conversation-timeline">
              <KickoffMessage role="user" label="ORIGINAL IDEA">
                <p>{{ originalIdea }}</p>
              </KickoffMessage>

              <template v-for="decision in decisions" :key="decision.questionId">
                <KickoffMessage role="ai">
                  <p v-if="decision.response">{{ decision.response }}</p>
                  <p class="history-question">{{ decision.question }}</p>
                </KickoffMessage>
                <KickoffMessage role="user"><strong>{{ decision.answer }}</strong></KickoffMessage>
              </template>

              <template v-if="phase === 'clarifying'">
                <KickoffMessage role="ai">
                  <p>{{ questionIndex === 0 ? scenario.understanding : currentQuestion.response }}</p>
                </KickoffMessage>
                <ChoiceQuestion :question="currentQuestion" @select="chooseAnswer" />
              </template>

              <ThinkingIndicator v-else-if="phase === 'thinking'" />
              <RetryState v-else-if="phase === 'error'" @retry="retry" />

              <template v-else-if="phase === 'iterating'">
                <KickoffMessage role="ai">
                  <p>当前设计已经可以开始制作。如果你还想继续完善，我们可以深入这些方向：</p>
                </KickoffMessage>
                <section class="iteration-choices" aria-labelledby="iteration-title">
                  <span>继续完善</span>
                  <h3 id="iteration-title">还想把哪个方向想得更清楚？</h3>
                  <div>
                    <ChoiceCard v-for="choice in iterationDirections" :key="choice.id" :choice="choice" @select="chooseIterationDirection" />
                  </div>
                  <ChoiceQuestion
                    :question="{
                      id: 'iteration-custom',
                      response: '',
                      prompt: '',
                      choices: [],
                    }"
                    @select="chooseIterationDirection"
                  />
                </section>
              </template>

              <template v-else-if="phase === 'iterating-question'">
                <KickoffMessage role="ai">
                  <p>{{ iterationQuestion.response }}</p>
                </KickoffMessage>
                <ChoiceQuestion :question="iterationQuestion" @select="chooseIterationAnswer" />
              </template>

              <template v-else-if="phase === 'ready'">
                <KickoffMessage role="ai">
                  <p>太好了，我已经确定这个游戏的核心制作方向。目前的设计已经足够明确，可以开始进入下一阶段。</p>
                  <p v-if="iterationNote" class="iteration-note"><Check :size="13" />已补充完善：{{ iterationNote }}</p>
                </KickoffMessage>
                <DesignReadySummary :summary="readySummary" />
              </template>
            </div>
          </div>

          <footer v-if="phase === 'ready'" class="kickoff-actions">
            <p><Check :size="14" />确认后将锁定当前设计并进入 GameSpec</p>
            <div>
              <button class="kickoff-secondary" type="button" @click="startIteration">继续完善</button>
              <button class="kickoff-primary" type="button" @click="confirmDesign">确认设计 <ArrowRight :size="16" /></button>
            </div>
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>
