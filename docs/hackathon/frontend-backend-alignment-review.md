# Frontend/backend alignment review — 2026-10-02

The second/third-pass UI supersedes the earlier frontend checkpoint below; see
[console review](h1-console-review.md). Backend source is unchanged. No persona adapter or
trusted session is activated; local history/operations remain explicitly fixture data.

## Connection status

The five H1 screens form a browser-only fictional journey. None calls the persona backend.
`use-studio.ts` stores bounded draft fields locally; decisions are React state. `main.py`
mounts only example/client-event routers plus health/banner. The typed HTTP client exists
but is unused by these screens. No trusted persona session adapter or route is activated.

| Screen | Frontend now | Backend now | Missing connection |
|---|---|---|---|
| Gallery | Static palette cards/filters | Scoped version reads | Authorized listing, durable IDs/revisions |
| Creation | Browser-stored draft | Bounded immutable versions, CAS/retries | Disclosure, assets, session/workspace and API adapter |
| Analysis/review | Timed scenario/notes | Independent version-bound reviews/history/evidence | Real analysis, independent session, review requests/receipts |
| Campaign | Fixed scope/demo acceptance | Owner offers, recipient decisions, revocation/current status | Party sessions, exact scope commands, server-time/conflict handling |
| Public passport | Local projection/unsigned JSON | Internal decision evidence inspection | Reviewed public projection, privacy, signing and verification |

Workers process committed server events; H1 clicks create none. Browser success cannot
prove persistence/detection. `/health` works through Compose's proxy, not the frontend-only
dev port; liveness is not persona integration. Zynth remains deferred. No scaffold identity
substitute, browser grant or public persona write route was introduced.

## Corrections and limits

- Review-note edits clear stale review/acceptance and require fresh confirmation.
- Draft edits and persona selection clear evidence notes anchored to the previous draft.
- Illustration comparison is disabled until the scenario is ready, with explanatory copy.
- Scan provenance correctly describes one original illustration in three palettes.
- Banner explicitly says persona records are not sent to the backend. Tests assert no fetch
  during the full demo journey, alongside note-edit and comparison regressions.
- Gallery counts remain fixtures. Campaign acceptance is not current use permission, which
  the backend separately computes from version/review, roles and time. Public/private
  toggling is presentation only. Unsigned exports omit notes and cannot prove rights.
- Real integration needs trusted identity, mounted typed routes, durable receipts and
  authenticated browser-to-worker tests. No such end-to-end claim is made.

## Test evidence and repeat round

Owner round on 2026-10-02: **31 frontend tests passed** and **349 backend tests passed
in 63.41s**. Supplied trailing fingerprints match the checkpoint below and were independently
confirmed against current source. The attachment does not include the leading fingerprints;
no claim of a complete before/after pair is made for this round.
The root-level coverage invocation reported 98% including tests/migrations. Re-reporting
the available coverage artifact with `backend/pyproject.toml` and application-only inclusion
passed the existing 70% floor: **96% (1,643 statements, 64 missed)**. Full-gate/audit and
browser-to-backend integration gaps remain unchanged.

31 frontend tests pass. ESLint, TypeScript and production build pass; shared client bundle
166.4 kB gzip is within 250 kB. Browser automation fails before opening a session: its trusted
kernel cannot start. Responsive/real-browser QA remains unverified. Backend source matches
the owner-tested 301-test checkpoint; no backend behavior changed in this audit.
Full gates and dependency audits remain incomplete.
Fresh `make frontend` passed lint/format/types and stopped at npm audit DNS resolution.
Fresh `make check` passed 776 guards (18 skipped), policy/harness/backend static checks
and stopped at pip-audit bootstrap. Targeted frontend code/test secret scans found no leaks.
The repeat round expands PostgreSQL verification to all 349 collected backend tests with
coverage, including the 301-test persona/migration target and existing API/auth/spine cases.

With Docker running, execute in Mac Terminal:

```bash
cd "/path/to/gen6th-accord"
backend/.venv/bin/python .cache/frontend-source-evidence.py
backend/.venv/bin/python .cache/workflow-source-evidence.py
PATH="/opt/homebrew/opt/node@22/bin:$PATH" npm --prefix frontend test
LC_ALL=en_US.UTF-8 backend/.venv/bin/pytest backend/tests -q --cov=accord --cov-config=backend/pyproject.toml --maxfail=1
backend/.venv/bin/python .cache/frontend-source-evidence.py
backend/.venv/bin/python .cache/workflow-source-evidence.py
```

Expected: 31 frontend tests, 349 backend tests, the existing coverage floor passing and
matching fingerprints for each tree. Explicit coverage configuration excludes tests from
the application denominator and enforces the repository's existing floor.
These use throwaway databases. For visual feedback, use [H1 source-preview instructions](h1-review.md);
existing Docker images do not automatically contain source changes. Check note editing after
acceptance, disabled comparison before scanning, interruption/retry, keyboard and narrow layouts.

Source checkpoint: frontend `59c689092a5bbd3e330fb93f97a1ae845f223c1d533ccb5716f1671fc2f0ff6b`
(31 files), backend `7a50df9ccefa699e26d24ce4302729f332d95f3a1166666f4bba8906b4c1c082`
(120 files). Fingerprints exclude environment files, caches and build output.
