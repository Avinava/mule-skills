#!/usr/bin/env python3
"""Dependency-free structural validation for this reusable skill repository."""

from __future__ import annotations

import re
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
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
    markdown_files = [root / "README.md", root / "SETUP.md"]
    markdown_files.extend((root / "skills").rglob("*.md"))
    markdown_files.extend((root / "templates").rglob("*.md"))
    markdown_files.extend((root / "workflows").rglob("*.md"))

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
        "skills/review-mulesoft-project/references/review-domains.md": ("Classes A", "cross-cutting"),
        "skills/mule-troubleshooting/SKILL.md": ("Classes A", "cross-cutting"),
        "skills/mule-ops/SKILL.md": ("Classes A", "cross-cutting"),
        "templates/AGENTS.md": ("Classes A", "cross-cutting"),
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


def validate_repository(root: Path) -> list[str]:
    findings: list[str] = []
    findings.extend(validate_skills(root))
    findings.extend(validate_local_links(root))
    findings.extend(validate_alignment(root))
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
