# Contributing an agent template

An OtoDock agent template is a directory with one required manifest (`agent.json`), one system prompt (`prompt.md`), a required-MCPs declaration (`mcps.json`), and a README. Optional files seed scheduled tasks, webhook triggers, scheduled notifications, a setup guide, and auto-context docs.

## Folder layout

```
<slug>/
├── agent.json              # required — agent manifest
├── prompt.md               # required — agent system prompt (becomes config/prompt.md)
├── mcps.json               # required — required MCPs (with optional skill lists)
├── README.md               # required — shown in the Browse Agents detail dialog
├── tasks.json              # optional — scheduled tasks (cron / interval)
├── triggers.json           # optional — webhook-fired triggers
├── notifications.json      # optional — scheduled user-facing notifications
├── setup.md                # optional — copied to config/docs/setup.md; agent removes via complete_setup
├── docs/                   # optional — auto-loaded into config/docs/
│   └── *.md / *.txt
└── icon.png                # optional — 256×256 PNG; falls back to color + first letter
```

## `agent.json`

```json
{
  "schema_version": "1",
  "slug": "executive-assistant",
  "display_name": "Executive Assistant",
  "description": "Calendar, email, and document drafting.",
  "color": "#3B82F6",
  "version": "1.0.0",
  "default_model": "",
  "default_layer": "claude-code-cli",
  "execution_paths": ["claude-code-cli", "codex-cli", "direct-llm"],
  "internal": false,
  "category": "productivity",
  "tags": ["calendar", "email"],
  "author": "Your Handle",
  "author_url": "https://github.com/your-handle",
  "license": "Apache-2.0",
  "platform_min_version": "0.4.0"
}
```

### Field reference

| Field | Required | Description |
|---|---|---|
| `schema_version` | yes | Currently `"1"`. |
| `slug` | yes | Lowercase + hyphens, 3–40 chars, matches the folder name. |
| `display_name` | yes | Human-readable label shown in the picker. |
| `description` | yes | One-liner (max 160 chars). |
| `color` | yes | Accent color (`#RRGGBB`). |
| `version` | yes | Semver. Bump when prompt or required MCPs change. |
| `default_model` | yes | Empty string = the platform's default. |
| `default_layer` | yes | One of `claude-code-cli`, `codex-cli`, `direct-llm`. These are the registered layer paths in `core/session_manager._LAYERS`. Note `codex-cli` (with the `-cli` suffix), not `codex`. |
| `execution_paths` | yes | Non-empty subset of the above. Must include `default_layer`. **Order matters at install time**: `execution_paths[0]` becomes the primary default — keep your `default_layer` first. |
| `internal` | no | Always `false` for community templates. |
| `category` | no | `productivity` / `infrastructure` / `creative` / `research` / `customer-support` / `experimental`. |
| `tags` | no | Lowercase, searchable. |
| `author` | no | Maintainer handle. |
| `author_url` | no | Profile link. |
| `license` | no | SPDX identifier. |
| `platform_min_version` | no | Minimum platform version for compat. |

## `mcps.json`

```json
{
  "required": [
    {"name": "task-mcp"},
    {"name": "workspace-mcp", "min_version": "1.0.0", "skills": ["email", "calendar"]},
    {"name": "google-maps"}
  ]
}
```

- `name` — MCP slug (custom or community).
- `min_version` (optional) — minimum installed version required.
- `skills` (optional) — default-enabled skills. Empty list = all defaults from the MCP's own manifest.

The platform pre-validates that every required MCP is in the platform's local installs OR the community-mcps catalog before creating the agent. If anything's missing AND not in any catalog, install hard-fails — list only MCPs that exist somewhere.

## `tasks.json` (optional)

```json
{
  "tasks": [
    {
      "slug": "daily-summary",
      "description": "Daily summary",
      "scope": "user",
      "prompt": "Produce a 5-bullet summary of today's events.",
      "schedule": {"type": "cron", "cron": "0 18 * * *"},
      "default_state": "paused",
      "auto_create_for_new_users": true,
      "roles": null
    }
  ]
}
```

| Field | Required | Description |
|---|---|---|
| `slug` | yes | Lowercase + hyphens. Used as the idempotency key per (agent, user). |
| `description` | yes | Shown in the agent's tasks list. |
| `scope` | yes | `user` (per-user) or `agent` (one row, all managers see). |
| `prompt` | yes | Fired when the schedule triggers. |
| `schedule.type` | yes | `cron` or `interval` (or `run_at` for one-shot). |
| `schedule.cron` / `schedule.interval_seconds` / `schedule.run_at` | yes | Per type. |
| `default_state` | no | `paused` (default for tasks) or `active`. |
| `auto_create_for_new_users` | no | Default `true`. Only meaningful for `scope=user`. |
| `roles` | no | If set (e.g. `["manager"]`), only users with those roles get this user-scope item. |

## `triggers.json` (optional)

Same shape as tasks but no `schedule` field — triggers fire via webhook. Default to `paused` because the upstream system needs the trigger URL connected before activating makes sense.

## `notifications.json` (optional)

```json
{
  "notifications": [
    {
      "slug": "monthly-cleanup",
      "title": "Time to clean up your workspace",
      "body": "Check old files and tidy up.",
      "deep_link": "/agents/{agent_slug}/workspace",
      "scope": "user",
      "schedule": {"type": "cron", "cron": "0 9 1 * *"},
      "default_state": "active",
      "auto_create_for_new_users": true
    }
  ]
}
```

`title` max 80 chars; `body` max 500 chars. `{agent_slug}` substitution supported in `deep_link`.

## `setup.md` (optional)

A markdown file that walks the manager through post-install configuration (OAuth flows, API keys, etc.). Copied to the new agent's `config/docs/setup.md` so it auto-loads into the agent's context. When configuration is verified done, the manager tells the agent "setup is complete" and the agent calls its `complete_setup` tool (from `agent-config-mcp`) which deletes the file. Subsequent chat turns no longer pay the token cost.

## `docs/` (optional)

Anything in this folder is copied recursively to the new agent's `config/docs/` and auto-loads as context (markdown + text files, 1 MB per file, 5 MB total cap).

## PR checklist

1. Slug + folder name match.
2. `version` matches between manifest and (if shipped) any change-history.
3. Every MCP in `mcps.json` exists in OtoDock/community-mcps OR is a platform-bundled custom MCP (`task-mcp`, `notifications-mcp`, `meetings-mcp`, `display-mcp`, `file-tools-mcp`, `image-gen-mcp`, `triggers-mcp`, `mcps-mcp`, `agent-config-mcp`, `phone-mcp`, `location-mcp`).
4. Run `python3 scripts/generate-registry.py` and commit the regenerated `registry.json`.
5. README explains what the agent does, what setup is needed, who would use it.

The CI workflow runs `generate-registry.py --check` on every PR and rejects stale registries.
