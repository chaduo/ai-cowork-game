<script setup lang="ts">
import { ArrowRight, WandSparkles } from 'lucide-vue-next'
import type { Choice } from './kickoffTypes'

defineProps<{ choice: Choice; disabled?: boolean }>()
defineEmits<{ select: [choice: Choice] }>()
</script>

<template>
  <button class="choice-card" type="button" :disabled="disabled" @click="$emit('select', choice)">
    <span v-if="choice.number" class="choice-number">{{ choice.number }}</span>
    <span class="choice-copy">
      <span class="choice-title-row">
        <strong>{{ choice.title }}</strong>
        <span v-if="choice.recommended" class="ai-recommended"><WandSparkles :size="12" />AI 推荐</span>
      </span>
      <span class="choice-description">{{ choice.description }}</span>
      <span v-if="choice.impact" class="choice-impact"><b>体验</b>{{ choice.impact }}</span>
    </span>
    <ArrowRight class="choice-arrow" :size="17" />
  </button>
</template>
