"""Advisory reviewer brief route: audited read of one saved version, then a Gemini draft.

The model sees only the four creator-written text fields of one version the signed-in actor may
read. It returns a draft for a human reviewer and never approves, identifies or decides rights.
"""

import asyncio
import time
from collections import deque
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.logger import logger
from accord.personas.assistant_contracts import NOTICE, BriefQuery, ReviewerBrief
from accord.personas.assistant_google import BriefProvider
from accord.personas.read_http import PrivateReadRoute, ReadError
from accord.personas.service import load
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.workflow_contracts import WorkflowActor

CALL_TIMEOUT_SECONDS = 45
CONCURRENT_CALLS = 4


class BriefLimiter:
    """Per-actor sliding window held in process memory; a restart only ever loosens it briefly."""

    def __init__(self, limit: int = 10, window: float = 600.0, tracked: int = 2000) -> None:
        self.limit, self.window, self.tracked = limit, window, tracked
        self._hits: dict[str, deque[float]] = {}

    def allow(self, actor_ref: str, now: float | None = None) -> bool:
        moment = time.monotonic() if now is None else now
        hits = self._hits.setdefault(actor_ref, deque())
        while hits and moment - hits[0] >= self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            return False
        hits.append(moment)
        if len(self._hits) > self.tracked:
            self._hits = {k: v for k, v in self._hits.items() if v and moment - v[-1] < self.window}
        return True


def create_assistant_router(
    verifier: PersonaSessionVerifier | None,
    provider: BriefProvider | None,
    limiter: BriefLimiter | None = None,
) -> APIRouter:
    """Always mounted so the route is registered; unavailable (503) until explicitly enabled."""
    router = APIRouter(
        prefix="/api/workspaces/{workspace_id}/personas/assistant",
        tags=["persona assistant"],
        route_class=PrivateReadRoute,
        responses={code: {"model": ReadError} for code in (401, 403, 422, 429, 503)},
    )
    window = limiter or BriefLimiter()
    gate = asyncio.Semaphore(CONCURRENT_CALLS)

    async def trusted_actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    @router.post("/brief", response_model=ReviewerBrief)
    async def brief(
        workspace_id: UUID,
        query: BriefQuery,
        actor: Annotated[WorkflowActor, Depends(trusted_actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> ReviewerBrief:
        if provider is None:
            raise HTTPException(status_code=503)
        if not window.allow(actor.actor_ref):
            raise HTTPException(status_code=429)
        version = await load(
            session, workspace_id, actor.actor_ref, query.persona_id, query.revision
        )
        try:
            async with gate, asyncio.timeout(CALL_TIMEOUT_SECONDS):
                draft, revision = await provider.brief(version.content)
        except Exception as exc:
            logger.error(
                "reviewer brief unavailable (incident_id=%s, type=%s)", uuid4(), type(exc).__name__
            )
            raise HTTPException(status_code=503) from exc
        return ReviewerBrief(
            persona_id=version.persona_id,
            version_id=version.version_id,
            revision=version.revision,
            state=draft.state,
            summary=draft.summary,
            gaps=draft.gaps,
            questions=draft.questions,
            model=provider.label,
            model_revision=revision,
            generated_at=datetime.now(UTC),
            notice=NOTICE,
        )

    return router
