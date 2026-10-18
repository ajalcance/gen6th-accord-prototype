"""Thin OIDC routes; tokens stay encrypted on the server and never appear in JSON responses."""

import asyncio
from typing import cast

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from accord.auth.browser_oidc import SESSION_COOKIE, STATE_COOKIE, BrowserOidc, csrf
from accord.cache.redis import get_redis
from accord.telemetry.emitter import Telemetry
from accord.telemetry.envelope import client_ip

PRIVATE_HEADERS = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
    "Referrer-Policy": "no-referrer",
}
router = APIRouter(prefix="/api/auth", tags=["workspace sessions"])


def browser(request: Request) -> BrowserOidc:
    provider = cast(BrowserOidc | None, getattr(request.app.state, "session_verifier", None))
    if provider is None:
        raise HTTPException(503, "Zynth connection is not configured", headers=PRIVATE_HEADERS)
    return provider


async def observed(
    request: Request, operation: str, actor: str | None = None, outcome: str = "success"
) -> None:
    await Telemetry(get_redis(), client_ip(request)).emit(
        category="auth",
        action="auth.session_observed",
        outcome=outcome,
        actor_type="user" if actor else "system",
        actor_id=actor,
        metadata={"operation": operation},
    )


def private(response: Response) -> Response:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@router.get("/login")
async def login(request: Request) -> Response:
    provider = browser(request)
    try:
        async with asyncio.timeout(3):
            location, state = await provider.login()
        response = RedirectResponse(location, status_code=303)
        response.set_cookie(
            STATE_COOKIE,
            state,
            max_age=300,
            path="/api/auth/callback",
            httponly=True,
            secure=provider.origin.startswith("https:"),
            samesite="lax",
        )
        await observed(request, "login_started")
        return private(response)
    except Exception as exc:
        await observed(request, "login_unavailable", outcome="failure")
        raise HTTPException(503, "sign-in could not be started", headers=PRIVATE_HEADERS) from exc


@router.get("/callback")
async def callback(request: Request) -> Response:
    provider = browser(request)
    response: Response
    try:
        async with asyncio.timeout(8):
            handle, seconds, verified = await provider.callback(request)
        response = RedirectResponse(provider.origin + "/", status_code=303)
        response.set_cookie(
            SESSION_COOKIE,
            handle,
            max_age=seconds,
            path="/api",
            httponly=True,
            secure=provider.origin.startswith("https:"),
            samesite="lax",
        )
        await observed(request, "login_completed", verified.actor_ref)
    except Exception:
        await observed(request, "login_rejected", outcome="denied")
        response = JSONResponse({"error": "sign-in could not be verified"}, status_code=401)
    response.delete_cookie(STATE_COOKIE, path="/api/auth/callback")
    return private(response)


@router.get("/session")
async def session(request: Request) -> Response:
    provider = browser(request)
    try:
        async with asyncio.timeout(3):
            verified = await provider.verify(request)
        if verified is None:
            await observed(request, "session_denied", outcome="denied")
            return private(JSONResponse({"error": "sign-in required"}, status_code=401))
        await observed(request, "session_verified", verified.actor_ref)
        return private(
            JSONResponse(
                {
                    "workspace_id": str(verified.workspace_id),
                    "session_key": verified.session_id,
                    "workspace_label": "Workspace",
                }
            )
        )
    except Exception:
        await observed(request, "session_unavailable", outcome="failure")
        return private(JSONResponse({"error": "session verification unavailable"}, status_code=503))


@router.post("/logout")
async def logout(request: Request) -> Response:
    provider = browser(request)
    try:
        csrf(request, provider.origin)
    except Exception as exc:
        raise HTTPException(403, "same-origin logout required", headers=PRIVATE_HEADERS) from exc
    handle = request.cookies.get(SESSION_COOKIE, "")
    response = JSONResponse({"signed_out": True})
    response.delete_cookie(SESSION_COOKIE, path="/api")
    try:
        async with asyncio.timeout(3):
            if handle and len(handle) <= 128:
                await provider.store.remove(handle)
        await observed(request, "logout_completed")
    except Exception:
        response = JSONResponse({"error": "server sign-out unavailable"}, status_code=503)
        response.delete_cookie(SESSION_COOKIE, path="/api")
    return private(response)
