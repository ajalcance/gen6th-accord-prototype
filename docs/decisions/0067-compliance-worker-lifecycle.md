# ADR-0067: Compliance worker lifecycle and progress health

Date: 2026-10-12
Status: Accepted for owner-approved source preparation; native activation pending.

## Context

The owner approved [compliance lifecycle preparation](../hackathon/compliance-lifecycle-proposal-2026-10-12.md).
The existing continuous worker has no native health endpoint or TERM coordination. A healthy proxy
does not prove progress. Worker passes independently commit ingestion, audit sealing, detection
and retention, so cancellation cannot imply full-pass atomic rollback.

## Decision

Prepare `accord.compliance:app`, a health-only ASGI worker-pool entry point. Its independent validator
requires production, Linux/CLOUD_RUN_WORKER_POOL, confined accord_compliance in appdb over reviewed
proxy transport, existing verified Redis TLS/CA and a finite polling interval of 1–10 seconds.
API/photos/Google product activation flags remain false. No browser, scanner, model or Tasks adapter.

Reuse the unchanged effective SQL-role predicate before starting and dispose its idle startup pool.
Require a first successful bounded pass before ASGI serving. Supervise unchanged `worker.run_once`
with a 30-second cooperative cancellation deadline, then poll serially. Existing run_once closes
its SQL session and disposes its per-pass engine. It retains all processing/outage predicates.

Progress health is 200 only after a completed pass while the runner is live, no failure is pending
and the monotonic success age is within pass deadline + poll + 5 seconds. Starting, failed, stalled
and stopping states return 503. Empty passes count as progress; swallowed Redis ingestion failure
allows durable SQL processing by existing design and is not a Redis or delivery-health assertion.
No actor, resource identifiers, private failure values, event counts or database contents are exposed.

On lifespan shutdown, mark stopping before cancelling the runner, wait at most four seconds for
its completion and close the process-owned Redis client with a two-second cooperative deadline.
Noncooperative cancellation times out as failure, never a shutdown acknowledgment. Late completed
passes while stopping/expired do not refresh health. The selected command proposes one-second
HTTP graceful shutdown, leaving seven seconds nominally within Cloud Run's ten-second window.
Native signal/proxy ordering still requires rehearsal; source tests do not prove actual termination.

Startup is bounded to 45 seconds, including a ten-second role check and first pass. Cleanup failure
fails closed. Existing stage commits remain durable; only the active uncommitted transaction rolls
back on cancellation. Preserve cursor/event idempotency and audit/detection/retention behavior.
No new product action, retention rule, audit guard, SQL guard or TLS implementation is introduced.

## Validation and consequences

31 synthetic lifecycle/health/config/deadline tests pass, including suppressed cancellation and
stalled recovery. Two disposable confined-SQL/in-memory-Redis tests cover active rollback with
earlier ingestion retained and health during Redis outage with existing audit/detection/retention.
Owner full gate 13 is pending. Real Redis TLS, native health/TERM, resource peaks and rollback
under platform drain remain unaccepted. No production test or cloud mutation occurs.

The [worker inventory](../runbooks/google-compliance-lifecycle.md) and separate contract supersede
only the historical composition snapshot's compliance lifecycle gap. Images, allocations, mounts,
private health routing and credentials remain unset. One production environment; Tasks paused;
Zynth later; reviewed CI, signed releases and owner Cloud Shell checkpoints remain required.
