# ADR-0055 — Opt-in Google runtime and durable approved-reference jobs

Date: 2026-10-05. Status: Accepted for source preparation by the owner's S7 instruction;
cloud, identity/key configuration, migration/grants and judged acceptance remain owner-gated.

## Context

The approved prototype must demonstrate capture, private retrieval, grounded investigation and
production/passport integrity through meaningful Google integration. S2–S6 prepared adapters;
ordinary synchronous requests cannot establish restart-safe delivery. Provider cost, SQL result
integrity, task identity and measured recognition are different evidence.

## Decision

Assemble Google providers only when `PERSONA_GOOGLE_ENABLED` and explicit bounded JSON
`PERSONA_GOOGLE_CONFIG` accompany approved identity/photos, matching workspace, Cloud Run Linux,
an inspected-image provider and TLS Redis. Construction makes no network call or credential
discovery. Workload access uses the fixed Cloud Run metadata endpoint. Optional public signing
trust and a separate immutable signing key enable existing S6 behavior. No local private key,
ADC file, scaffold-token or model/calibration default is introduced.

KMS envelope wrapping protects existing encrypted originals, analysis derivatives, representations,
query cache and investigation packets with authenticated context and checked CRC32C. New writes
use the explicit primary wrapping version; old KMS aliases resolve only through reviewed retained
versions. Legacy Vault unwrap is optional and explicitly configured; unknown KMS aliases cannot
fall back to Vault. Key retirement needs retained-data/backup inventory and owner review.

Persist reference-only `persona_face_jobs` and append-only `persona_face_job_transitions` before
task creation. Migration 0015jobs freezes RLS, immutable rows and a SQL transition protocol.
Runtime grants are SELECT/INSERT only. Serialize each job with transaction advisory locks and
each persona's reference processing through existing Persona UPDATE privilege; portraits need
no new UPDATE grant. Task bodies contain workspace/job/dispatch IDs only, never pixels, actor,
model choice, key or bearer credentials. The stored verified-human intent supplies attribution.

Cloud Tasks uses deterministic names and explicit service-account OIDC for the fixed worker
origin. Verify RS256, fixed Google JWKS, issuer, audience, service email, pinned subject and times;
queue headers do not authorize. Recheck stored creator membership/reference and configuration
before processing, then membership/reference after provider/key work. Job success, encrypted
generation and server observations commit together. Committed result replay makes no provider
call. Configuration change or lost membership cancels old work; foreign task scope is denied.

Queue outages preserve committed intent. Authenticated reconciliation examines at most 20 queued
jobs with a 45-second dispatch budget. Explicit creator recovery uses expected sequence and a
new dispatch ID after failure, a two-minute stalled queue interval or expired 120-second lease.
Reserve ledger sequence space for dispatch, execution and final completion. Automatic execution
allows at most three attempts; worker processing has a 100-second overall deadline. A Task
ALREADY_EXISTS response observes dispatch only: executed/deleted task tombstones do not prove
completion. Cancellation serializes with work and cannot interrupt an existing provider call.

The assembled runtime routes persistent reference detection/selection through jobs. Transient
similarity queries retain their S4 ten-minute lifecycle; grounded investigation and passport
signing retain their existing bounded explicit requests. Configuration observations expose
capabilities to the studio without claiming live availability or benchmark acceptance.

## Consequences and validation

Source UI exposes cost confirmation, face selection, queue/history, CAS recovery/cancellation,
unknown-outcome identical retry, completed-result reload and configuration refresh. Internal
worker/reconciliation routes remain machine-only. Existing server-authored workflow/workspace
and portrait events provide emission/detection/audit/compliance coverage; clients supply no actor.

Crashes before SQL completion can repeat provider expense; this is bounded at-least-once
execution, not exactly-once billing. Durable job metadata has no purge service. Google detector
and multimodal image encoder remain candidates: unresolved publisher revision, absent reviewed
calibration or incompatible vectors cannot yield confident search. No face accuracy is inferred
from synthetic vectors or mocked HTTP. Actual corpus, SQL/RLS/concurrency, restart/lease recovery,
KMS/trust rotation, Google/IAM and rendered journey require separate acceptance evidence.
See [S7 implementation and rehearsal](../hackathon/google-runtime-slice.md).
