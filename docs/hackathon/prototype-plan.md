# Accord AI Persona Passport — Prototype build plan

**2026-10-11 extension:** [ADR-0062](../decisions/0062-accountable-performer-lifecycle.md) and the
[L1–L10 register](performer-lifecycle.md) add accountable operator/rights/provenance declarations,
independent requirements, controlled trials, reassessment, concerns/suspension and current-use checks.
L1–L8 MVP source is prepared; activation/SQL/live acceptance remains pending. External credentials
and actual production attestations remain future contracts alongside the full O1–O8 roadmap.

**2026-10-06 update:** owner-approved ORCID-inspired MVP adds persistent identity/provenance,
optional version-bound aliases/credits, authenticated self-confirmation and production offer history.
[O1–O8 register](performer-identity-and-credits.md) preserves every future item with exit criteria;
[ADR-0060](../decisions/0060-attributed-performer-identity-and-credits.md) records the implementation boundary.
Credit schema/grants are prepared, default disabled; live/rendered acceptance remains pending.

**2026-10-05 update:** evidence intake, explicit asset enrollment and approved public/passport
issuance source are recorded in [S8–S10](evidence-assets-public-passport-slices.md). Source and
QR third-party notice belong in the package inventory; provider/SQL/publication acceptance
remains pending. This update supersedes older claims that these HTTP/UI capabilities are absent.

**Decision date:** 2026-10-01 (Asia/Manila). **Owner:** Albert Alcance.
**Status:** approved bounded prototype; future-industry scope extended October 5, 2026.
**Decisions:** [ADR-0023](../decisions/0023-ai-persona-passport-prototype.md) and
[ADR-0048](../decisions/0048-synthetic-performer-identity-and-search.md).

Current H1 decisions: [ADR-0028](../decisions/0028-persona-console-design-system.md) and
[ADR-0029](../decisions/0029-compact-persona-console.md). See [console review](h1-console-review.md)
for historical scope, evidence and visual acceptance. Current source-bound validation is in
[capture/search slices](capture-search-slices.md); earlier checkpoints are historical.
Owner reports real Zynth sign-in and first save; reviewer and rendered acceptance remain pending.
Photo runtime activation, real recognition/AI and signing remain incomplete. Console layout,
synthetic tests and approved design do not establish live service readiness.
S1 exact-file image search is implemented in source and exposed in Records; similarity/Google execution follow.
**Current reality:** [as-built](../architecture/current-state.md).
**Next-session order:** [MVP transition prompt](mvp-transition-prompt.md), with H2–H6 exit conditions.

## 1. Product promise and entry positioning

Build infrastructure for the emerging synthetic-performer industry. The owner anticipates
recurring AI actors across dramas, short films and endorsements with continuing identity,
commercial value and misuse risks. AI Persona Passport proposes a persistent, searchable
performer identity connected to creation evidence, contributors, recorded rights claims,
review decisions and authorized uses. Customers include studios, creators/agencies and
reviewers/brands deciding whether a specific appearance or production is authorized.

The [approved industry direction](synthetic-performer-industry.md) records this session's
scope, recognition process, proposed profile, future infrastructure and acceptance. Industry
adoption is the objective; current legal recognition is not a prerequisite for the experiment.
The full Stage 0–9 roadmap remains; hackathon delivery demonstrates a bounded working journey.

Customer question: **Who is claiming rights to this persona, what supports that claim,
and who authorized this particular use?**

The selected theme is **Media, Content & Digital Experiences**, subject to confirmation
in the entry portal. See [official themes](https://aibuildercup.com/themes.html).
Requirements, deadlines and pending correspondence are centralized in
[publication-record.md](publication-record.md); do not treat this plan as eligibility approval.

First-mover positioning is an approved ambition. Verify competitors before making a factual
first-in-market claim; previously noted adjacent services are research leads, not an exhaustive
current market survey. Differentiate through performer identity/reference search → creation/
contribution evidence → investigation/review → specific use clearance → verifiable record.

## 2. End-to-end journey

The owner requires enterprise standards and complete implementations within each approved
slice. Include authorization, consistency, recovery, observability and meaningful negative
tests; do not call a partial or unverified control complete. The bounded journey leaves
the full Stage 0–9 roadmap intact. Zynth repository changes remain owner-deferred. Current
Accord identity/runtime evidence follows as-built and the linked work records; trusted fixtures
never substitute for the owner-reported live flow or its remaining acceptance.

1. Authenticated creator/studio opens a workspace and registers an original synthetic performer.
2. Creator supplies name, biography, an inspected primary portrait, additional approved
   references where available, AI disclosure and creation evidence. Explicit Scan precedes save.
3. Creator records human contributions, reference permissions and available generation logs.
4. A review job builds the versioned visual reference profile and retrieves measured face/image
   candidates from a permitted catalogue. A query image can be checked without new registration.
   Gemini organizes supplied evidence and identifies supported gaps/conflicts; visual results
   link actual matched references. Approved enrollment and search remain separate operations.
5. Authorized reviewer inspects cited evidence, requests changes or records a decision.
6. Creator authorizes one persona version and specified assets for one named production/campaign,
   with recipient, purpose, duration and conditions recorded. Reviewer/brand accepts the use.
   Film/episode/adaptation clearance is an approved extension requiring concrete contracts.
7. Accord issues a platform-signed record and export. Owner-approved public fields appear
   in a passport page; verification detects an altered package.

Journey roles: creator and reviewer. A reviewer can represent the brand; a separate brand role
is optional. Human identity belongs to Zynth; the synthetic persona is an asset, not a
natural-person identity or an automatically credentialed autonomous agent.

Use original, permitted demo assets. Compare known modified copies, documented regenerated
performer appearances and unrelated lookalikes from a controlled catalogue. Later permitted
web discovery/monitoring, video and voice support extend the infrastructure; prototype catalogue
search does not claim internet-wide coverage. See the industry direction for staged delivery.

## 3. Data and assurance boundaries

Minimum logical records: workspace membership, persona, immutable persona version, asset,
evidence reference, contribution statement, analysis job/result, review decision,
campaign authorization, issued manifest/signature and approved public projection.
Membership, persona versions/receipts, review and campaign storage exist in migrations
0003–0005; identity and portrait preparation extend through 0010. Read current as-built/work
records for source-bound SQL and runtime evidence. Campaign asset references remain distinct
from portrait uploads. Visual profiles, analysis jobs/indexes and expanded production clearance
are new targets, not applied schema. Earlier checkpoint counts do not certify changed source.

- Bind decisions and authorization to the exact reviewed version and evidence hashes.
  Edits produce a new version and require a new approval; do not overwrite an issued record.
- Distinguish a claimant's asserted creation date from the server's recorded receipt time.
- A registered claim is not legal title, copyright registration, worldwide uniqueness or
  proof that the first submitter created the work. A signature verifies an attributed record.
- Gemini findings are proposals grounded in supplied evidence, not determinations of
  ownership or authorship. Missing evidence stays missing; model output cannot approve.
- Enforce creator/reviewer permissions server-side, including limits on self-review.
  Reuse the existing verified-principal boundary and minimum Zynth session integration.
- Public pages show only explicitly approved projections. Never expose evidence originals,
  contracts or personal contact details by default. "Unlisted" is not access control.
- Store personal data outside signed manifests using pseudonymous references. Protect
  private evidence and identity details with scoped encryption; broader erasure/retention
  operations remain full-product work and must not be advertised as implemented.
- IDs locate records; hashes fingerprint bytes; encryption keys protect private content;
  signing keys establish record integrity. Do not reuse these as interchangeable mechanisms.
- Use tenant-scoped data-key context with per-object encryption, wrapped through Cloud KMS;
  keep personal-data keys separate and encryption keys separate from signing keys.
  Authorized services decrypt selected evidence for processing. This is not creator-only
  decryption or a claim that the AI sees encrypted ciphertext.
- Encrypt embeddings as sensitive derived data. Search only authorized workspace data or
  approved public references; no cross-tenant deduplication or private similarity leakage.
- Use established cryptographic libraries, protected keys, no plaintext keys in storage/logs,
  HTTPS for deployment, upload limits, quarantine and scanning before analysis/publication.
- Use a trusted platform public-key configuration and key version for verification. A public
  key included by an untrusted exporter cannot establish Accord as the issuer by itself.
- Verification checks the disclosed manifest and package contents available to the verifier;
  hashes of withheld evidence do not disclose or independently prove that evidence's contents.

These requirements apply the [encryption design](../architecture/addendum-01-deployment-identity-trust.md)
and [personal-data separation](../architecture/addendum-03-operations-data-security-mobile.md).
Google's [envelope-encryption guidance](https://docs.cloud.google.com/kms/docs/envelope-encryption)
supports the key wrapping model. All new server actions retain telemetry, detection, audit
and compliance coverage. Client animation/telemetry never becomes authoritative evidence.

## 4. Premium UI/UX is part of acceptance

Visual direction: graphite media surfaces, large persona imagery, spacious evidence reading
panels, precise typography and electric-blue accents. Status color conveys actual state.
The whole experience must be designed, not just the upload animation.

| Main screen | Required interaction |
|---|---|
| Persona gallery | Portrait-led discovery, relevant filters, creator/version previews and role-specific next actions |
| Creation workspace | Guided registration, autosaved drafts, image previews, reference selection and evolving passport preview |
| Analysis and review | Scan animation, live job stages, ranked candidates, side-by-side/slider comparison, evidence links and anchored comments |
| Campaign approval | Readable recipient/assets/version/conditions summary, explicit human confirmation and change requests |
| Public passport | Disclosed history, approved-use summary, QR/share link, signature check and package download |

Also include a concise creation/contribution timeline, private/public preview controls,
clear empty/loading/error/retry states, responsive layouts, keyboard navigation, readable
contrast and reduced-motion support. A visual graph is optional; a useful timeline is sufficient.

Signature interactions: portrait becomes passport; possible match opens an investigation;
confirmed authorization becomes a verification receipt. Motion follows real events.
Face meshes, landmarks, percentage progress and encryption/verification labels require real
underlying results. Design fixtures remain labelled demo data; no fake ownership certificate.
No artificial wait once a job completes. Preserve drafts after interruptions and failures.

## 5. AI and visual matching

Follow the [controlled benchmark protocol](matching-benchmark-plan.md) before advertising
retrieval capability. It is preparation only; no measured matching result exists yet.

- Gemini consumes only authorized, scanned inputs. It returns structured findings with
  valid source references, evidence gaps and a draft review summary. Treat uploads as
  untrusted data, not instructions. Validate references against actual submitted evidence.
- Hash matching catches exact duplicates. Image embeddings retrieve visually related
  candidates; their ranking is not a probability of copying or a facial identity verdict.
  See [Google guidance](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/embeddings/get-multimodal-embeddings).
- First spike: test copies, crops/compression, changed backgrounds/poses and unrelated
  lookalikes. Report retrieval quality and failure cases. Narrow the advertised capability
  if matching cannot distinguish these reliably; preserve the evidence-review journey.
- Show catalogue coverage/count and analysis time. "No match found" applies only to that
  catalogue; it does not mean original, non-infringing or unlike every human face.
- Evaluation fixtures have known expected findings. Measure candidate retrieval, unsupported
  AI findings, reference validity, missing-evidence detection, latency and cost. Publish real
  results and limitations; no invented accuracy percentage or uncontrolled model actions.

## 6. Google stack and minimum integration

The owner emphasized technical implementation as central to the entry on October 5. The
[capture-to-serving architecture](google-capture-search-architecture.md) describes inspected
pixels → face/quality processing → versioned representations → scoped retrieval → evidence/
use investigation, with Google responsibilities and measurable demo proof. This is a proposed
integration design, not an activated stack or a selected set of model/package dependencies.

| Service | Prototype responsibility |
|---|---|
| Gemini via Vertex AI | Evidence organization and review proposals |
| Google multimodal embeddings | Controlled-catalogue candidate retrieval |
| Cloud Run | Next.js BFF, FastAPI Core/Intelligence and Go signing/verification component |
| Cloud SQL PostgreSQL | Versioned persona, review, authorization and audit records |
| Cloud Storage | Quarantined/private artifacts, encrypted evidence, exports and public projections |
| Pub/Sub | Reliable analysis/spine events with transactional outbox and idempotent consumers |
| Cloud KMS | Data-key wrapping and distinct platform signing key |
| Secret Manager / Logging / Monitoring | Protected configuration, operational evidence and bounded usage |

Keep Python, TypeScript and Go; do not introduce another framework just to increase service
count. Reuse the compliance spine and implement the minimum approved Pub/Sub transport
needed by this slice; do not leave new actions unaudited or invent a production Redis service.
The full control/cell fleet is deferred; maintain workspace isolation and service boundaries.

Target nonproduction region remains asia-southeast1. Confirm model/embedding availability,
SDK versions, region, costs and quotas before provisioning. Intended app URL is
`accord.gen6th.com`; DNS, TLS and hosting are pending. Its name does not define an IP boundary.
Local development retains the isolated ports 18660–18663; never take another project's port.

## 7. Build sequence and proposed checkpoints

Dates below are planning targets in Asia/Manila, not promises or permission to deploy.
Resolve administrative items alongside useful private/local work.

| Slice | Target | Exit condition |
|---|---|---|
| H0: entry and integration readiness | Oct 1–3 | Publication inventory approach, identity path and Google prerequisites identified; reply gaps recorded |
| H1: visual journey | Oct 1–4 | Five connected local screens with clearly labelled fixtures, responsive and accessible states |
| H2: secure core | Oct 4–8 | Sessions/roles, uploads, immutable versions, encryption, approvals and server action coverage work |
| H3: real AI and early staging | Oct 6–11 | Gemini + benchmarked retrieval, idempotent jobs, early deployed journey after owner authorization |
| H4: authorization and Trust | Oct 9–13 | Scoped campaign decision, real KMS signature, trusted-key verification and altered-package failure |
| H5: rehearsal and evaluation | Oct 13–16 | Complete clean-data journey; negative/security tests, actual AI evaluation and UX failure recovery |
| H6: reviewed submission | Oct 16–17 | Approved source inventory, working judge access, deck, recorded demo and owner submission review |

Keep the deadline day as buffer. If a prerequisite slips, report it and reduce optional
features through an explicit scope update; do not fabricate a deployment or weaken a gate.
No prototype source is published until the publication conditions are resolved.

## 8. Journey acceptance and demo

- A creator submits a persona, evidence and contribution statements through a real session.
- A controlled altered copy surfaces as a candidate; an unrelated control is also tested.
- A reviewer can inspect sources, request a change and approve the resulting exact version.
- A campaign authorization is accepted and signed; its public page excludes private evidence.
- Download verification succeeds unchanged and fails after modifying one signed field.
- Forged/unauthorized approvals, stale versions, leaked evidence and untrusted keys are refused.
- Server error/model outage does not approve a claim; duplicate deliveries cannot issue twice.
- Full repository gates and required PR review remain necessary, with owner runs for sandbox
  limitations. Local fixture previews are not evidence of live cloud integration.

Demo target: approximately 2:45. Show persona/evidence, suspicious match, human decision,
campaign permission and tamper detection. Include one architecture slide and measured
evaluation results. Only issued checks receive badges; no passkey/log/time-anchor badge yet.

## 9. Full roadmap mapping and deferred scope

Stages 0–1 provide necessary hosting, identity, encrypted storage and event plumbing.
Stages 2–3 provide one collaboration/review format. Stage 4 adds creation and campaign-use
claim profiles and export. Stage 5 provides platform signing and basic public verification.
A bounded Stage 9 similarity experiment is advanced; the general matching service stays later.

Defer full format catalogue, control-plane/cell fleet, person registry/record wallet,
claimant passkey signing, transparency log, anchoring, witnesses, mobile, autonomous agents,
voice cloning, persona generation studio, internet crawling/takedowns, government IP
registration, disputes/appeals, billing and full commercial launch. Existing launch requirements
are not waived by this scope. External publication commitments are in the companion record.
