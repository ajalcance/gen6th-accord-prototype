# Scanner packaging review — October 12, 2026

Status: owner-approved review completed; source adapter subsequently approved and prepared in
[ADR-0068](../decisions/0068-scanner-health-supervision-adapter.md); checkpoint-14 source phases verified, pasted exit omitted.
Image/config/runtime implementation, release changes and native acceptance remain separate.
No image pull, install, build, scanner execution, definitions download or cloud mutation.
Checkpoint 13 remains the accepted application source population: 719 files, SHA-256
`e5bc0137034e9573ee3f8123e1955697d64fbc76e8e2bc9919d8f9773a997965`.
All eight accepted deployment artifacts remain unchanged. The scanner contract is a historical
snapshot: its startup-not-wired wording predates ADR-0065's application startup integration.

## Findings and recommended direction

Use a reviewed, digest-pinned supported official ClamAV lineage with seeded definitions for the
initial disposable rehearsal. Keep FreshClam enabled and verify freshness at startup and at use.
Seeded definitions reduce repeated cold downloads; they do not establish current definitions.
Do not select a floating stable/latest tag, invent a digest or claim a verified publisher signature.
Exact release/build, architecture manifest, support status, vulnerabilities, SBOM/license and
publisher provenance remain unset until actual artifact metadata is reviewed.

The [official Docker guide](https://docs.clamav.net/manual/Installing/Docker.html) distinguishes
seeded and base images, documents non-root `/init-unprivileged`, and lists generic 3 GiB minimum/
4 GiB preferred memory. These are starting points, not measurements. A base image with empty
ephemeral storage repeatedly downloads full definitions; persistent storage would add a separate
reviewed resource. Prefer seeded images for MVP rehearsal before introducing persistence.

**Do not launch the upstream defaults unchanged.** The reviewed upstream main-branch
[Alpine 1.5 entrypoint](https://github.com/Cisco-Talos/clamav-docker/blob/main/clamav/1.5/alpine/scripts/docker-entrypoint-unprivileged.sh)
disables database load testing on its initial missing-database path, waits for a Unix socket,
starts background children and then tails indefinitely. It supplies no Accord native freshness
endpoint or proof that child failure terminates the whole container. This is source inspection,
not proof about a selected image. Recheck exact source revision/configuration after pinning.
The [upstream Dockerfile](https://github.com/Cisco-Talos/clamav-docker/blob/main/clamav/1.5/alpine/Dockerfile)
also leaves TCP address restriction unset; its UID/entrypoint and Docker HEALTHCHECK are not
enough to satisfy the reviewed listener, native startup and shutdown requirements.

Candidate design: a non-root scanner container with explicitly reviewed clamd/FreshClam config,
supervision of both children and a minimal HTTP native health adapter. Only clamd listens on
127.0.0.1:3310. Health exposes a fixed outcome on a separately reviewed platform-reachable port;
it must never accept pixels, scanner commands, filenames, endpoint overrides or application secrets.
Bounded PING/VERSION uses the existing receipt rules. Child death, stale/unavailable definitions,
shutdown or missing startup validation deny health. Keep the at-use inspection guards unchanged.
Health is protocol/freshness evidence, not a clean verdict or model evidence.

The [Cloud Run service health guide](https://docs.cloud.google.com/run/docs/configuring/healthchecks)
requires HTTP/TCP/gRPC native probes; Docker exec health checks are insufficient. Its current
startup budget is at most 600 seconds for non-GPU probes; the upstream 1800-second socket wait
must not become our default. Choose bounded download/load and native probe budgets from measured
cold starts. Proxy and scanner startup dependencies must not create a readiness cycle with API.
Keep native health private and out of application/public ingress. Validate reachability separately
from loopback scan isolation in the eventual owner platform checkpoint.

## Definitions, limits and resource measurement

Candidate FreshClam policy explicitly sets daily checks (initial review candidate: 12), foreground
supervised execution, bounded connection/read waits, official databases and clamd reload notification.
Keep `TestDatabases yes` for bootstrap and updates; do not trade validation for memory savings.
The [FreshClam sample](https://github.com/Cisco-Talos/clamav/blob/main/etc/freshclam.conf.sample)
documents these controls. Review their exact selected-version semantics, permissions, TLS and
database authenticity before constructing configuration. Deny startup after failed validation.
Transient update failure cannot refresh the loaded definition receipt; existing 48-hour age/
five-minute future bounds still deny stale or ambiguous scans.

Use explicit writable definition and temporary directories owned by the selected numeric UID,
without root chown at runtime, private-original mounts or application credentials. Account for
seed-to-writable copying, old/new databases, load testing, reload overlap and temporary streams.
[Cloud Run memory guidance](https://docs.cloud.google.com/run/docs/configuring/services/memory-limits)
includes filesystem writes in memory usage. A 4 GiB engine allocation is not evidence that writable
definitions fit. Storage mechanism/limit and total measured resource envelope remain unset.

For idle updates, retain instance-based billing as the candidate; it provides CPU outside requests
but does not make instances persistent. With zero minimum instances, every cold start must again
validate loaded fresh definitions. The [billing guide](https://docs.cloud.google.com/run/docs/configuring/billing-settings)
documents this distinction. No background update promise survives a scaled-to-zero instance.

Preserve application 10 MiB, two scans per adapter and 20-second bounds. Review daemon
`StreamMaxLength`, `MaxThreads`, queue, expansion/recursion/file/time limits and `AlertExceedsMax`
against the [selected-version clamd sample](https://github.com/Cisco-Talos/clamav/blob/main/etc/clamd.conf.sample).
`AlertExceedsMax` only documents some limits; it is not universal proof against skipped scans.
The reviewed main sample says MaxScanTime affects ZIP processing, so it cannot be treated as a
general hard scan deadline. Test every relevant uncertain/limit response: none may become clean.
Client cancellation does not prove daemon work stopped. Include residual work in timeout, restart,
two-way load and TERM measurements; retain expansion protections and supported scan features.

Start isolated measurement with the existing one-vCPU/4-GiB scanner candidate; include actual
writable-storage consumption. If it cannot pass safely, adjust the candidate to a supported
measured allocation rather than reducing protections. Only compare a smaller candidate after
complete matrix success and documented margin. Keep selected CPU/memory/storage null until
[all acceptance rows](../runbooks/google-scanner-acceptance-preparation.md) pass, including reload,
idle updates, interrupted scans and native TERM. No production tests or new cloud environment.

## Release integration is a separate reviewed unit

The current `.github/workflows/release.yml` builds/signs backend, optional frontend and trust;
it does not produce a scanner artifact. A digest copied from Docker Hub is not this repository's
signed release. Definition database signatures and container provenance are separate controls.
No acceptable upstream container signing identity was established in this review.

A future scanner release must record the verified upstream digest, reviewed configuration/source,
SBOM/license, our built immutable scanner digest and signature in the same release evidence.
Promote/import exactly those bytes without rebuilding; verify signature/evidence under existing
release policy. Do not sign an imported image manually or append evidence after the fact.

Adding the scanner to the release workflow touches a guard-defining file. Under
[AGENTS.md](../../AGENTS.md), that requires a separate explicit owner-approved guardrail PR and
owner-applied label; it cannot be bundled into the source work or used to bypass current gates.
No workflow, release checker, agent policy or historical contract was edited in this review.

## Next concrete units

1. Approve a bounded source-only health/supervision adapter design with synthetic tests: fixed
   endpoints, fresh-receipt denials, child failure, blocked startup, cancellation and TERM cleanup.
   Set an ADR before implementation. No image/build/runtime/configuration guard change in that unit.
2. Review exact supported image metadata and version-specific daemon/update config, then separately
   approve scanner release integration under the existing guardrail-change review process.
3. After signed artifact evidence exists, owner approves isolated Linux synthetic runtime rehearsal
   covering the entire measurement matrix. Capture exact hashes, verdicts, receipts, resource peaks,
   child exits and interrupted-work outcomes. Only then select minimum workable resources.
4. Prepare private platform topology/mount/egress manifests and owner Cloud Shell checkpoints.
   Reverify foundations first; do not recreate them. Tasks stays **PAUSED**; Zynth remains later.

This review completes the authorized packaging analysis. Implementation, image acquisition,
runtime rehearsal, release changes and production activation are distinct follow-up decisions.
