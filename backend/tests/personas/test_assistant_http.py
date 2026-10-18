"""Reviewer-brief route through real ASGI routing; the version loader is stubbed (no database)."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from accord.db.connection import get_db
from accord.personas import assistant_http
from accord.personas.assistant_contracts import NOTICE, BriefDraft
from accord.personas.assistant_http import BriefLimiter, create_assistant_router
from accord.personas.contracts import PersonaDraft, PersonaVersion
from accord.personas.repository import AccessDeniedError
from personas.test_session_boundary import verified

WORKSPACE, PERSONA = uuid4(), uuid4()
PATH = f"/api/workspaces/{WORKSPACE}/personas/assistant/brief"
BODY = {"persona_id": str(PERSONA), "revision": 1}
DRAFT = BriefDraft(
    state="brief",
    summary="The creator states that Nova is a fictional editorial character.",
    gaps=["Which tools produced the visuals is not stated."],
    questions=["Which tools did you use?"],
)


def saved() -> PersonaVersion:
    return PersonaVersion(
        persona_id=PERSONA,
        workspace_id=WORKSPACE,
        version_id=uuid4(),
        revision=1,
        creator_ref="creator-a",
        recorded_at=datetime.now(UTC),
        content=PersonaDraft(
            name="Fictional Nova",
            biography="Fictional editorial character.",
            human_contribution="Original fictional character concept.",
            ai_disclosure="Synthetic fixture; no real person represented.",
        ),
    )


class FakeProvider:
    label = "google/global/gemini-3.8-flash"

    def __init__(self) -> None:
        self.brief = AsyncMock(return_value=(DRAFT, "gemini-observed"))


@pytest.fixture
def loader(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    stub = AsyncMock(return_value=saved())
    monkeypatch.setattr(assistant_http, "load", stub)
    return stub


def session_provider() -> AsyncMock:
    provider = AsyncMock()
    provider.verify.return_value = verified()
    return provider


@asynccontextmanager
async def client_for(
    provider: FakeProvider | None,
    verifier: AsyncMock | None = None,
    limiter: BriefLimiter | None = None,
) -> AsyncIterator[AsyncClient]:
    app = FastAPI()
    app.include_router(create_assistant_router(verifier or session_provider(), provider, limiter))

    async def database() -> AsyncIterator[object]:
        yield object()

    app.dependency_overrides[get_db] = database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def test_brief_returns_the_draft_with_provenance_and_the_fixed_notice(
    loader: AsyncMock,
) -> None:
    ai = FakeProvider()
    async with client_for(ai) as client:
        reply = await client.post(PATH, json=BODY)
    assert reply.status_code == 200
    data = reply.json()
    assert data["summary"] == DRAFT.summary and data["gaps"] == DRAFT.gaps
    assert data["model"] == ai.label and data["model_revision"] == "gemini-observed"
    assert data["notice"] == NOTICE and data["state"] == "brief" and data["revision"] == 1
    assert reply.headers["cache-control"] == "no-store"
    loaded = loader.await_args
    assert loaded is not None and loaded.args[1:] == (WORKSPACE, "viewer", PERSONA, 1)
    sent = ai.brief.await_args
    assert sent is not None and sent.args[0] == saved().content.model_copy()


async def test_unconfigured_provider_is_unavailable_without_reading_the_record(
    loader: AsyncMock,
) -> None:
    async with client_for(None) as client:
        reply = await client.post(PATH, json=BODY)
    assert reply.status_code == 503
    loader.assert_not_awaited()


async def test_a_missing_or_denied_session_never_reaches_the_model(loader: AsyncMock) -> None:
    ai, verifier = FakeProvider(), session_provider()
    verifier.verify.return_value = None
    async with client_for(ai, verifier) as client:
        reply = await client.post(PATH, json=BODY)
    assert reply.status_code == 401
    ai.brief.assert_not_awaited()
    loader.assert_not_awaited()


async def test_no_membership_means_no_model_call(loader: AsyncMock) -> None:
    loader.side_effect = AccessDeniedError
    ai = FakeProvider()
    async with client_for(ai) as client:
        reply = await client.post(PATH, json=BODY)
    assert reply.status_code == 403
    ai.brief.assert_not_awaited()


@pytest.mark.parametrize(
    "body",
    [
        {**BODY, "actor_ref": "creator-a"},
        {**BODY, "content": {"name": "injected"}},
        {"revision": 1},
        {**BODY, "revision": "1"},
        {**BODY, "revision": 0},
        {**BODY, "persona_id": "not-a-uuid"},
    ],
)
async def test_the_client_cannot_supply_actor_or_content(
    loader: AsyncMock, body: dict[str, object]
) -> None:
    ai = FakeProvider()
    async with client_for(ai) as client:
        reply = await client.post(PATH, json=body)
    assert reply.status_code == 422
    ai.brief.assert_not_awaited()


@pytest.mark.parametrize("failure", [RuntimeError("x"), TimeoutError(), ValueError("bad")])
async def test_any_model_failure_is_an_opaque_503(loader: AsyncMock, failure: Exception) -> None:
    ai = FakeProvider()
    ai.brief.side_effect = failure
    async with client_for(ai) as client:
        reply = await client.post(PATH, json=BODY)
    assert reply.status_code == 503
    assert "Fictional" not in reply.text and "x" != reply.text


async def test_a_slow_model_is_cut_off(loader: AsyncMock, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(assistant_http, "CALL_TIMEOUT_SECONDS", 0.05)
    ai = FakeProvider()

    async def slow(_: object) -> None:
        await asyncio.sleep(5)

    ai.brief.side_effect = slow
    async with client_for(ai) as client:
        reply = await client.post(PATH, json=BODY)
    assert reply.status_code == 503


async def test_each_actor_is_rate_limited_independently(loader: AsyncMock) -> None:
    ai, limiter = FakeProvider(), BriefLimiter(limit=2, window=600)
    other = session_provider()
    other.verify.return_value = verified(actor_ref="viewer-two")
    async with client_for(ai, limiter=limiter) as client:
        codes = [(await client.post(PATH, json=BODY)).status_code for _ in range(3)]
    async with client_for(ai, other, limiter) as client:
        second = (await client.post(PATH, json=BODY)).status_code
    assert codes == [200, 200, 429] and second == 200
    assert ai.brief.await_count == 3


async def test_a_rate_limited_request_does_not_read_the_record(loader: AsyncMock) -> None:
    ai, limiter = FakeProvider(), BriefLimiter(limit=1, window=600)
    async with client_for(ai, limiter=limiter) as client:
        await client.post(PATH, json=BODY)
        loader.reset_mock()
        reply = await client.post(PATH, json=BODY)
    assert reply.status_code == 429
    loader.assert_not_awaited()


def test_limiter_window_slides_and_forgets_idle_actors() -> None:
    limiter = BriefLimiter(limit=2, window=10, tracked=3)
    assert [limiter.allow("a", 0), limiter.allow("a", 1), limiter.allow("a", 2)] == [
        True,
        True,
        False,
    ]
    assert limiter.allow("a", 10.0) is True
    assert limiter.allow("a", 11.0) is True
    assert limiter.allow("a", 11.5) is False
    for index in range(5):
        limiter.allow(f"idle-{index}", 12.0)
    assert limiter.allow("late", 100.0) is True
    assert set(limiter._hits) == {"late"}


def test_the_route_is_registered_exactly_once() -> None:
    app = FastAPI()
    app.include_router(create_assistant_router(None, None))
    schema = app.openapi()["paths"]
    assert list(schema) == ["/api/workspaces/{workspace_id}/personas/assistant/brief"]
    assert list(schema[PATH.replace(str(WORKSPACE), "{workspace_id}")]) == ["post"]
