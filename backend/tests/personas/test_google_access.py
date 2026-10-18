"""Actual bounded HTTP metadata contract; no metadata endpoint is contacted."""

import httpx
import pytest

from accord.personas.google_access import METADATA_ENDPOINT, CloudRunAccess


@pytest.mark.asyncio
async def test_metadata_identity_is_cached_and_never_discovered_from_local_credentials() -> None:
    calls: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200,
            headers={"Metadata-Flavor": "Google"},
            json={
                "access_token": "synthetic-workload-handle",
                "token_type": "Bearer",
                "expires_in": 300,
            },
        )

    access = CloudRunAccess(httpx.MockTransport(respond))
    assert await access.token() == await access.token() == "synthetic-workload-handle"
    assert len(calls) == 1 and str(calls[0].url) == METADATA_ENDPOINT
    assert calls[0].headers["Metadata-Flavor"] == "Google"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "changes",
    [
        {"expires_in": True},
        {"expires_in": 59},
        {"access_token": "invalid handle"},
        {"token_type": "other"},
    ],
)
async def test_invalid_metadata_never_establishes_workload_access(
    changes: dict[str, object],
) -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            headers={"Metadata-Flavor": "Google"},
            json={
                "access_token": "synthetic-handle",
                "token_type": "Bearer",
                "expires_in": 300,
                **changes,
            },
        )
    )
    with pytest.raises(RuntimeError):
        await CloudRunAccess(transport).token()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(302, headers={"Location": "https://arbitrary.test"}),
        httpx.Response(200, json={}),
        httpx.Response(200, headers={"Metadata-Flavor": "Google"}, content=b"x" * 8193),
    ],
)
async def test_metadata_redirect_header_loss_and_oversize_fail_closed(
    response: httpx.Response,
) -> None:
    with pytest.raises(RuntimeError):
        await CloudRunAccess(httpx.MockTransport(lambda _: response)).token()
