# Google production inventory and owner evidence — October 11

Current transition: [October 12 complete handoff](../hackathon/next-session-2026-10-12.md). Owner published draft
[PR #60](https://github.com/ajalcance/gen6th-accord/pull/60) at `116fa14d9d82a9e12dbae4a268db89086d549a4a`.
Linux guard fault tests fail before CLI execution with E2BIG (864 passed/1 failed/18 skipped);
owner review/label, green exact-head CI and release integration remain pending. Dependabot status
is unverified. Earlier candidate/setup statements below are historical; no cloud mutation occurred.

This is the canonical provisioning snapshot for [ADR-0061](../decisions/0061-production-first-google-bootstrap.md)
and the [G0–G8 bootstrap](google-production-bootstrap.md). Evidence is the owner's pasted Cloud
Shell output, inspected in chat on 2026-10-11; the agent did not query or mutate the cloud account.
Reverify before changing resources. Configuration evidence is not runtime or deployment acceptance.
No secret values, passwords, tokens, PEM contents or database URLs belong in this document.

## Owner choices and project

- One production environment, no separate staging; initial acceptance before inviting users.
- Use the minimum workable MVP sizing. Owner explicitly deferred a numerical monthly budget;
  do not repeatedly ask for one or treat an absent budget target as a setup blocker.
- Project `gen6th-accord-production`, number `<PROJECT_NUMBER>`, lifecycle `ACTIVE`.
- Billing linked and active: owner reported. Region: `asia-southeast1` (Singapore).
- Intended domain `accord.gen6th.com`; base domain `gen6th.com`. DNS/HTTPS not yet accepted.
- Zynth is the production sign-in provider; public URL/client/tenant/workspace setup is deferred.
- Cloud Run is the selected hosting direction. No VM, SSH server or staging resource is needed
  merely to continue this bootstrap. Provisioned SQL/Redis can incur charges while idle.

## APIs and network

Owner listed enabled Cloud Run, Artifact Registry, Compute, Service Networking, SQL Admin,
Memorystore Redis, Secret Manager, Cloud KMS, Cloud Tasks, IAM/credentials, Logging and Monitoring
APIs, among other existing APIs. Do not disable unrelated APIs. No provider/model probe is recorded.

| Resource | Owner output |
|---|---|
| VPC | `accord-prod-vpc`, custom subnet mode, regional BGP |
| Subnet | `accord-prod-sg`, Singapore, `10.20.0.0/24`, private Google access enabled |
| Private-services reservation | `accord-prod-services`, global VPC peering allocation, /16 |
| Peering | `servicenetworking-googleapis-com`, `ACTIVE` |

No broad SSH/RDP/internal firewall rule was created from the generic CLI suggestion. Cloud Run
private egress and verified SQL/Redis connections still need reviewed manifests and runtime proof.

## Service identities and registry

All seven named accounts were listed with `disabled: false`; emails use
`@gen6th-accord-production.iam.gserviceaccount.com`:
`accord-api`, `accord-frontend`, `accord-reference`, `accord-task-delivery`,
`accord-compliance`, `accord-migration`, `accord-deployer`.

Task delivery numeric subject: `103959856362075467064`. Retain this actual unique ID when preparing
the application's OIDC verifier; do not substitute the project number or email for the subject.
Account creation initially hit the per-minute quota after four accounts; remaining accounts were
created after waiting. Do not rerun the original seven-account creation loop.

Artifact Registry `accord-images` is DOCKER, STANDARD_REPOSITORY, Singapore, Google-managed
encryption. Repository-level `roles/artifactregistry.writer` was verified for `accord-deployer`.
Path: `asia-southeast1-docker.pkg.dev/gen6th-accord-production/accord-images`.
No CI federation, deploy automation or signed image import has been accepted yet.

Latest owner inventory: **0 Cloud Run services, 0 Cloud Run jobs, 0 container images** in the
selected region/repository. Worker pools were not queried. This proves an empty queried inventory,
not absence of every possible Google resource or a working deployment.

## Cloud SQL

| Setting | Owner output |
|---|---|
| Instance | `accord-prod-db`, `RUNNABLE` |
| Engine/tier | PostgreSQL 17, Enterprise, `db-f1-micro`, ZONAL |
| Zone | `asia-southeast1-c` |
| Connection name | `gen6th-accord-production:asia-southeast1:accord-prod-db` |
| Private address | `10.42.0.3`; public IPv4 disabled |
| TLS | `sslMode: ENCRYPTED_ONLY`; legacy `requireSsl: false` is not a plaintext override |
| Storage | 10 GiB SSD, auto-resize enabled, 20 GiB limit |
| Recovery | Daily backup at 18:00 UTC; seven backups and seven days PITR |
| Protection | Deletion protection enabled; activation ALWAYS |
| Logical database | `appdb`, UTF8, `en_US.UTF8`; default `postgres` also listed |

User inventory lists `postgres` and `accord_migrator`, both BUILT_IN. The owner creation command
requested `cloudsqlsuperuser` for `accord_migrator`; it is the administrative schema/role operator,
never the application's login. Listing users does not verify a successful login or actual SQL
attributes. No confined application SQL account, migration, runtime grant, schema revision, RLS
proof, connectivity test or restore rehearsal is recorded for production.

The following project-level `roles/cloudsql.client` binding was verified for `accord-api`,
`accord-reference`, `accord-compliance`, and `accord-migration`:

```text
title: accord-prod-db-only
expression: resource.name == 'projects/gen6th-accord-production/instances/accord-prod-db'
            && resource.service == 'sqladmin.googleapis.com'
```

This grant permits connection to the named instance through supported connectors/proxy; database
authentication, SQL privileges and private network routing remain separate requirements. Adding
the condition changed the project IAM policy to version 3; the CLI warning was expected.

The pasted project policy also contains existing Editor grants for the default Compute account
and Google APIs service account. Named Accord runtimes must use their own selected identities.
Audit inherited/default-account authority and existing dependencies before any removal; this
session neither removed those grants nor proved effective IAM across the resource hierarchy.

## Redis

`accord-prod-redis` is READY, BASIC, 1 GiB, Redis 7.2, on the same VPC with
PRIVATE_SERVICE_ACCESS. Address `10.42.65.11`, TLS port `6378`; AUTH enabled,
SERVER_AUTHENTICATION transit encryption, `maxmemory-policy: noeviction`.
No real client TLS/CA verification, retention/restart/restore or memory-capacity proof is recorded.
Noeviction prevents eviction on memory exhaustion; it does not establish durable audit delivery.
Both clients now have [source CA wiring](../hackathon/redis-ca-preparation-2026-10-11.md);
reviewed runtime mounts, reference-worker secret access and live verification remain pending.

## KMS keys and trust

Ring: `accord-prod-keys`, Singapore. Both actual version-1 resources were ENABLED, SOFTWARE:

| Key | Algorithm | Verified key-level role |
|---|---|---|
| `accord-data-wrap` | `GOOGLE_SYMMETRIC_ENCRYPTION` | `roles/cloudkms.cryptoKeyEncrypterDecrypter`: API and reference accounts |
| `accord-passport-sign` | `EC_SIGN_ED25519` | `roles/cloudkms.signer`: API account |

Actual versions (not yet pinned in a deployed application configuration):

```text
projects/gen6th-accord-production/locations/asia-southeast1/keyRings/accord-prod-keys/cryptoKeys/accord-data-wrap/cryptoKeyVersions/1
projects/gen6th-accord-production/locations/asia-southeast1/keyRings/accord-prod-keys/cryptoKeys/accord-passport-sign/cryptoKeyVersions/1
```

No wrap/unwrap, tamper, signing or rotation acceptance was performed. Keep version retention and
backup/key lifecycle explicit. Private signing keys were not exported.
The public-key secret below stores PEM. The runtime expects canonical base64 of a 32-byte raw
Ed25519 public key (44 characters), keyed by the full signing version ID. Conversion/trust binding
is pending; do not pass PEM directly as `trusted_signing_keys`.

## Secret Manager metadata and scoped access

All entries have **version 1 enabled**, with user-managed replication in Singapore. The owner
generated/captured values in memory and passed stdin to Secret Manager. Only metadata was pasted.

| Secret ID | Intended contents | Verified secret-level accessor |
|---|---|---|
| `accord-prod-redis-auth` | Redis AUTH | API, compliance |
| `accord-prod-redis-ca` | Redis service CA bundle | API, compliance |
| `accord-prod-passport-public-key` | Version-1 signing public PEM | API |
| `accord-prod-app-secret` | `SECRET_KEY`, generated 32-byte hex | API |
| `accord-prod-session-key` | `ZYNTH_SESSION_KEY`, independent 32-byte hex | API |
| `accord-prod-migration-password` | `accord_migrator` password | Migration |

These resource policies do not prove absence of inherited permissions. Runtime secret mounts,
version pins, worker-specific settings and application database credentials remain to be prepared.
Zynth client secret/configuration remains deferred; no downloaded service-account key is needed.

## Cloud Tasks

Queue: `projects/gen6th-accord-production/locations/asia-southeast1/queues/accord-reference-jobs`.
Owner created it and confirmed **PAUSED**. Preserve the pause; do not enqueue probes or resume it.

| Setting | Owner output |
|---|---|
| Dispatch | One concurrent dispatch, one dispatch/second; Google-calculated burst size 10 |
| Retry | Three attempts, min backoff 130s, max backoff 300s, max doublings 1 |
| Duration/logging | Requested max retry duration 0s (omitted default), sampling ratio 1 |

Verified IAM:
- Queue-level `roles/cloudtasks.enqueuer`: `accord-api`.
- On `accord-task-delivery`: `roles/iam.serviceAccountUser` for `accord-api`.
- Project `roles/cloudtasks.serviceAgent`:
  `service-<PROJECT_NUMBER>@gcp-sa-cloudtasks.iam.gserviceaccount.com`.

Worker URL/audience, worker-specific invocation grant, OIDC runtime config and reconciliation
are pending. `TaskConfig` requires the actual default HTTPS `run.app` origin and pinned delivery
subject. Existing task code sets a 120-second dispatch deadline per task. A configured queue is
not completed delivery or a strict spending cap; replay/lease/cost acceptance remains open.

## Latest owner test result — launch blocker

Follow-up: [SQL/job repair evidence](../hackathon/backend-test-repair-2026-10-11.md) records
full diagnostics, 32 owner focused passes and subsequent full-suite corrections. The result below
is historical; third repair full gate passed 1108 backend (93.12%), 514 frontend, 31 docs-site
tests, Trust/builds/audits/DoD. Fourth CA gate passed 1122 backend (93.26%) and all later phases;
DoD passed. Owner-approved SQL transport full gate passes: 1147 backend (93.40%), all later phases
and DoD; source/contract fingerprints match before/after. CI/release/live acceptance remain pending.
See [SQL preparation](../hackathon/sql-transport-proposal-2026-10-11.md).
No cloud inventory changed.
Later [approved migration runner](../hackathon/migration-job-preparation-proposal-2026-10-11.md)
passes its full gate: 1185 backend (93.45%), all later phases/DoD, matching fingerprints before/after;
no live migration or grants.
Later [approved scanner preparation](../hackathon/scanner-preparation-proposal-2026-10-11.md)
adds a loopback readiness probe/contract. First full gate: 1212 pass/1 collection-time fixture
failure; timing repaired. All full-check-8 phases verified October 12: 1217 backend (93.58%),
later phases/DoD pass; supplied post-run fingerprints match. Numeric exit line omitted.
No image/install/start/cloud change.

Owner ran the requested local check command after Node-22 preflight. Supplied evidence is a
319-line tail, not the complete execution log or a leading source fingerprint:
`<local attachment path withheld>`.
SHA-256: `d1c490611edea0c75468b4cdfd0d3b4c443760ef819845d3a14a59c99e9f03d3`.

- **795 passed, 2 failed, 307 errors**, 144.67 seconds; `make: *** [backend] Error 1`.
- Coverage **81.25%**, above the existing 70% floor. Coverage success does not close failures.
- Failure: `tests/personas/test_detection_contract.py::test_write_rule_and_version_digest`.
  Source expects an old 17-action set while `PERSONA_ACTIONS` derives the expanded telemetry
  registry. Check all emit/detection/audit/compliance contracts before updating the expectation;
  do not shrink production coverage or weaken any guard to make this pass.
- Failure: `tests/test_migrations.py::test_every_revision_can_be_reversed_and_reapplied`.
- All 307 ERROR summaries name `sqlalchemy.exc.ProgrammingError`, including schema-backed
  persona/spine tests and migration tests. Full PostgreSQL exception/SQL/SQLSTATE is truncated.
  A common setup/schema cause is a hypothesis, not a confirmed diagnosis or 307 separate defects.

This later owner attempt reached SQL tests; the earlier agent pip-audit bootstrap failure is
historical and cannot be asserted as this run's stopping point. Earlier audit output is absent
from the supplied tail, so do not infer a complete audit certificate. The requested serial
`make check && make dod-check` stops at backend: later Trust/frontend/docs-site phases and the
trailing DoD invocation are not demonstrated. Fresh current checks and exact-commit CI remain open.
The source fingerprint in the next-chat handoff describes the current tree, not an independently
bound fingerprint of the owner's earlier run. Owner explicitly deferred fixes to the next chat.

## Next sequence

1. Read-only warm-up and source verification from the [October 11 handoff](../hackathon/next-session-2026-10-11.md).
2. Preserve the completed diagnostic/repair and Redis CA evidence; their owner full gates passed.
3. Preserve the approved SQL preparation's successful disposable PostgreSQL/full gate evidence.
4. Prepare verified SQL proxy integration, scanner/migration/reference/compliance worker
   packaging, authenticated same-origin ingress, secret/identity config and rollback operations.
5. Review/PR/exact-main CI, signed images/import by digest; only then operator-run migration/grants
   and Cloud Run deployment. Existing nonproduction grant scripts are not production launch commands.
6. Connect Zynth/HTTPS, accept each enabled capability, then real permitted recognition measurement
   and the full independent-review/production/passport/recovery journey. Public sharing stays separate.

Continue one owner-run Cloud Shell checkpoint at a time for cloud mutations. Do not repeat creation
of existing resources, reset passwords, open public SQL, create a VM or deploy unreviewed images
to work around source failures. This record does not authorize model calls or wider IAM grants.
