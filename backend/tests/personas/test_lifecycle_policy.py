"""Fresh authority/rights policy and retained evidence attestation boundaries."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import lifecycle_evidence as evidence
from accord.personas import lifecycle_policy as policy
from accord.personas.production_contracts import ProductionUse
from accord.personas.repository import AccessDeniedError
from personas.lifecycle_fixtures import dossier, requirements


@pytest.mark.asyncio
async def test_evidence_snapshot_requires_clean_owned_exact_version_payload() -> None:
    session, content = AsyncMock(spec=AsyncSession), dossier()
    ids = {content.operator.evidence_id, content.rights[0].evidence_id}
    session.execute.return_value = [(key, "a" * 64) for key in ids]
    assert set(await evidence.capture_digests(session, uuid4(), uuid4(), "creator-a", content)) == {
        str(key) for key in ids
    }
    session.execute.return_value = []
    with pytest.raises(AccessDeniedError):
        await evidence.capture_digests(session, uuid4(), uuid4(), "creator-a", content)
    assert (
        await evidence.capture_digests(session, uuid4(), uuid4(), "creator-a", content, "content")
        == {}
    )


@pytest.mark.asyncio
async def test_disabled_policy_cannot_accept_a_bound_lifecycle_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(policy, "get_settings", lambda: Mock(persona_lifecycle_enabled=False))
    now = datetime.now(UTC)
    session = AsyncMock(spec=AsyncSession)
    args = (session, uuid4(), uuid4(), uuid4())
    assert await policy.lifecycle_blocks(*args, None, now, now + timedelta(days=1)) == []
    production = ProductionUse(
        title="Pilot",
        episode="One",
        role_name="Lead",
        adaptation="Costume",
        supporting_references=(),
        governance_profile_id=uuid4(),
        responsible_operator="viewer",
    )
    assert await policy.lifecycle_blocks(*args, production, now, now + timedelta(days=1)) == [
        "lifecycle_unavailable"
    ]


@pytest.mark.asyncio
async def test_suspension_applies_even_without_a_current_version_dossier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(policy, "get_settings", lambda: Mock(persona_lifecycle_enabled=True))
    monkeypatch.setattr(policy, "is_suspended", AsyncMock(return_value=True))
    monkeypatch.setattr(policy, "latest", AsyncMock(return_value=None))
    now = datetime.now(UTC)
    reasons = await policy.lifecycle_blocks(
        AsyncMock(), uuid4(), uuid4(), uuid4(), None, now, now + timedelta(days=1)
    )
    assert reasons == ["performer_suspended", "governance_missing"]


@pytest.mark.asyncio
async def test_replacement_role_loss_expiry_voice_and_permission_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(policy, "get_settings", lambda: Mock(persona_lifecycle_enabled=True))
    monkeypatch.setattr(policy, "is_suspended", AsyncMock(return_value=False))
    content, profile = dossier(), Mock(id=uuid4())
    profile.content = content.model_dump(mode="json")
    monkeypatch.setattr(policy, "latest", AsyncMock(return_value=profile))
    approvals = requirements(profile.id)
    lookup = AsyncMock(return_value=approvals)
    monkeypatch.setattr(policy, "requirements", lookup)
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = Mock()
    use = ProductionUse(
        title="Pilot",
        episode="One",
        role_name="Lead",
        adaptation="Costume",
        supporting_references=(),
        governance_profile_id=profile.id,
        responsible_operator="viewer",
    )
    now, args = datetime.now(UTC), (session, uuid4(), uuid4(), uuid4())
    assert await policy.lifecycle_blocks(*args, use, now, now + timedelta(days=1)) == []
    # No payload lookup occurs: already recorded attestations have their own bounded lifetime.
    session.execute.assert_not_called()
    changed = use.model_copy(update={"governance_profile_id": uuid4(), "voice_use": True})
    session.get.return_value = None
    reasons = await policy.lifecycle_blocks(*args, changed, now, now + timedelta(days=31))
    assert set(reasons) == {
        "governance_changed",
        "operator_unavailable",
        "governance_expired",
        "rights_window_unavailable",
        "voice_rights_missing",
    }
    lookup.return_value = tuple(
        item.model_copy(update={"status": "withdrawn"}) for item in approvals
    )
    assert "governance_review_required" in await policy.lifecycle_blocks(
        *args, use, now, now + timedelta(days=1)
    )
