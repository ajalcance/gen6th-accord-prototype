# Real creation and storage preparation

Prepared October 4, 2026 (ADR-0041). This work does not depend on Zynth tenant approval.
The production application contains no sample workflows. The creation form accepts authored
content while disconnected; saving requires the verified Zynth session and stored membership.
Drafts stay in tab memory, separated by workspace/session; refreshing loses unsaved fields.

## Verification boundary

Agent checks: 271 frontend unit tests, 15 isolated ASGI tests, lint, types, production webpack
build and client budget (166.4 kB / 250 kB) pass. Production source/chunks contain no sample
workspace imports/content. Owner's subsequent validation block exits 0 after full `make check`,
`make dod-check` and all 15 ASGI tests, with matching current fingerprints. The supplied tail
omits backend test count/coverage; do not invent those numbers. Full gate includes SQL regressions
on disposable databases, not application migration or authenticated live acceptance.
Agent-only runs remain limited by Docker access, pip bootstrap/registry DNS and browser startup.
No guard, dependency or sandbox was changed to bypass those limits. The owner-run baseline
and post-migration inventories below passed; the agent did not access the database directly.

### Owner baseline inventory — October 4, 2026

Owner output: `local-init`/`local-doctor` pass; this project's PostgreSQL/Redis are healthy.
Redis reports `# Keyspace` with no populated databases. PostgreSQL reports only
`public.alembic_version=1`, `public.audit_log=0`, `public.events=0`;
`tables_checked=3 non_migration_rows=0`, `inventory_result=empty_application_store`, `ROLLBACK`.
This establishes an empty local scaffold baseline. Persona/evidence/identity tables are not
present yet; schema migration through `0009identity`, confined runtime-role preparation,
authenticated read/write acceptance remain pending. Subsequent owner full-gate validation passes.
The output does not establish cleanliness of another database, retained dump or import source.

### Owner application migration — October 4, 2026

Owner rebuilt the current backend image and ran the one-shot migration successfully from
`0002source` through `0009identity`. PostgreSQL then reports 17 tables, including persona,
evidence, campaign and canonical identity tables; all 16 application tables have zero rows.
`tables_checked=17 non_migration_rows=0`, `inventory_result=empty_application_store`, `ROLLBACK`;
Redis remains empty. No legacy boolean fixture counts appear after migration 0008. Historical
migration descriptions contain fixture/fictional wording; this is frozen schema history, not
seeded rows or an active sample workflow. The subsequent role proof is recorded below.

### Owner restricted-role proof — October 4, 2026

Owner successfully applied `accord-runtime-role.sql`: role creation/grants commit. The read-only
application predicate under `SET LOCAL ROLE` returns `checked_role=accord_runtime` and
`runtime_role_confined=t`, followed by `ROLLBACK`. Operator re-inventory still reports all 16
application tables empty (`tables_checked=17 non_migration_rows=0`, `empty_application_store`).
Role privileges are verified. Owner completed password setup and successfully authenticated
over TCP inside PostgreSQL: `connected_role=accord_runtime`. Owner's backend Python probe also
passes: `backend_database_connection=pass role=accord_runtime endpoint=127.0.0.1:18662/accord_local`.
It used the actual session factory/privilege verifier, then disposed the engine. The password/URL
was held only in process memory. Persistent backend configuration remains pending; no running
authenticated HTTP connection or Zynth session is established. The next-chat continuation is
[the real-data handoff](../hackathon/real-data-transition-2026-10-04.md).

Current source fingerprints (secrets excluded):

```text
backend_source_sha256=ea2624bdda4ce049ff480dc2b8d76a0f4a8d616f04bb4774dfdde38bf267f848 files=181
frontend_source_sha256=3dbfb302fca80443e70fe59199a96735c7a2dce4de303d18cf296fd7741ff5a2 files=149
data_inventory_sha256=bda901031610e4b12be5e4bd2189aa7908c13f88c553f3b7d17bec08cc27cc67
```

## 1. Validate the changed source

In **Mac Terminal**, with Docker Desktop running:

```zsh
(
  cd "/path/to/gen6th-accord" || exit 1
  export PATH="/opt/homebrew/opt/node@22/bin:$PATH"
  backend/.venv/bin/python .cache/workflow-source-evidence.py
  backend/.venv/bin/python .cache/frontend-source-evidence.py
  make check && make dod-check && (cd frontend && npm run test:governance-integration)
  validation_result=$?
  backend/.venv/bin/python .cache/workflow-source-evidence.py
  backend/.venv/bin/python .cache/frontend-source-evidence.py
  shasum -a 256 deploy/accord-data-inventory.sql
  printf 'validation_exit_status=%s\n' "$validation_result"
  exit "$validation_result"
)
```

Report counts/coverage, 15 ASGI results, matching before/after fingerprints and exit status.
These database tests use disposable databases, not the application's database. Do not activate
the connection until the full block passes. Missing cached evidence scripts must be restored
from the current review record before using this convenience block in a fresh checkout.

## 2. Inventory the actual local application database

Use the existing isolated local stack. The following starts only PostgreSQL and Redis and
preserves the existing volume/password. It does not start the app, migrate or create records.
Check port owners first with `make local-doctor`; do not stop unrelated processes to free ports.

```zsh
(
  set -e
  cd "/path/to/gen6th-accord"
  make local-init
  make local-doctor
  docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
    up -d --wait postgres redis
  docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
    exec -T redis redis-cli INFO keyspace
  docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
    exec -T postgres psql --username=accord_local --dbname=accord_local \
    --set=ON_ERROR_STOP=1 < deploy/accord-data-inventory.sql
)
```

Expected: table/count notices, `non_migration_rows=0`, then either
`inventory_result=empty_database_without_application_schema` or
`inventory_result=empty_application_store`, followed by `ROLLBACK`.
The first result means tables still need migration; it does not certify a migrated app.
Redis should report no populated `dbN` lines for the empty baseline. Any keys, including queued
events or session state, require provenance review before reuse. This reports counts/expiry
statistics only; it neither reads values nor clears the cache. Do not flush it automatically.
Materialized views are counted as stored data. Foreign tables stop the inventory for explicit
source review without reading remote rows. Ordinary views hold no stored rows; their definitions
and any import sources still need schema/provenance review before use.

Any populated application table causes `populated store requires provenance review; no rows
changed`. Report those table/count notices. Do not delete rows, reset the volume, remove flags,
or weaken migration 0008. Genuine records also require review at this baseline; a count does
not classify their content. Review retention/audit obligations before choosing an empty,
separate database or retiring an old store. Do not reuse an old sample database by relabelling it.

This check covers `accord_local` in this Compose project only. Inventory each additional Accord
database/schema and retained import source separately with its own operator connection. Do not
inventory another product's databases. Backup files are not cleaned or validated by this SQL.
Before real writes, repeat after migration; after provisioning it will intentionally be populated.

## 3. Prepare empty storage without creating a persona

After a successful baseline inventory and full gate, migrate the exact local store with the
current backend image. Rebuild the migration image so an older image cannot leave the database
at scaffold revisions. This owner command starts only storage and a one-shot migration process:

```zsh
(
  set -e
  cd "/path/to/gen6th-accord"
  make local-init
  make local-doctor
  docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
    up -d --wait postgres redis
  docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
    build migrate
  docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
    run --rm --no-deps -e PERSONA_API_ENABLED=false migrate
  docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
    exec -T postgres psql --username=accord_local --dbname=accord_local \
    --set=ON_ERROR_STOP=1 --command='SELECT version_num FROM public.alembic_version;'
  docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
    exec -T postgres psql --username=accord_local --dbname=accord_local \
    --set=ON_ERROR_STOP=1 < deploy/accord-data-inventory.sql
  docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
    exec -T redis redis-cli INFO keyspace
)
```

Expected: migration head `0009identity`, persona/evidence/identity tables, zero domain rows,
`inventory_result=empty_application_store`, `ROLLBACK`, empty Redis keyspace. No membership,
persona, sample data, auth grant, application/worker startup or public deployment is created.
Report the migration head and inventory notices. A failed step stops the block; preserve output
and the volume, never skip or edit a failing migration. Image rebuilding uses pinned requirements
and may need registry access. It refreshes the local image tag; existing app containers are not
restarted by this block and can still contain older code.

### Restricted application role

After migration and empty-store proof, run this in Mac Terminal. The reviewed SQL creates
`accord_runtime` with record privileges and no superuser/BYPASSRLS/role-management capabilities.
The read-only probe uses the application's exact `ROLE_QUERY` under that role; it fails if the
role owns persona tables or can mutate membership/identity bindings. No credentials are read.

```zsh
(
  set -euo pipefail
  cd "/path/to/gen6th-accord"
  make local-doctor
  docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
    exec -T postgres psql --username=accord_local --dbname=accord_local \
    --set=ON_ERROR_STOP=1 < deploy/accord-runtime-role.sql

  PYTHONPATH=backend backend/.venv/bin/python -c '
from accord.personas.runtime_role import ROLE_QUERY
print("BEGIN READ ONLY; SET LOCAL ROLE accord_runtime;")
print("DO $probe$ BEGIN IF (" + ROLE_QUERY + ") IS DISTINCT FROM FALSE THEN")
print("RAISE EXCEPTION $$runtime role is not confined$$;")
print("END IF; END $probe$;")
print("SELECT current_user AS checked_role, true AS runtime_role_confined; ROLLBACK;")
' | docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
      exec -T postgres psql --username=accord_local --dbname=accord_local \
      --set=ON_ERROR_STOP=1

  docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
    exec -T postgres psql --username=accord_local --dbname=accord_local \
    --set=ON_ERROR_STOP=1 < deploy/accord-data-inventory.sql
)
```

Expected: `CREATE ROLE`, grants and `COMMIT`, then `checked_role=accord_runtime`,
`runtime_role_confined=t`, `ROLLBACK`, and an unchanged empty application inventory.
Role creation deliberately refuses an existing role. Stop and report that result rather than
altering/granting around it. This proves effective role privileges, not TCP password login.

Set its password interactively, choose a unique database password and keep it in your local
password manager. Run from the same repository directory; the prompt asks for it twice:

```zsh
docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
  exec postgres psql --username=accord_local --dbname=accord_local \
  --set=ON_ERROR_STOP=1 --command='\password accord_runtime'
```

Report success/role/inventory lines only, never the password. The backend runtime URL will use
this role and port 18662; the operator URL remains for migrations/provisioning only. Configure
and verify an actual runtime connection separately before enabling the API. Exact identity
steps are in [Zynth integration §3](zynth-local-integration.md#3-prepare-the-database-and-separate-operatorruntime-roles).

After setting its password, test an actual password login over TCP inside the PostgreSQL
container. Run this from the repository directory; enter the password locally when prompted:

```zsh
docker compose --env-file .cache/local-stack/runtime.env -f deploy/compose.local.yml \
  exec postgres psql --host=127.0.0.1 --username=accord_runtime --dbname=accord_local \
  --password --set=ON_ERROR_STOP=1 --command='SELECT current_user AS connected_role;'
```

Expected: `connected_role=accord_runtime`. This verifies TCP database authentication inside
the container; host-port 18662/backend URL and a genuine Zynth session still need separate
acceptance. Do not replace runtime credentials with the operator if password login fails.

Next, verify the Mac's published port through the actual Python settings/session factory and
runtime privilege verifier. This uses an in-process URL constructed with correct password
escaping. The password is entered locally and is neither printed nor written to configuration:

```zsh
(
  set -e
  cd "/path/to/gen6th-accord/backend"
  ENVIRONMENT=development PERSONA_API_ENABLED=false .venv/bin/python -c '
import asyncio
from getpass import getpass
from sqlalchemy.engine import URL
from accord.config import get_settings
from accord.db import connection as database
from accord.personas.runtime_role import verify_runtime_role

async def probe() -> None:
    try:
        await verify_runtime_role()
    finally:
        if database._engine is not None:
            await database._engine.dispose()

try:
    get_settings().database_url = URL.create(
        "postgresql+asyncpg",
        username="accord_runtime",
        password=getpass("Database password for accord_runtime: "),
        host="127.0.0.1",
        port=18662,
        database="accord_local",
    ).render_as_string(hide_password=False)
    asyncio.run(probe())
except Exception as error:
    print("backend_database_connection=failed error_type=" + type(error).__name__)
    raise SystemExit(1)
print("backend_database_connection=pass role=accord_runtime endpoint=127.0.0.1:18662/accord_local")
'
)
```

Expected: `backend_database_connection=pass role=accord_runtime endpoint=127.0.0.1:18662/accord_local`.
This is a real driver/permission probe, not a running HTTP backend or persistent configuration.
No app identity, persona, binding, sample data or auth grant is created. Errors report only their
class; never paste a credential-bearing URL/traceback to diagnose a failure.
Tables/roles are storage preparation; canonical user provisioning waits for actual tenant/user
UUIDs. Store private operator/runtime credentials locally, never in chat or browser variables.
No seeds, test persona, sample assets or temporary auth bypass are part of preparation.

## 4. Review creation before identity activation

Open the current local source preview and select **Create persona** or **Creation**. Verify
compact desktop/mobile fields, readable counters, keyboard focus and no duplicate heading or
readiness panel. Enter actual authored content if desired; **Save persona** stays disabled while
disconnected. Return to Records and back: the tab draft remains; a refresh clears it.
Once the genuine session is configured, enter the intended content in that session's form,
confirm, save and verify version 1 and generated record/version IDs. Return to Records, reload
and read back the same content. Retry only the same retained intent after an uncertain result.
Check permission loss, independent-account isolation and denied double submission.

Evidence uploads, scanner/key/retention providers, AI, signing and public publication remain
separate next work. Never substitute historical scenarios to make this acceptance pass.
