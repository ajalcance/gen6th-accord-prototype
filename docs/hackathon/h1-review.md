# H1 local review — 2026-10-01

This records the initial H1 checkpoint. Current second/third-pass scope and acceptance
evidence are in [console review](h1-console-review.md), governed by ADRs 0028/0029.

## Review unit

H1 owns `frontend/app/page.tsx`, `frontend/app/globals.css`, `frontend/app/passport/`,
`frontend/tests/page.test.tsx`, `frontend/tests/passport.test.tsx` and
`frontend/tests/fixture-data.test.ts`, plus the H1 paragraphs
in PLAN, LESSONS, current-state, CHANGELOG and prototype-plan, and this review record.
Keep the prior runtime/dependency, scope-planning and Codex-policy units separate.
Shared documentation needs hunk-level separation by the owner. No branch, commit or PR
was created; the existing checkout and all prior uncommitted changes are preserved.

Original asset inventory: `portrait.tsx` defines three fictional vector color studies.
No downloaded photographs, real-person likeness references or external asset requests.
These code-native illustrations need no additional runtime dependency. All workspace,
creator, reviewer and campaign data is fictional. No source publication is authorized.

## Preview on the owner's Mac

The existing Docker app on 18660 serves the previous built image. The sandbox refused a
new loopback bind with EPERM; it was not retried outside the sandbox. Run this in Mac
Terminal to show the source preview separately, without rebuilding that stack:

```bash
cd "/path/to/gen6th-accord"
(
  set -euo pipefail
  export PATH="/opt/homebrew/opt/node@22/bin:$PWD/.tools/bin:$PATH"
  test "$(node -p 'process.versions.node.split(".")[0]')" = "22"
  if lsof -nP -iTCP:18664 -sTCP:LISTEN; then
    echo "Port 18664 is occupied; stop and report the listener."
    exit 1
  fi
  cd frontend
  npm run dev -- --webpack --hostname 127.0.0.1 --port 18664
)
```

Open `http://127.0.0.1:18664`. Keep the terminal running; Ctrl+C stops this preview only.
Report the Next ready line or the exact failure. No install or cloud activation is involved.
The health link belongs to the Compose proxy and is unavailable on this frontend-only port.

Feedback route: gallery filter → select a persona → edit creation fields → continue →
run demo scenario → inspect candidate/slider → add a comment → record demo review →
confirm campaign scope → accept → inspect unsigned state and download demo JSON.
Also try interruption/retry, request changes and a changed draft after acceptance.
Check desktop and narrow mobile widths, Tab navigation and reduced-motion preference.
The owner supplied a gallery screenshot, reported completing the test and accepted the
frontend direction. This establishes owner feedback; it does not prove backend persistence
or a complete independent mobile/accessibility review.

## Fresh evidence and limits

- Node 22 frontend: 26 tests passed; production build/type check passed; shared client
  bundle 166.4 kB gzip, within 250 kB budget. Lint and formatting passed. `make frontend`
  passed lint/format/types then stopped at registry.npmjs.org audit DNS failure; no clean
  dependency audit is claimed. Separate tests/build do not bypass that required gate.
- Decision regression coverage now includes change requests from both screens, restarted/
  interrupted analysis and a newly recorded review. Each withdraws prior demo acceptance.
  Incomplete required fields cannot proceed through sidebar navigation; creation uses a
  native form and heading focus is tested. Filter buttons expose their selected state.
- Browser automation cannot start: its trusted Node kernel exits before opening a session.
  No independent responsive screenshot/real-browser accessibility claim is made.
- `make check`: preflight, 776 guards (18 skipped), policy, harness and backend static
  checks passed. Stopped at pip-audit temporary-tool bootstrap; no fresh full-gate success.
- No new server actions: telemetry, detection, audit and compliance registries unchanged.
  Browser state is not authoritative evidence. LocalStorage contains fictional draft fields;
  campaign/review states are in memory. Private/public toggle is a preview, not access control.
- Authentic uploads, reference permissions, sessions/roles, real analysis and signed
  verification remain H2–H4 work. QR/share issuance awaits a real public record.

## Minimum integration inspection and controlled benchmark plan

Repository requirements still describe future Zynth sessions and the `accord:*` resource.
The backend HMAC bearer principal is development scaffolding; no verified OIDC persona
session integration exists. Owner-deferred Zynth work remains a prerequisite for real routes.
H2 must confirm issuer/audience/JWKS contract, workspace membership, creator/reviewer
separation and denial of stale/self approvals before accepting real evidence. No sibling
repository or credentials were accessed; availability is unverified.

H3 benchmark: use a permitted original catalogue with known exact copies, palette changes,
crops/compression, changed backgrounds/poses and unrelated controls. Track top-k retrieval,
reference validity, missing-evidence detection, unsupported findings, latency and cost.
Separate exact hashes from embedding rankings. Record catalogue count and failure cases;
never describe a rank as copying probability or a face-identity verdict. Current fixtures
are UX scenarios and supply no benchmark or Gemini evidence. Model/cloud access remains
subject to owner activation; organizer acknowledgment and source packaging remain pending.
