"""Synthetic ASGI write bridge; stub-service proof only, never SQL or real identity proof."""

import asyncio
import json
import sys
from contextlib import ExitStack
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.campaign_contracts import CampaignDecisionReceipt, CampaignReceipt
from accord.personas.contracts import PersonaVersion
from accord.personas.governance_http import create_governance_read_router
from accord.personas.read_http import create_read_router
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.workflow_contracts import ReviewSnapshot
from accord.personas.write_http import create_write_router
from personas.governance_bridge import WIRE, responses
from personas.test_session_boundary import verified


def write_responses(body: dict[str, Any], actor: str) -> dict[str, BaseModel]:
    wire = json.loads(WIRE.read_text())
    version = {**wire["version"], "creator_ref": actor}
    if "content" in body:
        version.update(content=body["content"], revision=body.get("expected_revision", 0) + 1)
        if body.get("persona_id"):
            version["persona_id"] = body["persona_id"]
    review = {**wire["review"], "reviewer_ref": actor}
    if "version_id" in body and "statement" in body:
        review.update(
            id=str(uuid5(NAMESPACE_URL, "synthetic-review:" + body["request_id"])),
            ordinal=1 if body.get("expected_previous_id") is None else 2,
            version_id=body["version_id"],
            decision=body["decision"],
            statement=body["statement"],
        )
    offer = dict(wire["campaign"])
    if "scope" in body:
        offer.update(
            scope=body["scope"],
            version_id=body["version_id"],
            review_id=body["review_id"],
            owner_ref=actor,
        )
        offer["assets"] = [
            row for row in wire["campaign"]["assets"] if row["id"] in body["scope"]["asset_ids"]
        ]
    decision = {**wire["decision"], "actor_ref": actor}
    if "campaign_id" in body and "statement" in body:
        decision.update(
            id=str(uuid5(NAMESPACE_URL, "synthetic-decision:" + body["request_id"])),
            ordinal=1 if body.get("expected_previous_id") is None else 2,
            campaign_id=body["campaign_id"],
            decision=body["decision"],
            statement=body["statement"],
        )
    return {
        "save": PersonaVersion.model_validate(version),
        "record_review": ReviewSnapshot.model_validate(review),
        "offer_campaign": CampaignReceipt.model_validate(offer),
        "decide_campaign": CampaignDecisionReceipt.model_validate(decision),
    }


async def bridge(
    path: str, body: dict[str, Any], mode: str = "ready", actor: str = "creator-a"
) -> dict[str, Any]:
    provider = AsyncMock()
    provider.verify.return_value = None if mode == "session_lost" else verified(actor_ref=actor)
    app = FastAPI()
    app.include_router(create_write_router(provider))
    app.include_router(create_read_router(provider))
    app.include_router(create_governance_read_router(provider))

    async def database() -> AsyncSession:
        return AsyncSession()

    app.dependency_overrides[get_db] = database
    with ExitStack() as stack:
        values = {**responses(), **write_responses(body, actor)}
        for name, value in values.items():
            service = AsyncMock(return_value=value)
            if mode == "permission_lost":
                service.side_effect = AccessDeniedError("synthetic private detail")
            elif mode == "conflict":
                service.side_effect = ConflictError("synthetic private detail")
            elif mode == "unavailable":
                service.side_effect = RuntimeError("synthetic private detail")
            module = (
                "write_http"
                if name in {"save", "record_review", "offer_campaign", "decide_campaign"}
                else "read_http" if name in {"list_gallery", "load"} else "governance_http"
            )
            stack.enter_context(patch(f"accord.personas.{module}.{name}", service))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            result = await client.post(path, json=body)
    return {"status": result.status_code, "headers": dict(result.headers), "body": result.json()}


async def main() -> None:
    command = json.loads(sys.stdin.read())
    workspace = UUID(command["workspace"])
    path = f"/api/workspaces/{workspace}/personas{command['path']}"
    print(
        json.dumps(
            await bridge(
                path,
                command["body"],
                command.get("mode", "ready"),
                command.get("actor", "creator-a"),
            )
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
