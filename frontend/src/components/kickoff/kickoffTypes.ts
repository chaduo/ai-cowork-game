export type KickoffPhase =
  | 'clarifying'
  | 'thinking'
  | 'ready'
  | 'iterating'
  | 'iterating-question'
  | 'confirming'
  | 'confirmed'
  | 'error'

export type Choice = {
  id: string
  number?: string
  title: string
  description: string
  impact?: string
  recommended?: boolean
  loopLabel?: string
}

export type Question = {
  id: string
  response: string
  prompt: string
  choices: Choice[]
}

export type Decision = {
  questionId: string
  question: string
  response: string
  answerId: string
  answer: string
}

export type ReadySummary = {
  title: string
  summary: string
  highlights: string[]
  coreLoop: string[]
  progression?: string[]
}

export type KickoffScenario = {
  id: string
  title: string
  understanding: string
  coreQuestion: Question
  followUps: Record<string, Question>
  genericFollowUp: Question
  buildSummary: (idea: string, decisions: Decision[]) => ReadySummary
}

export type ConfirmedGameDesign = {
  originalIdea: string
  projectTitle: string
  scenarioId: string
  summary: ReadySummary
  decisions: Decision[]
}
