# Scanner build inputs and listener review

Current transition: [October 12 complete handoff](next-session-2026-10-12.md). Owner published draft
[PR #60](https://github.com/ajalcance/gen6th-accord/pull/60) at `116fa14d9d82a9e12dbae4a268db89086d549a4a`.
Linux guard fault tests fail before CLI execution with E2BIG (864 passed/1 failed/18 skipped);
owner review/label, green exact-head CI and release integration remain pending. Dependabot status
is unverified. Earlier candidate/setup statements below are historical; no cloud mutation occurred.

October 12, 2026. Read-only upstream research and documentation after accepted checkpoint 16.
737 source files and ten input hashes unchanged. No archive, key, CVD, wheel, package or image
acquired; no install/build/native execution or cloud query/mutation. Shell GitHub metadata lookup
failed DNS inside the sandbox; no unsandboxed retry. Public browser metadata provided the findings.

## Source archive candidate identified

The official [ClamAV 1.4.6 release assets](https://github.com/Cisco-Talos/clamav/releases/expanded_assets/clamav-1.4.6)
publish these values. They are observed upstream metadata, not locally verified file digests:

| Required asset | Published SHA-256 |
|---|---|
| clamav-1.4.6.tar.gz | 06dbc7adf96e2f6a27c548a841ce83c95360d1e121b106a6f7cf56f282a3c61b |
| clamav-1.4.6.tar.gz.sig | f55ae2aa17482cf870f16578e56c2d77885c22ac748ebee9f6808c4dbba93bea |

Use the named release archive and detached signature, not GitHub's automatically generated
source archive. Future acquisition must hash actual bytes, verify the detached signature against
an independently reviewed Talos key fingerprint, preserve verification output and bind all inputs
to the release. The [official verification instructions](https://docs.clamav.net/manual/Installing.html#verifying-clamavnet-downloads-with-gpg)
link the key and explain key rotation. No current trusted fingerprint or signature verification
is claimed here; a GitHub tag's Verified badge does not verify the downloadable archive.

## Candidate native build family

Prefer matching Debian Trixie builder/runtime ABI with explicit Python 3.12 patch version and
Linux/amd64 manifest. The [official Python image inventory](https://raw.githubusercontent.com/docker-library/official-images/master/library/python)
currently lists `3.12.15-slim-trixie`, recipe commit `2a3b794c223ab067d122719541cdd54a068732a5`,
directory `3.12/slim-trixie`. Owner registry lookup below identifies its candidate index/platform
digests, not a signature, vulnerability verdict or installed ABI. Existing backend base digest is unchanged and not selected
as a new scanner base. Do not use cached/search-result index digests with unknown platform mapping.

| Toolchain candidate from Debian's current catalog | Published version | Meaning |
|---|---|---|
| [rustc](https://packages.debian.org/trixie/rustc) and recommended matching cargo | 1.85.1+dfsg1-1+deb13u1 | Candidate exceeds documented ClamAV 1.4 minimum Rust 1.70 |
| [cmake](https://packages.debian.org/trixie/cmake) | 3.31.6-2 | Candidate exceeds tagged INSTALL.md minimum 3.17 |
| [gcc](https://packages.debian.org/trixie/gcc) | 4:14.2.0-1 | Metapackage version, not a complete compiler/runtime lock |

[Bookworm's default rustc](https://packages.debian.org/bookworm/rustc) is 1.63.0+dfsg1-2, below
the [documented 1.4 minimum](https://docs.clamav.net/manual/Installing/Installing-from-source-Unix.html).
Do not mix Bookworm runtime libraries with Trixie build output or use a floating rustup installer.
These catalog versions are candidates; exact repository snapshot, signed InRelease/package hashes,
architecture-specific dependency solution and security updates still need actual resolution.

Tagged [INSTALL.md](https://raw.githubusercontent.com/Cisco-Talos/clamav/clamav-1.4.6/INSTALL.md)
requires bzip2, zlib, libxml2, PCRE2, OpenSSL and json-c, plus libcurl for FreshClam.
The tagged [CMakeLists.txt](https://raw.githubusercontent.com/Cisco-Talos/clamav/clamav-1.4.6/CMakeLists.txt)
requires curses when apps are enabled; do not omit it simply because ClamDTop is unused.
Build-only test dependencies include libcheck and Python. Keep native tests enabled in the isolated
test stage, then exclude its sources/corpora/toolchain from every final layer. Resolve Rust crate
lock/vendor input hashes too; an exact rustc version does not lock Cargo dependencies.

Candidate options for review: `/usr` prefix, explicit libdir/config/database paths matching policy,
apps/shared libraries enabled, interpreter bytecode retained, systemd/milter/on-access/examples
disabled. Keep scan support and native tests; disabling unrelated services is not disabling checks.
Inspect actual installed paths/libs and notices before accepting any reduced runtime copy set.
No executable build instructions are emitted while these lock inputs are incomplete.

Python's ten direct requirement pins already exist. Still need the complete Linux/amd64 Python
3.12 transitive graph and hashes for selected wheels/source builds, plus any native wheel-build
inputs. Mac's virtualenv is test evidence, not that lock. Resolve in a separately approved isolated
Linux acquisition stage; never claim a cross-platform lock from pip freeze on Mac.

## Network review proposal

[ADR-0071](../decisions/0071-scanner-explicit-container-health-launch.md) proposes an explicit
container launch command, matching the existing API Dockerfile's deployment configuration pattern.
Keep Ruff S104/Bandit B104 unchanged. This changes where deployment configuration is reviewed and
requires compensating command/topology checks; relocating a bind alone does not establish safety.
No Dockerfile, launch command or guard changes are implemented by this document.

Cloud Run's [runtime contract](https://docs.cloud.google.com/run/docs/container-contract) has one
ingress container; its all-interface ingress requirement expressly does not apply to sidecars.
Therefore it alone does not prove the proposed scanner probe works. [Container configuration](https://docs.cloud.google.com/run/docs/configuring/services/containers)
requires a startup health check for ordered sidecars and one exposed ingress port. Actual native
HTTP probing/exposure still needs isolated and owner platform evidence. [Health checks](https://docs.cloud.google.com/run/docs/configuring/healthchecks)
accept HTTP 2xx/3xx; our health app emits 200 only for current verified readiness and 503 otherwise.
Never replace that readiness contract with a TCP listening-only probe.

## Owner metadata checkpoint completed — no full test rerun

Owner's formatted manifest lookup reports:

- Index: `sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1`.
- Linux/amd64 runtime child: `sha256:2b4f19dae3a777dfc3b76730bda1e82e1f66ab2a2686fa93ca78edbfb4f04ffe`.

Future acquisition/assembly must reference the child by digest, with Linux/amd64 explicit, and
verify its mapping to the recorded index. Ignore unknown/unknown attestation and other architecture
entries for runtime selection. Metadata identifies a candidate; no image layers, signatures,
SBOM/security verdict, ABI, installed native dependencies or build behavior were verified.
Current 737-file source and ten input bindings still match checkpoint 16. No source test rerun.

The original read-only identification command is retained as history; no repeat is required:

To resolve the candidate registry index/platform mapping, run in local Mac Terminal outside Codex's
sandbox. This reads registry manifests; it does not pull image layers, install, build or deploy:

```bash
cd "/path/to/gen6th-accord"
if backend/.venv/bin/python .cache/production-bootstrap/scanner-packaging-source-fingerprint.py; then
  docker buildx imagetools inspect docker.io/library/python:3.12.15-slim-trixie
fi
```

Report the complete inspect output or error. Record both index digest and exact Linux/amd64 child;
do not select ARM64 because the owner's Mac is ARM64. No install fallback if buildx is unavailable.
This is identification only; later digest-bound layer/ABI/security checks remain necessary.

Next approval units: review ADR-0071's explicit launch and separate command/topology/release guards;
then separately authorize bounded isolated input acquisition/lock resolution. No changes to owner
machine packages, production credentials, cloud resources, grants or Tasks. One production
environment, minimum workable measured sizing, Zynth later, no stubs/mock data in runtime payload.
