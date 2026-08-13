# Task 5 Report: GameSpec Resource Matching and Reuse

**Status:** DONE

## What changed

- Added a structured resource matcher that reads only the explicitly mapped NPC relationship fields and recommends a resource only after at least two declared signals match.
- Saved relationship resources now carry machine-readable `matchSignals` and `reuseDefaults`; the store refreshes matches after GameSpec generation and when the saved library changes.
- Reuse dismiss/use decisions are persisted on the project session for the current GameSpec version. Ordinary revisions leave a dismissal intact.
- Applying a relationship resource freezes the original relationship fields once, applies only `reuseDefaults`, and marks the characters section updated. Cancel restores only that frozen relationship snapshot.
- Workspace recommendation and drawer state now derive from the project store rather than a demo-only resource prop. The recommendation, used state, and drawer fit copy no longer assume Lucy, farm content, or a coffee-shop project.

## Verification

Commands:

```sh
cd frontend && npx vue-tsc -b
cd frontend && npx vite build
```

Result: both commands passed.

## Notes

- The empty saved-resource library produces no recommendation. A saved relationship resource with two or more structured signal hits is matched to the characters section.
- Tracked build output, TypeScript build info, and pre-existing unrelated files remain unstaged.
