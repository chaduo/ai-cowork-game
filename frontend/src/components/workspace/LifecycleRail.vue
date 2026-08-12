<script setup lang="ts">
import { Check, Circle, LoaderCircle } from 'lucide-vue-next'
import { computed } from 'vue'
import type { WorkspacePhase } from './workspaceTypes'

const props = defineProps<{ phase: WorkspacePhase }>()

const stages = computed(() => {
  const buildPhases: WorkspacePhase[] = [
    'build_starting', 'building_foundation', 'building_core', 'building_interaction',
    'building_presentation', 'building_progression', 'validating', 'auto_fixing',
    'validating_complete', 'build_error', 'playable_ready',
  ]
  const buildCurrent = buildPhases.includes(props.phase)
  const changePhases: WorkspacePhase[] = [
    'showing_recommendations', 'playing_v1', 'change_requested', 'analyzing_change', 'change_review',
    'preparing_working_build', 'reusing_unaffected_content', 'applying_gameplay_change', 'applying_visual_change',
    'checking_scope', 'scope_violation', 'building_working_version', 'validating_change', 'auto_fixing_change',
    'validation_complete_change', 'playable_v2_ready', 'version_history',
  ]
  const changeCurrent = changePhases.includes(props.phase)
  const changeWorking = [
    'preparing_working_build', 'reusing_unaffected_content', 'applying_gameplay_change', 'applying_visual_change',
    'checking_scope', 'scope_violation', 'building_working_version', 'validating_change', 'auto_fixing_change', 'validation_complete_change',
  ].includes(props.phase)
  const playableReady = props.phase === 'playable_ready' || props.phase === 'playable_v2_ready' || props.phase === 'version_history'
  const designComplete = buildCurrent || changeCurrent
  return [
    { id: 'design', label: 'DESIGN', note: 'Confirmed', state: 'done' },
    { id: 'gamespec', label: 'GAMESPEC', note: designComplete ? 'Confirmed' : 'Review', state: designComplete ? 'done' : 'current' },
    { id: 'build', label: 'BUILD', note: changeWorking ? 'Updating' : playableReady || changeCurrent ? 'Validated' : buildCurrent ? (props.phase === 'build_error' ? 'Attention' : 'In progress') : '', state: changeWorking ? 'current' : playableReady || changeCurrent ? 'verified' : buildCurrent ? 'current' : 'upcoming' },
    { id: 'playable', label: 'PLAYABLE', note: props.phase === 'playable_v2_ready' || props.phase === 'version_history' ? 'v2 · Stable' : playableReady || changeCurrent ? 'v1 · Stable' : '', state: changeWorking ? 'verified' : playableReady || changeCurrent ? 'current' : 'upcoming' },
  ]
})
</script>

<template>
  <nav class="lifecycle-rail" aria-label="游戏开发生命周期">
    <template v-for="(stage, index) in stages" :key="stage.id">
      <div class="lifecycle-stage" :class="`is-${stage.state}`">
        <span class="lifecycle-mark">
          <Check v-if="stage.state === 'done'" :size="13" />
          <LoaderCircle v-else-if="stage.state === 'current' && stage.id === 'build'" :size="13" class="spin" />
          <Circle v-else :size="11" />
        </span>
        <span><strong>{{ stage.label }}</strong><small v-if="stage.note">{{ stage.note }}</small></span>
      </div>
      <i v-if="index < stages.length - 1" class="lifecycle-link"></i>
    </template>
  </nav>
</template>
