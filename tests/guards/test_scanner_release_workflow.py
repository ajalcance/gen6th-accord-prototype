"""Release wiring and real shell denial; generated files are test-only."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml
from conftest import REPO_ROOT

PACKAGING = (
    "Dockerfile",
    "input-lock.json",
    "service.json",
    "prepare-context.sh",
    "native-acceptance.sh",
)


def steps(job: str) -> list[dict[str, Any]]:
    path = REPO_ROOT / ".github/workflows/release.yml"
    return yaml.safe_load(path.read_text())["jobs"][job]["steps"]


def test_candidate_requires_scanner_before_build_and_publication() -> None:
    candidate = steps("candidate")
    names = [step.get("name") for step in candidate]
    required = [
        names.index(name)
        for name in (
            "Require genuine scanner packaging and native acceptance",
            "Native acceptance of exact scanner digest",
            "Bind and verify scanner assembly before publication",
        )
    ]
    assert required[0] < names.index("Build & push backend")
    assert required[1] < required[2] < names.index("Publish the release with its evidence")
    for index in required:
        assert "if" not in candidate[index] and not candidate[index].get("continue-on-error")
    assert "scanner_release_gate.py --mode candidate" in candidate[required[2]]["run"]
    for identifier in ("scanner", "scanner_scan"):
        step = next(step for step in candidate if step.get("id") == identifier)
        assert "if" not in step and not step.get("continue-on-error")
    build = next(step for step in candidate if step.get("id") == "scanner")
    assert build["with"]["platforms"] == "linux/amd64"
    scan = next(step for step in candidate if step.get("id") == "scanner_scan")
    assert scan["with"]["fail-build"] is True
    assert scan["with"]["severity-cutoff"] == "high"
    assert scan["with"]["only-fixed"] is True


def test_promotion_requires_gate_before_any_retag_and_has_no_build() -> None:
    promotion = steps("promote")
    names = [step.get("name") for step in promotion]
    index = names.index("Verify mandatory scanner assembly before any retagging")
    assert "if" not in promotion[index] and not promotion[index].get("continue-on-error")
    assert "scanner_release_gate.py --mode promote" in promotion[index]["run"]
    assert index < names.index("Verify signatures and point :stable at the recorded digests")
    assert not any("build-push-action" in step.get("uses", "") for step in promotion)


@pytest.mark.parametrize("missing", PACKAGING)
def test_missing_packaging_stops_real_shell_before_context_or_build(
    tmp_path: Path,
    missing: str,
) -> None:
    directory = tmp_path / "deploy/google/scanner"
    directory.mkdir(parents=True)
    for name in PACKAGING:
        if name != missing:
            (directory / name).write_text("touch context-reached\n")
    step = next(
        step for step in steps("candidate") if step.get("name", "").startswith("Require genuine")
    )
    result = subprocess.run(
        ["bash", "-e", "-c", step["run"] + "\ntouch build-reached\n"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert not (tmp_path / "context-reached").exists()
    assert not (tmp_path / "build-reached").exists()
