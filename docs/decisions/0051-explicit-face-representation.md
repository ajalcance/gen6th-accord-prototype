# ADR-0051: Explicit version-bound face selection and measured representations

Date: 2026-10-05
Status: Accepted source direction under the approved S3 slice; activation/evaluation pending

## Context

S2 stores safe analysis pixels and explicit version reference approval. S3 must locate the
performer in group images, preserve processing provenance and prepare searchable evidence.
Google detection does not identify an individual. A general image encoder on a face crop
is a benchmark candidate, not a selected or calibrated face-recognition model.

## Decision

Expose explicit private face profile/detection/selection operations under the photo resource.
Authenticate the current session and workspace membership before reference lookup or decrypt.
Only the immutable version creator may process its approved references; members may inspect.
Accept server generation ID/face index, never browser actor, coordinates or vector values.
Require confirmation even for a single detected face; no automatic enrollment or selection.

Persist append-only `persona_face_generations`, encrypted result metadata and two normalized
vectors (face crop first, whole image second), bound to workspace/version/reference/request/
actor/fingerprint/time. The referenced exact version must have approved that portrait. Force
RLS and reuse immutable protection. Migration 0012faces and SELECT/INSERT-only grants are
owner-review source; populated history cannot be silently rolled back. No delete path exists.
Crop bytes remain transient; stored boxes, recipe and digest allow reproducible inspection.
Reads expose bounded boxes/status/provenance, never vectors, analysis pixels or wrapping keys.

Use synchronous, explicitly requested bounded processing in S3. Serialize by approved portrait
row; reauthorize and replay a committed exact request before calling a provider. Changed intent
under the same studio request ID conflicts. A provider failure rolls back its generation; it
never becomes `no_face`. A dropped connection or cancellation may leave an uncertain commit.
The frontend retains only authored unresolved intent in session/tab memory and explicitly
retries it. A failure before commit may repeat external calls/cost. This is not durable job
dispatch or crash-safe billing deduplication; S7 must supply dispatch/reconciliation before
production background processing. No implicit background task or automatic POST retry exists.

Injected Google REST adapters use Vision FACE_DETECTION and the documented
`multimodalembedding@001` image prediction interface as candidates. Discard emotions and
unneeded attributes. Bound responses/timeouts, refuse redirects/errors/malformed vectors;
use explicit injected workload authorization, no personal credential discovery or SDK install.
Detector revisions are unpinned; missing embedding deployment ID is explicitly unresolved.
A reported deployment ID alone does not prove immutable weights. Region/API availability,
provider drift and compatibility must be evaluated before serving similarities.

`face-square-512-v1` creates a metadata-free square, preserving geometry with transparent
padding and no upscale. It is not landmark alignment. Linux worker CPU/memory/time/output
limits are mandatory. Provisional quality policy blocks faces smaller than 64px, detector
confidence below 0.8, yaw over 45 degrees, pitch over 30 degrees or likely blur. These are
eligibility checks requiring calibration, not an accuracy certificate or identity probability.

The offline benchmark requires permission references, unique source digests and disjoint
performer families across development/calibration/test. Test includes regenerated, lookalike
and absent performers. Fit abstention using calibration impostors, preserve failed observations
in denominators, and report recall/false matches/latency/cost. Human permission/label review,
actual image-to-observation processing and calibrated model selection remain required.

## Consequences and validation

Studio frontend exposes provider status, numbered boxes/radios, confirmation, pending/cancel/
exact retry, quality/no-face feedback and model/generation provenance. The API does not
change reference enrollment, persona content, clearance or passport rights.
Real pixel/AES tests, mocked Google transport, synthetic ASGI and UI contracts can verify
source behavior. They cannot prove active PostgreSQL, Linux limits, Google recognition quality,
rendered geometry or live session/provider acceptance. See [S3 record](../hackathon/face-representation-slice.md).

Sources: [Google Vision detection](https://docs.cloud.google.com/vision/docs/detecting-faces),
[Google image embedding REST contract](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/multimodal-embeddings-api),
[InsightFace licensing](https://github.com/deepinsight/insightface/blob/master/python-package/README.md).
No pretrained face model is downloaded or selected by this decision.
