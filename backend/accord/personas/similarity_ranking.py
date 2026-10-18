"""Exact face cosine, maximum per persona, calibrated threshold and ambiguity abstention."""

import asyncio

from accord.personas.face_providers import quality_reasons
from accord.personas.face_storage import load_generation
from accord.personas.face_vectors import Vectors, cosine
from accord.personas.repository import snapshot
from accord.personas.similarity_contracts import SimilarityCandidate
from accord.personas.similarity_policy import CalibrationPolicy
from accord.personas.similarity_query import SimilarityRuntime
from accord.personas.similarity_repository import ReferenceRow


async def score_references(
    runtime: SimilarityRuntime, rows: list[ReferenceRow], query: Vectors, policy: CalibrationPolicy
) -> list[SimilarityCandidate]:
    bound = asyncio.Semaphore(8)

    async def score(row: ReferenceRow) -> SimilarityCandidate | None:
        async with bound:
            version, capture, generation = row
            if generation is None:
                return None
            result, vectors = await load_generation(generation, runtime.wrapper)
            if (
                result.source_sha256 != capture.sha256
                or result.width != capture.width
                or result.height != capture.height
            ):
                raise RuntimeError("reference capture integrity unavailable")
            if not policy.reference_matches(result, capture.decoder_version, capture.recipe):
                return None
            if result.selected is None or quality_reasons(result.faces[result.selected]):
                return None
            return SimilarityCandidate(
                version=snapshot(version),
                portrait_id=capture.portrait_id,
                generation_id=generation.id,
                face=result.faces[result.selected],
                face_cosine=cosine(query[0], vectors[0]),
                whole_cosine=cosine(query[1], vectors[1]),
                compatible_references=1,
            )

    return [
        result
        for result in await asyncio.gather(*(score(row) for row in rows))
        if result is not None
    ]


def ranked_personas(references: list[SimilarityCandidate]) -> list[SimilarityCandidate]:
    ordered = sorted(
        references,
        key=lambda c: (
            -c.face_cosine,
            -c.version.revision,
            str(c.version.persona_id),
            str(c.version.version_id),
            str(c.portrait_id),
            str(c.generation_id),
        ),
    )
    counts: dict[str, int] = {}
    best: dict[str, SimilarityCandidate] = {}
    for candidate in ordered:
        identity = str(candidate.version.persona_id)
        counts[identity] = counts.get(identity, 0) + 1
        best.setdefault(identity, candidate)
    return [
        candidate.model_copy(update={"compatible_references": counts[identity]})
        for identity, candidate in best.items()
    ]


def confident_candidates(
    references: list[SimilarityCandidate], policy: CalibrationPolicy
) -> tuple[tuple[SimilarityCandidate, ...], bool]:
    ranked = ranked_personas(references)
    if not ranked or ranked[0].face_cosine < policy.threshold:
        return (), False
    if len(ranked) > 1 and ranked[0].face_cosine - ranked[1].face_cosine < policy.margin:
        return (), False
    qualifying = [c for c in ranked if c.face_cosine >= policy.threshold]
    return tuple(qualifying[:5]), len(qualifying) > 5
