"""Bounded and membership-scoped review history."""

from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.reviews import record_review, review_history
from accord.personas.workflow_contracts import ReviewHistoryQuery
from personas.workflow_fixtures import draft_for_review, human, review_intent


@pytest.mark.parametrize(
    "field,value",
    [
        ("limit", 0),
        ("limit", 101),
        ("limit", True),
        ("before_ordinal", 0),
        ("before_ordinal", True),
    ],
)
def test_history_query_rejects_invalid_bounds(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        ReviewHistoryQuery.model_validate({"version_id": UUID(int=1), field: value})


async def test_review_history_has_stable_bounded_cursor(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await draft_for_review(session, workspace)
    empty = await review_history(
        session, workspace, human("viewer"), ReviewHistoryQuery(version_id=version.version_id)
    )
    assert empty.items == () and empty.next_before_ordinal is None
    first = await record_review(
        session, workspace, human("reviewer-a"), review_intent(version.version_id)
    )
    second = await record_review(
        session,
        workspace,
        human("reviewer-b"),
        review_intent(
            version.version_id,
            expected_previous_id=first.id,
            decision="changes_requested",
        ),
    )
    page = await review_history(
        session,
        workspace,
        human("viewer"),
        ReviewHistoryQuery(version_id=version.version_id, limit=1),
    )
    assert [row.id for row in page.items] == [second.id] and page.next_before_ordinal == 2
    last = await review_history(
        session,
        workspace,
        human("viewer"),
        ReviewHistoryQuery(
            version_id=version.version_id,
            limit=1,
            before_ordinal=page.next_before_ordinal,
        ),
    )
    assert [row.id for row in last.items] == [first.id] and last.next_before_ordinal is None
