#!/usr/bin/env python3
"""Generate ecosystem host configuration and documentation from ecosystem.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_manifest(root: Path) -> dict[str, Any]:
    manifest = json.loads((root / "ecosystem.json").read_text(encoding="utf-8"))
    if manifest.get("schemaVersion") != 1 or not isinstance(manifest.get("packages"), dict):
        raise ValueError("ecosystem.json must use schemaVersion 1 and contain packages")
    return manifest


def server_entry(package: dict[str, str], *, vscode: bool = False) -> dict[str, object]:
    entry: dict[str, object] = {
        "command": "npx",
        "args": ["-y", f'{package["npm"]}@{package["version"]}', "mcp"],
    }
    return {"type": "stdio", **entry} if vscode else entry


def render_json(value: object) -> str:
    return json.dumps(value, indent=2) + "\n"


def render_toml(packages: dict[str, dict[str, str]]) -> str:
    blocks = []
    for name, package in packages.items():
        blocks.append(
            f'[mcp_servers.{name}]\ncommand = "npx"\n'
            f'args = ["-y", "{package["npm"]}@{package["version"]}", "mcp"]'
        )
    return "\n\n".join(blocks) + "\n"


def render_docs(manifest: dict[str, Any]) -> str:
    packages = manifest["packages"]
    rows = []
    for name, package in packages.items():
        rows.append(
            f'| [`{name}`]({package["repository"]}) | `{package["npm"]}@{package["version"]}` '
            f'| {package["role"]} | {package["credentials"]} | '
            f'[Docs]({package["documentation"]}) |'
        )
    table = "\n".join(rows)
    return f"""# Ecosystem

This is the canonical compatibility and ownership map for the Mule agent toolkit. The current
bundle is `mule-skills@{manifest["bundleVersion"]}`; its MCP dependencies are pinned exactly so an
installation is reproducible.

| Project | Exact package | Owns | Credentials | Reference |
| ------- | ------------- | ---- | ----------- | --------- |
{table}

## Ownership boundaries

- **mule-lint owns engineering standards.** Best-practice guides, source classifications,
  executable lint rules, rule profiles, and their MCP resources are maintained together there.
- **mule-build owns local delivery mechanics.** It validates, tests, packages, runs, publishes, and
  releases without redefining source-quality standards.
- **anypoint-connect owns authorized platform evidence and mutations.** It exposes the current
  Anypoint state; it does not encode project conventions.
- **mule-skills owns composition.** Skills decide which evidence and tools a workflow needs, while
  referring to mule-lint standards instead of copying them.

```mermaid
flowchart TD
    Skills["mule-skills<br/>workflow and compatibility hub"] --> Lint["mule-lint<br/>standards and static analysis"]
    Skills --> Build["mule-build<br/>validation and delivery"]
    Skills --> Connect["anypoint-connect<br/>authorized runtime evidence"]
    Lint --> Project["Mule project"]
    Build --> Project
    Connect --> Platform["Anypoint Platform"]
```

## Version management

Tool repositories release independently. A successful tool release sends a repository dispatch to
this repository. Automation updates `ecosystem.json`, regenerates host configuration and this page,
runs validation, and opens a pull request. A maintainer reviews and merges that PR; no dependency
event auto-merges or releases `mule-skills`.

Each tool repository needs a `MULE_SKILLS_DISPATCH_TOKEN` Actions secret backed by a fine-grained
token or GitHub App installation that has **Contents: write** on `Avinava/mule-skills`. If the secret
is absent, the release completes with a warning and the same update can be started manually from the
`Propose ecosystem pin update` workflow.

The generator is deterministic:

```bash
python3 tools/generate_ecosystem.py --check
```

To prepare a pin update locally:

```bash
python3 tools/update_ecosystem.py mule-lint 1.26.0
```

Release a new `mule-skills` minor version when skills, compatibility policy, host configuration, or
the user-facing bundle changes. A dependency-only compatible pin refresh can be a patch release.
"""


def generated_files(root: Path, manifest: dict[str, Any]) -> dict[Path, str]:
    packages = manifest["packages"]
    generic = {name: server_entry(package) for name, package in packages.items()}
    vscode = {name: server_entry(package, vscode=True) for name, package in packages.items()}
    return {
        root / ".mcp.json": render_json({"mcpServers": generic}),
        root / "install/hosts/mcp.json": render_json({"mcpServers": generic}),
        root / "install/hosts/vscode/mcp.json": render_json({"servers": vscode}),
        root / "install/hosts/codex/config.toml": render_toml(packages),
        root / "docs/ecosystem.md": render_docs(manifest),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        outputs = generated_files(root, load_manifest(root))
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"ecosystem generation failed: {exc}", file=sys.stderr)
        return 2

    stale = []
    for path, expected in outputs.items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                stale.append(path.relative_to(root).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")

    if stale:
        print("generated ecosystem files are stale: " + ", ".join(stale), file=sys.stderr)
        return 1
    print("ecosystem generated files: current" if args.check else "ecosystem files generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
