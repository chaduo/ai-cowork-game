<script setup lang="ts">
import { RotateCcw, TriangleAlert } from 'lucide-vue-next'
import KickoffMessage from './KickoffMessage.vue'

defineEmits<{ retry: [] }>()
</script>

<template>
  <KickoffMessage role="ai">
    <div class="retry-state" role="alert">
      <TriangleAlert :size="17" />
      <div><strong>这一步没有完成。</strong><span>刚才的决定已经保留，可以只重试当前响应。</span></div>
      <button type="button" @click="$emit('retry')"><RotateCcw :size="14" />重新尝试</button>
    </div>
  </KickoffMessage>
</template>
