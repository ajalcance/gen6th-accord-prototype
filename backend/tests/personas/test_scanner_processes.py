"""Synthetic TERM/KILL/reaping evidence with no process launcher."""

from unittest.mock import AsyncMock, Mock

import pytest

from accord.scanner import processes
from personas.scanner_fixtures import SyntheticChild


@pytest.mark.parametrize("names", [(), ("clamd",), ("clamd", "clamd")])
def test_exact_two_distinct_live_children_required(names: tuple[str, ...]) -> None:
    children = tuple(Mock(name=name, returncode=None) for name in names)
    for child, name in zip(children, names, strict=True):
        child.name = name
    assert not processes.children_live(children)


async def test_term_all_and_reap_without_kill() -> None:
    children = (SyntheticChild("clamd"), SyntheticChild("freshclam"))
    assert processes.children_live(children)
    await processes.shutdown_children(children)
    assert all(child.signals == ["TERM"] for child in children)
    assert not processes.children_live(children)
    await processes.shutdown_children(())


async def test_resistant_child_escalates_after_term_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(processes, "TERM_SECONDS", 0.01)
    daemon, updater = SyntheticChild("clamd", True), SyntheticChild("freshclam")
    await processes.shutdown_children((daemon, updater))
    assert daemon.signals == ["TERM", "KILL"] and daemon.returncode == -9
    assert updater.signals == ["TERM"]


@pytest.mark.parametrize("fault", ["term", "kill", "wait", "lookup", "survivor"])
async def test_cleanup_faults_never_acknowledge_clean_exit_and_other_child_stops(
    fault: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(processes, "TERM_SECONDS", 0.01)
    monkeypatch.setattr(processes, "KILL_SECONDS", 0.01)
    daemon, updater = SyntheticChild("clamd", True), SyntheticChild("freshclam")
    if fault == "term":
        monkeypatch.setattr(daemon, "terminate", Mock(side_effect=RuntimeError("private")))
    if fault == "kill":
        monkeypatch.setattr(daemon, "kill", Mock(side_effect=RuntimeError("private")))
    if fault == "lookup":
        monkeypatch.setattr(daemon, "kill", Mock(side_effect=ProcessLookupError("private")))
    if fault == "wait":
        monkeypatch.setattr(daemon, "wait", AsyncMock(side_effect=RuntimeError("private")))
    if fault == "survivor":
        monkeypatch.setattr(daemon, "kill", Mock())
    with pytest.raises(RuntimeError, match="^scanner child cleanup unavailable$") as error:
        await processes.shutdown_children((daemon, updater))
    assert "private" not in str(error.value)
    assert updater.returncode == 0


async def test_disappeared_child_still_must_be_reaped() -> None:
    child = SyntheticChild("clamd")
    child.exit(0)
    await processes.shutdown_children((child,))
    assert child.signals == []
