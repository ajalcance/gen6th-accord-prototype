# Controlled persona-matching benchmark — preparation, 2026-10-02

**State:** protocol plus [offline workflow/viewer](recognition-evaluation-workflow.md) prepared;
no real assets uploaded, SDK installed, model called or measured recognition benchmark run.
Scope follows [the prototype plan](prototype-plan.md). Results must be measured before H3
advertises matching capability. This protocol does not authorize cloud activation or spending.

## October 5 extension — synthetic-performer face retrieval

The owner approved [ADR-0048](../decisions/0048-synthetic-performer-identity-and-search.md)
and [the industry direction](synthetic-performer-industry.md). Extend the experiment to
human-like synthetic faces and continuing performer identity across generated appearances.
The illustration protocol below remains a useful baseline, not synthetic-face acceptance.

- Enroll independently permitted performer families with studio-approved reference sets.
  Reserve unseen query appearances and separate development/held-out families. Held-out
  catalogue references are enrolled inputs; never tune models/ranking on their query answers.
- Compare whole-image and face-centered Google embedding baselines; evaluate an appropriately
  licensed face-specific encoder if needed. No concrete model, new package or deployment is
  selected/authorized by this extension. General image embeddings must prove suitability.
- Assess face location, resolution, blur, visibility and pose. Test explicit subject selection
  in multi-face queries; unsuitable/unsupported images must not receive successful analysis.
- Use dedicated bounded, inspected analysis derivatives. Existing 320-pixel thumbnails are
  not validated recognition input. Freeze orientation/crop/resolution and model provenance.
- Keep exact SHA-256, perceptual fingerprint and embedding evidence distinct. Test known
  image copies separately from documented newly generated appearances of the same performer.
- Add costume/lighting/background changes, independent lookalikes and absent-performer queries.
  Studio-confirmed intended continuity is ground truth, not evidence the model can recognize it.
- Rank/group by performer rather than filling results with many reference views. Measure
  persona recall@1/@3/@5, strong false-match results, abstention/quality handling, failures,
  latency/cost and unauthorized candidate leakage. State denominators and per-stratum results.
- Fix any combined ranking, quality rules and result-label operating points on development
  inputs before held-out evaluation. Do not convert similarity to identity probabilities.
- Test enrollment/version immutability, authorization before retrieval, permission recheck,
  exact job retries, index/restart recovery and refusal to enroll discovered candidates silently.
  Re-evaluate model/index versions and catalogue growth; no numerical target is approved yet.

Recognition reliability, evidence grounding, permission decisions and passport integrity have
separate acceptance. Future web discovery supplies candidate images to this evaluated pipeline;
its coverage/providers/source retention require their own design and authorization.

## What the experiment answers

Can a bounded, permitted catalogue retrieve the known source of a deliberately modified
fictional illustration, while showing the limits exposed by unrelated lookalikes?
The result concerns catalogue retrieval. It does not establish copying, legal ownership,
worldwide originality or whether a real person's face is unique.

The current H1 portraits share one SVG drawing with three palette variants in
`frontend/tests/legacy-passport/portrait.tsx` (historical tests only). Treat them as one source family, not three independent
originals. They are UI fixtures and provide no measured embedding evidence.

## Dataset and provenance, before choosing operating settings

Prepare original fictional illustrations or owner-approved permitted assets. Give every
original a stable family ID, content digest, permission/provenance reference and canonical
catalogue role. Put every derivative of a family in the same development or held-out split.
Freeze the manifest, split and transformation recipes before evaluating held-out queries.
Never tune against the held-out answers or count palette variants as independent creators.

Proposed first inventory: 24 independent families, split 12 development / 12 held-out,
with a balanced mixture of visual styles, palettes and compositions. These are planned
counts, not available assets or a general-purpose accuracy sample. The owner reviews the
actual inventory; every missing permission remains a blocked input.

| Query stratum | Known relationship | What to measure |
|---|---|---|
| Byte-identical copy | Same original bytes | Exact-hash hit and correct source ID |
| Lossless re-encoding / resize | Same declared source | Byte-hash miss versus retrieval rank |
| JPEG compression | Same declared source; fixed quality settings | Source rank and score drift |
| Crop | Same source; fixed crop fractions/positions | Recall by crop severity |
| Palette / background change | Declared derivative of original | Retrieval robustness and distractor ranks |
| Pose/composition variation | Documented derivative, created deliberately | Failure cases without a facial identity verdict |
| Unrelated lookalike | Independently created, similar style/features | Misleading candidate placement; no copying label |
| Unrelated control | No related catalogue family | Abstention/candidate presentation limitations |
| Blank/corrupt/oversized input | Invalid or content-poor | Safe rejection; no fabricated successful job |

Record recipe parameters and exact byte digests for all rendered inputs. Text labels,
family IDs and ground truth must not enter image-only embedding requests. Keep original
rights/evidence outside public projections. Do not scrape celebrities or private workspaces.

## Baselines and model preflight

Run byte-SHA-256 matching as a separate deterministic baseline. A re-encoded image may
have different bytes despite a known shared source; report that limitation explicitly.
Compare catalogue embeddings by ranking. Do not reuse a score as a probability of copying.
Google documents that embedding similarities are not calibrated probabilities and recommends
retrieval rankings rather than a fixed quality threshold.
[Google multimodal embedding guidance](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/embeddings/get-multimodal-embeddings).

The current official guide lists `gemini-embedding-2` and `multimodalembedding@001` as
supported models. They have different input/API contracts, so select and pin one adapter
after the region, privacy, quota, cost and SDK review. Do not mix their embedding spaces.
The legacy API documents 128/256/512/1408 image dimensions; this does not define dimensions
for every Google embedding model.
[Supported models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/embeddings/get-multimodal-embeddings),
[legacy API reference](https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/models/multimodal-embeddings-api).

Before any owner-approved live run: verify actual asia-southeast1 availability and data
handling for the selected model; confirm input limits and supported media, exact SDK pin,
service identity, request/response logging, budget cap and maximum request count. Stop on
missing configuration. Do not silently move regions, install a package, use personal
credentials or activate a different provider. Raster rendering/transform tooling likewise
needs an approved dependency if no existing tool can produce the recorded artifacts.

## Metrics and denominators

- Exact-hash correctness: hits / known byte-identical queries, with mismatched IDs rejected.
- Source retrieval: recall@1, @3 and @5 on known-source queries, separately for each transform
  and split. Report query and catalogue counts; do not include unrelated controls as positives.
- Unrelated-control behavior: candidate ranks/scores, false copying assertions and any
  abstention policy. Nearest-neighbor retrieval always has neighbors; that is not a known match.
- Evidence grounding: valid supplied references / all emitted references; missing-evidence
  findings / known gaps; unsupported factual or ownership findings / all factual findings.
- Reliability: complete/failed/retried requests, duplicate handling, p50/p95 latency and
  observed request/cost totals. Missing provider usage stays unknown, never an invented cost.
- Isolation: zero references, candidates or decrypted objects from an unauthorized workspace.

Fix display and operating settings using development results before held-out evaluation.
Include ties, empty candidate sets, non-finite/mismatched vectors and catalogue omissions
as explicit failure cases. A failed or incomplete query remains in the attempted denominator.
Use small-sample counts alongside percentages; this fixture sample cannot substantiate
general accuracy across real faces, media or styles.

## Evidence-review evaluation remains separate

Gemini may organize supplied evidence and propose gaps or review notes. It cannot approve
a persona or a campaign. Prepare fixtures with known complete evidence, missing references,
conflicting statements and prompt-injection text embedded in an uploaded document.
Treat document content as data. Validate every returned reference against the actual
authorized input set and reject an unsupported reference or ownership determination.
Report retrieval and evidence-review outcomes independently; neither is a legal verdict.

## Run record and exit condition

For each future run retain dataset/manifest digest, source revision, model identifier and
resolved version when available, adapter/SDK version, embedding dimensions/normalization,
parameters, query IDs, ranked reference IDs, timings, errors, usage and result-artifact digest.
Keep private derived data encrypted and tenant scoped before using real evidence. A shared
fixture result file is not authorization for a private cross-workspace catalogue.

Exit only with actual measured results, complete denominators, permitted inputs, valid
references and documented failure cases. Byte-identical retrieval and attribution must be
correct; unauthorized disclosure and autonomous approval must fail. If modified-source
retrieval is weak, narrow the product claim and keep the human evidence-review journey.
No benchmark result or matching badge is issued by this planning document.
