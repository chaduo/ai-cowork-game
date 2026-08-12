<script setup lang="ts">
import { ArrowRight, Boxes, Clock3 } from 'lucide-vue-next'
withDefaults(defineProps<{ acknowledged?: boolean; pendingCount?: number }>(), { acknowledged: false, pendingCount: 3 })
defineEmits<{ later: []; review: [] }>()
</script>

<template>
  <section class="resource-extraction-bridge">
    <div class="resource-bridge-icon"><Boxes :size="20" /></div>
    <div><span>可复用资源</span><h3>{{ pendingCount ? `发现 ${pendingCount} 项待确认内容` : '资源确认已完成' }}</h3><p>{{ pendingCount ? 'AI 已整理可能值得复用的内容，由你决定哪些值得留下。' : '所有内容都已经过人工决定，原 Release 仍保持冻结。' }}</p></div>
    <div v-if="pendingCount" class="resource-bridge-actions"><button v-if="!acknowledged" type="button" @click="$emit('later')"><Clock3 :size="13" />稍后处理</button><button type="button" class="primary" @click="$emit('review')">{{ acknowledged ? `继续确认 · ${pendingCount}` : '确认资源' }} <ArrowRight :size="14" /></button></div>
  </section>
</template>
