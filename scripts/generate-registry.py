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
import hashlib
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
APP_SLUG_REGEX = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
CHECK_NAME_REGEX = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
APP_FOLDERS = (("apps", "agent"), ("user-apps", "user"))
MAX_APPS = 4
MAX_CHECKS = 8
NEVER_IN_AN_APP = ("node_modules", "data")
# What an installer's consent may never cover on a copy seeded for someone
# else (each member approves such a copy on their own card).
OWNER_ACTION_TYPES = {"mcp_tool", "fire_task"}
OWNER_METHODS = {"files.write"}
OWNER_BLOCKS = ("handlers", "steps", "inbound", "secrets")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Signatures — must stay byte-identical to the platform's
# proxy/storage/agents/template_sig.py (the prep gate proves it against the
# platform's loader): the install dialog consents to what this file says
# an app or a check is, and the installer approves the tarball's copy only
# when the two agree.
# ---------------------------------------------------------------------------

def _canonical(doc) -> str:
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _app_files(folder: Path, label: str) -> list[tuple[str, Path]]:
    """The files a release takes (the platform's ``walk_tree`` rule), as
    ``(relative path, file)`` sorted by path. A catalog app may not carry
    what a release drops: dotfiles, ``.env``, ``data/``, ``node_modules``,
    links — they are an error here, not a skip."""
    out: list[tuple[str, Path]] = []
    for root, dirs, files in os.walk(folder):
        root_p = Path(root)
        rel_root = root_p.relative_to(folder).as_posix()
        for d in sorted(dirs):
            if d.startswith(".") or d in NEVER_IN_AN_APP or (root_p / d).is_symlink():
                raise ValueError(f"{label}: {rel_root + '/' if rel_root != '.' else ''}{d} may not ship in an app")
        dirs.sort()
        for name in sorted(files):
            path = root_p / name
            if name.startswith(".") or path.is_symlink() or not path.is_file():
                raise ValueError(f"{label}: {rel_root + '/' if rel_root != '.' else ''}{name} may not ship in an app")
            out.append((f"{rel_root}/{name}" if rel_root and rel_root != "." else name, path))
    return out


def _tree_sha(files: list[tuple[str, Path]]) -> str:
    entries: dict[str, dict] = {}
    for rel, path in files:
        if rel == "app.json":
            continue
        data = path.read_bytes()
        entries[rel] = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
    return _sha256_text(json.dumps({"files": entries}, sort_keys=True, separators=(",", ":")))


def _template_app_sig(app_json, blueprint_json, tree: str) -> str:
    return _sha256_text(_canonical({"app_json": app_json, "blueprint": blueprint_json, "tree_sha": tree}))


def _check_sig(raw_doc: dict, script_sha256: str) -> str:
    return _sha256_text(_canonical({"doc": raw_doc, "script_sha256": script_sha256 or ""}))


def _needs_owner(doc: dict) -> bool:
    for a in doc.get("actions") or []:
        if not isinstance(a, dict):
            continue
        if a.get("type") in OWNER_ACTION_TYPES:
            return True
        if a.get("type") == "platform" and a.get("method") in OWNER_METHODS:
            return True
    for name in OWNER_BLOCKS:
        if doc.get(name):
            return True
    files = doc.get("files")
    return bool(isinstance(files, dict) and files.get("write"))


def _summarize_apps(slug_dir: Path) -> list[dict]:
    """The folder apps under ``apps/`` (shared) and ``user-apps/`` (one per
    member), with the documents the install dialog renders and the
    signature it consents to (CONTRIBUTING.md "apps/ and user-apps/")."""
    out: list[dict] = []
    seen: set[str] = set()
    for folder, visibility in APP_FOLDERS:
        root = slug_dir / folder
        if not root.is_dir():
            continue
        for d in sorted(p for p in root.iterdir() if p.is_dir()):
            if not (d / "app.json").is_file():
                continue
            label = f"{slug_dir.name}: {folder}/{d.name}"
            if d.is_symlink():
                raise ValueError(f"{label} is a link")
            if not APP_SLUG_REGEX.match(d.name):
                raise ValueError(f"{label}: the folder name must be 1-40 chars of [a-z0-9-]")
            if d.name in seen:
                raise ValueError(f"{label}: the slug is used by another app of this template")
            seen.add(d.name)
            app_json = _read_json(d / "app.json")
            if not isinstance(app_json, dict):
                raise ValueError(f"{label}/app.json must be an object")
            blueprint = None
            if (d / "blueprint.json").is_file():
                blueprint = _read_json(d / "blueprint.json")
                if not isinstance(blueprint, dict):
                    raise ValueError(f"{label}/blueprint.json must be an object")
            files = _app_files(d, label)
            if not any(rel == "client/index.html" for rel, _ in files):
                raise ValueError(f"{label}: client/index.html is missing")
            tree = _tree_sha(files)
            req = app_json.get("requires") or {}
            out.append({
                "slug": d.name,
                "title": str(app_json.get("title") or "").strip()[:80],
                "visibility": visibility,
                "app_json": app_json,
                "blueprint_json": blueprint or None,
                "tree_sha": tree,
                "sig": _template_app_sig(app_json, blueprint or None, tree),
                "owner_approval": visibility == "user" and _needs_owner(app_json),
                "requires_mcps": [str(n) for n in (req.get("mcps") or []) if isinstance(n, str)]
                if isinstance(req, dict) else [],
            })
            if len(out) > MAX_APPS:
                raise ValueError(f"{slug_dir.name}: at most {MAX_APPS} apps per template")
    return out


def _summarize_checks(slug_dir: Path) -> list[dict]:
    """The agent checks under ``checks/<name>/`` with what consenting to
    each lets run; the platform validates the documents themselves."""
    root = slug_dir / "checks"
    if not root.is_dir():
        return []
    out: list[dict] = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        if not (d / "check.json").is_file():
            continue
        label = f"{slug_dir.name}: checks/{d.name}"
        if not CHECK_NAME_REGEX.match(d.name):
            raise ValueError(f"{label}: the folder name is the check's name (lowercase, digits, - and _)")
        doc = _read_json(d / "check.json")
        if not isinstance(doc, dict) or doc.get("name") != d.name:
            raise ValueError(f"{label}: check.json must be an object whose name is the folder's")
        script_name = (doc.get("script") or {}).get("run") if isinstance(doc.get("script"), dict) else None
        script_sha = ""
        if script_name:
            script_path = d / str(script_name)
            if not script_path.is_file() or script_path.is_symlink():
                raise ValueError(f"{label}: the script {script_name} is not in the check's folder")
            script_sha = hashlib.sha256(script_path.read_bytes()).hexdigest()
        handler = doc.get("handler") if isinstance(doc.get("handler"), dict) else {}
        out.append({
            "name": d.name,
            "description": str(doc.get("description") or "")[:500],
            "sections": [s for s in ("schema", "script", "handler", "judge") if doc.get(s)],
            "applies": list(doc.get("applies") or ["chats", "tasks", "delegations"]),
            "mandatory": bool(doc.get("mandatory")),
            "script": str(script_name or ""),
            "handler_app": str(handler.get("app") or ""),
            "script_sha256": script_sha,
            "sig": _check_sig(doc, script_sha),
        })
        if len(out) > MAX_CHECKS:
            raise ValueError(f"{slug_dir.name}: at most {MAX_CHECKS} checks per template")
    return out


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
    apps = _summarize_apps(slug_dir)
    checks = _summarize_checks(slug_dir)
    # An app's own MCP needs join the template's, as the installer's
    # cascade sees them (COMMUNITY-AGENTS-REGISTRY.md).
    known = {m.get("name") for m in required_mcps}
    for a in apps:
        for name in a.pop("requires_mcps"):
            if name not in known:
                required_mcps.append({"name": name})
                known.add(name)
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
        # Folder apps and checks (platform 1.7+): the documents the install
        # dialog renders and the signatures it consents to.
        "has_apps": any(a["visibility"] == "agent" for a in apps),
        "has_user_apps": any(a["visibility"] == "user" for a in apps),
        "has_checks": bool(checks),
        "apps": apps,
        "checks": checks,
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
