export type CreatorGameSpec = {
  schema_version: 1
  title: string
  first_playable: {
    goal: string
    hypothesis: string
  }
  gameplay: {
    core_loop: string[]
    actions: string[]
  }
  characters: {
    player: string
    player_actions: string[]
    npc_name: string
    npc_role: string
    npc_behaviors: string[]
    dialogue_states: string[]
    world_areas: string[]
    primary_npcs: string
    relationship_growth: string
    favor_rules: string
    relationship_events: string
    request_rewards: string
  }
  rules: {
    progression: string[]
    completion: string
  }
  scope: {
    included: string[]
    later: string[]
  }
  validation: string[]
}

export type RuntimeBuildSpec = {
  project_title: string
  first_playable_goal: string
  first_playable_hypothesis: string
  core_loop: string[]
  actions: string[]
  characters: CreatorGameSpec['characters']
  rules: CreatorGameSpec['rules']
  included_scope: string[]
  validation: string[]
}
