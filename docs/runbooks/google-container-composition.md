# Production runtime composition preparation

October 12, 2026. Owner-approved source preparation only; deployment remains disabled.
See [ADR-0065](../decisions/0065-production-startup-composition.md) and
[`composition-contract.json`](../../deploy/google/composition-contract.json).
No launchable manifests, images, credentials or cloud mutations are included.

## Actual entry points and boundaries

| Workload | Current entry point | Required dependencies | Composition gap |
|---|---|---|---|
| API | `uvicorn accord.main:app`, container port 8000 | SQL proxy; Redis AUTH + verified CA; scanner when photos enabled; Google/KMS when enabled | Inspected Google runtime also requires configured Zynth; sign-in is deferred, so full capability activation is pending |
| Reference delivery | Prepared `accord.reference:app`; existing task router in `job_http` | SQL proxy, wrapping KMS, Vision/Vertex; reconciliation also Tasks; no Redis/browser/scanner | ADR-0066 source factory prepared; gate-12 source phases verified; reconcile IAM, credentials and private routing pending |
| Compliance | Prepared `accord.compliance:app`; unchanged `command.worker.run_once` | SQL proxy; Redis AUTH + verified CA; event/audit/detection tables | ADR-0067 progress health and bounded cleanup prepared; checkpoint-13 source phases verified; native TERM/rollback pending; Redis failure still permits durable-event processing |
| Migration | `python -m accord.db.migration_job --target <reviewed revision>` | SQL proxy; separate operator SQL credential; Alembic files | Reviewed runner awaits proxy and requests shutdown in finally; actual task/sidecar exit remains unproved |

API and reference now have separate prepared factories (ADR-0066); gate-12 source phases are verified from log; pasted numeric exit omitted.
The frozen composition JSON preserves checkpoint-11's historical shared-factory inventory.
See [reference preparation](google-reference-runtime.md) for current narrowed dependencies.
API `runtime_bootstrap.read_config` still requires Linux, K_SERVICE, API/photos activation and
matching workspace. `build_zynth_verifier` still requires tenant/workspace, client, confidential
client secret, session key, origin, SQL and Redis. Those guards remain unchanged. The separately
approved reference boundary is prepared in ADR-0066. Zynth later means no activated full API now;
an unconfigured process banner would not establish working product readiness.

## Startup, probes and shutdown

Proxy begins first. For services, use its reviewed native HTTP `/startup` on 9090 as a dependency;
port 5432 stays loopback. Scanner binds only 127.0.0.1:3310. A native TCP probe cannot reach that
loopback-only listener or establish definition freshness. Its packaging must first provide a
reviewed native startup signal; no unauthenticated scanner TCP listener is exposed to solve this.
Cloud Run has HTTP/TCP/gRPC probes, not the Docker HEALTHCHECK/exec semantics.

`main.lifespan` now runs the existing SQL-role guard, then `runtime_startup.prepare_inspection`,
before yielding to the ASGI server. Non-development photo activation requires configured port
3310 and the existing fixed five-second PING/VERSION probe. Development retains its prior local
port/startup behavior. Disabled inspection does not contact a scanner. A failed role check, failed
scanner receipt or cancellation closes the assembled PersonaRuntime. At-use inspection still
checks definition freshness before and after every verdict. No startup result proves clean pixels,
provider accuracy, continuous dependency availability or authenticated live access.

The unchanged `/health` response describes process health after real ASGI startup. Transport-only
ASGI tests do not automatically execute lifespan; synthetic lifecycle tests enter it explicitly.
Use native HTTP startup on port 8000 after the final sidecar ordering is accepted; never substitute
configured-capability `/runtime/readiness` for dependency acceptance.

Worker pools support dependency startup probes and continuously allocated CPU. ADR-0067 prepares
[compliance lifecycle](google-compliance-lifecycle.md): independent startup, progress-only HTTP
health and bounded cleanup. Checkpoint-13 source phases are verified; native TERM/rollback remains pending.
Migration jobs support container ordering; retain the runner's independent 60-second proxy wait,
one-second requests, NullPool and three-second shutdown request. No scanner or Redis is needed
for migrations. Settings still requires SECRET_KEY outside development even for worker/job;
their secret binding/access is unresolved, not permission to copy API secrets.

Cloud Run sends TERM to all instance containers with a ten-second termination window; shutdown
order is not promised by startup dependencies. Proxy drain is at most eight seconds, so application
transaction rollback and termination must be rehearsed together. No scanner/proxy shutdown or
worker signal handling has been exercised here.

## Identity, mounts, egress and sizing

Each intended workload uses its own existing service account and selected SQL profile. Runtime
roles remain NOLOGIN; credential provisioning/binding is a later owner checkpoint. Proxy uses
workload metadata and existing instance-scoped Cloud SQL Client authority, not key files.
Containers in one instance share workload identity authority; mounts do not isolate metadata IAM.

API mounts Redis CA version 1 read-only, with Redis AUTH version 1 referenced without values;
app/session secret metadata and public signing-key conversion are inventoried separately. The new reference factory
needs no Redis secrets; reconciliation authority and independent base-secret/SQL binding are pending. Compliance has recorded Redis
AUTH/CA access; migration needs neither. SQL runtime credentials do not yet exist in inventory.
Scanner receives no SQL/Redis/application secret mount or private-original volume. Its writable
definition directory, updater ownership, size and persistence are pending selected-image review.

Private egress must reach Cloud SQL through its proxy and Redis TLS 6378 over the existing VPC.
Google metadata, SQL Admin, KMS and workload-specific model/Tasks APIs need reviewed egress;
FreshClam needs separately reviewed signature-update egress. Reference delivery stays authenticated
and private; public frontend/API same-origin routing and invoker design are a subsequent unit.

Candidate rehearsal caps are in the contract, not measured allocations: one application process,
two simultaneous scans per adapter, service concurrency two API/one reference, maximum one instance
per workload initially, and one migration task/parallelism with no automatic retry. Reconcile
revision overlap and total SQL connections before rollout. Each runtime pool is two connections;
migration proxy is one. Do not count all four workloads as only two database connections.

Application/proxy candidates start at one vCPU and 512 MiB each; scanner candidate one vCPU/4 GiB
follows generic ClamAV guidance, not Accord acceptance. Selected resources remain null until cold
definitions, concurrent 10 MiB input, update/reload peak, memory volume usage and restart measurements.
An inspection service's FreshClam needs CPU between requests; request-based CPU cannot promise
idle updates. Instance-based billing is the candidate, with zero minimum instances and fresh
startup definitions on each cold start. Persistence/download strategy remains pending.

## Acceptance matrix

| Evidence | Status |
|---|---|
| Actual factories, role profiles, ports and secret metadata traced | Source inspected |
| Role → scanner → serve ordering; failure/cancellation cleanup | Synthetic tests and checkpoint 11 backend pass |
| Official service/job/worker-pool lifecycle and probe constraints | Documentation checked October 12 |
| Scanner native startup signal, immutable image/config, idle updater | Pending separate packaging review |
| Reference-only assembly with its own authority | ADR-0066 source/SQL acceptance passes; checkpoint-12 phases verified |
| Compliance progress health, TERM/rollback and resources | ADR-0067 source phases verified in checkpoint 13; native acceptance/resources pending |
| Full source gate and before/after fingerprints | All phases verified from log; current hashes match, pasted numeric exit omitted |
| Effective IAM, private ingress/egress, credentials, resource peaks | Live acceptance pending |
| Reviewed default-branch CI, signed image/import, owner migration/grants | Release/deployment pending |

Tasks stays paused; no production tests, migration, grant, service or job execution is authorized.

## Official documentation checked

- [Service container dependencies](https://docs.cloud.google.com/run/docs/configuring/services/containers): dependent sidecars need successful startup probes, not launch order alone.
- [Job container dependencies](https://docs.cloud.google.com/run/docs/configuring/jobs/containers) and [job health checks](https://docs.cloud.google.com/run/docs/configuring/jobs/healthchecks): preserve task completion semantics separately from service readiness.
- [Worker pool health checks](https://docs.cloud.google.com/run/docs/configuring/workerpools/healthchecks): native HTTP/TCP/gRPC startup and HTTP/gRPC liveness support require actual endpoints.
- [Container runtime contract](https://docs.cloud.google.com/run/docs/container-contract): ingress interface, continuous worker CPU, manual worker scaling and simultaneous TERM window.
- [CPU/memory constraints](https://docs.cloud.google.com/run/docs/configuring/services/cpu): one vCPU supports up to 4 GiB; allocation must be checked for final topology.
- [ClamAV Docker guidance](https://docs.clamav.net/manual/Installing/Docker.html): generic 3 GiB minimum/4 GiB preferred; definitions and update strategy need measurement.
