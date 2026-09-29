# Personal Assistant

The default OtoDock assistant: scheduling and reminders, office documents,
file management, persistent memory, webhook automations, and multi-agent
meetings — everything works out of the box, no API keys or OAuth setup.

What it can do at any moment is defined by the tools attached to it (see
`mcps.json`); add more from the community catalog whenever you need another
capability — the agent itself can browse the catalog and request tools.

Ships with a short per-user onboarding (`user-setup.md`) that each new user
completes in their first chat.

On OtoDock 1.7 and later it also ships a personal **Home** app
(`user-apps/home/`): one page per user with the weather for their city and
their to-do list. It welcomes each user on their first visit and its "Set
up" button completes their onboarding without a chat; the assistant can
change the city and the list from a conversation, and the user can ask it to
change the page itself. Platforms before 1.7 install the assistant without
the app.

A full **Personal Assistant Pro** edition — Google Workspace, maps, phone
calls, browsing preconfigured — is coming to Browse Community Agents.
