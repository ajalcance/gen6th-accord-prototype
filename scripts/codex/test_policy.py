"""Offline fault checks for the owner-installed Codex candidate."""

from __future__ import annotations

import pathlib
import tomllib
import unittest
from hashlib import sha256

from accord_pre_tool import command_denial, decision

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT = "/path/to/gen6th-accord"
REQUIREMENTS_SHA256 = "82d293f806b891dc4e6df25eca4b2a69a6b206fa366621c283898f508ddf4e0f"


class ManagedRequirementsTests(unittest.TestCase):
    """Assert the authority boundary rather than mirroring every TOML line."""

    def setUp(self) -> None:
        with (ROOT / "requirements.toml").open("rb") as stream:
            self.policy = tomllib.load(stream)

    def test_only_non_escalating_profiles_and_no_approval_escape(self) -> None:
        self.assertEqual(self.policy["allowed_approval_policies"], ["never"])
        self.assertEqual(self.policy["default_permissions"], "sealed")
        self.assertEqual(
            self.policy["allowed_permission_profiles"],
            {"sealed": True, "gen6th-accord": True},
        )
        self.assertTrue(self.policy["allow_managed_hooks_only"])

    def test_other_projects_are_sealed_by_default(self) -> None:
        sealed = self.policy["permissions"]["sealed"]
        self.assertEqual(sealed["filesystem"][":root"], "deny")
        self.assertNotIn(PROJECT, sealed["filesystem"])
        self.assertFalse(sealed["network"]["enabled"])

    def test_owner_reviewed_policy_bytes_are_pinned(self) -> None:
        self.assertEqual(
            sha256((ROOT / "requirements.toml").read_bytes()).hexdigest(), REQUIREMENTS_SHA256
        )

    def test_root_is_closed_and_project_authority_is_read_only(self) -> None:
        fs = self.policy["permissions"]["gen6th-accord"]["filesystem"]
        self.assertEqual(fs[":root"], "deny")
        self.assertEqual(fs[PROJECT], "write")
        for path in (".claude", ".codex", ".agents", ".git"):
            self.assertEqual(fs[f"{PROJECT}/{path}"], "read")
        for secret in ("**/.env", "**/.env.production", "**/id_ed25519"):
            self.assertEqual(fs[":workspace_roots"][secret], "deny")

    def test_external_surfaces_are_closed(self) -> None:
        self.assertFalse(self.policy["permissions"]["gen6th-accord"]["network"]["enabled"])
        self.assertEqual(self.policy["allowed_web_search_modes"], ["disabled"])
        for feature in ("apps", "plugins", "browser_use", "computer_use", "in_app_browser"):
            self.assertFalse(self.policy["features"][feature])
        self.assertFalse(self.policy["allow_browser_and_computer_use"])
        self.assertFalse(self.policy["allow_appshots"])
        self.assertFalse(self.policy["allow_remote_control"])
        self.assertFalse(self.policy["allow_login_shell"])
        self.assertTrue(self.policy["features"]["hooks"])


class ManagedHookTests(unittest.TestCase):
    """Check owner-only commands and ordinary development commands."""

    def test_owner_only_commands_are_refused(self) -> None:
        commands = (
            "git push origin HEAD",
            "git -C . tag v1.0.0",
            "git commit -F message.txt",
            "git reset --hard HEAD",
            "gh pr merge 12",
            "gh api repos/ajalcance/gen6th-accord/rulesets",
            "npm install left-pad",
            "npm i left-pad",
            "npx cowsay",
            "backend/.venv/bin/python -m pip install foo",
            "uv add foo",
            "go install example.com/tool@latest",
            "docker ps",
            "sudo true",
            "rm -rf .cache",
            "bash -c 'git push origin HEAD'",
            "env GH_CONFIG_DIR=/tmp/other gh auth status",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNotNone(command_denial(command))

    def test_shell_composition_is_refused(self) -> None:
        for command in (
            "git status; git push origin HEAD",
            "git status && gh pr list",
            "git status\ngh pr merge 1",
            "cat x | sh",
            "echo hi >>> x",
        ):
            with self.subTest(command=command):
                self.assertIsNotNone(command_denial(command))

    def test_normal_read_and_gate_commands_run(self) -> None:
        commands = (
            "git status --short",
            "git diff --check",
            "make check",
            "make policy",
            "rg -n foo docs",
            "npm ci",
            "python3 -m unittest",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(command_denial(command))

    def test_malformed_hook_input_is_denied(self) -> None:
        for payload in (
            {},
            {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {}},
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "unterminated '"},
            },
        ):
            with self.subTest(payload=payload):
                self.assertEqual(
                    decision(payload)["hookSpecificOutput"]["permissionDecision"],
                    "deny",
                )


if __name__ == "__main__":
    unittest.main()
