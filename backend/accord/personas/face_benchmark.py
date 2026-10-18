"""Offline held-out evaluation of permitted assets and source-bound encoder observations.

This measures supplied observations; it does not generate faces, call providers or select a model.
"""

import math
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from accord.personas.face_providers import Embedding, normalized


class BenchmarkAsset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(min_length=1, max_length=80)
    family: str = Field(min_length=1, max_length=80)
    split: Literal["development", "calibration", "test"]
    role: Literal["reference", "query"]
    case: Literal["regenerated", "lookalike", "absent"]
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    permission_record: str = Field(min_length=1, max_length=200)
    synthetic: Literal[True]
    relative_path: str | None = Field(default=None, min_length=1, max_length=240)


class BenchmarkManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    assets: tuple[BenchmarkAsset, ...] = Field(min_length=6, max_length=10000)

    @model_validator(mode="after")
    def held_out(self) -> Self:
        if len({a.id for a in self.assets}) != len(self.assets):
            raise ValueError("duplicate asset identity")
        families: dict[str, set[str]] = {}
        for a in self.assets:
            families.setdefault(a.family, set()).add(a.split)
        if any(len(splits) != 1 for splits in families.values()):
            raise ValueError("performer family leaks between splits")
        if len({a.sha256 for a in self.assets}) != len(self.assets):
            raise ValueError("duplicate image leaks into the benchmark")
        for split in ("development", "calibration", "test"):
            rows = [a for a in self.assets if a.split == split]
            refs = {a.family for a in rows if a.role == "reference"}
            queries = [a for a in rows if a.role == "query"]
            if not refs or not queries:
                raise ValueError("each split requires references and queries")
            if len(queries) * sum(a.role == "reference" for a in rows) > 2_000_000:
                raise ValueError("benchmark comparison budget exceeded")
            if any((a.family in refs) == (a.case == "absent") for a in queries):
                raise ValueError("query presence does not match the declared case")
        test_cases = {a.case for a in self.assets if a.split == "test" and a.role == "query"}
        if test_cases != {"regenerated", "lookalike", "absent"}:
            raise ValueError("held-out test requires regenerated, lookalike and absent cases")
        return self


class BenchmarkObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    asset_id: str = Field(min_length=1, max_length=80)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    vector: tuple[float, ...] | None = Field(max_length=1408)
    latency_ms: float = Field(ge=0, allow_inf_nan=False)
    cost_usd: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @field_validator("vector", mode="before")
    @classmethod
    def numeric_vector(cls, value: object) -> object:
        if value is not None and (
            not isinstance(value, (list, tuple)) or any(type(v) not in (int, float) for v in value)
        ):
            raise ValueError("benchmark vectors require numeric values, excluding booleans")
        return value

    @field_validator("latency_ms", "cost_usd", mode="before")
    @classmethod
    def numeric_measurement(cls, value: object) -> object:
        if value is not None and type(value) not in (int, float):
            raise ValueError("benchmark measurements require numeric values")
        return value


class BenchmarkRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    model: str = Field(min_length=1, max_length=160)
    revision: str = Field(min_length=1, max_length=160)
    role: Literal["face", "whole_image"]
    observations: tuple[BenchmarkObservation, ...] = Field(min_length=1, max_length=10000)


def rank_query(
    query: BenchmarkAsset,
    assets: tuple[BenchmarkAsset, ...],
    vectors: dict[str, tuple[float, ...] | None],
) -> list[tuple[float, str]]:
    q = vectors[query.id]
    if q is None:
        return []
    scores: dict[str, float] = {}
    for ref in assets:
        r = vectors[ref.id]
        if ref.split == query.split and ref.role == "reference" and r is not None:
            score = max(-1.0, min(1.0, sum(a * b for a, b in zip(q, r, strict=True))))
            scores[ref.family] = max(score, scores.get(ref.family, -math.inf))
    return sorted(((s, f) for f, s in scores.items()), key=lambda item: (-item[0], item[1]))


def validate_observations(
    manifest: BenchmarkManifest, run: BenchmarkRun
) -> dict[str, tuple[float, ...] | None]:
    observed = {o.asset_id: o for o in run.observations}
    if len(observed) != len(run.observations) or set(observed) != {a.id for a in manifest.assets}:
        raise ValueError("observations must cover exactly the permitted manifest")
    vectors: dict[str, tuple[float, ...] | None] = {}
    for asset in manifest.assets:
        row = observed[asset.id]
        if row.sha256 != asset.sha256:
            raise ValueError("observation does not bind to its permitted image")
        vectors[asset.id] = (
            normalized(Embedding(run.model, run.revision, row.vector))
            if row.vector is not None
            else None
        )
    dimensions = {len(v) for v in vectors.values() if v is not None}
    if len(dimensions) != 1:
        raise ValueError("nonempty compatible dimensions required")
    return vectors


def calibration_threshold(
    manifest: BenchmarkManifest, vectors: dict[str, tuple[float, ...] | None]
) -> float:
    """Abstain above the largest calibration impostor score; never fit on test families."""
    scores: list[float] = []
    for q in manifest.assets:
        if q.split == "calibration" and q.role == "query":
            scores.extend(
                s for s, family in rank_query(q, manifest.assets, vectors) if family != q.family
            )
    if not scores:
        raise ValueError("calibration requires measured impostor comparisons")
    return math.nextafter(max(scores), math.inf)


def evaluate(manifest: BenchmarkManifest, run: BenchmarkRun) -> dict[str, object]:
    from accord.personas.benchmark_report import build_report

    vectors = validate_observations(manifest, run)
    threshold = calibration_threshold(manifest, vectors)
    return build_report(manifest, run, vectors, threshold).model_dump(mode="json")
