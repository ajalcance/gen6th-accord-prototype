# ADR-0053: Grounded investigation history

- Status: Proposed for human PR review; S5 source prepared under the approved slice plan
- Date: 2026-10-05
- Supersedes: None; builds on ADRs 0048–0052 and exact-version independent review

## Context

Studios need to investigate supplied appearances of continuing synthetic performers. A browser
search result is not trusted evidence, a visual observation is not an identity verdict, and a
model cannot issue production permission. S4 queries expire without enrollment; investigation
needs explicit retention of findings and provenance while preserving that image lifecycle.

## Decision

Expose a default-unavailable injected investigation runtime in the photo router. A verified
human studio member chooses a search candidate, supplies attributed source context and explicitly
requests retained findings. The server refreshes the S4 search from the actor-bound inspected
query, exact approved reference/latest generation and reviewed calibration. It refuses a selected
version/reference/generation absent from the fresh candidates. Browser scores, findings, actor
and scan claims are never accepted. Original uploads and source context are not sent to Gemini.

Gemini compares the two metadata-free analysis images and selected face boxes. No tool, URL
fetch or web grounding is configured. Images are untrusted data, including embedded instructions.
An allowlisted schema permits neutral visual comparison labels with both image citations or an
explicit insufficient-evidence abstention. No free-form conclusion, probability, inferred trait,
ownership, consent, copying, misuse, infringement or clearance label is accepted. Mandatory
identity/rights/source-context gaps are server-authored and cannot be removed by the provider.
This checks structure and available sources; it does not prove the model's observation is correct.

The Vertex REST adapter requires explicit project/region/model and injected workload tokens,
records the observed modelVersion, and reuses the bounded no-redirect Google transport. Safety
refusal, incomplete output, invalid citations, unsupported fields or malformed results fail closed.
Configuration readiness is distinct from real key/provider/SQL acceptance. No live call or default
model/key selection is activated by source work. Official wire references:
[structured output](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/samples/generativeaionvertexai-gemini-controlled-generation-response-schema-2),
[response contract](https://cloud.google.com/vertex-ai/generative-ai/docs/reference/rest/v1/GenerateContentResponse).

Persist encrypted bounded findings, selected query/reference digests, boxes, fresh search method,
policy/evidence digest, raw cosines, exact version/generation, source note, trusted actor, timestamp
and observed model revision. Store no supplied image, original, vector or other candidate's record
in this history. AES-GCM wrapping context includes immutable row identity and intent fingerprint.
Migration 0013investigation forces RLS, composite approved-reference binding and immutable rows;
reviewed runtime grants are SELECT/INSERT only. These are prepared, not applied.

Serialize exact-version history on the existing persona lock. Same-actor request replay returns
the committed packet after fresh authorization even after query expiry/provider withdrawal;
changed intent conflicts. Recheck membership, query openness, calibration and catalogue after
model/key work before committing findings and a server-attributed observation atomically. History
is exact-version, newest-first, 20 rows plus a bounded cursor, with authorization before decryption
and again before disclosure. A precommit failure may repeat provider cost; durable S7 dispatch
and reconciliation remain outstanding. No automatic retry or deletion/retention-erasure claim.

Save internal exact-version review requests linked by workspace/version/analysis composite FK.
New requests require the current version and an authorized existing analysis; same-actor intent
replay is immutable, changed evidence conflicts, and request history is bounded newest-first.
Migration 0013 also forces RLS and immutability on `persona_investigation_review_requests`.
Requests contain only trusted attribution, identifiers, ordinal and timestamp; no source pixels,
model text or notification. Request/history reads need current membership, without model/key calls.
Atomic observations record the saved handoff. A historical requested receipt is not a current
pending/approved state. Existing independent review/history owns decisions; the UI instructs
reviewers to cite the analysis ID. Reviewer permissions, self-review denial, current-version checks
and decision ordering stay server-enforced. Analysis and review requests do not approve production use.

## Consequences and acceptance

Explicit retained provenance includes query digests/boxes even after ephemeral pixels disappear.
History remains encrypted and immutable with no new purge route; review retention, lawful access,
provider policy and key lifecycle before activation. Historical review may require a new current
version under the existing review contract. This source slice does not implement web discovery,
verified posting context, automated misuse classification or signature issuance.

Negative tests cover unsupported output, binding/intent conflicts, authorization loss, query clear,
catalogue changes, provider failures, retry, encrypted history and frontend states. PostgreSQL
execution, actual Gemini quality/refusal behavior, rendered acceptance and source-bound PR/CI
remain separate gates. See [S5 implementation and evidence](../hackathon/grounded-investigation-slice.md).
