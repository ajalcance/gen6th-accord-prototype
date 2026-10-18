"""The evidence builder resolves server search candidates and exact approved references."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import investigation_evidence as module
from accord.personas.investigation_contracts import InvestigationCommand, InvestigationResult
from accord.personas.investigation_provider import InvestigationRuntime
from accord.personas.repository import ConflictError
from accord.personas.similarity_contracts import SimilarityPage
from accord.personas.similarity_query import QueryCapture
from accord.personas.workflow_contracts import WorkflowActor
from personas.investigation_fixtures import result
from personas.similarity_fixtures import candidate
from personas.test_face_processing import image_bytes
from personas.test_similarity_service import runtime


def evidence_setup() -> tuple[InvestigationResult, InvestigationCommand, SimilarityPage]:
    packet = result()
    c = candidate(packet.workspace_id, 0.95)
    intent = InvestigationCommand(
        version_id=c.version.version_id,
        portrait_id=c.portrait_id,
        generation_id=c.generation_id,
        request_id=packet.request_id,
        query_id=packet.query.query_id,
        face_index=0,
        source_note="supplied",
        retain_findings=True,
    )
    page = SimilarityPage.model_validate(
        {
            **intent.model_dump(include={"request_id", "query_id", "face_index", "scope"}),
            "workspace_id": packet.workspace_id,
            "policy_id": "fixture",
            "evidence_sha256": "e" * 64,
            "state": "candidate_review",
            "reasons": (),
            "reference_count": 1,
            "compatible_count": 1,
            "items": (c,),
            "has_more": False,
        }
        | {"representation": runtime_info()}
    )
    return packet, intent, page


@pytest.mark.asyncio
@pytest.mark.parametrize("changed", ["none", "candidate", "generation", "catalogue"])
async def test_fresh_search_binds_generation_before_approved_pixels(
    changed: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    packet, intent, page = evidence_setup()
    if changed == "candidate":
        intent = intent.model_copy(update={"generation_id": uuid4()})
    monkeypatch.setattr(
        module,
        "load_query",
        AsyncMock(return_value=QueryCapture(packet.query, "fixture", image_bytes(), image_bytes())),
    )
    monkeypatch.setattr(module, "pool", AsyncMock(return_value=[]))
    monkeypatch.setattr(module, "searched_page", AsyncMock(return_value=page))
    monkeypatch.setattr(
        module, "reference", AsyncMock(return_value=(Mock(), Mock(sha256=packet.reference_sha256)))
    )
    monkeypatch.setattr(
        module,
        "generation",
        AsyncMock(
            return_value=Mock(
                id=uuid4() if changed == "generation" else page.items[0].generation_id
            )
        ),
    )
    pixels = AsyncMock(return_value=image_bytes())
    monkeypatch.setattr(module, "analysis_pixels", pixels)
    monkeypatch.setattr(
        module,
        "recheck_catalogue",
        AsyncMock(side_effect=ConflictError("changed") if changed == "catalogue" else None),
    )
    async with AsyncSession() as session:
        call = module.gather(
            session,
            packet.workspace_id,
            WorkflowActor(actor_ref="human", kind="human"),
            intent,
            InvestigationRuntime(runtime()),
        )
        if changed == "none":
            evidence = await call
            assert evidence.search.face_cosine == 0.95
            assert evidence.images.reference_image == image_bytes()
        else:
            with pytest.raises(ConflictError):
                await call
    if changed in {"candidate", "generation"}:
        pixels.assert_not_called()


def runtime_info() -> dict[str, object]:
    return {
        "model": "synthetic-model",
        "provider_revision": "fixture-v1",
        "dimensions": 2,
        "crop_recipe": "face-square-512-v1",
        "crop_sha256": "a" * 64,
        "quality_policy": "provisional-face-v1",
        "calibration": "benchmark_pending",
    }
