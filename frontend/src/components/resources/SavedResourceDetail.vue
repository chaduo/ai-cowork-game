<script setup lang="ts">
import { ArrowLeft, FilePenLine } from 'lucide-vue-next'
import { ref, watch } from 'vue'
import ResourceDetailContent from './ResourceDetailContent.vue'
import ResourceMetadataEditor from './ResourceMetadataEditor.vue'
import type { ResourceCandidate } from './resourceTypes'

const props = defineProps<{ resource: ResourceCandidate }>()
const emit = defineEmits<{ back: []; updateMetadata: [payload: { id: string; name: string; summary: string }] }>()
const editorOpen = ref(false)

watch(() => props.resource.id, () => { editorOpen.value = false })

function saveMetadata(payload: { name: string; summary: string }) {
  emit('updateMetadata', { id: props.resource.id, ...payload })
  editorOpen.value = false
}
</script>

<template>
  <section class="saved-resource-detail-page">
    <button class="saved-detail-back" type="button" @click="$emit('back')"><ArrowLeft :size="15" />返回我的资源</button>
    <div class="saved-detail-shell">
      <ResourceDetailContent :resource="resource" mode="saved" />
      <footer class="saved-detail-actions"><button type="button" @click="editorOpen = true"><FilePenLine :size="14" />编辑信息</button></footer>
    </div>
    <ResourceMetadataEditor :open="editorOpen" :name="resource.name" :summary="resource.summary" @close="editorOpen = false" @save="saveMetadata" />
  </section>
</template>
