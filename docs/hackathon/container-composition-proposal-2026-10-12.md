# Production container composition preparation — October 12

Status: **Owner approved source preparation; startup/inventory implemented; checkpoint 11 phases verified from log, numeric exit omitted. No deployment authorized.**
Follows [verified SQL role acceptance](sql-role-checkpoint-2026-10-12.md), ADRs 0061/0063/0064
and the existing SQL proxy/scanner contracts. One production environment; minimum workable MVP
sizing; Tasks remains paused; Zynth sign-in later. Existing foundations must not be recreated.

## Problem and intended result

SQL, Redis CA, migration runner, scanner probe and distinct SQL profiles pass the owner source
gate. They are not yet composed into reviewed runtime containers. Image references remain unset;
scanner startup wiring, private routing, secret mounts, continuous compliance execution, resource
allocations and native service/job lifecycle acceptance remain pending.

Prepare an explicit per-runtime composition inventory and non-deployable topology contract for
API, reference, compliance and migration processes, using current code entry points. Map which
runtime actually needs each sidecar, SQL role, secret version, mount, port and outbound connection.
Do not copy the API profile into a worker or assume all runtimes need a scanner. Database privilege
acceptance is separate from production credentials and authenticated network acceptance.

## Proposed implementation scope

- Trace actual process startup, existing health behavior, inspected-upload activation and worker
  entry points. Identify exactly where existing readiness checks must finish before serving work.
- Specify proxy dependencies and startup/shutdown sequencing per service/job/continuous worker.
  Reuse the reviewed bounded migration runner; retain distinct operator credentials and role limits.
- Design scanner readiness integration for the workloads requiring inspection, with fixed loopback,
  current definition checks and bounded fail-closed startup. Preserve all at-use scan protections.
  Record missing image/version, configuration and platform support as pending, not acceptance.
- Produce a non-deployable composition contract and acceptance matrix for resource minima/maxima,
  concurrency, mounts, identities, private routing and signals. Scanner sizing follows measured
  cold-start/definition/reload acceptance, rather than assuming a tiny sidecar is workable.
- Verify current platform constraints against official documentation before selecting startup probes,
  continuous-worker packaging or idle definition-update behavior. Unsupported compositions stay
  blocked for review; no synthetic success or temporary auth/health bypass.
- If a source startup adapter is appropriate, prepare typed code and synthetic startup/failure tests
  only after the inventory confirms the boundary. Document changes, freeze source/contracts and
  run the owner/CI full gate. No route exposes scanner/private proxy internals or secret values.

Existing auth/role/retention guards, frozen migrations, gate scripts, agent policy and release
workflow are outside this unit. A needed guard/release change requires its own owner-reviewed
proposal/PR. Same-origin public routing/invoker design remains a separate subsequent unit.

## Authorization and acceptance boundary

This proposal requests source preparation only. No install, image pull/build/sign/import, scanner
start, credential/login activation, IAM grant, cloud mutation, resource resize, migration, service
deployment, production tests or queue resumption. Final images need reviewed immutable supply-chain
evidence; launchable manifests and owner Cloud Shell checkpoints follow separately.

Exit: truthful code-bound topology inventory, reviewed startup boundary, bounded failure tests and
matching full-gate evidence. This establishes source preparation, not live Cloud Run/scanner/SQL/
Redis/KMS/provider acceptance. Full-commit CI and signed-release requirements remain intact.
