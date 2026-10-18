"""Synthetic vector examples test evaluator arithmetic, never synthetic-face model accuracy."""

import pytest
from pydantic import ValidationError

from accord.personas.face_benchmark import BenchmarkManifest, BenchmarkRun, evaluate


def manifest_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for split in ("development", "calibration", "test"):
        for suffix, role, case in (
            ("ref", "reference", "regenerated"),
            ("regen", "query", "regenerated"),
            ("look", "query", "lookalike"),
            ("absent", "query", "absent"),
        ):
            rows.append(
                {
                    "id": f"{split}-{suffix}",
                    "family": f"{split}-{'absent' if suffix == 'absent' else 'actor'}",
                    "split": split,
                    "role": role,
                    "case": case,
                    "sha256": f"{len(rows)+1:064x}",
                    "permission_record": "synthetic evaluator fixture only",
                    "synthetic": True,
                }
            )
    return rows


def test_held_out_metrics_include_failed_queries_and_absent_family() -> None:
    manifest = BenchmarkManifest.model_validate({"assets": manifest_rows()})
    observations = [
        {
            "asset_id": a.id,
            "sha256": a.sha256,
            "vector": (
                None if a.id == "test-look" else ([0.0, 1.0] if a.case == "absent" else [1.0, 0.0])
            ),
            "latency_ms": 10,
            "cost_usd": 0.01,
        }
        for a in manifest.assets
    ]
    run = BenchmarkRun.model_validate(
        {
            "model": "synthetic",
            "revision": "fixture-v1",
            "role": "face",
            "observations": observations,
        }
    )
    report = evaluate(manifest, run)
    assert report["recall"] == {"1": 0.5, "3": 0.5, "5": 0.5}
    assert report["failed_queries"] == 1 and report["absent_false_match_rate"] == 0
    assert report["test_queries"] == 3 and report["strong_false_matches"] == 0


@pytest.mark.parametrize("change", ["family", "duplicate", "permission", "not_synthetic"])
def test_invalid_benchmark_provenance_and_family_leak_rejected(change: str) -> None:
    rows = manifest_rows()
    if change == "family":
        rows[4]["family"] = rows[0]["family"]
    elif change == "duplicate":
        rows[4]["sha256"] = rows[0]["sha256"]
    elif change == "permission":
        rows[0]["permission_record"] = ""
    else:
        rows[0]["synthetic"] = False
    with pytest.raises(ValidationError):
        BenchmarkManifest.model_validate({"assets": rows})
