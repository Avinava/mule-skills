#!/usr/bin/env python3
"""Generate ecosystem host configuration and documentation from ecosystem.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


NODE_REQUIREMENT_RE = re.compile(r"^>=(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def load_manifest(root: Path) -> dict[str, Any]:
    manifest = json.loads((root / "ecosystem.json").read_text(encoding="utf-8"))
    if manifest.get("schemaVersion") != 1 or not isinstance(manifest.get("packages"), dict):
        raise ValueError("ecosystem.json must use schemaVersion 1 and contain packages")
    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, dict) or set(capabilities) != set(manifest["packages"]):
        raise ValueError("capabilities must describe exactly the pinned packages")
    for name, expected in capabilities.items():
        if not isinstance(expected, dict) or set(expected) != {"tools", "resources", "examples"}:
            raise ValueError(f"{name}: capability keys must be tools, resources and examples")
        if not isinstance(expected["tools"], dict) or not expected["tools"]:
            raise ValueError(f"{name}: capability tools must be a non-empty object")
        for tool, fields in expected["tools"].items():
            if not isinstance(tool, str) or not tool or not isinstance(fields, dict):
                raise ValueError(f"{name}: invalid tool capability")
            if any(not isinstance(key, str) or not key or value not in {"string", "boolean", "number", "array", "object"} for key, value in fields.items()):
                raise ValueError(f"{name}: invalid input capability")
        examples = expected["examples"]
        if not isinstance(examples, dict) or set(examples) != set(expected["tools"]):
            raise ValueError(f"{name}: every expected tool needs representative inputs")
        if any(not isinstance(values, list) or not values or any(not isinstance(value, dict) for value in values) for values in examples.values()):
            raise ValueError(f"{name}: representative inputs must be non-empty lists of objects")
        if not isinstance(expected["resources"], list) or any(not isinstance(uri, str) or not uri for uri in expected["resources"]):
            raise ValueError(f"{name}: resources must be URI strings")
    return manifest


def parse_node_requirement(value: str) -> tuple[int, int, int]:
    match = NODE_REQUIREMENT_RE.fullmatch(value)
    if not match:
        raise ValueError(f"unsupported Node.js requirement {value!r}; expected >=X.Y.Z")
    return tuple(int(part) for part in match.groups())


def shared_node_requirement(packages: dict[str, dict[str, str]]) -> str:
    floor = max(parse_node_requirement(package["node"]) for package in packages.values())
    return ">=" + ".".join(str(part) for part in floor)


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
    shared_node = shared_node_requirement(packages)
    rows = []
    for name, package in packages.items():
        rows.append(
            f'| [`{name}`]({package["repository"]}) | `{package["npm"]}@{package["version"]}` '
            f'| `{package["node"]}` | {package["role"]} | {package["credentials"]} | '
            f'[Docs]({package["documentation"]}) |'
        )
    table = "\n".join(rows)
    capability_rows = []
    for name, expected in manifest["capabilities"].items():
        tools = ", ".join(f"`{tool}` ({', '.join(fields)})" for tool, fields in expected["tools"].items())
        resources = ", ".join(f"`{uri}`" for uri in expected["resources"]) or "Discovery only"
        capability_rows.append(f"| `{name}` | {tools} | {resources} |")
    capability_table = "\n".join(capability_rows)
    return f"""# Ecosystem

This is the canonical compatibility and ownership map for the Mule agent toolkit. The current
bundle is `mule-skills@{manifest["bundleVersion"]}`; its MCP dependencies are pinned exactly so an
installation is reproducible.

| Project | Exact package | Node.js | Owns | Credentials | Reference |
| ------- | ------------- | ------- | ---- | ----------- | --------- |
{table}

Node.js `{shared_node}` satisfies the complete bundle. Node.js 24 LTS is recommended for a new
installation.

## Ownership boundaries

- **mule-lint owns engineering standards.** Best-practice guides, source classifications,
  executable lint rules, rule profiles, and their MCP resources are maintained together there.
- **mule-build owns local delivery mechanics.** It validates, tests, packages, runs locally, and
  prepares versioned and tagged artifacts without redefining source-quality standards.
- **anypoint-connect owns authorized platform evidence and mutations.** It exposes the current
  Anypoint state and performs explicitly approved Exchange publishing or runtime deployment; it does
  not encode project conventions.
- **mule-skills owns composition.** Skills decide which evidence and tools a workflow needs, while
  referring to mule-lint standards instead of copying them.

```mermaid
flowchart TD
    Skills["mule-skills<br/>workflow and compatibility hub"] --> Lint["mule-lint<br/>standards and static analysis"]
    Skills --> Build["mule-build<br/>check, test, package, version, tag"]
    Skills --> Connect["anypoint-connect<br/>publish, deploy, runtime evidence"]
    Lint --> Project["Mule project"]
    Build --> Project
    Connect --> Platform["Anypoint Platform"]
```

## Machine-checked capability boundaries

These minimum tool/input/resource expectations come from `ecosystem.json`, alongside the
unchanged release pins. The executable smoke checks discovery against them; a missing tool,
input property/type, newly required argument, rejected representative enum value or public
resource fails compatibility. Samples cover minimal and common inputs without invoking build or
platform tools. This is bounded discovery validation, not a full JSON Schema validator or an
authenticated integration test. Extra capabilities remain allowed.
This is a consumer conformance fixture, not a second registry of server implementations.

| Owner | Required tools (input fields) | Required resources |
| --- | --- | --- |
{capability_table}

The owning tool documents its schemas and semantics. This hub links to those docs instead of
copying rule implementations or platform/build policies. Report-v1 remains capability-detected:
local-source validation does not assert support in an older pinned release. No runtime package
coupling is introduced between the tools.

## Execution evidence and artifact handoff

Skills consume the canonical lint report only when the installed executable supports it:
`structuredContent.schemaVersion`, `execution`, and `findings` are top-level MCP fields;
`--format report-json` is the CLI equivalent. Legacy `--format json` remains a flat array.
An `incomplete` or `no-files` execution never establishes a passed scan, even under quiet output,
baselines, or permissive gates. A `complete` scan covers only its recorded scope and enabled rules.
Missing or unknown scope must be disclosed. Older releases without this contract leave completeness
unverified; do not interpret zero findings or quality ratings as proof of completion.

The build secure-reference precondition checks a narrow property-reference policy. It does not
prove encryption correctness, runtime secret safety, or a full security assessment. Build and
connector remain independent of a mandatory lint dependency; skills coordinate separately configured
checks and report each outcome.

For artifact handoff, retain the exact JAR path, embedded Maven group/artifact/version, and SHA-256
when available. Display names and timestamped filenames are not coordinates. The connector's
`expectedSha256` protects the reviewed bytes when supported. Preview the destination and explicitly
approved coordinate mappings, preserve confirmation/authentication safeguards, then use returned
publication coordinates for deployment. Publication success is not runtime verification. If an older
release lacks required identity/digest support, disclose the gap instead of silently dropping it.

## Executable compatibility checks

Run the default check against the exact published pins in `install/hosts/mcp.json`:

```bash
python3 tools/compatibility_smoke.py
```

This starts each server with a temporary home and no inherited application/npm credentials,
preserving only configured proxy and CA transport settings for registry access. It initializes MCP and
lists tools/resources. The connector receives synthetic client placeholders and a loopback base URL
solely to satisfy its configuration prerequisite; it never logs in. Only public lint resources and synthetic local lint fixtures are read; no
build, authenticated Anypoint, publication, deployment, or other mutation tools are called. The first
run downloads pinned npm packages with lifecycle scripts disabled, so registry access is required.
Discovery success is not an authenticated platform integration test.

For coordinated development, build each of the three repositories first, then point to their common
parent directory without changing published pins:

```bash
python3 tools/compatibility_smoke.py --source-root <source-root> --require-report-v1
```

`--require-report-v1` rejects legacy-only results. A report-v1 server must prove complete, malformed,
and no-files states, top-level structured output, CLI/MCP finding parity, and legacy flat JSON.
The default mode reports the older release's limited evidence explicitly; it never treats legacy
text as verified execution completeness. Local-source success does not certify the published pins.

## Version management

Tool repositories release independently. A successful tool release sends a repository dispatch to
this repository. Automation updates `ecosystem.json`, regenerates host configuration and this page,
runs structural and executable compatibility validation, and opens a pull request. A maintainer reviews and merges that PR; no dependency
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
python3 tools/update_ecosystem.py mule-lint {packages["mule-lint"]["version"]} \
  --node '{packages["mule-lint"]["node"]}'
```

Keep existing pins until a published release passes the executable check. Use
`--require-report-v1` before claiming that a proposed lint release provides the new report contract.

The pin-update workflow uses `GITHUB_TOKEN`. GitHub may hold the resulting pull-request checks
for maintainer approval; use **Approve workflows to run** on the proposed PR when shown, and wait
for its checks before merging. See [GitHub's workflow trigger documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
The proposal workflow's own validation is not a substitute for the PR's required checks.

The bundle version in `ecosystem.json` and the plugin manifest must agree. The marketplace uses
that plugin manifest; it does not introduce another independently versioned package. Source versions
and changelog entries can precede a GitHub release; do not create a tag merely to hide that distinction.
Tool package versions, this bundle version, and GitHub releases are separate release decisions.

Documentation follows the default branch through a strict Pages build independently of tool or
bundle tags. Manual Pages publication also requires the default branch. Pull-request documentation
checks do not deploy the site. Keep unpublished capabilities explicitly capability-detected until
published packages pass compatibility validation and the reviewed pin update is merged.

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
