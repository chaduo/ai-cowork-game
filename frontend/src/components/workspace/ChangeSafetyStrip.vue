<script setup lang="ts">
import { AlertTriangle, Check, Circle, LoaderCircle, ShieldCheck } from 'lucide-vue-next'
import { computed } from 'vue'
import type { ChangePhase } from './changeTypes'

const props = defineProps<{ phase: ChangePhase }>()
const v2Ready = computed(() => props.phase === 'playable_v2_ready' || props.phase === 'version_history')
const hasWorkingBuild = computed(() => !['showing_recommendations', 'playing_v1', 'change_requested', 'analyzing_change', 'change_review', 'playable_v2_ready', 'version_history'].includes(props.phase))
const scopeBlocked = computed(() => props.phase === 'scope_violation')
</script>

<template>
  <div class="change-safety-strip" aria-label="稳定版本和工作版本状态">
    <div class="safety-track is-playable">
      <span><ShieldCheck :size="14" />当前稳定版本</span>
      <strong>Playable {{ v2Ready ? 'v2' : 'v1' }} · 稳定</strong>
      <small>{{ v2Ready ? '6 / 6 验证通过' : '工作版本完成前始终可试玩' }}</small>
      <Check :size="14" />
    </div>
    <div class="safety-track is-working" :class="{ empty: !hasWorkingBuild, done: v2Ready }">
      <span><AlertTriangle v-if="scopeBlocked" :size="14" /><LoaderCircle v-else-if="hasWorkingBuild" :size="14" class="spin" /><Circle v-else :size="11" />工作版本</span>
      <strong>{{ v2Ready ? '已成为 Playable v2' : scopeBlocked ? '已停止' : hasWorkingBuild ? '正在加入 NPC 关系反馈' : '尚未开始' }}</strong>
      <small>{{ v2Ready ? '验证证据已记录' : scopeBlocked ? '已阻断越界修改' : hasWorkingBuild ? '修改范围受控' : '应用修改后创建' }}</small>
    </div>
  </div>
</template>
