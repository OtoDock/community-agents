# Contributing an agent template

An OtoDock agent template is a directory. It holds:

- one required manifest (`agent.json`)
- one persona (`agent.md`), plus a byte-identical `prompt.md` copy during the pre-1.4 transition
- a required-MCPs declaration (`mcps.json`)
- a README

Optional files seed scheduled tasks, webhook triggers, scheduled notifications and standalone skill packages. They also seed ready-made mini-app dashboards, folder apps (shared and per-member), agent checks, setup guides (agent-wide and per-user) and auto-context files.

## Folder layout

```
<slug>/
├── agent.json              # required — agent manifest
├── agent.md                # required — the persona (becomes config/agent.md)
├── prompt.md               # required for now — byte-identical copy of agent.md (pre-1.4 platforms read this name)
├── skills.json             # optional — standalone skill packages: {"required": [{"name", "skills"?}]}
├── mcps.json               # required — required MCPs (with optional skill lists)
├── README.md               # required — shown in the Browse Agents detail dialog
├── tasks.json              # optional — scheduled tasks (cron / interval)
├── triggers.json           # optional — webhook-fired triggers
├── notifications.json      # optional — scheduled user-facing notifications
├── setup.md                # optional — agent-wide setup guide, copied to config/context/setup.md; a manager completes it once via complete_setup
├── user-setup.md           # optional — per-user onboarding, copied to config/user-setup.md and seeded into each user's context/ on attach; each user completes it via complete_setup(scope="user")
├── dashboards.json         # optional (platform 1.5+) — mini-app dashboards to seed + pin at install
├── dashboards/             # optional (platform 1.5+) — the dashboards' *.html files
│   └── *.html
├── apps/                   # optional (platform 1.7+) — shared folder apps, one folder per app
│   └── <slug>/             #   app.json + client/index.html (+ server/, blueprint.json)
├── user-apps/              # optional (platform 1.7+) — per-member folder apps, one folder per app
│   └── <slug>/
├── checks/                 # optional (platform 1.7+) — agent checks, one folder per check
│   └── <name>/             #   check.json (+ the script it names)
├── context/                # optional — auto-loaded into config/context/
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
| `slug` | yes | Lowercase + hyphens, 3 to 40 chars, matches the folder name. |
| `display_name` | yes | Human-readable label shown in the picker. |
| `description` | yes | Short summary shown on the catalog card, 1 to 3 sentences. Long text gets truncated in the grid view. |
| `color` | yes | Accent color (`#RRGGBB`). |
| `version` | yes | Semver. Bump when prompt or required MCPs change. |
| `internal` | no | Always `false` for community templates. |
| `category` | no | `productivity` / `infrastructure` / `creative` / `research` / `customer-support` / `experimental`. |
| `tags` | no | Lowercase, searchable. |
| `author` | no | Maintainer handle. |
| `author_url` | no | Profile link. |
| `license` | no | SPDX identifier. |
| `platform_min_version` | no | Minimum platform version for compat. |
| `default_scope` | no | `"user"` (default) or `"agent"`. With `collaborative`, selects the agent's **visibility mode**: how chats/tasks are scoped between per-user and shared. |
| `collaborative` | no | Boolean, default `true`. `collaborative: false` + `default_scope: "user"` = Personal-only mode, which the personal-assistant templates use. Each user gets their own private chats/tasks. `collaborative: false` + `default_scope: "agent"` = Shared-only (service agents). |
| `default_for_new_users` | no | Object `{enabled: bool, role: "viewer"\|"editor"\|"manager"}`. When enabled, the platform attaches every newly-signed-up user to this agent. See below the table. |
| `core_mcps` | no | `"all"` (default) or `"none"`. Every platform grants a newly installed agent its own core toolkit (memory, notifications, schedules, …) automatically. Templates never list core tools in `mcps.json`. Set `"none"` to opt a single-purpose agent out entirely: it then gets only what `mcps.json` asks for. Platforms below 1.4.0 ignore this field. |

**`default_for_new_users`.** When `enabled` is `true`, the OtoDock platform
attaches every newly-signed-up user to this agent with the chosen per-agent
role. Platform admins can override the manifest choice per-install via the
agent's Setup tab.

Most templates should leave this unset. Only set it if your agent is designed
to be a default-baseline experience for every user. Recommended role:

- `"viewer"` for personal-assistant-style templates: read-only on the shared
  workspace, writable in the user's own dir.
- `"editor"` for templates with a shared knowledge base the team is meant to
  contribute to.
- `"manager"` only for templates where every user is expected to administer
  the agent.

> **Manifests are engine-agnostic.** Don't pin an AI engine or model. There is
> no `default_layer` / `execution_paths` / `default_model` field.
>
> At install time the platform auto-enables the first engine connected on both
> the platform and the installer's account: Claude Code CLI, then Codex CLI. The
> model defaults to Auto. The installer can change the engine afterwards in the
> agent's Config tab.

## `mcps.json`

```json
{
  "required": [
    {"name": "schedules-mcp"},
    {"name": "google-workspace", "min_version": "1.0.0"},
    {"name": "file-tools", "skills": ["file-tools-usage"]},
    {"name": "google-maps"}
  ]
}
```

- `name`: the MCP slug **as declared in the MCP's `manifest.json::name` field**. This is NOT necessarily the folder name. See the naming gotcha below.
- `min_version` (optional): advisory minimum MCP version. Accepted by the schema and recorded, but not currently enforced at install time.
- `skills` (optional): a subset of the MCP's **manifest-declared skill IDs** (`manifest.json::skills[].id`) to enable for this agent. Omit the field (or pass an empty list) to enable all of the MCP's default skills. That's the right choice for almost every template. IDs that don't exist in the MCP's manifest are silently ignored. An MCP that declares no `skills` in its manifest has nothing to select, so don't invent entries for it.

Before it creates the agent, the platform pre-validates every required MCP. It checks that each one is in the platform's local installs OR the [community-mcps catalog](https://github.com/OtoDock/community-mcps). If anything's missing AND not in any catalog, install hard-fails. So list only MCPs that exist somewhere.

### MCP name vs folder name: a common gotcha

The MCP `name` field in `manifest.json` is the canonical slug used by the platform. The agent_mcps DB rows, the runtime lookups and your `mcps.json::required[].name` all use it. It is sometimes different from the folder name. As of the v1 launch, these mismatches exist, and contributors must use the manifest `name`, NOT the folder name:

| Folder | Canonical `name` |
|---|---|
| `mcps/custom/file-tools-mcp/` | `file-tools` |
| `mcps/community/google-workspace/` (was `workspace-mcp/`) | `google-workspace` |
| `mcps/community/ha-mcp/` | `home-assistant` |

If your template's `mcps.json` references a folder name that doesn't match the manifest name, the platform's preflight check will report the MCP as "Not installed; NOT in any catalog". It does so even though the MCP is clearly running. Check `manifest.json::name` when in doubt.

### Bundled custom MCPs available to every template

These ship with the platform and are always available. List them in `mcps.json::required` if your template needs them. No admin install is needed:

`schedules-mcp`, `notifications-mcp`, `meetings-mcp`, `display-mcp`, `file-tools` (folder: `file-tools-mcp/`), `image-gen-mcp`, `image-search-mcp`, `transcribe-mcp`, `triggers-mcp`, `mcps-mcp`, `agent-config-mcp`, `memory-mcp`, `phone-mcp`, `location-mcp`.

Anything else must come from the community-mcps catalog (`google-workspace`, `google-maps`, `home-assistant`, `ssh-server`, `prometheus`, etc.). The platform will queue an admin install-request for it as part of the cascade.

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

Same shape as tasks, but no `schedule` field: triggers fire via webhook. Default to `paused`, because the upstream system needs the trigger URL connected before activating makes sense.

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

`title` max 80 chars, `body` max 500 chars. `{agent_slug}` substitution supported in `deep_link`. The `schedule` block takes the same three types as tasks (`cron` / `interval` / `run_at`). Notifications also accept the per-user targeting fields tasks have:

- `auto_create_for_new_users` (default `true`, `scope=user` only)
- `roles` (e.g. `["manager"]` to seed only for users holding those per-agent roles)

## `dashboards.json` (optional, platform 1.5+)

Ship a ready-made **mini-app dashboard** with your agent. It is pinned and visible the moment the install finishes, and the agent's own scheduled tasks can refresh it later.

```json
{
  "dashboards": [
    {
      "slug": "team-board",
      "title": "Team Board",
      "file": "board.html",
      "visibility": "agent",
      "auto_pin_for_new_users": true
    }
  ]
}
```

| Field | Required | Description |
|---|---|---|
| `slug` | yes | 1 to 40 chars of `[a-z0-9-]`, starting alphanumeric. The pinned app's identity: re-pins by the agent update it in place. |
| `title` | no | Tab title shown to users. Defaults to the slug. |
| `file` | yes | Bare `*.html` filename under `dashboards/` (no subpaths). |
| `visibility` | no | `"agent"` (default): ONE shared dashboard every user of the installed agent sees. `"user"`: each user gets their own personal copy. Must be a visibility the template's **mode** offers. An `"agent"` dashboard on a Personal-only template (`collaborative: false` + `default_scope: "user"`) fails validation, as does `"user"` on Shared-only. |
| `auto_pin_for_new_users` | no | Default `true`. For `"user"` visibility: users attached to the agent **after** install also get their copy pinned automatically. |

Rules and behavior:

- **At most 4 dashboards per template, ≤1 MB each.** `{agent_slug}` in the HTML is substituted with the installed agent's slug.
- **Display-only on day one.** Seeded dashboards carry no action buttons, so there is nothing for the user to approve at install. The installed agent can later re-pin the same slug with a declared-actions manifest (buttons, live data feeds). That re-pin then goes through the normal user-approval flow.
- **Who gets what**: `"agent"` visibility seeds one shared pin + the file in the agent's shared `workspace/apps/`. `"user"` visibility seeds the installer's personal copy immediately, and each later joiner's copy on attach. Users can always hide a shared dashboard from their own strip without affecting the team.
- **Authoring**: the HTML renders in the same sandboxed iframe as agent-pinned mini-apps. Write a self-contained body fragment. A **Tailwind + mobile-responsive layout is required**: dashboards are seen daily on phones. The sandbox has no external network access, so keep assets inline.
- Platforms before 1.5 ignore `dashboards.json` entirely: their loader drops unknown files. So a template that ships dashboards still installs cleanly on older installs, just without the pins.

## `apps/` and `user-apps/` (optional, platform 1.7+)

Ship a **folder app**, the same thing an agent deploys with `deploy_app`. That is a page, optionally a Bun server with its own SQLite, and a manifest of what the page may do. The platform deploys it at install, and for every member who joins later.

```
apps/board/                    # ONE shared copy: every member of the installed agent opens it
├── app.json                   # the manifest: title, actions, egress, files, handlers, requires…
├── blueprint.json             # optional — {"format": 1, "tasks": [...], "triggers": [...]}
├── client/index.html          # the page (required)
└── server/index.ts            # optional — the Bun server (with /_health)
user-apps/home/                # ONE copy PER MEMBER: each member gets their own app and data
├── app.json
├── blueprint.json             # optional — adds "auto_create_for_new_users" and "roles"; "triggers" one per member
└── client/index.html
```

| Where | What the installer gets | What a later member gets |
|---|---|---|
| `apps/<slug>/` | one shared copy, deployed once for the agent | the same copy |
| `user-apps/<slug>/` | their own copy | their own copy, deployed on attach when `blueprint.json` says `auto_create_for_new_users` (default `true`). `roles`, e.g. `["manager"]`, narrows it. |

`blueprint.json` is the file `export_app` writes beside an app. It holds:

- `format`: always `1`.
- `tasks`: the tasks the app's `fire_task` buttons run. At most 16, each `{slug, description, prompt}`, with a slug of `^[a-z][a-z0-9_-]{0,39}$` and a prompt of 1 to 8000 chars. A button's `task` names the slug. The platform seeds one task per copy and points the button at it.
- For `user-apps/`, the two targeting fields above.
- On platform 1.7 and later, `triggers`: at most 8, each `{slug, handler, description}`. The slug is lowercase letters, digits and dashes, `<app slug>-<slug>` within 64 characters. `handler` is one of the manifest's `handlers.on_trigger` names.

The platform seeds one trigger per copy, aimed at the copy. For a `user-apps/` app it is owned by each member: their own address `/v1/webhooks/user/<username>/<app slug>-<slug>`, fired with their own API key. For an `apps/` app it is the agent's. So an app can wake on a webhook of its member's own. The member finds the address on the app's settings panel.

An app with handlers is each member's to approve, and its trigger waits with the copy until they do.

Everything else about an app is exactly the folder app of the platform's app-authoring skill: `app.json` keys, the `/_health` route, `window.otodock.*` in the page, egress, secrets. Author and test it as an agent's own app first (`deploy_app`, `screenshot_app`), then copy the folder in.

Rules the platform enforces (validation fails otherwise):

- **Visibility follows the template's mode.** A Personal-only template (`collaborative: false` + `default_scope: "user"`) ships `user-apps/` only. A Shared-only one ships `apps/` only. A collaborative template may ship both, and a shared app and a personal app may talk to each other through bindings.
- **At most 4 apps per template.** Slugs are 1 to 40 chars of `[a-z0-9-]`, starting alphanumeric, and unique across both folders. No dotfiles, `.env`, `data/`, `node_modules` or links inside an app folder. A release never takes them: the registry generator refuses them, and the platform's loader drops the first three and refuses a link. At most 2 MB per file, 32 MB and 500 files per app. `client/index.html` is required.
- **A per-user app never takes an inbound hook**: a public route aims at one row, and a hook has no member. Its `files` prefixes stay under the owner's tree, never `knowledge/`. It may wake on a trigger. Declare it in `blueprint.json`'s `triggers`, and the platform seeds one per copy, owned by its member (above).
- **Leave `deploy_requires_approval` unset.** The install decides who approves (below).
- An `mcp_tool` action may only name an MCP the template requires. That is one in `mcps.json`, or in the app's own `requires.mcps`, which the registry joins to the template's.

**Consent.** The install dialog shows every app the template ships, and one checkbox. It shows each app's buttons, feeds, methods, egress, files, blueprint tasks, and the triggers it comes with.

Ticked, the installer's consent approves the shared copies. It also approves the personal copies of an app whose manifest carries nothing that acts as the member. That means no `mcp_tool` or `fire_task` buttons, no `files.write`, and no handlers, steps, inbound hooks or secrets.

Of those personal copies the consent approves every member's copy when the installer is a platform admin. Otherwise it approves the installer's own copy. A creator's consent reaches no other member's card: those members approve theirs.

A personal app that does carry one of those is marked **each member approves their own copy** in the dialog. It lands waiting for approval on the member's card, whoever installs.

Unticked, everything waits for approval on its card and nothing is lost.

The consent is recorded with the signatures the registry carries, so what a member gets later is exactly what the installer saw. It is re-checked at every later seed. A template whose app changed, or an installer who has since lost the right to approve, approves no new copy.

**Write the template's prose conditionally.** A platform before 1.7 ignores these folders (its loader drops unknown files) and still installs the template. So `platform_min_version` need not rise for an app alone. But then the persona and the setup guides must not promise the app unconditionally: say "on OtoDock 1.7 or later" where they mention it. The README names no version, because such a line goes stale. Raise `platform_min_version` to `1.7.0` instead when the agent makes no sense without the app.

## `checks/` (optional, platform 1.7+)

Ship the **checks** the agent runs on its own work. They are the documents `set_check` takes, one folder per check, named after it:

```
checks/coding/
├── check.json                 # {"name": "coding", "description": …, "mandatory": true, "script": {"run": "lint.sh"}, "judge": {…}}
└── lint.sh                    # the script it names, beside it
```

- At most 8 per template.
- The folder name is the check's `name`: lowercase, digits, `-` and `_`.
- A `script.run` must be a UTF-8 file in the folder, at most 256 KB, never a link.
- A `handler.app` may name one of the template's own apps.

The platform validates the document with the checks' own validator when it loads the template. A bad document fails the install before anything is created. The install dialog lists each check with what consenting lets it run: a script in the agent's sandbox, a judge on a model, a handler in an app.

`mandatory: true` is a request. Consented, the check is installed mandatory. Unconsented, it is installed **offered**, and a manager makes it mandatory from the dashboard. The three shapes in the platform's `mcps/custom/checks-mcp/examples/` are the reference.

## `setup.md` (optional)

A markdown file that walks the manager through post-install configuration (OAuth flows, API keys, etc.). Copied to the new agent's `config/context/setup.md` so it auto-loads into the agent's context. When configuration is verified done, the manager tells the agent "setup is complete". The agent then calls its `complete_setup` tool (from `agent-config-mcp`), which deletes the file. Subsequent chat turns no longer pay the token cost.

## `user-setup.md` (optional, platform 1.4+)

Per-user onboarding. Copied to `config/user-setup.md` at install, and seeded into each user's `users/{u}/context/` when they are attached to the agent. So it auto-loads only into that user's own chats. The agent walks each user through it and calls `complete_setup` with scope `user`, which removes only that user's copy. Platforms before 1.4 ignore this file.

On platform 1.7 and later a per-member app can be that welcome instead. Such an app sits under `user-apps/`, reads the platform method `setup.status` and calls `setup.complete`. It shows the member a welcome page with a Setup button until they complete it. Then it shows its normal dashboard (the platform's app-authoring skill, "The setup page").

`setup.status` also names the agent (`display_name`, `description`). It grades every MCP the app's manifest names: its `requires.mcps` and the `mcp` of any tool button. For each it says whether it is enabled for the agent and connected for the member. It also says what would fix it (`fix`: `connect` / `admin`, with a `reason` in words). So a card can grey out where a tool is missing on that install.

Keep `user-setup.md` beside such an app for the chat path and for older platforms.

## `skills.json` (optional, platform 1.4+)

Standalone skill packages from [OtoDock/community-skills](https://github.com/OtoDock/community-skills), installed and assigned to the agent at install time. Same shape as `mcps.json`: `{"required": [{"name": "theme-factory", "skills": ["theme-factory"]}]}`. Omit `skills` to enable all of a package's skills.

A package in neither the platform nor the skills catalog fails the install before anything is created. A package not yet installed is installed inline when an admin installs the template. When a creator does, it is queued as an admin request, and the agent works meanwhile, minus that package. Platforms before 1.4 ignore this file.

## `context/` (optional)

Anything in this folder is copied recursively to the new agent's `config/context/` and auto-loads as context. It takes markdown + text files, 1 MB per file, with a 5 MB total cap.

## PR checklist

1. Slug + folder name match.
2. `version` matches between manifest and (if shipped) any change-history.
3. Every MCP in `mcps.json` uses the **canonical name**: the `manifest.json::name` field, not the folder name. It exists in [OtoDock/community-mcps](https://github.com/OtoDock/community-mcps) OR is a platform-bundled custom MCP (see "Bundled custom MCPs available to every template" above). See the "MCP name vs folder name" gotcha above.
4. Run `python3 scripts/generate-registry.py` and commit the regenerated `registry.json`. It carries each app's and check's signature, which is what an installer consents to.
5. README explains what the agent does, what setup is needed, who would use it.
6. A template that ships `apps/`, `user-apps/` or `checks/` was tried on a 1.7 platform. It was installed from a local catalog, the apps approved and opened, and a second member attached and given their copy.

The CI workflow runs `generate-registry.py --check` on every PR and rejects stale registries.
