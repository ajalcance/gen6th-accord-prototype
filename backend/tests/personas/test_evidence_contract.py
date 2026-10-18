"""Pure tests of reference validation; no substitutes for database execution."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from accord.personas.models import Version
from accord.personas.observability import validate_reference
from accord.personas.service import saved_event


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("tenant_id", uuid4()),
        ("action", "client.route_view"),
        ("actor_type", "system"),
        ("actor_id", "another-actor"),
        ("outcome", "failure"),
        ("ts", None),
        ("resource_type", "another-resource"),
        ("resource_id", str(uuid4())),
        ("metadata_", {}),
    ],
)
def test_mismatched_reference_is_rejected(field: str, value: object) -> None:
    version = Version(
        id=uuid4(),
        workspace_id=uuid4(),
        persona_id=uuid4(),
        revision=1,
        creator_ref="creator-a",
        event_id=uuid4().hex,
        recorded_at=datetime.now(UTC),
    )
    event = saved_event(version, "creator-a", uuid4())
    setattr(event, field, value)
    with pytest.raises(RuntimeError, match="references disagree"):
        validate_reference(event, version)


def test_matching_reference_passes() -> None:
    version = Version(
        id=uuid4(),
        workspace_id=uuid4(),
        persona_id=uuid4(),
        revision=1,
        creator_ref="creator-a",
        event_id=uuid4().hex,
        recorded_at=datetime.now(UTC),
    )
    validate_reference(saved_event(version, "creator-a", uuid4()), version)
