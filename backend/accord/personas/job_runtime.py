"""Explicit assembled providers and immutable configuration binding for durable work."""

from dataclasses import dataclass
from uuid import UUID

from accord.personas.evidence_crypto import KeyWrapper
from accord.personas.face_providers import FaceProviders
from accord.personas.task_google import TaskDispatcher


@dataclass(frozen=True)
class JobRuntime:
    workspace_id: UUID
    config_id: str
    wrapper: KeyWrapper
    faces: FaceProviders
    dispatcher: TaskDispatcher
