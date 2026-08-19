import type { GameSpecModel } from '../components/workspace/workspaceTypes'
import type { CreatorGameSpec, RuntimeBuildSpec } from './creatorGameSpec'

const copyList = (items: string[]): string[] => [...items]
const defaultCoreLoop = ['执行主要行动', '观察结果并调整下一步', '推进主要目标', '触发完成或失败结算']

function nonEmptyCoreLoop(items: string[]): string[] {
  const steps = items.filter((item) => item.trim().length > 0)
  return steps.length > 0 ? steps : copyList(defaultCoreLoop)
}

export function creatorGameSpecFromViewModel(model: GameSpecModel): CreatorGameSpec {
  return {
    schema_version: 1,
    title: model.title,
    first_playable: {
      goal: model.buildTarget.goal,
      hypothesis: model.buildTarget.hypothesis,
    },
    gameplay: {
      core_loop: nonEmptyCoreLoop(model.gameplay.coreLoop),
      actions: copyList(model.gameplay.actions),
    },
    characters: {
      player: model.characters.player,
      player_actions: copyList(model.characters.playerActions),
      npc_name: model.characters.npcName,
      npc_role: model.characters.npcRole,
      npc_behaviors: copyList(model.characters.npcBehaviors),
      dialogue_states: copyList(model.characters.dialogueStates),
      world_areas: copyList(model.characters.worldAreas),
      primary_npcs: model.characters.primaryNpcs,
      relationship_growth: model.characters.relationshipGrowth,
      favor_rules: model.characters.favorRules,
      relationship_events: model.characters.relationshipEvents,
      request_rewards: model.characters.requestRewards,
    },
    rules: {
      progression: copyList(model.rules.progression),
      completion: model.rules.completion,
    },
    scope: {
      included: copyList(model.scope.included),
      later: copyList(model.scope.later),
    },
    validation: copyList(model.validation),
  }
}

export function runtimeBuildSpecFromCreator(spec: CreatorGameSpec): RuntimeBuildSpec {
  return {
    project_title: spec.title,
    first_playable_goal: spec.first_playable.goal,
    first_playable_hypothesis: spec.first_playable.hypothesis,
    core_loop: copyList(spec.gameplay.core_loop),
    actions: copyList(spec.gameplay.actions),
    characters: {
      ...spec.characters,
      player_actions: copyList(spec.characters.player_actions),
      npc_behaviors: copyList(spec.characters.npc_behaviors),
      dialogue_states: copyList(spec.characters.dialogue_states),
      world_areas: copyList(spec.characters.world_areas),
    },
    rules: {
      progression: copyList(spec.rules.progression),
      completion: spec.rules.completion,
    },
    included_scope: copyList(spec.scope.included),
    validation: copyList(spec.validation),
  }
}

export function gameSpecViewModelFromCreator(spec: CreatorGameSpec, fallback: GameSpecModel): GameSpecModel {
  return {
    ...fallback,
    title: spec.title,
    draftLabel: `Draft · v${spec.schema_version}`,
    buildTarget: {
      goal: spec.first_playable.goal,
      hypothesis: spec.first_playable.hypothesis,
    },
    gameplay: {
      coreLoop: copyList(spec.gameplay.core_loop),
      actions: copyList(spec.gameplay.actions),
    },
    characters: {
      ...fallback.characters,
      player: spec.characters.player,
      playerActions: copyList(spec.characters.player_actions),
      npcName: spec.characters.npc_name,
      npcRole: spec.characters.npc_role,
      npcBehaviors: copyList(spec.characters.npc_behaviors),
      dialogueStates: copyList(spec.characters.dialogue_states),
      worldAreas: copyList(spec.characters.world_areas),
      primaryNpcs: spec.characters.primary_npcs,
      relationshipGrowth: spec.characters.relationship_growth,
      favorRules: spec.characters.favor_rules,
      relationshipEvents: spec.characters.relationship_events,
      requestRewards: spec.characters.request_rewards,
    },
    rules: {
      progression: copyList(spec.rules.progression),
      completion: spec.rules.completion,
    },
    scope: {
      included: copyList(spec.scope.included),
      later: copyList(spec.scope.later),
    },
    validation: copyList(spec.validation),
  }
}
