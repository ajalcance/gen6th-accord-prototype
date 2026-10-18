# Session/read integration preparation — 2026-10-03

The owner authorized the next audit/authentication/read integration sequence and renewed
two hours: **06:57:39–08:57:39 Asia/Manila on 2026-10-03**. No automatic extension.
Design: [ADR-0034](../decisions/0034-session-gated-persona-read-surface.md).

## Working local result

The gallery exposes separate “Browser fixtures” and “Saved records” controls. The latter
shows the trusted-session prerequisite in the current app. Prepared injected-source behavior
supports bounded pages, explicit name search, refresh, next page and read-only version details.
Loading, cancellation, unavailable, denied and invalid responses have distinct behavior;
late results and prior page/version data cannot remain displayed across access/context changes.
Server content is never copied into the browser fixture reducer or localStorage.

Backend `session_boundary.py` and `read_http.py` prepare a verifier-gated router factory for
gallery/version queries. There is no verifier implementation, mounted router, fallback login,
persona API activation or persistent-database migration. Zynth remains deferred (ADR-0015).
Synthetic verifier tests do not establish a real credential or authentication connection.

## Audit and validation evidence

Agent audits on October 3 failed registry DNS/temporary pip bootstrap. The owner then ran
the complete command below successfully in Mac Terminal; the local audit blockers are resolved.
No exemption, guard edit, policy widening or dependency upgrade was needed.
Current evidence:

- Frontend: **151 tests / 14 files**, ESLint, Prettier, strict TypeScript, production build
  and bundle budget pass (**166.4 kB gzip / 250 kB**).
- Backend: owner **454 tests pass in 70.30s**, then again inside `make check` in **64.79s**.
  Application coverage is **96.55%** (2,088 statements / 72 missed; existing 70% floor met).
  This includes the four new PostgreSQL HTTP cases using an explicit synthetic verifier.
- Owner **full `make check` passes**: 776 guards / 18 skips, policy/harness, backend static
  checks, pip-audit, PostgreSQL tests, Go verification/lint/vulnerability/race tests, frontend
  lint/format/types/audit/151 tests/build/budget, docs-site lint/format/audit/11 tests/build.
  Python audit reports no known vulnerabilities; both npm audits report zero vulnerabilities.
  No revision-bound CI, real credential verification or authenticated browser journey is claimed.
- Documentation consistency, file/function bounds and diff hygiene pass. Source preview
  listener rechecked on 18664 (PID 51509); Codex browser open was queued. Rendered mobile,
  zoom, touch and keyboard geometry acceptance remains pending.

Backend SHA-256: `84eb16651371c1b5f54e3cf75b0e27e007ec35cca9f8b48303fe155df7d5698f`
(**146 inputs**). Frontend SHA-256:
`328d764e47d6ada9757c2116ad57d2bd445f378a9d525c824740be854d787b30` (**85 inputs**).
Both include the shared wire fixture. The earlier 421-test result validates the preceding
tree, not the new session/router modules and tests.
The supplied command has matching preconditions, leading/intermediate/trailing backend
fingerprints and a trailing frontend fingerprint. Both match the agent's independent rehash.
The terminal returned normally after the docs build and final fingerprints.

## Completed owner verification / repeat command

Use Mac Terminal with Docker Desktop running. This runs throwaway database tests, then
the full unmodified gate with Python 3.12/Node 22. It neither migrates the persistent local
database nor activates identity, routes or cloud services. The source preconditions stop
on drift. The owner completed this exact block with **454 passing tests** and full gate success.
Retain it for deliberate reverification of this source; no repeat is needed for these doc updates.

```bash
cd "/path/to/gen6th-accord" &&
test "$(backend/.venv/bin/python .cache/workflow-source-evidence.py)" = "backend_source_sha256=84eb16651371c1b5f54e3cf75b0e27e007ec35cca9f8b48303fe155df7d5698f files=146" &&
test "$(backend/.venv/bin/python .cache/frontend-source-evidence.py)" = "frontend_source_sha256=328d764e47d6ada9757c2116ad57d2bd445f378a9d525c824740be854d787b30 files=85" &&
backend/.venv/bin/python .cache/workflow-source-evidence.py &&
LC_ALL=en_US.UTF-8 backend/.venv/bin/pytest backend/tests -q --cov=accord --cov-config=backend/pyproject.toml --maxfail=1 &&
backend/.venv/bin/python .cache/workflow-source-evidence.py &&
PATH="$PWD/backend/.venv/bin:$PWD/.tools/bin:/opt/homebrew/opt/node@22/bin:$PATH" make check &&
backend/.venv/bin/python .cache/workflow-source-evidence.py &&
backend/.venv/bin/python .cache/frontend-source-evidence.py
```

## Next review units and gates

Keep the prepared session/read router, frontend query/view/transport and documentation hunks
separate from the existing dirty evidence, UI and policy work. No staging, commits or PRs.
Activation requires approved Zynth review, verified session/identity mapping, revocation and
human-context proof, credential/proxy/origin/CSRF/TLS/header review, quotas and full gates.
Private evidence uploads still need real key, scanner and retention providers. No cloud,
signing, publication or deployment activation is included. Show the local result for feedback
before expanding beyond this read slice; manual connected acceptance remains deferred.
