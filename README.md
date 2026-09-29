# OtoDock Community Agents

Catalog of community-contributed agent templates for the [OtoDock](https://github.com/OtoDock) platform. Templates here are listed in `registry.json` and installed via the platform's Browse Community Agents UI.

## What's an agent template?

A pre-built agent: prompt, MCP requirements, optional scheduled tasks, optional triggers, optional notifications, optional ready-made mini-app dashboards (platform 1.5+), optional skill packages, optional setup guides (agent-wide and per-user), optional auto-context docs. Manager picks one from the catalog, the platform creates the agent, cascades the required MCPs (installing missing ones via admin approval), seeds the tasks/triggers/notifications/dashboards, copies the setup guides, and the agent is ready — dashboards included, pinned and visible on the agent's home from the first minute.

## Available agents

<!-- catalog:start -->
| Template | Version | What it is |
|----------|---------|------------|
| [personal-assistant](./personal-assistant/) | 3.1.2 | Your everyday assistant, ready out of the box |
<!-- catalog:end -->

## Adding a new template

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the manifest schema and PR process.

## License

Apache-2.0. See [`LICENSE`](./LICENSE).
