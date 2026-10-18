# 0013. Adopt the Gen6th Accord architecture v1.0 and its addenda

- **Status:** Accepted
- **Date:** 2026-09-23
- **Deciders:** Albert Alcance (founder)

## Context

Gen6th Accord was designed before this repository existed. Two source documents are held by the founder, outside the repository:
- the *Gen6th Founding Paper v1*, with the principles Accord puts into practice;
- the *Gen6th Accord Commercial Product and Technical Architecture v1.0* (23 September 2026), approved for implementation.

The design was then refined in three approved addenda. Contributors, human or AI, need one place that says which design is current.

## Decision

1. Architecture v1.0 is the **baseline**. Addenda 01–03 in [`docs/architecture/`](../architecture/README.md) amend it, and a later document overrides an earlier one where they conflict.
2. [`docs/architecture/README.md`](../architecture/README.md) is the **design at a glance**. It must be corrected whenever a source document changes.
3. The decisions in the addenda are recorded as ADRs 0014 (D-01 to D-11), 0015 (D-12 to D-20) and 0016 (D-21 to D-33). The `D-` identifiers stay stable, so the addenda and ADRs can cite each other.
4. [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) remains the template's target-design page and points to the Accord design. [`docs/architecture/current-state.md`](../architecture/current-state.md) remains the as-built page.

## Consequences

- One chain of authority: v1.0, then the addenda, then new ADRs.
- The source PDFs are not in the repository. The addenda summarise what changed, so the repository is usable without them, but v1.0 detail (full capability lists, appendices) still requires the PDF.
- A new design decision needs a new ADR (REL-015), not a silent edit to an addendum.

## Alternatives considered

- **Rewrite v1.0 as Markdown in the repo.** Rejected for now: it is a large document, already approved, and a rewrite risks drift. It can be imported later.
- **One ADR per `D-` decision (33 ADRs).** Rejected: the addenda already give each decision its full reasoning. Four grouped ADRs keep the index readable, and new decisions still get one ADR each.
