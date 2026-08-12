<script setup lang="ts">
import { ArrowRight, Check, ChevronDown, CircleMinus, Link2, RotateCcw, ShieldCheck } from 'lucide-vue-next'
import type { ChangePlan } from './changeTypes'

defineProps<{ plan: ChangePlan }>()
defineEmits<{ apply: []; cancel: [] }>()

const typeLabels = { Documentation: '说明 / 文档', Parameter: '数值调整', Gameplay: '玩法规则', Visual: '视觉表现' }
</script>

<template>
  <article class="change-analysis-panel">
    <header class="change-analysis-header">
      <div><span>修改分析</span><h1>{{ plan.summary }}</h1><p>{{ plan.interpretation }}</p></div>
      <div class="change-type-tags"><span v-for="type in plan.changeTypes" :key="type">{{ typeLabels[type] }}</span></div>
    </header>

    <section class="change-understanding">
      <div class="analysis-section-title"><span>AI 的理解</span><h2>我理解你想做这些改变</h2></div>
      <div class="interpreted-changes">
        <article v-for="(change, index) in plan.changes" :key="change.id">
          <span>{{ String(index + 1).padStart(2, '0') }}</span>
          <div><strong>{{ change.title }}</strong><small>{{ change.userType }}</small><p v-if="change.current"><b>当前</b>{{ change.current }}</p><p><b>{{ change.current ? '修改后' : '新增' }}</b>{{ change.next }}</p></div>
        </article>
      </div>
    </section>

    <section class="impact-reuse-grid">
      <div class="impact-summary">
        <div class="analysis-section-title"><span>影响范围</span><h2>这次修改会影响</h2></div>
        <ul>
          <li v-for="item in plan.affected" :key="item.label"><Check :size="14" /><span><strong>{{ item.label }}</strong><small>{{ item.detail }}</small></span></li>
        </ul>
        <details><summary>查看修改范围 <ChevronDown :size="13" /></summary><p v-for="item in plan.affected" :key="item.technicalScope"><Link2 :size="11" />{{ item.technicalScope }}</p></details>
      </div>

      <div class="reuse-summary">
        <div class="analysis-section-title"><span>直接复用</span><h2>这些内容不会重新生成</h2></div>
        <ul><li v-for="item in plan.reused" :key="item"><Check :size="13" />{{ item }}</li></ul>
        <p><RotateCcw :size="13" />未受影响内容从 Playable v1 继续使用。</p>
      </div>
    </section>

    <section class="build-strategy-notice">
      <ShieldCheck :size="18" />
      <div><span>构建方式</span><strong>创建新的工作版本，完整构建并验证</strong><p>{{ plan.buildReason }}</p></div>
      <div class="strategy-artifacts"><span><CircleMinus :size="12" />游戏设计 · 无需修改</span><span><Check :size="12" />GameSpec / 逻辑 / UI · 更新</span><span><RotateCcw :size="12" />角色与场景素材 · 复用</span></div>
    </section>

    <footer class="change-analysis-gate">
      <div><ShieldCheck :size="14" /><span><strong>当前稳定版本不会被覆盖</strong><small>只有修改验证全部通过后，Playable 才会更新。</small></span></div>
      <button type="button" @click="$emit('cancel')">取消</button>
      <button class="apply-change" type="button" @click="$emit('apply')">应用修改 <ArrowRight :size="15" /></button>
    </footer>
  </article>
</template>
