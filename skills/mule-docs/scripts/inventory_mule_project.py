#!/usr/bin/env python3
"""Create a value-safe, read-only inventory of a MuleSoft Mule 4 project."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


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
MUNIT_NS = "http://www.mulesoft.org/schema/mule/munit"
SENSITIVE_SUFFIXES = {
    ".cer",
    ".crt",
    ".der",
    ".jks",
    ".key",
    ".p12",
    ".pem",
    ".pfx",
    ".truststore",
}
TEXT_SUFFIXES = {
    ".dwl",
    ".json",
    ".properties",
    ".raml",
    ".xml",
    ".yaml",
    ".yml",
}
CONFIG_SUFFIXES = {".properties", ".yaml", ".yml"}
CORE_PREFIXES = {
    "",
    "apikit",
    "doc",
    "ee",
    "mule",
    "munit",
    "munit-tools",
    "secure-properties",
    "tls",
    "xsi",
}
SENSITIVE_KEY_RE = re.compile(
    r"(?i)(password|passwd|secret|token|private.?key|consumer.?key|api.?key|credential)"
)
PROPERTY_PATTERNS = (
    re.compile(r"\$\{([A-Za-z0-9_.:-]+)\}"),
    re.compile(r"(?:Mule::)?p\(\s*['\"]([^'\"]+)['\"]\s*\)"),
)
DWL_REFERENCE_RE = re.compile(r"[A-Za-z0-9_./-]+\.dwl")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def namespace_uri(tag: str) -> str:
    return tag[1:].split("}", 1)[0] if tag.startswith("{") else ""


def is_within(root: Path, candidate: Path) -> bool:
    try:
        return os.path.commonpath((str(root), str(candidate))) == str(root)
    except ValueError:
        return False


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def ignored_directory(name: str) -> bool:
    lowered = name.lower()
    return (
        name in IGNORED_DIRECTORIES
        or lowered.endswith((".bak", "-backup", "_backup"))
        or lowered.startswith("backup-")
    )


def is_under(root: Path, path: Path, *parts: str) -> bool:
    relative_parts = path.relative_to(root).parts
    return relative_parts[: len(parts)] == parts


def walk_files(root: Path) -> Iterable[Path]:
    for directory, names, filenames in os.walk(root, topdown=True, followlinks=False):
        current = Path(directory)
        names[:] = sorted(
            name
            for name in names
            if not ignored_directory(name)
            and not (current / name).is_symlink()
            and is_within(root, (current / name).resolve(strict=False))
        )
        for filename in sorted(filenames):
            path = current / filename
            if path.is_symlink():
                continue
            resolved = path.resolve(strict=False)
            if is_within(root, resolved):
                yield path


def read_text(path: Path, warnings: list[str], limit: int = 5_000_000) -> str | None:
    try:
        if path.stat().st_size > limit:
            warnings.append(f"Skipped oversized text file: {path.name}")
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        warnings.append(f"Could not read text file {path.name}: {error.__class__.__name__}")
        return None


def namespace_prefixes(path: Path) -> dict[str, str]:
    prefixes: dict[str, str] = {}
    try:
        for _event, item in ET.iterparse(path, events=("start-ns",)):
            prefix, uri = item
            prefixes.setdefault(uri, prefix or "")
    except (ET.ParseError, OSError):
        return prefixes
    return prefixes


def qualified_name(tag: str, prefixes: dict[str, str]) -> str:
    uri = namespace_uri(tag)
    name = local_name(tag)
    prefix = prefixes.get(uri, "")
    return f"{prefix}:{name}" if prefix else name


def child_text(element: ET.Element, name: str) -> str | None:
    for child in list(element):
        if local_name(child.tag) == name and child.text:
            value = child.text.strip()
            return value or None
    return None


def parse_pom(path: Path, root: Path, warnings: list[str]) -> dict[str, Any]:
    try:
        project = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        warnings.append(f"Could not parse {relative(root, path)}: {error.__class__.__name__}")
        return {}

    parent = next((item for item in list(project) if local_name(item.tag) == "parent"), None)
    group_id = child_text(project, "groupId") or (child_text(parent, "groupId") if parent else None)
    version = child_text(project, "version") or (child_text(parent, "version") if parent else None)

    properties: dict[str, str] = {}
    dependencies: list[dict[str, str]] = []
    plugins: list[dict[str, str]] = []

    for element in project.iter():
        name = local_name(element.tag)
        if name == "properties":
            for prop in list(element):
                key = local_name(prop.tag)
                value = (prop.text or "").strip()
                if value and "version" in key.lower() and not SENSITIVE_KEY_RE.search(key):
                    properties[key] = value
        elif name == "dependency":
            item = {
                key: value
                for key in ("groupId", "artifactId", "version", "scope", "type", "classifier")
                if (value := child_text(element, key))
            }
            if item:
                dependencies.append(item)
        elif name == "plugin":
            item = {
                key: value
                for key in ("groupId", "artifactId", "version")
                if (value := child_text(element, key))
            }
            if item:
                plugins.append(item)

    return {
        "source": relative(root, path),
        "group_id": group_id,
        "artifact_id": child_text(project, "artifactId"),
        "version": version,
        "packaging": child_text(project, "packaging"),
        "version_properties": dict(sorted(properties.items())),
        "dependencies": sorted(dependencies, key=lambda item: json.dumps(item, sort_keys=True)),
        "plugins": sorted(plugins, key=lambda item: json.dumps(item, sort_keys=True)),
    }


def parse_mule_artifact(path: Path, root: Path, warnings: list[str]) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        warnings.append(f"Could not parse {relative(root, path)}: {error.__class__.__name__}")
        return {}

    return {
        "source": relative(root, path),
        "name": data.get("name"),
        "minimum_mule_version": data.get("minMuleVersion"),
        "required_product": data.get("requiredProduct"),
        "secure_properties_declared": bool(data.get("secureProperties")),
    }


def safe_trigger_attributes(element: ET.Element) -> dict[str, str]:
    allowed = {
        "method",
        "path",
        "queueName",
        "topic",
        "destination",
        "frequency",
        "timeUnit",
        "cronExpression",
        "schedulingStrategy",
    }
    return {
        local_name(key): value
        for key, value in element.attrib.items()
        if local_name(key) in allowed and not SENSITIVE_KEY_RE.search(local_name(key))
    }


def scan_mule_xml(
    path: Path,
    root: Path,
    warnings: list[str],
    connectors: dict[str, dict[str, set[str]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, set[str]]:
    source = relative(root, path)
    prefixes = namespace_prefixes(path)
    try:
        xml_root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        warnings.append(f"Could not parse {source}: {error.__class__.__name__}")
        return [], [], 0, set()

    flows: list[dict[str, Any]] = []
    global_configurations: list[dict[str, Any]] = []
    inline_dataweave = 0
    dwl_references: set[str] = set()

    for element in xml_root.iter():
        qname = qualified_name(element.tag, prefixes)
        prefix = qname.split(":", 1)[0] if ":" in qname else ""
        if prefix not in CORE_PREFIXES:
            connector = connectors[prefix]
            connector["operations"].add(local_name(element.tag))
            connector["sources"].add(source)
            config_ref = element.attrib.get("config-ref")
            if config_ref:
                connector["config_refs"].add(config_ref)

        direct_text = element.text or ""
        if "%dw" in direct_text:
            inline_dataweave += 1
        dwl_references.update(DWL_REFERENCE_RE.findall(direct_text))
        for value in element.attrib.values():
            dwl_references.update(DWL_REFERENCE_RE.findall(value))

    for element in xml_root.iter():
        kind = local_name(element.tag)
        if kind not in {"flow", "sub-flow"}:
            continue

        children = list(element)
        direct_processors = [
            qualified_name(child.tag, prefixes)
            for child in children
            if local_name(child.tag) != "error-handler"
        ]
        trigger_element = children[0] if kind == "flow" and children else None
        trigger = None
        if trigger_element is not None and local_name(trigger_element.tag) not in {
            "set-variable",
            "set-payload",
            "logger",
            "flow-ref",
        }:
            trigger = {
                "type": qualified_name(trigger_element.tag, prefixes),
                "attributes": safe_trigger_attributes(trigger_element),
            }

        flow_refs = sorted(
            {
                item.attrib["name"]
                for item in element.iter()
                if local_name(item.tag) == "flow-ref" and item.attrib.get("name")
            }
        )
        config_refs = sorted(
            {
                value
                for item in element.iter()
                for key, value in item.attrib.items()
                if local_name(key) == "config-ref" and value
            }
        )
        error_handlers = [
            {
                "strategy": local_name(item.tag),
                "types": item.attrib.get("type", "ANY"),
            }
            for item in element.iter()
            if local_name(item.tag) in {"on-error-continue", "on-error-propagate"}
        ]

        flows.append(
            {
                "name": element.attrib.get("name"),
                "kind": kind,
                "source": source,
                "trigger": trigger,
                "direct_processors": direct_processors,
                "flow_refs": flow_refs,
                "config_refs": config_refs,
                "error_handlers": error_handlers,
            }
        )

    for child in list(xml_root):
        kind = local_name(child.tag)
        if kind in {"flow", "sub-flow"}:
            continue
        name = child.attrib.get("name")
        if name or "config" in kind or kind == "configuration-properties":
            global_configurations.append(
                {
                    "type": qualified_name(child.tag, prefixes),
                    "name": name,
                    "source": source,
                }
            )

    return flows, global_configurations, inline_dataweave, dwl_references


def scan_munit(path: Path, root: Path, warnings: list[str]) -> dict[str, Any]:
    source = relative(root, path)
    try:
        xml_root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        warnings.append(f"Could not parse {source}: {error.__class__.__name__}")
        return {"source": source, "parse_error": error.__class__.__name__, "tests": []}

    tests = sorted(
        {
            element.attrib.get("name", "<unnamed>")
            for element in xml_root.iter()
            if namespace_uri(element.tag) == MUNIT_NS and local_name(element.tag) == "test"
        }
    )
    return {"source": source, "tests": tests}


def collect_properties(text: str, source: str, properties: dict[str, set[str]]) -> None:
    for pattern in PROPERTY_PATTERNS:
        for key in pattern.findall(text):
            properties[key].add(source)


def is_sensitive_text_path(path: Path) -> bool:
    name = path.name.lower()
    return (
        name == ".env"
        or name.startswith(".env.")
        or name.startswith("secure-")
        or "secret" in name
        or path.suffix.lower() in SENSITIVE_SUFFIXES
    )


def is_api_spec(path: Path) -> bool:
    lowered = path.name.lower()
    if path.suffix.lower() == ".raml":
        return True
    stem = path.stem.lower()
    return path.suffix.lower() in {".yaml", ".yml", ".json"} and (
        stem in {"api", "openapi", "swagger", "asyncapi"}
        or lowered.startswith(("openapi.", "swagger.", "asyncapi."))
    )


def is_existing_doc(path: Path, root: Path) -> bool:
    if path.suffix.lower() != ".md" or ".agents" in path.parts:
        return False
    rel = path.relative_to(root)
    return rel.parent == Path(".") or any(part in {"docs", "doc", "exchange-docs"} for part in rel.parts)


def is_deployment_file(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    name = path.name.lower()
    if name in {"dockerfile", "jenkinsfile", "procfile"}:
        return True
    if ".github" in rel.parts and "workflows" in rel.parts and path.suffix.lower() in {".yaml", ".yml"}:
        return True
    return "deploy" in name and path.suffix.lower() in {".sh", ".yaml", ".yml", ".xml"}


def build_inventory(root: Path) -> dict[str, Any]:
    root = root.resolve()
    warnings: list[str] = []
    files = list(walk_files(root))
    pom_path = root / "pom.xml"
    artifact_path = root / "mule-artifact.json"
    pom = parse_pom(pom_path, root, warnings) if pom_path.is_file() else {}
    mule_artifact = (
        parse_mule_artifact(artifact_path, root, warnings) if artifact_path.is_file() else {}
    )

    mule_xml_files = [
        path
        for path in files
        if path.suffix.lower() == ".xml" and is_under(root, path, "src", "main", "mule")
    ]
    munit_files = [
        path
        for path in files
        if path.suffix.lower() == ".xml" and is_under(root, path, "src", "test", "munit")
    ]

    connector_sets: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"operations": set(), "config_refs": set(), "sources": set()}
    )
    flows: list[dict[str, Any]] = []
    global_configurations: list[dict[str, Any]] = []
    inline_dataweave_count = 0
    dwl_references: set[str] = set()

    for path in mule_xml_files:
        found_flows, found_globals, inline_count, references = scan_mule_xml(
            path, root, warnings, connector_sets
        )
        flows.extend(found_flows)
        global_configurations.extend(found_globals)
        inline_dataweave_count += inline_count
        dwl_references.update(references)

    properties: dict[str, set[str]] = defaultdict(set)
    skipped_sensitive_file_count = 0
    for path in files:
        if path.suffix.lower() in SENSITIVE_SUFFIXES:
            skipped_sensitive_file_count += 1
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES or is_sensitive_text_path(path):
            continue
        source = relative(root, path)
        text = read_text(path, warnings)
        if text is not None:
            collect_properties(text, source, properties)

    connectors = [
        {
            "type": connector_type,
            "operations": sorted(data["operations"]),
            "config_refs": sorted(data["config_refs"]),
            "sources": sorted(data["sources"]),
        }
        for connector_type, data in sorted(connector_sets.items())
    ]

    config_files = sorted(
        relative(root, path)
        for path in files
        if path.suffix.lower() in CONFIG_SUFFIXES
        and (
            "resources" in path.parts
            or "config" in path.parts
            or "config" in path.name.lower()
        )
    )
    api_specs = sorted(relative(root, path) for path in files if is_api_spec(path))
    dataweave_files = sorted(
        relative(root, path) for path in files if path.suffix.lower() == ".dwl"
    )
    existing_docs = sorted(relative(root, path) for path in files if is_existing_doc(path, root))
    deployment_files = sorted(
        relative(root, path) for path in files if is_deployment_file(path, root)
    )
    munit = [scan_munit(path, root, warnings) for path in munit_files]

    packaging = str(pom.get("packaging") or "").lower()
    mule_plugin_present = any(
        "mule-maven-plugin" == item.get("artifactId") for item in pom.get("plugins", [])
    )
    indicators = {
        "mule_artifact": artifact_path.is_file(),
        "mule_source_tree": bool(mule_xml_files) or (root / "src" / "main" / "mule").is_dir(),
        "mule_packaging": packaging == "mule-application",
        "mule_maven_plugin": mule_plugin_present,
    }
    is_mule_project = indicators["mule_artifact"] or (
        indicators["mule_source_tree"]
        and (indicators["mule_packaging"] or indicators["mule_maven_plugin"] or bool(pom))
    )
    if not is_mule_project:
        warnings.append("The supplied root does not contain enough evidence to classify it as a Mule project.")

    return {
        "schema_version": 1,
        "project_root": ".",
        "is_mule_project": is_mule_project,
        "mule_indicators": indicators,
        "build": pom,
        "mule_artifact": mule_artifact,
        "api_specs": api_specs,
        "mule_xml_files": sorted(relative(root, path) for path in mule_xml_files),
        "flows": sorted(flows, key=lambda item: (item.get("source") or "", item.get("name") or "")),
        "global_configurations": sorted(
            global_configurations,
            key=lambda item: (
                item.get("source") or "",
                item.get("type") or "",
                item.get("name") or "",
            ),
        ),
        "connectors": connectors,
        "dataweave": {
            "external_files": dataweave_files,
            "inline_transform_count": inline_dataweave_count,
            "referenced_files": sorted(dwl_references),
        },
        "configuration": {
            "files": config_files,
            "property_references": [
                {
                    "key": key,
                    "sensitive_name": bool(SENSITIVE_KEY_RE.search(key)),
                    "sources": sorted(sources),
                }
                for key, sources in sorted(properties.items())
            ],
            "skipped_sensitive_binary_count": skipped_sensitive_file_count,
        },
        "tests": {
            "munit_suites": munit,
            "suite_count": len(munit),
            "test_count": sum(len(suite.get("tests", [])) for suite in munit),
        },
        "deployment_files": deployment_files,
        "existing_documentation": existing_docs,
        "warnings": sorted(set(warnings)),
        "statistics": {
            "scanned_file_count": len(files),
            "mule_xml_file_count": len(mule_xml_files),
            "top_level_flow_count": sum(1 for flow in flows if flow.get("kind") == "flow"),
            "subflow_count": sum(1 for flow in flows if flow.get("kind") == "sub-flow"),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a read-only, value-safe JSON inventory of a MuleSoft Mule 4 project."
    )
    parser.add_argument("project_root", help="Path to the Mule project root")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.project_root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: project root is not a directory: {root}", file=sys.stderr)
        return 2

    inventory = build_inventory(root)
    print(json.dumps(inventory, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
