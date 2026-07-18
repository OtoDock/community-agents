# Security Policy

This repository holds community agent templates (personas, config, context
files) that OtoDock users install as ready-made agents. A template is trusted
instruction text, so payloads hidden in one are a real attack surface.

## Reporting a vulnerability

Please report vulnerabilities **privately** — do not open a public issue for
anything security-sensitive.

- **Preferred:** GitHub private vulnerability reporting — go to this
  repository's **Security** tab → **Report a vulnerability**. Reports land
  directly with the maintainer, privately.
- **Email:** [security@otodock.io](mailto:security@otodock.io)

You'll get an acknowledgment within **72 hours** and a status update as the
report is triaged. Confirmed issues are fixed ahead of feature work, with
credit to the reporter (if you'd like it).

This catalog is rolling — reports are always assessed against the current
`main` branch. Vulnerabilities in the OtoDock **platform** itself belong on
[OtoDock/oto-dock](https://github.com/OtoDock/oto-dock/security) instead.

There is no paid bounty program at this time — just fast fixes, honest
credit, and our thanks.

## Scope

Especially interesting to us:

- Templates containing hidden instructions that exfiltrate data or steer an
  agent against its user (prompt-injection payloads)
- Unsafe defaults in a template's config (over-broad scopes, permissive
  execution settings)
