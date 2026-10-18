# Scanner resource and lifecycle acceptance — preparation only

No test has run a scanner process/image here. No commands in this record authorize installs,
downloads, cloud deployment or production testing. Rehearse with a separately approved disposable
owner/CI Linux container and synthetic inputs; do not create another cloud environment.
One production environment, minimum workable sizing, paused Tasks and Zynth later remain fixed.

October 12 [packaging review](../hackathon/scanner-packaging-review-2026-10-12.md) identifies
upstream bootstrap validation/supervision gaps, writable-storage memory, native probe requirements
and absent scanner release integration. No selected digest or runtime allocation is accepted.
The [candidate/runtime review](../hackathon/scanner-runtime-review-2026-10-12.md) records exact
registry identifiers and proposed configuration/launcher work; every runtime row remains pending.
Application startup is now wired in ADR-0065; the frozen scanner JSON predates that wiring.

## Evidence matrix for the selected image/configuration

| Scenario | Record | Acceptance requirement |
|---|---|---|
| Cold start with seeded definitions | Image/config hashes, actual engine/definition receipt, startup time and peak memory | Loaded fresh definitions, exact PONG, five-second application probe passes; platform startup retry budget reviewed against measured load time |
| Missing definitions/bootstrap | Bounded download/load result, CPU/egress, writable-storage peak, startup failure | No ready/clean result until official definitions load; denied if download/verification/load fails |
| Benign and known antivirus test input | Synthetic input hashes/sizes, protocol result and receipt | In isolated disposable runtime only: benign input scans, antivirus test input rejects; readiness alone never counts as inspection |
| Two simultaneous bounded scans | Latency, CPU, peak memory and verdicts | Preserve two-scan bound and 20-second workflow; no unexpected clean result or silent resource exhaustion |
| Definition update/reload during scan | Before/after receipts, reload peaks, availability/errors | Existing changed-receipt denial remains; fail closed if unavailable; measure old/new engine overlap |
| Idle update period/CPU throttling | Update schedule, CPU availability, egress failures and definition age | Updates actually run under selected idle policy; stale definitions deny at use, regardless of earlier readiness |
| Oversized/truncated/limit-exceeded input | Response/error, configured daemon limits | Fail/reject rather than clean; preserve application input/response caps and review all selected-version scan limits |
| TERM/restart/failure | Both container exit states, pending scan result, update/storage recovery | Correct signal supervision and bounded shutdown; interrupted/uncertain scan cannot create a clean receipt |

ADR-0068 [source adapter](google-scanner-health-adapter.md) prepares health/supervision with synthetic
children; checkpoint-14 source phases verified. Required real runtime/config validation/launcher
is prepared in ADR-0069 [managed runtime](google-scanner-managed-runtime.md);
checkpoint 15 source phases are verified; all real scanner/platform acceptance remains pending.
All rows are **pending runtime evidence**, not passed from fixture tests or written configuration.
Use synthetic data only; record no original pixels, filenames, credentials or secret values.

## Sizing and container review

Official ClamAV [Docker guidance](https://docs.clamav.net/manual/Installing/Docker.html) states
generic 3 GiB minimum/4 GiB preferred memory. It is not a measured sizing result for this image,
input workload or definition set. Include reload overlap, scanner buffers, writable definition
storage, runtime overhead and other containers in the platform resource review. Do not resize
the existing SQL/Redis resources or choose a smaller scanner bound without measured justification.

Choose exact CPU/memory/storage and platform startup/retry/shutdown policy only after the
matrix is measured. The two-scan semaphore is per adapter, not a fleet-wide limit; include
process/instance/revision overlap in capacity review. A writable definition directory needs reviewed UID/permissions and reload
behavior; updates need explicit idle CPU/egress. Do not assume a request-driven process keeps
definitions current. Use official signature verification; never disable it to get startup green.

Selected daemon configuration must maintain private loopback TCP and prevent limit skips from
being interpreted as clean. The official [configuration sample](https://github.com/Cisco-Talos/clamav/blob/main/etc/clamd.conf.sample)
documents `AlertExceedsMax` for selected limits; verify the chosen version and all relevant
limits, not just that one option. No daemon configuration was changed in this source unit.

No private-original mount or application secret belongs in the scanner. Shared runtime containers
are not separate IAM identities; retain least privilege at the runtime boundary. Application startup now calls the
probe before serving (ADR-0065); scanner native health/supervision remains pending. A CLI is not a
native Cloud Run exec probe.
Immutable image lineage/signature verification and signed release/import precede owner cloud
checkpoints. This plan grants no production launch, provider activation or user invitation.
