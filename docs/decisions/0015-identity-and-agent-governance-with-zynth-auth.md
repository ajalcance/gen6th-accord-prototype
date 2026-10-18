# 0015. Identity and AI-agent governance through self-hosted Zynth Auth

- **Status:** Accepted (Zynth-dependent items pending Zynth confirmation)
- **Date:** 2026-09-23
- **Deciders:** Albert Alcance (founder)

## Context

Accord needs enterprise authentication (passkeys, MFA, SSO, SCIM) and governance for AI agents acting on people's behalf. The founder owns Zynth Auth, which provides both. Building these again inside Accord would duplicate a security-critical system. Full reasoning: [Addendum 02](../architecture/addendum-02-identity-agent-governance-zynth.md). Requests to Zynth: [requirements](../requirements/zynth-requirements-from-accord.md).

## Decision

| ID | Decision |
|---|---|
| D-12 | Zynth Auth is Accord's identity provider and agent-governance layer. Accord never builds its own login, and never adds a fallback login |
| D-13 | Zynth is self-hosted by Accord from day 0 at `id.gen6th.com`, with passkeys registered to `gen6th.com`, under a licence from Zynth Media Technology |
| D-14 | Responsibilities are split as offload, split or keep. Zynth governs **who may act**; Accord governs **what becomes part of the record** |
| D-15 | One Accord organization is one Zynth organization; personal workspaces are personal Zynth organizations; workforce population only. Signed records carry Accord's `person_id`, never the Zynth `sub` |
| D-16 | AI agents act on Accord only through the Zynth MCP gateway and the Accord MCP server. No agent calls the REST API. No agent tool can sign, decide, approve or publish |
| D-17 | Zynth builds gaps G1–G6. G1 (a verifiable signing ceremony) blocks launch |
| D-18 | The Zynth host starts on the cheapest workable spec (e2-medium) |
| D-19 | High availability is reached in stages on the same Zynth install |
| D-20 | The added cost (about USD 42–58 per month) is approved |

## Consequences

- Accord Trust verifies the **raw passkey assertion** itself, so a compromise of Zynth cannot create signatures.
- During an identity outage, public verification keeps working and every write fails closed. Operators reach GCP without Zynth.
- Launch depends on Zynth delivering G1–G4.

## Alternatives considered

- **Managed Zynth SaaS.** Rejected: passkeys would belong to `zynthmedia.com`, so moving later would force every user to re-enrol and would change identities underneath signed records. Key custody would also sit with a vendor.
- **Build identity in Accord.** Rejected: it duplicates Zynth and adds a second security-critical system.
