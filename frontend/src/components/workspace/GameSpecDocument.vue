<script setup lang="ts">
import { ArrowDown, ArrowRight, Check, Circle, Eye, RotateCcw } from 'lucide-vue-next'
import { computed } from 'vue'
import ResourceReuseRecommendation from './ResourceReuseRecommendation.vue'
import type { ResourceCandidate } from '../resources/resourceTypes'
import { specContexts } from './gameSpecFixture'
import SpecSection from './SpecSection.vue'
import type { GameSpecModel, SpecContext } from './workspaceTypes'

const props = withDefaults(defineProps<{ spec: GameSpecModel; relationshipResource?: ResourceCandidate | null; reuseState?: 'recommended' | 'dismissed' | 'used'; reuseFeedback?: boolean }>(), { relationshipResource: null, reuseState: 'dismissed', reuseFeedback: false })
defineEmits<{ adjust: [context: SpecContext]; viewResource: []; useResource: []; dismissResource: []; cancelResource: [] }>()

function isUpdated(key: string) {
  return props.spec.updatedSections.includes(key)
}

const characterContext = computed<SpecContext>(() => ({
  ...specContexts.characters,
  label: `NPC / ${props.spec.characters.npcName}`,
  path: ['GameSpec', 'NPC 与关系', props.spec.characters.npcName],
}))
</script>

<template>
  <article class="gamespec-document">
    <header class="gamespec-titlebar">
      <div>
        <span>GAME SPEC</span>
        <h1>{{ spec.title }} <small>· First Playable</small></h1>
      </div>
      <span class="draft-status">{{ spec.draftLabel }}</span>
    </header>

    <SpecSection
      kicker="FIRST PLAYABLE TARGET"
      title="这一版要验证什么"
      :context="specContexts.target"
      source="confirmed"
      :updated="isUpdated('target')"
      @adjust="$emit('adjust', $event)"
    >
      <p class="build-target-goal">{{ spec.buildTarget.goal }}</p>
      <div class="target-hypothesis"><span>本版本重点验证</span><strong>{{ spec.buildTarget.hypothesis }}</strong></div>
      <template #technical>
        <dl><dt>Target</dt><dd>Desktop browser</dd><dt>Runtime</dt><dd>Phaser 3 · TypeScript</dd><dt>Format</dt><dd>Fixed 2D top-down template</dd></dl>
      </template>
    </SpecSection>

    <SpecSection
      kicker="CORE GAMEPLAY"
      title="玩家真正会做什么"
      :context="specContexts.gameplay"
      source="confirmed"
      :updated="isUpdated('gameplay')"
      @adjust="$emit('adjust', $event)"
    >
      <h3 class="spec-subheading">Core Loop</h3>
      <div class="spec-loop">
        <template v-for="(step, index) in spec.gameplay.coreLoop" :key="step">
          <span>{{ step }}</span><ArrowRight v-if="index < spec.gameplay.coreLoop.length - 1" :size="13" />
        </template>
      </div>
      <h3 class="spec-subheading">Player Actions</h3>
      <div class="action-list"><span v-for="action in spec.gameplay.actions" :key="action">{{ action }}</span></div>
      <template #technical>
        <dl><dt>Input</dt><dd>WASD / Arrow Keys</dd><dt>Interaction</dt><dd>E</dd><dt>Physics</dt><dd>Arcade Physics</dd><dt>Events</dt><dd>crop_harvested · request_completed · favor_updated</dd></dl>
      </template>
    </SpecSection>

    <SpecSection
      kicker="WORLD & CHARACTERS"
      title="NPC 与关系"
      :context="characterContext"
      source="default"
      :updated="isUpdated('characters')"
      @adjust="$emit('adjust', $event)"
    >
      <div v-if="reuseState === 'used' && relationshipResource" class="resource-reuse-status" :class="{ 'is-entering': reuseFeedback }">
        <Check :size="15" /><span><strong>已使用 {{ relationshipResource.name }}</strong><small>已适配到当前 GameSpec 的关系字段</small></span><div></div><button type="button" @click="$emit('viewResource')"><Eye :size="13" />查看资源</button><button type="button" @click="$emit('cancelResource')"><RotateCcw :size="13" />取消使用</button>
      </div>
      <ResourceReuseRecommendation v-else-if="reuseState === 'recommended' && relationshipResource" :resource="relationshipResource" @view="$emit('viewResource')" @use="$emit('useResource')" @dismiss="$emit('dismissResource')" />

      <dl class="relationship-spec-rows" :class="{ 'is-reuse-updated': reuseFeedback }">
        <div><dt>主要 NPC</dt><dd>{{ spec.characters.primaryNpcs }}</dd></div>
        <div><dt>关系成长</dt><dd>{{ spec.characters.relationshipGrowth }}</dd></div>
        <div v-if="spec.characters.favorRules"><dt>好感规则</dt><dd>{{ spec.characters.favorRules }}</dd></div>
        <div><dt>关系事件</dt><dd>{{ spec.characters.relationshipEvents }}</dd></div>
        <div v-if="spec.characters.requestRewards"><dt>任务奖励</dt><dd>{{ spec.characters.requestRewards }}</dd></div>
      </dl>
      <div class="character-support-grid"><div><span class="entity-type">PLAYER</span><h3>{{ spec.characters.player }}</h3><ul><li v-for="action in spec.characters.playerActions" :key="action">{{ action }}</li></ul></div><div><span class="entity-type">WORLD</span><h3>第一版区域</h3><ul><li v-for="area in spec.characters.worldAreas" :key="area">{{ area }}</li></ul></div></div>
      <template #technical>
        <dl><dt>NPC state</dt><dd>{{ spec.characters.dialogueStates.join(' → ') }}</dd><dt>Movement</dt><dd>Fixed area patrol</dd><dt>Dialogue</dt><dd>Structured dialogue pools</dd></dl>
      </template>
    </SpecSection>

    <SpecSection
      kicker="RULES & PROGRESSION"
      title="目标、成长与完成条件"
      :context="specContexts.rules"
      source="confirmed"
      :updated="isUpdated('rules')"
      @adjust="$emit('adjust', $event)"
    >
      <div class="progression-lane">
        <template v-for="(step, index) in spec.rules.progression" :key="step">
          <span>{{ step }}</span><ArrowDown v-if="index < spec.rules.progression.length - 1" :size="13" />
        </template>
      </div>
      <div class="completion-rule"><span>WIN / COMPLETION</span><strong>{{ spec.rules.completion }}</strong></div>
    </SpecSection>

    <SpecSection
      kicker="FIRST PLAYABLE SCOPE"
      title="第一版先做什么"
      :context="specContexts.scope"
      source="simplified"
      :updated="isUpdated('scope')"
      @adjust="$emit('adjust', $event)"
    >
      <p class="scope-intro">先完成一个真正可以玩的核心闭环，其余内容保留到后续版本。</p>
      <div class="scope-board">
        <div class="scope-in"><span>FIRST PLAYABLE</span><ul><li v-for="item in spec.scope.included" :key="item"><Check :size="13" />{{ item }}</li></ul></div>
        <div class="scope-later"><span>LATER</span><ul><li v-for="item in spec.scope.later" :key="item"><Circle :size="11" />{{ item }}</li></ul></div>
      </div>
    </SpecSection>

    <SpecSection
      kicker="DEFINITION OF PLAYABLE"
      title="做到什么才算完成"
      :context="specContexts.validation"
      source="default"
      :updated="isUpdated('validation')"
      @adjust="$emit('adjust', $event)"
    >
      <p class="validation-intro">第一个 Working Build 必须满足：</p>
      <ul class="validation-list"><li v-for="item in spec.validation" :key="item"><Check :size="14" />{{ item }}</li></ul>
      <template #technical>
        <dl><dt>Type check</dt><dd>Required</dd><dt>Production build</dt><dd>Required</dd><dt>Browser smoke</dt><dd>Chromium</dd><dt>Blocking console errors</dt><dd>0</dd></dl>
      </template>
    </SpecSection>
  </article>
</template>
