"""Bounded real REST task transport; no task or queue is created."""

import base64
import json
from uuid import uuid4

import httpx
import pytest

from accord.personas.face_google import GoogleTransport
from accord.personas.task_google import GoogleTaskDispatcher, TaskReference
from personas.runtime_fixtures import task_config


class Access:
    async def token(self) -> str:
        return "synthetic-workload-handle"


@pytest.mark.asyncio
@pytest.mark.parametrize("existing", [False, True])
async def test_deterministic_tasks_contain_only_scoped_references_and_oidc(existing: bool) -> None:
    calls: list[dict[str, object]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        task = json.loads(request.content)["task"]
        calls.append(task)
        return (
            httpx.Response(409, json={"error": {"status": "ALREADY_EXISTS"}})
            if existing
            else httpx.Response(200, json={"name": task["name"]})
        )

    config = task_config()
    dispatcher = GoogleTaskDispatcher(
        config, GoogleTransport(Access(), httpx.MockTransport(respond))
    )
    reference = TaskReference(workspace_id=uuid4(), job_id=uuid4(), dispatch_id=uuid4())
    await dispatcher.dispatch(reference)
    await dispatcher.dispatch(reference)
    assert calls[0] == calls[1]
    task = calls[0]
    assert task["dispatchDeadline"] == "120s"
    request = task["httpRequest"]
    assert isinstance(request, dict)
    assert request["oidcToken"] == {
        "serviceAccountEmail": config.service_email,
        "audience": config.worker_origin,
    }
    assert json.loads(base64.b64decode(request["body"])) == reference.model_dump(mode="json")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(409, json={"error": {"status": "OTHER"}}),
        httpx.Response(200, json={"name": "different-task"}),
        httpx.Response(302, headers={"Location": "https://arbitrary.test"}),
    ],
)
async def test_other_conflicts_wrong_tasks_and_redirects_do_not_confirm_dispatch(
    response: httpx.Response,
) -> None:
    dispatcher = GoogleTaskDispatcher(
        task_config(), GoogleTransport(Access(), httpx.MockTransport(lambda _: response))
    )
    with pytest.raises(RuntimeError):
        await dispatcher.dispatch(
            TaskReference(workspace_id=uuid4(), job_id=uuid4(), dispatch_id=uuid4())
        )
