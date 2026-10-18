# Architecture Decision Records (ADRs)

One file per architectural decision — the log of *why*. See [ADR-0001](0001-record-architecture-decisions.md)
for the rationale, and [`template.md`](template.md) for the format.

**When to write one:** any decision that shapes structure, security, data, dependencies, or a
convention future contributors must follow. New decision → new ADR (next number); don't decide
silently.

## Index

- [ADR-0039: Workspace gallery without sample workflows](0039-workspace-gallery-without-sample-flows.md) — owner-requested empty default, consolidated actions and footer readiness; no activation.
- [ADR-0038: Private braces depth backport](0038-private-braces-depth-backport.md) — exact owner-approved artifact, bounded depth, source identity and temporary maintenance; full validation pending.
- [ADR-0037: Session-gated persona writes](0037-session-gated-persona-writes.md) — unmounted write router, separate transport and authored-draft recovery; activation gated.
- [ADR-0036: Record-bound governance reads](0036-record-bound-governance-reads.md) — authorized discovery, saved-version panels and isolated ASGI integration proof; unmounted.
- [ADR-0035: Visible governance and draft recovery](0035-visible-governance-and-draft-recovery.md) — separately labelled local contract examples; no API activation.
- [ADR-0030: Task-focused persona console](0030-task-focused-persona-console.md) — proposed, owner-authorized fourth-pass local implementation.
- [ADR-0031: Private evidence quarantine](0031-private-evidence-quarantine.md) — internal encrypted intake; provider/runtime gates remain.
- [ADR-0032: Persona connection contracts](0032-persona-connection-contracts.md) — prepared transport, disconnected by default.
- [ADR-0033: Bounded persona reads](0033-bounded-persona-read-contracts.md) — gallery, history and private evidence metadata.
- [ADR-0034: Session-gated persona read surface](0034-session-gated-persona-read-surface.md) — prepared verifier, unregistered queries and separate saved-record UI.

- [ADR-0029: Compact persona console](0029-compact-persona-console.md) — proposed, third-pass implementation authorized.

- [ADR-0028: Persona console design system](0028-persona-console-design-system.md) — proposed, second-pass implementation authorized.

- [ADR-0027: Durable internal persona detection](0027-durable-persona-detection.md) — proposed, implemented for review.

- [0001 — Record architecture decisions](0001-record-architecture-decisions.md)
- [0002 — Defense-in-depth against malicious & AI-generated code](0002-defense-in-depth-against-malicious-code.md)
- [0003 — Monorepo layout and backend skeleton conventions](0003-monorepo-layout-and-backend-skeleton.md)
- [0004 — Agent-resistant guardrails](0004-agent-resistant-guardrails.md)
- [0005 — Trunk-based branching](0005-trunk-based-branching.md)
- [0006 — Engineering process and control system](0006-engineering-process-and-control-system.md)
- [0007 — Low-friction agent permission model](0007-agent-permission-model.md)
- [0008 — Experience-to-control loop](0008-experience-to-control-loop.md)
- [0009 — Standards suite with honest enforcement markers](0009-standards-suite-with-honest-enforcement.md)
- [0010 — Release evidence chain](0010-release-evidence-chain.md)
- [0011 — A readiness verdict belongs to the artifact, not to a checkout](0011-readiness-belongs-to-the-artifact.md)
- [0012 — Client-reported events are data, never evidence](0012-client-reported-events.md)
- [0013 — Adopt the Gen6th Accord architecture v1.0 and its addenda](0013-accord-architecture-baseline.md)
- [0014 — Hybrid-ready deployment, global identity and the trust layer](0014-deployment-cells-and-trust-layer.md)
- [0015 — Identity and AI-agent governance through self-hosted Zynth Auth](0015-identity-and-agent-governance-with-zynth-auth.md)
- [0016 — Operations, data lifecycle, security, mobile and the engineering baseline](0016-operations-data-security-mobile-and-engineering-baseline.md)
- [0017 — Primary GCP region: asia-southeast1 (Singapore)](0017-primary-region-asia-southeast1.md)
- [0018 — CI integrity: every check proves it can see what it looks for](0018-ci-integrity-every-check-proves-it-can-see.md)
- [0019 — The agent is confined to the project and cannot approve its own work](0019-agent-confined-to-the-project.md)
- [0020 — The agent reaches GitHub with its own repo-only token and never leaves the sandbox](0020-agent-github-identity-and-no-sandbox-escape.md)
- [0021 — Codex uses an owner-managed agent boundary beside Claude Code](0021-codex-managed-agent-boundary.md)
- [0022 — Local-first delivery before cloud infrastructure](0022-local-first-delivery.md)
- [0023 — AI Persona Passport as the hackathon prototype](0023-ai-persona-passport-prototype.md)
- [0024 — Persona versions and durable events share one PostgreSQL transaction](0024-persona-transactional-persistence.md)
- [0025 — Human review decisions bind immutable persona versions](0025-version-bound-human-review.md)
- [0026 — Campaign permission binds the version, review, assets and recipient](0026-scoped-campaign-permission.md)

- [0040 — Real records and Zynth session boundary](0040-real-records-and-zynth-session-boundary.md)
- [0041 — Real creation and data inventory](0041-real-creation-and-data-inventory.md)
- [0042 — Records presentation and editing](0042-records-presentation-and-editing.md)
- [0043 — Creation completion screen](0043-creation-completion-screen.md)
- [0044 — Inspected version-bound portraits](0044-inspected-version-bound-portraits.md)
- [0045 — Portrait-focused creation layout](0045-portrait-focused-creation-layout.md)
- [0046 — System Capture terminology](0046-system-capture-terminology.md)
- [0047 — Required registration portrait](0047-required-registration-portrait.md)
- [0048 — Synthetic-performer identity and reference-based search](0048-synthetic-performer-identity-and-search.md)
- [0049 — Exact portrait search foundation](0049-exact-portrait-search-foundation.md)
- [0050 — Analysis capture and reference approval](0050-analysis-capture-and-reference-approval.md)
- [0051 — Explicit face selection and measured representations](0051-explicit-face-representation.md)
- [0052 — Private calibrated similarity serving](0052-private-calibrated-similarity.md)
- [0053 — Grounded investigation history](0053-grounded-investigation-history.md)
- [0054 — Production scopes and passport integrity](0054-production-passport-integrity.md)
- [0055 — Opt-in Google runtime and durable reference jobs](0055-google-durable-runtime.md)

- [0056 — Inspected evidence and explicit asset enrollment](0056-inspected-evidence-and-asset-enrollment.md)
- [0057 — Persisted issuance and approved public passports](0057-persisted-issuance-and-approved-public-passports.md)
- [0058 — Offline recognition evidence and local report inspection](0058-offline-recognition-evidence.md)
- [0059 — Performer workspace navigation and progressive capture](0059-performer-workspace-navigation.md)
- [0060 — Attributed performer identity and contributor credits](0060-attributed-performer-identity-and-credits.md)
- [0061 — Production-first Google bootstrap](0061-production-first-google-bootstrap.md)
- [0062 — Accountable performer lifecycle and controlled use](0062-accountable-performer-lifecycle.md)
- [0063 — Private SQL proxy transport and bounded runtime pools](0063-private-sql-proxy-transport.md)
- [0064 — Distinct production SQL runtime privileges](0064-distinct-production-sql-roles.md)
- [0065 — Production startup composition](0065-production-startup-composition.md)
- [0066 — Reference-only production runtime](0066-reference-only-runtime.md)
- [0067 — Compliance worker lifecycle and progress health](0067-compliance-worker-lifecycle.md)
- [0068 — Scanner health and supervision source adapter](0068-scanner-health-supervision-adapter.md)
- [0069 — Fixed scanner configuration and managed process runtime](0069-scanner-fixed-managed-runtime.md)
- [0070 — Scanner artifact assembly and release integration design (proposed)](0070-scanner-artifact-release-design.md)
- [0071 — Explicit container launch for scanner native health (proposed)](0071-scanner-explicit-container-health-launch.md)
- [0072 — Required-input scanner artifact verification entry point (separate PR preparation)](0072-scanner-artifact-verification-entrypoint.md)
- [0073 — Mandatory scanner release assembly boundaries (separate PR preparation)](0073-scanner-release-assembly-boundaries.md)
- [0074 — Advisory reviewer brief on Gemini](0074-advisory-reviewer-brief.md)
- [0075 — Record-bound paper passport booklet](0075-record-bound-passport-booklet.md)
