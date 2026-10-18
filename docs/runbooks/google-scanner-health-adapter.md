# Scanner health and supervision adapter

October 12, 2026. [ADR-0068](../decisions/0068-scanner-health-supervision-adapter.md).
Prepared source only. Checkpoint-14 phases verified from saved log; real scanner/platform acceptance pending.
See the [owner source checkpoint](../hackathon/scanner-adapter-checkpoint-2026-10-12.md).

`accord.scanner.app.create_scanner_app(runtime)` requires a server-owned typed ManagedRuntime.
No default application/runtime, executable selection, process creation or shell exists in this unit.
It uses existing backend dependencies; exact packaging into a scanner image remains pending.
It does not construct Settings, database/Redis, browser, KMS, model or Tasks providers.
Construction denies non-Linux and root execution. The runtime must initially have no children.

## Boundary and startup

The future image/runtime implementation must validate exact selected daemon/update configuration,
numeric UID/writable ownership and official bootstrap databases with load testing enabled in
`prepare()`. Then `start()` registers each child before yielding. Neither callback is implemented
by this unit; synthetic callbacks are not proof of real validation, provenance or safe launch.
No public API can supply them. Require exactly two live children named clamd and freshclam.

ASGI lifespan starts supervision and yields while health is starting/503. Native startup must
observe that denial until prepare/start and one successful fixed PING/VERSION receipt complete.
Startup source candidate is 120 seconds; attempts use a five-second cooperative deadline and
two-second retry. Candidate timings require cold-start measurement before platform selection.

The unchanged existing probe uses loopback 127.0.0.1:3310, exact PONG and receipt validation:
definition age at most 48 hours and future timestamp at most five minutes. It sends no pixels.
Existing scan input/concurrency/deadline and before/after receipt guards remain unchanged.

## Health and supervision

| State | HTTP | Evidence |
|---|---|---|
| starting | 503 | No completed successful startup receipt |
| ready | 200 | Recent fresh receipt, two live children and live supervisor |
| unavailable | 503 | Probe failed since last successful receipt; can recover |
| stalled | 503 | Last success older than ten monotonic seconds |
| failed | 503 | Child death, startup failure or terminated runner |
| stopping | 503 | Shutdown initiated; no later readiness acknowledgment |

Only GET /health exists, with fixed status/scope and no-store. No scanner command/configuration,
data, schema/docs or task routes. An unexpected child exit with code zero is still fatal.
Probe failure denies health and retries; child failure stops its peer and requires restart.
Healthy protocol/freshness is not clean inspection or proof of completed updates/delivery.
The native health port/private exposure and whole-container restart/exit behavior remain pending.

## Shutdown and limits

Lifespan stop marks unhealthy before cancellation, terminates all registered live children,
allows three seconds, kills remaining children and allows two seconds for reaping. Signal/reap
faults still attempt cleanup of every peer. Surviving/unreaped children fail cleanup; generic
errors contain no private subprocess output. Stop waits at most seven seconds for supervision.
Cleanup is shielded if stop arrives while a failure is already reaping children. Repeated stop
does not send a second cancellation into cleanup. Late probe success cannot refresh readiness.

The boundary assumes nonblocking child signal methods and cooperative async callbacks. Python
deadlines cannot forcibly terminate arbitrary callback code; stop timeout is failure, not success.
Real PID-1 signal forwarding, process creation races/registration, driver wait behavior, scans that
continue after client cancellation and final native TERM remain unaccepted until Linux rehearsal.

## Evidence and remaining work

Synthetic tests cover prepare-before-start, failed/blocked startup, partial child launch,
freshness denials through the existing probe, health/recovery/staleness, child death, stop races,
TERM/KILL escalation, unreaped-child denial and generic failure responses. Existing probe/provider
tests also pass. Checkpoint 14 verifies 1351 backend tests/93.94%, mypy 404 sources, Trust,
514 frontend tests, 31 docs-site tests, audits and builds. Current hashes match; pasted numeric
exit omitted. No scanner process was run.

The new [source contract](../../deploy/google/scanner-health-contract.json) supplements rather
than rewrites the eight historical artifacts. Image/version-specific config, native port, resources
and runtime implementation remain null in that historical snapshot; ADR-0069
[managed runtime](google-scanner-managed-runtime.md) supplies subsequent explicit source integration,
with real release-bound CVDs and no fixture fallback. Checkpoint 15 source phases verify 1414 backend/94.10% and all later phases; current hashes match, pasted exit omitted. Image/native evidence pending. The [packaging review](../hackathon/scanner-packaging-review-2026-10-12.md)
and [runtime matrix](google-scanner-acceptance-preparation.md) define later acceptance.
Exact image/source review, separate scanner release guardrail PR, signed artifact evidence and
isolated owner rehearsal precede cloud checkpoints. One production environment; minimum workable
measured sizing; Tasks paused; Zynth later. No resource recreation or production tests.
