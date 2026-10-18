"""secret_scan must prove it can see a secret before it may report none.

The matrix from the CI-integrity audit: every row is watched to behave, because a fix to a silent
control needs more suspicion than the control it replaced.

    clean range → pass            planted secret in range → fail
    blind scanner → refuse        scanner blind for one directory → refuse
    empty base → refuse           unknown ref → refuse       zero-commit range → refuse
    missing scanner → refuse      crashing scanner → refuse  scanner writes no report → refuse

The REAL guard runs against a stand-in scanner. The stand-in reads the git history of the
directory it is pointed at and reports GitHub-token-shaped values added in the requested range,
so the guard's decisions are tested against a scanner that behaves like one. The real binary is
proven separately, on every CI run, by the guard's own canary.

Tokens are assembled at run time. No literal secret exists in this file for a scanner to flag
or for anyone to exempt.
"""

from __future__ import annotations

import json
import secrets
import string
import subprocess
from pathlib import Path

from conftest import git_commit, git_init, install_guard, run_guard, write

TOKEN_PREFIX = "ghp" + "_"

# The stand-in scanner. STUB_MODE selects the behaviour; BLIND_DIR hides one directory the way a
# widened allowlist would; STUB_ARGV_LOG records exactly what the guard passed it.
STUB = """\
import json, os, re, subprocess, sys
argv = sys.argv[1:]
log = os.environ.get("STUB_ARGV_LOG")
if log:
    with open(log, "a") as handle:
        handle.write(json.dumps({"argv": argv, "config_env": os.environ.get("GITLEAKS_CONFIG")}))
        handle.write("\\n")
mode = os.environ.get("STUB_MODE", "honest")
if mode == "crash":
    sys.exit(3)
def value(flag):
    return argv[argv.index(flag) + 1] if flag in argv else None
report = value("--report-path")
if mode == "no-report":
    sys.exit(0)
findings = []
if mode == "honest":
    source = value("--source")
    log_opts = value("--log-opts")
    blind = os.environ.get("BLIND_DIR", "")
    rev = log_opts.split() if log_opts else ["--all"]
    out = subprocess.run(["git", "-C", source, "log", "-p", "--format=COMMIT %H", *rev],
                         capture_output=True, text=True).stdout
    pattern = re.compile(PREFIX + "[A-Za-z0-9]{36}")
    commit = path = ""
    for line in out.splitlines():
        if line.startswith("COMMIT "):
            commit = line.split()[1]
        elif line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("+") and pattern.search(line):
            if blind and path.startswith(blind + "/"):
                continue
            findings.append({"File": path, "StartLine": 1, "RuleID": "github-pat",
                             "Commit": commit})
with open(report, "w") as handle:
    json.dump(findings, handle)
sys.exit(1 if findings else 0)
"""


def token() -> str:
    return TOKEN_PREFIX + "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(36)
    )


def make_stub(tmp_path: Path) -> Path:
    stub = tmp_path / "bin" / "gitleaks"
    # `env python3`, not sys.executable: a shebang cannot hold a path with a space in it.
    write(stub, f"#!/usr/bin/env python3\nPREFIX = {TOKEN_PREFIX!r}\n" + STUB)
    stub.chmod(0o755)
    return stub


def make_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A sandbox repo with the real guard, a config, two directories and two commits."""
    repo = tmp_path / "repo"
    guard = install_guard(repo, "secret_scan.py")
    write(repo / ".gitleaks.toml", 'title = "sandbox"\n')
    write(repo / "backend" / "app.py", "def run():\n    return 1\n")
    write(repo / "docs" / "guide.md", "# Guide\n")
    git_init(repo)
    git_commit(repo, "base")
    write(repo / "backend" / "feature.py", "def feature():\n    return 2\n")
    git_commit(repo, "feature")
    return repo, guard, make_stub(tmp_path)


def scan(guard: Path, stub: Path, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
    return run_guard(guard, "--gitleaks", str(stub), *args, env=env or None)


def test_clean_range_passes_and_prints_its_denominators(tmp_path: Path) -> None:
    _, guard, stub = make_repo(tmp_path)
    result = scan(guard, stub, "--base", "HEAD~1")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "canary — 4/4 planted tokens detected across 4 director(ies)" in result.stdout
    assert "inspected 1 commit(s)" in result.stdout


def test_a_secret_committed_in_the_range_fails(tmp_path: Path) -> None:
    repo, guard, stub = make_repo(tmp_path)
    write(repo / "backend" / "settings.py", f'API_TOKEN = "{token()}"\n')
    git_commit(repo, "leak")
    result = scan(guard, stub, "--base", "HEAD~2")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "backend/settings.py" in result.stderr


def test_only_the_requested_range_is_scanned(tmp_path: Path) -> None:
    """History before the base was triaged once; the gate judges what this change adds."""
    repo, guard, stub = make_repo(tmp_path)
    write(repo / "backend" / "old.py", f'LEGACY = "{token()}"\n')
    git_commit(repo, "old leak")
    write(repo / "backend" / "new.py", "VALUE = 3\n")
    git_commit(repo, "clean change")
    result = scan(guard, stub, "--base", "HEAD~1")
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_blind_scanner_is_refused(tmp_path: Path) -> None:
    _, guard, stub = make_repo(tmp_path)
    result = scan(guard, stub, "--base", "HEAD~1", STUB_MODE="blind")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "missed 4 canary token(s)" in result.stderr


def test_a_scanner_blind_to_one_directory_is_refused(tmp_path: Path) -> None:
    """A config widened for one directory must not pass behind a canary planted elsewhere."""
    _, guard, stub = make_repo(tmp_path)
    result = scan(guard, stub, "--base", "HEAD~1", BLIND_DIR="docs")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "docs/zz-secret-canary.md" in result.stderr


def test_an_empty_base_is_refused(tmp_path: Path) -> None:
    _, guard, stub = make_repo(tmp_path)
    result = scan(guard, stub, "--base", "")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "empty" in result.stderr


def test_an_unknown_ref_is_refused(tmp_path: Path) -> None:
    _, guard, stub = make_repo(tmp_path)
    result = scan(guard, stub, "--base", "no-such-ref")
    assert result.returncode == 2, result.stdout + result.stderr


def test_a_range_with_no_commits_is_refused(tmp_path: Path) -> None:
    _, guard, stub = make_repo(tmp_path)
    result = scan(guard, stub, "--base", "HEAD")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "contains no commits" in result.stderr


def test_a_missing_scanner_is_refused(tmp_path: Path) -> None:
    _, guard, _ = make_repo(tmp_path)
    result = run_guard(guard, "--gitleaks", str(tmp_path / "absent"), "--base", "HEAD~1")
    assert result.returncode == 2, result.stdout + result.stderr


def test_a_scanner_that_cannot_execute_is_refused_not_reported_as_a_leak(tmp_path: Path) -> None:
    """An exec failure once surfaced as a traceback with exit 1 — the code a real leak uses."""
    _, guard, _ = make_repo(tmp_path)
    broken = tmp_path / "bin" / "broken-gitleaks"
    write(broken, "#!/nonexistent/interpreter\n")
    broken.chmod(0o755)
    result = run_guard(guard, "--gitleaks", str(broken), "--base", "HEAD~1")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "could not run gitleaks" in result.stderr


def test_a_crashing_scanner_is_refused(tmp_path: Path) -> None:
    _, guard, stub = make_repo(tmp_path)
    result = scan(guard, stub, "--base", "HEAD~1", STUB_MODE="crash")
    assert result.returncode == 2, result.stdout + result.stderr


def test_a_scanner_that_writes_no_report_is_refused(tmp_path: Path) -> None:
    _, guard, stub = make_repo(tmp_path)
    result = scan(guard, stub, "--base", "HEAD~1", STUB_MODE="no-report")
    assert result.returncode == 2, result.stdout + result.stderr


def test_ignore_mechanisms_and_ambient_config_are_disabled(tmp_path: Path) -> None:
    """No inline allow comments, no .gitleaksignore, no config but the one under review."""
    repo, guard, stub = make_repo(tmp_path)
    argv_log = tmp_path / "argv.jsonl"
    result = scan(
        guard,
        stub,
        "--base",
        "HEAD~1",
        STUB_ARGV_LOG=str(argv_log),
        GITLEAKS_CONFIG=str(tmp_path / "attacker.toml"),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    calls = [json.loads(line) for line in argv_log.read_text().splitlines()]
    assert len(calls) == 2, "expected exactly one canary scan and one real scan"
    for call in calls:
        argv = call["argv"]
        assert call["config_env"] is None
        assert "--ignore-gitleaks-allow" in argv
        assert argv[argv.index("--config") + 1] == str(repo / ".gitleaks.toml")
        ignore_dir = Path(argv[argv.index("--gitleaks-ignore-path") + 1])
        assert not str(ignore_dir).startswith(str(repo))
