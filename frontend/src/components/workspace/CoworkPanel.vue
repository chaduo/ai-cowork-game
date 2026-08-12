<script setup lang="ts">
import { ArrowRight, Bot, Check, CornerDownRight, LoaderCircle, RotateCcw, Send, X } from 'lucide-vue-next'
import { computed, nextTick, ref, watch } from 'vue'
import type { CoworkMessage, SpecContext, WorkspacePhase } from './workspaceTypes'

const props = defineProps<{
  phase: WorkspacePhase
  messages: CoworkMessage[]
  context: SpecContext | null
}>()

const emit = defineEmits<{
  submit: [text: string]
  apply: []
  retry: []
  clearContext: []
}>()

const request = ref('')
const composerRef = ref<HTMLTextAreaElement | null>(null)
const canSubmit = computed(() => request.value.trim().length > 0 && props.phase === 'review' && props.context !== null)

watch(
  () => props.context,
  async (context) => {
    if (!context) return
    await nextTick()
    composerRef.value?.focus()
  },
)

function submit() {
  const text = request.value.trim()
  if (!text || !canSubmit.value) return
  emit('submit', text)
  request.value = ''
}
</script>

<template>
  <aside class="cowork-panel" aria-label="Cowork AI">
    <header class="cowork-panel-header">
      <div class="cowork-mark"><Bot :size="17" /></div>
      <div><span>COWORK AI</span><strong>GameSpec 协作</strong></div>
      <span class="cowork-stage">{{ phase === 'generating' ? 'GENERATING' : phase === 'revising' ? 'REVISING' : 'ACTIVE' }}</span>
    </header>

    <div class="cowork-stage-context">
      <span>当前阶段</span>
      <strong>GameSpec · {{ phase === 'generating' ? '正在生成' : phase === 'generation_error' ? '生成失败' : 'Draft v1' }}</strong>
      <p>把确认过的设计收敛成第一版可开发范围。</p>
    </div>

    <div class="cowork-messages" aria-live="polite">
      <article v-for="message in messages" :key="message.id" class="cowork-message" :class="`is-${message.role}`">
        <span>{{ message.role === 'user' ? 'YOU' : message.role === 'system' ? 'SYS' : 'AI' }}</span>
        <div>
          <p>{{ message.text }}</p>
          <button v-if="message.action === 'apply-revision'" type="button" @click="$emit('apply')"><Check :size="13" />应用修改</button>
        </div>
      </article>

      <div v-if="phase === 'revising'" class="cowork-thinking"><LoaderCircle :size="14" class="spin" />正在整理这部分规格…</div>

      <div v-if="phase === 'generation_error'" class="cowork-error">
        <strong>GameSpec 没有生成完成。</strong>
        <p>已确认的 Game Design 不会丢失。</p>
        <button type="button" @click="$emit('retry')"><RotateCcw :size="13" />重新生成</button>
      </div>
    </div>

    <div class="cowork-composer-wrap">
      <div v-if="context" class="composer-context">
        <span>CONTEXT</span>
        <div><template v-for="(item, index) in context.path" :key="item"><b>{{ item }}</b><CornerDownRight v-if="index < context.path.length - 1" :size="11" /></template></div>
        <button type="button" aria-label="清除讨论上下文" @click="$emit('clearContext')"><X :size="13" /></button>
      </div>
      <form class="cowork-composer" @submit.prevent="submit">
        <label for="cowork-request">{{ context ? `调整 ${context.label}` : 'Ask Cowork AI' }}</label>
        <textarea
          id="cowork-request"
          ref="composerRef"
          v-model="request"
          rows="4"
          :disabled="phase !== 'review'"
          :placeholder="context ? '描述你希望这部分如何调整…' : '先在右侧选择一个要调整的 Section…'"
        ></textarea>
        <button type="submit" :disabled="!canSubmit"><Send :size="14" />发送 <ArrowRight :size="13" /></button>
      </form>
    </div>
  </aside>
</template>
