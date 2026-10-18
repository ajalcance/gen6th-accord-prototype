# Gen6th Accord: AI Persona Passport prototype

**AI Builder Cup 2026 submission, source release for evaluation.**
Theme selected: Media, Content & Digital Experiences.

> **Licence notice: the text in [`LICENSE`](LICENSE) is an owner-drafted evaluation notice that
> still needs the owner's review, and must be replaced if the competition portal requires an OSI
> (open-source) licence.** It is a source-available notice for evaluating this entry, not an
> open-source licence; all other rights are reserved. See also [`RIGHTS.md`](RIGHTS.md) for the
> intended scope of this submission.

## What this is

Accord is a central registry and verifiable passport for AI performers (synthetic or AI-assisted
"personas"). A creator records who made a performer and how AI was used, an independent reviewer
records a decision, a brand can see who may approve use, and anyone can lodge a claim for human
review. Model output never decides anything; a person does.

## What is live today, and what is not

Plain language, taken from the owner's readiness review of 2026-10-18. "Live" statements are
owner-reported output from the deployed service; this export has not been re-probed.

**Live on Google Cloud (Cloud Run, region asia-southeast1):**

- The web app (Next.js) and the API (FastAPI) on Cloud Run.
- A PostgreSQL database on Cloud SQL, migrated to its current schema (18 migrations), with a
  confined runtime role.
- Encrypted sessions (Memorystore Redis), secrets in Secret Manager, images built with Cloud Build.
- Sign-in through the Zynth Auth identity service (OIDC with PKCE).
- The Gemini on Vertex AI "reviewer brief" route is deployed (it is protected: anonymous requests
  are refused). Vertex AI was smoke-tested. An end-to-end brief on a real record has **not** been
  demonstrated.

**The live site currently holds no records.** Creating a performer requires an uploaded portrait to
pass a malware/format scanner, and that scanner is not yet deployed. A person who signs in sees an
empty app.

**Built and tested locally, not yet running live:** evidence upload and claims, Cloud Vision face
regions and multimodal embeddings for appearance checks, Cloud KMS signing of passports (Ed25519),
the signed public passport and QR route, Cloud Tasks workers, and the passport booklet view (the
booklet interface is deployed but has not been viewed on a real record). Source and tests for all of
these are in this repository.

**Not measured:** recognition accuracy. No accuracy figure is published or implied.

Test counts from the last full local gate on 2026-10-13 were 1,447 backend tests (94% coverage) and
514 frontend tests. They have not been re-run for this export.

## How to evaluate

**Sign-in is not offered to judges.** The sign-in is bound to a private Zynth organisation and the
live site holds no records, so the demonstration is the video and screenshots. Instead:

1. Watch the demo video (under three minutes): https://www.youtube.com/watch?v=ZGDhr8DivAs
2. Read the pitch deck and screenshots in the submission form. The three product screens in the deck
   are illustrative renders with fictional performers and are labelled as such.
3. Open the deployed app to confirm it is running:
   <https://accord-frontend-1073916405954.asia-southeast1.run.app>
   The home page loads; the session endpoint refuses anonymous requests, as designed.
4. Read the source. Start with `docs/OVERVIEW.md`, `docs/architecture/current-state.md` and
   `docs/decisions/0023-ai-persona-passport-prototype.md`; the Gemini reviewer brief is described in
   `docs/decisions/0074-advisory-reviewer-brief.md` and the booklet in
   `docs/decisions/0075-record-bound-passport-booklet.md`.

## Provenance (honest dates)

- The repository began on **2026-09-23** from the `zynth-setup` project scaffold (a Copier
  template). Template-derived material (CI, guards, docs layout, standards) predates and is separate
  from the prototype work. See `.copier-answers.yml`.
- The AI Builder Cup build window was 7 September to 18 October 2026. Whether template reuse meets
  the "fresh work" rule has been raised with the organiser and is not confirmed.
- This tree is a **reviewed export** of the private development repository, not its history.
  Source commit `0d1caa8` (booklet), plus two files taken from the deployment fixes
  (`frontend/Dockerfile` with API-origin build arguments, `backend/requirements.txt` with `httpx`).
  Those two files together with that commit are byte-identical to the source bundles built and
  deployed to Cloud Run (see `EXPORT-PROVENANCE.md` for hashes). The tree also includes 13
  frontend files of a later UI polish (branding and layout) that is **not yet deployed**; they are
  listed in `EXPORT-PROVENANCE.md`.
- Identifiers (cloud project number, local paths, personal email) were redacted from documentation.
  Private roadmap and internal hand-off notes were removed. The wider Gen6th initiative, founding
  framework, brand assets and other applications are **not** part of this submission.
- Third-party components keep their own licences (npm and PyPI dependencies, `vendor/braces`, QR
  code generation; see `docs/hackathon/qr-notice.md`). Nothing here claims exclusive ownership of
  them.

## Layout

| Path | Content |
|---|---|
| `backend/` | FastAPI service, Alembic migrations (0001 to 0018), tests |
| `frontend/` | Next.js app (passport workspace, booklet, reviewer brief), tests |
| `docs-site/` | Documentation site |
| `trust/` | Go trust services (signing and verification) |
| `deploy/` | Container, SQL role and Google contracts; `deploy/cloud-run/` holds the Cloud Run service and job specs actually used |
| `docs/` | Architecture, ADRs, standards, runbooks, hackathon slices |
| `scripts/`, `tests/`, `.github/` | Repository guards and CI |

## Run locally

```bash
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn accord.main:app --reload    # http://localhost:8000/health
cd ../frontend && npm ci && npm run dev
```

Backend tests need Docker (a throwaway PostgreSQL). Secrets are never committed; only
`.env.example` placeholders exist. Some repository guards (`make policy`) refer to documents that
were withheld from this export and will report them missing.

## Contact

Report security issues privately through GitHub's private vulnerability reporting (this
repository's Security tab). No mailbox is published; see `.github/SECURITY.md`.
