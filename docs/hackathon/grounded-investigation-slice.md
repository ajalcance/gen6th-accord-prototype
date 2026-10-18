# S5 — grounded investigation and independent review

Owner authorized implementation on October 5, 2026. Implements
[ADR-0053](../decisions/0053-grounded-investigation-history.md) and the approved
[capture/search slices](capture-search-slices.md). Source preparation includes backend and frontend.

## Studio journey

1. Records → Search by face similarity → prepare/confirm an inspected appearance → select a
   candidate. Side-by-side query/reference comparison remains the existing freshly authorized S4 flow.
2. Check investigation availability, supply source context and explicitly confirm retained findings.
   Gemini analysis runs only on a manual click; the server refreshes search evidence first.
3. Inspect bounded visual observations or abstention, both image citations, mandatory evidence gaps,
   query/reference digests, exact version/generation, method/policy, raw cosines and model revision.
4. Request independent review of the saved analysis and exact current version. Inspect its saved
   request receipt/history; an authorized independent reviewer uses the existing decision workflow
   and cites the analysis ID. An internal request sends no notification or approval.
5. Reopen Records → governance → saved version → Analysis & review for encrypted findings history,
   pagination and independent decision history. Query pixels need not still exist to read a packet.

New private routes, under `/api/workspaces/{workspace_id}/personas/photos/investigations`:

| Route | Authorized capability | Frontend exposure |
|---|---|---|
| POST `/readiness` | Injected provider + currently valid similarity configuration | Manual availability check and unavailable state |
| POST `/generate` | Fresh server-grounded comparison, explicit retained packet, exact committed replay | Context/retention form, findings/gaps/receipt, explicit retry/cancel/new intent |
| POST `/history` | Exact-version newest-first findings, 20 rows + ordinal cursor | Analysis & review, newest/older pages and saved packets |
| POST `/review-requests/request` | Save current-version request linked to authorized analysis; exact intent replay | Manual Request independent review, receipt, retry/cancel |
| POST `/review-requests/history` | Exact-version request history, 20 rows + cursor; no provider/key call | Saved review requests, refresh, newest/older pages |

Metadata is bounded to 4 KiB after verified membership. Generation has an 80-second outer bound
and the client 85 seconds, within the existing 90-second proxy budget;
Google transport has a 20-second request timeout and 256 KiB response cap. Findings are at most
five unique neutral labels, each citing both supplied images. Unsupported legal/permission claims
or incomplete provider output do not become findings. Model correctness still requires evaluation.
The adapter supplies two inspected metadata-free PNG analyses and selected boxes; source notes,
persona biography, creator claims and credentials are excluded from model context. No URL fetch.

## Evidence and lifecycle

The server re-runs S4 retrieval rather than sealing browser-provided candidates or scores.
Selection must match an authorized fresh candidate's exact version, portrait and latest generation.
Catalogue/calibration changes, query expiry/clear and permission loss fail closed after long work.
Missing/corrupt encrypted source evidence does not become an empty or completed result.
Persona locking serializes history/replay. Committed retries avoid new model calls; failures before
commit may repeat cost. Client cancellation ignores late results; server work may still commit, so
the UI directs users to retry the same intent or read history. S7 owns durable delivery/reconciliation.

Migration `0013investigation` and `deploy/accord-investigation-runtime-grants.sql` are owner-reviewed
preparation only. `persona_investigations` has forced workspace RLS, composite reference binding,
immutable trigger and actor/request plus version/ordinal uniqueness. Encrypted JSON is capped at
64 KiB; it retains provenance/findings/source context, not query pixels, original bytes or vectors.
Current members may inspect their studio's exact-version history after fresh authorization.
Query digests/boxes remain retained evidence after S4's ten-minute image expiry; explicit consent
and reviewed retention/key/provider policies are activation prerequisites. No purge is introduced.
Redis clearing and SQL commit are separate operations; clearing query pixels does not erase
already saved findings or withdraw a saved review request.
`persona_investigation_review_requests` uses forced RLS/immutable protection and a composite
workspace/version/analysis FK. It stores attribution/identifiers/timestamps only, with exact replay
and serialized ordinals. New requests cannot target a historical head or missing/foreign analysis.
The requested state is an immutable handoff receipt; independent decisions are inspected separately.

The atomic server observation uses existing `persona.workspace_observed`, resource
`persona_investigation` and operation `investigation_recorded`; its metadata contains no source
note, digest, vector or model output. Existing emit/detection/audit/compliance decisions apply.
The event records server processing, not the truth of a supplied source statement.
Review request observations use operation `investigation_review_requested` with the same action
and resource `persona_investigation_review_request`, atomic with the handoff row.

## Validation and remaining acceptance

October 5 source checks:

- 47 new focused backend tests pass; the combined S3/S4/S5 and unchanged spine coverage run
  passes 125 tests. These use synthetic providers/disconnected SQL, not real recognition proof.
- 391 frontend unit tests across 41 files pass, including 21 new S5 transport/UI cases.
  Fifteen existing isolated ASGI-to-UI cases pass separately with synthetic sessions/receipts.
- Frontend lint/format/strict types, production build and bundle budget pass (166.4 kB gzip shared
  client bundle / 250 kB budget). Rendered browser acceptance is pending.
- Full `make check` passes preflight, 776 guards (18 skipped), policy/harness, backend
  Ruff/Black (274 files), mypy (261 files) and Bandit, then stops at pip-audit's temporary
  pip-upgrade bootstrap. Dependency audit/full backend SQL/coverage/Trust/later stages do not run.
- `make frontend` passes lint/format/types, then npm audit cannot resolve `registry.npmjs.org`.
  Audits are retained. No full-green claim, install, sandbox bypass or guard change.
- DoD passes 55 ADRs/154 standards; whitespace and all changed file/function caps pass.

Three new owner/CI SQL cases cover committed replay after clear/provider withdrawal, changed intent,
encrypted exact-version history, foreign workspace denial, exact-analysis review requests/replay
and immutable update rejection for both history tables.
Migration SQL can be checked offline; collection does not execute these PostgreSQL cases.

Remaining: reviewed migration/grants, scanner/Linux/Redis/key setup, permitted corpus/calibration,
explicit Gemini model/region, actual bounded calls and quality/refusal/cost evidence, authorization
and restart/replay recovery, rendered review workflow, owner-reviewed PR and revision-bound CI.
No dependency installation, private configuration, model/provider activation, database alteration,
restart, signing, publication or Git write is part of this source preparation.
S6 source is now recorded in [production/passport evidence](production-passport-slice.md); S7 is next.
