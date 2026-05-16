# Personal Assistant Pro

Full-featured personal assistant template. Includes Google Workspace (Gmail, Calendar, Contacts, Drive), Google Maps for places + directions, phone-call automation for bookings and inquiries, image generation, document editing, and live location awareness.

Heavier than the bundled `personal-assistant-lite` (which ships out-of-the-box and needs no API keys). Install this template when you're ready to wire up the external services.

## What it does

- **Email + Calendar + Contacts + Drive** via Google Workspace OAuth (per-user tokens).
- **Places search + directions** via Google Maps.
- **Phone calls** for restaurant bookings, doctor appointments, etc. — uses a caller sub-agent to negotiate while keeping a question channel back to the assistant.
- **Document creation** (docx, xlsx, pptx, pdf) and **image generation/editing** locally.
- **Live GPS** for "where am I" / "what's near me" through the dashboard.
- **Multi-agent meetings** for delegation when a task needs cross-agent input.

## What you need to set up

After install, the agent's `config/docs/setup.md` walks the manager through the four configuration sections:

1. Google Workspace OAuth (client_id + client_secret in admin settings; per-user authorization on first request).
2. Google Maps API key (one platform-wide instance).
3. Phone call backend — FreePBX or Twilio.
4. (Optional) verify the `caller` agent exists and the Voice Server is up.

Ask the agent for help with each. When everything is verified, tell the agent **"setup is complete"** — it'll call `complete_setup` and the setup guide stops auto-loading into context.

## Bundled MCPs

| MCP | Required for | Setup needed |
|---|---|---|
| `task-mcp` | Scheduled tasks | No |
| `notifications-mcp` | Push notifications | No |
| `meetings-mcp` | Multi-agent meetings | No |
| `display-mcp` | Image display in chat | No |
| `file-tools` | Office docs + image edit | No |
| `image-gen-mcp` | Image generation | No |
| `triggers-mcp` | Webhook triggers | No |
| `mcps-mcp` | Browse / request more MCPs from chat | No |
| `agent-config-mcp` | Agent self-config | No |
| `google-workspace` | Gmail / Calendar / Contacts / Drive | Yes — OAuth client + per-user auth |
| `google-maps` | Places + directions | Yes — API key |
| `phone-mcp` | Phone calls | Yes — FreePBX or Twilio |
| `location-mcp` | GPS awareness | No (dashboard WS bridge) |

## Coexistence with PA-lite

PA-pro lives alongside PA-lite (different slugs) — no replacement needed. After PA-pro is configured and you're happy with it, you can delete PA-lite from `Admin → Agents` if you want a single agent.

## Author

OtoDock — <https://github.com/OtoDock>
