<script setup lang="ts">
defineProps<{
  role: 'ai' | 'user'
  label?: string
}>()
</script>

<template>
  <article class="kickoff-message" :class="`is-${role}`">
    <div class="message-rail" aria-hidden="true"><span>{{ role === 'ai' ? 'AI' : 'YOU' }}</span></div>
    <div class="message-content">
      <span class="message-label">{{ label ?? (role === 'ai' ? 'COWORK AI' : '你的决定') }}</span>
      <slot />
    </div>
  </article>
</template>
