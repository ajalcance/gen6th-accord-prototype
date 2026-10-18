"""Trusted injected comparison provider; no text instructions or external URL fetches."""

from dataclasses import dataclass
from typing import Protocol

from accord.personas.face_contracts import FaceBox
from accord.personas.investigation_contracts import ProviderFindings
from accord.personas.similarity_query import SimilarityRuntime


@dataclass(frozen=True)
class ComparisonInput:
    query_image: bytes
    reference_image: bytes
    query_face: FaceBox
    reference_face: FaceBox


@dataclass(frozen=True)
class ComparisonOutput:
    model: str
    revision: str
    findings: ProviderFindings


class InvestigationProvider(Protocol):
    async def compare(self, evidence: ComparisonInput) -> ComparisonOutput: ...


@dataclass(frozen=True)
class InvestigationRuntime:
    similarity: SimilarityRuntime
    provider: InvestigationProvider | None = None


async def compare(provider: InvestigationProvider, evidence: ComparisonInput) -> ComparisonOutput:
    try:
        return await provider.compare(evidence)
    except Exception as exc:
        raise RuntimeError("grounded comparison unavailable") from exc
