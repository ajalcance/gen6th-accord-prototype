# ADR-0066: Reference-only production runtime

Date: 2026-10-12
Status: Accepted for owner-approved source preparation; activation pending.

## Context

The owner approved [reference runtime preparation](../hackathon/reference-runtime-proposal-2026-10-12.md).
Shared API assembly required browser/Redis/inspection configuration even for stored reference tasks.
Separate SQL profiles did not resolve that dependency coupling. Zynth remains deferred.

## Decision

Add `accord.reference:app` using `reference_app` and `reference_bootstrap`. Mount only process health
and existing machine-authenticated execute/reconcile routes. Disable API docs/schema discovery.
Require explicit production Google activation, Linux/K_SERVICE, matching workspace and existing
typed Google configuration, reviewed proxy transport, appdb and accord_reference login. API/photo
activation flags must remain false for this entry point. Fail with a generic configuration error.

Reuse wrapping/retained KMS keys, face providers, Tasks dispatcher and task OIDC verification.
No browser, scanner, Redis, passport signing or investigation provider is constructed. Importing
shared helpers is not runtime capability activation. Constructors make no credential/network call.
The exact full Google configuration hash remains identical to the API job binding, including fields
unused by this worker. Removing them would cancel previously authorized work as configuration drift.

Await the unchanged SQL-role guard before ASGI serving. Existing job reauthorization, immutable
transitions, actor/workspace restrictions, retries/replay and bounded private errors remain intact.
Jobs write observation/face events directly in the SQL transaction; this path needs no Redis emitter.
No new product action is introduced. Scanner inspection happened earlier at the approved capture
boundary; reference uses encrypted analysis captures, not original portrait/evidence payloads.

Reconciliation requires Tasks creation plus use of the selected task-delivery identity. Inventory
records those grants for API only. Reference IAM remains pending owner review; no grants are added
here. API-only KMS signing authority and application/browser secrets must not be copied to workers.
Settings still requires SECRET_KEY outside development; its separate worker binding is unresolved.

## Validation and consequences

Synthetic config/factory/real signed OIDC tests plus existing job tests pass locally. A new disposable
SQL test runs the actual factory with the reference profile through reconciliation, completion and
exact replay. Owner full gate 12 is pending; no production connection/provider invocation occurs.
Configuration hash agreement does not prove model accuracy, native shutdown or private ingress.

Existing API bootstrap/identity/role/retention guards and migrations are unchanged. The accepted
composition artifact remains historical checkpoint-11 evidence; a new reference contract supersedes
its shared-factory dependency inventory for this prepared workload only. Source gate, reviewed CI,
signed images, owner credentials/IAM/private-routing checkpoints and live acceptance remain required.
One production environment; Tasks paused; Zynth later. Compliance/scanner packaging remains pending.
