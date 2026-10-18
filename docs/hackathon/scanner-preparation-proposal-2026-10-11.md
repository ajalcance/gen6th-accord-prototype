# Scanner readiness and packaging proposal — October 11

Status: **Implemented; all full-check-8 phases verified October 12; no cloud execution.**
SQL/Redis/migration-runner source passed the owner full gate. Scanner image/configuration,
live definitions and real inspection remain unaccepted. This is the next bounded source unit.

## Existing behavior and gap

`ClamdScanner` restricts connections to explicit loopback, streams at most 10 MiB, limits scan
concurrency to two and bounds the scan workflow to 20 seconds. It checks engine/definition
receipts before and after each scan, rejecting definitions older than 48 hours, excessive future
dates, changed receipts, malware verdicts and unavailable/ambiguous responses. Keep these guards.
Its command adapter bounds responses; an open TCP port alone proves none of those capabilities.

## Proposed implementation

- Add a callable, typed scanner readiness probe in the application image, using the existing
  loopback command adapter and definition-receipt validator. Require exact PING/PONG and a
  valid VERSION receipt within a short overall deadline. Close streams on success/failure.
- Provide a CLI that prints fixed generic outcomes and exits nonzero for stale/missing/malformed
  definitions, connection failure, timeout or unexpected responses. No uploaded pixels, filenames,
  arbitrary scanner commands, endpoint override or shell command belongs to this probe.
- Test valid readiness, every denial, bounded responses/deadline and cleanup using synthetic
  receipts/mock streams only. Existing scan denial and freshness behavior remain unchanged.
- Record a non-deployable scanner contract: loopback 3310, no public ingress, official-image
  lineage with digest/signature evidence still pending, non-root runtime/configuration review,
  private scan streams, definition updates and startup/shutdown/reload/resource acceptance.
- Document how the callable must later be wired into application startup readiness when
  inspection is enabled. A source CLI alone is not a Cloud Run native startup probe or an
  active deployment check. Do not add routes, activate capabilities or change app startup here.
- Update PLAN/LESSONS/current-state/SECURITY/CHANGELOG; run focused/static checks, then the
  owner/CI full gate with before/after source and contract fingerprints.

## Minimum workable sizing and definition lifecycle

ClamAV's official Docker guidance lists **3 GiB minimum, 4 GiB preferred** memory and describes
reload peaks. These are general documented recommendations, not measurements of this topology.
Do not choose a tiny scanner allocation merely because SQL/Redis already use minimum sizing.
[ClamAV Docker requirements](https://docs.clamav.net/manual/Installing/Docker.html).

Prepare a measured acceptance plan for cold start, definitions download/storage, scan concurrency,
reload and stale-definition denial. Keep exact container memory/CPU/storage allocations pending
that plan and platform review; writable definition storage and update work also consume capacity.
FreshClam/database loading and continuous updates require explicit lifecycle/egress/CPU design,
not an assumption that a request-driven sidecar stays current while idle. Verify definitions at
use even after startup succeeds. A PING/VERSION probe proves protocol/freshness only; real benign
and malware-test inspection belongs to a later isolated owner runtime acceptance checkpoint.

No image pull, package install, scanner start, definition download, release workflow/guard change,
resource creation/resize, or cloud mutation is authorized by this proposal. Signed immutable
release/import and owner-run cloud checkpoints remain required; Tasks stays paused, Zynth later.

## Implementation and acceptance boundary

`accord.personas.scanner_probe.probe_scanner()` returns a typed receipt only after exact PONG
and the existing validated VERSION receipt within five seconds at 127.0.0.1:3310. The CLI
`python -m accord.personas.scanner_probe` accepts no arguments and prints a fixed outcome.
No application route, startup hook, capability activation, scanner process or install was added.
The existing stream adapter now bounds normal close waits to one second and closes without
waiting on cancellation, preserving the outer deadline. All scan verdict/freshness/size/concurrency
protections remain unchanged. Real in-memory StreamReader tests cover truncated/oversized frames.

The non-deployable [scanner contract](../../deploy/google/scanner-contract.json) and
[packaging notes](../../deploy/google/README.md#scanner-contract) record remaining review and
runtime acceptance, including update/reload/idle resource tests and container identity limits.
The [runtime evidence matrix](../runbooks/google-scanner-acceptance-preparation.md) specifies
the measurements needed before selecting resource/update/platform allocations; all rows pending.
Daemon configuration must not turn skipped/limit-exceeded scans into clean results; review
selected-version settings against the [official configuration sample](https://github.com/Cisco-Talos/clamav/blob/main/etc/clamd.conf.sample).
No daemon configuration or guard was changed here. Live protocol/freshness and actual inspection
remain separate owner acceptance; no pixels or production connection were used in these tests.

Verification: **40 focused tests passed**, covering the new probe/cleanup plus existing provider
denials; full backend Ruff/Black/mypy, targeted Bandit, DoD and whitespace checks passed.
All full-check-8 phases pass as recorded below; the prior migration full gate is historical for
this changed source. The new callable has not contacted a real scanner.

Current source fingerprint: **699 files** (same population as the handoff):
`317ca878391075d442f2bb344a6296af15e9aa2321e93156560afe9d1baee3bf`.
Scanner contract SHA-256:
`f101fbd6f9c89b4c3a70530a6db7723df043a2b380190ff5ea8d9de5a7fd0292`.
Unchanged SQL proxy contract SHA-256:
`2cd885091fb51e25f8dd90e6f7dddeba9861959063f9d1bcabba884a149e15d8`.
The owner checkpoint prints all values before/after. This source population excludes dependency
manifests, Dockerfiles and most deploy files; it does not replace complete signed release evidence.

### First owner full gate and timing repair

`full-check-7` exited **2**: **1212 passed, 1 failed**, 152.14 seconds, **93.58% coverage**.
Source and both contract fingerprints matched before/after the original 699-file snapshot
`de9cfedf03bda2484a761a54eed7075e7d23b550f04ba9395dcec38ad5b1302c`.
Log SHA-256: `b1da874fc49857421029db0d750a840669aa1ace78d193029900cff171b47714`.
DoD passed separately; Trust/frontend/docs-site phases were not reached by that failed full gate.

Full trace shows DID NOT RAISE for the future-six-minute definition fixture. Its timestamp was
generated at collection and aged into the accepted five-minute future window before execution.
The probe behaved correctly. Generate relative-age replies inside the running test instead;
add fixed-clock tests for exact 48-hour/five-minute acceptance and one-second-outside denial.
Production code, freshness thresholds and contracts are unchanged by this repair.
The new fingerprint above binds the corrected tests; full-check-8 verifies the repair.

### Corrected full gate — verified October 12

The complete `full-check-8.log` confirms **1217 backend tests passed**, **93.58% coverage**,
154.97 seconds, followed by successful Trust, 514 frontend and 31 docs-site tests, both builds
and JS audits. No make failure is recorded; it reaches the final docs-site build. The pasted
report omits the numeric make exit status, so no independently captured exit code is claimed.
The separate owner DoD passed; current local DoD also passes (65 ADRs, 154 standards).
Go analysis reports no reachable vulnerabilities, not zero imported/module advisories.
Log SHA-256: `bdfd429fd7c1512846cdb7fb8bc7ed08ae8346e7aff35ee1233c1338f6c403b7`.
Supplied post-run source and both contract hashes match the current verified snapshot above.
The paste omits the leading pre-run portion; this is not a separately captured before/after log
binding. Keep execution evidence distinct from complete signed release and live acceptance.
Next proposed source unit: [production SQL privilege separation](sql-role-preparation-proposal-2026-10-12.md).
