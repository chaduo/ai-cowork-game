# Game Agent Contract Design

## Goal

Freeze the provider-neutral boundary consumed by BuildService so OpenGame, Claude SDK, piagent, and the
deterministic fake runtime can be swapped without changing Project lifecycle code.

## Scope

This change defines typed request/result/event models, a small async `GameAgent` protocol, a deterministic
`FakeGameAgent`, and a reusable contract test suite. It does not execute a provider, persist runs, expose API
routes, or advance Human Gates.

## Contract

`GameBuildRequest` contains `project_id`, `build_id`, `operation`, the validated `CreatorGameSpec`, its
`RuntimeBuildSpec` mapping, an approved workspace reference, an optional baseline playable reference, and the
user request text. `operation` remains a string so an adapter can return the standard `unsupported` result
instead of failing request parsing for a provider capability it does not implement.

`GameBuildResult` is terminal and contains one of `succeeded`, `failed`, `cancelled`, `timed_out`,
`invalid_output`, or `unsupported`, plus an artifact manifest, optional preview entry, sanitized diagnostics,
provider-neutral metadata, and a structured error when applicable.

`RunEvent` contains `run_id`, monotonically increasing `sequence`, `stage`, `kind`, a user-safe message,
optional progress in `[0, 1]`, an optional artifact reference, an optional structured error, and a UTC
timestamp. Event kinds are extensible strings, but `promoted`, `published`, and `resource_saved` (including
their gate-equivalent forms) are rejected so a provider cannot express a platform decision.

The `GameAgent` protocol uses an opaque `AgentRunHandle` and exposes `start`, `stream_events`, `result`, and
`cancel`. It has no Project repository, Human Gate, provider log, CLI command, or provider SDK type.

## Fake runtime

`FakeGameAgent` produces deterministic progress events and a minimal valid artifact result for supported
operations (`create`, `modify`, `repair`, `test`). It can be configured for one terminal outcome to exercise
failure, timeout, invalid output, unsupported operation, and cancellation paths. It stores state only in
memory and never mutates a Project or Release.

## Testing

The shared suite accepts an agent factory and verifies success, event ordering, cancellation, unsupported
operations, invalid output, timeout, and the prohibition on lifecycle gate events. C06 runs it against the fake
runtime; C10 will reuse the same suite for OpenGameAdapter, and later adapters can opt in without changing the
assertions.

## Non-goals and migration

No frontend type mirror is added in C06 because no API endpoint consumes these contracts yet. C11 will map the
contract into BuildService and C07 will persist/replay `RunEvent`. C09/C10 will own process and provider
mapping details. Claude SDK and piagent integrations must implement this boundary rather than expanding it with
provider-native fields.
