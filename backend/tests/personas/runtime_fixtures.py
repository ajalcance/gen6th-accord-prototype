"""Synthetic runtime configuration and jobs; no deployed resources or stored keys."""

from datetime import UTC, datetime
from uuid import uuid4

from accord.personas.face_contracts import FaceCommand
from accord.personas.face_storage import command_fingerprint
from accord.personas.job_models import FaceJob, FaceJobTransition
from accord.personas.runtime_contracts import GoogleRuntimeConfig, TaskConfig


def task_config() -> TaskConfig:
    return TaskConfig(
        queue="projects/synthetic-project/locations/us-central1/queues/face-jobs",
        worker_origin="https://synthetic-worker.run.app",
        service_email="job-worker@synthetic-project.iam.gserviceaccount.com",
        service_subject="123456789012345678901",
    )


def config() -> GoogleRuntimeConfig:
    return GoogleRuntimeConfig(
        workspace_id=uuid4(),
        project="synthetic-project",
        region="us-central1",
        dimensions=128,
        wrapping_version="projects/synthetic-project/locations/us-central1/"
        "keyRings/test/cryptoKeys/wrapping/cryptoKeyVersions/1",
        tasks=task_config(),
    )


def job_rows(state: str = "queued", attempts: int = 0) -> tuple[FaceJob, FaceJobTransition]:
    command = FaceCommand(version_id=uuid4(), portrait_id=uuid4(), request_id=uuid4())
    now = datetime.now(UTC)
    row = FaceJob(
        id=command.request_id,
        workspace_id=uuid4(),
        version_id=command.version_id,
        portrait_id=command.portrait_id,
        request_id=command.request_id,
        actor_ref="synthetic-creator",
        config_id="a" * 64,
        fingerprint=command_fingerprint(command),
        command=command.model_dump(mode="json"),
        recorded_at=now,
    )
    event = FaceJobTransition(
        workspace_id=row.workspace_id,
        job_id=row.id,
        sequence=0,
        request_id=uuid4(),
        fingerprint="b" * 64,
        dispatch_id=row.id,
        state=state,
        attempts=attempts,
        recorded_at=now,
        lease_until=None,
        generation_id=None,
    )
    return row, event
