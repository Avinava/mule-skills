#!/usr/bin/env python3
"""Dependency-free structural validation for this reusable skill repository."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SIBLING_RE = re.compile(r"\.\./([a-z0-9][a-z0-9-]*)/")
PLACEHOLDER_RE = re.compile(r"<skills-root>/([a-z0-9][a-z0-9-]*)/")
PIN_RE = re.compile(r"@sfdxy(?:%2F|/)([a-z0-9-]+)@(\d+\.\d+\.\d+)")
NAV_ENTRY_RE = re.compile(r"^\s*(?:-\s*)?(?:[^:]+:\s*)?([A-Za-z0-9._/-]+\.md)\s*$")
READINESS_REFERENCE = "references/anypoint-readiness.md"
READINESS_SKILLS = ("mule-build", "mule-ops", "mule-review", "mule-troubleshooting")
ACCESS_STATES = (
    "Ready",
    "Not configured",
    "Not authenticated",
    "Environment not visible",
    "Not permitted",
    "Transient failure",
)
CLASS_NAMES = (
    "Class A — Value contracts",
    "Class B — Expression embedding",
    "Class C — Contract authority",
    "Class D — Failure disposition",
    "Class E — State and idempotency",
)


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, [f"{path}: missing or malformed YAML frontmatter"]

    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.startswith((" ", "\t")):
            findings.append(f"{path}: frontmatter must use simple top-level name/description fields")
            continue
        key, separator, value = line.partition(":")
        if not separator:
            findings.append(f"{path}: malformed frontmatter line: {line}")
            continue
        values[key.strip()] = value.strip().strip('"\'')

    unexpected = sorted(set(values) - {"name", "description"})
    if unexpected:
        findings.append(f"{path}: unexpected frontmatter keys: {', '.join(unexpected)}")
    for required in ("name", "description"):
        if not values.get(required):
            findings.append(f"{path}: missing non-empty {required}")
    return values, findings


def validate_skills(root: Path) -> list[str]:
    findings: list[str] = []
    for skill_path in sorted((root / "skills").glob("*/SKILL.md")):
        values, frontmatter_findings = parse_frontmatter(skill_path)
        findings.extend(frontmatter_findings)
        folder_name = skill_path.parent.name
        name = values.get("name", "")
        if name and (not NAME_RE.fullmatch(name) or len(name) > 64):
            findings.append(f"{skill_path}: invalid skill name: {name}")
        if name and name != folder_name:
            findings.append(f"{skill_path}: name {name!r} does not match folder {folder_name!r}")
        if len(values.get("description", "")) > 1024:
            findings.append(f"{skill_path}: description exceeds 1024 characters")
    return findings


def validate_local_links(root: Path) -> list[str]:
    findings: list[str] = []
    markdown_files = list(root.glob("*.md"))
    markdown_files.extend((root / "skills").rglob("*.md"))
    markdown_files.extend((root / "install").rglob("*.md"))
    markdown_files.extend((root / "docs").rglob("*.md"))

    for path in sorted(set(markdown_files)):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            target = target.strip().strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            relative_target = target.split("#", 1)[0]
            if not relative_target:
                continue
            resolved = (path.parent / relative_target).resolve()
            if not resolved.exists():
                findings.append(f"{path}: broken local link: {target}")
    return findings


def validate_alignment(root: Path) -> list[str]:
    findings: list[str] = []
    development = (root / "skills/mule-development/SKILL.md").read_text(encoding="utf-8")
    invariant_path = root / "skills/mule-development/references/invariant-classes.md"
    invariants = invariant_path.read_text(encoding="utf-8")
    checklist = (root / "skills/mule-development/resources/post-development-checklist.md").read_text(
        encoding="utf-8"
    )

    for class_name in CLASS_NAMES:
        if class_name not in development:
            findings.append(f"skills/mule-development/SKILL.md: missing canonical {class_name}")
        if class_name not in invariants:
            findings.append(f"{invariant_path}: missing canonical {class_name}")
        if class_name not in checklist:
            findings.append(
                "skills/mule-development/resources/post-development-checklist.md: "
                f"missing canonical {class_name}"
            )

    required_text = {
        "skills/mule-review/references/review-domains.md": ("Classes A", "cross-cutting"),
        "skills/mule-troubleshooting/SKILL.md": ("Classes A", "cross-cutting"),
        "skills/mule-ops/SKILL.md": ("Classes A", "cross-cutting"),
        "install/templates/AGENTS.md": ("Classes A", "cross-cutting"),
    }
    for relative_path, tokens in required_text.items():
        text = (root / relative_path).read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                findings.append(f"{relative_path}: missing shared-model reference {token!r}")

    if "resources/post-development-checklist.md" not in development:
        findings.append("skills/mule-development/SKILL.md: stale or missing checklist routing")
    if "scripts/check_embedded_expressions.py" not in checklist:
        findings.append("post-development checklist: missing deterministic embedded-expression check")

    canonical_requirements = {
        "Class A": ("different media types", "required data"),
        "Class B": ("check_embedded_expressions.py", "does not end with"),
        "Class C": ("not APIKit-routable", "Event and queue authority"),
        "Class D": ("Intentional indefinite retryable", "Keep selective retry executable"),
        "Class E": ("OS:STORE_NOT_AVAILABLE", "invalid/blank keys"),
        "Cross-cutting gates": (
            "Security and configuration",
            "Delivery and transactions",
            "persistent VM support",
        ),
    }
    for area, phrases in canonical_requirements.items():
        for phrase in phrases:
            if phrase.lower() not in invariants.lower():
                findings.append(f"{invariant_path}: {area} missing required guidance {phrase!r}")

    stale_claims = (
        "implementation with no bound resource → dead path",
        "Pin `output` on multi-branch expressions",
        "optional cache degrades on store errors",
    )
    checked_text = invariants + "\n" + checklist
    for claim in stale_claims:
        if claim in checked_text:
            findings.append(f"canonical development guidance retains stale claim: {claim!r}")
    return findings


def validate_plugin_manifests(root: Path) -> list[str]:
    """Check the Claude Code plugin and marketplace manifests without any dependency."""
    findings: list[str] = []
    plugin_path = root / ".claude-plugin/plugin.json"
    marketplace_path = root / ".claude-plugin/marketplace.json"

    plugin: dict[str, object] = {}
    if not plugin_path.is_file():
        findings.append(f"{plugin_path}: missing plugin manifest")
    else:
        try:
            plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(f"{plugin_path}: invalid JSON: {exc}")
        else:
            name = plugin.get("name")
            if not isinstance(name, str) or not NAME_RE.fullmatch(name):
                findings.append(f"{plugin_path}: name must be kebab-case, got {name!r}")
            if not isinstance(plugin.get("version"), str):
                findings.append(f"{plugin_path}: missing string version")
            for field in ("description", "license", "repository", "homepage"):
                if not plugin.get(field):
                    findings.append(f"{plugin_path}: missing non-empty {field}")
            if "displayName" in plugin:
                findings.append(
                    f"{plugin_path}: remove displayName: it is not in the schema and is ignored"
                )

    if not marketplace_path.is_file():
        findings.append(f"{marketplace_path}: missing marketplace manifest")
        return findings

    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(f"{marketplace_path}: invalid JSON: {exc}")
        return findings

    for required in ("name", "owner", "plugins"):
        if not marketplace.get(required):
            findings.append(f"{marketplace_path}: missing non-empty {required}")

    name = marketplace.get("name")
    if isinstance(name, str) and not NAME_RE.fullmatch(name):
        findings.append(f"{marketplace_path}: name must be kebab-case, got {name!r}")
    if isinstance(marketplace.get("owner"), dict) and not marketplace["owner"].get("name"):
        findings.append(f"{marketplace_path}: owner.name is required")

    # Marketplace names are global per user, and this repository publishes its
    # own catalog rather than being listed in a shared one. Registering a second
    # catalog under a name already in use silently displaces the first and
    # orphans the plugins installed from it. Naming the catalog after the
    # repository makes the name unique by construction. This is the rule settled
    # in #5; nothing enforced it until now.
    repository = plugin.get("repository")
    if isinstance(name, str) and isinstance(repository, str):
        repository_name = repository.rstrip("/").rsplit("/", 1)[-1]
        if name != repository_name:
            findings.append(
                f"{marketplace_path}: marketplace name {name!r} must match the "
                f"repository name {repository_name!r} — a catalog name shared "
                "with another repository silently displaces its marketplace"
            )

    entries = marketplace.get("plugins")
    if not isinstance(entries, list):
        findings.append(f"{marketplace_path}: plugins must be a list")
        return findings

    for index, entry in enumerate(entries):
        label = f"{marketplace_path}: plugins[{index}]"
        if not isinstance(entry, dict):
            findings.append(f"{label}: must be an object")
            continue
        entry_name = entry.get("name")
        if not isinstance(entry_name, str) or not NAME_RE.fullmatch(entry_name):
            findings.append(f"{label}: name must be kebab-case, got {entry_name!r}")
        source = entry.get("source")
        if not source:
            findings.append(f"{label}: missing source")
        elif isinstance(source, str):
            if not source.startswith("./"):
                findings.append(f"{label}: relative source must start with './', got {source!r}")
            elif not (root / source).is_dir():
                findings.append(f"{label}: source does not resolve: {source}")
        # A field duplicated from plugin.json is a field that can drift.
        for field in ("version", "license", "repository", "homepage"):
            value = entry.get(field)
            if value is not None and plugin.get(field) is not None and value != plugin[field]:
                findings.append(
                    f"{label}: {field} {value!r} disagrees with plugin.json {plugin[field]!r}"
                )

        if entry.get("author") != marketplace.get("owner"):
            findings.append(f"{label}: author must match the marketplace owner")

        # A marketplace browser reads this entry, not plugin.json, so the entry
        # has to carry its own discovery metadata.
        for field in ("description", "license", "repository", "category", "tags"):
            if not entry.get(field):
                findings.append(f"{label}: missing non-empty {field}")

        # `displayName` is in neither the marketplace nor the plugin-manifest
        # schema, and both leave additionalProperties unset — so it validates
        # while the CLI ignores it and renders `name`. A field that looks
        # load-bearing but does nothing is worse than an absent one.
        if "displayName" in entry:
            findings.append(f"{label}: remove displayName: it is not in the schema and is ignored")

        if isinstance(source, str) and source in ("./", "."):
            if entry_name != plugin.get("name"):
                findings.append(
                    f"{label}: name {entry_name!r} must match plugin.json "
                    f"{plugin.get('name')!r} when source is the repository root"
                )
            # With the source at the repository root, skills/ is scanned by
            # default; declaring it explicitly can replace that scan rather
            # than extend it, which silently drops skills.
            if "skills" in plugin:
                findings.append(
                    f"{plugin_path}: remove \"skills\": skills/ is scanned by default, "
                    "and declaring it can replace that scan rather than extend it"
                )
            for skill_dir in sorted((root / "skills").glob("*/")):
                if not (skill_dir / "SKILL.md").is_file():
                    findings.append(f"{skill_dir}: directory under skills/ has no SKILL.md")

    return findings


def validate_mcp_configs(root: Path) -> list[str]:
    """The plugin's .mcp.json and the generic host template must not drift apart."""
    findings: list[str] = []
    plugin_config = root / ".mcp.json"
    host_config = root / "install/hosts/mcp.json"
    for path in (plugin_config, host_config):
        if not path.is_file():
            findings.append(f"{path}: missing MCP configuration")
            return findings
    try:
        plugin_servers = json.loads(plugin_config.read_text(encoding="utf-8"))["mcpServers"]
        host_servers = json.loads(host_config.read_text(encoding="utf-8"))["mcpServers"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        findings.append(f"{plugin_config} / {host_config}: unreadable mcpServers: {exc}")
        return findings
    if plugin_servers != host_servers:
        findings.append(
            f"{plugin_config} and {host_config} disagree; every host must get the same pins"
        )
    return findings


def validate_skill_portability(root: Path) -> list[str]:
    """Skills must not assume one install layout: no host-specific paths, siblings must exist."""
    findings: list[str] = []
    skills_root = root / "skills"
    known = {path.name for path in skills_root.glob("*/") if (path / "SKILL.md").is_file()}

    for path in sorted(skills_root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        if ".agents/skills/" in text and "when vendored" not in text:
            findings.append(
                f"{path}: hardcodes '.agents/skills/'; use <skill-root>/<skills-root> instead"
            )
        referenced = set(PLACEHOLDER_RE.findall(text))
        # From a SKILL.md, '../name/' means a sibling skill. Deeper files use '../' to reach
        # their own skill's other folders, so only the top level can be checked this way.
        if path.parent.parent == skills_root:
            referenced |= set(SIBLING_RE.findall(text))
        for name in sorted(referenced):
            if name not in known:
                findings.append(f"{path}: references unknown sibling skill: {name}")
    return findings


def mcp_pins(root: Path) -> tuple[dict[str, str], list[str]]:
    """Map package name to pinned version from the plugin's .mcp.json."""
    findings: list[str] = []
    config = root / ".mcp.json"
    try:
        servers = json.loads(config.read_text(encoding="utf-8"))["mcpServers"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        return {}, [f"{config}: unreadable mcpServers: {exc}"]

    pins: dict[str, str] = {}
    for name, entry in sorted(servers.items()):
        arguments = entry.get("args") if isinstance(entry, dict) else None
        specifiers = [
            match
            for value in (arguments or [])
            if isinstance(value, str)
            for match in PIN_RE.finditer(value)
        ]
        if len(specifiers) != 1:
            findings.append(f"{config}: server {name!r} must launch exactly one pinned @sfdxy package")
            continue
        package, version = specifiers[0].groups()
        pins[package] = version
    return pins, findings


def validate_pin_consistency(root: Path) -> list[str]:
    """Every documented pin must match .mcp.json.

    The same version string appears in the plugin config, three host forms, the
    installer, and the documentation. A bump that updates some of them leaves a
    user installing one version and reading instructions for another, which is
    the failure this repository is most likely to ship.
    """
    pins, findings = mcp_pins(root)
    if not pins:
        return findings

    candidates = [root / "README.md", root / "install/install.sh"]
    for directory in ("docs", "install", "skills"):
        for suffix in ("*.md", "*.json", "*.toml", "*.sh", "*.yaml", "*.yml"):
            candidates.extend((root / directory).rglob(suffix))

    for path in sorted(set(candidates)):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for match in PIN_RE.finditer(text):
            package, version = match.groups()
            expected = pins.get(package)
            if expected is None:
                findings.append(
                    f"{path}: pins @sfdxy/{package}, which .mcp.json does not launch"
                )
            elif version != expected:
                findings.append(
                    f"{path}: @sfdxy/{package}@{version} disagrees with .mcp.json pin {expected}"
                )
    return findings


def validate_site_nav(root: Path) -> list[str]:
    """No documentation page may be orphaned from the published site."""
    findings: list[str] = []
    config = root / "mkdocs.yml"
    docs_dir = root / "docs"
    if not config.is_file():
        return [f"{config}: missing documentation site configuration"]
    if not docs_dir.is_dir():
        return [f"{docs_dir}: missing docs directory"]

    remainder = config.read_text(encoding="utf-8").partition("\nnav:\n")[2]
    if not remainder:
        return [f"{config}: missing nav section"]

    # Read to the next top-level key so a later block such as `extra:` cannot
    # masquerade as a nav entry. Scanned with a regex on purpose: the validator
    # takes no third-party dependency, and YAML syntax is not what is checked
    # here — `mkdocs build --strict` in CI does that.
    navigated: set[str] = set()
    for line in remainder.splitlines():
        if line.strip() and not line[0].isspace():
            break
        match = NAV_ENTRY_RE.match(line)
        if match:
            navigated.add(match.group(1))

    for target in sorted(navigated):
        if not (docs_dir / target).is_file():
            findings.append(f"{config}: nav entry does not resolve: {target}")

    for path in sorted(docs_dir.rglob("*.md")):
        relative = path.relative_to(docs_dir).as_posix()
        if relative not in navigated:
            findings.append(f"docs/{relative}: not in the {config.name} nav")
    return findings


def validate_anypoint_readiness(root: Path) -> list[str]:
    """Skills that need authorized runtime access must route through one gate.

    Without this, a skill can quietly go back to calling a collection tool first
    and reporting a tool error as an environment finding.
    """
    findings: list[str] = []
    reference = root / "skills/mule-ops" / READINESS_REFERENCE
    if not reference.is_file():
        return [f"{reference}: missing shared Anypoint readiness reference"]

    text = reference.read_text(encoding="utf-8")
    for state in ACCESS_STATES:
        if f"| {state} |" not in text:
            findings.append(f"{reference}: missing access state {state!r}")
    for required in ("mcp_anypoint-connect_whoami", "mcp_anypoint-connect_list_environments"):
        if required not in text:
            findings.append(f"{reference}: missing probe call {required!r}")

    for name in READINESS_SKILLS:
        skill_path = root / "skills" / name / "SKILL.md"
        if not skill_path.is_file():
            findings.append(f"{skill_path}: missing SKILL.md")
            continue
        if READINESS_REFERENCE not in skill_path.read_text(encoding="utf-8"):
            findings.append(
                f"{skill_path}: needs authorized Anypoint evidence but does not route through "
                f"{READINESS_REFERENCE}"
            )
    return findings


def validate_repository(root: Path) -> list[str]:
    findings: list[str] = []
    findings.extend(validate_skills(root))
    findings.extend(validate_local_links(root))
    findings.extend(validate_alignment(root))
    findings.extend(validate_plugin_manifests(root))
    findings.extend(validate_skill_portability(root))
    findings.extend(validate_mcp_configs(root))
    findings.extend(validate_pin_consistency(root))
    findings.extend(validate_site_nav(root))
    findings.extend(validate_anypoint_readiness(root))
    return findings


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args in (["-h"], ["--help"]):
        print("usage: validate_repository.py [repository-root]")
        return 0
    if len(args) > 1:
        print("usage: validate_repository.py [repository-root]", file=sys.stderr)
        return 2
    root = Path(args[0] if args else ".").expanduser().resolve()
    try:
        findings = validate_repository(root)
    except (OSError, UnicodeError) as exc:
        print(f"repository validation failed: {exc}", file=sys.stderr)
        return 2

    for finding in findings:
        print(finding)
    if findings:
        print(f"repository validation: {len(findings)} finding(s)", file=sys.stderr)
        return 1
    print("repository validation: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
