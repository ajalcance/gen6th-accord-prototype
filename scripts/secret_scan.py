#!/usr/bin/env python3
"""Secret scan over COMMITS, proven by a canary on every run.

Why this exists. CI used to run gitleaks through its pre-commit hook, whose command is
``gitleaks protect --staged``. That is correct on a laptop at commit time, where the change is
staged. A CI checkout is clean: nothing is staged, so the scanner read no input and reported
success on every run. "No findings" looks identical whether a scanner found nothing or read
nothing, so every review that trusted the green result confirmed the error.

This guard makes the scan prove, on every run, that it can see what it is looking for:

1. **Canary first.** Fresh fake tokens are generated at run time and committed into a
   throwaway repository, one in EVERY directory that holds tracked files here, using file
   names that mimic that directory's real files. The real scanner, with this repository's real
   config, must find every one. A blind scanner fails. So does a config that exempts
   everything, or one that was widened to exempt a single directory.
2. **Then the real scan**, over the COMMITS in ``<base>..<head>``, not the staging area.

It fails closed. Every case below refuses (exit 2) rather than reporting clean:
- an empty base;
- a ref that does not resolve to a commit;
- a range with no commits;
- a missing scanner or config;
- a scanner that crashes, or writes no report;
- a canary token that was not found.

There is no ignore list. Inline ``gitleaks:allow`` comments are ignored, and so is any
``.gitleaksignore`` file: the scanner is pointed at an empty ignore directory. An ignore list is
an exemption that only ever grows.

Usage:  python3 scripts/secret_scan.py --base <ref> [--head <ref>] [--gitleaks <path>]
Exit codes: 0 clean · 1 secrets found · 2 refused (the scan could not prove it ran)
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import string
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".gitleaks.toml"

EXIT_CLEAN, EXIT_FINDINGS, EXIT_REFUSED = 0, 1, 2
CANARY_STEM = "zz-secret-canary"
TOKEN_ALPHABET = string.ascii_letters + string.digits


class ScanRefusedError(Exception):
    """The scan cannot prove it inspected anything, so it must not report clean."""


def git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False, timeout=120
    )


def resolve_commit(ref: str) -> str:
    """The full SHA a ref names, or refuse. An empty ref would silently become HEAD."""
    if not ref.strip():
        raise ScanRefusedError("the base ref is empty — an empty side makes the range HEAD..HEAD")
    result = git(["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], ROOT)
    sha = result.stdout.strip()
    if result.returncode != 0 or not sha:
        raise ScanRefusedError(f"{ref!r} does not resolve to a commit")
    return sha


def commit_count(base: str, head: str) -> int:
    result = git(["rev-list", "--count", f"{base}..{head}"], ROOT)
    if result.returncode != 0:
        raise ScanRefusedError(
            f"could not count commits in {base}..{head}: {result.stderr.strip()}"
        )
    return int(result.stdout.strip())


def tracked_directories() -> dict[str, str]:
    """Every directory holding tracked files, mapped to a file suffix seen there.

    The canary is planted in each one, named like that directory's real files, so a config
    exempting one directory or one file type cannot hide behind a canary planted elsewhere.
    """
    result = git(["ls-files", "-z"], ROOT)
    if result.returncode != 0:
        raise ScanRefusedError(f"could not list tracked files: {result.stderr.strip()}")
    directories: dict[str, str] = {}
    for name in filter(None, result.stdout.split("\0")):
        path = Path(name)
        directories.setdefault(path.parent.as_posix(), path.suffix or ".txt")
    if not directories:
        raise ScanRefusedError("no tracked files — there is nothing to plant a canary beside")
    return directories


def canary_token() -> str:
    """A fresh GitHub-token-shaped value. Assembled at run time: no literal exists to exempt."""
    return "ghp" + "_" + "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(36))


def run_gitleaks(gitleaks: str, source: Path, log_opts: str | None) -> list[dict[str, object]]:
    """Run the real scanner and return its findings. Anything but a clean verdict refuses."""
    with tempfile.TemporaryDirectory() as work:
        report = Path(work) / "report.json"
        empty_ignore_dir = Path(work) / "no-ignore-file"
        empty_ignore_dir.mkdir()
        command = [
            gitleaks,
            "detect",
            "--source",
            str(source),
            "--config",
            str(CONFIG),
            "--report-format",
            "json",
            "--report-path",
            str(report),
            "--redact",
            "--no-banner",
            "--exit-code",
            "1",
            "--ignore-gitleaks-allow",
            "--gitleaks-ignore-path",
            str(empty_ignore_dir),
        ]
        if log_opts:
            command += ["--log-opts", log_opts]
        # --config outranks GITLEAKS_CONFIG, but an ambient override is removed anyway: the
        # config under review is the only config this scan may use.
        env = {key: value for key, value in os.environ.items() if key != "GITLEAKS_CONFIG"}
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=False, timeout=600, env=env
            )
        except (OSError, subprocess.SubprocessError) as error:
            # Uncaught, this was a traceback and exit 1 — the code that means "secrets found".
            raise ScanRefusedError(f"could not run gitleaks: {error}") from error
        if result.returncode not in (0, 1):
            raise ScanRefusedError(
                f"gitleaks exited {result.returncode}: {result.stderr.strip()[-400:]}"
            )
        if not report.is_file():
            raise ScanRefusedError("gitleaks wrote no report — it cannot have inspected anything")
        try:
            findings = json.loads(report.read_text() or "[]")
        except json.JSONDecodeError as error:
            raise ScanRefusedError(f"gitleaks wrote an unreadable report: {error}") from error
    if not isinstance(findings, list):
        raise ScanRefusedError("gitleaks report is not a list of findings")
    return findings


def run_canary(gitleaks: str, directories: dict[str, str]) -> None:
    """Plant a token in every directory of a throwaway repo; every one must be found."""
    with tempfile.TemporaryDirectory() as sandbox:
        repo = Path(sandbox)
        for args in (
            ["init", "-q", "-b", "main"],
            ["config", "user.email", "secret-scan-canary@invalid"],
            ["config", "user.name", "secret-scan canary"],
            ["config", "commit.gpgsign", "false"],
        ):
            git(args, repo)
        planted: set[str] = set()
        for directory, suffix in directories.items():
            relative = Path(directory) / f"{CANARY_STEM}{suffix}"
            (repo / relative).parent.mkdir(parents=True, exist_ok=True)
            (repo / relative).write_text(f'token = "{canary_token()}"\n')
            planted.add(relative.as_posix())
        git(["add", "-A"], repo)
        committed = git(["commit", "-q", "--no-verify", "-m", "canary"], repo)
        if committed.returncode != 0:
            raise ScanRefusedError(f"could not commit the canary: {committed.stderr.strip()}")
        found = {str(finding.get("File", "")) for finding in run_gitleaks(gitleaks, repo, None)}
    missed = sorted(planted - found)
    print(
        f"secret-scan: canary — {len(planted) - len(missed)}/{len(planted)} planted tokens "
        f"detected across {len(directories)} director(ies)"
    )
    if missed:
        shown = ", ".join(missed[:10]) + (" …" if len(missed) > 10 else "")
        raise ScanRefusedError(
            f"the scanner missed {len(missed)} canary token(s): {shown}. It is blind, or the "
            f"config exempts those paths — either way this run cannot vouch for anything"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True, help="the commit the scanned range starts after")
    parser.add_argument("--head", default="HEAD", help="the last commit to scan (default HEAD)")
    parser.add_argument("--gitleaks", default="gitleaks", help="path to the gitleaks binary")
    args = parser.parse_args()

    try:
        gitleaks = shutil.which(args.gitleaks)
        if not gitleaks:
            raise ScanRefusedError(f"gitleaks not found ({args.gitleaks!r})")
        if not CONFIG.is_file():
            raise ScanRefusedError(f"config not found: {CONFIG}")
        base, head = resolve_commit(args.base), resolve_commit(args.head)
        count = commit_count(base, head)
        if count == 0:
            raise ScanRefusedError(f"the range {base[:12]}..{head[:12]} contains no commits")

        run_canary(gitleaks, tracked_directories())

        findings = run_gitleaks(gitleaks, ROOT, f"{base}..{head}")
        print(f"secret-scan: inspected {count} commit(s) in {base[:12]}..{head[:12]}")
    except ScanRefusedError as reason:
        print(f"secret-scan: REFUSED — {reason}", file=sys.stderr)
        return EXIT_REFUSED

    if findings:
        print(f"secret-scan: FAILED — {len(findings)} secret(s) found:", file=sys.stderr)
        for finding in findings:
            where = f"{finding.get('File')}:{finding.get('StartLine')}"
            commit = str(finding.get("Commit", ""))[:12]
            print(f"  ✗ {where} — {finding.get('RuleID')} in {commit}", file=sys.stderr)
        print(
            "Rotate every real secret listed: removing the commit does not un-publish it "
            "(SEC-003).",
            file=sys.stderr,
        )
        return EXIT_FINDINGS
    print("secret-scan: OK — no secrets in the scanned commits")
    return EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main())
