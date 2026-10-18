# Redis CA source preparation — October 11

Implements the accepted transport preparation in ADRs 0055/0061. No new infrastructure,
activation, secret access or deployment. Tasks remains paused; Zynth remains later.

## Source behavior

`accord/cache/redis.py` now owns the shared disconnected client factory. Both the
compliance/session client and `personas/runtime_bootstrap.py` use it; response decoding
remains text for compliance/session and bytes for private similarity queries.

Outside development, or whenever Google mode is enabled, a `rediss://` address and
`REDIS_CA_CERT_PATH` are required. The path must be absolute, readable and contain a valid
CA certificate bundle. Missing/malformed configuration raises a generic error without
including certificate bytes or the mount path. No client is constructed on validation failure.
URL queries/fragments are rejected so Redis URL precedence cannot override verification.
Every TLS client sets certificate verification to required and hostname verification to true.
Connection/read timeouts are five seconds. Development retains its existing local plaintext
default; supplying a CA with a plaintext address is rejected. This does not change the
existing telemetry delivery failure policy or create a durable audit guarantee.

The service CA is runtime-mounted configuration, never baked into an image or committed.
Google documents installing all active service CAs to support rotation:
[Memorystore TLS configuration](https://docs.cloud.google.com/memorystore/docs/redis/manage-in-transit-encryption).
The source accepts a bundle containing the active and overlap CAs. Runtime certificate/name
acceptance is still unverified; a mismatch must be resolved without turning off verification.

## Evidence and limits

Owner full gate **before this CA change** passed: 776 guards (18 skipped), 1108 backend
tests with 93.12% coverage, Trust, 514 frontend tests and 31 docs-site tests, including both
builds and npm audits with zero vulnerabilities. The repair record retains the full log hash.
Both JS manifests/locks agree on sharp 0.35.5 and source-map-js 1.2.2. npm install-script
warnings were informational; no script-approval policy was changed by the agent.

CA preparation: **26 focused tests passed**, including real redis-py TLS contexts loading a
synthetic public CA, CERT_REQUIRED/hostname verification, both decoding modes, cached shared
client assembly, rejection of URL verification overrides, absent/relative/missing/malformed
CA files, development behavior and Google configuration. Expanded non-database selection:
**51 passed**. Full backend Ruff/Black/mypy and targeted Bandit passed. These checks use no
sockets, real credentials, production database, cloud calls or persisted private keys.

Current source snapshot using the handoff population: **689 files**,
`05e0b95772df03816015d66a0f055edfd6d04fc762bc3b8834d43aa9281dc4b1`.
It includes two added test files and the CA changes. Owner fourth full `make check` exited **0**:
776 guards (18 skipped), **1122 backend passed in 138.93s**, coverage **93.26%**, Trust,
514 frontend and 31 docs-site tests, builds and zero-vulnerability npm audits. DoD passed.
Log `.cache/production-bootstrap/full-check-4.log`, SHA-256:
`321fab911ede9debfc1540b42adb0f96e63c2a1e4ce1cffeaa61bfb47956be68`.
The log has no leading source fingerprint; the snapshot is not an independent execution binding.
Review/merge, exact-main green CI and signed immutable release remain separate requirements.
Next: owner-approved [SQL transport preparation](sql-transport-proposal-2026-10-11.md), implemented
with its full gate passed: 1147 backend (93.40%), matching source/contract before/after.

## Later owner Cloud Shell checkpoint requirements

Prepare final deployment manifests only with the remaining SQL, scanner/worker and ingress
designs. Use existing provisioned resources; do not repeat creation or deploy a local build.

- Pin `accord-prod-redis-ca` to reviewed secret version 1 initially and mount read-only at an
  explicit path such as `/var/run/accord/redis-ca/ca.crt`; set `REDIS_CA_CERT_PATH` to that path.
  A later rotated bundle needs an explicitly reviewed new version and revision rollout.
- Keep Redis AUTH in Secret Manager and the Redis URL in private runtime configuration.
  Use the inventory endpoint and TLS port 6378; never paste credentials into source or logs.
- API and compliance identities have recorded access to the Redis AUTH/CA secrets. The
  reference identity does not have recorded secret access; Google runtime assembly also
  requires the CA, so its narrowly scoped access/mount needs owner review before deployment.
  Do not infer access from another identity or add broad project-level secret access.
- Verify the actual runtime certificate chain and endpoint identity from the private network,
  then test dependency rejection on a wrong CA/name and actual AUTH failure without logging
  credential values. No live handshake has been performed in this preparation.
- Validate CA rotation, noeviction/capacity, retention and restart separately. A working TLS
  connection is not evidence of audit sealing or durable delivery. Keep Tasks paused through
  these checks; resume only at its separately reviewed worker acceptance checkpoint.
