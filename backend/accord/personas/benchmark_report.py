"""Typed offline arithmetic evidence; supplied vectors cannot certify a provider or rights."""

import hashlib
import json
import math
from typing import Literal

from pydantic import BaseModel, ConfigDict

from accord.personas.face_benchmark import (
    BenchmarkAsset,
    BenchmarkManifest,
    BenchmarkRun,
    rank_query,
)


class Stratum(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    total: int
    scored: int
    failed: int
    abstained: int
    strong_false_matches: int
    recall: dict[str, float] | None
    false_match_rate_scored: float | None


class BenchmarkReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["accord-benchmark-v1"] = "accord-benchmark-v1"
    evidence: Literal["supplied_observations"] = "supplied_observations"
    corpus_binding: Literal["unchecked", "bytes_checked"] = "unchecked"
    manifest_sha256: str
    observations_sha256: str
    model: str
    revision: str
    role: Literal["face", "whole_image"]
    threshold: float
    threshold_source: Literal["calibration_impostor_max"] = "calibration_impostor_max"
    test_queries: int
    known_queries: int
    absent_queries: int
    failed_queries: int
    failed_references: int
    recall: dict[str, float]
    strong_false_matches: int
    absent_false_match_rate: float
    strata: dict[str, Stratum]
    latency_ms_p50: float
    latency_ms_p95: float
    latency_ms_max: float
    cost_usd_total: float | None
    cost_usd_known: float
    cost_unknown_observations: int
    acceptance: Literal["human_review_required"] = "human_review_required"


def fingerprint(value: BaseModel) -> str:
    data = json.dumps(value.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode()).hexdigest()


def recall(
    rows: list[BenchmarkAsset], ranks: dict[str, list[tuple[float, str]]]
) -> dict[str, float]:
    return {
        str(k): sum(a.family in [f for _, f in ranks[a.id][:k]] for a in rows) / len(rows)
        for k in (1, 3, 5)
    }


def stratum(
    rows: list[BenchmarkAsset],
    ranks: dict[str, list[tuple[float, str]]],
    vectors: dict[str, tuple[float, ...] | None],
    threshold: float,
) -> Stratum:
    scored = [a for a in rows if ranks[a.id]]
    strong = [a for a in scored if ranks[a.id][0][0] >= threshold]
    wrong = sum(ranks[a.id][0][1] != a.family for a in strong)
    return Stratum(
        total=len(rows),
        scored=len(scored),
        failed=sum(vectors[a.id] is None for a in rows),
        abstained=len(scored) - len(strong),
        strong_false_matches=wrong,
        recall=recall(rows, ranks) if rows[0].case != "absent" else None,
        false_match_rate_scored=wrong / len(scored) if scored else None,
    )


def percentile(values: list[float], fraction: float) -> float:
    """Nearest-rank latency across all supplied observations, including failed attempts."""
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]


def build_report(
    manifest: BenchmarkManifest,
    run: BenchmarkRun,
    vectors: dict[str, tuple[float, ...] | None],
    threshold: float,
) -> BenchmarkReport:
    queries = [a for a in manifest.assets if a.split == "test" and a.role == "query"]
    known = [a for a in queries if a.case != "absent"]
    ranks = {a.id: rank_query(a, manifest.assets, vectors) for a in queries}
    strata = {
        case: stratum([a for a in queries if a.case == case], ranks, vectors, threshold)
        for case in ("regenerated", "lookalike", "absent")
    }
    latency = [o.latency_ms for o in run.observations]
    unknown = sum(o.cost_usd is None for o in run.observations)
    cost = math.fsum(o.cost_usd for o in run.observations if o.cost_usd is not None)
    if not math.isfinite(cost):
        raise ValueError("benchmark cost sum must be finite")
    return BenchmarkReport(
        manifest_sha256=fingerprint(manifest),
        observations_sha256=fingerprint(run),
        model=run.model,
        revision=run.revision,
        role=run.role,
        threshold=threshold,
        test_queries=len(queries),
        known_queries=len(known),
        absent_queries=strata["absent"].total,
        failed_queries=sum(s.failed for s in strata.values()),
        failed_references=sum(
            vectors[a.id] is None for a in manifest.assets if a.role == "reference"
        ),
        recall=recall(known, ranks),
        strong_false_matches=sum(s.strong_false_matches for s in strata.values()),
        absent_false_match_rate=strata["absent"].strong_false_matches / strata["absent"].total,
        strata=strata,
        latency_ms_p50=percentile(latency, 0.5),
        latency_ms_p95=percentile(latency, 0.95),
        latency_ms_max=max(latency),
        cost_usd_total=None if unknown else cost,
        cost_usd_known=cost,
        cost_unknown_observations=unknown,
    )
