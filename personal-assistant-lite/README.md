# Personal Assistant Lite

Bundled, out-of-the-box assistant. Ships with every fresh OtoDock install — auto-created on first boot by the platform startup hook.

## What it does

- Schedules tasks and reminders.
- Creates and edits Office documents (docx, xlsx, pptx) and PDFs.
- Reads and writes files in the agent's workspace.
- Remembers your preferences and facts across conversations (persistent memory).
- Fires webhook triggers from external systems.
- Coordinates multi-agent meetings.

## What it doesn't do

- No Google Workspace (Gmail, Calendar, Contacts).
- No image generation.
- No web browsing / browser automation.

A full **Personal Assistant Pro** template covering those is coming to Browse Community Agents.

## Bundled MCPs

- `schedules-mcp` — scheduled tasks
- `notifications-mcp` — user-facing notifications
- `meetings-mcp` — multi-agent meetings
- `display-mcp` — image display in chat
- `file-tools` — Office docs + image edit (Docker MCP; folder is `file-tools-mcp/` but manifest name is `file-tools`)
- `triggers-mcp` — webhook triggers
- `mcps-mcp` — browse / request community MCPs from chat
- `agent-config-mcp` — agent self-configures (rename, color, default model)
- `memory-mcp` — persistent memory across conversations

All MCPs in this list are bundled with the platform — no admin install action required on a fresh deploy.
