"""Synthetic receipts only; no Gemini or face accuracy evidence."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from accord.personas.investigation_contracts import (
    InvestigationCommand,
    InvestigationResult,
    ProviderFindings,
    SearchEvidence,
)
from accord.personas.similarity_contracts import QueryReceipt
from personas.test_face_processing import face


def command() -> InvestigationCommand:
    return InvestigationCommand(
        request_id=uuid4(),
        query_id=uuid4(),
        face_index=0,
        version_id=uuid4(),
        portrait_id=uuid4(),
        generation_id=uuid4(),
        source_note="Owner supplied a frame; posting context unverified.",
        retain_findings=True,
    )


def result(
    workspace: UUID | None = None, intent: InvestigationCommand | None = None
) -> InvestigationResult:
    w, c, now = workspace or uuid4(), intent or command(), datetime.now(UTC)
    receipt = QueryReceipt(
        workspace_id=w,
        query_id=c.query_id,
        source_sha256="a" * 64,
        analysis_sha256="b" * 64,
        thumbnail_sha256="c" * 64,
        width=200,
        height=100,
        detector="synthetic",
        decoder_version="synthetic",
        issued_at=now,
        expires_at=now + timedelta(minutes=10),
        faces=(face(),),
        state="selection_required",
    )
    return InvestigationResult(
        id=uuid4(),
        workspace_id=w,
        version_id=c.version_id,
        portrait_id=c.portrait_id,
        generation_id=c.generation_id,
        request_id=c.request_id,
        ordinal=1,
        actor_ref="synthetic-human",
        recorded_at=now,
        source_note=c.source_note,
        query=receipt,
        reference_sha256="d" * 64,
        reference_face=face(),
        search=SearchEvidence(
            request_id=c.request_id,
            method="exact-cosine-face-max-v1",
            policy_id="synthetic-reviewed",
            evidence_sha256="e" * 64,
            scope=c.scope,
            face_index=c.face_index,
            face_cosine=0.9,
            whole_cosine=0.7,
        ),
        model="synthetic-model",
        provider_revision="fixture-v1",
        findings=findings(),
    )


def findings() -> ProviderFindings:
    return ProviderFindings(
        state="observations",
        observations=(
            {"label": "pose_differs", "citations": ("query_image", "approved_reference")},
        ),
    )
