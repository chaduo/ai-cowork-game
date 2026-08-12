<script setup lang="ts">
import { Check, LoaderCircle, ShieldCheck } from 'lucide-vue-next'
import ChangeAnalysisPanel from './ChangeAnalysisPanel.vue'
import ChangeBuildProgress from './ChangeBuildProgress.vue'
import ChangeSafetyStrip from './ChangeSafetyStrip.vue'
import ChangeValidationPanel from './ChangeValidationPanel.vue'
import type { ChangePhase, ChangePlan } from './changeTypes'

defineProps<{ phase: ChangePhase; plan: ChangePlan | null }>()
defineEmits<{ apply: []; cancel: []; retryScope: [] }>()
</script>

<template>
  <article class="controlled-change-workspace">
    <ChangeSafetyStrip :phase="phase" />

    <section v-if="phase === 'change_requested' || phase === 'analyzing_change'" class="change-analysis-loading">
      <span><LoaderCircle :size="22" class="spin" /></span><small>修改分析</small><h1>正在理解这次修改…</h1><p>分析玩法、视觉、影响范围以及可以直接复用的内容。</p>
    </section>

    <ChangeAnalysisPanel v-else-if="phase === 'change_review' && plan" :plan="plan" @apply="$emit('apply')" @cancel="$emit('cancel')" />

    <template v-else-if="plan && ['validating_change', 'auto_fixing_change', 'validation_complete_change'].includes(phase)">
      <div class="change-artifact-title"><div><span>工作版本</span><h1>验证 NPC 关系反馈</h1><p>Playable v1 继续保持稳定，工作版本正在接受修改与回归检查。</p></div><strong><LoaderCircle v-if="phase !== 'validation_complete_change'" :size="13" class="spin" /><Check v-else :size="13" />{{ phase === 'validation_complete_change' ? '全部通过' : '正在验证' }}</strong></div>
      <ChangeValidationPanel :phase="phase" :plan="plan" />
    </template>

    <template v-else-if="plan && !['playable_v2_ready', 'version_history'].includes(phase)">
      <div class="change-artifact-title"><div><span>正在应用修改</span><h1>{{ plan.summary }}</h1><p>只更新受影响内容，未受影响的游戏内容直接复用。</p></div><strong><LoaderCircle :size="13" class="spin" />工作版本</strong></div>
      <ChangeBuildProgress :phase="phase" :plan="plan" @retry-scope="$emit('retryScope')" />
    </template>

    <section v-else class="change-complete-state">
      <span><ShieldCheck :size="24" /></span><small>新版本已准备好</small><h1>Playable v2 · 稳定</h1><p>本次修改与回归检查共 6 项全部通过，Playable v1 已保留在版本历史中。</p>
    </section>
  </article>
</template>
