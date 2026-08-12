<script setup lang="ts">
import { Check, LoaderCircle, RotateCw, X } from 'lucide-vue-next'
import { computed } from 'vue'
import type { ChangePhase, ChangePlan } from './changeTypes'

const props = defineProps<{ phase: ChangePhase; plan: ChangePlan }>()
const complete = computed(() => ['validation_complete_change', 'playable_v2_ready', 'version_history'].includes(props.phase))
</script>

<template>
  <section class="change-validation-panel">
    <header>
      <div><span>修改验证</span><h2>新行为与回归检查</h2><p>先证明修改正确，再确认原来的核心循环没有被破坏。</p></div>
      <strong :class="{ complete }">{{ complete ? '6 / 6' : '5 / 6' }}<small>passed</small></strong>
    </header>

    <div v-if="phase === 'auto_fixing_change'" class="change-auto-fix">
      <RotateCw :size="15" class="spin" /><span><strong>正在修复好感条同步</strong><small>关系事件已正确触发，正在连接 Favor 状态与心形 UI。</small></span>
    </div>

    <div class="validation-groups">
      <section>
        <header><span>本次修改</span><strong>{{ complete ? '2 / 2' : '1 / 2' }}</strong></header>
        <ul>
          <li v-for="(check, index) in plan.changedChecks" :key="check.id" :class="{ failed: !complete && index === 1 }">
            <Check v-if="complete || index === 0" :size="14" />
            <LoaderCircle v-else-if="phase === 'auto_fixing_change'" :size="14" class="spin" />
            <X v-else :size="14" />
            <span><strong>{{ check.label }}</strong><small>{{ index === 1 && !complete ? 'Favor 更新后 UI 未刷新' : '验证通过' }}</small></span>
          </li>
        </ul>
      </section>

      <section>
        <header><span>回归检查</span><strong>4 / 4</strong></header>
        <ul><li v-for="check in plan.regressionChecks" :key="check.id"><Check :size="14" /><span><strong>{{ check.label }}</strong><small>保持正常</small></span></li></ul>
      </section>
    </div>
  </section>
</template>
