# Task 4 Report: Release-scoped Resource Batches

**Status:** DONE

## What changed

- Resource fixture candidates are now freshly generated from a real project session and release, with provenance derived from the project title plus release, playable, and GameSpec versions.
- Publishing a release creates its `resourceBatches[release.id]` entry. Batch creation filters out globally saved candidates and candidates ignored by earlier releases of the same project, so an empty batch is a valid outcome.
- Added store APIs for extracting a release batch and saving, ignoring, undoing, and editing saved resources. The 420ms save timer is keyed as `resource-save:${releaseId}:${candidateId}` in the project timer map, so it continues after the review screen unmounts.
- Resource Review now reads and mutates the session batch directly. It presents the required empty-batch copy without constructing a fallback candidate.
- App reads saved resources and pending counts from the store. My Resources now distinguishes an actually empty library from a no-match search/filter result.

## Verification

Command: `cd frontend && npm run build`

Result: passed (`vue-tsc -b` and Vite production build both exited 0).

## Notes

- Build output and `tsconfig.app.tsbuildinfo` are tracked generated artifacts and were left unstaged, as were all pre-existing unrelated dirty files.
