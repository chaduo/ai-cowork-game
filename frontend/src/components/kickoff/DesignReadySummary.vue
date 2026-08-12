<script setup lang="ts">
import { ArrowRight, Check, Sparkles } from 'lucide-vue-next'
import type { ReadySummary } from './kickoffTypes'

defineProps<{ summary: ReadySummary }>()
</script>

<template>
  <section class="design-ready-summary" aria-labelledby="ready-title">
    <div class="ready-stamp"><Check :size="15" />GAME DESIGN READY</div>
    <div class="ready-heading">
      <span>游戏设计摘要</span>
      <h3 id="ready-title">{{ summary.title }}</h3>
    </div>
    <p class="ready-summary-copy">{{ summary.summary }}</p>

    <div class="ready-details">
      <div>
        <span class="ready-label">HIGHLIGHTS</span>
        <ul>
          <li v-for="highlight in summary.highlights" :key="highlight"><Check :size="13" />{{ highlight }}</li>
        </ul>
      </div>
      <div class="core-loop-block">
        <span class="ready-label"><Sparkles :size="12" />CORE LOOP</span>
        <div class="core-loop">
          <template v-for="(step, index) in summary.coreLoop" :key="step">
            <span>{{ step }}</span><ArrowRight v-if="index < summary.coreLoop.length - 1" :size="12" />
          </template>
        </div>
      </div>
    </div>

    <div v-if="summary.progression?.length" class="ready-progression">
      <span class="ready-label">LONG-TERM PROGRESSION</span>
      <div class="core-loop">
        <template v-for="(step, index) in summary.progression" :key="step">
          <span>{{ step }}</span><ArrowRight v-if="index < summary.progression.length - 1" :size="12" />
        </template>
      </div>
    </div>
  </section>
</template>
