<script setup lang="ts">
import { ArrowRight, FilePenLine, LoaderCircle, Minus, RotateCcw, Save } from 'lucide-vue-next'
import { ref, watch } from 'vue'
import ResourceDetailContent from './ResourceDetailContent.vue'
import ResourceMetadataEditor from './ResourceMetadataEditor.vue'
import type { ResourceCandidate } from './resourceTypes'

const props = defineProps<{ candidate: ResourceCandidate; hasNextPending: boolean }>()
const emit = defineEmits<{ save: []; ignore: []; undo: []; next: []; updateMetadata: [payload: { name: string; summary: string }] }>()
const editorOpen = ref(false)

watch(() => props.candidate.id, () => { editorOpen.value = false })

function updateMetadata(payload: { name: string; summary: string }) {
  emit('updateMetadata', payload)
  editorOpen.value = false
}
</script>

<template>
  <section class="resource-review-center">
    <div class="resource-detail-scroll"><ResourceDetailContent :resource="candidate" mode="review" /></div>
    <ResourceMetadataEditor :open="editorOpen" :name="candidate.name" :summary="candidate.summary" @close="editorOpen = false" @save="updateMetadata" />

    <footer class="resource-human-gate">
      <div><strong>{{ candidate.status === 'saved' ? '已保存为资源' : candidate.status === 'ignored' ? '已忽略这项内容' : candidate.status === 'saving' ? '正在保存…' : '选择是否保留这项内容' }}</strong><span v-if="candidate.status === 'saved' || candidate.status === 'ignored'">你仍然可以撤销，也可以主动查看下一项。</span></div>
      <template v-if="candidate.status === 'pending' || candidate.status === 'saving'">
        <button type="button" class="danger" :disabled="candidate.status === 'saving'" @click="$emit('ignore')"><Minus :size="14" />忽略</button>
        <button type="button" :disabled="candidate.status === 'saving'" @click="editorOpen = true"><FilePenLine :size="14" />编辑信息</button>
        <button type="button" class="primary" :disabled="candidate.status === 'saving'" @click="$emit('save')"><LoaderCircle v-if="candidate.status === 'saving'" :size="14" class="spin" /><Save v-else :size="14" />{{ candidate.status === 'saving' ? '正在保存…' : '保存为资源' }}</button>
      </template>
      <template v-else>
        <button type="button" @click="$emit('undo')"><RotateCcw :size="14" />撤销</button>
        <button v-if="hasNextPending" type="button" class="next" @click="$emit('next')">查看下一项<ArrowRight :size="14" /></button>
      </template>
    </footer>
  </section>
</template>
