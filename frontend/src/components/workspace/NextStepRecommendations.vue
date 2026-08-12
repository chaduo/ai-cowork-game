<script setup lang="ts">
import { ArrowRight, Heart, Palette, Wheat } from 'lucide-vue-next'
import { nextStepDirections } from './changeFixture'

defineEmits<{ select: [directionId: string] }>()

const icons = { heart: Heart, wheat: Wheat, palette: Palette }
</script>

<template>
  <section class="next-step-recommendations" aria-labelledby="next-step-title">
    <div class="next-step-heading"><span>推荐的下一步</span><h3 id="next-step-title">继续完善一个方向</h3></div>
    <button
      v-for="direction in nextStepDirections"
      :key="direction.id"
      type="button"
      class="next-step-card"
      @click="$emit('select', direction.id)"
    >
      <span class="next-step-icon"><component :is="icons[direction.icon as keyof typeof icons]" :size="16" /></span>
      <span class="next-step-copy">
        <span><strong>{{ direction.title }}</strong><em v-if="direction.recommended">AI 推荐</em></span>
        <small>{{ direction.description }}</small>
        <span class="next-step-points">{{ direction.points.join(' · ') }}</span>
      </span>
      <ArrowRight :size="14" />
    </button>
  </section>
</template>
