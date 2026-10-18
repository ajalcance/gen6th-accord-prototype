# Developer Guide

How to set up, run, test, branch, and ship in Gen6th Accord.

## Prerequisites

- Python 3.12+
- Node 22 (pinned in `.nvmrc`; run `nvm use`) — for frontend/ and docs-site/
- (optional) Docker + Docker Compose for the full stack
- `pre-commit` (`pip install pre-commit`)

## Set up

```bash
git clone https://github.com/ajalcance/gen6th-accord.git
cd gen6th-accord
pre-commit install

cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp ../.env.example ../.env    # fill in local values
```

```bash
cd frontend && npm ci
```

```bash
cd docs-site && npm ci
```

## Run

```bash
uvicorn accord.main:app --reload    # http://localhost:8000
# health: GET /health ; docs (non-prod): /docs
```

```bash
cd frontend && npm run dev    # http://localhost:3000
```

```bash
cd docs-site && npm run dev   # http://localhost:3000 (different port if run alongside frontend)
```

## Test & gate

```bash
make backend    # ruff, black, mypy, bandit, pip-audit, pytest
make frontend   # eslint, prettier, tsc, npm audit, vitest, next build
make docs-site  # eslint, prettier, npm audit, vitest (public-only rule), next build
make check      # full gate — everything above
make dod-check  # doc-consistency guards
make fmt        # auto-format (backend + frontend + docs-site)
```

## Database & migrations

```bash
cd backend
# after adding/altering a model (imported in accord/db/models/__init__.py):
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Branch & ship

- Branch off `main`: `feat/*`, `fix/*`, `security/*`, `refactor/*`, `docs/*`, `chore/*`. Keep them short-lived.
- Conventional Commit messages; one logical change per commit.
- Open a PR → CI runs the gate + doc-guards → squash-merge when green.
- Complete the **Definition of Done** ([`../CLAUDE.md`](../CLAUDE.md) §2) in the same PR.
