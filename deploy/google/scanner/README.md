# Scanner packaging inputs

Source preparation under ADR-0070; no image or executable build recipe exists yet.
The production ASGI factory is `accord.scanner.production:create_app`. It constructs
`ScannerRuntime` directly, with no provider argument, development mode or fixture fallback.
An executable server command is deferred: proposed native health port 8091 requires a
non-loopback listener, which the existing Ruff S104/Bandit B104 guards reject. Review
intentional network exposure in the separate guardrail PR before implementing that command;
no suppression, alternative spelling or guard configuration change is introduced here.
Proposed [ADR-0071](../../../docs/decisions/0071-scanner-explicit-container-health-launch.md) reviews
explicit container configuration with separate command/topology checks, keeping Python guards.
See [input review](../../../docs/hackathon/scanner-build-input-review-2026-10-12.md) for published
archive hashes, candidate toolchain and the next read-only registry lookup; locks remain incomplete.

`accord.scanner.seed_policy.emit_configuration` is a build-only root/Linux/amd64
operation, not imported by the production entrypoint. A future reviewed assembly must
provide the three genuine CVDs, their independently acquired SHA-256 values and the
reviewed `/usr/bin/sigtool` executable hash. It checks exact inventory/permissions,
bounded no-follow file hashes, native signature verification with a 30-second limit,
and unchanged inputs before emitting exact config bytes and the real manifest.
No definitions, digest templates, downloads, shell commands or sample records are supplied.
An incomplete or nonempty config directory is denied; failures require a fresh assembly.

The proposed final source allowlist is in `source-files.txt`, relative to `backend/`.
It contains only the required package/runtime/probe/decoder closure, excludes this
build-only emitter and every test. Native libraries, Python dependencies and notices
remain additional required payload inputs. Validate all inherited/final layers too.

Before writing an executable Dockerfile, resolve and review exact signed ClamAV source,
base/builder digests, native toolchain/package locks, Python transitive hashes and flags.
These pins are absent today. Never substitute example hashes or mutable image tags.
One worker, disabled access logs/proxy trust and a two-second ASGI request drain plus
the existing seven-second supervisor stop remain proposed launch settings, unimplemented
and unmeasured until that review. A loopback-only substitute would not prove native probing.

Separate release guard integration and actual Linux import/load/update/signals/resources,
license/layer inspection, SBOM/scan/signatures remain pending. No build/install/cloud
action is authorized by these files. Tasks remains paused; production contains no stubs.
