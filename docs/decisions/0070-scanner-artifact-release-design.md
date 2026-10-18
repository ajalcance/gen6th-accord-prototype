# ADR-0070 — Scanner artifact assembly and release integration design

Date: 2026-10-12. Status: source preparation approved/partially implemented; guardrail/build/release review pending.

## Context

Checkpoint 15 verifies the ADR-0069 source runtime. Live deployment may contain no stubs, fake
definition databases, mock receipts or synthetic records. Existing release.yml builds/signs
backend and frontend only; its component evidence/listing is generic, but does not require a
scanner or bind detailed scanner inputs. Existing Google scanner/proxy image references remain null.

## Proposed decision

Build a separate Linux/amd64 scanner component from verified ClamAV 1.4.6 source, on a reviewed
digest-pinned Debian/Python 3.12 base compatible with the backend. Treat the existing backend base
digest as a candidate to recheck, not an accepted scanner input. Build native binaries against the
same runtime ABI; never copy the Debian Python environment into the reviewed Alpine image.
The previously observed upstream image identifiers remain comparison evidence, not selected bases.

Pin source archive hash/signature/trusted release key, builder/base digests, native build/runtime
packages and Python transitives with hashes. Record exact compile options and toolchain inputs;
test installed `/usr` paths, linked libraries and real engine versions. Source compilation requires
CMake/native dependencies and Rust; resolve exact supported package/toolchain versions before
writing executable build instructions. No arbitrary toolchain installer or unbounded upgrade.
[Official source build guidance](https://docs.clamav.net/manual/Installing/Installing-from-source-Unix.html).

Use a staged allowlisted build context and explicit copies. Include the scanner modules and the
unchanged probe/photo-contract/decoder import closure; prove that closure in the final image.
Include existing pinned dependencies initially rather than guessing a smaller untested set;
remove unrelated dependencies only after an explicit closure test and separately reviewed lock.
No broad repository COPY, test packages, source sample archives, demo launchers, dev tools, caches,
credentials or test definition manifests in runtime layers. Preserve licenses/notices and the
corresponding-source distribution obligations for ClamAV; copying an executable is not license review.

Obtain genuine official CVD seeds in an approved acquisition stage, verify signatures and actual
file hashes, then freeze them as one immutable build input set. Produce seeds.json from these real
bytes, not a generated fake database or hand-filled digest. Require exactly main/daily/bytecode CVD;
reject CLD as a seed. Use fresh CVD acquisition through the official verified update distribution;
if the staged updater yields CLD, do not rename it or bypass ADR-0069. Record source/update time,
receipt, hash and verification evidence; reject missing, stale or ambiguous inputs. Never fetch
definitions invisibly from a cached Docker layer or overwrite a released seed set.
[Official database management](https://docs.clamav.net/manual/Usage/SignatureManagement.html).

Final artifact contains root-owned fixed configuration/seed manifest, genuine seed files in the
UID-100 mode-0700 writable database directory and an empty private temp directory. A production
factory must instantiate ScannerRuntime directly; no runtime provider selection or fixture fallback.
Exec-form launch runs one ASGI worker as UID 100, with docs/access logs disabled and bounded graceful
shutdown. Proposed health listener 0.0.0.0:8091 is a native sidecar probe only; scanner protocol stays
127.0.0.1:3310. Actual private exposure/port collision and PID-1/TERM/reaping need isolated proof.

Use one final single-platform manifest as the digest built, tested, signed, imported and deployed.
Preserve the current single-manifest release convention; attach signed input/build evidence
separately rather than silently enabling an OCI index and changing digest meaning. The current
workflow has provenance:false; source commit/run evidence is not an independent SLSA attestation.
Do not claim a SLSA level. If adding attestations changes manifest topology, it needs a new reviewed
decision and index/child verification tests. [Build provenance](https://docs.docker.com/build/metadata/attestations/slsa-provenance/).

Extend the existing release workflow in its own owner-approved guardrail PR: mandatory scanner
build, immutable image signature, scanner SBOM and unchanged vulnerability policy before signed
release evidence publication. Add scanner image/SBOM to generic release-evidence components.
Require the scanner for the new production release path; do not silently skip a missing Dockerfile.
Bind a separately signed scanner assembly record to tag, source commit, run, final digest, seed/config
hashes, verified input set, scan/SBOM hashes and actual isolated-test report hashes. Promotion must
verify this record and its matching scanner component before existing image verification/retagging.
No rebuild on promotion. Existing ancestry, exact default-branch CI, release holds, readiness,
typed confirmation and signature checks remain unchanged.

Signing in CI uses the reviewed release identity, never local signing keys. Verification must bind
the OIDC issuer and exact approved tag/workflow identity, not merely accept a cryptographically valid
signature. Require matching evidence before Artifact Registry import and compare destination/source
manifest digests after import. No new mutable deployment tag or manifest-converting shortcut.
[Signature verification](https://docs.sigstore.dev/cosign/verifying/verify/).

## Consequences and implementation boundaries

The [source preparation](../hackathon/scanner-packaging-inputs-2026-10-12.md) implements a real ASGI
factory, build-only seed/config emitter and proposed source inventory. No native execution or build.
Executable health launch is deferred: the proposed non-loopback bind triggers Ruff S104/Bandit B104;
review that exposure in its separate guardrail PR, with no suppression or alternative spelling.
Exact native/Python locks remain unresolved. No Dockerfile, guard, workflow, release schema,
image, package, definition database, signature or live resource is changed.
The [implementation plan](../hackathon/scanner-artifact-design-2026-10-12.md) names separate source,
guardrail and acquisition/build/native checkpoints. Every enforcement addition is pending reviewed
implementation and fault tests; prose is not an active release gate.
The [isolated guardrail candidate](../hackathon/scanner-launch-guardrail-review-2026-10-12.md) now
prepares exact raw manifest/config digest binding plus command/topology validation: 129 tests pass.
The calling pipeline must verify signatures first and bind reviewed service/assembly inputs;
mandatory component/evidence enforcement and separate PR remain pending, with no workflow changes.

Resources remain unselected until startup, update/load/reload overlap, writable storage and scan
load are measured. Sidecar background updates require reviewed CPU availability; no current spend
or allocation change. Zynth later does not make the inspected API activation guard optional.
This scanner design does not close SQL proxy image/signature, credentials, IAM, schema/grants,
routing, full API/identity or real product-journey gaps. One production environment, Tasks paused,
owner Cloud Shell mutations only; no production tests, mock data or resource recreation.
