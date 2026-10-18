# Reference-only runtime preparation

Date: October 12, 2026. Status: owner approved; source implemented; checkpoint-12 phases verified, numeric exit omitted. No deployment authorization.
Follows [composition checkpoint 11](composition-checkpoint-2026-10-12.md).

## Problem and intended result

Reference task routes currently share `accord.main:app`, whose factory assembles browser auth,
Redis, inspection and optional signing/investigation. The reference SQL profile is distinct, but
assembly is not. Zynth is deferred; executing a verified task should not require browser secrets.

Prepare a separate ASGI entry point exposing process health and existing authenticated internal
task execute/reconcile routes only. Assemble wrapping KMS and face/job providers independently.
Preserve existing task identity, job reauthorization, replay, transactions and SQL-role checks.

## Proposed source scope

- Trace execute/reconcile dependencies, including task dispatch and telemetry authority; inventory
  needed IAM without changing grants. Do not assume execute and reconcile have identical needs.
- Add explicit reference configuration/assembly and entry-point modules. Validate Cloud Run Linux,
  service presence, workspace binding and existing typed Google configuration. No identity
  impersonation, credential discovery or enabling browser/photo flags to satisfy API assembly.
- Keep API `runtime_bootstrap.read_config`, Zynth factory and existing auth/role/retention guards
  unchanged. The separate reference boundary is a new security decision requiring owner review.
- Reuse existing role verification before serving. Exclude browser, original-inspection, signing,
  investigation and Redis providers unless tracing proves a real dependency. If it does, revise
  the proposed authority before implementation rather than copying the API profile.
- Test missing/mismatched configuration, role failure, absent API/browser routes, OIDC denial and
  existing job/replay behavior with synthetic providers/disposable PostgreSQL. Health contains no
  resource identifiers. Freeze source and run the owner/CI full gate.
- Update inventory/docs and add an ADR. Preserve accepted SQL/scanner/composition artifact bytes
  as historical evidence; bind reference preparation separately.

No existing guard implementation, frozen migration, gate script, agent policy or release workflow
edit is proposed. If one becomes necessary, stop for its own owner-approved guard PR under
[AGENTS.md](../../AGENTS.md), rather than bundling it into this unit.

## Acceptance and exclusions

Exit: independently assembled reference process with the existing authenticated task boundary,
source-bound failure/route/job tests and full-gate evidence. This is source preparation only.

No cloud mutation/grant, credential activation, image install/build/sign/import, launchable manifest,
migration, production test, queue resumption or sign-in activation. Compliance/scanner packaging,
resource measurements, private invoker and same-origin routing remain separate checkpoints.
One production environment; Tasks paused; Zynth later.
