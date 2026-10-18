"""Production binding and proposed source closure; no actual server/process launch."""

import ast
import inspect
import os
import platform
import pwd
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from starlette.routing import Route

from accord.scanner import production, runtime


def test_production_factory_constructs_actual_runtime_without_starting_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(os, "geteuid", lambda: 100)
    monkeypatch.setattr(pwd, "getpwnam", lambda _: SimpleNamespace(pw_uid=100))
    app = production.create_app()
    assert isinstance(app.state.scanner.runtime, runtime.ScannerRuntime)
    assert not app.state.scanner.runtime.children and app.state.scanner.task is None
    assert {route.path for route in app.routes if isinstance(route, Route)} == {"/health"}


def test_factory_requires_real_runtime_and_propagates_denial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime, factory = Mock(), Mock()
    monkeypatch.setattr(production, "ScannerRuntime", runtime)
    monkeypatch.setattr(production, "create_scanner_app", factory)
    assert not inspect.signature(production.create_app).parameters
    assert production.create_app() is factory.return_value
    factory.assert_called_once_with(runtime.return_value)
    runtime.assert_called_once_with()
    runtime.side_effect = ValueError("scanner platform unavailable")
    with pytest.raises(ValueError, match="platform unavailable"):
        production.create_app()
    assert factory.call_count == 1


def test_proposed_context_resolves_every_accord_import_and_excludes_build_tests() -> None:
    root = Path(__file__).resolve().parents[3]
    entries = (root / "deploy/google/scanner/source-files.txt").read_text().splitlines()
    assert len(entries) == len(set(entries)) and entries
    paths = {Path(entry) for entry in entries}
    assert Path("accord/scanner/production.py") in paths
    assert Path("accord/scanner/seed_policy.py") not in paths
    for relative in paths:
        assert relative.parts[0] == "accord" and relative.suffix == ".py"
        assert not {"tests", "fixtures", "examples", ".."} & set(relative.parts)
        source = root / "backend" / relative
        assert source.is_file() and not source.is_symlink()
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.level == 0
                if node.module.startswith("accord."):
                    module = Path(*node.module.split("."))
                    assert module.with_suffix(".py") in paths or module / "__init__.py" in paths
                    if module / "__init__.py" in paths:
                        for alias in node.names:
                            assert (module / alias.name).with_suffix(".py") in paths
