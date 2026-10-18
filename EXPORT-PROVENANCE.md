# Export provenance

This tree is a reviewed export of the private development repository. It carries no git history.

## Source

| Item | Value |
|---|---|
| Base commit (private repo) | `0d1caa8c1d1a6c9a29ddd30b638d1e6722032a33` (booklet, ADR-0075), which contains the advisory reviewer brief (`57c4332`) |
| Parent of that chain | `9320db0048aae2e26e848210de194329feb4e890` (main, PR 78) |
| Added file 1 | `frontend/Dockerfile` from `a6162ed` (blob `ba926650a85e219e4e160671ae97e3af582f8ac9`): API origin build arguments |
| Added file 2 | `backend/requirements.txt` from `2d7c9e9` (blob `c40329281b0d15abd793adfcffd9993fde16d762`): `httpx==0.28.1` |

## Deployed bundles this reproduces

| Bundle | SHA-256 |
|---|---|
| Frontend `accord-frontend-src-9320db00-gemini-booklet.tar.gz` | `40478959a9bef026a5a96156f3dc8971ec42750826845b1affceec99027026cf` |
| Backend `accord-backend-src-9320db00-gemini.tar.gz` | `a224aaddc20f2d2de9d70973eab3b1aa8fd67e2cab0809f857445c94abc15e44` |

All 331 frontend and 240 backend files in those bundles are byte-identical to the files under
`frontend/` and `backend/` here, except the 13 frontend files of the UI polish below. The bundles
omit tests and development requirements; this tree includes them.

## UI polish (not yet deployed)

13 frontend files come from the later bundle `accord-frontend-src-9320db00-polish.tar.gz`
(sha256 `92492e4f87a55ba8fee33bf54e9622dde67904dcaf749b51d5ed1ebd653c1225`): the polished UI and
branding. They are included in this export but are not in the bundle currently deployed to Cloud Run.

Files: `frontend/app/globals.css`, `app/icon.svg`, `app/passport/booklet-identity.tsx`,
`app/passport/booklet-records.tsx`, `app/passport/branding.css`, `app/passport/public-passport.tsx`,
`app/passport/saved-gallery.tsx`, `app/passport/signed-out-welcome.tsx`,
`app/passport/workspace-chrome.tsx`, `app/passport/workspace-console.tsx`,
`public/brand/gen6th-accord-dark.svg`, `public/brand/gen6th-icon.svg`, `tests/branding.test.tsx`
(all under `frontend/`). The favicon (`app/favicon.ico`) is unchanged here.

## Changes made for publication

- Replaced: the private `LICENSE` with a short owner-drafted evaluation notice.
- Removed: the private roadmap, internal session hand-offs and
  correspondence, and agent-confinement settings (`.claude/`).
- Redacted in documentation: cloud project number, local machine paths, one record-version id,
  personal email addresses.
- Added: this file, `README.md`, a stub `docs/PLAN.md`, and
  `deploy/cloud-run/` (the Cloud Run service and job specifications used for the deployment).
