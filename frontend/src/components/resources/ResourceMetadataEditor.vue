<script setup lang="ts">
import { Save, X } from 'lucide-vue-next'
import { reactive, watch } from 'vue'

const props = defineProps<{ open: boolean; name: string; summary: string }>()
const emit = defineEmits<{ close: []; save: [payload: { name: string; summary: string }] }>()
const edit = reactive({ name: props.name, summary: props.summary })

watch(() => [props.open, props.name, props.summary], () => {
  if (!props.open) return
  edit.name = props.name
  edit.summary = props.summary
})

function saveMetadata() {
  emit('save', {
    name: edit.name.trim() || props.name,
    summary: edit.summary.trim() || props.summary,
  })
}
</script>

<template>
  <div v-if="open" class="resource-editor-backdrop" @click.self="$emit('close')">
    <section class="resource-metadata-editor" role="dialog" aria-modal="true" aria-labelledby="resource-edit-title">
      <header><div><h2 id="resource-edit-title">编辑资源信息</h2><p>第一版只修改名称和说明。</p></div><button type="button" aria-label="关闭编辑" @click="$emit('close')"><X :size="16" /></button></header>
      <label><span>资源名称</span><input v-model="edit.name" /></label>
      <label><span>资源说明</span><textarea v-model="edit.summary" rows="4"></textarea></label>
      <footer><button type="button" @click="$emit('close')">取消</button><button type="button" class="primary" @click="saveMetadata"><Save :size="14" />保存调整</button></footer>
    </section>
  </div>
</template>
