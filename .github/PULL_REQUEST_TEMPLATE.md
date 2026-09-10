<!-- Thanks for the pull request. One template per PR. CONTRIBUTING.md has the folder layout, the manifest reference and the checklist this list mirrors. -->

## Template

<!-- Which agent template, new or updated, and what changes. For an update: the version bump (the persona or the required MCPs changed) and why. -->

## How it was tested

<!-- The OtoDock version you installed it on, the engine it ran on, and a chat or task that shows it doing its job. -->

## Checklist

- [ ] `python3 scripts/generate-registry.py` was run and `registry.json` is committed.
- [ ] The slug and the folder name match; `agent.json` follows CONTRIBUTING.md and pins no engine or model.
- [ ] Every MCP in `mcps.json` uses its canonical name and exists in community-mcps or among the platform's bundled MCPs.
- [ ] `agent.md` and `prompt.md` are byte-identical.
- [ ] `README.md` explains what the agent does, what setup it needs and who would use it.
- [ ] No `.env` file, key or credential anywhere in the folder.
- [ ] I have reviewed every line I submit, generated or not.
