# Codex permissions on this Mac

Owner runbook for ADR-0021. These files are separate from Claude Code's `.claude/` controls.

## What the reviewed change contains

- The managed default is sealed. After installation, the owner selects `gen6th-accord` in Codex.
- `scripts/codex/requirements.toml` is the owner-installed, Mac-wide requirements source.
- `scripts/codex/accord_pre_tool.py` is the root-owned managed Bash hook.
- `scripts/codex/probe.py` is a live positive and negative control. It never prints the canary.
- `scripts/codex/test_policy.py` and `tests/guards/test_codex_policy.py` fail on policy drift.

## Owner installation, after reviewing and merging the policy PR

Run in the **Mac Terminal**, outside Codex. The block refuses to overwrite an existing managed
policy and requires a clean clone of the reviewed files. It changes Codex on the whole Mac; other
repositories use the sealed profile until given a separate reviewed profile. It does not modify
Claude Code. The user may need to quit the Codex desktop app before installing.

```bash
cd "/path/to/gen6th-accord"
set -euo pipefail
test "$(git branch --show-current)" = main
test -z "$(git status --porcelain)"
test ! -e /etc/codex/requirements.toml
python3 - <<'PY'
import re
import subprocess
version = subprocess.check_output(['codex', '--version'], text=True)
match = re.search(r'(\d+)\.(\d+)', version)
assert match and tuple(map(int, match.groups())) >= (0, 138), version
print('Supported Codex version:', version.strip())
PY
python3 scripts/codex/test_policy.py
backend/.venv/bin/ruff check scripts/codex/*.py tests/guards/test_codex_policy.py --config ruff-harness.toml
sudo install -d -o root -g wheel -m 0755 /etc/codex/hooks
sudo install -o root -g wheel -m 0644 scripts/codex/accord_pre_tool.py /etc/codex/hooks/accord_pre_tool.py
sudo install -o root -g wheel -m 0644 scripts/codex/requirements.toml /etc/codex/requirements.toml
cmp scripts/codex/requirements.toml /etc/codex/requirements.toml
cmp scripts/codex/accord_pre_tool.py /etc/codex/hooks/accord_pre_tool.py
test ! -e "$HOME/accord-codex-sandbox-canary"
printf 'harmless sandbox probe\n' > "$HOME/accord-codex-sandbox-canary"
trap 'rm -f "$HOME/accord-codex-sandbox-canary"' EXIT
codex sandbox --include-managed-config -P gen6th-accord -C "$PWD" /usr/bin/python3 scripts/codex/probe.py
```

Expected: nine offline tests pass, both installed files compare equal, and all eight live probe lines
say `PASS`. A failure means the managed profile is not verified. Do not switch routine work to
it until the failure is understood. If Codex cannot start, use the Mac Terminal to move the
managed file out of `/etc/codex/` and report the exact error; do not change its rules silently.

The live probe tests a positive project read and write, readable Git metadata, unreadable home
canary, protected `.claude/` and `.git/` writes, denied outside write and denied direct network.
It cannot prove every action in Apps, MCP or hosted tools, so those surfaces are disabled.

## Codex desktop settings

1. Quit and reopen Codex after installation so managed requirements are reloaded.
2. Open this saved project. The managed default is `sealed` until you select the project profile.
3. In the task composer, open the permissions selector. Select the custom
   `gen6th-accord` profile. `Full access` and other unlisted profiles should be unavailable.
4. In Settings, leave Browser Use, Computer Use, Appshots and device remote control off. The
   managed policy also disables them; a UI switch must not restore them.
5. In Settings > Apps, leave the GitHub connection unused for this project. The managed policy
   turns Apps off. A future read-only integration needs its own review and live action test.
6. In a new task, use `/status` to confirm the effective profile, approval policy and writable
   roots. Use the Terminal probe above to verify actual filesystem and network enforcement.

`allowed_approval_policies = ["never"]` means the agent cannot request an unsandboxed retry.
The owner runs exceptional actions in their own Terminal after review. The app's permission
selector may describe this as a custom profile rather than an approval mode.

## Other projects

The managed default is sealed. Review each other project, add a distinct exact-path profile to
the managed source, test it, and install the new
version as an owner action. Its own Claude or other client policy can remain in place.
Use [`codex-sandbox-template.md`](codex-sandbox-template.md) for the copyable parameter list
and project-specific adaptation steps.
