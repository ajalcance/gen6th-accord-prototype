"""The observability coverage registry.

The contract that makes "monitor everything" mechanical: every API route maps to the envelope
actions it emits. ``tests/test_telemetry_coverage.py`` walks the real FastAPI app and fails the
gate when a route is missing here — so no feature can ship unobserved.

Keys are ``(HTTP method, path)`` exactly as registered on the app.
"""

from __future__ import annotations

# Actions emitted OUTSIDE any request route (e.g. background workers). The coverage guards
# union these in so "every emitted action" stays complete.
NON_ROUTE_ACTIONS: frozenset[str] = frozenset(
    {
        "persona.version_saved",
        "persona.portrait_uploaded",
        "persona.portrait_inspected",
        "persona.portrait_bound",
        "persona.portrait_read",
        "workspace.membership_provisioned",
        "persona.evidence_quarantined",
        "persona.evidence_inspected",
        "persona.evidence_read",
        "persona.evidence_purged",
        "persona.version_read",
        "persona.access_denied",
        "persona.write_conflict",
        "persona.workspace_observed",
        "persona.review_recorded",
        "persona.workflow_observed",
        "persona.asset_registered",
        "persona.passport_issued",
        "persona.publication_approved",
        "persona.publication_revoked",
        "persona.publication_observed",
        "persona.campaign_offered",
        "persona.campaign_decided",
        "command.persona_detection_evaluated",
    }
)

# System endpoints intentionally outside the observability contract (no principal, no security
# semantics; /health is probed frequently by the container healthcheck).
EXEMPT: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/"),
        ("GET", "/health"),
    }
)

# Actions REPORTED BY A CLIENT rather than observed by this service. They are ordinary events —
# queryable, alertable, retained — but they may never enter the tamper-evident audit chain, and
# the coverage guards fail if one is listed as auditable. See docs/decisions/0012.
CLIENT_ACTIONS: frozenset[str] = frozenset(
    {
        "client.error",
        "client.route_view",
    }
)

# route → envelope actions it emits (directly or via the layers it calls).
COVERAGE: dict[tuple[str, str], tuple[str, ...]] = {
    ("GET", "/api/auth/login"): ("auth.session_observed",),
    ("GET", "/api/auth/callback"): ("auth.session_observed",),
    ("GET", "/api/auth/session"): ("auth.session_observed",),
    ("POST", "/api/auth/logout"): ("auth.session_observed",),
    ("POST", "/api/v1/client-events"): tuple(sorted(CLIENT_ACTIONS)),
}

_PREFIX = "/api/workspaces/{workspace_id}/personas"
for _path, _action in {
    "/query": "persona.workspace_observed",
    "/photos/search": "persona.workspace_observed",
    "/photos/similarity/readiness": "persona.workspace_observed",
    "/photos/similarity/prepare": "persona.workspace_observed",
    "/photos/similarity/search": "persona.workspace_observed",
    "/photos/similarity/clear": "persona.workspace_observed",
    "/photos/investigations/readiness": "persona.workspace_observed",
    "/photos/investigations/generate": "persona.workspace_observed",
    "/photos/investigations/history": "persona.workspace_observed",
    "/photos/investigations/review-requests/request": "persona.workspace_observed",
    "/photos/investigations/review-requests/history": "persona.workspace_observed",
    "/photos/capture/query": "persona.portrait_read",
    "/photos/faces/query": "persona.portrait_read",
    "/photos/faces/process": "persona.portrait_inspected",
    "/versions/query": "persona.version_read",
    "/assistant/brief": "persona.version_read",
    "/versions/history/query": "persona.workflow_observed",
    "/reviews/history/query": "persona.workflow_observed",
    "/campaigns/query": "persona.workflow_observed",
    "/campaigns/history/query": "persona.workflow_observed",
    "/campaigns/status/query": "persona.workflow_observed",
    "/passports/assets": "persona.workflow_observed",
    "/passports/export": "persona.workflow_observed",
    "/passports/verify": "persona.workflow_observed",
    "/passports/readiness": "persona.workspace_observed",
    "/runtime/readiness": "persona.workspace_observed",
    "/jobs/enqueue": "persona.workflow_observed",
    "/jobs/history": "persona.workflow_observed",
    "/jobs/update": "persona.workflow_observed",
    "/workflow/evidence/query": "persona.workflow_observed",
    "/evidence/query": "persona.workflow_observed",
    "/evidence/status/query": "persona.workflow_observed",
    "/evidence/readiness": "persona.workspace_observed",
    "/evidence/upload/{version_id}": "persona.evidence_quarantined",
    "/evidence/inspect": "persona.evidence_inspected",
    "/evidence/content": "persona.evidence_read",
    "/evidence/purge": "persona.evidence_purged",
    "/assets/enroll": "persona.asset_registered",
    "/credits/read": "persona.workspace_observed",
    "/credits/save": "persona.workspace_observed",
    "/credits/confirm": "persona.workspace_observed",
    "/lifecycle/read": "persona.workspace_observed",
    "/lifecycle/append": "persona.workspace_observed",
    "/lifecycle/history": "persona.workspace_observed",
    "/publications/approve": "persona.publication_approved",
    "/publications/unpublish": "persona.publication_revoked",
    "/publications/history": "persona.workflow_observed",
    "/versions/save": "persona.version_saved",
    "/reviews/record": "persona.review_recorded",
    "/campaigns/offer": "persona.campaign_offered",
    "/campaigns/decide": "persona.campaign_decided",
}.items():
    COVERAGE[("POST", _PREFIX + _path)] = (
        _action,
        "persona.access_denied",
        "persona.write_conflict",
    )

COVERAGE[("POST", _PREFIX + "/photos/upload")] = (
    "persona.portrait_uploaded",
    "persona.portrait_inspected",
    "persona.access_denied",
)
COVERAGE[("POST", _PREFIX + "/passports/export")] += ("persona.passport_issued",)
for _method, _public_path in (("GET", ""), ("POST", "/verify"), ("GET", "/portrait")):
    COVERAGE[(_method, "/api/public/passports/{workspace_id}/{publication_id}" + _public_path)] = (
        "persona.publication_observed",
        "persona.access_denied",
    )
for _worker_path in ("execute", "reconcile"):
    COVERAGE[("POST", "/internal/personas/jobs/" + _worker_path)] = (
        "persona.workspace_observed",
        "persona.portrait_inspected",
        "persona.access_denied",
        "persona.write_conflict",
    )
COVERAGE[("GET", _PREFIX + "/photos/versions/{version_id}/thumbnail")] = (
    "persona.portrait_read",
    "persona.access_denied",
)
COVERAGE[("GET", _PREFIX + "/photos/similarity/queries/{query_id}/thumbnail")] = (
    "persona.workspace_observed",
    "persona.access_denied",
    "persona.write_conflict",
)
COVERAGE[("GET", _PREFIX + "/photos/versions/{version_id}/references/{portrait_id}/thumbnail")] = (
    "persona.portrait_read",
    "persona.access_denied",
)
