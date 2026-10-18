# Addendum 03 — Operations, Data Lifecycle, Security and Mobile

| | |
|---|---|
| Amends | Architecture v1.0, [Addendum 01](addendum-01-deployment-identity-trust.md), [Addendum 02](addendum-02-identity-agent-governance-zynth.md) |
| Addendum version | 1.0 |
| Date | 23 September 2026 |
| Status | Approved, all priorities (P0, P1, P2), including §12 (engineering baseline, Option B: Python backend) |
| Companion | [Retention schedule](retention-schedule.md) |

This addendum closes the gaps found in the whole-plan review of 23 September 2026. Priorities:

- **P0:** before Stage 1 (it changes the foundation).
- **P1:** before the first external customer.
- **P2:** after traction. Anything a P2 item depends on is designed now.

---

## 1 Decision register

| ID | Decision | Pri |
|---|---|---|
| D-21 | **Personal data stays outside the hash.** Signed manifests and the log carry pseudonymous IDs and salted commitments, never readable personal data. Erasure removes the separate personal-data layer and its salt (§5.2). | P0 |
| D-22 | A **retention schedule** governs every data class, with a stated deletion method ([retention-schedule.md](retention-schedule.md)). | P0 |
| D-23 | **Plumbing fixed:** outbox dispatch at commit plus a one-minute sweep; Intelligence becomes a **Cloud Run service** fed by Pub/Sub push; legal deadlines run on **Cloud Tasks**; public status projections live in **Cloud Storage** (replacing Firestore) (§2). | P0 |
| D-24 | **Web runs on Next.js (TypeScript) on Cloud Run as a backend-for-frontend (BFF).** Browser JavaScript never holds tokens: the session is an httpOnly cookie, and the content security policy uses nonces. Firebase Hosting stays in front as the day-0 edge and CDN (§2.5). | P0 |
| D-25 | **Native mobile apps (iOS and Android)** built with **Expo / React Native (TypeScript)** (§4). | P1 |
| D-26 | **Resend** for Accord's transactional email, with delivery evidence recorded (§3.6). | P0 |
| D-27 | **Billing through Paddle as merchant of record, with PayPal enabled inside Paddle checkout.** Direct PayPal Subscriptions is the fallback if Paddle onboarding of the Accord entity fails. No in-app purchases in the mobile apps at launch (§3.7). | P1 |
| D-28 | **Hosted status page** on a free or low-cost tier, independent of GCP (§3.8). | P1 |
| D-29 | **Observability standard:** OpenTelemetry, four separate log classes with their own retention, and service-level objectives for the Trust path (§6). | P0 |
| D-30 | **Storage layout:** a fixed bucket set per cell, control plane and trust project. Content-addressed objects. The log and public projections are mirrored to a second provider (§7). | P0 |
| D-31 | **Continuity:** critical recovery secrets are split among named custodians (Shamir), with documented emergency access. Accord repositories move to a GitHub organization (§5.10). | P1 |
| D-32 | The **`zynth-setup` template** is the engineering baseline, followed closely, with Go and TypeScript modules and a Cloud Run deploy target added (§12). | P0 |
| D-33 | **Backend in Python (FastAPI)**, supersedes the TypeScript backend in D-10. Go stays for Trust and the reference verifier. TypeScript stays for web (Next.js), mobile (Expo) and the browser verifier. **Why:** the template's guardrails, standards and compliance spine work from day one; `copier update` keeps working; it matches Zynth's stack; and it has the strongest Vertex AI and fingerprinting ecosystem (§12). | P0 |

---

## 2 Architecture corrections (P0)

### 2.1 Outbox dispatch

The domain change and its outbox row commit in one transaction. The service publishes to Pub/Sub straight after commit. A **Cloud Scheduler sweep every minute** calls a dispatch endpoint that publishes anything left behind, for example because an instance scaled to zero mid-request. Consumers are idempotent by event ID. Every topic has a **dead-letter topic** and a replay runbook.

### 2.2 Intelligence as a Cloud Run service

Intelligence is a Cloud Run **service**, not a Job. It receives Pub/Sub push deliveries, scales to zero and runs with bounded concurrency. It authenticates to Zynth by GCP workload attestation (Addendum 02). Long analyses are split into steps, each resumable by ID.

### 2.3 Durable timers

**Cloud Tasks** drives every deadline: dispute response periods, confirmation expiry, claim expiry, embargo lifts, approval windows and retention jobs. Each task names its record and deadline, is idempotent, and writes an audit event when it fires. A daily reconciliation sweep compares open deadlines with scheduled tasks and re-creates any that are missing. Deadlines are stored in UTC and shown in the recipient's local time. The deadline-calculation rule (calendar days, cut-off at 23:59:59 in the recipient's time zone) is part of the dispute policy pack.

### 2.4 Public status projections in Cloud Storage

This replaces the Firestore projection of v1.0 §10.2. It is more durable (multi-region or dual-region, versioning, retention locks), cacheable at the CDN, trivially mirrored, and fits the "records outlive the company" goal.

Layout, in the control-plane bucket `public-projections`:
- One immutable object per issued record version.
- One small mutable status object per record.
- An index per issuer.

The Public Verifier reads only from this bucket. Browser-side verification still checks everything against the log (Addendum 01 §6.4).

### 2.5 Web delivery and session (BFF)

- `frontend/` (the web app) is Next.js on Cloud Run (scales to zero). Firebase Hosting rewrites give the custom domain and CDN at day 0. The global load balancer and Cloud Armor replace this at P1 (§3.4).
- **BFF:**
  - Next.js server routes complete the Zynth OIDC login.
  - The tokens stay server-side, in an encrypted session store keyed by an httpOnly, `Secure`, `SameSite=Lax` cookie.
  - Browser code only ever talks to its own origin.
- **Headers:** nonce-based CSP with `strict-dynamic` (resolving the template's FE-024), Trusted Types, HSTS preload, `frame-ancestors 'none'` except on embeddable verify widgets, and a strict `Referrer-Policy`.
- The public verify pages run verification in the browser with `accord-open/ts/verify`. They need no session.

---

## 3 Infrastructure

### 3.1 GCP foundation (P0)

- A GCP **Organization** with folders `accord-prod`, `accord-nonprod` and `accord-shared`.
- Org policies:
  - no public buckets (except `public-projections`, served through the verifier or CDN only);
  - no service-account keys;
  - allowed regions only;
  - OS Login;
  - uniform bucket-level access;
  - CMEK required where tagged.
- A Terraform state bucket in `accord-shared` with versioning and a lock.
- Budgets and alerts per project; billing export to BigQuery.

### 3.2 CI/CD and release (P0)

- GitHub Actions authenticates to GCP through **Workload Identity Federation**, so no stored keys exist.
- Images live in **Artifact Registry**, are signed with cosign, carry an SBOM, and every Cloud Run service enforces **Binary Authorization**.
- Promotion from nonprod to prod deploys the exact signed digest and never rebuilds (the template's release evidence chain, §12).
- The Trust and identity projects deploy through a separate, restricted pipeline that needs owner approval.

### 3.3 DNS and email authentication (P0)

- DNSSEC, CAA records, HSTS preload for `gen6th.com`.
- SPF, DKIM and DMARC (moving to `p=reject`) for the sending subdomain `notify.gen6th.com`.

### 3.4 Edge protection and rate limits (P1)

- A **global HTTPS load balancer**, **Cloud Armor** (WAF rules, per-IP and per-path rate limits, adaptive protection) and **Cloud CDN** in front of the web app, the API and the verifier.
- Per-tenant and per-credential rate limits in the Accord API for humans and integrations. Agents are already limited by Zynth.
- About USD 20–25 per month.

### 3.5 Search (P1)

- Postgres full-text search, per cell.
- Indexes respect object visibility, and **sealed and restricted content is never indexed**.
- Public-record search runs from the control plane over public projections only.
- A dedicated engine only when measured load needs it.

### 3.6 Notifications (P0)

- **Resend** for email. **Web push** and **mobile push** through FCM and APNs (§4).
- Every notification that carries a legal effect (a dispute notice, a confirmation request, an appeal notice) records the recipient, channel, provider message ID, and delivery, bounce and open events from Resend webhooks.
- Undelivered legal notices escalate to a second channel and to operator review. **A failed notice never counts as consent or as a missed deadline.**

### 3.7 Billing (P1)

- **Paddle** is the merchant of record. It handles global sales tax and VAT, subscriptions, invoices and dunning, and offers **PayPal** in its checkout alongside cards, Apple Pay and Google Pay.
- The Philippines is not on Paddle's list of unsupported countries. **Onboarding of the Accord entity must be confirmed with Paddle.**
- **Fallback:** PayPal Subscriptions directly, with Accord then responsible for its own tax registration and collection.
- Plans and entitlements stay in Accord (v1.0 §17). Paddle webhooks update the subscription state.
- Mobile apps do not sell. Purchases happen on the web.

### 3.8 Status page (P1)

- A hosted status page on a free or low-cost tier (for example Better Stack or UptimeRobot), **outside GCP**, so it stays up when we are down.
- Components: web, API, sign-in (Zynth), signing, verification, notifications.
- Its checks mirror the synthetic probes in §6.5.

### 3.9 Local and preview environments (P1)

- Docker Compose for Postgres, the Pub/Sub and Cloud Storage emulators, a test KMS key (software, nonprod only) and a pointer to the nonprod Zynth.
- Preview environments per pull request, deployed to nonprod Cloud Run with a TTL.

### 3.10 Feature flags (P1)

- A flag table in the control plane, evaluated through OpenFeature-compatible clients in Python, TypeScript and Go.
- Flag changes are audited.
- Dormant capabilities (witnesses, hybrid packaging, earned autonomy) are flag-gated as well as entitlement-gated.

---

## 4 Mobile apps (D-25)

| Area | Decision |
|---|---|
| Stack | **Expo / React Native, TypeScript**. Uses the TypeScript client generated from the backend's OpenAPI, the shared `contracts/` schemas and the `accord-open` TS verifier |
| Apps | iOS and Android, one codebase. `mobile/` in the monorepo |
| Sign-in | Zynth OIDC with PKCE through the system browser (not an embedded web view). Tokens in the iOS Keychain or Android Keystore. **DPoP key held in the Secure Enclave or StrongBox** (Zynth supports DPoP) |
| Signing | Native passkeys with RP ID `gen6th.com`, linked through iOS associated domains and Android Digital Asset Links. **Zynth G1 must accept native-app origins** (added to the Zynth requirements) |
| MVP features | **Quick Proof capture** (photo, video, audio, document); **QR scan to verify**; approve and sign (reviews, confirmations, releases); notifications; case deadlines; record wallet |
| Capture-time evidence | The file's SHA-256 is computed **on the device at capture**, before upload, and recorded with the device attestation (App Attest / Play Integrity) and capture time. This is honest evidence of when the file existed, not a claim of authorship |
| Offline | Drafts and captures queue offline and are hashed immediately. Signing and submission need a connection |
| Push | FCM and APNs through Expo push or direct. The payload never contains restricted or sealed content, only "you have an action" |
| Release | EAS Build, signed binaries, staged store rollout, crash reporting without personal data |
| Commerce | No in-app purchases at launch |
| Stage | Mobile MVP starts after Stage 4 (signing) and ships with Stage 5 (verification) |
| Cost | Apple Developer USD 99 per year; Google Play USD 25 one-off; Expo free tier to start |

---

## 5 Security

### 5.1 Threat model (P0)

A STRIDE threat model plus abuse cases for each component (web BFF, Core, Control, MCP server, Intelligence, Trust Signer, Trust Log, Verifier, mobile, Zynth integration). It is written before Stage 1, reviewed at every stage exit, and kept in `docs/security/threat-model/`.

### 5.2 Personal data outside the hash (D-21, P0)

1. A manifest names people by `person_id` and, where a readable name is needed, a **salted commitment** `H(salt ‖ display_name)`.
2. The display name, contact details and salt live in an **erasable personal-data layer**, encrypted under a per-person key.
3. Public pages render names from that layer, and verifiers can check that the displayed name matches the commitment.
4. **Erasure** destroys the per-person key and salt (crypto-shredding). The signature, digests and log entries stay valid; the record then shows "erased person".
5. Evidence bytes containing personal data follow the tenant's retention and erasure rules. A manifest only holds their digests.
6. Legal-hold and legal-obligation exceptions are recorded when an erasure is refused.

### 5.3 Signing-key governance (P0)

- KMS administration and signing are separate roles; no single person holds both in production.
- Rotating, disabling or destroying a key requires dual approval through Privileged Access Manager, plus an audit record.
- Alerts fire on any KMS IAM change, key-version state change or signing from an unexpected identity.
- A **key ceremony** runbook is written: generation, witnesses, recorded fingerprints and published public keys.

### 5.4 Perimeters and privileged access (P1)

- **VPC Service Controls** around the Trust and identity projects.
- **Privileged Access Manager** for time-bound GCP roles, and Zynth access requests for application operator roles. No standing production access.
- Break-glass accounts use hardware security keys and trigger alerts when used.

### 5.5 Upload scanning (P1)

1. Uploads land in `uploads-quarantine`.
2. A ClamAV Cloud Run service scans them.
3. The content type is checked against the declared type and the digest against the client-computed hash.
4. Only then is the file moved to its destination bucket.
5. Files that fail stay quarantined, with a notice to the uploader.

### 5.6 Content safety and takedown (P1)

- Public media is checked against **known CSAM hash lists** through an industry service before publication, with reporting and preservation duties under Philippine law (the anti-OSAEC law) and target-market law. **Exact obligations to be confirmed by counsel.**
- A **takedown process** for illegal or infringing hosted content: notice intake, a designated agent, counter-notice and repeat-infringer handling. It is kept separate from Claims disputes, which are about the record, not about hosting.

### 5.7 Supply chain for `accord-open` (P1)

- Releases are signed with Sigstore and carry SLSA provenance.
- Verifier binaries build reproducibly, so anyone can confirm a release matches its source.

### 5.8 Testing and disclosure (P1)

- An independent **penetration test** before the first external customer, covering the web, API, mobile, signing, the verifier, tenant isolation and the Zynth integration.
- A **vulnerability disclosure policy** and `security.txt` on `accord.gen6th.com`.
- A **bug bounty** at P2.

### 5.9 AI data handling (P1)

- Vertex AI is pinned to the primary region, and customer data is never used for training.
- Prompt and response logging is off except for evaluation sets built from consented or synthetic data.
- Configuration is documented in the vendor register.

### 5.10 Continuity (D-31, P1)

- The backup decryption key, the KMS emergency admin path and the cloud and domain registrar recovery details are split with **Shamir secret sharing** (for example 2 of 3) among named custodians.
- A **dead-man's-switch runbook** says who can act, and how, if the founder is unavailable.
- Accord repositories move to a **GitHub organization** with at least two owners and hardware-key 2FA enforced.

---

## 6 Observability and logging

### 6.1 Standard (P0)

- **OpenTelemetry** SDKs in Python, TypeScript and Go.
- W3C trace context propagated through HTTP, Pub/Sub attributes, Cloud Tasks headers, the MCP gateway and Trust calls.
- **Google Cloud Logging, Monitoring, Trace and Error Reporting** as the backends.
- Structured JSON logs with `trace_id`, `correlation_id`, `tenant_id` (opaque) and `actor_type`.
- Personal data, tokens and evidence content are never logged (the template's OBS-002).

### 6.2 Log classes

| Class | Contents | Store | Retention |
|---|---|---|---|
| Application | Request, error and performance logs | Cloud Logging `_Default` bucket | 30 days |
| Security | Auth decisions, permission denials, rate-limit hits, Zynth Command Center exports, WAF events | Dedicated log bucket, plus a sink to a locked archive bucket | 1 year (archive) |
| Cloud audit | GCP Admin Activity (always on); Data Access **enabled for KMS, Secret Manager, Cloud SQL and the evidence buckets** | `_Required` bucket, plus a sink to the archive | 400 days, then archive to 1 year |
| Domain audit | Accord's append-only domain events (v1.0 `audit` schema) | Postgres, with daily roots in the transparency log | Per the [retention schedule](retention-schedule.md) |

### 6.3 Security monitoring (P1)

Security logs, GCP audit logs, Zynth Command Center events and Accord security events are sunk to **BigQuery**. Scheduled detection queries alert on:
- KMS and IAM changes
- sealed-evidence access outside a case
- mass export
- repeated denials
- break-glass use

A managed security-operations platform is a P2 option.

### 6.4 Service-level objectives (P1)

| Service-level indicator | Initial target |
|---|---|
| Web and API availability | 99.9% monthly |
| Public verifier availability | 99.95% monthly |
| Signing end-to-end latency (approval to log receipt) | 95th percentile under 5 s |
| Outbox lag (commit to publish) | 99th percentile under 60 s |
| Checkpoint freshness | New entries checkpointed within 5 minutes |
| Time-anchor completion | 99% of checkpoints anchored within 24 h |
| Legal-notice delivery | 99% delivered or escalated within 1 h |
| Verifier correctness | 100% of synthetic probes pass |

Error budgets drive alerting. There are two alert tiers: **page** (the phone) and **ticket**.

### 6.5 Synthetic probes (P1)

Every 5 minutes, from outside GCP, a probe:
- fetches a canary record;
- verifies it end to end with the open CLI (signature, inclusion, checkpoint, anchor, status);
- confirms that sign-in is reachable;
- confirms that the status page mirrors the result.

### 6.6 Independent log monitor (P1)

A small job on a second provider (for example a scheduled GitHub Action or a Cloudflare Worker) fetches every checkpoint. It checks consistency with the previous one and alerts on any fork or rewrite. It is not a witness, since it co-signs nothing, but it **detects tampering from day 0**.

### 6.7 On-call (P1)

- Pages go to the founder's phone through Cloud Monitoring alerting (with an escalation contact once one exists).
- Every page links to a runbook (v1.0 §16.3).

### 6.8 Product analytics (P2)

Cookieless and privacy-preserving. Events are aggregate only and never derived from restricted or sealed content.

---

## 7 Storage management

### 7.1 Bucket layout (P0)

| Bucket | Project | Contents | Protection |
|---|---|---|---|
| `uploads-quarantine` | Cell | Unscanned uploads | 7-day lifetime; no public access |
| `artifacts` | Cell | Tenant artifacts, content-addressed | Per-tenant key context; versioning; soft delete |
| `evidence-restricted` | Cell | Restricted evidence | Encrypted per tenant; access-logged; no indexing |
| `evidence-sealed` | Cell | Sealed evidence | Separate bucket; reviewer-bound access; reason required; Data Access logs |
| `exports` | Cell | Tenant and personal exports | 7-day lifetime; signed URLs only |
| `public-projections` | Control | Public record projections (§2.4) | Dual-region; versioning; retention lock on issued versions |
| `log-tiles`, `anchors` | Trust | Transparency log tiles, checkpoints, OpenTimestamps proofs | Dual-region; retention lock; written only by the Trust Log |
| `security-archive` | Shared | Archived security and audit logs | Retention lock (1 year) |
| `backups` | Backup project | Zynth and database backup copies | Retention lock; separate IAM |

All buckets use uniform bucket-level access. Access goes only through short-lived signed URLs or service identities.

### 7.2 Content addressing and deduplication (P1)

Objects are keyed by SHA-256 inside a tenant. **Deduplication happens only within a tenant**; cross-tenant deduplication would reveal that another tenant holds the same file.

### 7.3 Uploads, quotas and lifecycle (P1)

- Resumable uploads with limits per plan. Storage is metered against plan quotas (v1.0 §17).
- Lifecycle moves artifacts older than a tenant-configured age from Standard to Nearline, Coldline or Archive. Retrieval cost is disclosed to the customer in admin settings.

### 7.4 Durability (P1)

- Versioning and soft delete on every data bucket.
- **Dual-region** buckets for restricted and sealed evidence on Enterprise.
- A periodic integrity sweep re-hashes a sample of stored objects against their recorded digests.

### 7.5 Records outlive the company (P1)

- `public-projections`, `log-tiles` and `anchors` are **mirrored to a second provider** (for example S3-compatible object storage outside GCP), plus a public Git mirror of checkpoints.
- A continuity runbook covers the hand-over of the log to the Gen6th Foundation or a successor.

### 7.6 Legal hold (P1)

- GCS object holds (event-based and temporary) plus database flags block deletion, lifecycle transitions and crypto-shredding.
- Placing and releasing a hold is an audited, dual-approved action.

---

## 8 Retention and data lifecycle (P0)

The full table is in [retention-schedule.md](retention-schedule.md). It defines, for each data class:
- the default and allowed range;
- the legal basis;
- the deletion method (hard delete, crypto-shred, anonymize or never);
- the legal-hold behaviour;
- who may change it.

Tenant offboarding, personal erasure and data-subject requests run through that schedule.

---

## 9 Product features

| Feature | Decision | Pri |
|---|---|---|
| **Quick Proof** | Add or connect a work, sign, and get a verification link plus QR code in under 5 minutes, on web and mobile. It creates a Casual-format record in the personal workspace and can be promoted to a formal project later | P1 |
| **Content fingerprints** | Perceptual hashes (image, audio, video) and text shingles are **computed by the Python backend and stored from Stage 1**. Similarity matching runs against public records and opt-in tenants only, never across private data. Matching and alerts ship at P2 | P2 (data P0) |
| **Accord Evidence Package** | Open spec in `accord-open`: manifest, proofs, selective-disclosure envelopes, RO-Crate and C2PA mappings, offline verification instructions | P1 |
| Search | §3.5 | P1 |
| Deadlines and time zones | §2.3 | P0 |
| Languages | English and Filipino at launch; the framework is ready for more | P1 |
| Accessibility | WCAG 2.2 AA on web and mobile, checked in CI (the template's FE-002 plus automated axe checks) | P1 |
| Mobile | §4 | P1 |
| **Evidentiary statement** | A court-ready export: chain of custody, verification steps, what Accord attests and what it does not, and an operator declaration template | P2 |
| Dispute operations | A reviewer and appeal roster, conflict checks, target handling times per route, and operator runbooks | P1 |

---

## 10 AI and Intelligence

| Item | Decision | Pri |
|---|---|---|
| Evaluation harness | Test sets per AI function (semantic diff, extraction, classification, case chronology). No model or prompt change ships without passing regression thresholds | P1 |
| Model lifecycle | Model IDs pinned. A deprecation calendar is tracked, and migrations are re-evaluated before switching | P1 |
| Cost controls | AI spend quotas per tenant and per plan, with hard caps and alerts | P1 |
| Data handling | §5.9 | P1 |

---

## 11 Compliance and legal

| Item | Decision | Pri |
|---|---|---|
| Philippine Data Privacy Act operations | Appoint a Data Protection Officer, register with the National Privacy Commission where required, privacy impact assessments per processing activity, a **72-hour** breach notification runbook, processor agreements | P1 |
| Vendor register | Zynth, Google Cloud, Resend, Paddle, PayPal, OpenTimestamps calendars, the status-page provider, the CSAM-matching service and Expo: purpose, data shared, region, exit plan | P1 |
| Certification roadmap | SOC 2 Type I timed to the first enterprise deal, then Type II and ISO 27001. Zynth's ISMS tools can hold Accord's own risk register and policies | P2 |

---

## 12 Engineering baseline: `zynth-setup` (D-32, D-33)

The repository `ajalcance/gen6th-accord` is generated from the **`zynth-setup`** Copier template and **follows it closely** (Option B: Python backend). The template already provides:
- the AI working contract;
- the ADR and docs system;
- the standards suite;
- the CI security gates and guard fault tests;
- the release evidence chain;
- Dependabot, Scorecard and the branch ruleset.

**None of this is re-specified in the plan.** Accord adds Go and TypeScript modules and changes the deploy target.

### 12.1 Copier answers

| Question | Answer |
|---|---|
| `project_name` / `project_slug` | Gen6th Accord / `gen6th-accord` |
| `python_package` | `accord` |
| `github_owner` / `github_repo` | Current owner (moves to the GitHub organization under D-31) / `gen6th-accord` |
| `license` | Apache-2.0 at generation, **replaced by a proprietary licence** straight after (§12.2) |
| `include_frontend` | Yes (Next.js BFF) |
| `include_docs_site` | Yes (`/docs`) |
| `include_deploy` | Yes, for the release evidence chain. The Compose and Caddy files are removed and the target becomes Cloud Run |
| `include_compliance_spine` | Yes, with its transport adapted to Pub/Sub |
| `solo_maintainer` | Yes (until a second maintainer exists) |
| `include_claude_hooks` | Yes |

### 12.2 Follow, adapt, not use

| Template part | Decision | Accord implementation |
|---|---|---|
| AI contract, `/dod`, docs system, ADRs, `PLAN`, `current-state`, `LESSONS` | **Follow** | The `docs/architecture/*` files move in, and D-01 to D-33 become ADRs |
| Standards suite (API, BE, OBS, SEC, TA, REL, FE) | **Follow** | Plus a new **GO** rule set for `trust/` and a **MOB** rule set for `mobile/` |
| FastAPI backend skeleton, fail-closed config, structured logging | **Follow** | `backend/accord/`, several Cloud Run services from one codebase (Addendum 01 §8) |
| Alembic migrations | **Follow, extended** | Two environments: `control` and `cell` databases |
| Python CI gates (ruff, black, mypy strict, bandit, pip-audit, pytest) | **Follow** | Unchanged |
| Compliance spine (telemetry registry, audit chain, detections, coverage guards) | **Adapt** | Same contract and guards. Transport moves from Redis Streams and a polling worker to the **Pub/Sub outbox**, with sealing on a Cloud Scheduler trigger. **No Redis** |
| Tests on in-memory SQLite (ADR-0003) | **Not use** | Real **Postgres** through Testcontainers, required by row-level security and by the template's own TA-015. Fast unit tests stay database-free |
| `frontend/` Next.js | **Follow** | The BFF (§2.5), with nonce-based CSP (closes FE-024) |
| `docs-site/` | **Follow** | Public docs |
| Release evidence chain (`release.yml`, SBOM, cosign, digest-pinned promotion, readiness verdict) | **Adapt** | Registry becomes Artifact Registry; deploy step becomes Cloud Run with Binary Authorization. Everything else unchanged |
| `deploy/` Docker Compose and Caddy | **Not use** | Cloud Run and Terraform (`infra/`). Local development uses Compose only for emulators (§3.9) |
| Semgrep dangerous-operations rules | **Adapt** | Add Go rules for `trust/` |
| `check_pins.py` | **Adapt** | Also cover `go.mod`/`go.sum` and the mobile lockfile |
| Guard scripts, `make policy`, meta-guard, pre-commit, gitleaks, unicode checks | **Follow** | `trust/`, `mobile/`, `contracts/` and `infra/` are added to the protected-path lists |
| Devcontainer | **Adapt** | Add Go, Terraform, gcloud and the emulators |
| Claude hooks | **Adapt** | Add `gofmt` and prettier hooks |
| Licence (Apache-2.0 or MIT only) | **Replace** | Proprietary licence for `gen6th-accord`. Apache-2.0 for `accord-open` |
| Go (`trust/`) | Not in template | Gates: gofmt, golangci-lint, gosec, govulncheck, `go test -race` |
| Mobile (`mobile/`) | Not in template | Gates: eslint, prettier, `tsc --strict`, jest, `npm audit`; EAS builds |
| Terraform (`infra/`) | Not in template | Gates: `terraform fmt`/`validate`, tflint, checkov |

### 12.3 Accord-owned adaptations

The template is the **foundation only**. Accord makes these changes **in its own repository**; nothing waits on the template. Each is tracked as a Stage 0 or Stage 1 task in `docs/PLAN.md` and lands through the normal pull-request gates.

| # | Adaptation | Stage |
|---|---|---|
| 1 | Proprietary licence | 0 (initial commit) |
| 2 | Accord architecture docs and ADRs imported | 0 (initial commit) |
| 3 | Tests on **Postgres** (Testcontainers) instead of SQLite; two Alembic environments (`control`, `cell`) | 0 |
| 4 | **Go module** `trust/` with its gates, Semgrep rules, pin checks and a `GO-*` standards file | 0 |
| 5 | **Cloud Run** release path (Artifact Registry, Binary Authorization, Workload Identity Federation) replacing the Compose and Caddy deploy | 0 |
| 6 | **Terraform** `infra/` with fmt, validate, tflint and checkov gates | 0 |
| 7 | Spine transport on the **Pub/Sub outbox** (no Redis, no polling worker) | 1 |
| 8 | **Mobile** `mobile/` (Expo) with its gates and a `MOB-*` standards file | 4 |

`copier update` is used selectively. Template improvements are merged by hand where they don't conflict with these adaptations.

## 13 Build stages (updates Addendum 01 §9.1)

| Stage | Additions from this addendum |
|---|---|
| 0 Repository and foundation (new) | Repository from `zynth-setup` with the §12 answers and the §12.3 adaptations, GitHub organization, GCP organization and folders, org policies, Terraform state, Workload Identity Federation, Artifact Registry, Binary Authorization, DNS and email authentication, threat model, ADRs D-01 to D-33 |
| 1 Platform foundation | OpenTelemetry, log buckets and sinks, bucket layout, outbox dispatch and sweep, Cloud Tasks timers, the personal-data layer and crypto-shredding, fingerprint computation, feature flags, local environment |
| 2 Collab core | Resend notifications with delivery evidence; deadline rules |
| 3 Contribution and review | Upload scanning, search, Intelligence service with evaluation harness and cost caps |
| 4 Claims core | Quick Proof (web); evidence package export |
| 5 Trust and verification | Status projections in Cloud Storage, mirrors, independent log monitor, synthetic probes, `accord-open` signed releases; **mobile MVP ships** |
| 6 Disputes and appeals | Dispute operations roster; takedown process |
| 7 Specialized formats | Unchanged |
| 8 Commercial hardening | Paddle billing, status page, Cloud Armor, VPC Service Controls, Privileged Access Manager, penetration test, content safety, Data Privacy Act operations, continuity split, SLOs and on-call |
| 9 Triggered | Unchanged, plus P2 items: similarity matching, evidentiary statement, bug bounty, certification, product analytics |

---

## 14 Cost changes

| Item | Cost | When |
|---|---|---|
| Load balancer, Cloud Armor, CDN | about USD 20–25 per month | P1 (launch) |
| Status page | USD 0–10 per month | P1 |
| Resend | Free tier, then about USD 20 per month | As volume grows |
| Apple Developer / Google Play | USD 99 per year / USD 25 once | Mobile |
| Paddle | Per-transaction fee (confirm the current rate) | Revenue only |
| Logging, BigQuery, mirrors, Cloud Tasks | A few USD per month at low volume | P0/P1 |

The private-build total stays within the approved **about USD 57–93 per month** until launch-gate additions.

---

## 15 Changes to earlier documents

| Section | Change |
|---|---|
| v1.0 §10.2 | Verifier reads Cloud Storage projections, not Firestore |
| v1.0 §12, §9.1 | Intelligence is a Cloud Run service, not a Job |
| v1.0 §16–17 | Extended by §3, §6 and the retention schedule |
| Addendum 01 §2.3 | Static web becomes Next.js on Cloud Run behind Firebase Hosting; Intelligence becomes a service; adds Cloud Tasks and the ClamAV scanner |
| Addendum 01 §8 | Rewritten for the template layout: `backend/accord/*` (Python), `frontend/`, `docs-site/`, `mobile/`, `trust/` (Go), `contracts/`, `infra/` |
| Addendum 01 D-10 | Revised by D-33 (Python backend) |
| Addendum 02 G1 | Must accept native-app origins (iOS associated domains, Android asset links) |

## 16 Open items

| Item | Owner |
|---|---|
| Paddle onboarding of the Accord entity | Founder |
| GitHub organization name and owners | Founder |
| ~~Primary region~~ **Decided:** asia-southeast1, ADR-0017 | Founder |
| CSAM-matching service selection and legal duties | Counsel / Engineering |
| Retention periods confirmed by counsel | Counsel |
| Shamir custodians named | Founder |
