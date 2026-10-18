# Production SQL transport proposal — October 11

Status: **Owner approved source preparation; implemented, full gate passed; no cloud execution.**
Recorded in [ADR-0063](../decisions/0063-private-sql-proxy-transport.md). One production environment,
existing minimum MVP database sizing, Zynth later, Tasks paused.

## Recommended transport

Use a Cloud SQL Auth Proxy v2 sidecar beside each SQL-using runtime. Bind only to
`127.0.0.1:5432`, explicitly select private IP and the existing connection name:

```text
API / reference worker / compliance worker / migration operator
  -> same-instance loopback proxy
  -> authenticated encrypted private connection
  -> gen6th-accord-production:asia-southeast1:accord-prod-db / appdb
```

The proxy uses that runtime's selected workload service identity. Do not download keys,
mount owner credentials, enable public SQL IP or change `ENCRYPTED_ONLY`. The existing
instance-scoped Cloud SQL Client grants are recorded for the four selected identities.
Proxy connection authority remains separate from SQL login and table/RLS privileges.
Application processes never use `accord_migrator` or administrative SQL credentials.

The proxy manages the remote TLS connection; the application-to-proxy hop is loopback
inside the same Cloud Run instance. A direct private-IP URL without verified TLS is not
an equivalent substitute. Keep the proxy address private to that instance, not a VPC
listener or independently exposed service. Google's guidance supports private-IP proxy
connections and describes loopback as the default TCP listener:
[Cloud SQL Auth Proxy](https://docs.cloud.google.com/sql/docs/postgres/connect-auth-proxy).

## Approved source-preparation scope

1. Add an explicit reviewed SQL transport setting and fail-closed validation of the proxy
   mode's asyncpg URL: loopback host, agreed port, explicit database/login and no transport
   query overrides. Development keeps its existing disposable/local SQL behavior.
2. Share runtime engine configuration between `db/connection.py` and
   `command/worker.py`. Start with pool size 2 and overflow 0 per runtime engine, with
   bounded checkout/connect waits. The migration engine retains its existing NullPool.
   Connection limits must later account for revision overlap and the actual SQL ceiling;
   these small pools are proposed bounds, not a proven capacity result.
3. Prepare a reviewed proxy container contract: exact private instance, explicit loopback
   listener, workload identity, pinned verified image digest, health probes/start order and
   shutdown behavior. Container startup order alone is insufficient without a successful
   startup probe. [Cloud Run sidecar startup](https://docs.cloud.google.com/run/docs/configuring/services/containers#configure-container-start-order-for-sidecar-deployments).
4. Test wrong/missing transport settings, remote hosts, credential/config failures, bounded
   pool behavior and migration compatibility using mocks and disposable SQL only. Run the
   full gate/DoD, reconcile docs and record the implementation decision in an ADR.

No Python connector dependency is required for this choice. Source approval does not authorize
package installs, grant changes, image import, production queries/migrations or deployment.
Pinning/verifying the proxy's supply chain needs its own reviewed release integration;
the existing application release workflow signs backend/frontend images only. No workflow,
release guard, evidence validator or scanner policy will be edited under this transport unit.

## Implementation and evidence

`db/runtime.py` implements explicit transport/credential-bearing URL validation and the shared
runtime engine factory. `db/connection.py` and `command/worker.py` use it; migration URL resolution
validates transport but retains operator credentials and Alembic's unchanged NullPool. Explicit
Alembic URL overrides remain owner-controlled and must bind the same reviewed job/proxy contract.
Known administrative logins are rejected by runtime engines; this does not prove SQL role attributes.
`.env.example` documents `DATABASE_TRANSPORT`; no private environment file was read or changed.

The non-deployable [proxy contract](../../deploy/google/sql-proxy-contract.json) and
[packaging notes](../../deploy/google/README.md) record identities, flags, probes and shutdown.
Its immutable image is pending supply-chain integration; no proxy executable/image was installed.
Startup probes show process initialization, not application database authorization.

Local **50 focused tests passed**, including SQL config denial, secret-safe errors, shared engine
selection/disposal and existing Redis/Google bootstrap checks. Full backend Ruff/Black/mypy and
targeted Bandit passed. Owner `full-check-5` exited **0**: **1147 backend tests passed**, including
disposable-SQL pool saturation/recovery and migration replay; **93.40% coverage**, 531.20 seconds.
Also passed: 776 guard tests (18 skipped), Trust, 514 frontend and 31 docs-site tests, both builds
and JS audits, and DoD (65 ADRs, 154 standards). Go vulnerability analysis reports no reachable
vulnerabilities; its imported/module findings are not a claim of zero dependency advisories.
No production query or test was run. Full log SHA-256:
`5e38c4464ab7554bdad4d10495bbe6e2fd70a19046c77199e40446dc9d8307c0`.

Current 692-file source fingerprint (same population as the handoff):
`32d80b0838d6c44785a4339345a30330c16c86bf552b722aae090d5c430fc725`.
Proxy contract SHA-256:
`70c1e8011736bae3f806015eb5efe69d1dcfd61a0f06ce02307cfef234e6be43`.
Owner printed matching source and contract fingerprints before and after the successful gate.
This population is not a complete release binding or live connection result.

## Remaining deployment contracts

This choice does not finalize SQL users/grants, scanner packaging, ingress or worker execution.
Next review: [migration job preparation](migration-job-preparation-proposal-2026-10-11.md).
Preserve their separate implementation review and signed-release requirements:

- Reconcile the existing confined runtime-grant chain with API/reference/compliance privileges
  before creating SQL logins. The current grant templates must not be applied blindly at head.
- Package the loopback-only scanner with current definitions and measured Linux memory/startup
  bounds. Keep unsafe/stale/unavailable rejection; no remote scanner endpoint is substituted.
- Choose the public same-origin browser entry and authenticated route to the IAM-private API.
  Existing Next rewrites do not obtain a Cloud Run identity token.
- Package the continuous compliance process separately from the request-driven reference
  worker. The current worker has no HTTP listener; an idle HTTP service is not its runtime.
- Keep max service/worker counts small; measure before declaring a workable scanner/worker
  memory profile. Do not resize/recreate the provisioned SQL or Redis resources during prep.

After approved source and exact-main CI/signing, prepare concrete owner-run Cloud Shell
checkpoints against the existing inventory. No live readiness is claimed by this proposal.
