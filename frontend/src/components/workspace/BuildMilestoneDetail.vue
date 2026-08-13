<script setup lang="ts">
import { Check, ChevronDown, FileCode2, Link2, LoaderCircle, RotateCcw, TriangleAlert } from 'lucide-vue-next'
import type { BuildMilestone, BuildPhase, MilestoneStatus } from './buildTypes'

defineProps<{
  milestone: BuildMilestone
  status: MilestoneStatus
  phase: BuildPhase
}>()

defineEmits<{ retry: [] }>()
</script>

<template>
  <section class="build-detail" :class="{ 'is-error': phase === 'build_error' }">
    <header class="build-detail-header">
      <div>
        <span>{{ milestone.number }} · CURRENT MILESTONE</span>
        <h2>{{ milestone.title }}</h2>
        <p>{{ milestone.summary }}</p>
      </div>
      <span class="milestone-state" :class="`is-${status}`">
        <Check v-if="status === 'completed'" :size="13" />
        <LoaderCircle v-else-if="status === 'active'" :size="13" class="spin" />
        <TriangleAlert v-else-if="status === 'failed'" :size="13" />
        {{ status === 'completed' ? 'COMPLETED' : status === 'failed' ? 'BLOCKED' : 'IN PROGRESS' }}
      </span>
    </header>

    <div v-if="phase === 'build_error'" class="build-error-callout">
      <TriangleAlert :size="18" />
      <div>
        <strong>角色素材没有生成完成</strong>
        <p>Foundation、Core Gameplay 和 NPC 逻辑已经保留。只需要重新尝试 Presentation。</p>
      </div>
      <button type="button" @click="$emit('retry')"><RotateCcw :size="14" />重新尝试此阶段</button>
    </div>

    <template v-else>
      <ul class="build-feature-list">
        <li v-for="(feature, index) in milestone.features" :key="feature">
          <Check v-if="status === 'completed' || index < Math.ceil(milestone.features.length / 2)" :size="14" />
          <LoaderCircle v-else-if="status === 'active' && index === Math.ceil(milestone.features.length / 2)" :size="14" class="spin" />
          <span v-else></span>
          {{ feature }}
        </li>
      </ul>

      <div class="build-trace-source"><Link2 :size="13" /><span>来自 GameSpec</span><strong>{{ milestone.gameSpecSource }}</strong></div>

      <details class="build-functional-detail">
        <summary>功能详情 <ChevronDown :size="13" /></summary>
        <p>{{ milestone.completedMessage }}</p>
        <details>
          <summary><FileCode2 :size="12" />查看执行详情</summary>
          <ul><li v-for="item in milestone.executionDetails" :key="item">{{ item }}</li></ul>
        </details>
      </details>
    </template>
  </section>
</template>
