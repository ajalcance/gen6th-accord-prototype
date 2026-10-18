# 0061. Production-first Google bootstrap

- **Status:** Accepted for deployment direction; implementation and live acceptance pending
- **Date:** 2026-10-11
- **Deciders:** Repository owner

## Context

The owner wants the prototype's first deployed environment to be production, with no separate
staging environment, because it has no users yet. The owner will create the Google project and
requests step-by-step setup guidance. Production sign-in will use Zynth. The current source has
Google runtime adapters but no Google deployment manifests or executed cloud acceptance.

## Decision

1. Prepare one production environment in the existing primary region, Singapore
   `asia-southeast1` (ADR-0017). Run initial acceptance there before inviting users.
2. Make the workspace entry accessible over HTTPS with Zynth sign-in and existing workspace
   authorization. Keep database, Redis and machine workers private. A public workspace entry
   does not enable public passport sharing or access to private evidence.
3. Preserve PR review, exact-commit CI, production-readiness checks and signed immutable images
   (ADRs 0010/0011). This decision does not waive a release hold, accept an unresolved failing
   check, change a guard or authorize the agent to approve its own work.
4. Provision and verify dependencies in ordered checkpoints. Enable capabilities only when
   their schema/grants, identity, scanner/key/provider and acceptance prerequisites are proved.
   Google runtime construction is not recognition acceptance; similarity still needs measured
   permitted-corpus calibration and resolved representation provenance (ADRs 0051/0052/0058).
5. Use the [production bootstrap runbook](../runbooks/google-production-bootstrap.md) as the
   setup and evidence register. Record unknown project/domain/budget/Zynth details as pending,
   not fabricated configuration. Secrets remain owner-local or in Secret Manager.

## Consequences

There is no staging promotion step: subsequent fixes pass review and deploy new verified image
digests to the same production environment. Disposable SQL tests still precede production schema
changes. Backups, restore rehearsal, previous-revision rollback and retained-key inventory are
required before storing meaningful data. Application rollback does not reverse a migration.

Resource sizing, final ingress/SQL transport/Redis CA wiring, scanner packaging, continuous-worker
execution and Google deployment automation require implementation review. This ADR accepts the
environment strategy, not unimplemented manifests or live readiness. Provisioning and paid
provider execution must use the owner's selected project and cost envelope.

## Alternatives considered

- Separate private staging: recommended in the earlier review; the owner explicitly chose one
  production environment for the initial prototype instead.
- Upload the dirty checkout and build on a host: conflicts with the signed-artifact release
  contract and cannot bind CI evidence to what runs.
- Enable all capabilities at launch: obscures unavailable dependencies and cannot establish
  measured recognition or current production permission.
