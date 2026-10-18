"""Scope bounds, canonical retries and authoritative-field rejection."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from accord.personas.campaign_contracts import CampaignScope
from accord.personas.service import fingerprint
from personas.campaign_fixtures import campaign_scope, decision_intent, offer_intent


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", " "),
        ("name", "x" * 81),
        ("recipient_ref", ""),
        ("recipient_ref", "x" * 65),
        ("purpose", " "),
        ("conditions", "x" * 501),
        ("fixture", False),
        ("asset_ids", ()),
        ("asset_ids", tuple(uuid4() for _ in range(21))),
        ("owner_ref", "injected-owner"),
        ("role", "creator"),
        ("starts_at", datetime(2026, 10, 1)),
        ("ends_at", datetime(2027, 10, 1)),
    ],
)
def test_campaign_scope_rejects_invalid_or_authoritative_fields(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        campaign_scope((uuid4(),), **{field: value})


@pytest.mark.parametrize("days", [-1, 0, 367])
def test_campaign_duration_is_bounded(days: int) -> None:
    start = datetime.now(UTC)
    with pytest.raises(ValidationError, match="duration"):
        campaign_scope((uuid4(),), starts_at=start, ends_at=start + timedelta(days=days))


def test_assets_are_distinct_and_canonical_for_exact_retry() -> None:
    ids = (uuid4(), uuid4())
    scope = campaign_scope(ids)
    with pytest.raises(ValidationError, match="distinct"):
        campaign_scope((ids[0], ids[0]))
    reordered = CampaignScope.model_validate(
        {**scope.model_dump(), "asset_ids": tuple(reversed(ids))}
    )
    first = offer_intent(uuid4(), uuid4(), ids, scope=scope)
    second = type(first).model_validate({**first.model_dump(), "scope": reordered})
    assert fingerprint(first) == fingerprint(second)
    changed = type(first).model_validate({**first.model_dump(), "review_id": uuid4()})
    assert fingerprint(first) != fingerprint(changed)


@pytest.mark.parametrize(
    "field,value",
    [
        ("actor_ref", "creator-a"),
        ("role", "reviewer"),
        ("recorded_at", datetime.now(UTC)),
        ("decision", "auto_approved"),
        ("fixture", False),
        ("statement", " "),
    ],
)
def test_campaign_decision_rejects_forged_authority(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        decision_intent(uuid4(), **{field: value})
