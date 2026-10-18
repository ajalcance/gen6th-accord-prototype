# Google production bootstrap

Updated: 2026-10-11. Direction: [ADR-0061](../decisions/0061-production-first-google-bootstrap.md).
One production environment; no separate staging. Owner performs Google Console setup and uses
Zynth for production sign-in. Initial acceptance happens before inviting users.

This is the setup sequence and evidence register, not a completed deployment. Google manifests,
reviewed resource sizing and deploy commands remain to be prepared against the selected project.
Do not execute old Compose launch commands as if they deploy this Google topology.

Current owner configuration evidence: [October 11 inventory](google-production-inventory-2026-10-11.md).
Next-chat entry: [handoff](../hackathon/next-session-2026-10-11.md). Owner selected minimum workable
MVP sizing, deferred a numerical budget target and Zynth setup, and completed the foundations
listed there. Do not repeat those choices or resource creation. No application is deployed.

## Checkpoint discipline

Complete one checkpoint, report its non-secret evidence, verify it, then advance. Mark incomplete
work Pending or Blocked, never Passed from a flag, screenshot of configuration or mock test.
Do not paste credentials, secret values, identity tokens, database URLs or uploaded pixels.
Infrastructure names/URLs, image digests, schema revision and redacted failure summaries suffice.

| Checkpoint | Status | Exit evidence |
|---|---|---|
| G0 Project, billing and intended domain | Project/domain confirmed; Zynth deferred; budget target deferred by owner | Actual choices in inventory; live HTTPS/login remains G5 |
| G1 Reviewed deployable source | SQL/CA/runner/scanner/role source gate passes; release pending | [SQL role acceptance](../hackathon/sql-role-checkpoint-2026-10-12.md): full-check-10 exits 0, 1249 backend (93.58%), later phases/DoD, matching hashes; composition/startup/CI/signed digests pending |
| G2 APIs, identities and networking | Foundations provisioned; integration pending | Scoped IAM/VPC inventory; federation and runtime egress/routing pending |
| G3 Database and TLS Redis | Provisioned; acceptance pending | Private connectivity, confined runtime role, schema/RLS/CA and restore proof pending |
| G4 Keys, secrets and scanner | Keys/secrets provisioned; acceptance pending | Runtime version/trust wiring, scanner and real crypto probes pending |
| G5 HTTPS workspace and Zynth | Pending | Production origin/callback, authorized login/read and denied foreign scope |
| G6 Durable and compliance workers | Queue paused; workers pending | Private OIDC delivery, reconciliation/replay, audit ingest/seal and restart proof |
| G7 Provider and recognition acceptance | Pending | Model provenance, permitted corpus, measured results and reviewed calibration |
| G8 Full workflow and launch operations | Pending | Human review/production/passport journey, tamper/revocation and recovery evidence |

## G0 — Create the project and billing envelope

1. Open [Google Cloud Console](https://console.cloud.google.com/) with your owner account.
2. Open the project selector, choose **New project**, and name it `Gen6th Accord Production`.
   Choose an available project ID; record the actual ID, not the display name. Select the
   appropriate existing organization/folder, or No organization if that is your account setup.
3. Create the project and select it. Record its project number from the project dashboard.
4. Open **Billing** and link an active billing account. Complete Google's billing setup if needed.
5. Open **Billing → Budgets & alerts**, create a project-scoped monthly budget with your chosen
   amount, and configure actual/forecast alerts to recipients you control. An alerts-only budget
   does not stop spending. Record any separately selected supported spend cap and its coverage.
   Owner later deferred the numerical budget target and requested minimum workable sizing;
   preserve that override. Do not block setup or keep asking for a budget amount.
6. Choose the intended Accord HTTPS domain and record the existing Zynth production issuer URL.
   If Zynth is not deployed yet, record that prerequisite; local sign-in is not live-server proof.
7. Report project ID, project number, billing-linked status, budget target, intended domain and
   Zynth public URL. Credentials/payment details stay in Google's Console or your local setup.

Region is selected per regional resource later: use `asia-southeast1`, not an invented global
project region. Estimate database, Redis, continuous worker, ingress and model costs before G3;
these resources can incur charges without end users.

Official guidance: [project creation](https://docs.cloud.google.com/resource-manager/docs/creating-managing-projects),
[billing](https://docs.cloud.google.com/billing/docs/how-to/manage-billing-account),
[budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets).

## G1 — Prepare the exact source and release

1. Preserve the current mixed checkout. Review prototype, dependency and agent-boundary work
   into focused PRs; never publish HEAD as though it includes uncommitted/untracked capabilities.
2. Resolve latest owner SQL/setup and detection-contract failures, then recorded integration
   timeouts; run current `make check` and `make dod-check`.
   Use owner/CI for sandbox-inaccessible SQL tests; keep failed/unavailable phases explicit.
3. Prepare reviewed Google infrastructure/manifests, ingress, scanner packaging, transport/CA
   wiring, migration operation and rollback instructions. Source preparation is not provisioning.
4. Merge reviewed changes, verify the default-branch CI run for that exact commit and satisfy
   existing release checks. Produce the signed backend/frontend images and release evidence.
5. Prepare Artifact Registry access/import that preserves verified image digests. The current
   GHCR release workflow does not deploy to Cloud Run; private registry access must be wired.
   Never build application images on a production server or substitute moving tags.

ADRs/guard-sensitive deployment changes require existing owner review; agents apply no approval
labels. [Cloud Run image deployment](https://docs.cloud.google.com/run/docs/deploying).

## G2 — Enable APIs and establish scoped identities/networking

1. In **APIs & Services → Library**, enable the reviewed foundation APIs: Cloud Run, Artifact
   Registry, Compute Engine/networking, Service Networking, Cloud SQL Admin, Memorystore for
   Redis, Secret Manager, Cloud KMS, Cloud Tasks, Cloud Logging and Cloud Monitoring. Enable
   IAM/Workload Identity Federation dependencies for the reviewed deploy identity configuration.
2. Create separate service identities for API, frontend, reference worker, task delivery,
   compliance worker, migration operator and deployment. Give each only its required resource
   permissions; runtime identities do not inherit migration/database-owner authority.
3. Configure repository-scoped CI workload federation if CI deploys. Do not download service
   account keys or give every runtime project Editor/Owner.
4. Create a custom VPC and regional subnet, allocate reviewed private-services ranges and
   configure private services access. Plan Cloud Run VPC egress to private SQL/Redis and required
   outbound HTTPS; routing all egress requires an explicit external egress plan.
5. Prepare one HTTPS browser/API origin and keep private machine services IAM-protected.
   Review ingress and token handling before choosing load-balancer routing or an authenticated
   frontend proxy. Ordinary Next rewrites alone cannot invoke an IAM-private API.

[Cloud Run VPC egress](https://docs.cloud.google.com/run/docs/configuring/vpc-direct-vpc),
[service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service).

## G3 — Create and prove data services

1. In **SQL**, create a PostgreSQL 17 instance in Singapore using the reviewed sizing,
   availability, private networking, backup/PITR and deletion-protection configuration.
2. Owner approved private Cloud SQL Auth Proxy transport with workload identity. The shared
   runtime engine validates loopback configuration and bounds pools; the prepared container
   contract still needs verified-image and lifecycle integration. Complete its full source gate
   and later runtime acceptance. [SQL preparation](../hackathon/sql-transport-proposal-2026-10-11.md)
   authorizes no production query, grant or deployment.
3. Rehearse the complete migration chain on disposable SQL first. Then advance production
   schema incrementally with the separate migration operator, applying each reviewed confined
   grant at its required exact migration head, through `0018lifecycle`. Earlier grant scripts
   intentionally refuse later heads. Verify runtime privileges and workspace RLS/concurrency.
   Review [grant sequencing](google-migration-grant-sequencing.md); the prepared runner upgrades
   one explicit revision and requests proxy shutdown, but never executes grants or creates roles.
4. In **Memorystore for Redis**, create the reviewed regional/private instance with in-transit
   encryption enabled at creation. Configure AUTH if selected; keep its value in Secret Manager.
5. Mount the existing service CA secret at an absolute path and set `REDIS_CA_CERT_PATH`.
   [Source preparation](../hackathon/redis-ca-preparation-2026-10-11.md) shares verification
   across both clients and passed the full gate; reviewed images/mounts and live certificate/name
   acceptance remain pending. Do not disable verification or substitute plaintext `redis://`.
6. Prove TTL behavior, session isolation, compliance-stream retention and backup restoration.
   Review shared Redis memory/eviction policy; ephemeral queries and audit delivery have different
   loss/retention needs. Record production data and backup retention before storing images.

[Cloud SQL connection](https://docs.cloud.google.com/sql/docs/postgres/connect-run),
[Redis TLS setup](https://docs.cloud.google.com/memorystore/docs/redis/manage-in-transit-encryption).

## G4 — Configure crypto, secrets and inspected upload

1. In **Security → Key Management**, create a regional key ring and a symmetric encryption key
   for envelope wrapping. Pin the actual key version; retain versions needed by stored data/backups.
2. Create a separate asymmetric signing key with SOFTWARE protection and `EC_SIGN_ED25519`
   for the existing passport adapter. Record its version and reviewed public trust key. Grant
   wrapping/signing authority separately; public key access does not confer signing authority.
3. In **Secret Manager**, create the application/session, confined database/Redis and Zynth
   client secret entries required by `.env.example`; generate values locally or in the owner
   setup, never in chat. Grant access per named secret and runtime identity; pin secret versions.
4. Package a reviewed scanner sidecar beside image-processing services. The current scanner
   connects only to loopback; provide current definitions, bounded resources and startup probes.
   Prove clean upload, unsafe rejection, stale-definition denial and Linux decode/memory bounds.
5. Verify real KMS wrap/unwrap and tamper rejection; later prove passport signing/verification.
   No Vault is required for a fresh Google store unless retained Vault-encrypted data needs it.

[KMS algorithms](https://docs.cloud.google.com/kms/docs/algorithms),
[Cloud Run containers](https://docs.cloud.google.com/run/docs/configuring/services/containers).

## G5 — Deploy the HTTPS workspace and connect Zynth

1. Deploy reviewed signed frontend/API digests with `ENVIRONMENT=production`, selected identities,
   secret references and health checks. Explicitly configure frontend/backend container ports.
2. Configure the reviewed same-origin `/api` route and HTTPS certificate, then point domain DNS
   to that entry. Verify direct ingress cannot bypass the selected boundary.
3. In Zynth, register the real production origin/callback and intended tenant/workspace. Configure
   issuer/client settings, server-only session key, `ACCORD_APP_ORIGIN` and frontend connection
   settings. Verify the callback path against the current router before registration.
4. Enable the identity/API capability only after schema/session prerequisites pass. Verify login,
   logout, secure cookie/CSRF behavior, unauthorized access and foreign-workspace denial.
5. Start with sign-in and record reads. Portrait saving additionally needs inspected upload and
   an encryption wrapper: Google mode requires valid Tasks/KMS/Redis configuration even with
   calibration, Gemini and signing unset. Do not claim a disabled-wrapper image path works.

Public workspace hosting does not enable `PERSONA_PUBLIC_PASSPORTS_ENABLED`. Credits and private
evidence flags also require their own live schema/authorization acceptance before activation.
Lifecycle also defaults disabled. Accept migration `0018lifecycle` and
`deploy/accord-lifecycle-runtime-grants.sql` with confined runtime privileges before enabling
`PERSONA_LIFECYCLE_ENABLED`. Once enabled, all new offers and current permission checks require
an exact reviewed declaration; existing unbound permissions become ineligible until replaced.
Rollback is schema-compatible only; a populated lifecycle ledger refuses destructive downgrade.

## G6 — Configure and rehearse the workers

1. Deploy the private reference worker first and record its default HTTPS `run.app` origin.
2. The regional queue was already created empty and paused before worker deployment; do not
   recreate or resume it. Bind the reviewed task delivery service account,
   numeric subject and audience; grant invoke only on the worker and scoped enqueue/actAs rights.
   Match retry/rate/deadline settings to the existing three-attempt/100-second processing contract.
3. Configure an authenticated bounded reconciliation trigger. Scheduler may be used only with
   reviewed compatible identity; machine OIDC checks remain mandatory inside the application.
4. Provide continuous execution for `accord.command.worker`, using a reviewed worker pool or
   equivalent always-running configuration. An ordinary scale-to-zero request service does not
   establish continuous telemetry ingestion/sealing.
5. Set reviewed `PERSONA_GOOGLE_CONFIG`: workspace/project/region, supported dimensions, exact
   KMS versions, Tasks queue/default origin and pinned delivery identity. Enable the runtime
   only after these prerequisites pass; no invented calibration or default model is supplied.
6. Exercise dispatch outage, restart, duplicate delivery, expired lease, reconciliation, CAS
   recovery and completed replay. Verify SQL atomicity, fresh creator permission and audit sealing.

[Cloud Tasks OIDC](https://docs.cloud.google.com/tasks/docs/creating-http-target-tasks),
[worker pools](https://docs.cloud.google.com/run/docs/deploy-worker-pools).

## G7 — Run bounded Google/provider and recognition acceptance

1. Enable Cloud Vision and Vertex AI APIs; review regional availability, approved Gemini model,
   quotas, task rates, Cloud Run limits and an explicit bounded probe budget before model calls.
2. Prove actual provider/key access using permitted synthetic-performer evidence. Cloud Vision
   face detection does not establish identity matching; record real encoder/detector provenance.
3. Select the permitted held-out corpus and run the documented recognition evaluation. Record
   corpus/model fingerprints, scored/failure denominators, false matches, abstentions, quality,
   rank/margins, latency and spend. An unresolved publisher revision blocks calibrated search.
4. Review measured calibration before supplying it to the runtime. Enable grounded investigation
   and trusted signing separately after their own acceptance. Keep unavailable capabilities honest.

Follow [S7 rehearsal](../hackathon/google-runtime-slice.md) and the
[recognition workflow](../hackathon/recognition-evaluation-workflow.md); neither imports an
offline report as server activation authority.

## G8 — Complete the workflow and operate the live deployment

1. On the production origin, verify capture/scan/save/read-back, approved references, exact and
   calibrated search, grounded findings, an independent reviewer and recipient production use.
2. Verify passport export/current permission, altered-package rejection, revocation and key
   rotation. Public passport sharing remains a separate explicit approval and ingress test.
   Exercise [L1–L8 acceptance](../hackathon/performer-lifecycle.md): owner/operator separation,
   inspected rights evidence, all three independent assessments, declaration replacement,
   lost reviewer/operator roles, private 30-day trials and multi-case, cross-version suspension.
   Verify older history cases remain actionable and resolving one does not clear another.
3. Configure uptime/error/queue/backlog/scanner/key/budget alerts and redacted logs. Demonstrate
   audit ingestion/sealing, restore and previous-revision rollback with a schema-compatible image.
4. Record each result against source/image/config/schema fingerprints. Invite users after the
   enabled journey passes; continue fixes through reviewed signed releases to this environment.

Cloud Storage evidence adapters, Vector Search, broader Pub/Sub/cell architecture and public
resolver/organization/delegate/import/dispute features remain separate roadmap work, not bootstrap
dependencies. Hosting production does not turn those planned capabilities into implemented ones.

## Preparation verification — October 11

Latest owner repair gate exited **0**: **1108 backend passed, 93.12% coverage**, Trust,
514 frontend and 31 docs-site tests, both builds/audits and DoD pass. Patched JS pins/locks agree.
Subsequent [CA preparation](../hackathon/redis-ca-preparation-2026-10-11.md) full gate also passes:
1122 backend (93.26%), all later phases/DoD green. Approved SQL transport implementation passes
1147 backend (93.40%), all later phases/DoD, matching source/contract before/after. CI/release
and live acceptance remain pending.

Historical agent preparation, before owner provisioning and the later SQL attempt:
Earlier bootstrap-only preparation: `make dod-check`, whitespace and Unicode checks pass.
Current ADR-0062 source checks and outstanding acceptance are recorded in the
[lifecycle register](../hackathon/performer-lifecycle.md#evidence).
The default shell selected Node 23; using the existing Node 22.23.1 installation passes preflight.
That `make check` run passes 776 guard tests (18 skipped), policy, harness and backend
Ruff/Black/mypy/Bandit, then fails at pip-audit's temporary pip/wheel/setuptools upgrade.
SQL/coverage, Trust, frontend and docs-site phases are not reached in this run. Full green and
exact-candidate CI remain required; no audit or release gate was changed to bypass this failure.
No package installation, cloud setup, service restart, key/provider activation or deployment was
performed by the agent for that preparation. Later owner provisioning is in the inventory;
existing checkout changes remain preserved and uncommitted.
