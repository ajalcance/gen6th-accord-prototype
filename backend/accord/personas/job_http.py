"""Studio job controls use human sessions; private delivery uses separately verified Google OIDC."""

from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas import job_service, job_worker
from accord.personas.face_contracts import FaceCommand, FaceSubject
from accord.personas.face_http import bounded_intent
from accord.personas.job_contracts import JobPage, JobReceipt, JobUpdate
from accord.personas.job_runtime import JobRuntime
from accord.personas.passport_http import intent
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.task_google import TaskReference
from accord.personas.task_identity import GoogleTaskIdentity
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.write_http import PrivateWriteRoute


def create_job_router(
    verifier: PersonaSessionVerifier | None,
    runtime: JobRuntime | None,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/workspaces/{workspace_id}/personas/jobs", route_class=PrivateWriteRoute
    )

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    @router.post("/enqueue", response_model=JobReceipt)
    async def enqueue(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> JobReceipt:
        command = await intent(session, workspace_id, who, request, FaceCommand)
        return await job_service.enqueue(session, workspace_id, who, command, runtime)

    @router.post("/history", response_model=JobPage)
    async def history(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> JobPage:
        command = await intent(session, workspace_id, who, request, FaceSubject)
        return await job_service.history(session, workspace_id, who, command)

    @router.post("/update", response_model=JobReceipt)
    async def update(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> JobReceipt:
        command = await intent(session, workspace_id, who, request, JobUpdate)
        return await job_service.update(session, workspace_id, who, command, runtime)

    return router


def create_task_router(
    runtime: JobRuntime | None, identity: GoogleTaskIdentity | None
) -> APIRouter:
    router = APIRouter(prefix="/internal/personas/jobs", route_class=PrivateWriteRoute)

    async def machine(request: Request) -> str:
        if runtime is None or identity is None:
            raise HTTPException(503, "worker unavailable")
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            raise HTTPException(401, "worker identity required")
        try:
            return await identity.verify(authorization[7:])
        except PermissionError as exc:
            raise HTTPException(401, "worker identity rejected") from exc

    register_execute(router, machine, runtime)
    register_reconcile(router, machine, runtime)
    return router


def register_execute(
    router: APIRouter,
    machine: Callable[[Request], Awaitable[str]],
    runtime: JobRuntime | None,
) -> None:
    @router.post("/execute")
    async def execute(
        request: Request,
        principal: Annotated[str, Depends(machine)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> dict[str, str]:
        ref = await bounded_intent(request, TaskReference)
        if runtime is None:
            raise HTTPException(503, "worker unavailable")
        await job_worker.execute(session, ref, runtime, principal)
        return {"state": "acknowledged"}


def register_reconcile(
    router: APIRouter,
    machine: Callable[[Request], Awaitable[str]],
    runtime: JobRuntime | None,
) -> None:
    @router.post("/reconcile")
    async def reconcile(
        principal: Annotated[str, Depends(machine)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> dict[str, int]:
        if runtime is None:
            raise HTTPException(503, "worker unavailable")
        return await job_worker.reconcile(session, runtime, principal)
