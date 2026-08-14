# C05 Contract Conformance Design

**Scope:** GDD revisions/readiness and independent GameSpec confirmation only.

The C05 implementation keeps the existing Project-level `GameDesign` aggregate and adds immutable `GameDesignRevision` history. Every save creates a draft revision; confirmed content is never edited. Clarification answers, unresolved decisions and readiness blockers are stored with the revision. Confirm GDD is a FastAPI-owned gate that accepts only the current valid revision with readiness `ready`.

`GameSpecRevision` gains a relational source pointer to the confirmed GDD revision. The GameSpec payload remains provider-neutral; no provider command, workspace path, resource id or UI workflow state is added. Existing `/design` and `/gamespec` routes keep their current response fields and add revision/readiness metadata for compatibility.

The implementation order is migration/model → contract models → service invariants → API responses/errors → regression tests. Build, OpenGame, Candidate verification, Resource Review and frontend state migration are explicitly excluded.
