from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FirstPlayableSpec(ContractModel):
    goal: str = Field(min_length=1)
    hypothesis: str = Field(min_length=1)


class GameplaySpec(ContractModel):
    core_loop: list[str] = Field(min_length=1)
    actions: list[str] = Field(min_length=1)


class CharactersSpec(ContractModel):
    player: str = Field(min_length=1)
    player_actions: list[str] = Field(min_length=1)
    npc_name: str = Field(min_length=1)
    npc_role: str = Field(min_length=1)
    npc_behaviors: list[str] = Field(min_length=1)
    dialogue_states: list[str] = Field(min_length=1)
    world_areas: list[str] = Field(min_length=1)
    primary_npcs: str = Field(min_length=1)
    relationship_growth: str = Field(min_length=1)
    favor_rules: str = Field(min_length=1)
    relationship_events: str = Field(min_length=1)
    request_rewards: str = Field(min_length=1)


class RulesSpec(ContractModel):
    progression: list[str] = Field(min_length=1)
    completion: str = Field(min_length=1)


class ScopeSpec(ContractModel):
    included: list[str] = Field(min_length=1)
    later: list[str] = Field(default_factory=list)


class RuntimeBuildSpec(ContractModel):
    project_title: str
    first_playable_goal: str
    first_playable_hypothesis: str
    core_loop: list[str]
    actions: list[str]
    characters: CharactersSpec
    rules: RulesSpec
    included_scope: list[str]
    validation: list[str]


class CreatorGameSpec(ContractModel):
    schema_version: Literal[1] = 1
    title: str = Field(min_length=1)
    first_playable: FirstPlayableSpec
    gameplay: GameplaySpec
    characters: CharactersSpec
    rules: RulesSpec
    scope: ScopeSpec
    validation: list[str] = Field(min_length=1)

    def to_runtime_build_spec(self) -> RuntimeBuildSpec:
        return RuntimeBuildSpec(
            project_title=self.title,
            first_playable_goal=self.first_playable.goal,
            first_playable_hypothesis=self.first_playable.hypothesis,
            core_loop=list(self.gameplay.core_loop),
            actions=list(self.gameplay.actions),
            characters=self.characters,
            rules=self.rules,
            included_scope=list(self.scope.included),
            validation=list(self.validation),
        )
