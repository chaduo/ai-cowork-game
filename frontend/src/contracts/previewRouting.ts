/**
 * Candidate artifacts are only playable during the review gate. Once a
 * candidate is promoted, its endpoint intentionally stops serving preview
 * content, so the workspace must switch to the immutable Playable URL.
 */
export function previewUrlForPhase(
  phase: string,
  candidatePreviewUrl: string | null | undefined,
  playablePreviewUrl: string | null | undefined,
): string | null {
  if (phase === 'candidate_ready' && candidatePreviewUrl) return candidatePreviewUrl
  return playablePreviewUrl ?? null
}
