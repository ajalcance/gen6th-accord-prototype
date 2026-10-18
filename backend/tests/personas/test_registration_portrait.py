"""Initial HTTP registration requires an inspected attachment; legacy history stays readable."""

import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.write_http import VersionSaveIntent
from personas.governance_bridge import WIRE
from personas.write_http_fixtures import write_client


@pytest.mark.parametrize("photo", [None, {"action": "keep"}, {"action": "remove"}])
async def test_initial_registration_without_attachment_never_reaches_service(
    photo: dict[str, str] | None,
) -> None:
    body = json.loads(WIRE.read_text())["save"]
    if photo is None:
        body.pop("photo")
    else:
        body["photo"] = photo
    with patch("accord.personas.write_http.save", AsyncMock()) as service:
        async with AsyncSession() as session, write_client(session) as (client, _provider):
            result = await client.post(
                f"/api/workspaces/{uuid4()}/personas/versions/save", json=body
            )
    assert result.status_code == 422
    assert result.json()["error"]["code"] == "invalid_intent"
    service.assert_not_awaited()


def test_client_cannot_substitute_a_scan_verdict_or_blank_upload_identifier() -> None:
    body = json.loads(WIRE.read_text())["save"]
    for photo in (
        {"action": "attach", "upload_id": None},
        {"action": "attach", "upload_id": str(uuid4()), "scanned": True},
    ):
        with pytest.raises(ValidationError):
            VersionSaveIntent.model_validate({**body, "photo": photo})


def test_legacy_edit_intents_keep_their_original_shape() -> None:
    body = json.loads(WIRE.read_text())["save"]
    body.pop("photo")
    body.update(persona_id=str(uuid4()), expected_revision=1)
    intent = VersionSaveIntent.model_validate(body)
    assert intent.model_dump(mode="json") == body
