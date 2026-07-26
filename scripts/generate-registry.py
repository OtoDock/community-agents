#!/usr/bin/env python3
"""Generate registry.json for OtoDock/community-agents.

Walks every ``<slug>/agent.json``, validates the manifest fields, and
emits a top-level ``registry.json`` summary that the platform's catalog
endpoint serves.

Usage:
    python3 scripts/generate-registry.py             # write registry.json
    python3 scripts/generate-registry.py --check     # fail if stale
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "registry.json"

REQUIRED_AGENT_JSON_FIELDS = {"slug", "display_name", "version"}
SLUG_REGEX = re.compile(r"^[a-z][a-z0-9-]{1,38}[a-z0-9]$")
HEX_COLOR_REGEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_agent_json(slug_dir: Path) -> dict:
    p = slug_dir / "agent.json"
    if not p.is_file():
        raise ValueError(f"{slug_dir.name}: missing agent.json")
    data = _read_json(p)
    missing = REQUIRED_AGENT_JSON_FIELDS - data.keys()
    if missing:
        raise ValueError(f"{slug_dir.name}: agent.json missing fields {sorted(missing)}")
    if data["slug"] != slug_dir.name:
        raise ValueError(
            f"{slug_dir.name}: agent.json slug '{data['slug']}' must match folder name"
        )
    if not SLUG_REGEX.fullmatch(data["slug"]):
        raise ValueError(f"{slug_dir.name}: invalid slug")
    color = data.get("color", "")
    if color and not HEX_COLOR_REGEX.fullmatch(color):
        raise ValueError(f"{slug_dir.name}: invalid color {color!r}")
    return data


def _validate_mcps_json(slug_dir: Path) -> list[dict]:
    p = slug_dir / "mcps.json"
    if not p.is_file():
        raise ValueError(f"{slug_dir.name}: missing mcps.json")
    data = _read_json(p)
    required = data.get("required") or []
    if not isinstance(required, list):
        raise ValueError(f"{slug_dir.name}: mcps.json 'required' must be a list")
    for idx, raw in enumerate(required):
        if not isinstance(raw, dict) or not raw.get("name"):
            raise ValueError(
                f"{slug_dir.name}: mcps.json required[{idx}] must have a name"
            )
    return required


def _validate_skills_json(slug_dir: Path) -> list[dict]:
    p = slug_dir / "skills.json"
    if not p.is_file():
        return []
    data = _read_json(p)
    required = data.get("required") or []
    if not isinstance(required, list):
        raise ValueError(f"{slug_dir.name}: skills.json 'required' must be a list")
    for idx, raw in enumerate(required):
        if not isinstance(raw, dict) or not raw.get("name"):
            raise ValueError(
                f"{slug_dir.name}: skills.json required[{idx}] must have a name"
            )
    return required


def _require_persona_and_readme(slug_dir: Path, deprecated: bool) -> None:
    """Persona-file transition rule (platform 1.4 renamed prompt.md →
    agent.md): non-deprecated templates ship BOTH names, byte-identical —
    pre-1.4 platforms hard-require prompt.md while 1.4+ prefers agent.md.
    Deprecated (frozen) templates only need the name their era used.
    Drop the dual requirement once pre-1.4 installs stop mattering."""
    if not (slug_dir / "README.md").is_file():
        raise ValueError(f"{slug_dir.name}: missing README.md")
    agent_md = slug_dir / "agent.md"
    prompt_md = slug_dir / "prompt.md"
    if deprecated:
        if not (agent_md.is_file() or prompt_md.is_file()):
            raise ValueError(f"{slug_dir.name}: missing persona file")
        return
    for f in (agent_md, prompt_md):
        if not f.is_file():
            raise ValueError(
                f"{slug_dir.name}: missing {f.name} (non-deprecated templates "
                "ship agent.md AND prompt.md, byte-identical, during the "
                "1.3.x transition)"
            )
    if agent_md.read_bytes() != prompt_md.read_bytes():
        raise ValueError(
            f"{slug_dir.name}: agent.md and prompt.md differ — they must be "
            "byte-identical copies"
        )


def _summarize(slug_dir: Path) -> dict:
    """Build one registry entry from one template directory."""
    agent_json = _validate_agent_json(slug_dir)
    required_mcps = _validate_mcps_json(slug_dir)
    required_skills = _validate_skills_json(slug_dir)
    _require_persona_and_readme(
        slug_dir, bool(agent_json.get("deprecated", False)),
    )
    return {
        "slug": agent_json["slug"],
        "display_name": agent_json["display_name"],
        "description": agent_json.get("description", ""),
        "long_description_url": f"./{slug_dir.name}/README.md",
        "color": agent_json.get("color", "#6B7280"),
        "version": agent_json["version"],
        "category": agent_json.get("category", "productivity"),
        # Visibility mode (collaborative × default_scope). Shown in the install
        # UI so an operator knows how the agent relates to users before install.
        "collaborative": bool(agent_json.get("collaborative", True)),
        "default_scope": agent_json.get("default_scope", "user"),
        "tags": agent_json.get("tags") or [],
        "author": agent_json.get("author", "OtoDock"),
        "author_url": agent_json.get("author_url", "https://github.com/OtoDock"),
        "license": agent_json.get("license", "Apache-2.0"),
        "icon_url": f"./{slug_dir.name}/icon.png"
        if (slug_dir / "icon.png").is_file()
        else None,
        "readme_url": f"./{slug_dir.name}/README.md",
        "manifest_url": f"./{slug_dir.name}/agent.json",
        "required_mcps": required_mcps,
        "required_skills": required_skills,
        "has_triggers": (slug_dir / "triggers.json").is_file(),
        "has_tasks": (slug_dir / "tasks.json").is_file(),
        "has_notifications": (slug_dir / "notifications.json").is_file(),
        "has_setup": (slug_dir / "setup.md").is_file(),
        "has_user_setup": (slug_dir / "user-setup.md").is_file(),
        "has_context": (slug_dir / "context").is_dir(),
        "platform_min_version": agent_json.get("platform_min_version", "0.4.0"),
        "deprecated": bool(agent_json.get("deprecated", False)),
        "deprecation_note": agent_json.get("deprecation_note"),
    }


def build_registry() -> dict:
    agents = []
    for child in sorted(REPO_ROOT.iterdir()):
        if not child.is_dir():
            continue
        if child.name in (".git", ".github", "scripts", "node_modules", "venv"):
            continue
        if not (child / "agent.json").is_file():
            continue
        try:
            agents.append(_summarize(child))
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(2)
    return {
        "registry_version": "1",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platform_min_version": "0.4.0",
        "agents": agents,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true",
        help="Fail with exit code 1 if registry.json is stale",
    )
    args = parser.parse_args()

    registry = build_registry()

    if args.check:
        if not REGISTRY_PATH.is_file():
            print("registry.json missing", file=sys.stderr)
            return 1
        current = _read_json(REGISTRY_PATH)
        # Drop the timestamp before comparing — it ticks every run.
        current_no_ts = {k: v for k, v in current.items() if k != "updated_at"}
        new_no_ts = {k: v for k, v in registry.items() if k != "updated_at"}
        if current_no_ts != new_no_ts:
            print(
                "registry.json is stale — run scripts/generate-registry.py",
                file=sys.stderr,
            )
            return 1
        return 0

    REGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {REGISTRY_PATH} with {len(registry['agents'])} agent(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
