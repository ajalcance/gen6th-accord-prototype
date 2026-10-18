"""Google wire contracts via MockTransport; no real provider request or identity measurement."""

import json

import httpx
import pytest

from accord.personas.face_google import GoogleFaceDetector, GoogleImageEncoder, GoogleTransport


class FixtureAccess:
    async def token(self) -> str:
        return "synthetic-authorization"


@pytest.mark.asyncio
async def test_google_detection_discards_emotion_and_uses_only_pixel_input() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert request.url == "https://vision.googleapis.com/v1/images:annotate"
        assert payload["requests"][0]["features"] == [{"type": "FACE_DETECTION", "maxResults": 10}]
        return httpx.Response(
            200,
            json={
                "responses": [
                    {
                        "faceAnnotations": [
                            {
                                "fdBoundingPoly": {
                                    "vertices": [{}, {"x": 80}, {"x": 80, "y": 80}, {"y": 80}]
                                },
                                "detectionConfidence": 0.9,
                                "joyLikelihood": "LIKELY",
                            }
                        ]
                    }
                ]
            },
        )

    adapter = GoogleFaceDetector(
        "accord-test", GoogleTransport(FixtureAccess(), httpx.MockTransport(respond))
    )
    result = await adapter.detect(b"synthetic-pixels", 200, 100)
    assert result.faces[0].width == 80 and "joy" not in result.faces[0].model_dump_json()


@pytest.mark.asyncio
async def test_google_embedding_dimensions_and_alias_provenance() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["parameters"] == {"dimension": 128}
        assert "/locations/asia-southeast1/" in str(request.url)
        return httpx.Response(200, json={"predictions": [{"imageEmbedding": [0.5] * 128}]})

    adapter = GoogleImageEncoder(
        "accord-test",
        "asia-southeast1",
        128,
        GoogleTransport(FixtureAccess(), httpx.MockTransport(respond)),
    )
    result = await adapter.encode(b"synthetic-pixels")
    assert len(result.values) == 128 and result.revision == "publisher-alias-unresolved"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"responses": [{"error": {"code": 9}}]},
        {"responses": []},
        {"responses": [{"faceAnnotations": [{}]}]},
    ],
)
async def test_detector_malformed_and_error_results_fail_closed(payload: dict[str, object]) -> None:
    adapter = GoogleFaceDetector(
        "accord-test",
        GoogleTransport(
            FixtureAccess(), httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
        ),
    )
    with pytest.raises((RuntimeError, ValueError)):
        await adapter.detect(b"synthetic", 200, 100)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,body", [(302, b"redirect"), (503, b"provider-sensitive-detail"), (200, b"x" * 262145)]
)
async def test_transport_rejects_redirect_errors_and_large_responses(
    status: int, body: bytes
) -> None:
    transport = GoogleTransport(
        FixtureAccess(), httpx.MockTransport(lambda _: httpx.Response(status, content=body))
    )
    with pytest.raises(RuntimeError) as caught:
        await transport.post("https://vision.googleapis.com/v1/images:annotate", "accord-test", {})
    assert "provider-sensitive-detail" not in str(caught.value)
