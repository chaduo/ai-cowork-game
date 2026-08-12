# Publish / Release Prototype Design

## Scope

Incrementally extend the existing AI Cowork Game Workspace with a deterministic
Publish / Release prototype. Publishing freezes an explicitly identified Stable
Playable into an immutable Release. It is not deployment, community publishing,
or a lifecycle stage.

## Product Contract

- Publish is available when a Stable Playable has passed validation.
- The user decides whether the work is ready to publish; the system only checks
  eligibility.
- A Release has its own monotonically increasing version and records its source
  Playable, GameSpec, and Game Design versions.
- Publishing never closes or locks the project.
- Later Playable versions never mutate an existing Release.
- Resource extraction is represented only by a post-publish entry point.

## Interaction

`Playable Stable -> Release Review -> Publishing -> Release Created -> Workspace
with Release -> Release Detail`

The Review modal is the single human gate. It shows the publish target, new
Release version, editable friendly name and description, validation evidence,
and the effect of publishing. A deterministic failure query can stop Release
creation without affecting the Playable and retry the same Release number.

## Visual Direction

Retain the frozen Verified Workshop design. The signature is a compact
"version imprint" that places the Stable Playable and immutable Release on one
quiet evidence line. Verified green communicates machine validation; the blue
workbench accent communicates the human publish action. No celebration effects,
deployment console, community controls, gradients, or large decorative cards.

## Prototype States

- `review`
- `publishing`
- `error`
- `success`
- `closed_with_release`
- `release_detail`

The divergence fixture uses `?screen=publish&diverged=1`: Playable v3 remains
Stable while Release v1 stays based on Playable v2, and the next action prepares
Release v2 based on Playable v3.

## Scope Guard

Mock data and local timers only. Do not add a backend, deployment, storage,
public/private visibility, community, analytics, hosting, resource extraction,
or a fifth lifecycle stage.
