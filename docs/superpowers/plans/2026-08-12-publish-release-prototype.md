# Publish / Release Prototype Implementation Plan

1. Add typed Release fixtures and local publish state.
2. Extend Preview with publish eligibility, explicit target actions, current
   Release provenance, and the resource extraction bridge.
3. Add Release Review modal states: review, publishing, error/retry, success.
4. Add Release Detail drawer with frozen provenance and playable preview action.
5. Integrate `?screen=publish`, deterministic failure, and divergence fixtures
   into the existing Workspace without changing its lifecycle.
6. Build and verify the main, retry, working-build eligibility, and divergence
   paths in a desktop browser.
