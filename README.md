# OtoDock Community Agents

Catalog of community-contributed agent templates for the [OtoDock](https://github.com/OtoDock) platform. Templates here are listed in `registry.json` and installed via the platform's Browse Community Agents UI.

## What's an agent template?

A pre-built agent: prompt, MCP requirements, optional scheduled tasks, optional triggers, optional notifications, optional setup guide, optional auto-context docs. Manager picks one from the catalog, the platform creates the agent, cascades the required MCPs (installing missing ones via admin approval), seeds the tasks/triggers/notifications, copies the setup guide, and the agent is ready.

## Available agents

| Slug | Description |
|---|---|
| `personal-assistant-lite` | Out-of-the-box assistant — tasks, reminders, documents, images. No external API keys. Ships bundled with OtoDock; also installable from this catalog for re-deployment or extra copies. |
| `personal-assistant-pro` | Full personal assistant — Gmail, Calendar, Contacts, Drive, maps, phone calls, docs, images. Requires admin OAuth + API keys (setup guide included). |

## Adding a new template

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the manifest schema and PR process.

## License

Apache-2.0. See [`LICENSE`](./LICENSE).
