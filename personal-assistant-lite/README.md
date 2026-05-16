# Personal Assistant Lite

Bundled, out-of-the-box assistant. Ships with every fresh OtoDock install — auto-created on first boot by the platform startup hook.

## What it does

- Schedules tasks and reminders.
- Creates and edits Office documents (docx, xlsx, pptx) and PDFs.
- Generates and edits images on-device.
- Reads and writes files in the agent's workspace.
- Fires webhook triggers from external systems.
- Coordinates multi-agent meetings.

## What it doesn't do

- No Google Workspace (Gmail, Calendar, Contacts).
- No Google Maps / places search.
- No phone-call automation.
- No live location awareness.

For any of those, install the **personal-assistant-pro** community template alongside this one (Browse Community Agents from the dashboard). The two coexist — no replacement needed.

## Bundled MCPs

- `task-mcp` — scheduled tasks
- `notifications-mcp` — user-facing notifications
- `meetings-mcp` — multi-agent meetings
- `display-mcp` — image display in chat
- `file-tools` — Office docs + image edit (Docker MCP; folder is `file-tools-mcp/` but manifest name is `file-tools`)
- `image-gen-mcp` — local image generation
- `triggers-mcp` — webhook triggers
- `mcps-mcp` — browse / request community MCPs from chat
- `agent-config-mcp` — agent self-configures (rename, color, default model)

All MCPs in this list are bundled with the platform — no admin install action required on a fresh deploy.

## How to upgrade to Pro

1. Open the dashboard → Agents → "Browse Community Agents".
2. Find `personal-assistant-pro` in the catalog.
3. Click Install. The cascade walks through Google Workspace OAuth + Google Maps API key + phone-call setup (`setup.md`).
4. Both agents coexist. Delete the lite version once Pro is configured if you want a single agent.
