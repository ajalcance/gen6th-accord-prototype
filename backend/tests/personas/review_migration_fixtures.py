"""Seed a review through the actual migrated schema, independent of campaign models."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Connection, select
from test_migrations import _seed_migrated_persona

from accord.personas.database_policy import TABLES
from accord.personas.review_policy import REVIEW_TABLES


def seed_review(connection: Connection) -> tuple[UUID, UUID, UUID]:
    workspace = _seed_migrated_persona(connection)
    version = connection.scalar(select(TABLES[2].c.id))
    assert isinstance(version, UUID)
    for actor_ref in ("fixture-reviewer", "fixture-recipient"):
        connection.execute(
            TABLES[0]
            .insert()
            .values(
                workspace_id=workspace,
                actor_ref=actor_ref,
                role="reviewer",
            )
        )
    review = uuid4()
    connection.execute(
        REVIEW_TABLES[0]
        .insert()
        .values(
            id=review,
            workspace_id=workspace,
            version_id=version,
            ordinal=1,
            reviewer_ref="fixture-reviewer",
            request_id=uuid4(),
            fingerprint="a" * 64,
            decision="approved",
            statement="Fictional independent review",
            recorded_at=datetime.now(UTC),
            event_id=uuid4().hex,
        )
    )
    return workspace, version, review
