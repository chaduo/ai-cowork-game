<script setup lang="ts">
import { ArrowRight, BadgeCheck, Check, Clock3, Gamepad2, Heart, History, LoaderCircle, MessageSquareText, PackageCheck, Send, Sprout } from 'lucide-vue-next'
import { computed } from 'vue'
import ResourceExtractionBridge from './ResourceExtractionBridge.vue'
import { isWorkingPreviewAvailable } from './buildFixture'
import type { BuildPhase } from './buildTypes'
import type { ChangePhase } from './changeTypes'
import type { ReleaseRecord } from './releaseTypes'

const props = withDefaults(defineProps<{
  phase: BuildPhase | ChangePhase
  playableVersion?: number
  release?: ReleaseRecord | null
  resourceBridgeAcknowledged?: boolean
  resourcePendingCount?: number
}>(), { playableVersion: 2, release: null, resourceBridgeAcknowledged: false, resourcePendingCount: 3 })
defineEmits<{ openHistory: []; publish: []; viewRelease: []; continueDevelopment: []; resourceLater: []; resourceReview: [] }>()

const changePhases: ChangePhase[] = [
  'showing_recommendations', 'playing_v1', 'change_requested', 'analyzing_change', 'change_review',
  'preparing_working_build', 'reusing_unaffected_content', 'applying_gameplay_change', 'applying_visual_change',
  'checking_scope', 'scope_violation', 'building_working_version', 'validating_change', 'auto_fixing_change',
  'validation_complete_change', 'playable_v2_ready', 'version_history',
]
const isChangeFlow = computed(() => changePhases.includes(props.phase as ChangePhase))
const v2Ready = computed(() => props.phase === 'playable_v2_ready' || props.phase === 'version_history')
const ready = computed(() => props.phase === 'playable_ready' || isChangeFlow.value)
const workingChange = computed(() => isChangeFlow.value && !['showing_recommendations', 'playing_v1', 'change_requested', 'analyzing_change', 'change_review', 'playable_v2_ready', 'version_history'].includes(props.phase))
const available = computed(() => isChangeFlow.value || isWorkingPreviewAvailable(props.phase as BuildPhase))
</script>

<template>
  <section v-if="!available" class="build-preview-empty">
    <span><LoaderCircle :size="22" class="spin" /></span>
    <small>PREVIEW</small>
    <h2>Preparing runnable build…</h2>
    <p>Core Gameplay 完成后，这里会出现第一个 Working Build。</p>
  </section>

  <article v-else class="build-preview-view">
    <header>
      <div>
        <span :class="ready ? 'is-playable' : 'is-working'">{{ v2Ready ? '新版本已准备好' : isChangeFlow ? '当前稳定版本' : ready ? 'PLAYABLE READY' : 'WORKING BUILD' }}</span>
        <h1>{{ v2Ready ? `Playable v${playableVersion} · Stable` : ready ? 'Playable v1 · Stable' : '多代田园物语 · Build in progress' }}</h1>
        <p>{{ v2Ready ? 'NPC 关系反馈增强已经通过全部修改与回归验证。' : workingChange ? '工作版本正在修改，当前 v1 仍然可以继续试玩。' : ready ? '第一版已经通过全部可玩性验证。' : '核心玩法已经可以运行，其余系统仍在制作。' }}</p>
      </div>
      <div class="preview-build-meta" :class="{ 'has-release-actions': ready }">
        <strong><BadgeCheck v-if="ready" :size="14" /><Clock3 v-else :size="14" />{{ v2Ready ? '6 / 6 PASS' : ready ? (workingChange ? 'v1 SAFE' : '9 / 9 PASS') : 'NOT YET VERIFIED' }}</strong>
        <small>{{ v2Ready ? 'stable / v2' : ready ? 'stable / v1' : 'working / draft' }}</small>
        <div v-if="ready" class="preview-release-actions">
          <button v-if="v2Ready" type="button" class="open-version-history" @click="$emit('openHistory')"><History :size="13" />版本</button>
          <button v-if="release" type="button" class="open-release-detail" @click="$emit('viewRelease')"><PackageCheck :size="13" />查看 Release</button>
          <button type="button" class="publish-release-button" @click="$emit('publish')"><Send :size="13" />{{ workingChange ? `发布 Playable v${playableVersion}` : release ? '发布新 Release' : '发布版本' }}</button>
        </div>
      </div>
    </header>

    <div v-if="ready" class="release-imprint-bar">
      <div><span>当前开发版本</span><strong><BadgeCheck :size="14" />Playable v{{ playableVersion }} · 稳定</strong></div>
      <div class="release-imprint-divider"></div>
      <div v-if="release"><span>当前正式版本</span><strong><PackageCheck :size="14" />Release v{{ release.version }} · 已发布</strong><small>基于 Playable v{{ release.basedOnPlayable }}</small></div>
      <div v-else><span>当前正式版本</span><strong class="is-empty">尚未发布</strong><small>由你决定何时冻结作品</small></div>
      <button v-if="release" type="button" @click="$emit('continueDevelopment')">继续开发 <ArrowRight :size="13" /></button>
    </div>

    <div class="farm-preview-frame">
      <img src="/farm-game-preview.png" alt="多代田园物语俯视角农场 Mock 游戏画面" />
      <div class="farm-preview-hud hud-money"><span>G</span><strong>1,240</strong></div>
      <div class="farm-preview-hud hud-favor"><MessageSquareText :size="13" /><strong>Lucy · 68</strong></div>
      <div v-if="v2Ready" class="favor-heart-bar"><Heart :size="14" fill="currentColor" /><span><i></i></span><strong>68 / 100</strong></div>
      <div v-if="workingChange" class="stable-preview-note"><Clock3 :size="13" /><span><strong>工作版本正在修改</strong>这里继续显示稳定的 Playable v1</span></div>
      <div v-if="!ready" class="working-watermark">WORKING BUILD · MOCK PREVIEW</div>
      <div v-else class="playable-seal"><BadgeCheck :size="15" />PLAYABLE {{ v2Ready ? 'v2' : 'v1' }}</div>
    </div>

    <div class="preview-capabilities">
      <div><span>已可体验</span><p><Check :size="13" />移动</p><p><Check :size="13" />种植与收获</p><p><Check :size="13" />Lucy 委托</p></div>
      <div v-if="!ready"><span>仍在制作</span><p><LoaderCircle :size="13" class="spin" />关系结局</p><p><Sprout :size="13" />代际传承</p></div>
      <div v-else><span>验证结果</span><p><BadgeCheck :size="13" />{{ v2Ready ? '关系反馈增强' : '核心经营闭环' }}</p><p><BadgeCheck :size="13" />{{ v2Ready ? '回归检查通过' : '关系与代际目标' }}</p></div>
      <div class="preview-runtime-note"><Gamepad2 :size="15" /><span><strong>Static prototype preview</strong>本画面不运行真实 Phaser 游戏</span></div>
    </div>
    <ResourceExtractionBridge v-if="release" :acknowledged="resourceBridgeAcknowledged" :pending-count="resourcePendingCount" @later="$emit('resourceLater')" @review="$emit('resourceReview')" />
  </article>
</template>
