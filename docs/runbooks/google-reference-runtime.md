# Reference-only runtime preparation

October 12, 2026. [ADR-0066](../decisions/0066-reference-only-runtime.md).
Source only; checkpoint 12 phases verified from saved log, current hashes match; pasted exit omitted. No deployment or cloud mutation authorized.

## Runtime and configuration

Prepared entry point: `uvicorn accord.reference:app --host 0.0.0.0 --port 8000 --no-access-log`.
Container command review must select it explicitly; the existing backend Dockerfile still defaults
to the API entry point. No image/manifest/build is supplied by this unit.

`personas.reference_bootstrap` validates production, explicit PERSONA_GOOGLE_ENABLED, Linux and
K_SERVICE, matching workspace/full Google configuration and proxy transport with accord_reference
in appdb. PERSONA_API_ENABLED and PERSONA_PHOTOS_ENABLED remain false. This does not relax API
configuration guards. No local credentials, Zynth settings, Redis endpoint or scanner is needed.
The full Google configuration JSON is identical to API job configuration, retaining unused fields
for exact config_id agreement; those fields do not construct extra providers.

`personas.reference_app` mounts only `/health` and existing POST execute/reconcile task routes.
The real ASGI lifespan awaits existing SQL-role verification before serving. Lazy Google adapters
own no open persistent HTTP client; SQL request sessions retain existing shared bounded-pool behavior.
Health shows status/version only; no dependency/model/identity readiness or runtime internals.
HTTPX transport-only tests do not execute lifespan unless explicitly entered.

## Required authority and data

| Operation | Required access | Recorded production status |
|---|---|---|
| SQL role verification, stored-job authorization and transitions | Private proxy and confined accord_reference profile | IAM proxy access provisioned; SQL profile/credential activation pending |
| Analysis capture decode and encrypted generation storage | Wrapping KMS encrypt/decrypt, including retained key versions | Version-1 key-level grant recorded; actual key use/retention acceptance pending |
| Face detection and embedding | Vision/Vertex APIs via workload metadata | Provider access/usage acceptance pending |
| Durable observation and face events | INSERT events within existing SQL transactions | Disposable profile tests cover authority; no Redis dependency |
| Reconcile queued references | Tasks enqueuer on selected queue and permission to use task-delivery identity | Inventory grants API only; reference grants pending owner review |
| Verify delivery | Google signed OIDC/JWKS; exact issuer/audience/email/subject/time | Existing validator reused; native private invoker acceptance pending |

Execution does not dispatch a new task; reconciliation does. Both routes retain the same existing
machine identity validator. Failure to dispatch preserves queued intent. Do not resume the queue
or interpret a configured dispatcher as accepted IAM. Source approval adds no authority.

Reference mounts no Redis CA/AUTH, browser client/session, public signing key or original payloads.
It needs its own SQL credential binding and the base Settings SECRET_KEY binding; neither is
provisioned by this unit. Shared container workload IAM remains an instance-level boundary.
Google model calls process approved analysis pixels, not unauthorised corpus/identity evidence.

## Acceptance

- 21 new synthetic config/factory tests plus existing signed OIDC/job tests: 46 focused tests pass.
- Ruff/Black, changed-code Bandit and exact mypy . (389 source files) are checked before checkpoint.
- Disposable SQL factory/reconciliation/execution/replay test passes within all 1285 backend tests.
- Reference contract has no image, selected resource allocation, credentials or launchable manifest.
- Existing six accepted SQL/scanner/composition artifact hashes stay frozen as historical evidence.
- Private egress/ingress, effective IAM, SQL login, TERM/transaction rollback, native probes, measured
  resource sizing and signed-release/default-branch CI remain pending. No live acceptance claimed.

The [composition inventory](google-container-composition.md) and new
[`reference-contract.json`](../../deploy/google/reference-contract.json) describe current source.
The older composition JSON intentionally preserves checkpoint-11's shared-factory snapshot.
Checkpoint 12: 1285 backend tests, 93.81% coverage, Trust, 514 frontend, 31 docs-site tests and builds
verified from saved log; current source/seven artifact hashes match, pasted numeric exit omitted.
One production environment; paused Tasks; Zynth later; scanner/compliance preparation remains separate.
