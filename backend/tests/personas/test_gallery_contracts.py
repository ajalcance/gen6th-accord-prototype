"""Bounded gallery input and output invariants without database dependencies."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from accord.personas.gallery import GalleryPage, GalleryQuery


@pytest.mark.parametrize(
    "payload",
    [
        {"limit": 0},
        {"limit": 101},
        {"limit": True},
        {"search": "x" * 81},
        {"after_persona_id": "invalid"},
        {"owner_ref": "creator-a"},
        {"workspace_id": str(uuid4())},
    ],
)
def test_gallery_query_rejects_unbounded_or_authoritative_input(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        GalleryQuery.model_validate(payload)


def test_empty_page_cannot_claim_another_page() -> None:
    with pytest.raises(ValidationError):
        GalleryPage(workspace_id=uuid4(), items=(), next_after_persona_id=uuid4())


def test_search_is_bounded_normalized_literal_text() -> None:
    assert GalleryQuery(search="  100%_Original  ").search == "100%_Original"
