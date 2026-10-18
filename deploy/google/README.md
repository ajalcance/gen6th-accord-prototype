# Google source-preparation contracts

These are review records, **not launchable Cloud Run manifests**. They reference existing
owner-provisioned resources. No creation/import/deployment command is authorized by this folder.

## SQL proxy contract — ADR-0063

`sql-proxy-contract.json` records the approved sidecar topology, explicit private instance,
loopback SQL listener, workload identities, connection bounds and service probes. Its image
reference is deliberately null while signed digest/release integration is pending. Never replace
that state with a moving tag, claim it is verified, or bypass the reviewed release workflow.

SQL listens on 127.0.0.1:5432. HTTP health listens on the container interface at 9090 for native
service probes, and is never the Cloud Run ingress container/port. No SQL or health port is
published independently. The app depends on a successful proxy `/startup` probe; `/liveness`
checks the process. Neither proves the application's SQL login, grants or RLS. `/readiness`
also checks connection availability; it is not a liveness probe for a saturated small pool.

Use the same selected workload service identity for application and proxy containers in each
runtime, with existing instance-scoped Cloud SQL Client access. Do not set credentials-file,
JSON credentials, user gcloud authentication or token flags. Private routing is still required.
Proxy metadata access and app Google metadata access do not require downloaded account keys.

The signal contract accepts new connections for two seconds and drains for at most eight
seconds after TERM. Runtime termination/order and transaction rollback must be rehearsed in
the final container topology. The migration job needs a bounded startup wait, NullPool, its
separate operator credential, and a finally-path that stops the proxy through its loopback
admin endpoint after success or failure. `accord.db.migration_job` now implements the bounded
wait, allowlisted Alembic upgrade and finally shutdown request; no shell command is accepted.
It requires the separate `accord_migrator` login and `appdb` over the validated proxy transport.
The shutdown acknowledgment does not prove container exit; live job completion is still pending.
Review [grant sequencing](../../docs/runbooks/google-migration-grant-sequencing.md) before any launch.
ADR-0067 now prepares independent compliance lifecycle source; native probe/TERM acceptance remains pending.

Flags/probe semantics were checked against the
[Google proxy CLI reference](https://github.com/GoogleCloudPlatform/cloud-sql-proxy/blob/main/docs/cmd/cloud-sql-proxy.md)
and [official health example](https://github.com/GoogleCloudPlatform/cloud-sql-proxy/blob/main/examples/k8s-health-check/proxy_with_http_health_check.yaml).
Recheck the selected immutable version during image review; none was installed or run here.

Remaining contracts: signed scanner image/definition updates/resources, native worker acceptance,
same-origin authenticated ingress, migration/grants/rollback, and digest-preserving import.
Keep Tasks paused and Zynth setup later. Source acceptance is distinct from live acceptance.

## Scanner contract

`scanner-contract.json` records fixed loopback 3310 and the callable/CLI readiness probe in the
application image: `python -m accord.personas.scanner_probe` (no arguments). It requires exact
PONG and a fresh VERSION receipt within five seconds; it sends no pixels or filenames.
The existing stream adapter now bounds close waits and closes immediately on cancellation.
Non-development inspected ASGI startup now calls it before serving (ADR-0065); native scanner
startup signaling remains pending: Cloud Run has no native exec probe. An open TCP port
does not prove definition freshness; PING/VERSION does not prove clean inspection or liveness.

The image, UID, daemon limits, FreshClam/update policy, writable definitions, idle CPU/egress,
resources and live signal/reload behavior need final review. Prevent daemon limit-exceeded scans
from appearing clean; verify selected-version configuration rather than reducing protections.
Mount no private originals, DB credentials or application secrets into the scanner. Containers
sharing a runtime are not independent IAM boundaries; the runtime identity remains least-privilege.

Official [Docker requirements](https://docs.clamav.net/manual/Installing/Docker.html) describe
generic 3 GiB minimum/4 GiB preferred memory, not measured Accord allocations. The
[scanning guide](https://docs.clamav.net/manual/Usage/Scanning.html) describes unauthenticated
TCP and signature requirements. Keep the listener private and existing at-use freshness checks.
See [preparation evidence](../../docs/hackathon/scanner-preparation-proposal-2026-10-11.md) and the
[October 12 packaging review](../../docs/hackathon/scanner-packaging-review-2026-10-12.md) and
[candidate/runtime review](../../docs/hackathon/scanner-runtime-review-2026-10-12.md). Registry identifiers
do not prove image provenance. ADR-0069 [managed runtime](../../docs/runbooks/google-scanner-managed-runtime.md)
prepares real seed/config validation and fixed process launch; actual image/native acceptance pending.
The upstream bootstrap/load-testing and child supervision paths need review; a scanner image is
absent from the existing signed release workflow. Any workflow addition is a separate owner-approved
guardrail PR. Accepted JSON artifacts remain historical and unchanged.

ADR-0068 [scanner-health-contract.json](scanner-health-contract.json) supplements the snapshot:
required-runtime `accord.scanner.app.create_scanner_app(runtime)` prepares health and child lifecycle
without executable selection, launch, Settings or automatic image wiring. 33 synthetic tests pass;
checkpoint-14 source phases verified, current hashes match, pasted exit omitted. The
[adapter inventory](../../docs/runbooks/google-scanner-health-adapter.md) remains distinct from
real definition validation, process/native acceptance and signed packaging.

## Composition inventory

[`reference-contract.json`](reference-contract.json), ADR-0066, supersedes the reference factory
inventory for current source: `accord.reference:app` prepares independent authenticated task routes,
without browser/Redis/scanner/signing/investigation assembly. Checkpoint-12 source phases are verified from log; current hashes match, pasted exit
omitted. Reference reconcile IAM,
SQL/base-secret binding and live/private routing remain pending. See
[reference inventory](../../docs/runbooks/google-reference-runtime.md) and
[owner checkpoint](../../docs/hackathon/reference-checkpoint-2026-10-12.md).

[`composition-contract.json`](composition-contract.json) records current entry points, dependency
coupling, candidate limits and unresolved bindings. See the
[runtime inventory and acceptance matrix](../../docs/runbooks/google-container-composition.md).
It is not a launchable manifest and retains the checkpoint-11 snapshot: reference then shared the
API factory. Reference assembly is narrowed above. ADR-0067 now prepares
[`compliance-contract.json`](compliance-contract.json) with independent progress health and bounded
cleanup; checkpoint-13 source phases are verified; native
[lifecycle acceptance](../../docs/runbooks/google-compliance-lifecycle.md) remains pending. See the [owner checkpoint](../../docs/hackathon/compliance-checkpoint-2026-10-12.md).
Existing worker guards and the historical composition snapshot stay unchanged. Checkpoint 11 phases are verified from the log; current hashes match, pasted numeric exit
omitted. Final packaging/resources/routing and live acceptance remain pending.
Proposed ADR-0070 [artifact/release design](../../docs/hackathon/scanner-artifact-design-2026-10-12.md)
names real inputs/layer checks and separate signed scanner assembly integration; [source preparation](../../docs/hackathon/scanner-packaging-inputs-2026-10-12.md) now adds real factory/config emitter and [proposed context](scanner/README.md). Listener review/native locks remain open; nothing is built.
