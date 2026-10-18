"""Bounded Google REST candidate adapters; authorization is supplied by the reviewed runtime."""

import base64
import json
import re
from typing import Protocol, cast

import httpx

from accord.personas.face_contracts import FaceBox
from accord.personas.face_providers import Detection, Embedding, normalized


class GoogleAccess(Protocol):
    async def token(self) -> str: ...


class GoogleTransport:
    def __init__(
        self, access: GoogleAccess, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self.access, self.transport = access, transport

    async def post(
        self, url: str, project: str, payload: dict[str, object], *, allow_existing: bool = False
    ) -> dict[str, object]:
        token = await self.access.token()
        if not token or any(c.isspace() for c in token):
            raise RuntimeError("Google workload authorization unavailable")
        headers = {"Authorization": f"Bearer {token}", "x-goog-user-project": project}
        async with httpx.AsyncClient(
            transport=self.transport, trust_env=False, follow_redirects=False, timeout=20
        ) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200 and not (
                    allow_existing and response.status_code == 409
                ):
                    raise RuntimeError("Google processing unavailable")
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > 256 * 1024:
                        raise RuntimeError("Google response exceeded the bound")
        result = json.loads(body)
        if not isinstance(result, dict):
            raise RuntimeError("invalid Google response")
        if response.status_code == 409:
            error = result.get("error")
            if not isinstance(error, dict) or error.get("status") != "ALREADY_EXISTS":
                raise RuntimeError("task creation unavailable")
            return {"already_exists": True}
        return cast(dict[str, object], result)


def project_id(value: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", value):
        raise ValueError("invalid Google project")
    return value


def parse_face(value: object, index: int, width: int, height: int) -> FaceBox:
    if not isinstance(value, dict):
        raise RuntimeError("invalid detector face")
    polygon = value.get("fdBoundingPoly")
    if not isinstance(polygon, dict) or not isinstance(polygon.get("vertices"), list):
        raise RuntimeError("detector box unavailable")
    vertices = polygon["vertices"]
    if len(vertices) != 4 or any(not isinstance(v, dict) for v in vertices):
        raise RuntimeError("invalid detector vertices")
    xs, ys = [v.get("x", 0) for v in vertices], [v.get("y", 0) for v in vertices]
    if any(type(v) is not int for v in xs + ys):
        raise RuntimeError("invalid detector coordinates")
    x, y, right, bottom = min(xs), min(ys), max(xs), max(ys)
    if x < 0 or y < 0 or right > width or bottom > height:
        raise RuntimeError("detector box outside analysis image")
    return FaceBox.model_validate(
        {
            "index": index,
            "x": x,
            "y": y,
            "width": right - x,
            "height": bottom - y,
            "confidence": value.get("detectionConfidence"),
            "yaw": value.get("panAngle", 0.0),
            "pitch": value.get("tiltAngle", 0.0),
            "blur": value.get("blurredLikelihood", "UNKNOWN"),
        }
    )


class GoogleFaceDetector:
    def __init__(self, project: str, transport: GoogleTransport) -> None:
        self.project, self.transport = project_id(project), transport

    async def detect(self, pixels: bytes, width: int, height: int) -> Detection:
        response = await self.transport.post(
            "https://vision.googleapis.com/v1/images:annotate",
            self.project,
            {
                "requests": [
                    {
                        "image": {"content": base64.b64encode(pixels).decode()},
                        "features": [{"type": "FACE_DETECTION", "maxResults": 10}],
                    }
                ]
            },
        )
        responses = response.get("responses")
        if (
            not isinstance(responses, list)
            or len(responses) != 1
            or not isinstance(responses[0], dict)
        ):
            raise RuntimeError("invalid detector response")
        row = responses[0]
        faces = row.get("faceAnnotations", [])
        if "error" in row or not isinstance(faces, list) or len(faces) > 10:
            raise RuntimeError("detector unavailable")
        return Detection(
            "google-vision-FACE_DETECTION-v1-unpinned",
            tuple(parse_face(f, i, width, height) for i, f in enumerate(faces)),
        )


class GoogleImageEncoder:
    def __init__(
        self, project: str, region: str, dimensions: int, transport: GoogleTransport
    ) -> None:
        if dimensions not in {128, 256, 512, 1408} or not re.fullmatch(
            r"[a-z]+-[a-z]+[0-9]", region
        ):
            raise ValueError("invalid Google embedding configuration")
        self.project, self.region = project_id(project), region
        self.dimensions, self.transport = dimensions, transport

    async def encode(self, pixels: bytes) -> Embedding:
        model = "multimodalembedding@001"
        url = (
            f"https://{self.region}-aiplatform.googleapis.com/v1/projects/{self.project}/"
            f"locations/{self.region}/publishers/google/models/{model}:predict"
        )
        response = await self.transport.post(
            url,
            self.project,
            {
                "instances": [
                    {
                        "image": {
                            "bytesBase64Encoded": base64.b64encode(pixels).decode(),
                            "mimeType": "image/png",
                        }
                    }
                ],
                "parameters": {"dimension": self.dimensions},
            },
        )
        predictions = response.get("predictions")
        if (
            not isinstance(predictions, list)
            or len(predictions) != 1
            or not isinstance(predictions[0], dict)
        ):
            raise RuntimeError("invalid embedding response")
        values = predictions[0].get("imageEmbedding")
        if not isinstance(values, list) or len(values) != self.dimensions:
            raise RuntimeError("invalid embedding dimensions")
        revision = response.get("deployedModelId")
        if revision is not None and (not isinstance(revision, str) or not revision):
            raise RuntimeError("invalid provider revision")
        result = Embedding(
            f"google/{self.region}/{model}", revision or "publisher-alias-unresolved", tuple(values)
        )
        normalized(result)
        return result
