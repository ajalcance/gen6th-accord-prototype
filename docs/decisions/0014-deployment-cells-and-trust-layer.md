# 0014. Hybrid-ready deployment, global identity and the trust layer

- **Status:** Accepted (D-10 revised by ADR-0016 D-33)
- **Date:** 2026-09-23
- **Deciders:** Albert Alcance (founder)

## Context

Accord must serve individuals, teams, enterprises and regulated customers who keep data in their own cloud, without a later re-architecture. Its records must be verifiable by anyone, including against Accord itself, and must be useful in copyright and authorship disputes. Full reasoning: [Addendum 01](../architecture/addendum-01-deployment-identity-trust.md).

## Decision

| ID | Decision |
|---|---|
| D-01 | Hybrid-ready from day one: an Accord-operated control plane and data-plane **cells**. The managed service is cell 1 |
| D-02 | Tiers: Accord Cloud, Cloud Enterprise, Hybrid, and Self-hosted (deferred). Individuals are always managed |
| D-03 | A person's identity is global (control plane). Tenants hold memberships. People keep portable proof of their own signed records |
| D-04 | Cross-organization projects are core scope. Each party's evidence stays in its own tenant and cell |
| D-05 | Two-layer signing: the claimant attests with a passkey (and optionally an organization key); Accord signs as the platform; the log records the digest |
| D-06 | A transparency log (C2SP checkpoint and tile formats) runs from the first record |
| D-07 | Witness software is built and open from day 0. External witnesses are activated by trigger |
| D-08 | OpenTimestamps anchoring from day 0 |
| D-09 | Spec, verifiers, log and witness software are open source at launch (`accord-open`). The workflow product is commercial |
| D-10 | Languages. *Revised by D-33:* Python (FastAPI) backend, Go for Trust and the verifier, TypeScript for web, mobile and the browser verifier |
| D-11 | IP rights registration is a research item for later |

## Consequences

- Cells talk to the control plane only through a versioned API. Record IDs resolve independently of cells. Tenant data keys make CMEK a configuration change.
- Trust services live in a separate GCP project. The log is single-writer and outside the application project's write access.
- Every record is labelled honestly for its witnessing phase and verified under the policy in force when it was issued.

## Alternatives considered

- **Managed-only SaaS, like Slack.** Rejected: regulated and sealed-evidence customers need hybrid, and retrofitting it would be a rewrite.
- **Platform-key-only signing.** Rejected: it proves Accord recorded an approval, not that the person signed.
- **No witnesses or anchoring until there are users.** Rejected for anchoring: records made before activation would lack independent time proof.
