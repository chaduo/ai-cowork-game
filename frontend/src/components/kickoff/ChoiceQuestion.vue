<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { ArrowRight, PenLine } from 'lucide-vue-next'
import ChoiceCard from './ChoiceCard.vue'
import type { Choice, Question } from './kickoffTypes'

defineProps<{ question: Question; disabled?: boolean }>()
const emit = defineEmits<{ select: [choice: Choice] }>()

const showCustom = ref(false)
const customAnswer = ref('')
const customInput = ref<HTMLTextAreaElement | null>(null)

async function openCustom() {
  showCustom.value = true
  await nextTick()
  customInput.value?.focus()
}

function sendCustom() {
  const answer = customAnswer.value.trim()
  if (!answer) return
  emit('select', { id: `custom-${Date.now()}`, title: answer, description: '' })
}
</script>

<template>
  <section class="choice-question" :aria-labelledby="`question-${question.id}`">
    <div v-if="question.prompt" class="question-intro">
      <span>关键设计问题</span>
      <h3 :id="`question-${question.id}`">{{ question.prompt }}</h3>
    </div>
    <div v-if="question.choices.length" class="choice-list">
      <ChoiceCard
        v-for="choice in question.choices"
        :key="choice.id"
        :choice="choice"
        :disabled="disabled"
        @select="$emit('select', $event)"
      />
    </div>

    <button v-if="!showCustom" class="custom-answer-toggle" type="button" @click="openCustom">
      <PenLine :size="14" />这些都不是，我有自己的想法
    </button>
    <form v-else class="custom-answer" @submit.prevent="sendCustom">
      <label :for="`custom-${question.id}`">告诉我你希望怎么设计</label>
      <div>
        <textarea
          :id="`custom-${question.id}`"
          ref="customInput"
          v-model="customAnswer"
          rows="2"
          :disabled="disabled"
          placeholder="用你自己的方式描述这个决定…"
        ></textarea>
        <button type="submit" :disabled="!customAnswer.trim() || disabled" aria-label="发送自定义回答">
          发送 <ArrowRight :size="14" />
        </button>
      </div>
    </form>
  </section>
</template>
