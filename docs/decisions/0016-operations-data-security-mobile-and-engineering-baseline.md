# 0016. Operations, data lifecycle, security, mobile and the engineering baseline

- **Status:** Accepted
- **Date:** 2026-09-23
- **Deciders:** Albert Alcance (founder)

## Context

A whole-plan review found gaps in plumbing, data lifecycle, security, observability, storage, mobile and engineering process. It also settled how this repository relates to the `zynth-setup` template it was generated from. Full reasoning: [Addendum 03](../architecture/addendum-03-operations-data-security-mobile.md) and the [retention schedule](../architecture/retention-schedule.md).

## Decision

| ID | Decision |
|---|---|
| D-21 | Personal data stays outside the hash: pseudonymous IDs and salted commitments in signed records; erasure crypto-shreds a separate personal-data layer |
| D-22 | A retention schedule governs every data class, with a deletion method |
| D-23 | Outbox dispatch at commit plus a one-minute sweep; Intelligence as a Cloud Run service; Cloud Tasks for deadlines; public projections in Cloud Storage |
| D-24 | Web is a Next.js BFF on Cloud Run: tokens never in browser JavaScript, nonce-based CSP |
| D-25 | Native iOS and Android apps with Expo / React Native |
| D-26 | Resend for transactional email, with delivery evidence |
| D-27 | Paddle as merchant of record with PayPal inside checkout; direct PayPal as fallback; no in-app purchases at launch |
| D-28 | Hosted status page outside GCP |
| D-29 | OpenTelemetry, four log classes with their own retention, service-level objectives for the Trust path |
| D-30 | Fixed bucket layout; content addressing; log and projections mirrored to a second provider |
| D-31 | Continuity: Shamir-split recovery secrets; a GitHub organization (the repo stays under `ajalcance` for now) |
| D-32 | `zynth-setup` is the engineering baseline, followed closely. Accord makes its own adaptations in this repository without waiting on the template |
| D-33 | Backend in Python (FastAPI), superseding the TypeScript backend in D-10. Go for Trust and the verifier. TypeScript for web, mobile and the browser verifier |

## Consequences

- This repository keeps the template's layout, gates, guards, compliance spine and release chain. It carries these Accord-owned adaptations, tracked in [`PLAN.md`](../PLAN.md):
  - tests on Postgres (Testcontainers) and two Alembic environments;
  - a Go module (`trust/`) with its gates;
  - a Cloud Run release path replacing the Docker Compose and Caddy deploy;
  - Terraform (`infra/`) with its gates;
  - the spine transport on the Pub/Sub outbox;
  - an Expo mobile module;
  - a proprietary licence (done at the initial commit).
- `copier update` is used selectively. Template changes are merged by hand where they don't conflict with the adaptations.
- The template's Docker Compose and Caddy files and its SQLite test default stay **until** their replacements land, so the gates stay green in the meantime.

## Alternatives considered

- **TypeScript backend.** Rejected in favour of D-33. The template's guards, standards and compliance spine exist for Python, and it matches Zynth's stack and the Vertex AI and fingerprinting ecosystem.
- **Request template changes before adapting.** Rejected: the template is a foundation only, and Accord shouldn't wait on it.
