"""A serialized receipt cannot contradict its permission, assets or temporal scope."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from accord.personas.campaign_contracts import CampaignReceipt, CampaignStatus
from personas.campaign_fixtures import campaign_scope


def status_fixture() -> dict[str, object]:
    asset, campaign, workspace = uuid4(), uuid4(), uuid4()
    now = datetime.now(UTC)
    receipt = CampaignReceipt.model_validate(
        {
            "id": campaign,
            "workspace_id": workspace,
            "version_id": uuid4(),
            "review_id": uuid4(),
            "owner_ref": "creator-a",
            "scope": campaign_scope((asset,)),
            "assets": [{"id": asset, "digest": "a" * 64, "label": "Fictional portrait"}],
            "recorded_at": now,
            "event_id": uuid4().hex,
        }
    )
    return {
        "receipt": receipt,
        "latest_decision": {
            "id": uuid4(),
            "workspace_id": workspace,
            "campaign_id": campaign,
            "ordinal": 1,
            "actor_ref": "reviewer-b",
            "decision": "accepted",
            "statement": "Fictional acceptance",
            "recorded_at": now,
            "event_id": uuid4().hex,
        },
        "evaluated_at": now,
        "blocking_reasons": (),
        "eligible_for_use": True,
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"blocking_reasons": ("revoked",)},
        {"eligible_for_use": False},
        {"eligible_for_use": 1},
        {"latest_decision": None},
        {"evaluated_at": datetime.now(UTC) + timedelta(days=90)},
        {"evaluated_at": datetime.now(UTC) - timedelta(days=90)},
        {"evaluated_at": datetime(2026, 10, 1)},
    ],
)
def test_status_rejects_contradictory_eligibility(changes: dict[str, object]) -> None:
    fixture = status_fixture()
    assert CampaignStatus.model_validate(fixture).eligible_for_use
    with pytest.raises(ValidationError):
        CampaignStatus.model_validate({**fixture, **changes})


@pytest.mark.parametrize(
    "field,value",
    [
        ("workspace_id", uuid4()),
        ("campaign_id", uuid4()),
        ("actor_ref", "creator-a"),
    ],
)
def test_status_rejects_misattributed_decision(field: str, value: object) -> None:
    fixture = status_fixture()
    previous = fixture["latest_decision"]
    assert isinstance(previous, dict)
    with pytest.raises(ValidationError):
        CampaignStatus.model_validate({**fixture, "latest_decision": {**previous, field: value}})


@pytest.mark.parametrize(
    "changes",
    [
        {"assets": ()},
        {"owner_ref": "reviewer-b"},
        {"assets": [{"id": uuid4(), "digest": "a" * 64, "label": "Other"}]},
    ],
)
def test_receipt_rejects_missing_mismatched_assets_or_self_permission(
    changes: dict[str, object],
) -> None:
    receipt = status_fixture()["receipt"]
    assert isinstance(receipt, CampaignReceipt)
    with pytest.raises(ValidationError):
        CampaignReceipt.model_validate({**receipt.model_dump(), **changes})
