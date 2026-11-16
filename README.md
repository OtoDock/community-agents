# OtoDock Community Agents

Catalog of community-contributed agent templates for the [OtoDock](https://github.com/OtoDock) platform. Templates here are listed in `registry.json` and installed via the platform's Browse Community Agents UI.

## What's an agent template?

A pre-built agent: a prompt and its MCP requirements. It may also ship:

- scheduled tasks, triggers and notifications
- ready-made mini-app dashboards
- skill packages
- setup guides, agent-wide and per-user
- auto-context docs

A manager picks one from the catalog. Then the platform:

- creates the agent
- cascades the required MCPs, and installs missing ones via admin approval
- seeds the tasks, triggers, notifications and dashboards
- copies the setup guides

The agent is then ready, dashboards included. They are pinned and visible on
the agent's home from the first minute.

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
