"""Scoped metadata checks do not decrypt evidence or equate scans with legal consent."""

from typing import cast
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.production_evidence import (
    require_supporting_evidence,
    supporting_evidence_available,
)
from accord.personas.repository import AccessDeniedError
from personas.passport_fixtures import production


@pytest.mark.asyncio
async def test_evidence_requires_owner_exact_version_clean_unexpired_retained_payload() -> None:
    evidence, workspace, version = uuid4(), uuid4(), uuid4()
    use = type(production()).model_validate(
        {
            **production().model_dump(),
            "supporting_references": [{"kind": "consent", "evidence_id": evidence}],
        }
    )
    fake = Mock(scalars=AsyncMock(return_value=[evidence]))
    session = cast(AsyncSession, fake)
    assert await supporting_evidence_available(session, workspace, version, "owner", use)
    sql = str(fake.scalars.await_args.args[0])
    assert all(
        field in sql
        for field in (
            "workspace_id",
            "version_id",
            "owner_ref",
            "expires_at",
            "verdict",
            "private_evidence_payloads",
        )
    )
    parameters = fake.scalars.await_args.args[0].compile().params
    assert (
        workspace in parameters.values()
        and version in parameters.values()
        and "owner" in parameters.values()
        and "clean" in parameters.values()
    )
    fake.scalars.return_value = []
    with pytest.raises(AccessDeniedError):
        await require_supporting_evidence(session, workspace, version, "owner", use)


@pytest.mark.asyncio
async def test_optional_claim_gaps_do_not_invent_evidence_or_query_unrelated_rows() -> None:
    fake = Mock(scalars=AsyncMock())
    for use in (None, production()):
        assert await supporting_evidence_available(
            cast(AsyncSession, fake), uuid4(), uuid4(), "owner", use
        )
    fake.scalars.assert_not_called()
