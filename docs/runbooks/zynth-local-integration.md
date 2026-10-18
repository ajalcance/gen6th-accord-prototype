# Real records and local Zynth integration

## Current verification and limits

Owner reported the preceding source passing the full gate: 601 backend tests / 94.27% coverage,
260 frontend tests, 14 ASGI tests, Trust and dependency audits; validation exited 0.
ADR-0041 adds real creation and read-only data inventory. Current frontend: 271 unit tests,
15 isolated ASGI tests, lint/types/production webpack build and 166.4 kB / 250 kB budget pass.
Owner's current full validation now exits 0 with matching ADR-0041 fingerprints and all 15 ASGI
tests; the supplied tail omits backend count/coverage. Owner local migration reaches 0009identity;
17 tables have zero domain rows and Redis is empty. Restricted runtime-role preflight passes;
password TCP and Mac backend Python connection pass. Persistent configuration and Zynth/rendered acceptance remain separate proof.
Agent-only audit/Docker limits remain; they do not override the owner's successful full gate.
See [creation/storage preparation](creation-and-storage-preparation.md) before connecting.

Owner's preceding source inputs (historical for the new slice; secrets excluded):
```text
backend_source_sha256=032cfd99451384585484de3ae9824267339a3f94826fed8e5220802c83984758 files=180
frontend_source_sha256=0de12694a97d8a4480612e3cc6abc29f5c323662ad68ca115b902890349625ba files=139
```

Prepared 2026-10-04. Implementation is local and disabled until owner configuration.
Owner migrated only the local application database; no Zynth organization/client or deployment
was changed. The agent did not directly access the database or credentials.
Steps 1–3 prepare storage, identity and saved-record reads. ADR-0041 supplies the real creation
form; actual authenticated creation/read-back still needs acceptance. Uploads, AI, signing and
publication remain incomplete.

## Recommended Zynth setup

Use your existing Zynth deployment with a dedicated **Accord Local** nonproduction organization.
Use two genuine workforce accounts: creator and independent reviewer. Keep this client separate
from production. The published managed issuer is `https://auth.zynthmedia.com`; use that only
if your organization's actual Zynth account is hosted there. For your existing self-hosted
deployment, use its configured HTTPS issuer. Do not create a second identity deployment merely
to run this test. Managed signup is invitation-only during the private beta; documentation
cannot create the organization or recover its IDs for you.

Sources reviewed: [Zynth token guide](https://auth.zynthmedia.com/docs/guides/verifying-tokens),
[OpenID Provider guide](https://auth.zynthmedia.com/docs/guides/openid-provider), and local
`zynth-auth` checkout `5095ec9b58cc8383436b36d8686ac7a605ba225c`:
the OpenID Provider, token-verification and SDK guides, and the UserInfo/token services.
Public token docs were fetched; the web tool could not fetch the OIDC/discovery pages, so the
OIDC contract was verified from the local primary documentation and implementation. The
deployed issuer must still be checked below. No unpublished SDK installation is required.

## 1. Verify the changed source on the owner's Mac

Run this in **Mac Terminal**, with Docker Desktop running. These tests use disposable databases,
not your application's database. Do not activate the connection until the complete block passes.

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
  printf 'validation_exit_status=%s\n' "$validation_result"
  exit "$validation_result"
)
```

Report the final backend pass count/coverage, frontend pass count, 15 ASGI results and exit status.
SQL cases include migrations, RLS/immutable history, canonical identity provisioning and real
record persistence. ASGI tests use isolated fault data and do not prove a live Zynth connection.
Preserve the prior 601-test result as historical; it cannot certify the seven new inventory tests.

## 2. Register the real Zynth client

1. Open your Zynth admin console. Select the dedicated **Accord Local** organization.
2. Confirm both actual workforce users are active members of that organization. Record its
   non-secret organization UUID and each user's UUID from the admin account/member details.
3. Open **Organization → OAuth Clients** and create **Accord Local** as **Confidential**.
4. Set grant types to **authorization_code** and allowed scopes to **openid** only.
5. Register this exact local callback, including the port:
   `http://127.0.0.1:18664/api/auth/callback`.
6. Leave refresh-token, client-credentials, resource indicator, DPoP and back-channel logout
   settings unused for this initial profile. Accord does not implement those flows here.
7. Save the public `client_id`. Store the show-once secret directly in your local secret file;
   never paste it, passwords, access tokens or the encryption key into chat.

This organization-specific client can authenticate only its organization's users. Zynth uses
the user's current organization session at authorization; this integration does not invent an
organization chooser. A platform-level client is unnecessary for this one-organization test.

From your terminal, check `https://YOUR-ISSUER/.well-known/openid-configuration`. It must report
your exact HTTPS issuer, RS256, code flow and S256, with same-issuer authorization/token/UserInfo/
JWKS endpoints matching `/api/v1/oauth/authorize`, `/api/v1/oauth/token`, `/api/v1/oauth/userinfo`
and `/.well-known/jwks.json`. A differing contract requires review before using credentials.

## 3. Prepare the database and separate operator/runtime roles

First run the [read-only baseline inventory](creation-and-storage-preparation.md#2-inventory-the-actual-local-application-database).
Use an empty, dedicated PostgreSQL 17 Accord database for this integration. An existing sample
database must be archived and reviewed separately; migration 0008 intentionally refuses it.
Do not drop data or weaken that check. The all-tenant operator applies migrations; the runtime
must have no superuser, BYPASSRLS, table ownership or membership/binding write privilege.
The narrowly scoped membership-read function retains row locks without granting role updates;
the operator owns it and runtime receives execute permission only. Review this boundary in
ADR-0040 before live use; PostgreSQL behavior remains an owner/CI verification requirement.

Run `backend/.venv/bin/alembic upgrade head` **from backend/** with the operator database URL
supplied to that process. It applies through `0009identity`. This creates tables, not a persona.
Owner SQL for the confined runtime role is in `deploy/accord-runtime-role.sql`; run it through
your PostgreSQL administrator connection after migration. It creates a new role and deliberately
fails if that role already exists. Set its password interactively using `\password accord_runtime`.
Store its async SQLAlchemy URL in `backend/.env` as `DATABASE_URL`; do not use the operator URL
for the web backend. Configure Redis to your real local service; no memory substitute exists.

Provision the real creator/reviewer using the owner-only CLI. It creates membership/binding
database rows and an auditable operator observation, with a generated canonical Accord actor ID.
It does not create a persona. A matching rerun is idempotent; a changed grant is refused.
From backend/, supply the operator URL only for each provisioning process:

```zsh
read -s 'ACCORD_OPERATOR_DATABASE_URL?Operator async PostgreSQL URL (local only): '
printf '\n'
DATABASE_URL="$ACCORD_OPERATOR_DATABASE_URL" .venv/bin/alembic upgrade head
DATABASE_URL="$ACCORD_OPERATOR_DATABASE_URL" .venv/bin/python -m accord.personas.provision \
  --issuer 'https://YOUR-ISSUER' --tenant 'YOUR-ZYNTH-ORG-UUID' \
  --workspace 'YOUR-ACCORD-WORKSPACE-UUID' --subject 'REAL-CREATOR-UUID' --role creator
DATABASE_URL="$ACCORD_OPERATOR_DATABASE_URL" .venv/bin/python -m accord.personas.provision \
  --issuer 'https://YOUR-ISSUER' --tenant 'YOUR-ZYNTH-ORG-UUID' \
  --workspace 'YOUR-ACCORD-WORKSPACE-UUID' --subject 'REAL-REVIEWER-UUID' --role reviewer
unset ACCORD_OPERATOR_DATABASE_URL
```

Choose the Accord workspace UUID once (`python3 -c 'import uuid; print(uuid.uuid4())'`) and use
it consistently. Creator/reviewer output IDs are non-secret Accord identities; Zynth subjects
are never accepted as request-body actor grants.

## 4. Configure the local backend and source frontend

Edit **backend/.env** locally with these values. The file is gitignored. No secret is a
`NEXT_PUBLIC` value. Fill UUIDs with actual IDs; placeholders do not establish a connection.

```dotenv
ENVIRONMENT=development
DATABASE_URL=YOUR-CONFINED-RUNTIME-ASYNC-POSTGRES-URL
REDIS_URL=YOUR-LOCAL-REDIS-URL
PERSONA_API_ENABLED=true
ZYNTH_ISSUER=https://YOUR-ISSUER
ZYNTH_CLIENT_ID=YOUR-REGISTERED-CLIENT-ID
ZYNTH_CLIENT_SECRET=YOUR-SHOW-ONCE-SECRET
ZYNTH_TENANT_ID=YOUR-ZYNTH-ORG-UUID
PERSONA_WORKSPACE_ID=YOUR-ACCORD-WORKSPACE-UUID
ZYNTH_SESSION_KEY=YOUR-LOCALLY-GENERATED-32-BYTE-HEX-KEY
ACCORD_APP_ORIGIN=http://127.0.0.1:18664
```

Generate the session key locally with `openssl rand -hex 32`, storing it only in backend/.env.
The owner-run local stack exposes PostgreSQL at 18662 and Redis at 18663; those are database
and cache ports, never backend HTTP ports. Check listeners before starting/replacing services:

```zsh
lsof -nP -iTCP:18664 -sTCP:LISTEN
lsof -nP -iTCP:18665 -sTCP:LISTEN
```

The current source preview already occupies 18664. Stop it from the terminal that owns it,
then start the configured processes in two terminals; do not kill an unrelated listener.

Backend terminal:
```zsh
cd "/path/to/gen6th-accord/backend"
PERSONA_API_ENABLED=true .venv/bin/uvicorn accord.main:app --host 127.0.0.1 --port 18665 --no-access-log
```

For the already approved/configured local identity integration, keep this process override on
each start: the owner's recorded setup preserves `PERSONA_API_ENABLED=false` in the saved file.
Without the override, the backend starts with no session verifier and login returns
`Zynth connection is not configured`. This command uses the existing private backend configuration;
it does not configure credentials, enable photo/Google/publication providers or certify acceptance.

Frontend terminal:
```zsh
cd "/path/to/gen6th-accord/frontend"
export PATH="/opt/homebrew/opt/node@22/bin:$PATH"
ACCORD_CONNECTION_ENABLED=true ACCORD_API_ORIGIN=http://127.0.0.1:18665 npm run dev -- --hostname 127.0.0.1 --port 18664
```

The browser calls only `/api` on 18664. Next proxies it to backend 18665. Keep this same origin
through login/callback/writes; do not switch between localhost and 127.0.0.1. Container builds
and production ingress are separate configuration/release work; this runbook activates no cloud
deployment. Callback query strings contain one-use codes: do not enable access-query logging
or collect those URLs in diagnostics. The backend image also disables Uvicorn access logging.

## 5. Live acceptance and what to report

Open `http://127.0.0.1:18664`, select **Sign in**, and sign in with the real creator in the
correct Zynth organization. Return to an empty Records workspace with **Sign out** available.
No sample records should appear. Repeat with the independent reviewer in a separate browser
session. Login alone creates no persona. In the creator session, select **Create persona**,
enter actual authored content, confirm and save. Verify version 1 and generated record/version
IDs, then return to Records and reload to read back that exact content. No sample input is needed.

Verify unknown users/other organizations cannot connect; end the Zynth grant under Connected
apps/Active sessions and check the next record request is denied; confirm drafts stay private
and fetched records clear. Check Origin-rejected writes, expiry and local logout. Redis/provider
outage must deny reads/writes; never swap in a test verifier. Actual creation/read-back is now
an acceptance step. Complete independent exact-version review; asset-bound campaign journeys
still require genuine asset intake and providers.

Report only non-secret issuer, organization UUID, creator/reviewer Accord actor IDs, migration
head, runtime-role preflight result, HTTP status codes and observed browser behavior. Do not
send cookie headers, callback URLs with codes, tokens, secrets or raw .env/log dumps.
Logout ends the Accord session; global Zynth logout, refresh and back-channel handlers are
not implemented. Footer Monitoring stays factual about unconnected live monitoring.
