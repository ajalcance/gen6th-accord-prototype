# ADR-0043: Creation completion screen

**Date:** 2026-10-04
**Status:** Accepted; owner requested the creation success-flow correction.
**Deciders:** Repository owner

## Context

After Save persona returned a validated receipt, the creation form remained visible and the
record IDs were appended below it. At the submit position a user could miss the receipt or
interpret the disabled form as an incomplete save. The owner called this the wrong behavior.

## Decision

Replace the editor after a validated successful initial save with a focused Persona saved
completion screen. Present the actual saved name/version/time, collapse storage IDs beneath
Inspect storage receipt, and expose Open saved record, Return to records and Create another
persona. Opening the record performs a fresh authorized version read under the same verified
workspace/session; the creation receipt does not become a cached read or a grant.

Keep uncertain, rejected or malformed outcomes in the original editor and preserve exact
retry semantics. An earlier confirmed save may leave only an authored completion marker in
session-scoped memory. Reopening Creation then shows Persona already saved with Records/new
creation actions, without recreating a receipt or permitting another submission. Retain authored
input for explicit read-only inspection; later edits after an uncertain request stay available
and do not become part of the validated receipt. Starting another persona explicitly clears
that creation draft and uses a new request ID/confirmation.

## Consequences

The success heading receives focus so the browser brings the completion into view. Storage IDs
remain inspectable without dominating the next action. Backend contracts, identity, records and
permissions do not change. Source-context changes hide the previous receipt, navigation target
and retained draft. Tests cover replacement/focus, collapsed identifiers, fresh read navigation,
completion-marker duplicate prevention, explicit restart and retained later edits. Rendered
scroll/zoom acceptance remains owner/manual evidence.

## Alternatives considered

Appending a receipt leaves the outcome below the submitted form. Automatically returning to
the gallery discards immediate confirmation. Reusing the creation response as a loaded record
would bypass a fresh authorization/read. Persisting a fetched receipt to restore confirmation
would violate the existing authored-draft-only memory boundary.
