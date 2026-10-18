# ADR-0065: Production startup composition

Date: 2026-10-12
Status: Accepted for owner-approved source preparation; packaging/deployment pending.

## Context

The owner approved the [container composition proposal](../hackathon/container-composition-proposal-2026-10-12.md).
SQL role acceptance does not prove separately assembled workloads, scanner startup, continuous
worker lifecycle or working production ingress. Existing factories couple API/reference providers.

## Decision

Record actual dependencies in a non-deployable composition contract and
[runtime inventory](../runbooks/google-container-composition.md). Leave images, selected resource
allocations, native scanner readiness packaging and private routing unaccepted. Do not widen the
existing identity/role/retention guards or copy API authority into a reference runtime to launch it.

For non-development inspected application startup, require the reviewed fixed loopback 3310
configuration and existing bounded scanner probe after the SQL-role guard and before ASGI yield.
Keep existing development startup and all at-use scan checks. Place checks inside the lifecycle
cleanup boundary so failed startup/cancellation closes the assembled PersonaRuntime.
No readiness endpoint discloses scanner receipts, proxy internals or secrets.

The same main factory currently serves API and task routes. Independent reference assembly needs
separate review. The continuous compliance worker needs actual progress health and signal/rollback
packaging; a healthy proxy is not a healthy worker. Official Cloud Run worker-pool support exists,
but no deployment, availability or runtime acceptance is inferred from documentation.

Use measured minimum workable sizing. Candidate one-instance caps and scanner memory guidance are
rehearsal inputs, not accepted production capacity. Definition updates need idle CPU and reviewed
storage/egress; request-based sidecar CPU cannot promise continuous updates. Container mounts do
not establish independent workload IAM. Existing separate SQL profiles and migration runner remain.

## Validation and consequences

Synthetic tests exercise enabled/disabled inspection, fixed endpoint, success/failure and lifecycle
order/cleanup including cancellation. Owner/CI full-gate execution is pending new frozen source.
No live SQL, Redis, scanner or Google request is made by these tests. Missing Zynth configuration
still prevents activated API assembly; sign-in remains deferred. Product readiness is not claimed.

No image build/install, credential activation, cloud mutation or launchable manifest is authorized.
Existing migrations/guards/release pipelines remain intact. Reviewed CI and signed releases,
owner Cloud Shell checkpoints, private routing and live acceptance are required before deployment.
One production environment; Tasks paused; Zynth later.
