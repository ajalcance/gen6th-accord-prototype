"""Run the pinned Codex managed-policy fault checks in CI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_codex_managed_policy() -> None:
    """The guard and its pinned policy must fail when weakened."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/codex/test_policy.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_project_has_no_profile_selector_before_owner_installation() -> None:
    """A clean checkout must load before the managed Mac policy is installed."""
    active = ROOT / ".codex/config.toml"
    assert not active.exists()
