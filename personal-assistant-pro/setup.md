# Personal Assistant Pro — Setup Guide

Welcome. This agent uses external services that need one-time admin configuration. Walk through each section below; when everything works, ask the agent to call its `complete_setup` tool to remove this file from auto-loaded context.

## 1. Google Workspace OAuth (`google-workspace`)

The Workspace MCP gives the agent access to Gmail, Calendar, Contacts, and Drive on a per-user basis. Each user authorizes their own Google account — the platform stores per-user OAuth tokens, not a shared service account.

**Admin setup (one-time, platform-wide):**

1. In Google Cloud Console, create a new OAuth 2.0 Client ID (type: Web application).
2. Add the authorized redirect URI shown on `/admin/credentials/google` in the dashboard (or use the deep-link the agent suggests on first request).
3. Copy the client_id + client_secret into the platform settings page (`Admin → Credentials → Google OAuth`).

**Per-user authorization (each user does this once):**

1. Ask the agent something that needs Gmail or Calendar (e.g. *"What's on my calendar today?"*).
2. The agent will reply with an authorization link — open it, sign in, grant access.
3. The token is stored encrypted in the platform's per-user credential store; the agent automatically picks it up on the next request.

## 2. Google Maps API key (`google-maps`)

The Maps MCP uses Google Places + Directions. It needs **one** API key (admin-owned, billed to the admin's Google Cloud project).

1. In Google Cloud Console, enable: Places API (New), Directions API, Geocoding API.
2. Create an API key, restrict it to your platform's domain (HTTP referrers).
3. Set it in `Admin → MCP Servers → google-maps → Instances` — create an instance with the key, tick "Assign to all agents" or scope it to this agent only.

A typical month of light personal usage stays inside Google's free tier.

## 3. Phone calls (`phone-mcp`)

Phone calls need either FreePBX (self-hosted) or Twilio.

**FreePBX path:**

1. Configure a SIP trunk for outbound calling in FreePBX.
2. Note the AMI host + port + secret.
3. Set them in `Admin → Voice → AMI Configuration`.

**Twilio path:**

1. Create a Twilio account, get an Account SID + Auth Token + phone number.
2. Set them in `Admin → MCP Servers → phone-mcp → Instances`.

## 4. Caller agent (optional but recommended)

The caller agent makes the actual outbound call and negotiates with the business while keeping a question-and-answer channel back to this assistant.

1. The platform ships a `caller` internal agent (slug `caller`) at install time — verify it exists in `Admin → Agents`.
2. Make sure your Voice Server (`voice/`) is running and connected (the AudioSocket bridge).

## 5. Location awareness (`location-mcp`)

Reads the user's GPS via the dashboard. No admin setup required — the location MCP just needs a session WS bridge that comes in for free with the dashboard. Test by asking the agent *"Where am I?"* from the dashboard.

## When you're done

Tell the agent **"setup is complete"**. The agent will call `complete_setup` on `agent-config-mcp`, which removes this file from `config/context/` so it stops auto-loading into context (and saves tokens on every future turn).
