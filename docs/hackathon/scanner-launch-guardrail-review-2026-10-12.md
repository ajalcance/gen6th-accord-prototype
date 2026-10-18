# Scanner launch guardrail candidate — 2026-10-12

Current transition: [October 12 complete handoff](next-session-2026-10-12.md). Owner published draft
[PR #60](https://github.com/ajalcance/gen6th-accord/pull/60) at `116fa14d9d82a9e12dbae4a268db89086d549a4a`.
Linux guard fault tests fail before CLI execution with E2BIG (864 passed/1 failed/18 skipped);
owner review/label, green exact-head CI and release integration remain pending. Dependabot status
is unverified. Earlier candidate/setup statements below are historical; no cloud mutation occurred.

Owner approved proceeding with ADR-0071 preparation. The accumulated checkout is dirty and its
Git metadata is read-only to the agent. The rule requiring a separate guardrail PR therefore
means this unit is an isolated review patch, not a change to active guards or release workflows.

## Prepared result

Local ignored artifact: `.cache/production-bootstrap/scanner-launch-guardrail.patch`.
It proposes only `scanner_launch_guard.py` in the scripts directory and
`test_scanner_launch_guard.py` in the guards test directory of the separate clean checkout.
At that historical stage the destination files did not exist. Do not apply it to the mixed tree.
The owner later committed the 14-file review unit in PR #60; this patch is superseded, not release evidence.

Original two-file patch snapshot bindings (preserved; superseded candidate described below):

| Artifact | SHA-256 |
| --- | --- |
| Review patch | `f7c3bd324c48089b8d24abc521cb7528b34f2aa22cbbfead6329043ffc9a75db` |
| Candidate validator | `366f89421d9013e29f431e9dbdc129784b6f0ff279824c5ae1bc1efd4842c268` |
| Candidate fault tests | `cd4dcd2cca95298df7cca08600d78c65844c702fb33c4ffb3f558cc69984d042` |

The candidate takes OCI configuration JSON, Knative v1 service JSON and an expected immutable
scanner reference. It checks Linux/amd64, UID 100, the literal reviewed command and absence of
entrypoint/environment overrides. Service checks require the three named API/scanner/SQL-proxy
containers, API-only ingress 8000, scanner HTTP `/health` on 8091 and both API startup dependencies.
Scanner deployment fields are restricted to name/image/resources/startupProbe; additional fields,
including mounts, command/env overrides and liveness configuration, need separate design review.
Probe timing is only structurally bounded; no allocation or native timing is selected here.
Duplicate JSON fields, oversized inputs, ambiguous environments and malformed shapes fail closed.
CLI failures print a generic message without repeating supplied configuration.

## Verified locally

86 tests pass, including deliberately changed command elements, reload/proxy/log/environment
overrides, identity/platform faults, mutable/mismatched digests, duplicate container names,
sidecar ingress, TCP/wrong HTTP probes, dependency omissions, malformed/duplicate/oversized JSON
and CLI success/failure. These tests use test-only generated data, never deployment inputs.
Ruff harness configuration, Black and validator strict mypy pass. Both files meet 400-line/50-line limits.
Patch syntax and read-only `git apply --check` pass; application to a clean target remains pending.
DoD, production-readiness, standards and whitespace checks pass; these do not prove native acceptance.
Checkpoint 16 source remains 737 files, SHA-256
`b9de452a5324bfc7f14b5d19a6938caf62e3c431ca5b49cd158a70351a90dd94`; all ten input hashes match.
An unchanged application suite was not rerun for this isolated candidate and documentation unit.

## Manifest/config binding follow-up

The current four-file review artifact is `.cache/production-bootstrap/scanner-guardrail-binding.patch`.
It includes the two launch files and proposes `scanner_image_binding.py` plus its fault tests.
It supersedes applying the original patch; do not apply both. Candidate files now use the actual
harness's 100-column Black configuration; the original patch bytes remain preserved.

| Current artifact | SHA-256 |
| --- | --- |
| Four-file patch | `a713c94c4e9ac487c114e371d961f6488d6d1dd87d999592713719733eecbd4e` |
| Binding validator | `044c57906ab74f4f6847345d1776ffec0f026b4fa05ca9ce12d272b499bab028` |
| Binding fault tests | `02fe264bb776cd15ce12b106a10bc760f5792e021eede23997ec710ea1339d62` |
| Launch validator | `e56b27f8a3807ea7b4de725cdaa889f1a8c03958acd2dd1296de45a7a00c4e20` |
| Launch fault tests | `1764c3c956002e3329e134ee8749f7c0dfd66f9c2f46590d2b7f4b70dd0dfd1d` |

The new validator hashes raw manifest bytes against the expected scanner reference, then hashes
raw configuration bytes against that manifest's configuration descriptor and checks its exact size.
Only a single OCI/Docker v2 image manifest is accepted; indexes, artifact/subject topology, empty
layers, malformed descriptors and external/embedded descriptor data are rejected. It then invokes
the launch validator against that bound configuration and the supplied actual service document.
Layer descriptors are checked for shape; actual layer contents are not inspected or acquired.

43 new tests plus the original 86 pass: 129 total. Positive manifests use independently computed
test hashes; tampered raw bytes, incorrect config sizes/digests, index topology, descriptor faults
and real CLI launch/service failures are covered. All JSON and layer descriptors are test-only.
Ruff, harness-length Black, strict mypy for both validators and read-only patch application checks
pass. No production source/input hash changed; no native executable or image was run.

## Required separate PR and remaining work

In a clean owner-provided guardrail checkout, check/apply the four-file patch and review its scope.
Wire the validator and fault tests into the reviewed enforcement surfaces; the repository's
guard-coverage check must prove the gate is called and can fail. Run required full checks there.
Only the owner applies the guardrail-change label. The later owner-created branch/PR is recorded above.
Owner-only local helper `.cache/production-bootstrap/prepare-scanner-guardrail-review.sh` is prepared
and shell syntax checked, then owner-executed once. Do not rerun it. It checked branch/HEAD and patch hash,
refuses an existing destination, clones local committed objects to a separate review directory,
creates the named review branch from cached main and applies only the candidate patch. It preserves
the dirty source tree and checks its status afterward. It performs no fetch/install/build/cloud
action and configures only a local source remote, not a GitHub publication origin. Cached main is
not current remote/CI evidence; verify that before completing the separate PR. Report helper output
and review status so work can continue on actual enforcement wiring without mixing source changes.

The future release/import stages must acquire the raw manifest/config from the verified image
digest, without reserializing bytes, and validate the actual reviewed service document. Call the
binding validator with manifest, image-config, service and scanner-image arguments. Signature
verification must occur first under the existing reviewed issuer/workflow identity policy; never
take the expected digest from the untrusted supplied manifest. The actual service bytes also need
binding to the reviewed signed assembly record before deployment, including destination import.
Candidate publication requires mandatory scanner build, native acceptance, unchanged vulnerability
policy, scanner SBOM and matching tag/commit/run/input/report hashes in signed assembly evidence.
Promotion/import verifies those records and image signatures, runs the binding/launch checks on
the actual destination inputs, and does not rebuild. Every step must have a fault test at its real
enforcement boundary; no optional missing-file skip or echo-only workflow reference.
Matching supplied JSON alone cannot prove signatures, public routing, application routes or readiness.
Mandatory scanner component/assembly evidence and promotion/import bindings remain to implement
in that separate PR. Native toolchain/Python/Rust locks, trusted archive verification, genuine
signed CVD acquisition, fixture-free layers, measured sizing and isolated native/platform acceptance
remain open before a runnable Dockerfile or signed image. Existing reviewed CI/signature gates stay
required. One production environment; Tasks paused; cloud mutations owner-run; no live mock data.
