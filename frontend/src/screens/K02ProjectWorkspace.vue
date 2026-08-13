<script setup lang="ts">
import { ArrowLeft, ArrowRight, Check, ChevronRight, FileCode2, Gamepad2, Hammer, Image, LoaderCircle, MonitorPlay, ScrollText, SlidersHorizontal } from 'lucide-vue-next'
import { computed, onBeforeUnmount, ref } from 'vue'
import AssetGalleryReadOnly from '../components/workspace/AssetGalleryReadOnly.vue'
import ArtifactEmptyState from '../components/workspace/ArtifactEmptyState.vue'
import BuildCoworkPanel from '../components/workspace/BuildCoworkPanel.vue'
import BuildPreview from '../components/workspace/BuildPreview.vue'
import BuildWorkspaceView from '../components/workspace/BuildWorkspaceView.vue'
import ControlledChangeCoworkPanel from '../components/workspace/ControlledChangeCoworkPanel.vue'
import ControlledChangeWorkspace from '../components/workspace/ControlledChangeWorkspace.vue'
import CodeReadOnlyState from '../components/workspace/CodeReadOnlyState.vue'
import CoworkPanel from '../components/workspace/CoworkPanel.vue'
import GameSpecDocument from '../components/workspace/GameSpecDocument.vue'
import ResourceReuseDrawer from '../components/workspace/ResourceReuseDrawer.vue'
import LifecycleRail from '../components/workspace/LifecycleRail.vue'
import VersionHistoryDrawer from '../components/workspace/VersionHistoryDrawer.vue'
import ReleaseDetailDrawer from '../components/workspace/ReleaseDetailDrawer.vue'
import ReleaseReviewModal from '../components/workspace/ReleaseReviewModal.vue'
import type { ConfirmedGameDesign } from '../components/kickoff/kickoffTypes'
import type { BuildPhase } from '../components/workspace/buildTypes'
import type { ChangePhase, ChangeSource } from '../components/workspace/changeTypes'
import type { ReleaseDraft, ReleasePhase, ReleaseRecord } from '../components/workspace/releaseTypes'
import type { ArtifactTab, SpecContext } from '../components/workspace/workspaceTypes'
import {
  applyControlledChange as applyProjectControlledChange,
  applySpecRevision,
  cancelChange as cancelProjectChange,
  confirmSpecAndStartBuild,
  getActiveProject,
  requestChange as requestProjectChange,
  requestSpecConfirmation,
  requestSpecRevision,
  retryBuild,
  retryScopeViolation as retryProjectScopeViolation,
  cancelRelationshipResource as cancelProjectRelationshipResource,
  dismissResourceRecommendation,
  prepareReleaseReview,
  publishRelease as publishProjectRelease,
  createReleaseDraftForProject,
  getCurrentRelease,
  getCurrentPlayable,
  restorePlayable,
  acknowledgeResourceBridge as acknowledgeProjectResourceBridge,
  setWorkspacePhase,
  startGeneration,
  refreshResourceMatches,
  projectStore,
  useRelationshipResource as useProjectRelationshipResource,
  updateReleaseDraft,
} from '../stores/projectStore'

const props = withDefaults(defineProps<{ design: ConfirmedGameDesign; resourcePendingCount?: number }>(), { resourcePendingCount: 0 })
const emit = defineEmits<{ back: []; resources: []; reviewResources: [release: ReleaseRecord] }>()

const session = getActiveProject()!
const phase = computed(() => session.phase)
const activeTab = ref<ArtifactTab>(session.phase.includes('build') ? 'build' : session.phase.includes('change') || session.phase === 'playable_v2_ready' ? 'preview' : 'gamespec')
const selectedContext = ref<SpecContext | null>(null)
const spec = session.spec
const reuseDrawerOpen = ref(false)
const reuseFeedback = ref(false)
let reuseFeedbackTimer: number | null = null
const changePlan = computed(() => session.changePlan)
const versionHistoryOpen = ref(false)
const releaseReviewOpen = ref(false)
const releaseDetailOpen = ref(false)
const releasePhase = computed(() => session.releasePhase)
const resourceBridgeAcknowledged = computed(() => session.resourceBridgeAcknowledged)
const playable = computed(() => getCurrentPlayable(session))
const playableVersion = computed(() => playable.value?.version ?? 0)
const currentRelease = computed<ReleaseRecord | null>(() => getCurrentRelease(session))
const releaseDraft = session.releaseDraft

function createReleaseDraft(): ReleaseDraft {
  return createReleaseDraftForProject(session.id) ?? session.releaseDraft
}

function resetReleaseDraft() {
  Object.assign(releaseDraft, createReleaseDraft())
}

const messages = computed(() => session.messages)
const relationshipResource = computed(() => {
  const resourceId = Object.entries(session.matchedResources).find(([, section]) => section === 'characters')?.[0]
  return resourceId ? projectStore.savedResources.find((resource) => resource.id === resourceId) ?? null : null
})
const reuseState = computed<'recommended' | 'dismissed' | 'used'>(() => {
  const resourceId = relationshipResource.value?.id
  if (!resourceId || session.reuseSpecVersion !== session.specVersion) return 'dismissed'
  return session.reuseDecisions[resourceId] ?? 'recommended'
})

const specTabs = [
  { id: 'gamespec' as const, label: 'GAME SPEC', icon: ScrollText },
  { id: 'preview' as const, label: 'PREVIEW', icon: MonitorPlay },
  { id: 'assets' as const, label: 'ASSETS', icon: Image },
  { id: 'code' as const, label: 'CODE', icon: FileCode2 },
]

const buildTabs = [
  { id: 'build' as const, label: 'BUILD', icon: Hammer },
  { id: 'preview' as const, label: 'PREVIEW', icon: MonitorPlay },
  { id: 'assets' as const, label: 'ASSETS', icon: Image },
  { id: 'code' as const, label: 'CODE', icon: FileCode2 },
]

const changeTabs = [
  { id: 'change' as const, label: '修改', icon: SlidersHorizontal },
  { id: 'preview' as const, label: 'PREVIEW', icon: MonitorPlay },
  { id: 'assets' as const, label: 'ASSETS', icon: Image },
  { id: 'code' as const, label: 'CODE', icon: FileCode2 },
]

const buildPhases: BuildPhase[] = [
  'build_starting', 'building_foundation', 'building_core', 'building_interaction',
  'building_presentation', 'building_progression', 'validating', 'auto_fixing',
  'validating_complete', 'playable_ready', 'build_error',
]

const changePhases: ChangePhase[] = [
  'showing_recommendations', 'playing_v1', 'change_requested', 'analyzing_change', 'change_review',
  'preparing_working_build', 'reusing_unaffected_content', 'applying_gameplay_change', 'applying_visual_change',
  'checking_scope', 'scope_violation', 'building_working_version', 'validating_change', 'auto_fixing_change',
  'validation_complete_change', 'playable_v2_ready', 'version_history',
]

const isBuildMode = computed(() => buildPhases.includes(phase.value as BuildPhase))
const isChangeMode = computed(() => changePhases.includes(phase.value as ChangePhase))
const tabs = computed(() => isChangeMode.value ? changeTabs : isBuildMode.value ? buildTabs : specTabs)
const emptyArtifactTab = computed<Exclude<ArtifactTab, 'gamespec' | 'build' | 'change'>>(() => {
  return activeTab.value === 'assets' || activeTab.value === 'code' ? activeTab.value : 'preview'
})

const generationSteps = computed(() => [
  { label: 'Reading confirmed design', state: 'done' },
  { label: 'Identifying core gameplay', state: 'done' },
  { label: 'Defining first playable scope', state: phase.value === 'generating' ? 'active' : phase.value === 'generation_error' ? 'failed' : 'done' },
  { label: 'Preparing validation criteria', state: phase.value === 'review' ? 'done' : 'upcoming' },
])

function useRelationshipResource() {
  if (!relationshipResource.value) return
  useProjectRelationshipResource(session.id, relationshipResource.value.id)
  reuseDrawerOpen.value = false
  reuseFeedback.value = true
  if (reuseFeedbackTimer !== null) window.clearTimeout(reuseFeedbackTimer)
  reuseFeedbackTimer = window.setTimeout(() => { reuseFeedback.value = false }, 900)
}

function cancelRelationshipResource() {
  if (!relationshipResource.value) return
  cancelProjectRelationshipResource(session.id, relationshipResource.value.id)
  reuseFeedback.value = false
}

function dismissRelationshipResource() {
  if (relationshipResource.value) dismissResourceRecommendation(session.id, relationshipResource.value.id)
}

function selectContext(context: SpecContext) {
  selectedContext.value = context
}

function askForRevision(text: string) {
  if (!selectedContext.value) return
  requestSpecRevision(session.id, selectedContext.value, text)
}

function applyRevision() {
  applySpecRevision(session.id)
  selectedContext.value = null
}

function requestConfirmation() {
  requestSpecConfirmation(session.id)
}

function confirmGameSpec() {
  activeTab.value = 'build'
  confirmSpecAndStartBuild(session.id)
}

function retryBuildStage() {
  retryBuild(session.id)
}

function requestChange(source: ChangeSource, request?: string) {
  versionHistoryOpen.value = false
  activeTab.value = 'change'
  requestProjectChange(session.id, source, request)
}

function selectDirection(directionId: string) {
  const labels: Record<string, string> = {
    relationship: '加强 NPC 关系反馈', farming: '优化经营体验', visual: '提升视觉表现',
  }
  requestChange('suggested_next_step', labels[directionId] ?? labels.relationship)
}

function cancelChange() {
  cancelProjectChange(session.id)
  activeTab.value = 'preview'
}

function applyControlledChange() {
  activeTab.value = 'change'
  applyProjectControlledChange(session.id)
}

function retryScopeViolation() {
  retryProjectScopeViolation(session.id)
}

function openVersionHistory() {
  if (phase.value !== 'playable_v2_ready' && phase.value !== 'version_history') return
    setWorkspacePhase(session.id, 'version_history')
  versionHistoryOpen.value = true
}

function closeVersionHistory() {
  versionHistoryOpen.value = false
  if (phase.value === 'version_history') setWorkspacePhase(session.id, 'playable_v2_ready')
}

function openReleaseReview() {
  const publishEligible = phase.value === 'playable_ready' || isChangeMode.value
  if (!publishEligible) return
  versionHistoryOpen.value = false
  releaseDetailOpen.value = false
  resetReleaseDraft()
  prepareReleaseReview(session.id)
  releaseReviewOpen.value = true
}

function publishRelease() {
  if (releasePhase.value !== 'review' && releasePhase.value !== 'error') return
  publishProjectRelease(session.id)
}

function closeReleaseReview() {
  if (releasePhase.value === 'publishing') return
  releaseReviewOpen.value = false
}

function viewRelease() {
  releaseReviewOpen.value = false
  releaseDetailOpen.value = true
}

function continueDevelopment() {
  releaseReviewOpen.value = false
  releaseDetailOpen.value = false
  activeTab.value = 'preview'
}

function acknowledgeResourceBridge() {
  acknowledgeProjectResourceBridge(session.id)
}

function reviewResources() {
  if (!currentRelease.value) return
  releaseReviewOpen.value = false
  emit('reviewResources', currentRelease.value)
}

function restoreVersion(version: number) {
  if (restorePlayable(session.id, version)) {
    versionHistoryOpen.value = false
    activeTab.value = 'preview'
  }
}

refreshResourceMatches(session.id)
onBeforeUnmount(() => {
  if (reuseFeedbackTimer !== null) window.clearTimeout(reuseFeedbackTimer)
})
</script>

<template>
  <div class="k02-workspace">
    <header class="workspace-header">
      <div class="workspace-brand"><span><Gamepad2 :size="17" /></span><strong>AI Cowork Game</strong></div>
      <button class="workspace-back" type="button" @click="$emit('back')"><ArrowLeft :size="15" />Projects</button>
      <button class="workspace-resources-link" type="button" @click="$emit('resources')">我的资源</button>
      <div class="workspace-project"><span>PROJECT</span><h1>{{ design.projectTitle }}</h1></div>
      <LifecycleRail :phase="phase" />
    </header>

    <ControlledChangeCoworkPanel
      v-if="isChangeMode"
      :phase="phase as ChangePhase"
      :plan="changePlan"
      @select="selectDirection"
      @submit="requestChange('natural_language', $event)"
          @continue-playing="setWorkspacePhase(session.id, 'playing_v1')"
          @show-recommendations="setWorkspacePhase(session.id, 'showing_recommendations')"
    />
    <BuildCoworkPanel v-else-if="isBuildMode" :phase="phase as BuildPhase" />
    <CoworkPanel
      v-else
      :phase="phase"
      :messages="messages"
      :context="selectedContext"
      @submit="askForRevision"
      @apply="applyRevision"
      @retry="startGeneration(session.id)"
      @clear-context="selectedContext = null"
    />

    <main class="artifact-workspace">
      <nav class="artifact-tabs" aria-label="项目产物">
        <button v-for="tab in tabs" :key="tab.id" type="button" :class="{ active: activeTab === tab.id }" @click="activeTab = tab.id">
          <component :is="tab.icon" :size="14" />{{ tab.label }}
        </button>
      </nav>

      <div class="artifact-stage">
        <ControlledChangeWorkspace
          v-if="activeTab === 'change' && isChangeMode"
          :phase="phase as ChangePhase"
          :plan="changePlan"
          @apply="applyControlledChange"
          @cancel="cancelChange"
          @retry-scope="retryScopeViolation"
        />

        <BuildWorkspaceView v-else-if="activeTab === 'build' && isBuildMode" :phase="phase as BuildPhase" @retry="retryBuildStage" />

        <section v-else-if="activeTab === 'gamespec' && (phase === 'generating' || phase === 'generation_error')" class="spec-generating">
          <span>GAME SPEC</span>
          <h2>Preparing your first playable specification…</h2>
          <p>正在把已确认设计收敛为一个可开发、可验证的 First Playable。</p>
          <div class="generation-track">
            <div v-for="step in generationSteps" :key="step.label" :class="`is-${step.state}`">
              <Check v-if="step.state === 'done'" :size="14" />
              <LoaderCircle v-else-if="step.state === 'active'" :size="14" class="spin" />
              <span v-else></span>
              <strong>{{ step.label }}</strong>
            </div>
          </div>
        </section>

        <GameSpecDocument
          v-else-if="activeTab === 'gamespec' && (phase === 'review' || phase === 'revising' || phase === 'confirming')"
          :spec="spec"
          :relationship-resource="relationshipResource"
          :reuse-state="reuseState"
          :reuse-feedback="reuseFeedback"
          @adjust="selectContext"
          @view-resource="reuseDrawerOpen = true"
          @use-resource="useRelationshipResource"
          @dismiss-resource="dismissRelationshipResource"
          @cancel-resource="cancelRelationshipResource"
        />

        <section v-else-if="activeTab === 'gamespec'" class="spec-confirmed-state">
          <span class="confirmed-icon"><Check :size="26" /></span>
          <span>{{ phase === 'build_starting' ? 'BUILD STARTING' : 'GAME SPEC CONFIRMED' }}</span>
          <h2>{{ phase === 'build_starting' ? '正在准备第一个 Working Build…' : '游戏规格已确认' }}</h2>
          <p>Game Design ✓ &nbsp; GameSpec ✓<br />当前规格已成为第一个 Playable Version 的构建基线。</p>
          <div class="build-start-line"><span>DESIGN</span><ChevronRight :size="13" /><span>GAMESPEC</span><ChevronRight :size="13" /><strong>BUILD</strong></div>
        </section>

        <BuildPreview
          v-else-if="activeTab === 'preview' && (isBuildMode || isChangeMode)"
          :phase="phase as BuildPhase | ChangePhase"
          :playable="playable"
          :release="currentRelease"
          :resource-bridge-acknowledged="resourceBridgeAcknowledged"
          :resource-pending-count="resourcePendingCount"
          @open-history="openVersionHistory"
          @publish="openReleaseReview"
          @view-release="viewRelease"
          @continue-development="continueDevelopment"
          @resource-later="acknowledgeResourceBridge"
          @resource-review="reviewResources"
        />
        <AssetGalleryReadOnly v-else-if="activeTab === 'assets' && (isBuildMode || isChangeMode)" :project-title="playable?.snapshot.projectTitle ?? session.spec.title" :npc-names="playable?.snapshot.npcNames ?? []" />
        <CodeReadOnlyState v-else-if="activeTab === 'code' && (isBuildMode || isChangeMode)" :project-title="playable?.snapshot.projectTitle ?? session.spec.title" />
        <ArtifactEmptyState v-else :tab="emptyArtifactTab" />
      </div>

      <footer v-if="activeTab === 'gamespec' && (phase === 'review' || phase === 'revising')" class="gamespec-gate">
        <div><Check :size="14" /><span><strong>GameSpec 已准备好</strong><small>当前 Draft 将成为第一个 Build 的输入基线</small></span></div>
        <button type="button" :disabled="phase === 'revising'" @click="requestConfirmation">确认规格并开始构建 <ArrowRight :size="16" /></button>
      </footer>

      <footer v-if="activeTab === 'gamespec' && phase === 'confirming'" class="gamespec-confirm-bar">
        <div><strong>确认 GameSpec？</strong><span>AI 将按照当前 First Playable Scope 开始构建，后续仍可以通过新版本继续修改。</span></div>
        <button type="button" @click="setWorkspacePhase(session.id, 'review')">返回检查</button>
        <button class="confirm-build" type="button" @click="confirmGameSpec">确认并开始构建 <ArrowRight :size="16" /></button>
      </footer>
    </main>
    <VersionHistoryDrawer :open="versionHistoryOpen" :versions="session.playableVersions" :design-version="session.designVersion" :spec-version="session.specVersion" @close="closeVersionHistory" @restore="restoreVersion" />
    <ReleaseReviewModal
      :open="releaseReviewOpen"
      :phase="releasePhase"
      :draft="releaseDraft"
      :release="currentRelease"
      :pending-resource-count="resourcePendingCount"
      @close="closeReleaseReview"
      @publish="publishRelease"
      @retry="publishRelease"
      @view-release="viewRelease"
      @continue-development="continueDevelopment"
      @review-resources="reviewResources"
      @update-name="updateReleaseDraft(session.id, { name: $event })"
      @update-description="updateReleaseDraft(session.id, { description: $event })"
    />
    <ReleaseDetailDrawer :open="releaseDetailOpen" :release="currentRelease" @close="releaseDetailOpen = false" @play="releaseDetailOpen = false" />
    <ResourceReuseDrawer v-if="relationshipResource" :open="reuseDrawerOpen" :resource="relationshipResource" :used="reuseState === 'used'" :spec="spec" @close="reuseDrawerOpen = false" @use="useRelationshipResource" />
  </div>
</template>
