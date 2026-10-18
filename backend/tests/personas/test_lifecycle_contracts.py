"""Trust markers, duration and legacy canonical scope boundaries."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from accord.personas.campaign_contracts import CampaignScope
from accord.personas.lifecycle_contracts import AppendLifecycle, effective_status
from accord.personas.lifecycle_service import validate_expiry
from accord.personas.production_contracts import ProductionUse
from accord.personas.repository import ConflictError
from personas.lifecycle_fixtures import assessment, command, dossier, receipt


@pytest.mark.parametrize("field", ["actor_ref", "verified", "evidence_digests", "workspace_id"])
def test_client_cannot_assign_trust_or_server_evidence(field: str) -> None:
    with pytest.raises(ValidationError):
        AppendLifecycle.model_validate({**command().model_dump(), field: "forged"})


def test_rights_and_provenance_bounds() -> None:
    content = dossier().model_dump()
    content["rights"] = ()
    with pytest.raises(ValidationError):
        type(dossier()).model_validate(content)
    content = dossier().model_dump()
    content["provenance"]["source"] = "metadata_verified"
    with pytest.raises(ValidationError):
        type(dossier()).model_validate(content)
    content = dossier().model_dump()
    content["rights"][0]["ends_at"] = content["rights"][0]["starts_at"]
    with pytest.raises(ValidationError):
        type(dossier()).model_validate(content)


def test_assessment_lifetime_and_current_status() -> None:
    value = assessment(uuid4())
    validate_expiry(value, dossier())
    for expiry in (
        datetime.now(UTC) - timedelta(seconds=1),
        datetime.now(UTC) + timedelta(days=31),
    ):
        with pytest.raises(ConflictError):
            validate_expiry(value.model_copy(update={"valid_until": expiry}), dossier())
    row = receipt(command().model_copy(update={"content": value}), actor="reviewer")
    assert effective_status(row, True) == "approved"
    assert effective_status(row, False) == "unavailable"
    assert effective_status(None, True) == "missing"
    expired = row.model_copy(
        update={
            "content": value.model_copy(
                update={"valid_until": datetime.now(UTC) - timedelta(seconds=1)}
            )
        }
    )
    assert effective_status(expired, True) == "expired"


def test_trial_requires_private_distribution_and_bounded_duration_without_changing_legacy() -> None:
    legacy = dict(
        title="Pilot",
        episode="One",
        role_name="Performer",
        adaptation="Costume only",
        supporting_references=(),
    )
    assert ProductionUse.model_validate(legacy).model_dump(mode="json") == {
        **legacy,
        "supporting_references": [],
    }
    trial = {
        **legacy,
        "governance_profile_id": uuid4(),
        "responsible_operator": "viewer",
        "use_mode": "trial",
        "distribution": "private",
    }
    now = datetime.now(UTC)
    scope = dict(
        name="Rehearsal",
        recipient_ref="reviewer",
        asset_ids=(uuid4(),),
        purpose="Private test",
        conditions="No publication",
        starts_at=now,
        ends_at=now + timedelta(days=30),
    )
    accepted = CampaignScope.model_validate({**scope, "production": trial})
    assert accepted.production is not None and accepted.production.use_mode == "trial"
    with pytest.raises(ValidationError):
        ProductionUse.model_validate({**trial, "distribution": "public"})
    with pytest.raises(ValidationError):
        CampaignScope.model_validate(
            {**scope, "ends_at": now + timedelta(days=31), "production": trial}
        )
