# S7 — Google runtime preparation and judged rehearsal

Owner authorized S7 on October 5, 2026. [ADR-0055](../decisions/0055-google-durable-runtime.md)
implements runtime assembly and durable reference processing in backend and frontend source.
Live activation and the judged rehearsal are pending; this record is not a deployment certificate.

## Capability and studio coverage

| Capability | Backend | Frontend |
|---|---|---|
| Configuration observation | POST `/api/workspaces/{workspace_id}/personas/runtime/readiness` | Connection panel; configured/unavailable flags, refresh; no live-accuracy claim |
| Durable detection or explicit selected-face representations | POST `.../jobs/enqueue` | Records → approved reference → face inspection → cost confirmation, queue detection or choose/confirm performer |
| Exact-reference recent jobs | POST `.../jobs/history`, max 20 with overflow | Refresh jobs, attempts/state, completed-result reload through existing face read |
| Compare-and-swap recovery/cancellation | POST `.../jobs/update` | Recover stalled/failed job, cancel future processing, same-intent uncertain retry and status reload |
| Authenticated task execution | POST `/internal/personas/jobs/execute` | Job state/result; machine route has no browser control |
| Bounded dispatch reconciliation | POST `/internal/personas/jobs/reconcile` | Committed queued state/recovery; reviewed machine trigger only |
| Existing S4–S6 providers | Runtime supplies Google detection/encoding, optional Gemini, encrypted Redis and KMS signing/trust | Existing private search, investigation/review, production and passport controls |

Selection previews and explicit Scan/Save/reference approval remain the beginning of capture.
Task creation is not completion. Job history does not poll or automatically resubmit cloud work.
Reloading a completed result reads stored encrypted evidence and makes no model call. Unknown
HTTP outcomes retain the exact intent in the existing session-scoped draft lifecycle; stopping
a view does not cancel committed work. Server-side concurrent reference intents are rejected.

## Assembly and lifecycle

Default `PERSONA_GOOGLE_ENABLED=false` supplies no Google provider, metadata token discovery or
live probe. Explicit activation additionally requires approved persona identity/photos, matching
workspace, Linux Cloud Run `K_SERVICE`, a real inspected-image provider and `rediss` query storage.
`PERSONA_GOOGLE_CONFIG` is parsed by `runtime_contracts.GoogleRuntimeConfig`: workspace/project,
region, dimension (128/256/512/1408), immutable primary and retained wrapping versions, optional
signing version/public trust keys, optional Gemini model and reviewed calibration, plus named
queue, default Cloud Run HTTPS worker origin, service-account email and pinned numeric subject.
Extra fields and partial configurations fail closed. No local-key file discovery is supported.

Wrapping and signing must use separate CryptoKeys. Public Ed25519 trust keys are canonical
base64 raw 32-byte public keys; uploaded packages cannot set trust. New encryption uses the
primary KMS version and authenticated tenant/record context. Explicit retained aliases preserve
old data. Existing Vault data needs the explicitly retained legacy provider; a KMS-prefixed
unknown alias never routes to it. Redis remains ephemeral and TLS; expiry/tombstones do not
certify deletion from Google logs, backups or external services. SQL generations/findings and
job ledgers have their existing durable retention boundaries; no new purge job is invented.

Jobs store no pixels or encryption credentials. The database enforces an append-only transition
protocol with scoped advisory serialization and bound successful generation. Runtime uses only
the stored human intent after fresh creator/reference authorization; the independently verified
Google workload identity is recorded separately. Face result, job success and observations are
atomic. Task names are deterministic per dispatch. ALREADY_EXISTS can name a tombstone and
therefore records dispatch only; explicit stalled-job recovery creates a new dispatch reference.

Worker execution allows three attempts, a 120-second lease and 100-second overall processing
bound. Precommit crash or ambiguous provider response can repeat cost; committed replay does
not. Reconciliation processes at most 20 queued intents with a 45-second budget. Cancellation
waits for the job lock and cannot undo a provider call. Human recovery uses current sequence,
fresh membership and unchanged runtime configuration. Changing configuration cancels old work;
the creator can prepare a fresh authorized intent. Ledger bounds reserve final completion space.
Google JWKS cache lasts five minutes; an unknown key fails closed until refresh, an availability
tradeoff that needs live key-rotation rehearsal. Task headers are never an authentication source.

The real assembled runtime disables inline persistent face processing; jobs supply it. S4
query pixels remain transient and S5/S6 comparison/signing remain explicit bounded requests.
No task body can choose an actor, model, destination or key. Workload access is fixed metadata
on Cloud Run, with no ADC credential file, redirect or local development token fallback.

## Reviewable activation and judged rehearsal

This is a preparation checklist for owner review, not authorization to execute it.

1. Review the mixed source changes and revision-bound CI. Run prepared SQL tests on a disposable
   PostgreSQL database before applying anything to the real store. Review intermediate migrations
   and exact-head grant scripts in order; prepare 0015jobs and then confined
   `deploy/accord-job-runtime-grants.sql`. No migration or role command ran in this slice.
2. Select the permitted synthetic-performer corpus, held-out performer-family splits, actual
   detector/encoder revision and calibration policy. Vision detection is not identity matching;
   Vertex multimodal image embeddings are candidate representations, not proven facial accuracy.
   If the publisher returns an unresolved revision, record abstention and select a reviewed
   revision-capable encoder in its own implementation decision. Never invent thresholds/results.
3. Review Google project/region/budget, Cloud Run service identities, Cloud Tasks queue retry and
   rate limits, fixed worker origin and pinned service-account subject. Restrict Cloud Run invoke
   privileges and task enqueue/actAs authority to the named services; application OIDC validation
   remains mandatory. Configure an approved machine reconciliation trigger independently.
4. Review KMS encrypt/decrypt authority for wrapping, separate signing authority and public trust
   registry; scanner Linux limits, trusted-session origin/CSRF settings, confined SQL credentials
   and TLS Redis. Keep credentials/private config owner-local. Define log/backups retention and
   retained-key lifecycle before enabling. Existing app configuration status does not probe IAM.
5. Owner explicitly authorizes deployment, restart and bounded cloud calls. Capture actual
   provider/model revision, corpus fingerprint, latency, spend, encryption/decryption/signature
   evidence and failures without recording secrets/pixels. Deny missing identity, wrong task
   audience/subject, foreign workspace/reference, revoked creator and tampered ciphertext/package.
6. Rehearse commit-before-task outage, reconciliation, process restart, duplicate delivery,
   crash-before-completion, expired lease, stale CAS recovery, task-name tombstone, concurrent
   reference intents and max attempts. Demonstrate SQL success/generation/event atomicity;
   distinguish repeated external calls from committed-result replay. Prove revoked access before
   and after long processing leaves no completed result. Exercise retained-key/public-trust rotation.
7. Render the complete creator Scan/Save/approve/detect/select → private query/abstention/match →
   grounded investigation → independent reviewer → recipient production clearance → passport
   export/tamper verification/revocation journey. Record actual held-out retrieval denominators,
   false matches, abstentions, quality failures, rank, margins and p50/p95; preserve failures.
   No publication, broad web scanning or real-person enrollment is included in this prototype.

## Source verification

October 5 source verification:

- 74 S7 backend tests pass: real RSA/Ed25519/AES primitives with ephemeral synthetic keys,
  bounded mock Google wire contracts, stored actor/configuration, attempts/lease/replay, queue
  outage, partial reconciliation timeout, fresh permission, private ASGI/CAS and offline DDL parity.
  Disconnected session/ledger mocks establish orchestration only, not SQL durability/concurrency.
- Broader S1–S7/spine selection passed 286 cases, then four existing SQL-backed auth fixtures
  could not start because Docker socket access is forbidden. No unsandboxed retry occurred.
- 434 frontend unit tests across 47 files pass, including 21 S7 cases. Actual isolated ASGI-to-UI
  serialization/gateway/React integration passes 17 cases across three files, including two S7
  cases. These use synthetic sessions/services and no listener, SQL or cloud provider.
- Backend Ruff/Black (325 files), mypy (310 files) and Bandit pass. Frontend lint, formatting,
  TypeScript, production build and shared-bundle budget pass: 166.4 kB gzip / 250 kB.
- `make check` passes preflight, 776 guards (18 skipped), policy/harness and backend static checks,
  then pip-audit fails its temporary pip-upgrade bootstrap. Full dependency audit, SQL/coverage,
  Trust and subsequent stages remain incomplete. `make frontend` passes lint/format/types then
  npm audit fails registry DNS `ENOTFOUND`; independent tests/build do not replace the audit.
- `make dod-check` passes with 57 ADRs / 154 standards. File/function bounds, whitespace and
  offline migration/model transition-protocol parity pass. Five new PostgreSQL tests collect
  only: outage/reconciliation/atomic replay, owner/CAS isolation, cancellation/immutability,
  invalid sequence and confined-role RLS/advisory/Persona locks without portrait UPDATE.

Actual Google, scanner/Linux/Redis, migration/runtime-role, permitted recognition benchmark,
restart/key rotation and rendered acceptance remain open. No package install, credential/private
configuration, migration/grant execution, runtime restart, cloud/model/key activation, signing with
real keys, publication, memory update or Git write occurred. The mixed checkout is preserved;
owner review, commit/PR and revision-bound CI remain pending.

Primary wire references: [Cloud Tasks creation/tombstones](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues.tasks/create),
[task HTTP/OIDC/deadline schema](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues.tasks),
[Cloud Run workload identity](https://docs.cloud.google.com/run/docs/securing/service-identity),
[Google signed identity validation](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token),
[KMS encryption](https://docs.cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys/encrypt)
and [KMS decryption](https://docs.cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys/decrypt).
