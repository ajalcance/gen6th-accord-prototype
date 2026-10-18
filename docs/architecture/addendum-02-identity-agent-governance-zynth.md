# Addendum 02 — Identity and AI Agent Governance (Zynth Auth)

| | |
|---|---|
| Amends | Architecture v1.0 and [Addendum 01](addendum-01-deployment-identity-trust.md) |
| Addendum version | 1.0 |
| Date | 23 September 2026 |
| Status | Approved, including the §6.3 cost. §6.2 (database) and §6.4 (availability) are approved by Accord, with the parts that depend on Zynth (D1, D2, D4, D5) **pending Zynth confirmation** |
| Companion | [Zynth requirements from Accord](../requirements/zynth-requirements-from-accord.md), the document to send to the Zynth team |

Accord uses **Zynth Auth** (Zynth Media Technology) for authentication, identity and AI-agent authority, and does not build these itself. Accord keeps everything that becomes part of a signed record.

**Zynth governs who may act. Accord governs what becomes part of the record.**

---

## 1 Decision register

| ID | Decision |
|---|---|
| D-12 | Zynth Auth is Accord's identity provider and agent-governance layer. Accord never builds its own login, session, MFA, SSO, SCIM or agent-credential system, and never adds a fallback login. |
| D-13 | Zynth is **self-hosted by Accord from day 0** in its own GCP project, at `id.gen6th.com`, with passkeys registered to the domain `gen6th.com`. The self-host licence runs from Zynth Media Technology to the Accord operating entity. |
| D-14 | Responsibilities are split as in §2: **offload**, **split** or **keep**. |
| D-15 | Mapping (§3): one Accord organization is one Zynth organization; each personal workspace is a personal Zynth organization; all people use Zynth's **workforce** population. |
| D-16 | **AI agents act on Accord only through the Zynth MCP tool gateway**, calling the Accord MCP server. No agent calls the Accord REST API directly. |
| D-17 | Zynth builds gaps G1–G6 (§7). **G1 blocks launch.** |
| D-18 | The Zynth host runs on the cheapest workable spec now and scales once there are users (§6.1). |
| D-19 | High availability is reached in stages on the **same** Zynth install. No second identity system is built (§6.4). |
| D-20 | The added identity cost (about USD 42–58 per month, for a private-build total of about USD 57–93) is **approved** (§6.3). |

---

## 2 Responsibility split

### 2.1 AI agent governance

| Capability | Decision | Owner detail |
|---|---|---|
| Agent identity: own credential, risk level and oversight band | Offload | Zynth |
| Accountable operator: authority only through a human delegation, never wider than the grantor, chain depth ≤ 3 | Offload | Zynth. Accord copies the agent, operator and delegation identifiers into signed manifests |
| Bounded delegations: scope, ≤ 30-day expiry, cascading revocation | Offload | Zynth |
| Task-scoped tokens: one purpose, a permission subset and a request budget | Offload | Zynth. Every Intelligence job run mints its own |
| Accord's own permission vocabulary (`accord:*`) and permission checks | Split | Zynth evaluates. Accord's policy packs decide which actions are consequential |
| Human approval of agent actions: single-use, bound to the exact action, humans only, no self-approval | Offload | Zynth (G5 extends it to Accord permissions) |
| Kill switch and the blast-radius write budget | Offload | Zynth. This is effective for Accord because of D-16 |
| MCP tool gateway and MCP authorization server | Offload | Zynth |
| Workload identity without stored secrets (GCP attestation), DPoP | Offload | Zynth. The Intelligence job on Cloud Run uses GCP attestation |
| Agent audit trail, detections, incidents | Offload | Zynth. Accord logs Zynth's audit-chain head in its transparency log (optional ask D10) |
| AI-governance evidence (EU AI Act Art. 14, ISO 42001, OWASP Agentic) | Offload | Zynth, for the agent layer |
| Undoing an agent's changes | Split | Zynth for its own state. Accord records are append-only and corrected by new records |
| Earned autonomy | Keep the rule | Never for signing, decisions or adverse outcomes. G6 supplies the mechanism for low-risk drafting only |
| **Human adoption of AI output into claims, reviews, decisions and manifests** | Keep | Accord, bound to the manifest digest (v1.0 §12.2). May ride the G6 approval ledger |
| **Model governance:** pinned models, prompt versions, structured output, permission-filtered retrieval, prompt-injection isolation, override metrics | Keep | Accord Intelligence |
| **Contribution and authorship:** semantic diff, CRediT, "AI never assigns authorship" | Keep | Accord |

### 2.2 Authentication and identity

| Capability | Decision | Owner detail |
|---|---|---|
| Passkeys, TOTP, magic links, Google and GitHub, password | Offload | Zynth |
| OIDC login for Accord web and apps | Offload | Accord is one platform client, installed in every organization (G3) |
| Global person with many memberships | Offload | Zynth user. Accord keeps its **own person ID**, mapped to the Zynth `sub` (§3) |
| Organizations, invitations, domain auto-join, organization admin roles | Offload | Zynth |
| Enterprise SSO (OIDC, SAML), SCIM, SSO-required with break-glass | Offload | Zynth |
| Sessions: rotation, reuse detection, instant revocation | Offload | Zynth |
| Step-up for signing, sealed evidence, key administration, destructive retention | Offload | Zynth step-up, plus G1 for signing |
| Integration credentials for the Accord API | Offload | Zynth: the Accord API is a registered OAuth resource with audience-bound tokens |
| Organization-level role- and attribute-based access, access requests, separation of duties, recertification | Offload | Zynth. This covers operator separation of duties (v1.0 §5.9) |
| **Project roles, object visibility, conflicts of interest, charter authority, sealed-evidence rules** | Keep | Accord policy packs, which are versioned and bound into signed records |
| Privacy for identity data: consent, data-subject requests, retention | Offload | Zynth |
| **Privacy for claims, evidence and records:** legal hold, records that can't be erased | Keep | Accord |
| Membership, agent and delegation events | Offload | Zynth webhooks (G4) |
| **Accord plans and billing** | Keep | Accord |

---

## 3 Identity mapping

| Accord concept | Zynth concept | Rule |
|---|---|---|
| Person | User (global) | Accord's control plane holds `person_id` → Zynth `sub`. **Signed records carry `person_id`, never the Zynth `sub`**, so the identity provider can be replaced without changing any record. |
| Organization | Organization (tenant) | 1:1. Accord keys on the Zynth `tid` (immutable), never the slug. |
| Personal workspace | Personal organization owned by the person | Created at sign-up. It is the person's home for their record wallet. |
| Organization membership and admin role | Membership and role | Zynth is the source of truth. Accord cells sync through G4 webhooks and check live through the permission API. |
| Project membership and project roles | — | Accord cell (kept). |
| AI agent | Agent in the owning organization | Registered and governed in Zynth. Accord copies identifiers into manifests. |
| Accord API | OAuth resource `https://accord.gen6th.com/api` with namespace `accord` | Audience-bound tokens. `accord:*` permissions are defined in Zynth. |
| Accord MCP server | Server registered in the Zynth MCP gateway | The only path agents have into Accord (D-16). |
| Population | `workforce` only | The `customer` population is not used: it can't hold admin roles and is fixed forever. |

This updates Addendum 01 §3.1. Credentials, passkeys and assurance live in Zynth. Accord's control plane keeps the person record, the Zynth mapping, passkey key bindings (logged, see §5) and the record wallet.

---

## 4 Agent access path (D-16)

1. An organization registers its agent in Zynth, and a human delegates it `mcp:call`, scoped to the `accord` server and specific tools.
2. The agent obtains a token: task-scoped, from GCP or GitHub attestation where available, with DPoP.
3. The agent calls `POST id.gen6th.com/api/v1/mcp/call/accord`. The gateway checks the allowlist, delegation scope, rate and write budgets, risk ceiling, attribute policies and human approval, then forwards the call.
4. The **Accord MCP server** (a new component in cell 1, Python) receives only gateway-forwarded calls, which it verifies by audience-bound token. It runs Accord's own domain checks, and the result lands in the Accord audit and outbox.
5. Accord's tools are declared in the gateway with a risk score and a `read_only` flag. Tools that change records (attach evidence, draft a claim, submit a contribution) are writes. **No tool can sign, decide, approve or publish.** Those actions exist only for humans.

The Accord REST API refuses tokens whose actor is an agent.

---

## 5 Signing with Zynth (updates Addendum 01 §5.1 step 3)

1. Accord computes the manifest digest and signing context and asks Zynth to open a **signing ceremony** (G1) bound to that digest.
2. The person completes the passkey ceremony, with user verification required.
3. Zynth returns the **raw WebAuthn assertion** and the credential's public key identifier.
4. **Accord Trust verifies the raw assertion itself** against the passkey key binding in Accord's transparency log. A statement from Zynth that the user passed is never accepted as the signature. A compromise of Zynth can therefore create sessions, but it cannot create signatures.
5. Passkey additions and removals arrive as G4 events and are appended to the transparency log as key bindings.

---

## 6 Deployment of Zynth

### 6.1 Host (day 0, cheapest workable)

| Item | Choice |
|---|---|
| Project | `gen6th-accord-identity-prod` (and `gen6th-accord-identity-nonprod`) |
| Region | asia-southeast1 (Singapore), the same region as Accord's Cloud SQL (ADR-0017) |
| VM | **e2-medium** (2 shared vCPU, 4 GB), Compute Engine, Container-Optimized OS or Debian. Move down to e2-small only if Zynth confirms the minimal profile fits 2 GB (D3) |
| Disk | 30 GB balanced persistent disk, daily snapshot schedule |
| Stack | Zynth self-host bundle in the **minimal profile**: API, workers, Redis, Caddy, frontend, egress proxy, backup sidecar. Bundled observability off. Alerts go to `COMMAND_ALERT_EMAIL` |
| Network | Only 443 open to the internet. SSH only through IAP. Zynth's egress allowlist stays default-deny |
| Nonprod | Same shape. The VM is **stopped when not in use**, so it costs only disk |
| Enabled flags | `AGENT_APPROVALS_ENABLED`, `MCP_GATEWAY_ENABLED`, `AGENT_FEDERATION_ENABLED`, `SSO_FEDERATION_ENABLED` (plan-gated for enterprise), `PUBLIC_SIGNUP_ENABLED` (at public launch). `AUTONOMY_EXECUTION_ENABLED` stays off until an operator decides |

### 6.2 Database (proposed — Zynth to confirm D1, D2)

**Recommended: a dedicated Cloud SQL for PostgreSQL instance for Zynth, in the identity project.**

| Option | Verdict |
|---|---|
| Bundled Postgres on the Zynth VM | Cheapest, but the database and application share one host and one failure. Kept only as a fallback if D1 or D2 cannot be met in time; moving to Cloud SQL later is a database move, not an ID change |
| A database on Accord's existing Cloud SQL instance | **Rejected.** The identity store would share a blast radius, administrators, maintenance windows and upgrades with application data |
| **Dedicated Cloud SQL instance** | **Recommended.** Identity is isolated from application data. Managed backups and point-in-time recovery, private IP only, CMEK-ready, and regional high availability is a setting change later |

Day 0 sizing: the smallest shared-core tier (`db-f1-micro`, 10 GB SSD, single zone), with automated backups and point-in-time recovery on. It is upgraded together with Accord's database at the first-customer launch gate (v1.0 §20.1): dedicated core and regional high availability.

- **Connection:** private IP, TLS `verify-full`.
- **Roles:** Zynth's migration role and its DML-only application role. The application role never owns tables and never bypasses row-level security.
- **Redis:** stays on the VM. Zynth to state what is lost if Redis is wiped (D4).

### 6.3 Cost (approved; estimates to be confirmed in the GCP pricing calculator)

| Item | Monthly |
|---|---|
| e2-medium VM, disk, snapshots, static IP | about USD 30–40 |
| Cloud SQL `db-f1-micro`, 10 GB, backups | about USD 11–15 |
| Backup bucket, egress | about USD 1–3 |
| **Identity total** | **about USD 42–58** |
| Accord baseline (Addendum 01) | about USD 15–35 |
| **Private-build total** | **about USD 57–93** |

### 6.4 Availability and backup plan (proposed — one install, staged)

**Stage A — day 0 (no customers)**

- **Self-healing single host.** A managed instance group of size 1 with a health check recreates the VM if it fails. The VM is stateless apart from Redis, because the database is Cloud SQL, so no second system is involved.
- **Rebuildable host.** The VM is defined only by Terraform, a startup script and the signed Zynth bundle. It is never hand-configured.
- **Secrets:**
  - The token-signing keys, `MFA_ENCRYPTION_KEY`, `JWT_SECRET_KEY` and the licence live in Secret Manager in the identity project and are mounted at boot.
  - The backup decryption (`age`) private key is kept **offline**, never on the server.
  - `MFA_ENCRYPTION_KEY` is treated as critical: losing it forces every TOTP user to enrol again.
- **Backups:**
  - Cloud SQL automated backups and point-in-time recovery, which give minutes of data-loss exposure.
  - A second copy: Zynth's sidecar writes encrypted logical dumps and Redis snapshots to a GCS bucket with a retention lock, in a separate backup project.
  - Daily disk snapshots.
- **Drills:** Zynth's `restore-drill.sh` and a Cloud SQL restore test, run quarterly.
- **Monitoring:** a GCP uptime check on `/.well-known/jwks.json` and the sign-in page, alerting by email.
- **Target:** recovery in about 15 minutes after a VM failure (auto-heal), or 1–2 hours for a full rebuild.

**Stage B — before the first external customer (launch gate)**

- Cloud SQL moves to a dedicated core with regional high availability.
- **Two Zynth hosts** in two zones behind a load balancer, with external Redis. This uses **Zynth's supported high-availability topology** (D5): API instances active/active and the audit-chain writer active/passive with fencing. It is still one Zynth install, now with two hosts.

**Stage C — enterprise**

- A cross-region Cloud SQL replica, backups in a second region, and a documented regional failover.

### 6.5 When identity is down (all stages)

| Function | Behaviour |
|---|---|
| Public verification (`/verify`, `/manifest`, open CLI) | **Unaffected.** It never depends on Zynth |
| Signed-in reading | Continues until the access token expires (about 15 minutes), then stops |
| Writes, signing, approvals, sealed evidence | **Fail closed**, with a maintenance banner. Nothing is queued for later signing |
| Agents | Stop, because the gateway is unavailable (fail closed) |
| Operator access to cloud infrastructure | Uses Google accounts with hardware keys, **never Zynth**, so an identity outage can't lock operators out of their own recovery tools |

---

## 7 Zynth gaps (built by Zynth)

| ID | Gap | Launch blocker |
|---|---|---|
| G1 | Verifiable signing ceremony: raw WebAuthn assertion over a caller-supplied digest, passkey public-key export, extra allowed origins **including native mobile-app origins** (Addendum 03 §4) | **Yes** |
| G2 | Organization switcher: choose or switch the active organization without a full re-login | Yes, for UX |
| G3 | Platform client installed by default in every organization on the instance | Yes |
| G4 | Webhooks: membership, organization, agent, delegation, passkey and erasure events | Yes |
| G5 | Permission check returns an approval obligation for agent principals on customer resource permissions | Before agent tools go live |
| G6 | General content-hash approval lane: approve exact bytes, outside the CMS | Before AI drafting goes live |

Detailed acceptance criteria and the deployment asks D1–D10 are in the [requirements document](../requirements/zynth-requirements-from-accord.md).

---

## 8 Changes to earlier documents

| Section | Change |
|---|---|
| v1.0 §9.1 deployables | Adds the Zynth host (identity project) and the Accord MCP server (cell 1) |
| v1.0 §9.3 projects | Adds `gen6th-accord-identity-prod` and `-nonprod`, plus a backup project |
| v1.0 §10.1 `identity` schema | Credentials, groups, service accounts, agents and delegations move to Zynth. Accord keeps `person` (with the Zynth mapping), key bindings and the record wallet in the control database |
| v1.0 §11 identity | Replaced by §2.2 and §3 |
| v1.0 §12.2 AI safety | Agent authority and oversight come from Zynth. Model governance stays in Accord |
| v1.0 §14.1 API credentials | Audience-bound OAuth tokens and API keys from Zynth |
| v1.0 §15.2 AI and agents threats | Covered by §2.1 and D-16 |
| v1.0 §19 cost | Updated by §6.3 |
| v1.0 §20.1 launch gates | Adds: G1–G4 delivered; Stage B availability; restore drill passed; an identity-outage drill shows public verification unaffected and writes failing closed |
| Addendum 01 §2.2 control plane | Accord Control no longer runs authentication. It holds the person mapping, key bindings, wallet, registries, cells and billing |
| Addendum 01 §3.1 | Updated by §3 (credentials in Zynth) |
| Addendum 01 §5.1 step 3 | Updated by §5 (Zynth ceremony, Accord verifies the raw assertion) |
| Addendum 01 §9.1 Stage 1 | Adds: Zynth self-host, the identity project, OIDC integration, person mapping, G3 and G4 integration |
| Addendum 01 §9.1 Stage 3–4 | Adds: Accord MCP server behind the gateway, `accord:*` permission vocabulary, G5 |

## 9 Open items

| Item | Owner |
|---|---|
| Zynth responses to D1–D10 and G1–G6 delivery dates | Zynth |
| ~~Region choice~~ **Decided:** asia-southeast1, ADR-0017 | Founder |
| Self-host licence and install ID for the Accord entity | Zynth / counsel |
| Monthly cost confirmation in the GCP calculator | Engineering |
