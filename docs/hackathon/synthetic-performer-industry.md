# AI Persona Passport — infrastructure for the emerging performer industry

**October 11 extension:** all ten accountable-lifecycle adaptations are approved and retained in
[L1–L10](performer-lifecycle.md), [ADR-0062](../decisions/0062-accountable-performer-lifecycle.md).
L1–L8 MVP source extends governed performer operation, separate rights/authority/content reviews,
private trials, reassessment, concerns/suspension and passport current status. L9/L10 preserve
external credentials and actual-use attestations. Live acceptance and Google deployment remain open.

**Approved direction:** October 5, 2026, Asia/Manila. **Owner:** Albert Alcance.
**Decision:** [ADR-0048](../decisions/0048-synthetic-performer-identity-and-search.md).
**October 6 extension:** owner approved attributed identity/credits and production history for the MVP.
[ADR-0060](../decisions/0060-attributed-performer-identity-and-credits.md) and the
[complete O1–O8 register](performer-identity-and-credits.md) preserve scope and future acceptance criteria.
**Delivery state:** approved product/design scope; recognition and expanded studio workflows
are not implemented or activated by this record. Runtime truth remains in
[current state](../architecture/current-state.md).

## 1. The objective the owner clarified

Build for what is coming. AI dramas, short films and digital content can develop recurring
synthetic performers that audiences recognize and studios invest in. Their continuing identity,
creation history, authorized appearances and commercial use will need dependable infrastructure.
The owner anticipates this market and wants Accord to help establish its practices and standards.
This is a forward-looking product thesis, not a measured market forecast.

AI Persona Passport is a proposed industry mechanism whose acceptance is still to be earned.
Present legal recognition is not the prerequisite for demonstrating its value. The industry
is figuring out these questions too. Do not reduce the product to current legal administration
or repeatedly redirect the vision into legal disclaimers. Existing applicable obligations and
honest evidence remain constraints; they do not define the limit of the product's ambition.

The hackathon entry targets **Media, Content & Digital Experiences**. Build a bounded working
prototype of the new infrastructure while retaining the full Stage 0–9 roadmap. Narrow feature
breadth without weakening security, authorization, data integrity or meaningful verification.
First-mover positioning is an approved ambition; a factual claim of being first requires research.

The owner additionally emphasized that capture/search technology and meaningful Google stack
integration must carry the hackathon entry alongside the concept. The
[capture-to-serving architecture](google-capture-search-architecture.md) maps the processing,
representation, retrieval, result contracts, Google services and technical demo evidence.

Proposed product promise:

> An Accord AI Persona Passport connects a synthetic performer's persistent, searchable
> identity with creation and contribution evidence, recorded rights claims, authorized uses
> and verifiable history across productions.

## 2. Approval provenance from this session

- The owner agreed with the misuse scenarios and authorized the recommended studio/creator
  features: competing claims, unauthorized productions/endorsements, overextended permissions,
  altered official appearances and supporting human face/voice consent evidence.
- The owner explicitly agreed with all recommendations for visual reference profiles,
  database similarity search, multiple approved references, scoped discovery, human investigation
  and future web discovery. A supplied image or supported URL is an intermediate investigation path.
- The owner clarified that recognition must analyze the human-like face itself, using the
  same family of techniques as facial recognition, rather than relying on a registration ID.
- The owner endorsed the future-industry objective after correcting the assistant's excessive
  emphasis on present legal acceptance, then explicitly requested these records and a memory update.

These approvals establish direction and feature scope. They do not select a model/package,
authorize new installations, cloud/model spending, migration/grants, service activation,
publication or signing-key activation. This task changes documentation only.

## 3. Problems and approved product responses

| Anticipated problem | Approved response |
|---|---|
| Another party registers or claims the studio's performer | Attributed creation/contribution evidence, history and investigation of competing claims |
| A performer appears in an unauthorized production or endorsement | Check the appearance against references and recorded production/use permissions |
| Permission for one episode is extended to sequels or advertising | Explicit production, purpose, duration, recipient and adaptation conditions |
| An altered face or voice is promoted as the official performer | Approved appearance versions; voice reference support is a later extension |
| A persona incorporates a real human's likeness or performance | Supporting source permissions/consent evidence and visible unresolved gaps |
| A studio finds a suspicious appearance | Image comparison, matched reference, source context and a human investigation outcome |

Distinguish the continuing synthetic performer from its character/role in a particular film.
An approved appearance belongs to a versioned performer profile; a production authorization
names the specific version/assets and use. New looks and roles must not rewrite old evidence.

Production clearance is approved scope: a studio or brand supplies a proposed use, AI assists
with evidence gaps and supported conflicts, and an authorized human decides. The receipt binds
the performer/version, production and recorded permission. Existing campaign contracts are a
foundation, not proof that film/episode clearance or all new conditions already exist.

## 4. What registration captures

The profile is a proposed logical data shape, not an applied database schema:

| Component | Purpose |
|---|---|
| Persona ID, attribution and immutable versions | Persistent asset identity and history |
| Primary portrait and additional approved references | Studio-confirmed appearances across angles/expressions |
| Selected face region and quality observations | Identify the subject; record resolution, blur, visibility and pose limitations |
| Exact digest and perceptual fingerprints | Exact-file lookup and tested altered-image retrieval |
| Face-centered and whole-image embeddings | Candidate retrieval across face and scene appearances |
| Confirmed descriptive metadata | Supporting visible features; no inferred sensitive human identity attributes |
| Creation/contribution evidence and rights claims | Attributed statements, supporting material and unresolved/competing claims |
| Model and processing provenance | Source digest, crop, settings, model/version and analysis time |

A mathematical representation is model-dependent and is not a universally unique face number.
One portrait starts a profile; multiple independently approved references improve the basis
for comparison. Keep each reference's representation and provenance. Never automatically add
search candidates to the canonical profile: a false match would contaminate future searches.

## 5. Approved capture and ingestion design

1. Verified studio/creator selects references and explicitly begins Scan. Selection previews
   locally; it does not upload. Initial registration still requires an inspected attachment.
2. Authorize scope; validate size/type/digest/replay; inspect original bytes; decode in the
   bounded worker; create metadata-free derivatives and inspect them before downstream use.
3. Locate faces and assess suitability. Multiple faces need explicit subject selection.
   Unsupported, obscured or insufficient-quality faces must not receive a successful profile
   analysis. Explain the limitation and request a better reference where appropriate.
4. Produce consistently processed face and whole-image analysis derivatives. Correct orientation;
   preserve distinguishing features. No beautification or generative reconstruction of the face.
5. Extract exact/perceptual fingerprints and embedding representations. Compare a Google image
   embedding baseline with an appropriately licensed face-specific encoder if needed. Model choice,
   licensing, synthetic-face performance, region, privacy, cost and dependencies remain to resolve.
6. Protect originals and derived data; bind analysis to the immutable reference/version. Record
   complete processing provenance and maintain separate compatible model/index versions.
7. Publish into only the authorized search scope after analysis and indexing succeed. Distinguish
   upload inspected, analysis pending, search ready and analysis failed. Index recovery/replay and
   source/permission changes must not expose stale or unauthorized results.

The existing `photo_decoder.py` produces a derivative capped at 320 pixels. It is prepared
thumbnail storage, not validated recognition input. A dedicated bounded analysis derivative
needs resolution determined by evaluation; enlarging the existing thumbnail cannot recover detail.
The existing scanner, Linux worker, storage/schema/grants and runtime acceptance prerequisites
remain. No face detector, quality evaluator, fingerprint library or embedding adapter is added here.

Encryption at rest is required for private derived data. Select an index/query design that can
enforce authorization before retrieval without leaking other tenants. Do not claim that ordinary
vector search compares encrypted ciphertext or that a private global index is already safe.

## 6. Search and interpretation

Allow a query upload without creating a new persona. Process it through the same safe image,
subject-selection and representation pipeline as references. Search the studio's own records,
explicitly shared collections or an opt-in discovery catalogue; registration alone is not sharing.

Retrieve candidates, apply an evaluated ranking method, group by persona and recheck access before
display. Show the actual matched references, search scope/coverage, quality limitations and analysis
provenance. Preserve separate exact-file, possible altered-copy and visual-resemblance evidence.
No strong candidate is an allowed outcome; nearest neighbors alone do not establish a known match.
Embedding scores are not identity probabilities or copying percentages.

Gemini may organize authorized evidence and summarize supported observations/gaps. Do not invent
explanations for embedding scores. Human review interprets the relationship and recorded permissions;
model similarity does not approve a use or adjudicate an ownership dispute.

The passport's planned assurances are registered performer identity, attributed evidence/rights
claims, authorized uses and issued-record integrity. Registration time establishes receipt time.
An early uploader cannot obtain unquestionable ownership merely by registering first. Signed
records do not create statutory rights; the product can support evolving industry conventions
without claiming existing government recognition or an unregulated market.

## 7. Prototype acceptance before recognition claims

Extend the [matching benchmark](matching-benchmark-plan.md) to independently permitted synthetic
performer families, approved reference sets and unseen queries. The old palette variants and
illustration-only tests cannot certify face recognition. Freeze ground truth and development/
held-out families; the held-out catalogue may contain enrolled references, but no tuning on its queries.

Measure exact-file correctness, persona recall at top ranks, strong false matches on unrelated
lookalikes/absent personas, poor-quality input handling, failures, latency and costs. Test compression,
resizing, crops, background/costume/lighting changes and documented same-performer pose variations.
Group results by performer; do not inflate metrics with many views of one source. Include failed
attempts in denominators. Tune ranking/operating rules on development data before held-out evaluation.
Model upgrades and larger catalogues need re-evaluation. No accuracy number or threshold is approved.

Require isolation, exact retries, restart/index recovery, immutable reference history, grounded
evidence and human decision boundaries. Report supported transformations and failure cases; narrow
claims if the selected model cannot reliably retrieve newly generated appearances of the performer.

## 8. Future infrastructure and staged delivery

**Hackathon core:** approved visual profiles and measured catalogue search, evidence investigation,
independent review, specific use permission/clearance and a verifiable passport/export. The full
journey remains the target; existing safety/security/activation gates are not waived.

**Intermediate:** Check this appearance using a studio-supplied image, with supported URL intake
planned separately. Inspect a found appearance and compare its context against recorded permission.

**Future:** permitted web/platform discovery, film-frame/video search, voice references, ongoing
appearance monitoring, dispute evidence and broader licensing/adoption integrations. Discoveries
retain source URL, observation time, matched references, coverage and human classifications such as
authorized, unrelated or suspected misuse. Web access, retention, installs, provider contracts and
monitor activation require their own concrete design and authorization; no worldwide coverage claim.

The reusable infrastructure is performer identity/versioning, approved reference enrollment,
safe analysis jobs, permission-scoped retrieval, production-use records, evidence investigation,
trust issuance and interoperable projections. Build for eventual adoption by studios, creators,
brands and content platforms; industry acceptance and first-mover status are outcomes to pursue.

## References consulted in the discussion

- [Hackathon themes and requirements](https://aibuildercup.com/themes.html): selected theme,
  Google AI/cloud requirements and judging. Recheck submission requirements when acting on them.
- [Google embeddings](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/embeddings/get-multimodal-embeddings):
  image/vector retrieval and scores that are not calibrated probabilities.
- [NIST quality evaluation](https://pages.nist.gov/frvt/html/frvt_quality.html): image suitability
  and evaluation discipline; human-face results do not certify synthetic-performer performance.

Current-law material discussed in chat supplies assurance boundaries, not the product's mission.
This document records approved intent; no model benchmark, package install, live acceptance,
schema/index migration, service restart, public passport or monitoring activation occurred.

## Documentation validation — October 5, 2026

The documentation-only update passes `make dod-check`, production-readiness and standards
validation (50 ADR files including index/template; 154 rules). Full `make check` with installed
Node 22 passes 776 guard tests (18 skipped), policy/harness and backend Ruff/Black/mypy/Bandit,
then stops at pip-audit's temporary pip upgrade failure. SQL/Trust/frontend/docs-site stages
are not reached. No audit was bypassed or environment/package/runtime changed. This is not
full-green acceptance or recognition evidence; final evidence-only edits receive doc validation.
