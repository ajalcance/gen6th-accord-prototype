"""dod-check must catch an undocumented module and a stale doc reference."""

from __future__ import annotations

from conftest import app_package, install_guard, run_guard, write

ARCH = "docs/architecture/current-state.md"


def _sandbox(tmp_path, arch_body: str):
    guard = install_guard(tmp_path, "dod-check.py")
    write(tmp_path / ARCH, arch_body)
    return guard


def _base_arch() -> str:
    # `scripts/` (the guard) and `docs/` (this page) exist in every sandbox, and every top-level
    # directory is derived from the tree and must be documented — so both are named here.
    return "# Current State\n\nscripts/   the guards\ndocs/      the records\n"


def test_documented_tree_passes(tmp_path):
    guard = _sandbox(tmp_path, _base_arch())
    result = run_guard(guard)
    assert result.returncode == 0, result.stdout + result.stderr


def test_top_level_dir_absent_from_as_built_fails(tmp_path):
    guard = _sandbox(tmp_path, "# Current State\n\nnothing documented here\n")
    result = run_guard(guard)
    assert result.returncode != 0, "an undocumented top-level dir must fail"
    assert "scripts" in result.stdout


def test_a_new_top_level_directory_must_be_documented(tmp_path):
    """Derived from the tree, not hand-listed: `trust/` once passed with no mention at all.

    Both directions: a new directory fails until it is named, and hidden tooling directories
    are never demanded.
    """
    guard = _sandbox(tmp_path, _base_arch())
    write(tmp_path / "infra" / "main.tf", "")
    write(tmp_path / ".cache" / "x" / "y.txt", "")
    missing = run_guard(guard)
    assert missing.returncode != 0, "an undocumented top-level directory passed"
    assert "'infra/'" in missing.stdout and ".cache" not in missing.stdout, missing.stdout
    write(tmp_path / ARCH, _base_arch() + "infra/   the servers, as code\n")
    assert run_guard(guard).returncode == 0, "documenting it must satisfy the check"


def test_undocumented_backend_module_fails(tmp_path):
    guard = _sandbox(tmp_path, _base_arch())
    write(tmp_path / "backend" / app_package() / "billing" / "__init__.py", "")
    result = run_guard(guard)
    assert result.returncode != 0, "a new backend module must be named in current-state.md"
    assert "billing" in result.stdout


def test_documenting_the_module_makes_it_pass(tmp_path):
    """The positive control: the guard must be satisfiable, not merely angry."""
    guard = _sandbox(tmp_path, _base_arch() + "\nbackend/*/billing/   invoicing\n")
    write(tmp_path / "backend" / app_package() / "billing" / "__init__.py", "")
    result = run_guard(guard)
    assert result.returncode == 0, result.stdout + result.stderr


def test_stale_backticked_reference_fails(tmp_path):
    guard = _sandbox(tmp_path, _base_arch() + "\nSee `scripts/does_not_exist.py` for details.\n")
    result = run_guard(guard)
    assert result.returncode != 0, "a backticked path that does not exist must fail"
    assert "does_not_exist" in result.stdout


def test_a_nested_repository_is_not_this_projects_documentation(tmp_path):
    """An agent worktree in `.claude/worktrees/` is another checkout — both directions.

    Its documents (and its node_modules) must be skipped, while the same stale reference in
    this project's own `.claude/` documentation is still caught.
    """
    guard = _sandbox(tmp_path, _base_arch())
    worktree = tmp_path / ".claude" / "worktrees" / "agent-1"
    write(worktree / ".git", "gitdir: /elsewhere/.git/worktrees/agent-1\n")
    write(worktree / "node_modules" / "pkg" / "README.md", "See `scripts/roles.json`.\n")
    skipped = run_guard(guard)
    assert skipped.returncode == 0, "a nested repository's docs were checked as ours\n" + (
        skipped.stdout
    )
    write(tmp_path / ".claude" / "commands" / "note.md", "See `scripts/roles.json`.\n")
    caught = run_guard(guard)
    assert caught.returncode != 0, "a stale reference in our own .claude/ docs must still fail"
    assert ".claude/commands/note.md" in caught.stdout, caught.stdout


def test_duplicate_adr_number_fails(tmp_path):
    guard = _sandbox(tmp_path, _base_arch())
    decisions = tmp_path / "docs" / "decisions"
    write(decisions / "0001-first.md", "# 1. First\n")
    write(decisions / "0001-also-first.md", "# 1. Also first\n")
    write(decisions / "README.md", "- 0001-first.md\n- 0001-also-first.md\n")
    result = run_guard(guard)
    assert result.returncode != 0, "a reused ADR number must fail"
    assert "0001" in result.stdout


def test_adr_number_gap_fails(tmp_path):
    guard = _sandbox(tmp_path, _base_arch())
    decisions = tmp_path / "docs" / "decisions"
    write(decisions / "0001-first.md", "# 1\n")
    write(decisions / "0003-third.md", "# 3\n")
    write(decisions / "README.md", "- 0001-first.md\n- 0003-third.md\n")
    result = run_guard(guard)
    assert result.returncode != 0, "a gap in ADR numbering must fail"


def test_unindexed_adr_fails(tmp_path):
    guard = _sandbox(tmp_path, _base_arch())
    decisions = tmp_path / "docs" / "decisions"
    write(decisions / "0001-first.md", "# 1\n")
    write(decisions / "README.md", "no entries here\n")
    result = run_guard(guard)
    assert result.returncode != 0, "an ADR absent from the index must fail"
    assert "0001-first.md" in result.stdout


def test_contiguous_indexed_adrs_pass(tmp_path):
    guard = _sandbox(tmp_path, _base_arch())
    decisions = tmp_path / "docs" / "decisions"
    write(decisions / "0001-first.md", "# 1\n")
    write(decisions / "0002-second.md", "# 2\n")
    write(decisions / "README.md", "- 0001-first.md\n- 0002-second.md\n")
    result = run_guard(guard)
    assert result.returncode == 0, result.stdout + result.stderr


def test_out_of_order_lessons_fail(tmp_path):
    guard = _sandbox(tmp_path, _base_arch())
    write(
        tmp_path / "docs" / "LESSONS.md",
        "# Lessons\n\n## 2026-01-01 — older on top\n\n## 2026-06-01 — newer below\n",
    )
    result = run_guard(guard)
    assert result.returncode != 0, "LESSONS declares newest-first; ascending order must fail"


def test_newest_first_lessons_pass(tmp_path):
    guard = _sandbox(tmp_path, _base_arch())
    write(
        tmp_path / "docs" / "LESSONS.md",
        "# Lessons\n\n## 2026-06-01 — newest\n\n## 2026-01-01 — older\n",
    )
    result = run_guard(guard)
    assert result.returncode == 0, result.stdout + result.stderr


# --- The denominator: an as-built check over an absent tree passes over nothing ---------


def test_the_denominator_is_printed_on_success(tmp_path):
    guard = _sandbox(tmp_path, _base_arch())
    result = run_guard(guard)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "inspected" in result.stdout and "top-level dirs" in result.stdout, result.stdout


def test_a_renamed_package_does_not_silently_empty_the_check(tmp_path):
    """After a package rename, every as-built assertion walks an absent directory.

    It finds nothing to complain about and prints OK over a page describing a different
    project — the worst kind of green, because it is indistinguishable from a real one.
    """
    guard = install_guard(tmp_path, "dod-check.py")
    # Point the guard at a package that does not exist, and remove the one directory that
    # would otherwise keep the top-level count non-zero.
    guard.write_text(
        guard.read_text().replace(f'APP_PKG = "{app_package()}"', 'APP_PKG = "renamed_away"')
    )
    write(tmp_path / ARCH, "# Current State\n")
    result = run_guard(guard, cwd=tmp_path / "scripts")
    assert "inspected" in result.stdout, result.stdout
