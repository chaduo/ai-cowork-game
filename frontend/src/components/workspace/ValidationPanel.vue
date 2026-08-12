<script setup lang="ts">
import { Check, LoaderCircle, RotateCw, X } from 'lucide-vue-next'
import { computed } from 'vue'
import { validationChecks } from './buildFixture'
import type { BuildPhase } from './buildTypes'

const props = defineProps<{ phase: BuildPhase }>()

const complete = computed(() => props.phase === 'validating_complete' || props.phase === 'playable_ready')
const passedCount = computed(() => complete.value ? 9 : 7)
</script>

<template>
  <section class="validation-panel">
    <header>
      <div><span>DEFINITION OF PLAYABLE</span><h2>Validation</h2></div>
      <strong :class="{ complete }">{{ passedCount }} / 9 <small>passed</small></strong>
    </header>

    <div v-if="phase === 'auto_fixing'" class="auto-fix-band">
      <RotateCw :size="15" class="spin" />
      <span><strong>正在修复代际触发流程</strong>关系条件达成后，传承事件没有进入最终完成状态。</span>
    </div>

    <ul>
      <li v-for="(check, index) in validationChecks" :key="check.id" :class="{ failed: !complete && index >= 7 }">
        <Check v-if="complete || index < 7" :size="14" />
        <LoaderCircle v-else-if="phase === 'auto_fixing' && index === 7" :size="14" class="spin" />
        <X v-else :size="14" />
        <span><strong>{{ check.label }}</strong><small>GameSpec · {{ check.source }}</small></span>
      </li>
    </ul>
  </section>
</template>
