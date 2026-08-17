<script setup lang="ts">
import { ArrowLeft, ArrowRight, Check, ChevronRight, CircleX, FileCode2, Gamepad2, Hammer, Image, LoaderCircle, MonitorPlay, Rocket, ScrollText, ShieldCheck, SlidersHorizontal, ThumbsDown } from 'lucide-vue-next'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
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
import { ApiClientError, confirmProjectGameSpec, getProjectDesign, getProjectGameSpec, saveProjectGameSpec } from '../api/client'
import { creatorGameSpecFromViewModel, gameSpecViewModelFromCreator } from '../contracts/creatorGameSpecMapping'
import { shouldResumeGameSpecGeneration } from '../contracts/gamespecRecovery'
import {
  applyControlledChange as applyProjectControlledChange,
  applySpecRevision,
  cancelChange as cancelProjectChange,
  confirmSpecAndStartBuild,
  cancelBuild,
  cancelRemoteBuild,
  getActiveProject,
  requestChange as requestProjectChange,
  requestSpecConfirmation,
  requestSpecRevision,
  retryBuild,
  startRemoteBuild,
  refreshRemoteBuild,
  refreshRemoteCandidateTest,
  refreshRemoteHumanReview,
  refreshRemotePlayable,
  reviewRemoteCandidate,
  promoteRemoteCandidate,
  rebuildRemoteCandidate,
  testRemoteCandidate,
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
  setProjectDesignStatus,
  setProjectGameSpecState,
  useRelationshipResource as useProjectRelationshipResource,
  updateReleaseDraft,
} from '../stores/projectStore'

const props = withDefaults(defineProps<{ design: ConfirmedGameDesign; resourcePendingCount?: number }>(), { resourcePendingCount: 0 })
const emit = defineEmits<{ back: []; resources: []; reviewResources: [release: ReleaseRecord] }>()

const session = getActiveProject()!
const phase = computed(() => session.phase)
const previewPhases: string[] = ['playable_ready', 'showing_recommendations', 'playing_v1', 'playable_v2_ready', 'version_history']
const activeTab = ref<ArtifactTab>(session.phase.includes('build') || session.phase === 'candidate_ready' ? 'build' : previewPhases.includes(session.phase) || session.phase.includes('change') ? 'preview' : 'gamespec')
const selectedContext = ref<SpecContext | null>(null)
const spec = session.spec
const reuseDrawerOpen = ref(false)
const reuseFeedback = ref(false)
let reuseFeedbackTimer: number | null = null
const changePlan = computed(() => session.changePlan)
const versionHistoryOpen = ref(false)
const releaseReviewOpen = ref(false)
const releaseDetailOpen = ref(false)
const humanReviewNotes = ref('')
const releasePhase = computed(() => session.releasePhase)
const resourceBridgeAcknowledged = computed(() => session.resourceBridgeAcknowledged)
const playable = computed(() => getCurrentPlayable(session))
const playableVersion = computed(() => playable.value?.version ?? 0)
const currentRelease = computed<ReleaseRecord | null>(() => getCurrentRelease(session))
const releaseDraft = session.releaseDraft
const gamespecError = ref<string | null>(null)
const gamespecLoading = ref(false)
let gamespecSaveInFlight = false

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
  'candidate_ready',
]

const changePhases: ChangePhase[] = [
  'showing_recommendations', 'playing_v1', 'change_requested', 'analyzing_change', 'change_review',
  'preparing_working_build', 'reusing_unaffected_content', 'applying_gameplay_change', 'applying_visual_change',
  'checking_scope', 'scope_violation', 'building_working_version', 'validating_change', 'auto_fixing_change',
  'validation_complete_change', 'playable_v2_ready', 'version_history',
]

const isBuildMode = computed(() => phase.value === 'spec_confirmed' || buildPhases.includes(phase.value as BuildPhase) || phase.value === 'candidate_ready')
const isBuildTimelineMode = computed(() => buildPhases.includes(phase.value as BuildPhase) && phase.value !== 'candidate_ready')
const isBuildPanelMode = computed(() => isBuildTimelineMode.value || phase.value === 'candidate_ready')
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

const evidenceLabels: Record<string, string> = {
  build_check: '构建产物',
  browser_started: '浏览器启动',
  console: '控制台错误',
  core_input: '核心输入',
  gameplay: '核心玩法',
  completion: '完成条件',
  phaser_hook: '游戏测试接口',
}

function evidenceObserved(evidence: { observed: string }) {
  return evidence.observed.includes('outside its run workspace')
    ? '无法在本次 Run Workspace 中找到 Candidate 产物。'
    : evidence.observed
}

watch(phase, (nextPhase) => {
  if (nextPhase === 'spec_confirmed' || nextPhase === 'candidate_ready') activeTab.value = 'build'
  else if (previewPhases.includes(nextPhase) || nextPhase === 'scope_violation') activeTab.value = 'preview'
})

watch(() => session.remoteBuild?.testGateStatus, (status) => {
  if (status === 'ready' && phase.value === 'candidate_ready') activeTab.value = 'build'
})

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
  void persistGameSpecDraft()
}

function requestConfirmation() {
  requestSpecConfirmation(session.id)
}

async function persistGameSpecDraft() {
  if (session.designStatus !== 'confirmed' || gamespecSaveInFlight) return true
  gamespecSaveInFlight = true
  gamespecError.value = null
  try {
    const response = await saveProjectGameSpec(session.id, creatorGameSpecFromViewModel(spec))
    setProjectGameSpecState(session.id, {
      status: response.status,
      revisionId: response.revision_id,
      spec: response.spec,
      gitCommit: response.git_commit,
    })
    return true
  } catch (cause) {
    if (!(cause instanceof ApiClientError && cause.code === 'project_not_found')) {
      gamespecError.value = cause instanceof ApiClientError ? cause.message : '暂时无法保存 GameSpec，请稍后重试。'
    }
    return false
  } finally {
    gamespecSaveInFlight = false
  }
}

async function confirmGameSpec() {
  if (session.designStatus !== 'confirmed') {
    activeTab.value = 'build'
    if (session.backendProjectId) void startRemoteBuild(session.id)
    else confirmSpecAndStartBuild(session.id)
    return
  }
  const saved = await persistGameSpecDraft()
  if (!saved) {
    setWorkspacePhase(session.id, 'review')
    return
  }
  try {
    const response = await confirmProjectGameSpec(session.id)
    setProjectGameSpecState(session.id, {
      status: response.status,
      revisionId: response.revision_id,
      spec: response.spec,
      gitCommit: response.git_commit,
    })
    activeTab.value = 'build'
    if (session.backendProjectId) void startRemoteBuild(session.id)
    else confirmSpecAndStartBuild(session.id)
  } catch (cause) {
    gamespecError.value = cause instanceof ApiClientError ? cause.message : 'GameSpec 确认失败，请检查后重试。'
    setWorkspacePhase(session.id, 'review')
  }
}

function retryBuildStage() {
  if (session.backendProjectId) {
    session.remoteBuild = null
    void startRemoteBuild(session.id)
  } else {
    retryBuild(session.id)
  }
}

function cancelBuildStage() {
  if (session.backendProjectId) void cancelRemoteBuild(session.id)
  else cancelBuild(session.id)
}

function runCandidateTest() {
  void testRemoteCandidate(session.id)
}

function rebuildCandidate() {
  void rebuildRemoteCandidate(session.id)
}

function acceptCandidate() {
  void reviewRemoteCandidate(session.id, 'accepted', humanReviewNotes.value)
}

function rejectCandidate() {
  void reviewRemoteCandidate(session.id, 'rejected', humanReviewNotes.value)
}

function promoteCandidate() {
  void promoteRemoteCandidate(session.id)
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

onMounted(async () => {
  gamespecLoading.value = true
  try {
    const designResponse = await getProjectDesign(session.id)
    setProjectDesignStatus(session.id, designResponse.status)
    if (designResponse.status === 'confirmed') {
      try {
        const response = await getProjectGameSpec(session.id)
        Object.assign(session.spec, gameSpecViewModelFromCreator(response.spec, session.spec))
        setProjectGameSpecState(session.id, {
          status: response.status,
          revisionId: response.revision_id,
          spec: response.spec,
          gitCommit: response.git_commit,
        })
        if (response.status === 'confirmed') {
          if (session.backendProjectId) {
            // Restore the real Playable first. A refresh must never create a
            // second Build when a durable version or run already exists.
            await refreshRemotePlayable(session.id)
            if (session.remoteBuild?.buildId) await refreshRemoteBuild(session.id)
            if (session.remoteBuild?.candidateId) {
              await refreshRemoteCandidateTest(session.id)
              await refreshRemoteHumanReview(session.id)
            }
            if (session.remoteBuild?.playableVersion) {
              activeTab.value = 'preview'
              setWorkspacePhase(session.id, 'playable_ready')
            } else if (session.remoteBuild?.buildId) {
              activeTab.value = session.remoteBuild.status === 'succeeded' ? 'build' : 'preview'
            } else {
              void startRemoteBuild(session.id)
            }
          } else if (getCurrentPlayable(session)) setWorkspacePhase(session.id, 'playable_ready')
          else confirmSpecAndStartBuild(session.id)
        }
      } catch (cause) {
        if (cause instanceof ApiClientError && cause.code === 'gamespec_not_found') {
          if (shouldResumeGameSpecGeneration(session.phase, session.gamespecStatus)) {
            startGeneration(session.id)
          }
        } else {
          gamespecError.value = cause instanceof ApiClientError ? cause.message : '暂时无法读取 GameSpec。'
        }
      }
    }
  } catch (cause) {
    if (!(cause instanceof ApiClientError && cause.code === 'project_not_found')) {
      gamespecError.value = cause instanceof ApiClientError ? cause.message : '暂时无法读取设计状态。'
    }
  } finally {
    gamespecLoading.value = false
  }
})

watch(phase, (nextPhase) => {
  if (nextPhase === 'review' && session.designStatus === 'confirmed' && session.gamespecStatus === 'missing') {
    void persistGameSpecDraft()
  }
})
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
    <BuildCoworkPanel v-else-if="isBuildPanelMode" :phase="phase as BuildPhase" :error-code="session.remoteBuild?.errorCode" :error-message="session.remoteBuild?.errorMessage" />
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

        <section v-else-if="activeTab === 'build' && phase === 'spec_confirmed'" class="spec-confirmed-state">
          <span class="confirmed-icon"><LoaderCircle :size="26" class="spin" /></span>
          <span>BUILD STARTING</span>
          <h2>正在准备第一个 Working Build…</h2>
          <p>GameSpec 已确认。接下来会按 First Playable 范围构建并验证核心玩法。</p>
          <div class="build-start-line"><span>DESIGN</span><ChevronRight :size="13" /><span>GAMESPEC</span><ChevronRight :size="13" /><strong>BUILD</strong></div>
        </section>

        <section v-else-if="activeTab === 'build' && phase === 'candidate_ready'" class="candidate-ready-state">
          <span class="confirmed-icon"><Check :size="26" /></span>
          <span>BUILD CANDIDATE READY</span>
          <h2>真实 Build 已生成候选版本</h2>
          <p>OpenGame 已生成构建产物。它还没有成为 Playable，需要先完成平台验证和人工试玩确认。</p>
          <dl class="candidate-ready-meta">
            <div><dt>Candidate</dt><dd>{{ session.remoteBuild?.candidateId }}</dd></div>
            <div><dt>入口</dt><dd>{{ session.remoteBuild?.artifactPath ?? '已生成，等待验证' }}</dd></div>
          </dl>
          <div class="candidate-test-gate" :class="`is-${session.remoteBuild?.testGateStatus ?? 'untested'}`">
            <div>
              <strong>{{ session.remoteBuild?.testGateStatus === 'ready' ? '平台验证通过' : session.remoteBuild?.testGateStatus && session.remoteBuild.testGateStatus !== 'untested' ? '平台验证未通过' : '等待平台验证' }}</strong>
              <p v-if="session.remoteBuild?.testReport">{{ session.remoteBuild.testGateStatus === 'ready' ? '真实浏览器检查与核心玩法证据均已通过。' : '平台验证发现阻塞项，Candidate 尚不能进入人工试玩确认。' }}</p>
              <p v-else-if="session.remoteBuild?.testGateStatus === 'untested' || !session.remoteBuild?.testGateStatus">将使用真实 Chrome 检查页面启动、控制台、核心输入、玩法和完成条件。</p>
              <p v-else>正在读取已保存的验证证据。</p>
            </div>
            <button v-if="!session.remoteBuild?.testReport" type="button" :disabled="session.remoteBuild?.testRunning || (session.remoteBuild?.testGateStatus !== undefined && session.remoteBuild.testGateStatus !== 'untested')" @click="runCandidateTest">
              <LoaderCircle v-if="session.remoteBuild?.testRunning" :size="15" class="spin" />
              <Check v-else :size="15" />
              {{ session.remoteBuild?.testRunning ? '正在验证' : '运行平台验证' }}
            </button>
            <button v-else-if="session.remoteBuild.testGateStatus !== 'ready'" type="button" @click="rebuildCandidate"><Hammer :size="15" />重新构建 Candidate</button>
          </div>
          <p v-if="session.remoteBuild?.testError" class="candidate-test-error">{{ session.remoteBuild.testError }}</p>
          <ul v-if="session.remoteBuild?.testReport" class="candidate-evidence-list" aria-label="平台验证证据">
            <li v-for="evidence in session.remoteBuild.testReport.evidence" :key="evidence.id" :class="`is-${evidence.status}`">
              <Check v-if="evidence.status === 'passed'" :size="14" />
              <CircleX v-else :size="14" />
              <span><strong>{{ evidenceLabels[evidence.kind] ?? evidence.kind }}</strong><small>{{ evidenceObserved(evidence) }}</small></span>
            </li>
          </ul>
          <section v-if="session.remoteBuild?.candidatePreviewUrl" class="candidate-live-preview" aria-label="Candidate 人工试玩预览">
            <header>
              <div><strong>Candidate 人工试玩</strong><span>这是待审核构建，不会覆盖当前 Playable</span></div>
              <Gamepad2 :size="16" />
            </header>
            <iframe
              :src="session.remoteBuild.candidatePreviewUrl"
              title="Candidate 人工试玩预览"
              sandbox="allow-scripts allow-same-origin"
            ></iframe>
          </section>
          <section class="human-play-gate" :class="`is-${session.remoteBuild?.humanReview?.decision ?? 'pending'}`" aria-label="Human Play Review">
            <div class="human-play-gate-heading">
              <ShieldCheck :size="18" />
              <div>
                <strong>Human Play Review</strong>
                <p v-if="session.remoteBuild?.humanReview?.decision === 'accepted'">你已确认这个 Candidate 可以代表当前 GameSpec。下一步由你决定是否 Promote。</p>
                <p v-else-if="session.remoteBuild?.humanReview?.decision === 'rejected'">这个 Candidate 已退回。可以记录原因并重新构建，不会影响现有 Playable。</p>
                <p v-else-if="session.remoteBuild?.testGateStatus === 'ready'">请打开候选版本并确认核心玩法、输入和完成条件，再做人工决定。</p>
                <p v-else>平台验证通过后，才能进入人工试玩确认。</p>
              </div>
            </div>
            <textarea
              v-if="!session.remoteBuild?.humanReview || session.remoteBuild.humanReview.decision === 'pending'"
              v-model="humanReviewNotes"
              class="human-play-notes"
              :disabled="session.remoteBuild?.testGateStatus !== 'ready' || session.remoteBuild?.reviewRunning"
              rows="2"
              placeholder="可选：记录这次试玩观察"
            ></textarea>
            <p v-if="session.remoteBuild?.reviewError" class="candidate-test-error">{{ session.remoteBuild.reviewError }}</p>
            <div v-if="!session.remoteBuild?.humanReview || session.remoteBuild.humanReview.decision === 'pending'" class="human-play-actions">
              <button type="button" class="human-play-reject" :disabled="session.remoteBuild?.testGateStatus !== 'ready' || session.remoteBuild?.reviewRunning" @click="rejectCandidate">
                <ThumbsDown :size="14" />退回修改
              </button>
              <button type="button" class="human-play-accept" :disabled="session.remoteBuild?.testGateStatus !== 'ready' || session.remoteBuild?.reviewRunning" @click="acceptCandidate">
                <Check :size="14" />{{ session.remoteBuild?.reviewRunning ? '正在保存' : '确认试玩通过' }}
              </button>
            </div>
            <div v-else-if="session.remoteBuild?.humanReview?.decision === 'accepted'" class="human-play-promote">
              <span><Check :size="14" />人工试玩已通过</span>
              <button type="button" :disabled="session.remoteBuild.promoteRunning" @click="promoteCandidate">
                <Rocket :size="14" />{{ session.remoteBuild.promoteRunning ? '正在设为 Playable' : 'Promote 为当前 Playable' }}
              </button>
            </div>
            <div v-else class="human-play-promote">
              <span><ThumbsDown :size="14" />已退回，不影响当前 Playable</span>
              <button type="button" @click="rebuildCandidate"><Hammer :size="14" />重新构建 Candidate</button>
            </div>
            <p v-if="session.remoteBuild?.promoteError" class="candidate-test-error">{{ session.remoteBuild.promoteError }}</p>
          </section>
        </section>

        <BuildWorkspaceView v-else-if="activeTab === 'build' && isBuildTimelineMode" :phase="phase as BuildPhase" :error-code="session.remoteBuild?.errorCode" :error-message="session.remoteBuild?.errorMessage" @retry="retryBuildStage" @cancel="cancelBuildStage" />

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
          :real-preview-url="session.remoteBuild?.previewUrl"
          :candidate-preview-url="session.remoteBuild?.candidatePreviewUrl"
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

      <p v-if="gamespecLoading" class="gamespec-api-status" aria-live="polite">正在读取已保存的 GameSpec…</p>
      <p v-if="gamespecError" class="gamespec-api-error" role="alert">{{ gamespecError }}</p>

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
