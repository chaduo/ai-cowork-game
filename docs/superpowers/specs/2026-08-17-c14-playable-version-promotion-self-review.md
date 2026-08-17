# C14 Design Self-Review

## Requirement coverage

- Platform `PASSED` is read from the persisted `TestReport`, not a request
  verdict.
- Human Play Review is explicit and auditable.
- Amendment and semantic drift blockers are represented as review gate data;
  no hidden recalculation is introduced.
- Promote is transactional and idempotent through the existing unique
  candidate/version relationship.
- Playable and Release history is append-only.
- Restore creates a fresh candidate and cannot move the current pointer.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Old C02 helper calls bypass the new gate | Update contract tests to seed a real TestReport and accepted review. |
| A client submits fake artifact metadata | Promote snapshots path/checksum already stored on Candidate. |
| Restore accidentally becomes playable | New candidate starts `untested` with no review. |
| Cross-project version restore | Service verifies both version and project ownership. |
| Partial Promote transaction | Create version and update pointer in one session transaction; API commits only after service returns. |

## Deliberate limitations

C14 records Amendment/Drift gate status but does not implement detection or
draft authoring. Those remain future changes and can use the same persisted
statuses without changing the Promote contract.

## Review result

The design is the smallest implementation that satisfies C14 while preserving
C02/C11/C12 boundaries. No generic gate abstraction is warranted yet.
