# Reuse the Codex sandbox in another project

This is a copyable record of Gen6th Accord's **proposed** Codex settings (ADR-0021).
The source is [`scripts/codex/requirements.toml`](../../scripts/codex/requirements.toml),
the managed hook is [`scripts/codex/accord_pre_tool.py`](../../scripts/codex/accord_pre_tool.py),
and the installation procedure is [`codex-permissions.md`](codex-permissions.md).
PR [#50](https://github.com/ajalcance/gen6th-accord/pull/50) is awaiting GitHub CI and
owner installation. These settings are not yet verified as active on this Mac.

## Where each control lives

| Layer | Current location | What it controls |
| --- | --- | --- |
| Reviewed source | `scripts/codex/requirements.toml` | Versioned proposal and tests; a repository copy alone enforces nothing. |
| Managed Codex policy | `/etc/codex/requirements.toml` | Mac-wide limits, sealed default, and exact-path project profiles; owner installs it. |
| Managed Bash hook | `/etc/codex/hooks/accord_pre_tool.py` | Early refusal of direct owner-only shell commands; owner installs it. The OS sandbox remains the boundary. |
| Repository contract | `AGENTS.md` and `CLAUDE.md` | Instructions for agents; each other repository needs its own reviewed contract. |
| Repository gates | CI, branch rules, and guard tests | Independent checks that must be assessed in each repository. |

Codex 0.138.0 or later is required for managed permission-profile allowlists.
Keep each other project sealed until its exact path has a reviewed profile and a passing
live probe. Do not put a `default_permissions` selector in that project's
`.codex/config.toml` before the managed profile exists: Codex may fail to load.

## Mac-wide parameters from this project

These are the current values to carry forward in the **one** owner-managed requirements file.
They apply to all Codex projects on this Mac. Do not create a second copy of these tables
when adding a project profile.

```toml
allowed_approval_policies = ["never"]
allowed_approvals_reviewers = ["user"]
allowed_web_search_modes = ["disabled"]
default_permissions = "sealed"
allow_managed_hooks_only = true
allow_browser_and_computer_use = false
allow_appshots = false
allow_remote_control = false
allow_login_shell = false

[allowed_permission_profiles]
"sealed" = true
"gen6th-accord" = true

[features]
apps = false
plugins = false
hooks = true
browser_use = false
browser_use_external = false
browser_use_full_cdp_access = false
computer_use = false
in_app_browser = false

[permissions.sealed]
description = "No project source access until an owner-selected profile applies"

[permissions.sealed.filesystem]
":root" = "deny"
":minimal" = "read"
":tmpdir" = "write"
":slash_tmp" = "write"

[permissions.sealed.network]
enabled = false

[hooks]
managed_dir = "/etc/codex/hooks"

[[hooks.PreToolUse]]
matcher = "^Bash$"

[[hooks.PreToolUse.hooks]]
type = "command"
command = "/usr/bin/python3 /etc/codex/hooks/accord_pre_tool.py"
timeout = 10
statusMessage = "Checking owner-only commands"
```

The hook refuses direct shell commands for remote Git changes, selected dependency
installation verbs, privileged tools, and similar owner actions. It is advisory for
indirect commands; the filesystem and network profile, CI, and branch rules remain necessary.
`network.enabled = false` closes network access for sandboxed commands. The separate
feature and web-search settings close the other surfaces named above.

## Exact-path profile to adapt for another repository

In the same managed requirements file, add `"new-project" = true` **inside the existing**
`[allowed_permission_profiles]` table. Then add this new profile. Replace every `new-project`
name and every `/ABSOLUTE/PATH/TO/NEW-PROJECT` path with the reviewed values for that
repository. Do not reuse the Gen6th Accord path or give one project access to a sibling.
For reference, this repository uses the profile name `gen6th-accord` and the exact root
`/path/to/gen6th-accord`.

```toml
[permissions.new-project]
description = "Only this project's source and bounded scratch are writable"

[permissions.new-project.filesystem]
":root" = "deny"
":minimal" = "read"
":tmpdir" = "write"
":slash_tmp" = "write"
"~/.gitconfig" = "read"
"~/.config/git" = "read"
"/ABSOLUTE/PATH/TO/NEW-PROJECT" = "write"
"/ABSOLUTE/PATH/TO/NEW-PROJECT/.claude" = "read"
"/ABSOLUTE/PATH/TO/NEW-PROJECT/.codex" = "read"
"/ABSOLUTE/PATH/TO/NEW-PROJECT/.agents" = "read"
"/ABSOLUTE/PATH/TO/NEW-PROJECT/.git" = "read"

[permissions.new-project.filesystem.":workspace_roots"]
"**/.env" = "deny"
"**/.env.local" = "deny"
"**/.env.development" = "deny"
"**/.env.staging" = "deny"
"**/.env.test" = "deny"
"**/.env.production" = "deny"
"**/id_rsa" = "deny"
"**/id_ed25519" = "deny"
"**/id_ecdsa" = "deny"
"**/*.p12" = "deny"
"**/*.pfx" = "deny"
"**/*.jks" = "deny"
"**/*.gpg" = "deny"

[permissions.new-project.network]
enabled = false
```

Review the new repository for additional credential paths and add exact denials as needed.
If it lacks `.claude/` or `.agents/`, retaining those read-only paths protects them if
they are later created. Keep `.git/` read-only so the agent cannot change Git history,
hooks, or configuration through the sandbox. The owner handles commits and pushes.

## Apply and verify for each project

1. Review the other repository's secret locations, build tools, CI, branch protection,
   agent instructions, and any existing Claude or other-client policy. Keep those files.
2. Add the new profile to the versioned managed-policy source through a reviewed PR.
   Adapt the policy tests and a harmless positive/negative live probe to the new path.
3. After review, the owner updates the **single** root-owned
   `/etc/codex/requirements.toml`; do not overwrite it with only the new project's
   snippet or remove the Gen6th Accord profile. Verify installed bytes against the
   reviewed source. Keep the managed hook installed.
4. Restart Codex. In the new project's task composer, select its custom permission
   profile. Leave Browser Use, Computer Use, Appshots, remote control, Apps, and plugins
   disabled. Use `/status` to inspect the effective profile and writable roots.
5. Run a live probe from the owner's Mac Terminal. Require a successful project read
   and scratch write, and refusals for home canary reads, policy and Git writes,
   writes outside the project, and direct network access. Treat any unexpected access
   or probe error as a failed rollout.

Copying this Markdown file or a repository `.codex/config.toml` does **not** install the
Mac-wide policy. The tests prove the proposed source; only the owner-installed file
and live probe establish the active local boundary. This profile also does not
reproduce another repository's CI, branch rules, or external-service identity.

## Official Codex references

- [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- [Config basics](https://learn.chatgpt.com/docs/config-file/config-basic)
- [Codex security](https://learn.chatgpt.com/docs/security)
