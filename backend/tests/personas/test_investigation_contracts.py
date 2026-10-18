"""Unsupported findings, missing citations and client claims fail closed."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from accord.personas.investigation_contracts import (
    InvestigationCommand,
    InvestigationResult,
    ProviderFindings,
)
from personas.investigation_fixtures import command, result


@pytest.mark.parametrize(
    "field,value",
    [
        ("actor_ref", "attacker"),
        ("findings", {}),
        ("face_cosine", 1.0),
        ("retain_findings", False),
        ("source_note", "x" * 501),
    ],
)
def test_browser_actor_scores_findings_and_unconfirmed_retention_are_rejected(
    field: str, value: object
) -> None:
    data = command().model_dump()
    data[field] = value
    with pytest.raises(ValidationError):
        InvestigationCommand.model_validate(data)


@pytest.mark.parametrize(
    "label,citations",
    [
        ("infringement_confirmed", ["query_image", "approved_reference"]),
        ("pose_differs", ["web_search", "approved_reference"]),
        ("pose_differs", ["query_image", "query_image"]),
        ("pose_differs", ["query_image"]),
    ],
)
def test_unsupported_claim_or_unavailable_citation_is_not_a_finding(
    label: str, citations: list[str]
) -> None:
    with pytest.raises(ValidationError):
        ProviderFindings(
            state="observations", observations=({"label": label, "citations": citations},)
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"state": "observations", "observations": []},
        {
            "state": "insufficient_evidence",
            "observations": [
                {"label": "pose_differs", "citations": ["query_image", "approved_reference"]}
            ],
        },
        {"state": "insufficient_evidence", "observations": [], "ownership": "verified"},
    ],
)
def test_state_and_extra_conclusions_are_rejected(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ProviderFindings.model_validate(changes)


@pytest.mark.parametrize(
    "changes", [{"workspace_id": uuid4()}, {"gaps": []}, {"request_id": uuid4()}]
)
def test_packet_binding_and_mandatory_gaps(changes: dict[str, object]) -> None:
    data = result().model_dump()
    data.update(changes)
    with pytest.raises(ValidationError):
        InvestigationResult.model_validate(data)


def test_duplicates_and_contradictory_observations_are_rejected() -> None:
    row = {"label": "facial_features_similar", "citations": ["query_image", "approved_reference"]}
    for second in (row, {**row, "label": "facial_features_different"}):
        with pytest.raises(ValidationError):
            ProviderFindings(state="observations", observations=(row, second))
    assert ProviderFindings(state="insufficient_evidence", observations=()).observations == ()
