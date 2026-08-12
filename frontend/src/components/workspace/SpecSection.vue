<script setup lang="ts">
import { Check, ChevronDown, PencilLine, Sparkles, Triangle } from 'lucide-vue-next'
import type { SourceKind, SpecContext } from './workspaceTypes'

defineProps<{
  title: string
  kicker?: string
  context: SpecContext
  source?: SourceKind
  updated?: boolean
  technicalLabel?: string
}>()

defineEmits<{ adjust: [context: SpecContext] }>()
</script>

<template>
  <section class="spec-section" :id="`spec-${context.key}`">
    <header class="spec-section-header">
      <div>
        <span v-if="kicker" class="spec-kicker">{{ kicker }}</span>
        <h2>{{ title }}</h2>
      </div>
      <div class="spec-section-tools">
        <span v-if="updated" class="spec-updated"><Check :size="12" />Draft updated</span>
        <button type="button" @click="$emit('adjust', context)"><PencilLine :size="13" />调整</button>
      </div>
    </header>

    <slot />

    <div v-if="source" class="spec-source" :class="`is-${source}`">
      <Check v-if="source === 'confirmed'" :size="12" />
      <Sparkles v-else-if="source === 'default'" :size="12" />
      <Triangle v-else :size="11" />
      {{ source === 'confirmed' ? '来自已确认设计' : source === 'default' ? 'AI 实现默认' : '已为 First Playable 简化' }}
    </div>

    <details v-if="$slots.technical" class="technical-disclosure">
      <summary><span>{{ technicalLabel ?? '查看技术细节' }}</span><ChevronDown :size="14" /></summary>
      <div class="technical-content"><slot name="technical" /></div>
    </details>
  </section>
</template>
