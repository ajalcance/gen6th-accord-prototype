# Gen6th Accord — Architecture

This page is the **current design at a glance**. It combines the baseline and every approved addendum. The full detail is in the source documents below. Where a source document and this page disagree, the source document wins and this page must be corrected.

## Source documents

Read in order. A later document overrides an earlier one where they conflict.

| # | Document | Status |
|---|---|---|
| — | Gen6th Founding Paper v1 (private document, not published) | The principles Accord puts into practice |
| 0 | Commercial Product and Technical Architecture v1.0 (private document, not published) | Baseline |
| 1 | [Addendum 01 — Deployment, Identity and Trust](addendum-01-deployment-identity-trust.md) | Approved 23 September 2026. Revised to match Addendum 02 |
| 2 | [Addendum 02 — Identity and AI Agent Governance (Zynth Auth)](addendum-02-identity-agent-governance-zynth.md) | Approved 23 September 2026. Zynth-dependent items are pending Zynth confirmation |
| 3 | [Addendum 03 — Operations, Data Lifecycle, Security and Mobile](addendum-03-operations-data-security-mobile.md) | Approved 23 September 2026, including §12 (engineering baseline, Python backend) |
| — | [Retention schedule](retention-schedule.md) | Draft for counsel review |

Requests to other teams: [Zynth requirements from Accord](../requirements/zynth-requirements-from-accord.md).

---

## What Accord is

Accord is accountability infrastructure for work made by people, institutions and AI agents. It has three domains in one product:
- **Collab:** governed work, contributions, reviews and releases.
- **Claims:** typed assertions, evidence, disputes and appeals.
- **Trust:** signing, a transparency log and public verification.

Accord records who asserted what, about which version, with what evidence, and who approved it. **It never decides truth or legal ownership.**

**Immediate implementation track:** [AI Persona Passport](../hackathon/prototype-plan.md),
selected in [ADR-0023](../decisions/0023-ai-persona-passport-prototype.md). This bounded
hackathon application uses persona creation and campaign authorization claims. Its initial
platform signature does not represent the complete launch assurance described below.
H1's fixture UI is accepted by the owner; H2's internal fixture persistence is under
database validation ([ADR-0024](../decisions/0024-persona-transactional-persistence.md)).
The owner reported the earlier storage target passing; internal review/campaign slices
([ADR-0025](../decisions/0025-version-bound-human-review.md),
[ADR-0026](../decisions/0026-scoped-campaign-permission.md)) need fresh SQL proof.
Zynth repository work is deferred; no persona routes or alternative identity are activated.

## Who does what

| Layer | Owner |
|---|---|
| Login, sessions, MFA, passkeys, SSO/SCIM, organizations and memberships | **Zynth Auth**, self-hosted by Accord |
| AI agent identity, delegated authority, approvals, kill switch, MCP gateway | **Zynth Auth** |
| Person registry, key bindings, record wallet, cells, registries, billing | **Accord Control** (control plane) |
| Projects, claims, evidence, cases, project roles, policy packs, AI-draft adoption, model governance | **Accord cells** (data plane) |
| Platform signing, transparency log, time anchoring | **Accord Trust** |
| Verification | **Anyone**: the open verifier library and CLI, or Accord's public verify page, which runs the checks in the visitor's browser |
| Web and mobile clients | Next.js BFF on Cloud Run (tokens never in browser JavaScript); iOS and Android apps with Expo / React Native |
| Languages | **Python (FastAPI)** backend; **Go** for Trust and the reference verifier; **TypeScript** for web, mobile and the browser verifier |
| Engineering baseline | The `zynth-setup` Copier template, followed closely: its AI contract, ADRs, standards, CI gates, compliance spine and release chain. Adapted for Cloud Run, Pub/Sub, Postgres tests, Go and mobile (Addendum 03 §12) |
| Email, billing, status | Resend; Paddle as merchant of record (PayPal inside checkout; direct PayPal as fallback); hosted status page outside GCP |

Zynth governs **who may act**. Accord governs **what becomes part of the record**.

## Deployment model

- **Tiers:**
  - Accord Cloud (individuals and teams, shared cell).
  - Accord Cloud Enterprise (dedicated cell, customer-managed keys, SSO).
  - Accord Hybrid (a cell in the customer's cloud).
  - Self-hosted (deferred).
- **Control plane and cells.** Accord always operates the control plane, identity and Trust. Tenant data lives in cells. The managed service is itself cell 1, so hybrid later is packaging, not a refactor.
- **Agents** act on Accord **only** through the Zynth MCP gateway, which calls the Accord MCP server. They never call the REST API.
- **Personal data stays outside the hash.** Signed records hold pseudonymous IDs and salted commitments, so erasure crypto-shreds a separate personal-data layer while every signature stays valid.

## Signing and verification

1. The person signs with their passkey through the Zynth signing ceremony. **Accord Trust verifies the raw assertion itself.**
2. Accord signs as the platform using Cloud KMS.
3. The transparency log records the digest, and the record gets an inclusion receipt.
4. Checkpoints are anchored hourly with **OpenTimestamps** (from day 0).
5. External witnesses are built and open but **switched off** until the first paying customer or the first real dispute.
6. Records are verified under the policy that was in force when they were issued. Public labels are honest about the witnessing phase.

## Google Cloud projects

| Project | Contents |
|---|---|
| `gen6th-accord-prod` | Web and BFF, Accord Control, cell 1 (Core, Intelligence, MCP server, upload scanner), Public Verifier, Cloud SQL (`control` + `cell_01`), cell and `public-projections` buckets |
| `gen6th-accord-trust-prod` | Trust Signer, Trust Log, Anchor Job, KMS, log storage |
| `gen6th-accord-identity-prod` | Zynth Auth host (auto-healing instance group of size 1), dedicated Cloud SQL, Secret Manager |
| Backup project | Retention-locked bucket for Zynth backups |
| `gen6th-accord-nonprod`, `gen6th-accord-identity-nonprod` | Development and staging. The Zynth test VM is stopped when not in use |
| Region | **asia-southeast1 (Singapore)** for every project (ADR-0017) |

## Deployables (day 0)

| Deployable | Language | Runtime |
|---|---|---|
| Web app and BFF (Next.js) | TS | Cloud Run behind Firebase Hosting at day 0; load balancer and Cloud Armor at launch |
| Accord Control | Python | Cloud Run, scales to zero |
| Accord Core (cell 1) | Python | Cloud Run, scales to zero |
| Accord Intelligence | Python | Cloud Run service, fed by Pub/Sub push |
| Upload scanner | — | Cloud Run (ClamAV) |
| Timers and sweeps | — | Cloud Tasks, Cloud Scheduler |
| Mobile apps | TS | Expo / React Native (iOS, Android) |
| Accord MCP server | Python | Cloud Run, scales to zero, reachable only through the Zynth gateway |
| Trust Signer, Trust Log | Go | Private Cloud Run, scales to zero (the log has a single writer) |
| Anchor Job | Go | Cloud Run Job, scheduled |
| Public Verifier | Go | Public Cloud Run, scales to zero |
| Zynth Auth | vendor bundle | Compute Engine e2-medium, always on |
| PostgreSQL | — | Accord: one Cloud SQL instance with two databases. Zynth: its own Cloud SQL instance |
| Witness | Go | Built, not deployed |

## Cost (approved, private build, estimates)

| Part | Monthly |
|---|---|
| Accord services and database (scale to zero, OpenTimestamps free) | about USD 15–35 |
| Zynth identity host, database and backups | about USD 42–58 |
| **Total** | **about USD 57–93** |

Confirm in the GCP pricing calculator before provisioning. Costs rise at the first-customer gate: regional high-availability databases, two Zynth hosts, and the load balancer with Cloud Armor (about USD 20–25). Mobile adds USD 99 per year (Apple) and USD 25 once (Google).

## Availability

- **Stage A (now):**
  - The Zynth VM heals itself and can be rebuilt from Terraform.
  - Secrets are in Secret Manager.
  - Backups: Cloud SQL point-in-time recovery, an encrypted copy in a retention-locked bucket, and disk snapshots.
  - Restore drills run quarterly.
- **Stage B (before the first customer):** regional high-availability databases and two Zynth hosts. This is still one Zynth install.
- **Stage C (enterprise):** cross-region recovery.
- **While identity is down:** public verification keeps working, writes and signing fail closed, and agents stop. Operators reach Google Cloud without depending on Zynth.

## Open source

**Open at launch:**
- spec (CC BY 4.0)
- Go and TypeScript verifiers, transparency log, witness, anchoring (Apache-2.0)
- test vectors (CC0)

**Commercial:** the workflow product, Intelligence, connectors, enterprise features and hosting. A Gen6th Foundation may later take custody of the spec, the log and the appeal roster.

## Build stages

| Stage | Focus |
|---|---|
| 0 | Repository from `zynth-setup` (Python backend, Next.js frontend, docs site, spine, release chain) plus Go, mobile and Terraform modules, GitHub and GCP organizations, org policies, CI/CD with Workload Identity Federation and Binary Authorization, threat model, ADRs |
| 1 | Platform foundation: control/cell split, Zynth self-hosted, OIDC, person registry, personal-data layer, OpenTelemetry and log classes, bucket layout, outbox and timers, fingerprints |
| 2 | Collab core: formats, charters, cross-organization projects |
| 3 | Contribution and review: Accord MCP server behind the gateway, agent approvals, AI-draft adoption |
| 4 | Claims core: passkey signing ceremony, record wallet |
| 5 | Trust and verification: transparency log, OpenTimestamps, verifiers, test vectors, mirrors, independent log monitor; **mobile MVP ships** |
| 6 | Disputes and appeals |
| 7 | Specialized formats |
| 8 | Commercial hardening: Paddle, status page, Cloud Armor, VPC Service Controls, penetration test, content safety, Data Privacy Act operations, SLOs, launch gates |
| 9 | Triggered: hybrid packaging, witness activation |

## Observability, storage and retention

- **Observability:** OpenTelemetry in Python, TypeScript and Go, and Google Cloud's logging, monitoring and trace tools. Four log classes (application 30 days, security 1 year, cloud audit 400 days plus archive, domain audit per schedule). Service-level objectives for signing, outbox, checkpoints, anchors and notices. External synthetic probes and an independent log monitor from day 0.
- **Storage:** fixed buckets per cell (quarantine, artifacts, restricted, sealed, exports), plus control-plane `public-projections`, trust `log-tiles`/`anchors`, `security-archive` and `backups`. Content-addressed objects, deduplicated within a tenant only. The log and public projections are mirrored to a second provider.
- **Retention:** every data class has a period and deletion method in the [retention schedule](retention-schedule.md).

## Open items

- Zynth replies to G1–G6 and D1–D10. G1 blocks launch.
- Paddle onboarding of the Accord entity; GitHub organization; Shamir custodians; CSAM-matching service; retention periods confirmed by counsel.
- Legal weight of passkey signatures.
- Pricing and packaging.
- IP rights registration research (deferred).
- Capture plugins for creative and developer tools.
- Tessera storage backends and the OpenTimestamps client library.
- Foundation structure.
