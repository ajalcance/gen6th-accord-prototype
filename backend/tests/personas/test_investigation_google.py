"""Google wire contracts via MockTransport; no cloud activation or real model acceptance."""

import json

import httpx
import pytest

from accord.personas.face_google import GoogleTransport
from accord.personas.investigation_google import GoogleInvestigationProvider, parse_response
from accord.personas.investigation_provider import ComparisonInput
from personas.test_face_google import FixtureAccess
from personas.test_face_processing import face, image_bytes


def response(findings: object = None, finish: str = "STOP") -> dict[str, object]:
    return {
        "modelVersion": "gemini-synthetic-observed-revision",
        "candidates": [
            {
                "finishReason": finish,
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(
                                findings
                                or {
                                    "state": "observations",
                                    "observations": [
                                        {
                                            "label": "pose_differs",
                                            "citations": ["query_image", "approved_reference"],
                                        }
                                    ],
                                }
                            )
                        }
                    ]
                },
            }
        ],
    }


@pytest.mark.asyncio
async def test_vertex_schema_images_and_observed_revision() -> None:
    def wire(request: httpx.Request) -> httpx.Response:
        data = json.loads(request.content)
        assert request.url.path.endswith("gemini-2.5-flash:generateContent")
        assert "tools" not in data and "fileData" not in request.content.decode()
        assert data["generationConfig"]["responseMimeType"] == "application/json"
        assert len([p for p in data["contents"][0]["parts"] if "inlineData" in p]) == 2
        assert "ownership" in data["systemInstruction"]["parts"][0]["text"]
        return httpx.Response(200, json=response())

    provider = GoogleInvestigationProvider(
        "accord-test",
        "asia-southeast1",
        "gemini-2.5-flash",
        GoogleTransport(FixtureAccess(), httpx.MockTransport(wire)),
    )
    output = await provider.compare(ComparisonInput(image_bytes(), image_bytes(), face(), face()))
    assert output.revision == "gemini-synthetic-observed-revision"
    assert output.findings.observations[0].label == "pose_differs"


@pytest.mark.parametrize(
    "payload",
    [
        response(finish="SAFETY"),
        response(finish="MAX_TOKENS"),
        response(
            {
                "state": "observations",
                "observations": [
                    {
                        "label": "copying_confirmed",
                        "citations": ["query_image", "approved_reference"],
                    }
                ],
            }
        ),
        {**response(), "modelVersion": None},
        {"candidates": []},
        {
            "modelVersion": "fixture",
            "candidates": [{"finishReason": "STOP", "content": {"parts": [{"functionCall": {}}]}}],
        },
    ],
)
def test_refusal_incomplete_malformed_and_unsupported_output_unavailable(
    payload: dict[str, object],
) -> None:
    with pytest.raises(RuntimeError):
        parse_response(payload, "synthetic")
