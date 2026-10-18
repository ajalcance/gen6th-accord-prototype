"""Arithmetic, grouping and abstention fixtures do not measure identification accuracy."""

from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine

from accord.personas.face_vectors import cosine, unit_vector
from accord.personas.similarity_policy import CalibrationPolicy
from accord.personas.similarity_ranking import confident_candidates, ranked_personas
from accord.personas.similarity_repository import reference_pool
from personas.similarity_fixtures import candidate, policy


@pytest.mark.parametrize(
    "value", [[True, 0], [float("nan"), 0], [float("inf"), 0], [0, 0], [1, 1], [1], "bad"]
)
def test_invalid_vectors_cannot_enter_similarity(value: object) -> None:
    with pytest.raises(RuntimeError):
        unit_vector(value, 2)


def test_exact_cosine_and_dimension_mismatch() -> None:
    assert cosine((0.6, 0.8), (0.6, 0.8)) == 1
    assert cosine((1.0, 0.0), (-1.0, 0.0)) == -1
    assert cosine((1.0, 0.0), (0.0, 1.0)) == 0
    with pytest.raises(RuntimeError):
        cosine((1.0,), (1.0, 0.0))


def test_group_best_reference_deterministic_ties_and_context_does_not_rank() -> None:
    workspace, identity = uuid4(), uuid4()
    old = candidate(workspace, 0.95, identity)
    newer = candidate(workspace, 0.95, identity, 2)
    different = candidate(workspace, 0.7)
    ranked = ranked_personas([different, old, newer])
    assert ranked[0].generation_id == newer.generation_id
    assert ranked[0].compatible_references == 2
    assert ranked == ranked_personas([newer, different, old])
    assert ranked[0].whole_cosine == -0.9


def test_threshold_ambiguity_and_empty_abstain() -> None:
    workspace = uuid4()
    assert confident_candidates([], policy()) == ((), False)
    assert confident_candidates([candidate(workspace, 0.79)], policy()) == ((), False)
    assert confident_candidates(
        [candidate(workspace, 0.95), candidate(workspace, 0.94)], policy()
    ) == ((), False)
    best = candidate(workspace, 0.95)
    assert confident_candidates([best, candidate(workspace, 0.8)], policy())[0][0] == best


def test_limit_overflow_is_explicit() -> None:
    workspace = uuid4()
    rows = [candidate(workspace, 0.99)] + [candidate(workspace, 0.8) for _ in range(6)]
    items, more = confident_candidates(rows, policy())
    assert len(items) == 5 and more


@pytest.mark.parametrize(
    "changes",
    [
        {"margin": 0},
        {"threshold": float("nan")},
        {"provider_revision": "publisher-alias-unresolved"},
        {"expires_at": "2000-01-01T00:00:00Z"},
    ],
)
def test_unreviewable_policy_rejected(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        CalibrationPolicy.model_validate({**policy().model_dump(), **changes})


def test_current_and_history_sql_keep_workspace_and_latest_reference_binding() -> None:
    workspace = uuid4()
    dialect = create_engine("postgresql+asyncpg://").dialect
    current = str(
        reference_pool(workspace, "current").compile(
            dialect=dialect, compile_kwargs={"literal_binds": True}
        )
    )
    history = str(
        reference_pool(workspace, "history").compile(
            dialect=dialect, compile_kwargs={"literal_binds": True}
        )
    )
    assert "persona_versions.revision = personas.head_revision" in current
    assert "persona_versions.revision = personas.head_revision" not in history
    assert "DISTINCT ON" in current and "LIMIT 129" in current
    assert current.count(str(workspace)) >= 5
