"""The owner-run wall-off script denies every sibling and nothing of this project's own.

It writes deny rules into the local settings, so its two failure modes are both costly: miss a
sibling, and that project is one reflex click away; deny this project, or its own memory, and
the agent cannot work. Each test builds a fake parent folder and home, and runs the real
script against them.
"""

from __future__ import annotations

import json

from conftest import SCRIPTS, run

SCRIPT = SCRIPTS / "wall_off_siblings.py"
TOOLS = ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit")


def _layout(tmp_path):
    parent = tmp_path / "Software Applications"
    project = parent / "gen6th accord"
    for name in ("gen6th accord", "zynth-auth", "zynthq", ".hidden"):
        (parent / name).mkdir(parents=True)
    (parent / "notes.txt").write_text("a file, not a project\n")
    (project / ".claude").mkdir()
    home = tmp_path / "home"
    memories = home / ".claude" / "projects"
    own = str(project).replace("/", "-").replace(" ", "-").replace(".", "-")
    for name in (own, "-Users-x-zynth-auth", "-Users-x-other"):
        (memories / name).mkdir(parents=True)
    return parent, project, home, own


def _run(project, home, *extra):
    return run(
        ["python3", str(SCRIPT), "--project", str(project), "--home", str(home), *extra],
        project,
    )


def test_every_sibling_and_foreign_memory_is_denied_to_every_tool(tmp_path):
    parent, project, home, _ = _layout(tmp_path)
    result = _run(project, home)
    assert result.returncode == 0, result.stderr
    for sibling in ("zynth-auth", "zynthq"):
        for tool in TOOLS:
            assert f"{tool}(/{parent / sibling}/**)" in result.stdout
    for memory in ("-Users-x-zynth-auth", "-Users-x-other"):
        for tool in TOOLS:
            assert f"{tool}(~/.claude/projects/{memory}/**)" in result.stdout
    assert "wall-off: 4 folder(s) to refuse (20 rules)" in result.stdout


def test_this_project_and_its_own_memory_are_never_denied(tmp_path):
    """Denying either would stop the agent working here, or remembering anything."""
    parent, project, home, own = _layout(tmp_path)
    result = _run(project, home)
    assert f"/{project}/**" not in result.stdout
    assert own not in result.stdout
    assert ".hidden" not in result.stdout and "notes.txt" not in result.stdout


def test_a_dry_run_changes_nothing(tmp_path):
    parent, project, home, _ = _layout(tmp_path)
    _run(project, home)
    assert not (project / ".claude" / "settings.local.json").exists()


def test_apply_merges_keeps_existing_rules_and_backs_up(tmp_path):
    parent, project, home, _ = _layout(tmp_path)
    local = project / ".claude" / "settings.local.json"
    local.write_text(json.dumps({"permissions": {"deny": ["Bash(existing)"]}}))
    result = _run(project, home, "--apply")
    assert result.returncode == 0, result.stderr
    deny = json.loads(local.read_text())["permissions"]["deny"]
    assert "Bash(existing)" in deny and len(deny) == 21
    backup = local.with_name("settings.local.json.bak-pre-siblings")
    assert json.loads(backup.read_text())["permissions"]["deny"] == ["Bash(existing)"]


def test_apply_twice_adds_nothing_the_second_time(tmp_path):
    parent, project, home, _ = _layout(tmp_path)
    _run(project, home, "--apply")
    again = _run(project, home, "--apply")
    assert "added 0 rule(s)" in again.stdout


def test_a_malformed_settings_file_is_left_alone(tmp_path):
    """Never overwrite a file this script cannot read: fail, and change nothing."""
    parent, project, home, _ = _layout(tmp_path)
    local = project / ".claude" / "settings.local.json"
    local.write_text("[1, 2]")
    result = _run(project, home, "--apply")
    assert result.returncode != 0
    assert local.read_text() == "[1, 2]"
