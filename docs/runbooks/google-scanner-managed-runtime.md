# Fixed scanner managed runtime — source preparation

[ADR-0069](../decisions/0069-scanner-fixed-managed-runtime.md) adds an explicit `ScannerRuntime()`
for the ADR-0068 health factory. No global app/entrypoint, selected built image or production launch.
The source is executable integration code, not a stub; packaging and native acceptance remain open.

## Required real artifact contents

| Location | Requirement |
|---|---|
| `/etc/accord-scanner` | Root-owned directory; exact clamd/bootstrap/freshclam config bytes from `accord.scanner.policy`, plus real seeds.json only |
| `seeds.json` | Exactly main.cvd, daily.cvd, bytecode.cvd mapped to genuine release-bound SHA-256; no shipped placeholder or fixture manifest |
| `/var/lib/accord-scanner` | Fresh UID-100 mode-0700 directory containing exactly the three bound genuine CVDs before updater execution |
| `/var/lib/accord-scanner-tmp` | Empty UID-100 mode-0700 directory; private transient engine storage |
| Executables | Root-owned regular executable files at `/usr/sbin/clamd`, `/usr/bin/freshclam`, `/usr/bin/sigtool`, `/usr/bin/clamscan`; actual image layout/engine version must be verified |
| Runtime | Linux x86_64, effective UID 100, clamav account UID 100, compatible pinned Python/dependencies; no application secrets/private originals |

Root-owned non-writable ancestors, no symlinks/hardlinks/set-ID files and bounded descriptor reads
are required. Definition files may be writable only by the trusted scanner UID. This assumes that
UID runs only the reviewed scanner/updater; it does not protect against a hostile same-UID process.
No public paths/commands or runtime policy/environment overrides are accepted.

No seed files or JSON manifest are supplied by this unit. Bind actual release definitions and
manifest inside the signed image; a root-owned JSON file alone is not independently signed evidence.
The candidate upstream seeded image has not been inspected for CVD/CLD inventory and cannot be
declared compatible. Do not substitute arbitrary local CLD, empty databases or test fixtures.

## Lifecycle and evidence limits

Prepare validates real files/hashes, checks all three CVD signatures, rechecks seed bytes, runs
trusted FreshClam bootstrap and requires a separate database load/compile check with EOF stdin.
Helpers consume no user data. Success is initialization evidence, not an antivirus verdict or
synthetic-record enrollment. Bind updated CVD/CLD bytes through load and pre-launch validation.
Then start fixed foreground clamd and foreground daemon FreshClam; existing supervision/probe
decides readiness. Updated CLD trust depends on the trusted updater, not the CVD outer signature.

Raw helper/daemon stdout/stderr is discarded. Failure is generic and fail-closed. The current code
has no structured native failure diagnostics; selected-image isolated acceptance must capture
safe operator evidence independently without exposing data/secrets. No configuration HTTP route.

Helper waits are 30 seconds; configuration/hash await deadlines are 15 seconds. Existing outer
startup remains 120 seconds. Hashing in a read-only thread can finish after cancellation; it never
launches or writes. Every acquired native child is registered before yielding. A cancelled pending
spawn remains an owned task and reaps a late child; no hard native spawn bound is claimed.
TERM-three/KILL-two-second helper cleanup reports uncertainty. Whole-process/native PID containment
and platform shutdown are still [acceptance rows](google-scanner-acceptance-preparation.md).

The runtime is single-attempt and expects fresh ephemeral storage on each native container start.
Persisted CLD/state or leftover temp storage denies initial preparation; verify actual platform
restart filesystem semantics before activation. Do not delete/relabel existing production data.

## Checks and next checkpoint

Mocked processes/filesystem bytes live only in backend tests. Existing backend `.dockerignore`
excludes tests and caches. Future scanner packaging must preserve that separation, and release
review must verify final layers contain genuine components only. No fixtures enter release data.

Source phases are verified from the saved log for
[checkpoint 15](../hackathon/scanner-runtime-checkpoint-2026-10-12.md): 1414 backend/94.10%, Trust,
frontend/docs tests, audits/builds. Current hashes match, pasted numeric exit omitted. No scanner
executable or production database was used; preserve the log rather than rerun for a truncated paste.
The proposed [artifact/release design](../hackathon/scanner-artifact-design-2026-10-12.md) defines
source packaging, real inputs and a separate guardrail PR; obtain signed
artifact/SBOM/provenance, isolated Linux scanner/parser/update/signal evidence and measured sizing.
All live cloud actions remain owner Cloud Shell checkpoints. One production environment; Tasks
**PAUSED**; Zynth sign-in later. No mock/stub runtime or fake records may be deployed.
