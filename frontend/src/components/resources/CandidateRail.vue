<script setup lang="ts">
import { ArrowLeft, Heart, Image, LayoutPanelTop } from 'lucide-vue-next'
import type { ResourceCandidate } from './resourceTypes'

defineProps<{ candidates: ResourceCandidate[]; selectedId: string; processed: number }>()
defineEmits<{ select: [id: string]; back: [] }>()

const typeLabels = { gameplay: '玩法模块', ui: 'UI 模块', visual: '美术资源' }
</script>

<template>
  <aside class="candidate-rail">
    <button class="candidate-back" type="button" @click="$emit('back')"><ArrowLeft :size="15" />返回工作区</button>
    <header><h2>可复用资源</h2><p>AI 从这次发布中整理了 {{ candidates.length }} 项可能值得以后继续使用的内容。你只需要判断哪些值得留下。</p></header>
    <nav aria-label="资源候选">
      <button v-for="candidate in candidates" :key="candidate.id" type="button" :class="{ active: selectedId === candidate.id }" @click="$emit('select', candidate.id)">
        <span class="candidate-type-icon"><Heart v-if="candidate.type === 'gameplay'" :size="17" /><LayoutPanelTop v-else-if="candidate.type === 'ui'" :size="17" /><Image v-else :size="17" /></span>
        <span class="candidate-rail-copy"><strong>{{ candidate.name }}</strong><span class="candidate-rail-tags"><span class="candidate-tag">{{ typeLabels[candidate.type] }}</span><span v-if="candidate.status === 'pending'" class="candidate-tag is-warn">待确认</span><span v-else class="candidate-tag" :class="candidate.status === 'saved' ? 'is-good' : 'is-muted'">{{ candidate.status === 'saved' ? '已保存' : candidate.status === 'ignored' ? '已忽略' : '正在保存' }}</span></span></span>
      </button>
    </nav>
    <footer>
      <div><span>处理进度</span><strong>{{ processed }} / {{ candidates.length }} 已处理</strong></div>
      <div class="candidate-progress"><i :style="{ width: `${processed / candidates.length * 100}%` }"></i></div>
    </footer>
  </aside>
</template>
