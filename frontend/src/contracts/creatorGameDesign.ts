export type CreatorGameDesignDraft = {
  schema_version: 1
  original_idea: string
  project_title: string
  scenario_id: string
  summary: {
    title: string
    summary: string
    highlights: string[]
    core_loop: string[]
    progression: string[]
  }
  decisions: Array<{
    question_id: string
    question: string
    response: string
    answer_id: string
    answer: string
  }>
  clarification: {
    question_index: number
    status: 'clarifying' | 'ready' | 'iterating' | 'confirmed'
    custom_input: string
    current_question?: {
      id: string
      prompt: string
      input_hint?: string
      choices: Array<{
        id: string
        title: string
        description: string
        recommended?: boolean
      }>
    } | null
  }
  readiness?: DesignReadiness
}

export type DesignReadiness = {
  status: 'not_ready' | 'ready' | 'blocked'
  blockers: string[]
  unresolved_decisions: string[]
  checked_at?: string | null
}
