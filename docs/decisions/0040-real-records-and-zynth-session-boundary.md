# 0040. Real records and a Zynth session boundary

- **Status:** Proposed for owner PR review; implemented locally under approved steps 1–3
- **Date:** 2026-10-04
- **Deciders:** Repository owner

## Context

The owner removed sample workflows and authorized real database/session/read integration.
The prior fixture-only schema and HMAC scaffold cannot establish real identity or records.
Zynth's OIDC guide, token guide and actual UserInfo implementation were inspected read-only.

## Decision

1. Remove fixture flags from active contracts/models and rename the asset table. Migration
   0008 refuses populated prior history, under an all-tenant migration role; it never deletes
   examples or silently reclassifies them. Revision/ordinal, immutable-history, digest,
   independent-party and forced tenant RLS protections remain. Historical migrations stay frozen.
2. Use an organization-specific confidential client, code + S256 PKCE, exact callback, state,
   nonce, RS256 signatures and at_hash. ID tokens pin the HTTPS OIDC issuer/client audience;
   access tokens pin `zynth-auth`, `zynth-services`, type and client ID. No alternate audience,
   HMAC fallback, machine actor or DPoP credential is accepted by this initial human profile.
3. Check UserInfo on every authenticated request. Platform audience is deliberate because
   resource-bound tokens cannot call UserInfo. Resolve issuer/tenant/subject through immutable
   server-managed bindings to canonical Accord identities, then recheck stored membership.
   Login does not provision accounts or infer roles. Migration 0009 and the owner-terminal
   provisioning module commit membership, binding and an attributed system observation together.
4. Keep tokens in encrypted, expiring Redis storage; browser cookies contain only opaque
   HttpOnly handles. Exact Origin and JSON content type protect cookie-authenticated writes;
   no credential-bearing cross-origin transport is added. Callback state is consumed once and
   token exchange is never retried. Auth responses are private/no-store; access-query logging is off.
5. Mount real record/auth routes; absent configuration denies requests. Startup refuses a
   superuser/BYPASSRLS/table-owning runtime or membership/binding mutation privilege. Operator
   migration/provisioning credentials stay separate from runtime credentials.
   A scoped security-definer role-read function preserves membership row locks without granting
   runtime membership updates. It requires matching transaction workspace context, selects only
   that workspace/actor, has a fixed search path, and revokes default public execution.
6. Frontend configuration enables same-origin session discovery, validated saved reads and
   explicit existing-record writes. The default remains empty and disconnected. Create-persona
   UI, asset intake, evidence providers, AI, signing and publication are later work.

## Consequences

Redis/UserInfo/identity-resolution failure denies access. This profile requests `openid` only,
does not refresh tokens, and ends the local Accord session on logout; it does not end the global
Zynth session or implement back-channel logout. New login follows token expiry. Historical
immutable bindings need a separately reviewed membership revocation/reassignment lifecycle.
Automated fault data stays in tests; no test provider is imported as an application fallback.
Live SQL, provider configuration and authenticated browser acceptance remain required.
Workspace provisioning observations use `workspace.membership_provisioned`; they and auth
transitions have catalogue decisions but no new live detection-delivery path in this slice.
See [the integration runbook](../runbooks/zynth-local-integration.md) for precise owner steps.

## Alternatives considered

Relabelled examples and scaffold identities were rejected. A public SPA client would expose
tokens to the browser. Resource-bound tokens require a different revocation design. The local
private TypeScript SDK verifies tokens but does not provide this confidential Python login flow;
no package was installed. This bounded implementation requires security review before live use.
