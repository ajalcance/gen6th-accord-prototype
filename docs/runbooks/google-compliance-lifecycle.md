# Compliance worker lifecycle preparation

October 12, 2026. [ADR-0067](../decisions/0067-compliance-worker-lifecycle.md).
Source prepared; checkpoint-13 source phases verified from saved log; pasted numeric exit omitted. No production/deployment authorization.

## Prepared process

`uvicorn accord.compliance:app --host 0.0.0.0 --port 8000 --workers 1 --lifespan on --timeout-graceful-shutdown 1 --no-access-log`

The image command must explicitly select this entry point; the existing Dockerfile still defaults
to API. It is a proposed worker-pool process, not a request-driven service or completion job.
Native worker-pool HTTP health support, always-allocated CPU and simultaneous TERM to all containers
are documented in the [Cloud Run runtime contract](https://docs.cloud.google.com/run/docs/container-contract)
and [worker health guide](https://docs.cloud.google.com/run/docs/configuring/workerpools/healthchecks),
checked October 12. Regional deployment/effective platform acceptance is not established here.

`command.compliance_config` validates production worker-pool/Linux presence, accord_compliance/appdb
and existing loopback SQL proxy and Redis TLS/CA validation. Polling must be finite, 1–10 seconds;
default is two. API/photos/Google activation flags remain false. No credentials are discovered.
SQL login and separate base Settings SECRET_KEY binding remain pending; Redis AUTH/CA version 1
access is recorded for compliance. Mount values/paths and effective IAM still need owner review.

`command.compliance_app` reuses existing SQL-role verification, disposes its idle startup pool and
awaits one successful `worker.run_once` before serving. Role deadline ten seconds; startup overall
45 seconds. The app owns the existing process Redis client and closes it after supervision stops.
Every actual pass retains the existing SQL-session/engine finally disposal.

## Health, failures and shutdown

`command.compliance_supervisor` serially calls unchanged run_once, with a 30-second cancellation
deadline and monotonic last-success age. Cancellation deadlines are cooperative; noncooperative
work cannot be made to exit by a Python timeout. It is not accepted as progress or clean shutdown.

| Health | HTTP | Meaning |
|---|---|---|
| starting | 503 | No successful pass yet |
| progressing | 200 | Completed pass within 30 + polling interval + 5 seconds; runner not finished |
| failed | 503 | Pass failure or terminated runner; next successful pass can recover |
| stalled | 503 | Last completed pass exceeds the monotonic progress window |
| stopping | 503 | Stop initiated; no new passes or progress acknowledgment |

Only status and `scope: worker_pass_progress` are exposed; no-store responses. No other routes,
schema/docs, data access or internal task execution. An empty pass is legitimate progress. A pass
can succeed during Redis outage while sealing/evaluating already-durable SQL events. HTTP 200
does not prove Redis, total ingestion, complete audit delivery, model accuracy or backup readiness.

Stopping marks unhealthy before cancelling the poll/pass task. Wait at most four seconds for task
completion, then close Redis with a two-second deadline. Even if cancellation times out, cleanup
is attempted and failure propagates. A selected one-second HTTP grace plus these six seconds
leaves nominal margin in Cloud Run's ten-second TERM window. Native signals, connection drain,
driver cleanup and multi-container races remain pending; no platform termination proof is claimed.

Ingestion commits before Redis cursor update; sealing commits separately; detection commits its
own transaction; retention commits separately. Cancellation rolls back the active transaction,
not earlier stages. Existing idempotency/source filters, detection support windows and seal-before-
delete rules remain unchanged. Do not describe a whole pass as atomic or claim all Redis entries
are durably delivered from a healthy process signal.

## Acceptance and remaining packaging

31 synthetic tests pass; exact mypy . (396 source files), Ruff/Black and changed-code Bandit pass.
Two new disposable migrated SQL tests using the real compliance grants and in-memory Fakeredis
pass: active cancellation rollback with committed ingestion/cursor retained, and factory health
during Redis outage preserving real audit/detection/retention. Checkpoint 13 verifies 1318 backend
tests/93.86%, Trust, 514 frontend, 31 docs-site, audits and builds. Current hashes match; pasted exit
omitted. See the [saved evidence](../hackathon/compliance-checkpoint-2026-10-12.md).
These are not live Redis TLS or production tests.

[`compliance-contract.json`](../../deploy/google/compliance-contract.json) has unset image/resources,
no launchable manifest and private health exposure pending. Proposed single-worker instance and
proxy-first native startup use the existing SQL contract; startup probe must allow the 45-second
application initialization after its proxy dependency. Suggested HTTP probe timings are rehearsal
inputs, not deployed configuration. Liveness must not interpret transient outage as unsafe purge.

Recorded compliance SQL/Redis authority is separate from activation, credential access and metrics.
Keep selected workload identity accord-compliance, no private originals/browser/model/scanner/Tasks
mounts. Preserve old SQL/scanner/reference/composition hashes as accepted historical source evidence.
Resource measurements, secret versions/mount paths, private VPC health port, native rollback/drain,
reviewed default-branch CI, signed images/import and owner Cloud Shell checkpoints remain required.
One production environment; minimum workable measured sizing; Tasks paused; Zynth later.
