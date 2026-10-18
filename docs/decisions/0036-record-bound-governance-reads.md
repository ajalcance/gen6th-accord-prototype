# ADR-0036: Bind saved governance to authorized version discovery

**Status:** Proposed; owner authorized tasks 2–4 and local implementation on 2026-10-03.
Owner security/ADR review and activation remain pending.
**Date:** 2026-10-03
**Builds on:** ADRs 0024–0026 and 0031–0035.

## Context

The separately labelled governance example explains the lifecycle, but cannot describe a
selected saved persona. The saved gallery has no discovery of older versions, campaigns or
private evidence, and its two-route adapter intentionally excludes other reads. Zynth remains
deferred. The owner wants record-aware governance and integration preparation without activation.

## Decision

- Preserve the browser example as a separate source. Add governance inspection to authorized
  saved details, keyed by workspace, trusted session context, persona and selected version.
  Never replace a missing service response with example history, invented IDs or browser roles.
- Add bounded immutable version history and exact-version campaign/evidence discovery.
  Version/review history follows current human workspace membership. Offers are visible only
  to their owner or named recipient. Evidence metadata requires the version creator/owner's
  current creator membership, including empty pages. No private payload or key reference is read.
- Use exclusive revision/UUID cursors and limit-plus-one pages, with a maximum of 100 records.
  Validate every frontend item against the requested tenant/resource, ordering and continuation.
  Discover references before requesting existing status, decision history or audit inspection.
- Reuse the existing authorization, transactions, inspection and event machinery. Discovery
  emits registered `persona.workflow_observed` server events, even for authorized empty pages;
  no new action, grant, table, migration, background process or provider is introduced.
- Prepare a separate unregistered eight-query router and separate read transport. Keep the
  original gallery/version factory unchanged. All queries are POST because reads record
  observations; the verifier runs before the database dependency, failures are sanitized and
  responses uncached. Bodies cannot supply identity. No application factory mounts either router.
- Clear query values/retry closures and unmount record panels on version, section, campaign,
  page or trusted context changes. Ignore late responses. Permission loss in any governance or
  audit read clears the selected saved view. Draft state remains separate and unchanged.
- Display status from validated backend reasons. Historical acceptance/review remains unsigned
  and does not establish current permission. Audit presence is not chain/signature verification;
  evidence inspection/expiry does not establish rights, promotion or deletion.
- Confine synthetic verifiers, stub services and ASGI process bridging to test files. Test actual
  FastAPI/Pydantic serialization through the browser HTTP client, gateway and UI without a live
  listener or identity provider. Add separate real-service PostgreSQL/ASGI journeys for owner/CI.
  Stub-service bridge results cannot substitute for database authorization or browser acceptance.
- Run the two-runtime bridge with `npm run test:governance-integration` using the installed
  backend venv and Node 22. Preserve the normal Node-only test command/configuration and CI jobs.
  This additional command is a local/owner verification step, not an existing CI-enforced gate.

## Gates and consequences

The default saved source remains unavailable and write transport rejects. Routes, login,
uploads, inspection/key/retention providers, Zynth, monitoring, signing and cloud remain inactive.
Real activation needs ADR-0034's identity, credential, origin/CSRF/TLS/header review and separate
owner authorization. No publication, licensing/visibility change or deployment is included.

New backend source invalidates the previous 454-test checkpoint. Current relevant checks and
the fresh owner/CI SQL/full-gate command are in the [record-bound checkpoint](../hackathon/h2-record-bound-review.md).
Rendered mobile/zoom/keyboard/touch/reduced-motion acceptance and revision-bound PR CI remain
pending. Keep discovery services, saved UI/transport and test bridge reviewable independently
from the existing policy, dependency, evidence and recovery work.
