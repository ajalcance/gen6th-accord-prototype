# Zynth Auth — Requirements from Gen6th Accord

| | |
|---|---|
| From | Gen6th Accord |
| To | Zynth Media Technology (Zynth Auth team) |
| Date | 23 September 2026 |
| Context | Accord will self-host Zynth Auth as its identity provider and AI-agent governance layer ([Addendum 02](../architecture/addendum-02-identity-agent-governance-zynth.md)) |

## Summary

Accord is a trust product. People and organizations sign claims about their work, and anyone can verify those signatures later without trusting Accord. Accord will run Zynth self-hosted at `id.gen6th.com`, with passkeys registered to `gen6th.com`, on Google Cloud.

We need:
- six product capabilities (**G1–G6**);
- answers or small changes on ten deployment items (**D1–D10**).

**G1 blocks Accord's launch.** Please reply per item with one of: *already supported (how)*, *will build (date)*, or *not possible (why)*.

---

## Part 1 — Product capabilities

### G1 Verifiable signing ceremony (launch blocker)

**Why:** When a person signs an Accord record, the proof must be verifiable by third parties **without trusting Zynth or Accord**. A Zynth statement that the user passed step-up is not enough. We need the raw passkey assertion.

**Requirements**

1. An endpoint opens a ceremony for the signed-in user. It takes `purpose`, a `digest` (SHA-256, hex) and a `display_text`, and returns WebAuthn request options.
   - The `challenge` must be derived deterministically from the digest and publicly documented, e.g. `SHA-256("zynth-sign-v1" || purpose || digest)`, so a verifier can recompute it.
   - `userVerification: "required"`.
   - `allowCredentials` lists the user's passkeys.
2. A completion endpoint verifies the assertion and returns, **unaltered**: `authenticatorData`, `clientDataJSON`, `signature`, `credentialId`, `userHandle`. It also returns the credential public key (COSE and JWK), the user `sub`, `tid`, time and `amr`.
3. **Single use**, bound to the session, with a short expiry and a recent-authentication requirement like step-up.
4. The ceremony may be performed from `https://accord.gen6th.com` as well as `https://id.gen6th.com` (RP ID `gen6th.com`), **and from Accord's native iOS and Android apps**. We need **multiple allowed WebAuthn origins**, including native-app origins:
   - iOS: associated domains / `webcredentials`.
   - Android: the `android:apk-key-hash:` origin, through Digital Asset Links.

   We also need OIDC with PKCE for native apps through the system browser, with DPoP-bound tokens.
5. **Public key export:** list a user's passkey public keys with created and removed timestamps (for Accord's server, with an `accord`-scoped service credential).
6. Assertions without user verification are refused.

**Acceptance:** an independent script with only `clientDataJSON`, `authenticatorData`, `signature`, the public key and the original digest can verify the signature and recompute the challenge.

### G2 Organization switcher

**Why:** Accord users belong to a personal organization plus one or more company organizations. Today `/authorize` uses only the session's current organization, with no chooser.

**Requirements:**
- `/authorize` accepts an organization hint (by `tid`), **or** the session can switch to another of the user's memberships without a full re-login.
- A chooser page when the hint is absent and the user has more than one membership.
- The `id_token` carries the chosen `tid`.

### G3 Platform client installed by default

**Why:** On Accord's own instance, every organization must be able to sign in to Accord without its admin installing Accord first.

**Requirement:** an operator-level setting that marks a platform client as **installed in all organizations, existing and future**, with a fixed scope ceiling. Organization admins cannot withdraw it.

### G4 Webhooks for membership, agents and keys

**Why:** Accord's data cells mirror organization membership and must log passkey key changes.

**Requirement:** add these events, with the same signing and retry contract as today:
- `tenant.created`, `tenant.deleted`
- `member.joined`, `member.removed`, `member.role_changed`
- `agent.registered`, `agent.updated`, `agent.killed`, `agent.released`, `agent.retired`
- `delegation.created`, `delegation.revoked`
- `passkey.added`, `passkey.removed` (with the public key)
- `user.erased`

An instance-level subscription covering all organizations is preferred.

### G5 Approval obligations from the permission check

**Why:** Agents act on Accord through the MCP gateway. Some Accord tools need a human approval under the agent's oversight mode.

**Requirement:** when `POST /authz/service-check` evaluates an **agent** principal on a customer resource permission (`accord:*`), and the agent's band or delegation requires human approval, the answer includes an `approval_required` obligation with an `approval_request_id`. The request is bound to a fingerprint of the permission plus a caller-supplied `context_digest`. The existing ledger rules apply unchanged: single use, humans only, no self-approval, and the approver must hold the permission. A consume call lets Accord spend the approval once.

### G6 General content-hash approval lane

**Why:** Accord requires a person to explicitly accept an AI draft before it can enter a signed record. Zynth already does this for CMS posts.

**Requirement:** generalize `/approvals/content` beyond the CMS store. An agent or service requests approval for any `{resource_type, content_hash, summary, preview_url}`. Humans decide with a reason. Accord consumes the approval by hash, once. Feedback and the track-record endpoints work the same way.

---

## Part 2 — Deployment items

| ID | Ask | Why |
|---|---|---|
| D1 | **External managed Postgres**: support Cloud SQL for PostgreSQL (16 or 17) over private IP with TLS `verify-full`, through a supported compose profile that removes the bundled Postgres container **without editing the compose file**. | Identity data on a managed, backed-up, HA-capable database separate from the application host |
| D2 | **Bootstrap and migrations without SUPERUSER**. Cloud SQL provides `cloudsqlsuperuser`, not SUPERUSER. Please document the exact role attributes needed, and confirm the application role neither owns tables nor has `BYPASSRLS`, so row-level security stays enforced. | Required for D1 |
| D3 | **Minimal footprint profile**: a supported way to run without the docs-internal, `zynth-web`, `marketing` and bundled observability containers. Please also publish the minimum RAM and CPU. Target: fits in 4 GB, ideally 2 GB. | Cheapest host at day 0 |
| D4 | **Redis semantics**: what is lost if Redis is wiped (sessions? rate limits? pending approvals?), and is an external Redis (Memorystore) supported? | Recovery planning, and Stage B high availability |
| D5 | **Supported HA topology**: two hosts behind a load balancer sharing external Postgres and Redis; API active/active; background workers (the sole audit-chain writer) active/passive with leader election or fencing; a health endpoint suitable for a load balancer and instance-group auto-healing. | Required before Accord's first external customer. Must be one install, not two identity systems |
| D6 | **Backups with external Postgres**: the sidecar backs up Redis and optional encrypted (`age`) logical dumps to **GCS through its S3-compatible API** (HMAC keys). `restore-drill.sh` works against Cloud SQL. | A second copy outside Cloud SQL's own backups |
| D7 | **Secrets from files populated at boot** from Google Secret Manager (signing keys, `MFA_ENCRYPTION_KEY`, `JWT_SECRET_KEY`, licence). Please confirm there is no requirement for secrets in the env file itself. | Rebuildable host with no secrets on disk images |
| D8 | **Self-host licence** for the Accord operating entity, with an install ID, covering production. Enterprise-tier entitlements are needed for SSO/SAML, SCIM, access governance and the MCP gateway. | Commercial prerequisite |
| D9 | **Nonprod instance** under the same licence, which may be stopped when idle. | Test environment |
| D10 *(optional)* | **Audit-chain head export**: an endpoint returning the current audit-chain head hash and sequence, signed, for an operator credential. | Accord appends it to its public transparency log, so Zynth's audit chain gains independent witnessing |

---

## Part 3 — How Accord will use Zynth (for context)

- **Identity mapping:**
  - Each Accord organization is one Zynth organization, and each person also has a personal organization.
  - All users are **workforce** population.
  - Accord keeps its own person ID, mapped to the Zynth `sub`.
- **Login:** Accord is a platform OIDC client (G3), and uses G2 for switching between organizations.
- **Agents:** agents reach Accord **only** through the Zynth MCP gateway, calling a registered `accord` MCP server. The Accord API is a registered OAuth resource with an `accord:*` permission namespace.
- **Signing:** signing uses G1. Accord verifies the raw assertion itself and logs passkey key bindings in its public transparency log.
- **Enabled flags:** `AGENT_APPROVALS_ENABLED`, `MCP_GATEWAY_ENABLED`, `AGENT_FEDERATION_ENABLED`, `SSO_FEDERATION_ENABLED`, and `PUBLIC_SIGNUP_ENABLED` at public launch. `AUTONOMY_EXECUTION_ENABLED` stays off.
- **Hosting:** GCP Compute Engine (e2-medium), a dedicated Cloud SQL instance, in asia-southeast1 (Singapore).
