# ADR-0046: System Capture terminology

**Date:** 2026-10-05
**Status:** Accepted; owner explicitly requested this application-wide terminology change.
**Deciders:** Repository owner

## Context

The persona entry workflow was named Creation in navigation and Create persona in its entry
actions. The owner requested System Capture in the left sidebar and corresponding terminology
throughout the app.

## Decision

Name the page System Capture in sidebar labels/tooltips, Quick Actions, page/form/region headings
and the workspace guide. Use Start System Capture for entry actions, Save System Capture for
initial submission and Start another System Capture after completion. Completion and retained
draft messages use the same term. Align accessibility labels and legacy UI test fixtures.

This is product terminology for the existing persona record workflow. It does not imply an
automated capture, completed photo inspection or verified identity. Preserve the persona API,
DTOs, database identities, draft keys, retry semantics and internal module/style identifiers.
Historical ADRs and dated evidence retain their original wording; current planning/as-built
documents record the new name.

## Consequences

Users find the same term at every entry point and through save completion. Existing navigation,
focus, draft recovery, authorization and exact-version behavior remain covered by the same tests,
with their accessible-label expectations updated. No migration, dependency or runtime change
is required.
