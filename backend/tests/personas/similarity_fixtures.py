"""Synthetic vectors/policy only; real Pillow captures and AES-GCM ciphertext."""

import base64
import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from accord.personas.contracts import PersonaDraft, PersonaVersion
from accord.personas.photo_contracts import PhotoUpload
from accord.personas.similarity_contracts import SimilarityCandidate
from accord.personas.similarity_policy import CalibrationPolicy
from personas.test_face_processing import face, image_bytes


def policy(**changes: object) -> CalibrationPolicy:
    now = datetime.now(UTC)
    return CalibrationPolicy.model_validate(
        {
            "policy_id": "synthetic-policy",
            "dataset_id": "synthetic-only",
            "run_id": "fixture",
            "evidence_sha256": "a" * 64,
            "model": "synthetic-encoder",
            "provider_revision": "fixture-v1",
            "dimensions": 2,
            "detector": "synthetic-detector",
            "decoder_version": "Pillow-12.3.0",
            "threshold": 0.8,
            "margin": 0.05,
            "reviewed_at": now - timedelta(minutes=1),
            "expires_at": now + timedelta(hours=1),
            **changes,
        }
    )


def upload() -> PhotoUpload:
    data = image_bytes()
    return PhotoUpload(
        request_id=uuid4(),
        media_type="image/png",
        byte_length=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        data=base64.b64encode(data).decode(),
    )


def candidate(
    workspace: UUID, score: float, identity: UUID | None = None, revision: int = 1
) -> SimilarityCandidate:
    version = PersonaVersion(
        workspace_id=workspace,
        persona_id=identity or uuid4(),
        version_id=uuid4(),
        revision=revision,
        creator_ref="synthetic-human",
        recorded_at=datetime.now(UTC),
        content=PersonaDraft(
            name="Synthetic performer",
            biography="Fixture",
            human_contribution="Fixture",
            ai_disclosure="Fixture",
        ),
    )
    return SimilarityCandidate(
        version=version,
        portrait_id=uuid4(),
        generation_id=uuid4(),
        face=face(),
        face_cosine=score,
        whole_cosine=-0.9,
        compatible_references=1,
    )
