# ADR-0044: Inspected version-bound portraits

**Date:** 2026-10-04
**Status:** Proposed runtime activation; owner authorized photo feature implementation.
**Deciders:** Repository owner

## Context

The owner approved optional creation/editing photos. Private evidence requires an existing
version, expires after seven days and is owner-only; it cannot supply permanent workspace portraits.
A browser selection preview is not durable storage.

## Decision

Prepare inspected portrait metadata, encrypted original/thumbnail payloads and immutable version
bindings in migration 0010portraits. Authorize creator membership before bounded JSON/base64
consumption, preserving the cookie Origin/JSON/CSRF contract. Bind digest/length/media/request to
exact bytes. Scan the original, fully decode, generate fresh metadata-free PNG and scan the
derivative before committing AES-GCM ciphertext and context-bound wrapped keys.

Owner-approved Pillow 12.3.0 is installed. Workers require Linux address-space/CPU limits, wall
timeout and input/output/concurrency bounds. Mac memory-limit setup failed; unsupported workers
return unavailable. Direct real pixel tests and isolated worker availability are distinct proof.
Photo activation needs a bounded Linux runtime; the current Mac backend cannot enable its worker.

Use loopback clamd INSTREAM, definitions at most 48 hours old and unchanged around a scan, exact
complete verdicts and bounded requests/responses. Scanner timezone must be UTC. Use persistent
Vault Transit with an existing derived AES-256-GCM key, no export/plaintext backup/deletion.
The application token may read that key and update encrypt/decrypt, but cannot create keys.
Fresh object data keys use workspace/portrait/part/digest authenticated contexts. No plaintext,
default-key, clean-scan or platform-limit fallback exists.

Current workspace members read only a saved version's inspected thumbnail. Originals have no
browser route; committed read events precede plaintext return. Add/replace/remove creates a
new immutable version atomically; ordinary text edits keep its preceding portrait. Staged
attachments expire after 24 hours; keeping historical bindings remains permitted. Photo-free
commands preserve existing replay fingerprints.

## Retention and activation

Expiry is not deletion permission. Metadata, bindings and payloads are immutable; runtime has
no UPDATE/DELETE grants and no active purge worker. Abandoned stages and removed historical
images remain until a separately approved trusted retention/legal-hold policy and worker exist.
That cleanup is a registered prerequisite, not implemented retention proof.

Migration/grants, persistent providers, Linux worker runtime, backup/restart recovery, full SQL
gate and live photo acceptance remain owner/CI steps. Do not restart the connected backend on
this source before schema/grants validation. Each concrete package/container install needs owner
approval; no existing service or populated record is changed by preparing this code.

## Consequences and alternatives

Selections/receipts stay on a mounted session screen. Cancellation/failure retains text and exact
upload retry; late/mismatched receipts cannot attach. Saving needs checked upload plus confirmation.
Private card/detail thumbnails revoke object URLs on session changes/unmount; placeholders make
no inspection claim. Reject public URLs, browser-only persistence, evidence expiry reuse, mutable
old-version photos, client scan verdicts, dev Vault/default keys and removing worker memory limits.
