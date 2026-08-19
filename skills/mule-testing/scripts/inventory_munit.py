#!/usr/bin/env python3
"""Emit a read-only, value-safe inventory of MUnit test structure."""

from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable


MUNIT_NS = "http://www.mulesoft.org/schema/mule/munit"
MUNIT_TOOLS_NS = "http://www.mulesoft.org/schema/mule/munit-tools"
IGNORED_DIRECTORIES = {
    ".git",
    ".idea",
    ".m2",
    ".mule",
    ".settings",
    ".tooling-project",
    ".vscode",
    "__MACOSX",
    "backup",
    "backups",
    "coverage",
    "dist",
    "generated-sources",
    "node_modules",
    "target",
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def namespace_uri(tag: str) -> str:
    return tag[1:].split("}", 1)[0] if tag.startswith("{") else ""


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def ignored_directory(name: str) -> bool:
    lowered = name.lower()
    return (
        name in IGNORED_DIRECTORIES
        or lowered.endswith((".bak", "-backup", "_backup"))
        or lowered.startswith("backup-")
    )


def walk_files(directory: Path) -> Iterable[Path]:
    if not directory.is_dir() or directory.is_symlink():
        return
    for current_text, names, filenames in os.walk(directory, topdown=True, followlinks=False):
        current = Path(current_text)
        names[:] = sorted(
            name
            for name in names
            if not ignored_directory(name) and not (current / name).is_symlink()
        )
        for filename in sorted(filenames):
            path = current / filename
            if not path.is_symlink():
                yield path


def child_text(element: ET.Element, name: str) -> str | None:
    for child in list(element):
        if local_name(child.tag) == name and child.text:
            value = child.text.strip()
            return value or None
    return None


def resolve_version(value: str | None, properties: dict[str, str]) -> str | None:
    if not value:
        return None
    if value.startswith("${") and value.endswith("}"):
        return properties.get(value[2:-1]) or value
    return value


def parse_versions(root: Path, findings: list[dict[str, str]]) -> dict[str, str | None]:
    versions: dict[str, str | None] = {
        "minimum_mule": None,
        "munit_plugin": None,
        "mule_maven_plugin": None,
    }
    artifact = root / "mule-artifact.json"
    if artifact.is_file() and not artifact.is_symlink():
        try:
            data = json.loads(artifact.read_text(encoding="utf-8"))
            minimum = data.get("minMuleVersion")
            if isinstance(minimum, str):
                versions["minimum_mule"] = minimum
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            findings.append(
                {
                    "code": "artifact-unreadable",
                    "message": f"Could not parse mule-artifact.json: {error.__class__.__name__}",
                    "source": "mule-artifact.json",
                }
            )

    pom = root / "pom.xml"
    if not pom.is_file() or pom.is_symlink():
        return versions
    try:
        project = ET.parse(pom).getroot()
    except (ET.ParseError, OSError) as error:
        findings.append(
            {
                "code": "pom-unreadable",
                "message": f"Could not parse pom.xml: {error.__class__.__name__}",
                "source": "pom.xml",
            }
        )
        return versions

    properties: dict[str, str] = {}
    for element in project.iter():
        if local_name(element.tag) == "properties":
            for prop in list(element):
                value = (prop.text or "").strip()
                if value:
                    properties[local_name(prop.tag)] = value
    for element in project.iter():
        artifact_id = child_text(element, "artifactId")
        if artifact_id not in {"munit-maven-plugin", "mule-maven-plugin"}:
            continue
        version = resolve_version(child_text(element, "version"), properties)
        if artifact_id == "munit-maven-plugin":
            versions["munit_plugin"] = version
        else:
            versions["mule_maven_plugin"] = version
    return versions


def is_mule_project(root: Path) -> bool:
    artifact = root / "mule-artifact.json"
    if artifact.is_file() and not artifact.is_symlink():
        return True
    pom = root / "pom.xml"
    if not pom.is_file() or pom.is_symlink():
        return False
    try:
        project = ET.parse(pom).getroot()
    except (ET.ParseError, OSError):
        return False
    packaging = child_text(project, "packaging")
    if packaging == "mule-application":
        return True
    return any(
        child_text(element, "artifactId") == "mule-maven-plugin"
        for element in project.iter()
    )


def production_flows(root: Path, findings: list[dict[str, str]]) -> set[str]:
    names: set[str] = set()
    source_root = root / "src/main/mule"
    for path in walk_files(source_root):
        if path.suffix.lower() != ".xml":
            continue
        try:
            xml_root = ET.parse(path).getroot()
        except (ET.ParseError, OSError) as error:
            findings.append(
                {
                    "code": "production-xml-unreadable",
                    "message": f"Could not parse production Mule XML: {error.__class__.__name__}",
                    "source": relative(root, path),
                }
            )
            continue
        for element in xml_root.iter():
            if local_name(element.tag) in {"flow", "sub-flow"}:
                name = element.attrib.get("name")
                if name:
                    names.add(name)
    return names


def fixture_inventory(root: Path) -> tuple[list[str], dict[str, str]]:
    fixtures: list[str] = []
    aliases: dict[str, str] = {}
    fixture_root = root / "src/test/resources"
    for path in walk_files(fixture_root):
        item = relative(root, path)
        fixtures.append(item)
        aliases[item] = item
        aliases[path.name] = item
        aliases[path.relative_to(fixture_root).as_posix()] = item
    return sorted(fixtures), aliases


def mentioned_fixtures(xml_root: ET.Element, aliases: dict[str, str]) -> list[str]:
    references: set[str] = set()
    values: list[str] = []
    for element in xml_root.iter():
        values.extend(element.attrib.values())
        if element.text:
            values.append(element.text)
    for value in values:
        normalized = value.replace("\\", "/")
        for alias, source in aliases.items():
            if alias and alias in normalized:
                references.add(source)
    return sorted(references)


def suite_inventory(
    path: Path,
    root: Path,
    flows: set[str],
    fixture_aliases: dict[str, str],
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    source = relative(root, path)
    result: dict[str, Any] = {
        "source": source,
        "parse_status": "ok",
        "tests": [],
        "mocks": [],
        "assertions": [],
        "verifications": [],
        "spies": [],
        "fixture_references": [],
        "inferred_flow_targets": [],
    }
    try:
        xml_root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        result["parse_status"] = "error"
        findings.append(
            {
                "code": "suite-unreadable",
                "message": f"Could not parse MUnit suite: {error.__class__.__name__}",
                "source": source,
            }
        )
        return result

    suite_name = xml_root.attrib.get("name")
    if suite_name:
        result["name"] = suite_name

    mentioned_values: set[str] = set()
    for element in xml_root.iter():
        mentioned_values.update(element.attrib.values())
        uri = namespace_uri(element.tag)
        name = local_name(element.tag)
        if uri == MUNIT_NS and name == "test":
            test_name = element.attrib.get("name", "<unnamed>")
            ignored = element.attrib.get("ignore", "false").strip().lower() == "true"
            result["tests"].append({"name": test_name, "ignored": ignored})
        elif uri == MUNIT_TOOLS_NS and name == "mock-when":
            selector_names = sorted(
                {
                    child.attrib[attribute]
                    for child in element.iter()
                    if namespace_uri(child.tag) == MUNIT_TOOLS_NS
                    and local_name(child.tag) == "with-attribute"
                    for attribute in ("attributeName", "attribute-name")
                    if child.attrib.get(attribute)
                }
            )
            result["mocks"].append(
                {
                    "component": element.attrib.get("processor", "unspecified"),
                    "selector_attributes": selector_names,
                }
            )
        elif uri == MUNIT_TOOLS_NS and name.startswith("assert"):
            result["assertions"].append(name)
        elif uri == MUNIT_TOOLS_NS and name == "verify-call":
            result["verifications"].append(name)
        elif uri == MUNIT_TOOLS_NS and name == "spy":
            result["spies"].append(name)

    result["fixture_references"] = mentioned_fixtures(xml_root, fixture_aliases)
    targets: list[dict[str, str]] = []
    for flow in sorted(flows):
        if flow in mentioned_values or any(flow in item["name"] for item in result["tests"]):
            targets.append(
                {"name": flow, "mapping_method": "name-mention", "confidence": "heuristic"}
            )
    result["inferred_flow_targets"] = targets

    executable = sum(not item["ignored"] for item in result["tests"])
    if result["tests"] and executable == 0:
        findings.append(
            {
                "code": "suite-ignored-only",
                "message": "Suite contains tests but none are executable.",
                "source": source,
            }
        )
    if executable and not result["assertions"] and not result["verifications"]:
        findings.append(
            {
                "code": "suite-no-observable-check",
                "message": "Executable tests have no discovered assertion or call verification.",
                "source": source,
            }
        )
    return result


def build_inventory(root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    flows = production_flows(root, findings)
    fixtures, fixture_aliases = fixture_inventory(root)
    suites = [
        suite_inventory(path, root, flows, fixture_aliases, findings)
        for path in walk_files(root / "src/test/munit")
        if path.suffix.lower() == ".xml"
    ]

    tests = [test for suite in suites for test in suite["tests"]]
    statistics = {
        "suite_count": len(suites),
        "test_count": len(tests),
        "executable_test_count": sum(not test["ignored"] for test in tests),
        "ignored_test_count": sum(test["ignored"] for test in tests),
        "mock_count": sum(len(suite["mocks"]) for suite in suites),
        "assertion_count": sum(len(suite["assertions"]) for suite in suites),
        "verification_count": sum(len(suite["verifications"]) for suite in suites),
        "spy_count": sum(len(suite["spies"]) for suite in suites),
        "fixture_count": len(fixtures),
    }
    if statistics["executable_test_count"] == 0:
        findings.append(
            {
                "code": "no-executable-tests",
                "message": "No executable MUnit tests were discovered in src/test/munit.",
            }
        )
    return {
        "schema_version": 1,
        "project_root": ".",
        "is_mule_project": True,
        "versions": parse_versions(root, findings),
        "production_flow_count": len(flows),
        "suites": suites,
        "fixtures": fixtures,
        "findings": findings,
        "statistics": statistics,
    }


def parse_args(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a value-safe, read-only inventory of MUnit test structure."
    )
    parser.add_argument("root", nargs="?", default=".", help="Mule project root (default: .)")
    parser.add_argument("--pretty", action="store_true", help="Indent the JSON output")
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    args = parse_args(arguments if arguments is not None else sys.argv[1:])
    root = Path(args.root).expanduser()
    if not root.is_dir():
        print(f"error: project root is not a directory: {root}", file=sys.stderr)
        return 2
    root = root.resolve()
    if not is_mule_project(root):
        print(f"error: not a Mule application project: {root}", file=sys.stderr)
        return 2
    result = build_inventory(root)
    json.dump(result, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
