# ADR-0022 — Local-first delivery before cloud infrastructure

- **Date:** 2026-10-01
- **Status:** Proposed for PR review; owner gate/startup verified, browser rehearsal pending

## Context

The owner approved adapting the supplied local-first delivery process before further product
work. No application server is provisioned. Other projects occupy common development ports
on this Mac. Local work must preserve the existing security and release gates.

## Decision

1. Reuse the backend/frontend Dockerfiles and mirror deployment service definitions in a
   standalone local Compose file, without changing production ports, TLS or signed deployment.
   Build the current checkout. Use only synthetic development data.
2. Publish app, PostgreSQL and Redis on `127.0.0.1:18660`, `18662` and `18663`. Serve public
   docs separately in the foreground on `127.0.0.1:18661` through the existing loader.
   Probe IPv4 and IPv6 before startup. Refuse collisions and uncertain errors. Never kill
   another process or select a different port silently. Docker remains the final bind arbiter.
3. Derive project names and image tags from the canonical checkout path. Networks and
   database volumes belong to that project. Shutdown preserves named volumes. Provide no
   automatic reset or volume deletion command.
4. Generate local secrets once in `.cache/local-stack/runtime.env` (mode `600`, directory
   `700`). Refuse symlinks, unsafe modes, changed checkout identity and non-local databases.
   Never read root `.env`, print merged secrets, import production data, change host trust or
   install machine-wide agent policies.
5. Support Compose >= 2.24.4. Use ordinary YAML so the existing YAML guard can validate it.
   A fault-tested parity check compares local services with production plus its build override,
   allowing only the explicit local ports, credentials, proxy config and development environment.
   Inspect the resolved model privately before lifecycle commands. Retain read-only application
   filesystems, non-root application images and no-new-privileges.
6. Include the existing Go trust gate in `make check`. Preserve PR and `main` CI, path filters,
   owner labels and signed release controls. Local evidence cannot authorize a merge or
   release while required CI cannot run.
7. Finish local checks and manual use before opening a feature PR. Temporary integration
   branches are disposable rehearsals; feature branches still start from `main` and get their
   own PRs. This tooling/guard work needs a separate owner-reviewed PR and owner-applied
   `guardrail-change`, rather than extending the Codex permission-policy PR.

## Consequences and verification

`make local-init`, `local-doctor`, `local-up`, `local-down`, `local-status`, `local-smoke`
and `local-docs` are the owner command surface. Startup builds production-style app images,
runs migrations, waits for long-lived services and probes the proxied app and health endpoint.
Fault tests run through `make guard-tests` and CI. Live Docker evidence requires the owner's
Mac Terminal because the agent cannot access the daemon (ADR-0020).

This starts the current scaffold, not all planned Accord services. Local HTTP does not prove
production TLS, IAM, identity-provider or outbound-integration behavior. Populated older-schema
migration, rollback and merged-tree reconciliation remain follow-ups. Cloud staging,
production, domain setup and artifact promotion need their own authorization and implementation.
Retain local Compose when production moves to Cloud Run.

## References

- [Local runbook](../runbooks/local-first-delivery.md)
- [Compose file selection](https://docs.docker.com/reference/cli/docker/compose/)
- [Project isolation](https://docs.docker.com/compose/how-tos/project-name/)
- [Shutdown and volume retention](https://docs.docker.com/reference/cli/docker/compose/down/)
