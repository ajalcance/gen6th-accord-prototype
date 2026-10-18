# ADR-0031: Internal encrypted evidence quarantine

**Status:** Proposed; owner authorized implementation and cryptography 50.0.2 installation
on 2026-10-02. PR/security review and runtime activation remain pending.
**Date:** 2026-10-02
**Builds on:** ADR-0024 and Addendum 03 upload/retention boundaries.

## Context

Persona campaign assets are server-seeded fixtures, not uploaded evidence. The owner approved
secure evidence preparation before connecting the frontend. No trusted identity, scanner,
key-management provider or legal-hold service is activated. These omissions must not become
default-allow implementations.

## Decision

- Keep private intake separate from `persona_fixture_assets`; never treat a clean inspection
  as permission to use an asset, proof of originality or a campaign binding.
- Internal intake accepts bounded PNG/JPEG/plain-text declarations, up to 10 MiB. It authorizes
  the current version's creator before consuming a bounded/time-limited stream, checks exact
  size and SHA-256, and never retains or uses a client filename/path.
- Encrypt each object with a fresh 256-bit AES-GCM data key and 96-bit nonce. Bind workspace,
  version, evidence ID and content digest as authenticated context. An injected key wrapper
  must authenticate that same context; no production key loader or fallback key is supplied.
  Use the maintained, owner-approved `cryptography==50.0.2`, not custom cryptography.
- Store bounded ciphertext in PostgreSQL for this internal slice. This makes metadata, encrypted
  payload and the server intake event one transaction. Object storage and its cross-system
  commit/reconciliation protocol are a later reviewed adapter, not secretly activated here.
- Keep evidence metadata and inspection decisions immutable. Encrypted payloads have their
  own table and deletion lifecycle; metadata remains for provenance. Migration 0007 and
  metadata-created test schemas install forced tenant RLS and immutable/expiry triggers.
- A mandatory injected inspector must perform bounded full media decoding and malware
  inspection using current definitions. Verify its result against the exact digest, size,
  type and times. Missing/unavailable/mismatched inspection leaves quarantine closed. No
  production inspector is supplied, and test doubles explicitly identify themselves as such.
- Owner reads require a clean inspection, current membership and unexpired payload. Decrypt
  only after authorization and commit the read event before releasing bytes. No public URL,
  download endpoint, reviewer-sharing grant or browser upload is enabled.
- This remains **temporary quarantine**, even after clean inspection: seven-day access expiry.
  It is not promoted restricted/sealed evidence. Promotion needs the applicable tenant/case
  retention and hold policy; the existing retention schedule is unchanged.
- Explicit purge requires expiry and an injected affirmative legal-hold/retention decision.
  No default decision or automatic cleanup worker is installed. Activation must include the
  reviewed retention provider and worker; expiry of access alone does not prove deletion.
- Intake/inspection/read/purge have server events and explicit detection, audit and compliance
  registration. Client assertions never enter the server audit chain as observations.

## Verification and remaining gates

Real AES-GCM tests cover fresh encryption, round trip, altered ciphertext/nonce/wrapped key,
wrong context/key, and unavailable wrapping. Contract tests cover bounds and false authority.
PostgreSQL tests cover transaction/authorization/replay/inspection behavior and retention;
they require owner/CI execution. Offline DDL rendering is supplemental evidence only.

Before live use: trusted session adapter, real bounded decoder/malware inspector with current
definitions, key-provider access/rotation/recovery, legal holds and retention worker, quotas,
authenticated routes, full audit gates and source-bound database verification. Synthetic data
only until those gates are resolved. No cloud activation, signing or publication follows here.
