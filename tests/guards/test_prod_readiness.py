"""prod_readiness must detect drift between PROD-BLOCKER markers and the register, both ways."""

from __future__ import annotations

from conftest import install_guard, load_module, run_guard, set_register, write

# Assembled at runtime so this file contains no literal marker of its own. prod_readiness.py
# scans .py sources, and a test *demonstrating* the convention must not be counted as *declaring*
# a real production blocker — the same "wrote about it vs did it" distinction the suppression scan
# makes. Do NOT inline these back into string literals: it will fail `make dod-check`.
MARKER = "PROD-" + "BLOCKER"

REGISTER_EMPTY: tuple[tuple[str, str], ...] = ()
REGISTER_ONE = (("auth-stub", "replace before launch"),)


def _sandbox(tmp_path, *, register: tuple[tuple[str, str], ...], marker: bool):
    guard = install_guard(tmp_path, "prod_readiness.py")
    # Always set, never inherited: the real register may hold entries of its own.
    set_register(guard, register)
    # A scannable source file, always. "A clean project" means one with source and no
    # markers, not an empty directory — and an empty directory is precisely the vacuous
    # denominator this guard now refuses, so a fixture without one tests the wrong branch.
    write(tmp_path / "main.py", "def run():\n    return 1\n")
    if marker:
        write(tmp_path / "app.py", f"# {MARKER}(auth-stub): dev-only check\n")
    return guard


def test_clean_project_passes(tmp_path):
    guard = _sandbox(tmp_path, register=REGISTER_EMPTY, marker=False)
    result = run_guard(guard)
    assert result.returncode == 0, result.stdout + result.stderr


def test_marker_without_register_entry_fails(tmp_path):
    guard = _sandbox(tmp_path, register=REGISTER_EMPTY, marker=True)
    result = run_guard(guard)
    assert result.returncode != 0, "an unregistered PROD-BLOCKER marker must fail"
    assert "auth-stub" in result.stdout


def test_register_entry_without_marker_fails(tmp_path):
    """Anti-rot: a register that outlives its marker becomes a list of already-fixed items."""
    guard = _sandbox(tmp_path, register=REGISTER_ONE, marker=False)
    result = run_guard(guard)
    assert result.returncode != 0, "a stale register entry must fail"


def test_consistent_pair_passes_but_strict_blocks_release(tmp_path):
    guard = _sandbox(tmp_path, register=REGISTER_ONE, marker=True)
    assert run_guard(guard).returncode == 0, "a consistent open blocker is not an error"
    assert run_guard(guard, "--strict").returncode != 0, "--strict must deny release"


def test_documentation_prose_is_not_counted_as_a_marker(tmp_path):
    """Docs explaining the convention name the marker; that must not count as declaring one."""
    guard = _sandbox(tmp_path, register=REGISTER_EMPTY, marker=False)
    write(tmp_path / "ONBOARDING.md", f"Use `# {MARKER}(example): why` to register a hold.\n")
    assert run_guard(guard).returncode == 0


def test_fixtures_never_inherit_the_real_register(tmp_path):
    """The failure that kept the register empty: a real entry leaked into every fixture.

    Simulate a repository whose register holds a multi-line entry — the shape a real one
    takes — and prove each fixture shape replaces it wholesale, rather than silently not.
    """
    guard = install_guard(tmp_path, "prod_readiness.py")
    set_register(guard, REGISTER_EMPTY)
    hand_edited = (
        "BLOCKERS: tuple[tuple[str, str], ...] = (\n"
        '    ("docs-harness", "no test proves the docs site publishes only docs/public"),\n'
        '    ("second", "another open stand-in"),\n'
        ")\n"
    )
    empty_line = f"BLOCKERS: tuple[tuple[str, str], ...] = {REGISTER_EMPTY!r}\n"
    guard.write_text(guard.read_text().replace(empty_line, hand_edited))
    assert len(load_module(guard).BLOCKERS) == 2, "the simulated real register did not take"
    for wanted in (REGISTER_EMPTY, REGISTER_ONE):
        set_register(guard, wanted)
        assert load_module(guard).BLOCKERS == wanted, f"the register was not replaced: {wanted}"


def test_a_register_that_cannot_be_found_is_refused(tmp_path):
    """Silently doing nothing is what the old string replace did. Refuse instead."""
    guard = install_guard(tmp_path, "prod_readiness.py")
    guard.write_text(guard.read_text().replace("BLOCKERS", "RENAMED"))
    try:
        set_register(guard, REGISTER_ONE)
    except AssertionError as exc:
        assert "0 times" in str(exc)
    else:
        raise AssertionError("a missing register was silently accepted")


def test_a_nested_repository_is_not_scanned_but_a_subdirectory_is(tmp_path):
    """An agent worktree is a second copy of the tree: its markers are not ours.

    Both directions: a marker inside a directory with its own `.git` is ignored, and the same
    marker one level over, in an ordinary subdirectory, still fails as unregistered.
    """
    guard = _sandbox(tmp_path, register=REGISTER_EMPTY, marker=False)
    worktree = tmp_path / ".claude" / "worktrees" / "agent-1"
    write(worktree / ".git", "gitdir: /elsewhere/.git/worktrees/agent-1\n")
    write(worktree / "scripts" / "copy.py", f"# {MARKER}(auth-stub): the worktree's copy\n")
    skipped = run_guard(guard)
    assert skipped.returncode == 0, "a nested repository was scanned as ours\n" + skipped.stdout
    write(tmp_path / "pkg" / "real.py", f"# {MARKER}(auth-stub): ours\n")
    caught = run_guard(guard)
    assert caught.returncode != 0, "an unregistered marker in our own tree must still fail"
    assert "pkg/real.py" in caught.stdout, caught.stdout


def test_scanning_no_file_at_all_fails(tmp_path):
    """The denominator rule: "no open blockers" and "this read nothing" printed the same line."""
    guard = install_guard(tmp_path, "prod_readiness.py")  # nothing else in the tree
    result = run_guard(guard)
    assert result.returncode != 0, "scanning zero files must fail, not report no blockers"
    assert "no file was scanned" in result.stdout, result.stdout


def test_the_denominator_is_printed_on_success(tmp_path):
    guard = _sandbox(tmp_path, register=REGISTER_EMPTY, marker=False)
    result = run_guard(guard)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "inspected" in result.stdout and "file(s)" in result.stdout, result.stdout
