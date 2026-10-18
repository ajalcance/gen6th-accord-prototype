"""Offline report provenance and failure arithmetic, using explicitly synthetic vectors."""

import hashlib
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from accord.personas import benchmark_corpus
from accord.personas.benchmark_corpus import check_corpus
from accord.personas.face_benchmark import BenchmarkManifest, BenchmarkRun, evaluate
from accord.personas.face_benchmark_runner import main, read_json
from personas.test_face_benchmark import manifest_rows


def inputs() -> tuple[BenchmarkManifest, BenchmarkRun]:
    manifest = BenchmarkManifest.model_validate({"assets": manifest_rows()})
    run = BenchmarkRun.model_validate(
        {
            "model": "fixture",
            "revision": "not-real-model-evidence",
            "role": "face",
            "observations": [
                {
                    "asset_id": a.id,
                    "sha256": a.sha256,
                    "vector": [0, 1] if a.case == "absent" else [1, 0],
                    "latency_ms": i + 1,
                    "cost_usd": None if i == 0 else 0.01,
                }
                for i, a in enumerate(manifest.assets)
            ],
        }
    )
    return manifest, run


def test_report_cost_missing_is_unknown_and_fingerprints_bind_inputs() -> None:
    manifest, run = inputs()
    report = evaluate(manifest, run)
    assert report["cost_usd_total"] is None and report["cost_unknown_observations"] == 1
    assert report["cost_usd_known"] == pytest.approx(0.11)
    assert report["latency_ms_p50"] == 6 and report["latency_ms_p95"] == 12
    assert report["corpus_binding"] == "unchecked"
    assert report["evidence"] == "supplied_observations"
    changed = run.model_copy(update={"revision": "different"})
    assert evaluate(manifest, changed)["observations_sha256"] != report["observations_sha256"]
    assert evaluate(manifest, changed)["manifest_sha256"] == report["manifest_sha256"]


def test_failed_absent_query_cannot_be_counted_as_scored_rejection() -> None:
    manifest, run = inputs()
    rows = tuple(
        o.model_copy(update={"vector": None}) if o.asset_id == "test-absent" else o
        for o in run.observations
    )
    result = evaluate(manifest, run.model_copy(update={"observations": rows}))
    strata = result["strata"]
    assert isinstance(strata, dict)
    assert strata["absent"] == {
        "total": 1,
        "scored": 0,
        "failed": 1,
        "abstained": 0,
        "strong_false_matches": 0,
        "recall": None,
        "false_match_rate_scored": None,
    }


def test_calibration_threshold_is_not_fit_to_test_vectors() -> None:
    manifest, run = inputs()
    changed = tuple(
        o.model_copy(update={"vector": (1.0, 1.0)}) if o.asset_id.startswith("test-") else o
        for o in run.observations
    )
    assert (
        evaluate(manifest, run)["threshold"]
        == evaluate(manifest, run.model_copy(update={"observations": changed}))["threshold"]
    )


@pytest.mark.parametrize(
    "field,value", [("latency_ms", True), ("cost_usd", "0"), ("cost_usd", float("inf"))]
)
def test_measurements_are_finite_numbers(field: str, value: object) -> None:
    _, run = inputs()
    data = run.model_dump(mode="json")
    data["observations"][0][field] = value
    with pytest.raises(ValidationError):
        BenchmarkRun.model_validate(data)


def corpus(tmp_path: Path) -> BenchmarkManifest:
    rows = manifest_rows()
    for i, row in enumerate(rows):
        data = f"private synthetic fixture {i}".encode()
        name = f"asset-{i}.bin"
        (tmp_path / name).write_bytes(data)
        row.update(relative_path=name, sha256=hashlib.sha256(data).hexdigest())
    return BenchmarkManifest.model_validate({"assets": rows})


def test_corpus_checks_every_digest(tmp_path: Path) -> None:
    manifest = corpus(tmp_path)
    check_corpus(manifest, tmp_path)
    (tmp_path / "asset-2.bin").write_bytes(b"changed")
    with pytest.raises(ValueError, match="digest mismatch"):
        check_corpus(manifest, tmp_path)


@pytest.mark.parametrize("path", ["../outside.bin", "/outside.bin", None])
def test_corpus_rejects_unconfined_or_missing_path(tmp_path: Path, path: str | None) -> None:
    manifest = corpus(tmp_path)
    asset = manifest.assets[0].model_copy(update={"relative_path": path})
    with pytest.raises(ValueError, match="confined relative"):
        check_corpus(
            manifest.model_copy(update={"assets": (asset, *manifest.assets[1:])}), tmp_path
        )


def test_json_duplicate_keys_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "report.json"
    path.write_text('{"model":"first","model":"second"}')
    with pytest.raises(ValueError, match="duplicate"):
        read_json(path)
    path.write_text(json.dumps({"model": "one"}))
    assert read_json(path) == {"model": "one"}


def test_cli_report_checks_actual_bytes_before_claiming_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest = corpus(tmp_path)
    _, fixture = inputs()
    run = fixture.model_copy(
        update={
            "observations": tuple(
                o.model_copy(update={"sha256": a.sha256})
                for o, a in zip(fixture.observations, manifest.assets, strict=True)
            )
        }
    )
    mpath, opath = tmp_path / "manifest.json", tmp_path / "observations.json"
    mpath.write_text(manifest.model_dump_json())
    opath.write_text(run.model_dump_json())
    monkeypatch.setattr(
        sys, "argv", ["benchmark", str(mpath), str(opath), "--corpus-root", str(tmp_path)]
    )
    main()
    report = json.loads(capsys.readouterr().out)
    assert report["corpus_binding"] == "bytes_checked"
    assert report["acceptance"] == "human_review_required"
    (tmp_path / "asset-0.bin").write_bytes(b"modified")
    with pytest.raises(ValueError, match="digest mismatch"):
        main()
    assert capsys.readouterr().out == ""


def test_corpus_rejects_symlink_outside_selected_root(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    manifest = corpus(root)
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    (root / "link.bin").symlink_to(outside)
    asset = manifest.assets[0].model_copy(update={"relative_path": "link.bin"})
    with pytest.raises(ValueError, match="escapes"):
        check_corpus(manifest.model_copy(update={"assets": (asset, *manifest.assets[1:])}), root)


def test_failed_test_references_leave_queries_unscored_and_recall_denominator_intact() -> None:
    manifest, run = inputs()
    rows = tuple(
        o.model_copy(update={"vector": None}) if o.asset_id == "test-ref" else o
        for o in run.observations
    )
    report = evaluate(manifest, run.model_copy(update={"observations": rows}))
    assert report["failed_references"] == 1
    assert report["failed_queries"] == 0
    assert report["recall"] == {"1": 0, "3": 0, "5": 0}
    strata = report["strata"]
    assert isinstance(strata, dict)
    assert strata["regenerated"]["scored"] == 0
    assert strata["absent"]["false_match_rate_scored"] is None


def test_perfect_impostor_calibration_abstains_instead_of_shipping_threshold() -> None:
    manifest, run = inputs()
    rows = tuple(o.model_copy(update={"vector": (1.0, 0.0)}) for o in run.observations)
    report = evaluate(manifest, run.model_copy(update={"observations": rows}))
    assert isinstance(report["threshold"], float) and report["threshold"] > 1
    assert report["strong_false_matches"] == 0


def test_complete_costs_have_numeric_total() -> None:
    manifest, run = inputs()
    rows = tuple(o.model_copy(update={"cost_usd": 0.01}) for o in run.observations)
    result = evaluate(manifest, run.model_copy(update={"observations": rows}))
    assert result["cost_usd_total"] == pytest.approx(0.12)
    assert result["cost_unknown_observations"] == 0


@pytest.mark.parametrize("budget", ["MAX_ASSET_BYTES", "MAX_CORPUS_BYTES"])
def test_corpus_byte_limits_fail_before_digest_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, budget: str
) -> None:
    manifest = corpus(tmp_path)
    monkeypatch.setattr(benchmark_corpus, budget, 4 if budget == "MAX_ASSET_BYTES" else 40)
    with pytest.raises(ValueError, match="byte budget"):
        check_corpus(manifest, tmp_path)


def test_large_comparison_population_rejected_before_scoring() -> None:
    rows = manifest_rows()[4:]
    example = manifest_rows()[0]
    for i in range(3000):
        rows.append(
            {
                **example,
                "id": f"dev-{i}",
                "role": "reference" if i < 1500 else "query",
                "sha256": f"{i+100:064x}",
            }
        )
    with pytest.raises(ValidationError, match="comparison budget"):
        BenchmarkManifest.model_validate({"assets": rows})


def test_false_matches_count_wrong_known_family_and_absent_query() -> None:
    _, run = inputs()
    rows = manifest_rows()
    rows.append({**rows[8], "id": "test-other", "family": "test-other", "sha256": f"{99:064x}"})
    manifest = BenchmarkManifest.model_validate({"assets": rows})
    data = run.model_dump(mode="json")
    data["observations"][10]["vector"] = [0, 1]
    data["observations"].append(
        {
            "asset_id": "test-other",
            "sha256": f"{99:064x}",
            "vector": [0, 1],
            "latency_ms": 1,
            "cost_usd": 0,
        }
    )
    report = evaluate(manifest, BenchmarkRun.model_validate(data))
    assert report["strong_false_matches"] == 2
    assert report["absent_false_match_rate"] == 1
    assert report["recall"] == {"1": 0.5, "3": 1, "5": 1}
    strata = report["strata"]
    assert isinstance(strata, dict)
    assert strata["lookalike"]["false_match_rate_scored"] == 1
