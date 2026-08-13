<script setup lang="ts">
import { ArrowLeft, ArrowRight, Check, ChevronRight, FileCode2, Gamepad2, Hammer, Image, LoaderCircle, MonitorPlay, ScrollText, SlidersHorizontal } from 'lucide-vue-next'
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
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
import type { ResourceCandidate } from '../components/resources/resourceTypes'
import type { BuildPhase } from '../components/workspace/buildTypes'
import type { ChangePhase, ChangeSource } from '../components/workspace/changeTypes'
import type { ReleaseDraft, ReleasePhase, ReleaseRecord } from '../components/workspace/releaseTypes'
import type { ArtifactTab, SpecContext } from '../components/workspace/workspaceTypes'
import {
  applyControlledChange as applyProjectControlledChange,
  applySpecRevision,
  cancelChange as cancelProjectChange,
  clearJob,
  confirmSpecAndStartBuild,
  createProject,
  getActiveProject,
  requestChange as requestProjectChange,
  requestSpecConfirmation,
  requestSpecRevision,
  retryBuild,
  retryScopeViolation as retryProjectScopeViolation,
  scheduleJob,
  setDebugFlags,
  startBuildTimeline,
  startGeneration,
} from '../stores/projectStore'

const props = withDefaults(defineProps<{ design: ConfirmedGameDesign; initialRelease?: ReleaseRecord | null; resourcePendingCount?: number; relationshipResource?: ResourceCandidate | null }>(), { initialRelease: null, resourcePendingCount: 3, relationshipResource: null })
const emit = defineEmits<{ back: []; resources: []; reviewResources: [release: ReleaseRecord] }>()

const requestedScreen = new URLSearchParams(window.location.search).get('screen')
const startInBuild = requestedScreen === 'build'
const startInChange = requestedScreen === 'change'
const startInPublish = requestedScreen === 'publish' || requestedScreen === 'resources'
const session = getActiveProject() ?? createProject(props.design)
const phase = computed(() => session.phase)
const activeTab = ref<ArtifactTab>(startInPublish || startInChange ? 'preview' : startInBuild ? 'build' : 'gamespec')
const selectedContext = ref<SpecContext | null>(null)
const spec = session.spec
type ResourceReuseState = 'recommended' | 'dismissed' | 'used'
type RelationshipDraft = Pick<typeof spec.characters, 'primaryNpcs' | 'relationshipGrowth' | 'favorRules' | 'relationshipEvents' | 'requestRewards'>
const resourceReuseDemo = requestedScreen === 'resource-reuse'
const reuseState = ref<ResourceReuseState>(resourceReuseDemo && props.relationshipResource ? 'recommended' : 'dismissed')
const reuseDrawerOpen = ref(false)
const reuseFeedback = ref(false)
const relationshipSnapshot = ref<Readonly<RelationshipDraft> | null>(null)
let reuseFeedbackTimer: number | null = null
const forceGenerationError = new URLSearchParams(window.location.search).get('specError') === '1'
const forceBuildError = new URLSearchParams(window.location.search).get('buildError') === '1'
const forceScopeError = new URLSearchParams(window.location.search).get('scopeError') === '1'
const changePlan = computed(() => session.changePlan)
const versionHistoryOpen = ref(false)
const releaseReviewOpen = ref(false)
const releaseDetailOpen = ref(false)
const releasePhase = ref<ReleasePhase>('review')
const forcePublishError = new URLSearchParams(window.location.search).get('publishError') === '1'
const divergedReleaseDemo = new URLSearchParams(window.location.search).get('diverged') === '1'
const hasUsedPublishError = ref(false)
const resourceBridgeAcknowledged = ref(false)
const playableVersion = ref(divergedReleaseDemo ? 3 : startInPublish ? 2 : 1)
const currentRelease = ref<ReleaseRecord | null>(props.initialRelease ?? (divergedReleaseDemo ? {
  id: 'release-v1', version: 1, name: '多代田园物语 · First Release',
  description: '完成核心经营、NPC 关系与代际传承体验的第一个正式版本。',
  basedOnPlayable: 2, basedOnGameDesign: 2, basedOnGameSpec: 2,
  status: 'published', createdAt: '上一正式里程碑',
} : null))
const releaseDraft = reactive<ReleaseDraft>(createReleaseDraft())

function createReleaseDraft(): ReleaseDraft {
  const nextVersion = (currentRelease.value?.version ?? 0) + 1
  return {
    version: nextVersion,
    name: nextVersion === 1 ? '多代田园物语 · First Release' : `多代田园物语 · Release ${nextVersion}`,
    description: nextVersion === 1
      ? '完成核心经营、NPC 关系与代际传承体验的第一个正式版本。'
      : '优化 NPC 关系反馈，新增好感 UI 与关系事件。',
    basedOnPlayable: playableVersion.value,
    basedOnGameDesign: 2,
    basedOnGameSpec: 2,
  }
}

function resetReleaseDraft() {
  Object.assign(releaseDraft, createReleaseDraft())
}

const messages = computed(() => session.messages)

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

function cloneRelationshipDraft(): RelationshipDraft {
  return {
    primaryNpcs: spec.characters.primaryNpcs,
    relationshipGrowth: spec.characters.relationshipGrowth,
    favorRules: spec.characters.favorRules,
    relationshipEvents: spec.characters.relationshipEvents,
    requestRewards: spec.characters.requestRewards,
  }
}

function useRelationshipResource() {
  if (!resourceReuseDemo || !props.relationshipResource) return
  if (relationshipSnapshot.value === null) relationshipSnapshot.value = Object.freeze({ ...cloneRelationshipDraft() })
  Object.assign(spec.characters, {
    primaryNpcs: 'Emily · 店员；Alex · 常客。',
    relationshipGrowth: '完成 NPC 委托或互动后获得好感。',
    favorRules: '默认范围 0–100；关键关系节点为 30 / 60 / 80。',
    relationshipEvents: '达到关键关系节点后，可以触发新的角色事件。',
    requestRewards: '完成普通委托：好感 +5；完成重要事件：好感 +10。',
  })
  if (!spec.updatedSections.includes('characters')) spec.updatedSections.push('characters')
  reuseState.value = 'used'
  reuseDrawerOpen.value = false
  reuseFeedback.value = true
  if (reuseFeedbackTimer !== null) window.clearTimeout(reuseFeedbackTimer)
  reuseFeedbackTimer = window.setTimeout(() => { reuseFeedback.value = false }, 900)
}

function cancelRelationshipResource() {
  if (!relationshipSnapshot.value) return
  Object.assign(spec.characters, { ...relationshipSnapshot.value })
  reuseState.value = 'recommended'
  reuseFeedback.value = false
}

function dismissRelationshipResource() {
  reuseState.value = 'dismissed'
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
  session.phase = 'version_history'
  versionHistoryOpen.value = true
}

function closeVersionHistory() {
  versionHistoryOpen.value = false
  if (phase.value === 'version_history') session.phase = 'playable_v2_ready'
}

function openReleaseReview() {
  const publishEligible = phase.value === 'playable_ready' || isChangeMode.value
  if (!publishEligible) return
  versionHistoryOpen.value = false
  releaseDetailOpen.value = false
  resetReleaseDraft()
  releasePhase.value = 'review'
  releaseReviewOpen.value = true
}

function publishRelease() {
  if (releasePhase.value !== 'review' && releasePhase.value !== 'error') return
  releasePhase.value = 'publishing'
  scheduleJob(session.id, 'publish', () => {
    if (forcePublishError && !hasUsedPublishError.value) {
      hasUsedPublishError.value = true
      releasePhase.value = 'error'
      return
    }
    currentRelease.value = {
      ...releaseDraft,
      id: `release-v${releaseDraft.version}`,
      status: 'published',
      createdAt: '刚刚',
    }
    releasePhase.value = 'success'
  }, 900)
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
  resourceBridgeAcknowledged.value = true
}

function reviewResources() {
  if (!currentRelease.value) return
  releaseReviewOpen.value = false
  emit('reviewResources', currentRelease.value)
}

setDebugFlags({ specError: forceGenerationError, buildError: forceBuildError, scopeError: forceScopeError })

if (startInPublish || startInChange) {
  requestProjectChange(session.id, 'suggested_next_step')
  session.phase = startInPublish ? 'playable_v2_ready' : 'showing_recommendations'
} else if (startInBuild) startBuildTimeline(session.id)
else if (session.phase === 'generating' && session.messages.length === 0) startGeneration(session.id)
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
      @continue-playing="phase = 'playing_v1'"
      @show-recommendations="phase = 'showing_recommendations'"
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
          :playable-version="playableVersion"
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
        <AssetGalleryReadOnly v-else-if="activeTab === 'assets' && (isBuildMode || isChangeMode)" />
        <CodeReadOnlyState v-else-if="activeTab === 'code' && (isBuildMode || isChangeMode)" />
        <ArtifactEmptyState v-else :tab="emptyArtifactTab" />
      </div>

      <footer v-if="activeTab === 'gamespec' && (phase === 'review' || phase === 'revising')" class="gamespec-gate">
        <div><Check :size="14" /><span><strong>GameSpec 已准备好</strong><small>当前 Draft 将成为第一个 Build 的输入基线</small></span></div>
        <button type="button" :disabled="phase === 'revising'" @click="requestConfirmation">确认规格并开始构建 <ArrowRight :size="16" /></button>
      </footer>

      <footer v-if="activeTab === 'gamespec' && phase === 'confirming'" class="gamespec-confirm-bar">
        <div><strong>确认 GameSpec？</strong><span>AI 将按照当前 First Playable Scope 开始构建，后续仍可以通过新版本继续修改。</span></div>
        <button type="button" @click="phase = 'review'">返回检查</button>
        <button class="confirm-build" type="button" @click="confirmGameSpec">确认并开始构建 <ArrowRight :size="16" /></button>
      </footer>
    </main>
    <VersionHistoryDrawer :open="versionHistoryOpen" @close="closeVersionHistory" />
    <ReleaseReviewModal
      :open="releaseReviewOpen"
      :phase="releasePhase"
      :draft="releaseDraft"
      :release="currentRelease"
      @close="closeReleaseReview"
      @publish="publishRelease"
      @retry="publishRelease"
      @view-release="viewRelease"
      @continue-development="continueDevelopment"
      @review-resources="reviewResources"
      @update-name="releaseDraft.name = $event"
      @update-description="releaseDraft.description = $event"
    />
    <ReleaseDetailDrawer :open="releaseDetailOpen" :release="currentRelease" @close="releaseDetailOpen = false" @play="releaseDetailOpen = false" />
    <ResourceReuseDrawer v-if="relationshipResource" :open="reuseDrawerOpen" :resource="relationshipResource" :used="reuseState === 'used'" @close="reuseDrawerOpen = false" @use="useRelationshipResource" />
  </div>
</template>
