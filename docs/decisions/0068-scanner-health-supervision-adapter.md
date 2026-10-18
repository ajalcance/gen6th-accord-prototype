# ADR-0068 — Scanner health and supervision source adapter

Date: 2026-10-12. Status: accepted for source preparation; runtime/image acceptance pending.

## Context

Owner approved the next source unit in the [packaging review](../hackathon/scanner-packaging-review-2026-10-12.md).
Existing inspection/probe guards are accepted; upstream default bootstrap and child supervision
do not establish Accord's required definition validation, native health or bounded cleanup.
No exact scanner image/version-specific configuration or release integration is accepted yet.

## Decision

Prepare an independent `accord.scanner` adapter with a health-only ASGI factory and typed
supervisor around an explicitly supplied internal managed runtime. There is no default runtime,
process launcher, shell/argv/endpoint input, new dependency or activated image entrypoint.
Future packaging must supply a reviewed runtime whose prepare method validates selected
configuration, writable ownership and bootstrap databases, with database load testing enabled.
The adapter calls prepare before start; that interface is not proof of real validation today.
The runtime registers each child before yielding so cancellation can clean partial starts.
Require exactly clamd and FreshClam live children after start. Missing/exited children fail closed.

Reuse unchanged fixed-loopback PING/VERSION receipt validation. Startup has a cooperative
120-second source candidate budget, with two-second polling and five-second probe attempts.
Native HTTP can answer starting/503 while preparation runs; only current successful freshness
and two live children produce ready/200. Probe failures deny until recovery; a terminated runner,
child failure, stale success or stopping never returns healthy. No data/configuration/command
routes or private response values. Linux/non-root is required at factory construction.

On cancellation/TERM via eventual ASGI lifespan, mark stopping before cancelling supervision.
TERM all registered live children, allow three seconds, KILL remaining children, then allow two
seconds to reap. Any signal/reap failure or surviving child is a cleanup failure. Await runner
completion at most seven seconds. Cooperative startup/probe cancellation and eventual native
process containment remain distinct from hard termination guarantees.

## Consequences and acceptance

Synthetic providers/children test ordering, denied/healthy/stale/recovering states, partial launch,
child failure, cancellation, TERM/KILL escalation and cleanup deadlines. No real scanner or
definitions are run. Existing application scan, probe, startup, SQL/TLS/audit/retention guards,
release workflow and eight frozen contracts stay unchanged. Owner full gate follows source freeze.

The managed-runtime implementation, exact image/configuration, native health port/exposure,
real signal/child reaping, safe definitions and measured resources remain pending packaging.
No source health result establishes clean inspection, update completeness, PID-1 behavior or
production readiness. A failed supervisor reports 503; native restart/whole-container exit is
not proven by this adapter. Scanner signing needs its own owner-approved guardrail PR.
One production environment; Tasks paused; Zynth later; owner Cloud Shell mutations only.
