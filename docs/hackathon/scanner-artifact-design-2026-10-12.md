# Scanner assembly/release design — review only

Current transition: [October 12 complete handoff](next-session-2026-10-12.md). Owner published draft
[PR #60](https://github.com/ajalcance/gen6th-accord/pull/60) at `116fa14d9d82a9e12dbae4a268db89086d549a4a`.
Linux guard fault tests fail before CLI execution with E2BIG (864 passed/1 failed/18 skipped);
owner review/label, green exact-head CI and release integration remain pending. Dependabot status
is unverified. Earlier candidate/setup statements below are historical; no cloud mutation occurred.

October 12, 2026. [ADR-0070](../decisions/0070-scanner-artifact-release-design.md) is proposed.
Source/checkpoint-15 hashes and all nine contracts remain unchanged. No executable/package/image
acquisition, definition download, build, workflow edit, signing, import or cloud mutation here.

## Verified current release path

| Existing mechanism | Verified behavior | Scanner gap |
|---|---|---|
| release.yml guard | Tag/default-branch ancestry and release preflight | Keep unchanged; dirty local source is not release eligible |
| Candidate job | Builds backend and conditional frontend, signs immutable digests | No scanner build/sign step |
| SBOM/scan | Per-image SPDX, existing high/fixable scan policy before evidence publication | Scanner/native/Python/OS components absent |
| release_evidence.py | Generic named components, digest refs and SBOM hashes, signed readiness | Can record scanner without schema change; does not require it or detailed inputs |
| Promotion | Signed evidence/tag/readiness checks; verifies every recorded image, retags without build | Needs matching scanner assembly acceptance and required-component check |
| deploy/verify.sh | Verifies signed evidence and each listed component | Not a Cloud Run importer or native acceptance check |
| Build metadata | Explicit provenance:false to preserve single image manifest | No independent build provenance/SLSA-level claim |

The images are signed before their SBOM scan in the current workflow. A signature alone therefore
does not establish accepted candidate status: signed release evidence/publication and all gates
must succeed. Preserve existing ordering/guards; do not claim scans precede every image signature.

## Proposed artifact boundary

Preferred route: compile verified ClamAV source against a digest-pinned Debian/Python 3.12 runtime
ABI. Resolve signed source inputs, exact native packages/toolchain, Python transitive hashes and
build options before executable packaging. Do not transplant Alpine binaries/libraries into Debian.
The upstream image comparison does not resolve actual binary/linker/seed inventory or provenance.

Candidate source files from the design (see [partial source implementation](scanner-packaging-inputs-2026-10-12.md)):

- `deploy/google/scanner/` Dockerfile, context inventory and pinned input metadata/locks;
  no placeholder digest can be consumed by a build. Root config comes from accepted policy bytes.
- A narrowly scoped artifact-preparation module that emits real seed hashes/configuration into
  a staging directory and rejects missing/extra/CLD inputs. No definitions are committed to git.
- A production scanner factory using ScannerRuntime directly, one worker, fixed native health
  port 8091 and bounded signals. A test-only injected factory is never its deployed entrypoint.
- Tests for missing/placeholder inputs, source/hash drift, unsafe context files, unexpected
  imports, fixture leakage and signal/startup settings. Test assets remain outside runtime layers.

Final payload must include real ClamAV binaries/runtime libraries, compatible Python components,
allowlisted Accord source closure, exact configs, genuine CVD seeds/manifest and license notices.
Exclude backend tests, test keys/providers, fake records, local databases, caches, build toolchains
and source-tree examples. An installed ClamAV test corpus may be used only in an isolated test stage,
and must not exist in the final artifact. Inventory every final layer, including inherited layers;
excluding files from a COPY does not remove data already present in a base layer.

Do not fabricate seed files to complete a Dockerfile. Genuine definitions are obtained once per
approved input snapshot, verified, hashed and held immutable. Runtime FreshClam updates its own
ephemeral writable store; those updates do not rewrite signed image seeds. A new baked seed set
requires a new tested signed artifact. Cold starts from aged seeds and update/CDN failures must
still fail closed within existing startup bounds. Rate limits/egress/download volume need measurement.

## Proposed signed assembly record

New record is supplementary, not an edit to release-evidence schema. Its future validator needs
strict field/type/duplicate checks and fault tests; no new active gate is asserted today.

| Bound field | Required real evidence |
|---|---|
| Identity | Exact release tag, source commit, workflow run URL and timestamp |
| Output | Single Linux/amd64 scanner manifest digest; same component in signed release evidence |
| Build inputs | Base/builder manifest hashes, verified source archive/tag/key evidence, toolchain/native/Python locks and compile flags |
| Data/config | Three genuine CVD hashes, verification/update time and receipt, seeds.json/config hashes, UID/path inventory |
| Supply chain | Scanner SPDX hash, vulnerability scan report hash/verdict, notices/source obligations |
| Native acceptance | Final-image import/layout/version, real load/update/scanning/limits, signals and resource report hashes |

Bind report bytes by hash and retain the reports with the release. No copied fixture result,
truncated console tail, upstream tag, unsigned claim or SBOM generation alone satisfies these fields.
An unsigned local rehearsal is developmental evidence until the exact final digest and reports are
bound into accepted release evidence. After signing, verify and rehearse the same immutable digest;
do not rebuild it for production or confuse structural validator tests with signature verification.

## Separate guardrail PR

Required future paths: `.github/workflows/release.yml`, dedicated scanner assembly evidence guard
and its fault tests under `scripts/` / `tests/guards/`; deploy verification/import preparation only
where explicitly reviewed. Existing generic release-evidence.py need not change simply to add a
component. Keep guard changes separate from packaging/source work and owner-applied labels.

Negative cases must fail before publication/promotion: missing scanner/component/SBOM/assembly
record, wrong tag/commit/digest, mutable ref, wrong signing issuer/identity, altered seed/config,
bad scan, missing real acceptance, leaked fixture layer and digest change during import. Do not
add a bypass label or lower scan/coverage/freshness limits. No workflow permissions are widened here.

## Native/platform acceptance and resources

Use the [existing isolated matrix](../runbooks/google-scanner-acceptance-preparation.md), with real
official definitions and synthetic antivirus inputs only in disposable tests. None of those inputs
are enrolled, retained or deployed as product records. Final artifact must contain no test corpus.

Cloud Run sidecar startup dependencies need a successful native probe; listening alone is
insufficient. Proposed health HTTP serves statuses only on 8091, never the public ingress route;
clamd stays loopback 3310. Verify network exposure and port collisions in the actual topology.
[Container dependencies](https://docs.cloud.google.com/run/docs/configuring/services/containers).

Writable files consume instance memory and do not persist after instance stop; seed files baked
into the image and update-copy/reload/temporary peaks must be measured separately. Exact restart
behavior must satisfy the fresh-directory requirement, not reuse arbitrary CLD/state storage.
[Runtime filesystem contract](https://docs.cloud.google.com/run/docs/container-contract).

Idle updater work requires CPU outside requests while an instance exists. Instance-based billing
provides that allocation, but instances can still terminate; no continuous availability is assumed.
Keep min/max instance counts and CPU/memory unselected until owner sizing/spend review. Retain
minimum workable measured MVP sizing and one production environment.
[CPU allocation](https://docs.cloud.google.com/run/docs/configuring/billing-settings).

## Ordered next units

1. Owner-reviewed source packaging implementation: exact input metadata, staged context, genuine
   seed/config emitter and real production factory; local fixtures only in tests. No install/build.
2. Separate owner-approved guardrail PR: scanner build/sign/SBOM/evidence and mandatory-component
   verification with fault tests; exact commit/default-branch CI must pass.
3. Separately approved acquisition/build and isolated Linux acceptance: verify inputs, build once,
   inspect all layers, measure real update/scan/signals/resources, scan/sign/bind reports and retain
   final digest evidence. Resolve any failures before accepting a release.
4. Owner Cloud Shell checkpoint: verify signed release, import preserving digest, verify destination
   and final composition before any service activation. SQL proxy/identity/IAM/schema/grants/routing
   remain separate prerequisites. Tasks stays paused; no stubs/mock data/live test records.

The design unit needed no command. Source preparation now needs checkpoint 16's owner full gate;
the executable listener requires separate guardrail review. No deployable manifest or artifact exists.
