<script setup lang="ts">
import { Check, Circle, LoaderCircle, X } from 'lucide-vue-next'
import { buildMilestones, getMilestoneStatus } from './buildFixture'
import type { BuildPhase } from './buildTypes'

defineProps<{ phase: BuildPhase }>()
</script>

<template>
  <ol class="build-ledger" aria-label="First Playable 构建里程碑">
    <li
      v-for="milestone in buildMilestones"
      :key="milestone.id"
      :class="`is-${getMilestoneStatus(milestone.id, phase)}`"
    >
      <span class="ledger-marker">
        <Check v-if="getMilestoneStatus(milestone.id, phase) === 'completed'" :size="13" />
        <LoaderCircle v-else-if="getMilestoneStatus(milestone.id, phase) === 'active'" :size="13" class="spin" />
        <X v-else-if="getMilestoneStatus(milestone.id, phase) === 'failed'" :size="13" />
        <Circle v-else :size="9" />
      </span>
      <span class="ledger-copy">
        <small>{{ milestone.number }}</small>
        <strong>{{ milestone.title }}</strong>
        <em v-if="getMilestoneStatus(milestone.id, phase) === 'active'">正在制作</em>
        <em v-else-if="getMilestoneStatus(milestone.id, phase) === 'failed'">需要重试</em>
        <em v-else-if="getMilestoneStatus(milestone.id, phase) === 'completed'">完成</em>
      </span>
    </li>
  </ol>
</template>
