# ADR-0071 — Explicit container launch for scanner native health

Date: 2026-10-12. Status: owner approved preparation; isolated candidate, separate PR and deployment pending.

## Context

Checkpoint 16 accepts source/config-emitter tests, not an image. An attempted Python all-interface
health launch was rejected by Ruff S104 and Bandit B104 and removed. The guards remain unchanged.
The existing API Dockerfile explicitly declares Uvicorn's binding in its exec-form container CMD.
Scanner packaging needs a reviewed deployment boundary rather than a Python guard suppression.

Cloud Run's [runtime contract](https://docs.cloud.google.com/run/docs/container-contract) requires
one ingress container and describes its binding, explicitly excluding sidecars from that rule.
The proposed scanner listener must still prove native sidecar probing and private exposure.
Its status route cannot expose definitions, filenames, evidence, records or runtime exceptions.

## Approved preparation decision

Keep `accord.scanner.production:create_app` directly bound to real `ScannerRuntime`. Declare fixed
deployment parameters in the future scanner Dockerfile's literal exec-form command, as the API does.
The reviewed candidate command, not an executable file or instruction to run now:

```json
["uvicorn", "accord.scanner.production:create_app", "--factory", "--host", "0.0.0.0", "--port", "8091", "--workers", "1", "--no-access-log", "--no-proxy-headers", "--no-server-header", "--lifespan", "on", "--timeout-graceful-shutdown", "2"]
```

No Python all-interface bind, computed address, S104/B104 ignore, Bandit exclusion or general
guard exception. An explicit container command is not sufficient by itself: add fail-closed
command/topology validation and fault tests in the separately owner-approved guardrail PR.
Do not implement the Dockerfile until complete genuine build inputs and the separate guardrail PR are reviewed.

Require the exact command, UID 100, sole status route, disabled docs/schema, one worker, no reload,
no proxy trust/access logs, bounded drain and existing seven-second supervisor cleanup. Reject
deployment command/args overrides, scanner ingress-port assignment, host port publication and
`UVICORN_*`/`WEB_CONCURRENCY` environment overrides. In particular, omitted CLI reload settings
must not be enabled through environment configuration. Review actual Uvicorn option behavior.

Only API is Cloud Run ingress. Scanner HTTP 8091 is a native sidecar probe; clamd protocol remains
127.0.0.1:3310. API depends on successful scanner startup health. No TCP-only readiness substitute.
The scanner has no public forwarding route, separate public service or host-published health port.
Confirm actual exposure and startup/cleanup behavior in isolated Linux and owner platform checks;
neither source tests nor the generic ingress documentation prove those properties.

Guard fault cases: changed host/port/factory/worker/lifespan/timeout/log/proxy flags, reload/env
overrides, missing scanner probe/dependency, wrong probe port, extra ingress assignment, public
scanner routing and altered commands during promotion/import. Keep existing signature/default-branch
CI/scan policies and all application guards. Do not edit guards in the source PR they happen to block.

## Consequences

This separates deployment configuration from application code without making exposure implicit.
Future command/topology validation is a new enforcement mechanism, not an active gate today.
It needs its own reviewed implementation/fault tests and owner-applied guardrail label. If rejected,
the executable listener stays unimplemented; do not revert to a hidden bind or weaken readiness.

[Build-input review](../hackathon/scanner-build-input-review-2026-10-12.md) identifies actual published
archive hashes and candidate toolchain versions, with verification/lock gaps explicit. No source,
contract, active guard/workflow, Dockerfile, image or live resource changes. The [isolated candidate](../hackathon/scanner-launch-guardrail-review-2026-10-12.md)
has 129 passing fault/CLI tests with manifest/config binding and lint/format/strict typing checks; no unchanged-source full test rerun.
Pipeline input binding and enforcement wiring remain pending. One environment, Tasks paused, no live mock data.
