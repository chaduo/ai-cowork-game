<script setup lang="ts">
import { ArrowRight, Bot, Check, Circle, LoaderCircle, Play, RotateCcw, Send, ShieldCheck, TriangleAlert } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import NextStepRecommendations from './NextStepRecommendations.vue'
import type { ChangePhase, ChangePlan } from './changeTypes'

const props = defineProps<{ phase: ChangePhase; plan: ChangePlan | null }>()
const emit = defineEmits<{
  select: [directionId: string]
  submit: [text: string]
  continuePlaying: []
  showRecommendations: []
}>()

const request = ref('')

const stage = computed(() => {
  const labels: Record<ChangePhase, string> = {
    showing_recommendations: 'Playable v1 · 稳定', playing_v1: '继续试玩',
    change_requested: '已收到修改要求', analyzing_change: '正在分析修改', change_review: '修改分析',
    preparing_working_build: '准备工作版本', reusing_unaffected_content: '直接复用',
    applying_gameplay_change: '更新玩法规则', applying_visual_change: '更新视觉反馈',
    checking_scope: '修改范围检查', scope_violation: '修改范围异常',
    building_working_version: '构建工作版本', validating_change: '修改验证',
    auto_fixing_change: '正在修复', validation_complete_change: 'Validation Passed',
    playable_v2_ready: 'Playable v2 · 稳定', version_history: '版本历史',
  }
  return labels[props.phase]
})

const isWorking = computed(() => [
  'preparing_working_build', 'reusing_unaffected_content', 'applying_gameplay_change',
  'applying_visual_change', 'checking_scope', 'scope_violation', 'building_working_version',
  'validating_change', 'auto_fixing_change', 'validation_complete_change',
].includes(props.phase))

function submitRequest() {
  const text = request.value.trim()
  if (!text) return
  emit('submit', text)
  request.value = ''
}
</script>

<template>
  <aside class="cowork-panel controlled-change-cowork" aria-label="Cowork AI Controlled Change">
    <header class="cowork-panel-header">
      <div class="cowork-mark"><Bot :size="17" /></div>
      <div><span>COWORK AI</span><strong>安全修改游戏</strong></div>
      <span class="cowork-stage" :class="{ ready: phase === 'playable_v2_ready' || phase === 'version_history' }">{{ isWorking ? 'WORKING' : 'ACTIVE' }}</span>
    </header>

    <div class="cowork-stage-context">
      <span>当前阶段</span><strong>{{ stage }}</strong>
      <p>{{ isWorking ? '当前稳定版本不会被覆盖。' : '从稳定版本继续完善游戏。' }}</p>
    </div>

    <div class="controlled-change-body" aria-live="polite">
      <template v-if="phase === 'showing_recommendations'">
        <div class="first-playable-summary">
          <span><Check :size="14" />第一版已经完成</span>
          <p>核心行动、关系反馈和阶段目标已经形成完整可玩循环。</p>
        </div>
        <p class="change-ai-copy">接下来可以继续完善其中一个方向。推荐只是起点，你也可以自己描述。</p>
        <NextStepRecommendations @select="$emit('select', $event)" />
        <button class="continue-playing" type="button" @click="$emit('continuePlaying')"><Play :size="13" />先继续试玩</button>
      </template>

      <template v-else-if="phase === 'playing_v1'">
        <div class="playing-v1-note"><Play :size="16" /><span><strong>继续试玩 Playable v1</strong><small>不会创建工作版本，也不会改变当前游戏。</small></span></div>
        <p class="change-ai-copy">随时告诉我你想修改什么，我也可以继续帮你推荐下一步。</p>
        <button class="show-recommendations" type="button" @click="$emit('showRecommendations')">推荐下一步 <ArrowRight :size="13" /></button>
      </template>

      <template v-else-if="phase === 'change_requested' || phase === 'analyzing_change' || phase === 'change_review'">
        <div class="change-conversation is-user"><span>你</span><p>{{ plan?.originalRequest }}</p></div>
        <div class="change-conversation is-ai">
          <span>AI</span>
          <p v-if="phase === 'change_requested'">我会重点处理这次修改，不改变当前的农场经营核心。</p>
          <p v-else-if="phase === 'analyzing_change'"><LoaderCircle :size="13" class="spin" />正在分析这次修改会影响哪些内容…</p>
          <p v-else>修改分析已经准备好。请先确认我理解得是否正确，以及哪些内容会直接复用。</p>
        </div>
      </template>

      <template v-else-if="isWorking">
        <div class="stable-protection"><ShieldCheck :size="15" /><span><strong>Playable v1 仍然稳定</strong><small>AI 正在隔离的工作版本中修改。</small></span></div>
        <div class="change-conversation is-ai">
          <span>AI</span>
          <p v-if="phase === 'reusing_unaffected_content'">正在复用农场场景、角色、种植、经济和音频内容。</p>
          <p v-else-if="phase === 'applying_gameplay_change'">关系成长事件现在会在 Favor 达到 30 时触发。</p>
          <p v-else-if="phase === 'applying_visual_change'">正在加入关系反馈条；现有角色素材继续复用。</p>
          <p v-else-if="phase === 'checking_scope'">正在确认修改只发生在预期范围…</p>
          <p v-else-if="phase === 'scope_violation'"><TriangleAlert :size="13" />检测到超出预期范围的修改，工作版本已停止。</p>
          <p v-else-if="phase === 'building_working_version'">因为玩法规则发生变化，正在重新构建完整运行版本。</p>
          <p v-else-if="phase === 'validating_change'">关系事件已经触发，但心形好感条还没有跟随 Favor 刷新。</p>
          <p v-else-if="phase === 'auto_fixing_change'"><LoaderCircle :size="13" class="spin" />正在修复好感条的状态同步问题。</p>
          <p v-else>我会在新的工作版本中完成修改，当前稳定版本仍然可以试玩。</p>
        </div>
      </template>

      <template v-else>
        <div class="v2-ready-message"><Check :size="17" /><span><strong>新版本已准备好</strong><small>修改已通过全部验证，Playable v1 已保留在版本历史中。</small></span></div>
        <p class="change-ai-copy">当前稳定版本已经更新为 Playable v2。</p>
      </template>
    </div>

    <div class="cowork-composer-wrap">
      <form class="cowork-composer" @submit.prevent="submitRequest">
        <label for="controlled-change-request">自己描述想修改的内容</label>
        <textarea
          id="controlled-change-request"
          v-model="request"
          rows="4"
          :disabled="!['showing_recommendations', 'playing_v1'].includes(phase)"
          placeholder="例如：关系成长反馈太慢了，希望每次任务的增量更明显。"
        ></textarea>
        <button type="submit" :disabled="!request.trim() || !['showing_recommendations', 'playing_v1'].includes(phase)"><Send :size="14" />分析这次修改 <Circle :size="11" /></button>
      </form>
    </div>
  </aside>
</template>
