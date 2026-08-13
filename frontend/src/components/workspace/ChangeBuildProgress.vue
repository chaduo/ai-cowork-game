<script setup lang="ts">
import { Check, Circle, LoaderCircle, RotateCcw, ShieldAlert, ShieldCheck, X } from 'lucide-vue-next'
import { computed } from 'vue'
import { getChangeStepStatus } from './changeFixture'
import type { ChangePhase, ChangePlan } from './changeTypes'

const props = defineProps<{ phase: ChangePhase; plan: ChangePlan }>()
defineEmits<{ retryScope: [] }>()

const activeIndex = computed(() => {
  const index = props.plan.progress.findIndex((_, itemIndex) => ['active', 'failed'].includes(getChangeStepStatus(itemIndex, props.phase)))
  return index >= 0 ? index : props.plan.progress.length - 1
})
const activeStep = computed(() => props.plan.progress[activeIndex.value]!)
</script>

<template>
  <div class="change-build-grid">
    <ol class="change-progress-ledger" aria-label="本次修改进度">
      <li v-for="(step, index) in plan.progress" :key="step.id" :class="`is-${getChangeStepStatus(index, phase)}`">
        <span>
          <Check v-if="getChangeStepStatus(index, phase) === 'completed'" :size="13" />
          <LoaderCircle v-else-if="getChangeStepStatus(index, phase) === 'active'" :size="13" class="spin" />
          <X v-else-if="getChangeStepStatus(index, phase) === 'failed'" :size="13" />
          <Circle v-else :size="9" />
        </span>
        <div><strong>{{ step.label }}</strong><small>{{ getChangeStepStatus(index, phase) === 'completed' ? '完成' : getChangeStepStatus(index, phase) === 'active' ? '正在处理' : getChangeStepStatus(index, phase) === 'failed' ? '已停止' : '等待' }}</small></div>
      </li>
    </ol>

    <section class="change-progress-detail" :class="{ 'is-violation': phase === 'scope_violation' }">
      <template v-if="phase === 'scope_violation'">
        <ShieldAlert :size="22" />
        <span>修改范围检查</span>
        <h2>检测到超出预期范围的修改</h2>
        <p>这次工作版本影响到了与需求无关的内容。修改已停止，Playable v1 不受影响。</p>
        <div><strong>发现的问题</strong><small>农场经济配置出现了未声明的变化</small></div>
        <button type="button" @click="$emit('retryScope')"><RotateCcw :size="14" />重新生成修改</button>
      </template>

      <template v-else>
        <span>当前步骤</span>
        <h2>{{ activeStep.label }}</h2>
        <p>{{ activeStep.detail }}</p>

        <div v-if="activeStep.id === 'reuse'" class="reused-progress-detail">
          <strong>继续使用</strong><span v-for="item in plan.reused" :key="item"><Check :size="12" />{{ item }}</span>
        </div>
        <div v-else-if="activeStep.id === 'gameplay'" class="rule-change-evidence"><strong>关系事件触发条件</strong><span>Favor ≥ 30</span><b>→ Relationship Event</b></div>
        <div v-else-if="activeStep.id === 'visual'" class="visual-change-evidence"><strong>关系反馈 UI</strong><span><Check :size="12" />Favor 变化时同步更新</span><span><RotateCcw :size="12" />现有角色素材继续复用</span></div>
        <div v-else-if="activeStep.id === 'scope'" class="scope-check-evidence"><ShieldCheck :size="16" /><span><strong>正在确认修改只发生在预期范围</strong><small>{{ plan.scopeExpected.join(' · ') }}</small></span></div>
        <div v-else-if="activeStep.id === 'build'" class="scope-check-evidence"><LoaderCircle :size="16" class="spin" /><span><strong>重新构建完整运行版本</strong><small>未受影响内容不会重新生成。</small></span></div>
        <div v-else class="scope-check-evidence"><ShieldCheck :size="16" /><span><strong>Playable v1 始终安全</strong><small>所有修改只发生在隔离的工作版本。</small></span></div>
      </template>
    </section>
  </div>
</template>
