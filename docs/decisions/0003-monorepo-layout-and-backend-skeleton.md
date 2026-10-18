# 0003. Monorepo layout and backend skeleton conventions

- **Status:** Accepted. Decision 4 is superseded by ADR-0016 (implemented 2026-09-25): tests run
  on a throwaway PostgreSQL through Testcontainers, not in-memory SQLite.
- **Date:** initial scaffold
- **Deciders:** project owner

## Context

A new project needs a consistent layout and a backend skeleton that is secure and testable from
the first commit, so features are added by filling in a known structure rather than inventing one.

## Decision

1. **Monorepo layout.** Top-level `backend/`, `frontend/`, `docs-site/`, `deploy/`, `scripts/`, `docs/`. CI is path-filtered so each area's gate runs only when it changes.
2. **Backend package** at `backend/accord/` with a thin **app factory** (`main.py`), a
   **fail-closed settings** module (`config.py`), **structured JSON logging** (`logger.py`), and a
   **DB layer** (`db/` — declarative base + async engine/session + models package). Business logic
   goes in `services/`; routers stay thin.
3. **Migrations** via Alembic (async env) under `backend/migrations/`.
4. **Tests** use in-memory SQLite (`conftest.py`) so the suite is fast and needs no live database.
5. **One command gate** — `make check` runs ruff/black/mypy/bandit/pip-audit/pytest; `make dod-check`
   runs the documentation-consistency guards.

## Consequences

- New contributors (and AI agents) find a predictable structure; the gate is a single command.
- The as-built page must name every `backend/accord/` module + top-level dir (enforced by
  `dod-check`), keeping docs honest.

## Alternatives considered

- **Polyrepo / no skeleton.** Rejected: higher coordination cost and inconsistent structure across
  projects — the problem this template exists to solve.
