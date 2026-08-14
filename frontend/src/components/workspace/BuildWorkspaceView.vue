<script setup lang="ts">
import { Ban, Check, Hammer, LoaderCircle } from 'lucide-vue-next'
import { computed } from 'vue'
import { buildMilestones, getMilestoneStatus } from './buildFixture'
import BuildMilestoneDetail from './BuildMilestoneDetail.vue'
import BuildMilestoneList from './BuildMilestoneList.vue'
import ValidationPanel from './ValidationPanel.vue'
import type { BuildPhase } from './buildTypes'

const props = defineProps<{ phase: BuildPhase }>()
const emit = defineEmits<{ retry: []; cancel: [] }>()

const isValidation = computed(() => ['validating', 'auto_fixing', 'validating_complete', 'playable_ready'].includes(props.phase))
const isCancellable = computed(() => [
  'build_starting', 'building_foundation', 'building_core', 'building_interaction',
  'building_presentation', 'building_progression', 'validating', 'auto_fixing', 'validating_complete',
].includes(props.phase))
const activeMilestone = computed(() => {
  const active = buildMilestones.find((milestone) => ['active', 'failed'].includes(getMilestoneStatus(milestone.id, props.phase)))
  return active ?? buildMilestones.at(-1)!
})
const activeStatus = computed(() => getMilestoneStatus(activeMilestone.value.id, props.phase))
</script>

<template>
  <article class="build-workspace-view">
    <header class="build-view-title">
      <div>
        <span><Hammer :size="13" /> FIRST PLAYABLE</span>
        <h1>Building your first playable version</h1>
        <p>根据已确认的 GameSpec，逐步完成游戏并验证每一项可玩标准。</p>
      </div>
      <div class="build-view-actions">
        <button v-if="isCancellable" type="button" class="cancel-build-button" @click="emit('cancel')"><Ban :size="13" />取消构建</button>
        <span class="working-build-status">
          <Check v-if="phase === 'playable_ready'" :size="13" />
          <LoaderCircle v-else :size="13" class="spin" />
          {{ phase === 'playable_ready' ? 'PLAYABLE READY' : 'WORKING BUILD' }}
        </span>
      </div>
    </header>

    <div class="build-view-grid">
      <BuildMilestoneList :phase="phase" />
      <ValidationPanel v-if="isValidation" :phase="phase" />
      <BuildMilestoneDetail v-else :milestone="activeMilestone" :status="activeStatus" :phase="phase" @retry="$emit('retry')" />
    </div>
  </article>
</template>
