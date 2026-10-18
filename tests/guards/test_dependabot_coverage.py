"""Dependabot must cover every manifest the repository actually has — derived, not hand-listed.

From the CI-integrity audit (ADR-0018): documentation said the dependency bot covered every
service, while three services and three Dockerfiles were missing and one entry pointed at a path
that no longer existed. A new manifest (the Go module, the mobile app, Terraform) must not arrive
without updates, and a deleted one must not leave an entry that watches nothing.

Coverage is derived from the manifests git tracks, in both directions:
- every manifest directory has a Dependabot entry for its ecosystem;
- every Dependabot entry points at a directory that has a manifest for that ecosystem.
"""

from __future__ import annotations

import subprocess
from pathlib import PurePosixPath

import yaml
from conftest import REPO_ROOT

DEPENDABOT = REPO_ROOT / ".github" / "dependabot.yml"

# Manifest file name → the Dependabot ecosystem that updates it. Extend this when a new
# ecosystem arrives (gomod for trust/, terraform for infra/); the test then demands the entry.
ECOSYSTEM_OF = {
    "requirements.txt": "pip",
    "requirements-dev.txt": "pip",
    "requirements-ci.txt": "pip",
    "package.json": "npm",
    "Dockerfile": "docker",
    "go.mod": "gomod",
    "main.tf": "terraform",
}


def _manifest_dirs() -> set[tuple[str, str]]:
    """(ecosystem, "/dir") for every tracked manifest, plus the workflows."""
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    found: set[tuple[str, str]] = set()
    for name in tracked:
        path = PurePosixPath(name)
        ecosystem = ECOSYSTEM_OF.get(path.name)
        if ecosystem:
            directory = "/" if str(path.parent) == "." else f"/{path.parent}"
            found.add((ecosystem, directory))
        if path.parent == PurePosixPath(".github/workflows"):
            found.add(("github-actions", "/"))
    return found


def _configured() -> set[tuple[str, str]]:
    updates = yaml.safe_load(DEPENDABOT.read_text())["updates"]
    return {(entry["package-ecosystem"], entry["directory"]) for entry in updates}


def test_every_manifest_is_watched_by_dependabot() -> None:
    manifests = _manifest_dirs()
    assert manifests, "no manifests found — this test cannot see what it guards"
    missing = sorted(manifests - _configured())
    assert (
        not missing
    ), f"manifests with no Dependabot entry (they would never receive updates): {missing}"


def test_every_dependabot_entry_watches_a_real_manifest() -> None:
    configured = _configured()
    assert configured, "dependabot.yml has no update entries"
    stale = sorted(configured - _manifest_dirs())
    assert not stale, f"Dependabot entries pointing at no manifest (they watch nothing): {stale}"
