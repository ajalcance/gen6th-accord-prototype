# 0063. Private SQL proxy transport and bounded runtime pools

- **Status:** Accepted for source preparation by the owner's October 11 approval;
  release integration, cloud execution and live acceptance pending
- **Date:** 2026-10-11
- **Deciders:** Repository owner

## Context

The production-first Google foundations have private Cloud SQL with ENCRYPTED_ONLY and
instance-scoped Cloud SQL Client grants. The current asyncpg engine does not supply verified
direct TLS or a connector. The owner approved the [transport proposal](../hackathon/sql-transport-proposal-2026-10-11.md)
after backend/dependency/Redis CA repairs passed the full local gate.

## Decision

Use a Cloud SQL Auth Proxy v2 sidecar on the same runtime instance, bound to
127.0.0.1:5432, selecting private IP and the existing production instance explicitly.
The proxy uses the runtime's workload identity; no downloaded key or owner credential.
Its remote connection is authenticated and encrypted; the application hop is loopback.
Database authentication and confined SQL privileges remain independent of proxy IAM.

`DATABASE_TRANSPORT=cloud_sql_proxy` is explicit. Outside development, local mode is denied
at database URL/engine resolution. Proxy URLs require postgresql+asyncpg, the agreed loopback
host/port, database, login/password and no URL query options. Invalid configuration uses
generic errors without credential-bearing URLs. Runtime engines reject known administrative
logins; migration URL resolution can retain the separately authorized operator login.
This check does not prove SQL role attributes or replace the reviewed RLS/grant boundary.

HTTP/reference and compliance engines share pool size 2, overflow 0, five-second checkout
and connect waits, and connection pre-ping. Development retains existing local SQL URLs;
the runtime capacity limits also apply there. Alembic retains NullPool and explicit operator
configuration. Migration/worker shutdown needs reviewed packaging before live execution.

Record the proxy listener, workload identities, health/start order and bounded signal drain
in a non-deployable contract. A selected immutable proxy image and verified supply chain are
required before producing launchable manifests. Existing release guards/workflows are unchanged;
their integration is a separate owner-reviewed unit. Health probes do not establish SQL role,
RLS, restore, audit-delivery or model acceptance.

## Consequences

No Python connector dependency is added. Small pools bound per-engine connections; revision
overlap, instance counts and the actual SQL ceiling still need capacity verification.
The owner preserves the existing minimum database/Redis sizing and paused Tasks queue.
Source approval authorizes no production query, grant, migration, image import or deployment.
Tests use mocks/disconnected engines and disposable PostgreSQL; live acceptance stays pending.

## Alternatives considered

- Verified direct TLS: viable but requires additional certificate/endpoint configuration.
- Python connector: viable but adds a dependency and changes the application's driver wiring.
- Direct private-IP plaintext: violates the authenticated encrypted transport requirement.
