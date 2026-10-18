# Scanner candidate and runtime design review

October 12, 2026. Authorized metadata/configuration review completed; implementation proposed.
No image layers, source archive, definitions or packages downloaded; no process/build/cloud action.
Public registry metadata was read after scoped network approval. Application source and all nine
accepted contracts remain bound to checkpoint 14. This record does not select a deployable image.

## Candidate and evidence level

Recommend evaluating the latest LTS patch **ClamAV 1.4.6** for this MVP. The
[official support matrix](https://docs.clamav.net/faq/faq-eol.html) lists critical patch support
through August 15, 2027 and database downloads through August 15, 2028. Recheck before release;
stay current with LTS patches. The current stable alternative is 1.5.4. LTS is not equivalent to
latest-feature false-positive testing or every noncritical fix; synthetic inspection acceptance
and ongoing vulnerability review remain necessary. [Official downloads](https://www.clamav.net/downloads).

Public Docker Hub tag API observation on October 12 around 03:12 UTC:

| Metadata | Observed value |
|---|---|
| Seeded candidate | `clamav/clamav:1.4.6` |
| OCI index | `sha256:b5b910ce43d595bf8a2fe401e34db56434602b2c755b7c2b07f00c917d04d469` |
| Linux/amd64 child manifest | `sha256:fefe26428207c7ec3e51396376cbd5084528f134b504db76a92363ed534e0b10` |
| Reported compressed child size | 155049138 bytes; not memory or writable-storage allocation |
| Tag last pushed | 2026-10-12T01:25:27.656967Z |
| Base comparison index | `sha256:1b483c3988220dae0e107911e2788c2a671ccd4ec01901777f8ac02e518d3af2` |
| Base Linux/amd64 child | `sha256:934a62e82e30bfa2665216b0cf042c01d8842d010540c82b1fdc9e3b87784731` |

Sources: public [seeded metadata](https://hub.docker.com/v2/repositories/clamav/clamav/tags/1.4.6)
and [base metadata](https://hub.docker.com/v2/repositories/clamav/clamav/tags/1.4.6_base).
Only Linux/amd64 and an unknown-architecture companion are reported. The companion is not a
usable runtime architecture or verified signature. Index and child digest are different bytes;
record both, verify actual registry manifests/platform mapping before release, and bind the final
single-platform built scanner digest independently. Mac ARM execution is not the target evidence.

These are registry-reported identifiers, not locally recomputed manifest hashes. No image config,
layer inventory, seed files, SBOM, provenance attachment, scanner-image signature or vulnerability
scan was inspected. Candidate suitability remains pending. Do not promote/import these bytes as
an Accord signed release or infer a signature from an unknown companion descriptor.

## Matching source review

Engine tag `clamav-1.4.6` is an annotated tag object
`26071af7b26cd71e66b13dcbe4bcb6bae8a8c2be`; its release page points to commit
`5853e1396777bae4d909cd3dd44f58352e7cf9b3`. GitHub displays verified signatures, but this session
did not locally verify them against an independently trusted key.
[Release](https://github.com/Cisco-Talos/clamav/releases/tag/clamav-1.4.6).

Container recipe repository head observed through public GitHub metadata:
`1eba87c1b014d6b5598a1ad54325edb491bd691c`, whose patch sets 1.4.6/1.5.4 build versions.
This supplies an immutable source reference for review; linkage to the actual registry image
still requires build provenance. The recipe uses floating Alpine/package inputs internally,
so rebuilding that source alone does not reproduce the candidate digest.
[Recipe](https://github.com/Cisco-Talos/clamav-docker/blob/1eba87c1b014d6b5598a1ad54325edb491bd691c/clamav/1.4/alpine/Dockerfile).

The matching [entrypoint](https://github.com/Cisco-Talos/clamav-docker/blob/1eba87c1b014d6b5598a1ad54325edb491bd691c/clamav/1.4/alpine/scripts/docker-entrypoint-unprivileged.sh)
still disables bootstrap load testing, uses a Unix-socket wait and tails after background child
startup. Override this through the reviewed managed runtime, preserving validation and supervision.
Source recipe UID is 100; actual image/user/library/executable layout still needs inspection.
Clamd installs in the sbin directory, FreshClam in bin; `/usr/sbin/clamd` and `/usr/bin/freshclam`
are candidate fixed paths under the recipe's /usr prefix, not verified image execution paths.

The final Alpine recipe does not install Python. Packaging must supply a reviewed, pinned Python
runtime and the adapter's existing Python dependencies with compatible libc/architecture, without
assuming the Debian backend runtime can be copied into Alpine. No dependency installation or
Dockerfile modification is authorized by this review. Preserve licenses/notices and include all
added components in the final SBOM/vulnerability checks. No package/CVE-free claim is made here.

## Proposed fixed configuration policy

The [1.4.6 clamd sample](https://github.com/Cisco-Talos/clamav/blob/5853e1396777bae4d909cd3dd44f58352e7cf9b3/etc/clamd.conf.sample)
supports the following proposed review inputs. These are not installed configuration:

| Control | Proposed policy |
|---|---|
| Endpoint | Explicit TCPAddr 127.0.0.1, TCPSocket 3310; no public scan listener |
| Runtime | Foreground yes; reviewed numeric non-root ownership; fixed data/temp paths |
| Stream and worker capacity | StreamMaxLength 10M, MaxThreads 2, finite queue and socket waits |
| Expansion | Explicit finite file/scan-size, file-count and recursion limits; AlertExceedsMax yes |
| Features | Keep supported inspection features and bytecode validation enabled; unsigned bytecode denied |
| Reload | Concurrent reload remains candidate; measure overlap before allocation |

Freeze exact expansion/queue/time values only after checking every limit's response semantics.
AlertExceedsMax documents file-size, scan-size and recursion cases; it does not guarantee all
limit skips are detectable. MaxScanTime is described as ZIP-specific. Retain the application's
20-second bound, and measure daemon work that continues after client cancellation.

The [1.4.6 FreshClam sample](https://github.com/Cisco-Talos/clamav/blob/5853e1396777bae4d909cd3dd44f58352e7cf9b3/etc/freshclam.conf.sample)
supports explicit TestDatabases yes, Checks 12, official database/DNS sources, bytecode enabled,
foreground execution and finite connection/read waits. Keep custom mirrors, excluded official
databases, arbitrary hooks/commands, debug and environment-driven option rewriting disabled.
Use separate fixed bootstrap/update configurations if NotifyClamd requires a running daemon.
Actual TLS, signature/update and configuration parsing behavior still requires selected-image tests.

The [1.4.6 database loader](https://github.com/Cisco-Talos/clamav/blob/5853e1396777bae4d909cd3dd44f58352e7cf9b3/libclamav/cvd.c)
checks CVD digital signatures, while local incremental CLD follows a distinct path that skips that
same outer signature check. Preserve trusted updater ownership/provenance; reject arbitrary local
seed databases. FreshClam success with unchanged definitions alone does not prove a full load test.
Prepare must force verified seed/load acceptance, then update only through the trusted updater;
first clamd startup/probe and continuous at-use receipt guards remain mandatory.

## Proposed implementation unit

Implement new files around ADR-0068, preserving existing adapters/guards and frozen contracts:

1. Fixed, bounded configuration/seed policy: reject duplicates, unknown directives, symlinks,
   unexpected local databases, unsafe ownership/permissions or changed bytes. No public path,
   environment override, shell string or command hook. Candidate templates are source fixtures
   until actual image parser acceptance; they cannot claim runtime validation from string checks.
2. Required ManagedRuntime with fixed executable vectors and minimal explicit environment.
   Prepare validates config and bootstrap/load evidence before long-lived clamd/FreshClam launch.
   Temporary verification/bootstrap processes have their own registered handles and bounded
   finally cleanup; the public two-child tuple represents long-lived children only.
3. Cancellation-safe process acquisition: register before the next yield; cleanup processes whose
   spawn completes while cancellation arrives. Test that race with mocked process handles. Never
   claim a cancelled spawn guarantees no OS child. Preserve peer TERM/KILL/reaping semantics.
4. Mock process/filesystem/clock tests for every denial and launch/cleanup boundary. No executable
   is invoked by the new test unit. No image, dependency, definitions, workflow or cloud action.
   Add an ADR, docs and a fresh owner full gate after approval and source freeze.

The exact seed verification executable/layout and final numeric daemon limits must be resolved
before claiming the runtime implementation is complete. Missing evidence denies startup; it is
not permission to trust a tag, disable load testing or relax an existing guard. If the new design
requires changing an existing guard, stop for its separate owner-approved PR.

After that source unit: separate scanner release-integration guardrail PR, signed built artifact,
owner isolated Linux measurement matrix, then native/cloud checkpoints. Resources remain null;
one production environment, minimum workable measured sizing, Tasks **PAUSED**, Zynth later.
