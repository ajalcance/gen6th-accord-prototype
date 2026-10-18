"""CI must test the runtime the repository ships, and every pin must stay a pin.

From the CI-integrity audit (ADR-0018): a large repository tested Python 3.12 and Node 20 in CI
while its images shipped Python 3.13 and Node 22, and nobody noticed. Here the same drift was
already being proposed on day one — Dependabot opened PRs for Node 25 and a Python 3.13/3.14
devcontainer. These tests make that drift a failure instead of a surprise:

- one Python minor version across CI, the backend image and the devcontainer;
- one Node major version across CI, the frontend image, `.nvmrc` and the devcontainer;
- one pinned runner image for every CI job, never a moving `-latest` label;
- one PostgreSQL major version between the test suite and the deployed database;
- the pre-commit gitleaks hook at the same version CI's secret scan pins;
- every pre-commit hook pinned to a full commit SHA, never a movable tag.

Each check also asserts it found something to compare, because a comparison over an empty set
passes for any repository (CLAUDE.md §8 rule 1).
"""

from __future__ import annotations

import json
import re

import yaml
from conftest import REPO_ROOT

WORKFLOWS = sorted((REPO_ROOT / ".github" / "workflows").glob("*.y*ml"))
PRE_COMMIT = REPO_ROOT / ".pre-commit-config.yaml"


def _setup_versions(action: str, key: str) -> set[str]:
    """Every `<key>` passed to `<action>` in any workflow."""
    found: set[str] = set()
    for workflow in WORKFLOWS:
        for job in (yaml.safe_load(workflow.read_text()).get("jobs") or {}).values():
            for step in job.get("steps") or []:
                if action in str(step.get("uses", "")):
                    found.add(str(step.get("with", {}).get(key, "")))
    return found


def _first(pattern: str, path: str) -> str:
    match = re.search(pattern, (REPO_ROOT / path).read_text(), re.M)
    assert match, f"{path}: no match for {pattern!r} — this test can no longer see the version"
    return match.group(1)


def test_one_python_version_everywhere() -> None:
    ci = _setup_versions("actions/setup-python", "python-version")
    assert ci, "no setup-python step found in any workflow"
    backend_image = _first(r"^FROM python:(\d+\.\d+)", "backend/Dockerfile")
    devcontainer = _first(r"devcontainers/python:(\d+\.\d+)-", ".devcontainer/Dockerfile")
    assert ci == {backend_image} == {devcontainer}, (
        f"Python drift: CI {sorted(ci)}, backend image {backend_image}, devcontainer "
        f"{devcontainer}. Upgrade them together, in one PR."
    )


def test_one_node_version_everywhere() -> None:
    ci = _setup_versions("actions/setup-node", "node-version")
    assert ci, "no setup-node step found in any workflow"
    frontend_image = _first(r"^FROM node:(\d+)-", "frontend/Dockerfile")
    nvmrc = (REPO_ROOT / ".nvmrc").read_text().strip().lstrip("v").split(".")[0]
    # The devcontainer installs Node through a feature, not its Dockerfile, so the Dockerfile
    # check above never saw it: it sat on Node 20 against 22 everywhere else until 2026-09-25.
    features = json.loads((REPO_ROOT / ".devcontainer" / "devcontainer.json").read_text())
    node_feature = features.get("features", {}).get("ghcr.io/devcontainers/features/node:1", {})
    devcontainer = str(node_feature.get("version", "")).split(".")[0]
    assert devcontainer, "devcontainer.json installs no Node — this test can no longer see it"
    assert ci == {frontend_image} == {nvmrc} == {devcontainer}, (
        f"Node drift: CI {sorted(ci)}, frontend image {frontend_image}, .nvmrc {nvmrc}, "
        f"devcontainer {devcontainer}. Upgrade them together, in one PR."
    )


def test_every_job_runs_on_one_pinned_runner_image() -> None:
    """`ubuntu-latest` moves on GitHub's schedule, not ours.

    It was due to jump to Ubuntu 26 on 2026-10-19, announced only in a job annotation. A moved
    image changes the compilers, system libraries and preinstalled tools under every gate at
    once, with no PR to review. An image upgrade is a deliberate PR, like a runtime upgrade.
    """
    images: dict[str, str] = {}
    for workflow in WORKFLOWS:
        for name, job in (yaml.safe_load(workflow.read_text()).get("jobs") or {}).items():
            images[f"{workflow.name}:{name}"] = str(job.get("runs-on", ""))
    assert images, "no jobs found in any workflow — this test can no longer see the runners"
    moving = {
        job: image for job, image in images.items() if not re.fullmatch(r"ubuntu-\d+\.\d+", image)
    }
    assert not moving, f"jobs on a moving or unreviewed runner image: {moving}"
    assert len(set(images.values())) == 1, f"runner image drift across jobs: {images}"


def test_the_test_database_is_the_production_database() -> None:
    """TA-015: evidence about PostgreSQL has to come from the PostgreSQL that ships.

    The tests run the image pinned in backend/tests/postgres/Dockerfile. It must be pinned by
    digest (a tag can be moved), and its major version must match the deployed database.
    """
    tests = _first(r"^FROM (postgres:\S+)", "backend/tests/postgres/Dockerfile")
    assert "@sha256:" in tests, f"the test database image is not pinned by digest: {tests}"
    tests_major = _first(r"^FROM postgres:(\d+)", "backend/tests/postgres/Dockerfile")
    deployed = _first(r"image:\s*postgres:(\d+)", "deploy/docker-compose.yml")
    assert tests_major == deployed, (
        f"tests run PostgreSQL {tests_major} but deploy/docker-compose.yml runs {deployed}. "
        f"Upgrade them together, in one PR."
    )


def test_the_commit_time_secret_scan_matches_the_ci_one() -> None:
    ci = _first(r"GITLEAKS_VERSION:\s*(\S+)", ".github/workflows/ci.yml")
    hook = _first(r"gitleaks/gitleaks\n\s+rev:\s*\S+\s*#\s*frozen:\s*v(\S+)", PRE_COMMIT.name)
    assert hook == ci, f"pre-commit gitleaks v{hook} but CI scans with v{ci}"


def test_every_pre_commit_hook_is_pinned_to_a_commit() -> None:
    """A tag can be moved to point at different code; a commit cannot."""
    repos = yaml.safe_load(PRE_COMMIT.read_text())["repos"]
    remote = [repo for repo in repos if repo["repo"] not in ("local", "meta")]
    assert remote, "no remote pre-commit repos found"
    unpinned = [
        f"{repo['repo']}@{repo['rev']}"
        for repo in remote
        if not re.fullmatch(r"[0-9a-f]{40}", str(repo["rev"]))
    ]
    assert not unpinned, f"pre-commit revs that are not full commit SHAs: {unpinned}"
