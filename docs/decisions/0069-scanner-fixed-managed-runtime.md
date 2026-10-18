# ADR-0069 — Fixed scanner configuration and managed process runtime

Date: 2026-10-12. Status: accepted for source preparation; image/native acceptance pending.

## Context

Owner approved the [candidate/runtime review](../hackathon/scanner-runtime-review-2026-10-12.md)
and explicitly requires no stubs or mock data on the live server. ADR-0068 supplies supervision,
but its required runtime must validate real files and own real native processes. Registry metadata
does not prove image provenance. Upstream seeded database formats/layout remain uninspected.

## Decision

Add `policy`, `filesystem`, `launcher` and `runtime` within `accord.scanner`; preserve the existing
probe, scan, supervision and release guards. `ScannerRuntime()` requires Linux x86_64, UID 100,
and the clamav account bound to that UID. No default app, public executable/path/argv input,
environment-driven configuration, application Settings, credential or fixture fallback.

Fixed root-owned configuration files must match exact source policy bytes. Reject extra files,
duplicates/unknown directives by exact comparison, symlinks, writable parents, unsafe ownership,
hardlinks, set-ID files and descriptor metadata changes. Private UID-100 data/temp directories
require mode 0700; parents remain root-owned. Each database is bounded to 256 MiB; reads stream
through 1 MiB chunks. Read-only hashing runs off the event loop with a 15-second await deadline;
an outstanding cancelled read cannot modify files or launch a process.

Packaging must supply genuine main/daily/bytecode CVD files and a root-owned `seeds.json` mapping
their exact names to release-bound SHA-256 digests. No seed manifest or definitions are generated
by this source unit. Require a fresh directory containing exactly those three files; reject CLD
as an initial seed. This is an artifact/ownership precondition, not a manifest signature verifier.
The eventual signed image/provenance must bind the manifest and actual definitions.

Run fixed sigtool --info checks on each CVD, then recheck their bound bytes. Run FreshClam once
with TestDatabases enabled and official sources. Permit exactly one CVD/CLD per official database
plus FreshClam's state file after this trusted update; reject extra local signatures. Require a
separate clamscan database load/compile with EOF stdin, even if the updater reports no change.
This transient empty stream is a database initialization check, not a saved record, mock data or
clean-inspection acceptance. Bind database hashes before/after load and immediately before launch.

The matching [sigtool source](https://github.com/Cisco-Talos/clamav/blob/5853e1396777bae4d909cd3dd44f58352e7cf9b3/sigtool/sigtool.c)
verifies CVD inside --info; [clamscan](https://github.com/Cisco-Talos/clamav/blob/5853e1396777bae4d909cd3dd44f58352e7cf9b3/clamscan/manager.c)
loads/compiles databases before stdin processing. CLD remains the trusted updater path, not a
claim of the same outer CVD signature. Actual selected-image command semantics remain untested.

Candidate daemon limits: loopback 3310, stream 10M, two threads, queue/backlog four, socket waits
five seconds, send wait 1000 ms, file 10M/scan 50M, recursion 16/files 1000, ZIP scan 20000 ms,
AlertExceedsMax, official databases and signed bytecode; concurrent reload enabled. FreshClam
checks 12/day with connect/read waits five/ten seconds and fixed clamd notification only in the
long-lived updater config. These are finite source candidates, not measured resource allocations
or proof that every engine limit returns a detectable rejection. Existing 20-second at-use guards
remain unchanged. Native limit/update/reload behavior must pass the acceptance matrix.

Use absolute exec vectors, explicit minimal environment, fixed working directory and closed stdin;
discard raw process output. Temporary helper handles are distinct from the public clamd/FreshClam
children. Helpers have 30-second waits and TERM-three/KILL-two-second cleanup. Register acquisition
before yielding. Cancellation waits one second for acquisition; a still-pending task stays owned
and closes a late child when it arrives. Failed acquisition/cleanup prevents reuse/readiness.
This does not guarantee OS spawn completion or hard container shutdown within that second.
Existing cooperative supervisor startup 120 seconds/stop seven seconds remain authoritative.

## Consequences and acceptance

New mocked process and temporary filesystem tests exercise denial/order/cancellation boundaries;
all synthetic bytes/handles stay in `backend/tests/`, excluded by the existing backend Docker
context. No real executable, definition download, image build or cloud mutation occurs here.
No production runtime imports test providers, supplies fabricated digests or returns mock receipts.

Image assembly must provide compatible pinned Python/libc dependencies, verified executable layout,
genuine CVD seeds, release-bound policy and complete SBOM/provenance/signatures. Directly using the
upstream image or copying a CLD seed does not satisfy this runtime. Actual parser/engine behavior,
native signals, pending-spawn containment, ephemeral fresh-directory restarts, health port/private
exposure and measured minimum resources remain pending. Release workflow integration is a separate
owner-approved guardrail PR. Owner full disposable gate follows source freeze; owner Cloud Shell
checkpoints follow reviewed signed release and isolated native evidence. Tasks paused; Zynth later.
