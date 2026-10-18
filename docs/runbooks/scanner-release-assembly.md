# Scanner release assembly — preparation contract

See [ADR-0022](../decisions/0073-scanner-release-assembly-boundaries.md). Staged source; normal
reviewed PR, owner-applied guardrail-change and exact-head Linux CI are required. PR #60 is merged;
do not reuse its completed publish/prepare helpers.

## Required producers

Candidate release first requires deploy/google/scanner/{Dockerfile,input-lock.json,service.json,
prepare-context.sh,native-acceptance.sh}. These genuine producers are still absent. Missing inputs
fail before registry login or image builds. The stager must isolate the approved Python import
closure, pinned upstream source/key, native snapshot/locks, Cargo vendoring, seeds and configs.
The native harness receives the immutable image, tag, commit, Actions run URL and artifact folder.
Retain real raw manifest/config, reviewed service JSON and every manifest layer blob. No generated
acceptance, mock providers or fake records may reach the build context or runtime.

Artifact files are scanner-ROLE.json for inputs, seeds, configs, layers, native, scan, manifest,
image_config, service, notices and scan_raw; SPDX uses sbom-scanner.spdx.json. scan_raw is the actual
pinned scan-action JSON output. Layer records name retained basename-only blobs. The strict field
contract is scripts/scanner_assembly_evidence.py; unknown/missing fields deny. All receipts carry
tag/commit/run_url/image. Native receipts require twelve checks and positive finite observed CPU,
memory and writable-storage peaks. Hashes prove recorded bytes, not that a producer performed
the claimed work. Signed genuine Linux harness evidence remains required. Seed/config/input
digests are producer receipts; final layer digest/path inspection is independent. Retain
corresponding source and license review evidence alongside the signed release artifacts.

## Publication and promotion

The workflow requires scanner digest/signature/SPDX/unchanged scan policy/native reports, emits
and validates assembly, verifies images, signs assembly and release evidence, then publishes both
bundles and raw reports/layer blobs. Promotion fetches those exact assets and verifies both signed
blobs, every component signature, scanner assembly and launch binding before the existing retag loop.
No promotion build is permitted. Failed verification stops the step; do not override it.

## Owner Cloud Shell import checkpoint

Before copying, use scanner_release_gate.py --mode promote with --assembly, --release, --artifacts
and --tag pointing to the downloaded signed release. The separately reviewed owner copy procedure
must preserve the source manifest and signatures. After import, run this read-only verifier with
the actual digest reference and release paths; the notation below is not executable production input:

```text
python3 scripts/scanner_release_gate.py --mode destination --assembly <assembly-path> \
  --release <release-path> --artifacts <artifact-folder> --tag <release-tag> \
  --destination <Google-registry-scanner-reference@sha256:digest>
```

Cosign and crane must already be owner-provisioned. Missing tools/signatures, identity/issuer
mismatch, report changes or unequal registry digests deny. The verifier makes no mutation.
Activation follows genuine acceptance and measured sizing in a later owner Cloud Shell checkpoint.
Tasks paused; Alembic for application tables, one production environment and Zynth later.
No production tests, recreation, credential fallback or secret output.
