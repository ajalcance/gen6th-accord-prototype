# Compliance worker lifecycle preparation

Date: October 12, 2026. Status: owner approved; source prepared; checkpoint-13 phases verified from saved log, pasted exit omitted.
Follows [reference checkpoint 12](reference-checkpoint-2026-10-12.md).

## Problem and intended result

`python -m accord.command.worker` continuously polls, but provides neither native HTTP health
nor graceful shutdown coordination. A healthy SQL proxy does not prove worker progress. The
existing loop catches pass failures and retries; it does not coordinate cancellation with TERM.

Prepare a separate worker-pool entry point/lifecycle adapter using existing `run_once` processing.
Expose only bounded process/progress health for native startup/liveness, without application data,
secret values or public product routes. Configure no actual platform resources in this unit.

## Proposed source scope

- Trace existing SQL sessions/engine disposal, Redis singleton lifetime, ingestion/sealing/detection/
  retention transactions and cancellation. Preserve operation order and existing outage behavior:
  Redis loss pauses ingestion while already-durable SQL events can still seal/evaluate/expire.
- Add typed lifecycle/supervision and a health-only factory/entry point. Validate the intended
  production worker configuration, confined compliance SQL profile and reviewed Redis TLS/CA.
  Reuse existing role protections; no browser, scanner, model, signing or Tasks capability.
- Health must distinguish started/progressing, failed/stalled and stopping. Successful empty passes
  count as progress; swallowed Redis ingestion failure must not become a claim of healthy Redis or
  complete audit delivery. Use bounded monotonic progress measurements, not a permanently true flag.
- Bound startup and pass/shutdown coordination. TERM stops new passes, then completes or cancels
  in-flight work with session rollback/engine disposal and Redis close within the platform window.
  Cancellation is not a successful pass. Do not modify existing retention predicates or audit rules.
- Use new adapters/modules around existing processing. Existing worker/consumer/audit/detection/
  retention, SQL guards and TLS validation implementations stay unchanged. If tracing requires an
  existing guard edit, stop for its own explicit owner-approved guard PR under
  [AGENTS.md](../../AGENTS.md); do not bundle it into lifecycle work.
- Test blocked/failed startup, progress health, empty passes, stalled/cancelled work, recovery and
  cleanup with synthetic clocks/providers. Disposable SQL/Redis tests must exercise cancellation
  rollback and preserve existing retention/audit/detection behavior. Freeze new source/contracts,
  update docs/ADR and run the owner/CI full gate.

## Acceptance and boundaries

Exit: independently prepared continuous worker lifecycle with truthful native health semantics,
bounded shutdown/failure tests and full-gate evidence. A healthy process is not proof of Redis
delivery completeness, production retention acceptance or backup/recovery.

No dependency/image install/build/sign/import, launchable manifest, production tests, credential/
IAM mutation, worker-pool creation, migration/grant, resize or queue resumption. Final private health
port exposure, SQL/base-secret/Redis mounts, regional platform support, native TERM/proxy drain,
resource measurements and signed-release/default-branch CI remain owner checkpoints.
One production environment; minimum workable measured sizing; Tasks paused; Zynth later.
