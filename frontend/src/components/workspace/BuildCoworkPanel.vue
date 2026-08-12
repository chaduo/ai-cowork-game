<script setup lang="ts">
import { Bot, Check, ChevronDown, Circle, FileCode2, LoaderCircle, Send, TriangleAlert } from 'lucide-vue-next'
import { computed } from 'vue'
import { buildEvents, getCompletedEvents } from './buildFixture'
import type { BuildPhase } from './buildTypes'

const props = defineProps<{ phase: BuildPhase }>()

const stage = computed(() => {
  const labels: Record<BuildPhase, string> = {
    build_starting: '准备 First Playable', building_foundation: 'Foundation', building_core: 'Core Gameplay',
    building_interaction: 'NPC & Interaction', building_presentation: 'Presentation', building_progression: 'Progression & Goal',
    validating: 'Validation', auto_fixing: '自动修复', validating_complete: 'Validation Complete',
    playable_ready: 'First Playable Ready', build_error: 'Presentation · 需要重试',
  }
  return labels[props.phase]
})

const completed = computed(() => getCompletedEvents(props.phase))
const currentEvent = computed(() => buildEvents.find((event) => !completed.value.some((done) => done.id === event.id)))
</script>

<template>
  <aside class="cowork-panel build-cowork-panel" aria-label="Cowork AI Build Activity">
    <header class="cowork-panel-header">
      <div class="cowork-mark"><Bot :size="17" /></div>
      <div><span>COWORK AI</span><strong>First Playable 开发</strong></div>
      <span class="cowork-stage" :class="{ ready: phase === 'playable_ready' }">{{ phase === 'playable_ready' ? 'READY' : 'BUILDING' }}</span>
    </header>

    <div class="cowork-stage-context">
      <span>当前阶段</span><strong>{{ stage }}</strong>
      <p>{{ phase === 'playable_ready' ? '第一版已通过全部验证，可以稳定试玩。' : '按 GameSpec 逐步完成游戏，并保留可追踪的验证证据。' }}</p>
    </div>

    <div class="build-activity" aria-live="polite">
      <p class="build-ai-intro">GameSpec 已确认。我会先完成核心玩法，再补充 NPC、表现和目标系统，最后按照 Playable 标准验证。</p>

      <details v-for="event in completed" :key="event.id" class="activity-event is-done">
        <summary><Check :size="14" /><span><strong>{{ event.label }}</strong><small>{{ event.detail }}</small></span><ChevronDown :size="13" /></summary>
        <div><FileCode2 :size="12" />已记录功能结果与构建证据</div>
      </details>

      <div v-if="phase === 'build_error'" class="activity-current is-error"><TriangleAlert :size="14" /><span><strong>NPC 素材没有完成</strong><small>已完成的游戏逻辑保持不变，等待重试 Presentation。</small></span></div>
      <div v-else-if="phase === 'auto_fixing'" class="activity-current"><LoaderCircle :size="14" class="spin" /><span><strong>正在修复代际触发流程</strong><small>修复后会自动重新验证失败项。</small></span></div>
      <div v-else-if="phase !== 'playable_ready' && currentEvent" class="activity-current"><LoaderCircle :size="14" class="spin" /><span><strong>{{ currentEvent.label }}</strong><small>{{ currentEvent.detail }}</small></span></div>
      <div v-else class="activity-current is-ready"><Check :size="14" /><span><strong>First Playable Ready</strong><small>9 / 9 项可玩性标准已经通过。</small></span></div>
    </div>

    <div class="cowork-composer-wrap">
      <form class="cowork-composer">
        <label for="build-cowork-request">Ask Cowork AI</label>
        <textarea id="build-cowork-request" rows="4" disabled placeholder="首个版本完成后可以继续修改…"></textarea>
        <button type="button" disabled><Send :size="14" />构建期间暂不可修改 <Circle :size="11" /></button>
      </form>
    </div>
  </aside>
</template>
