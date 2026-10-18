"""Test-only ASGI wire bridge. Synthetic sessions and stub services never ship as providers."""

import asyncio
import json
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.campaign_contracts import CampaignDecisionPage, CampaignStatus
from accord.personas.contracts import PersonaVersion
from accord.personas.evidence_contracts import EvidenceSnapshot
from accord.personas.gallery import GalleryPage
from accord.personas.governance_contracts import CampaignPage, EvidencePage, VersionPage
from accord.personas.governance_http import create_governance_read_router
from accord.personas.read_http import create_read_router
from accord.personas.repository import AccessDeniedError
from accord.personas.workflow_contracts import ReviewPage
from accord.personas.workflow_evidence_contracts import WorkflowEvidence
from personas.test_session_boundary import verified

WIRE = Path(__file__).resolve().parents[3] / "frontend/tests/fixtures/persona-wire.json"


def responses(mode: str = "ready") -> dict[str, BaseModel]:
    wire = json.loads(WIRE.read_text())
    if mode in {"revoked", "expired"}:
        wire["status"]["eligible_for_use"] = False
        wire["status"]["blocking_reasons"] = [mode]
        if mode == "revoked":
            decision = wire["status"]["latest_decision"]
            decision.update(decision="revoked", actor_ref="creator-a")
            wire["campaignHistory"]["items"] = [decision]
        else:
            wire["status"]["evaluated_at"] = wire["campaign"]["scope"]["ends_at"]
    if mode in {"rejected", "expired"}:
        wire["evidenceStatus"]["state"] = mode
        if mode == "expired":
            wire["evidenceStatus"]["recorded_at"] = "2026-09-25T04:00:00Z"
            wire["evidenceStatus"]["expires_at"] = "2026-10-02T04:00:00Z"
    return {
        "list_gallery": GalleryPage.model_validate(wire["gallery"]),
        "load": PersonaVersion.model_validate(wire["version"]),
        "version_history": VersionPage.model_validate({"items": [wire["version"]]}),
        "review_history": ReviewPage.model_validate(wire["reviewHistory"]),
        "campaign_offers": CampaignPage.model_validate({"items": [wire["campaign"]]}),
        "campaign_history": CampaignDecisionPage.model_validate(wire["campaignHistory"]),
        "inspect_campaign": CampaignStatus.model_validate(wire["status"]),
        "evidence_list": EvidencePage.model_validate({"items": [wire["evidenceStatus"]]}),
        "evidence_status": EvidenceSnapshot.model_validate(wire["evidenceStatus"]),
        "inspect_workflow_evidence": WorkflowEvidence.model_validate(wire["workflowEvidence"]),
    }


async def bridge(path: str, body: dict[str, Any], mode: str = "ready") -> dict[str, Any]:
    provider = AsyncMock()
    provider.verify.return_value = (
        None if mode == "session_lost" else verified(actor_ref="creator-a")
    )
    app = FastAPI()
    app.include_router(create_read_router(provider))
    app.include_router(create_governance_read_router(provider))

    async def database() -> AsyncSession:
        return AsyncSession()

    app.dependency_overrides[get_db] = database
    with ExitStack() as stack:
        for name, value in responses(mode).items():
            service = AsyncMock(return_value=value)
            if mode == "permission_lost":
                service.side_effect = AccessDeniedError("synthetic private detail")
            if mode == "unavailable":
                service.side_effect = RuntimeError("synthetic private detail")
            module = "read_http" if name in {"list_gallery", "load"} else "governance_http"
            stack.enter_context(patch(f"accord.personas.{module}.{name}", service))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            result = await client.post(path, json=body)
    return {"status": result.status_code, "headers": dict(result.headers), "body": result.json()}


async def main() -> None:
    command = json.loads(sys.stdin.read())
    workspace = UUID(command["workspace"])
    path = f"/api/workspaces/{workspace}/personas{command['path']}"
    print(json.dumps(await bridge(path, command["body"], command.get("mode", "ready"))))


if __name__ == "__main__":
    asyncio.run(main())
