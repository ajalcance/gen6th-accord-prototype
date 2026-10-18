"""Build a fresh server search receipt; browser scores and findings are never evidence."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.face_contracts import FaceSubject
from accord.personas.face_providers import quality_reasons
from accord.personas.face_repository import generation, reference
from accord.personas.face_storage import analysis_pixels
from accord.personas.investigation_contracts import InvestigationCommand, SearchEvidence
from accord.personas.investigation_provider import ComparisonInput, InvestigationRuntime
from accord.personas.repository import ConflictError
from accord.personas.similarity_contracts import SearchCommand, SimilarityCandidate, SimilarityPage
from accord.personas.similarity_query import QueryCapture, available, load_query
from accord.personas.similarity_repository import pool, pool_binding
from accord.personas.similarity_service import recheck_catalogue, searched_page
from accord.personas.workflow_contracts import WorkflowActor


@dataclass(frozen=True)
class GroundedEvidence:
    capture: QueryCapture
    search: SearchEvidence
    images: ComparisonInput
    reference_sha256: str
    catalogue: tuple[tuple[UUID, UUID, UUID | None], ...]


async def gather(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: InvestigationCommand,
    runtime: InvestigationRuntime,
) -> GroundedEvidence:
    active = available(runtime.similarity)
    capture = await load_query(active, workspace, actor.actor_ref, command.query_id)
    if command.face_index >= len(capture.receipt.faces):
        raise ConflictError("selected face unavailable")
    search_command = SearchCommand.model_validate(
        {field: getattr(command, field) for field in SearchCommand.model_fields}
    )
    binding = pool_binding(await pool(session, workspace, command.scope))
    reasons = quality_reasons(capture.receipt.faces[command.face_index])
    page = await searched_page(session, workspace, actor, search_command, active, capture, reasons)
    candidate = next(
        (
            item
            for item in page.items
            if (
                item.version.version_id == command.version_id
                and item.portrait_id == command.portrait_id
                and item.generation_id == command.generation_id
            )
        ),
        None,
    )
    if candidate is None:
        raise ConflictError("candidate no longer matches the fresh search receipt")
    image, digest = await reference_image(session, workspace, actor, command, runtime)
    await recheck_catalogue(session, workspace, actor, search_command, active, binding)
    receipt = search_evidence(page, candidate)
    return GroundedEvidence(
        capture,
        receipt,
        ComparisonInput(
            capture.analysis, image, capture.receipt.faces[command.face_index], candidate.face
        ),
        digest,
        binding,
    )


def search_evidence(page: SimilarityPage, candidate: SimilarityCandidate) -> SearchEvidence:
    return SearchEvidence(
        request_id=page.request_id,
        method=page.method,
        policy_id=page.policy_id,
        evidence_sha256=page.evidence_sha256,
        scope=page.scope,
        face_index=page.face_index,
        face_cosine=candidate.face_cosine,
        whole_cosine=candidate.whole_cosine,
    )


async def reference_image(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: InvestigationCommand,
    runtime: InvestigationRuntime,
) -> tuple[bytes, str]:
    subject = FaceSubject(version_id=command.version_id, portrait_id=command.portrait_id)
    photo, stored = await reference(session, workspace, actor.actor_ref, subject, write=False)
    row = await generation(session, workspace, subject)
    if row is None or row.id != command.generation_id:
        raise ConflictError("reference generation changed")
    return await analysis_pixels(photo, stored, runtime.similarity.wrapper), stored.sha256
