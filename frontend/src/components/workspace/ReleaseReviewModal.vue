<script setup lang="ts">
import { AlertTriangle, ArrowRight, BadgeCheck, Check, Gamepad2, LoaderCircle, PackageCheck, RotateCcw, X } from 'lucide-vue-next'
import type { ReleaseDraft, ReleasePhase, ReleaseRecord } from './releaseTypes'

const props = defineProps<{
  open: boolean
  phase: ReleasePhase
  draft: ReleaseDraft
  release: ReleaseRecord | null
}>()

const emit = defineEmits<{
  close: []
  publish: []
  retry: []
  viewRelease: []
  continueDevelopment: []
  reviewResources: []
  updateName: [value: string]
  updateDescription: [value: string]
}>()
</script>

<template>
  <Transition name="release-modal">
    <div v-if="open" class="release-review-layer" role="dialog" aria-modal="true" aria-labelledby="release-review-title">
      <button class="release-review-scrim" type="button" aria-label="关闭发布审阅" @click="phase === 'review' && emit('close')"></button>
      <section class="release-review-modal">
        <header>
          <div>
            <span>正式 RELEASE</span>
            <h2 id="release-review-title">{{ phase === 'success' ? `Release v${release?.version} 已创建` : phase === 'error' ? 'Release 创建失败' : '发布正式版本' }}</h2>
            <p v-if="phase === 'review'">把当前稳定游戏冻结为一个正式 Release。</p>
          </div>
          <button v-if="phase !== 'publishing'" type="button" aria-label="关闭发布审阅" @click="emit('close')"><X :size="17" /></button>
        </header>

        <div v-if="phase === 'review'" class="release-review-body">
          <div class="release-version-imprint">
            <div>
              <span>发布目标</span>
              <strong><Gamepad2 :size="16" />Playable v{{ draft.basedOnPlayable }} · 稳定</strong>
              <small><BadgeCheck :size="13" />Validation 已通过</small>
            </div>
            <ArrowRight :size="18" />
            <div>
              <span>新的正式版本</span>
              <strong><PackageCheck :size="16" />Release v{{ draft.version }}</strong>
              <small>创建后保持冻结</small>
            </div>
          </div>

          <label class="release-field">
            <span>版本名称</span>
            <input :value="draft.name" @input="emit('updateName', ($event.target as HTMLInputElement).value)" />
          </label>
          <label class="release-field">
            <span>版本说明</span>
            <textarea :value="draft.description" rows="3" @input="emit('updateDescription', ($event.target as HTMLTextAreaElement).value)"></textarea>
          </label>

          <div class="release-provenance">
            <span>来源记录</span>
            <strong>Playable v{{ draft.basedOnPlayable }}</strong>
            <strong>GameSpec v{{ draft.basedOnGameSpec }}</strong>
            <strong>Game Design v{{ draft.basedOnGameDesign }}</strong>
          </div>

          <div class="release-effect-note">
            <Check :size="16" />
            <div><strong>发布不会结束项目</strong><p>当前 Playable 仍可继续开发；Release v{{ draft.version }} 不会被后续修改自动覆盖。</p></div>
          </div>
        </div>

        <div v-else-if="phase === 'publishing'" class="release-process-state">
          <LoaderCircle :size="30" class="spin" />
          <span>正在创建 Release v{{ draft.version }}…</span>
          <h3>冻结 Playable v{{ draft.basedOnPlayable }}</h3>
          <ul><li><Check :size="14" />验证发布资格</li><li><LoaderCircle :size="14" class="spin" />创建正式 Release</li></ul>
        </div>

        <div v-else-if="phase === 'error'" class="release-process-state is-error">
          <AlertTriangle :size="30" />
          <span>创建没有完成</span>
          <h3>Release v{{ draft.version }} 尚未创建</h3>
          <p>当前 Playable v{{ draft.basedOnPlayable }} 没有受到影响。重新发布不会生成重复版本。</p>
          <button type="button" @click="emit('retry')"><RotateCcw :size="14" />重新发布</button>
        </div>

        <div v-else class="release-success-state">
          <span class="release-success-mark"><PackageCheck :size="30" /></span>
          <small>RELEASE CREATED</small>
          <h3>{{ release?.name }}</h3>
          <p>Release v{{ release?.version }} 已基于 Playable v{{ release?.basedOnPlayable }} 冻结。后续开发不会改变这个正式版本。</p>
          <div class="release-success-actions">
            <button type="button" @click="emit('continueDevelopment')">继续开发</button>
            <button type="button" class="primary" @click="emit('viewRelease')">查看 Release <ArrowRight :size="14" /></button>
          </div>
          <div class="release-success-resource-bridge">
            <div><span>可复用资源候选</span><strong>发现 3 个可能值得沉淀的内容</strong><small>1 个玩法模块 · 1 个 UI 模块 · 1 个视觉资产</small><p>这些目前只是候选，不会自动进入正式资源库。</p></div>
            <button type="button" @click="emit('continueDevelopment')">稍后处理</button>
            <button type="button" class="primary" @click="emit('reviewResources')">Review 资源 <ArrowRight :size="14" /></button>
          </div>
        </div>

        <footer v-if="phase === 'review'">
          <button type="button" @click="emit('close')">取消</button>
          <button type="button" class="primary" @click="emit('publish')">发布 Release v{{ draft.version }} <ArrowRight :size="15" /></button>
        </footer>
      </section>
    </div>
  </Transition>
</template>
