export const MAX_AUTOMATIC_REPAIR_ROUNDS = 3
export const MAX_REPAIR_REQUEST_LENGTH = 4000

export type CandidateVerificationAction =
  | 'verify'
  | 'repair'
  | 'human_review'
  | 'manual_retry'
  | 'wait'
  | 'stopped'

export type CandidateVerificationState = {
  testGateStatus?: string
  hasReport: boolean
  repairRound: number
  testRunning: boolean
  repairRunning: boolean
  hasTransportError: boolean
}

export type CandidateFailureReport = {
  repairRound: number
  summary: string
  diagnostics: Array<Record<string, unknown>>
  evidence: Array<{ kind: string; status: string; observed: string }>
}

export type CandidateVerificationRuntimeState = {
  candidateId: string
  testGateStatus?: string
  testReport: Omit<CandidateFailureReport, 'repairRound'> | null
  repairRound: number
  testRunning: boolean
  repairRunning: boolean
  testError: string | null
}

export type CandidateVerificationFlow = {
  getState: () => CandidateVerificationRuntimeState | null
  verify: () => Promise<boolean>
  repair: (request: string) => Promise<boolean>
}

export function nextCandidateVerificationAction(input: CandidateVerificationState): CandidateVerificationAction {
  if (input.testRunning || input.repairRunning) return 'wait'
  if (input.testGateStatus === 'ready') return 'human_review'
  if (input.hasTransportError && !input.hasReport) return 'manual_retry'
  if (!input.hasReport && (!input.testGateStatus || input.testGateStatus === 'untested')) return 'verify'
  if (input.hasReport && ['failed', 'invalid'].includes(input.testGateStatus ?? '')) {
    return input.repairRound < MAX_AUTOMATIC_REPAIR_ROUNDS ? 'repair' : 'stopped'
  }
  return 'wait'
}

function displayValue(value: unknown): string {
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value) ?? ''
  } catch {
    return String(value)
  }
}

function diagnosticLine(item: Record<string, unknown>): string {
  const code = typeof item.code === 'string' ? item.code : 'diagnostic'
  const message = typeof item.message === 'string' ? item.message : displayValue(item)
  return `${code}: ${message}`
}

export function buildCandidateRepairRequest(report: CandidateFailureReport): string {
  const evidence = report.evidence
    .filter((item) => item.status === 'failed' || item.status === 'missing')
    .map((item) => `${item.kind}: ${item.observed}`)
  const lines = [
    `Repair round ${report.repairRound + 1} of ${MAX_AUTOMATIC_REPAIR_ROUNDS}.`,
    'Repair the existing game according to this platform-owned verification report.',
    `Summary: ${report.summary}`,
    ...evidence.map((item) => `Evidence: ${item}`),
    ...report.diagnostics.map((item) => `Diagnostic: ${diagnosticLine(item)}`),
    'Keep the confirmed GameSpec and unaffected behavior unchanged. Produce a complete index.html Candidate.',
  ]
  return lines.join('\n').slice(0, MAX_REPAIR_REQUEST_LENGTH)
}

export async function runCandidateVerificationFlow(flow: CandidateVerificationFlow): Promise<void> {
  while (true) {
    const state = flow.getState()
    if (!state) return
    const action = nextCandidateVerificationAction({
      testGateStatus: state.testGateStatus,
      hasReport: Boolean(state.testReport),
      repairRound: state.repairRound,
      testRunning: state.testRunning,
      repairRunning: state.repairRunning,
      hasTransportError: Boolean(state.testError),
    })
    if (action === 'verify') {
      if (!await flow.verify()) return
      continue
    }
    if (action === 'repair' && state.testReport) {
      const request = buildCandidateRepairRequest({
        repairRound: state.repairRound,
        ...state.testReport,
      })
      if (!await flow.repair(request)) return
      continue
    }
    return
  }
}
