"""Deterministic reference-only Cloud Tasks dispatch, bounded OIDC identity and deadline."""

import base64
import hashlib
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from accord.personas.face_google import GoogleTransport
from accord.personas.runtime_contracts import TaskConfig


class TaskReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    job_id: UUID
    dispatch_id: UUID


class TaskDispatcher(Protocol):
    async def dispatch(self, reference: TaskReference) -> None: ...


class GoogleTaskDispatcher:
    def __init__(self, config: TaskConfig, transport: GoogleTransport) -> None:
        self.config, self.transport = config, transport

    async def dispatch(self, reference: TaskReference) -> None:
        body = reference.model_dump_json().encode()
        name = self.config.queue + "/tasks/" + hashlib.sha256(body).hexdigest()
        result = await self.transport.post(
            f"https://cloudtasks.googleapis.com/v2/{self.config.queue}/tasks",
            self.config.queue.split("/")[1],
            {
                "task": {
                    "name": name,
                    "dispatchDeadline": "120s",
                    "httpRequest": {
                        "httpMethod": "POST",
                        "url": self.config.worker_origin + "/internal/personas/jobs/execute",
                        "headers": {"Content-Type": "application/json"},
                        "body": base64.b64encode(body).decode(),
                        "oidcToken": {
                            "serviceAccountEmail": self.config.service_email,
                            "audience": self.config.worker_origin,
                        },
                    },
                },
            },
            allow_existing=True,
        )
        if result.get("already_exists") is not True and result.get("name") != name:
            raise RuntimeError("task dispatch binding unavailable")
