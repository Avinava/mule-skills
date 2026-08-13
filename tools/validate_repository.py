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
        version = entry.get("version")
        if version is not None and version != plugin.get("version"):
            findings.append(
                f"{label}: version {version!r} disagrees with plugin.json {plugin.get('version')!r}"
            )
        if isinstance(source, str) and source in ("./", "."):
            if entry_name != plugin.get("name"):
                findings.append(
                    f"{label}: name {entry_name!r} must match plugin.json "
                    f"{plugin.get('name')!r} when source is the repository root"
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


def validate_repository(root: Path) -> list[str]:
    findings: list[str] = []
    findings.extend(validate_skills(root))
    findings.extend(validate_local_links(root))
    findings.extend(validate_alignment(root))
    findings.extend(validate_plugin_manifests(root))
    findings.extend(validate_skill_portability(root))
    findings.extend(validate_mcp_configs(root))
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
