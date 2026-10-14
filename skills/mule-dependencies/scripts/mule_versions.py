#!/usr/bin/env python3
"""Look up current Mule connector, plugin, and runtime versions with compatibility evidence.

Read-only. Standard library only. JSON on stdout, diagnostics on stderr.

Exit codes: 0 success, 2 not found or no compatible version, 3 network or authentication failure,
64 usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXIT_OK = 0
EXIT_NOT_FOUND = 2
EXIT_NETWORK = 3
EXIT_USAGE = 64

SKILL_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = SKILL_ROOT / "assets" / "version-snapshot.json"

EXCHANGE_ASSET_URL = "https://anypoint.mulesoft.com/exchange/api/v1/assets/{group}/{artifact}"
EXCHANGE_MAVEN_URL = "https://maven.anypoint.mulesoft.com/api/v3/maven/{group}/{artifact}/maven-metadata.xml"
RELEASES_URL = "https://repository.mulesoft.org/releases/{path}/maven-metadata.xml"
JAVA_SUPPORT_URL = (
    "https://raw.githubusercontent.com/mulesoft/docs-general/HEAD/modules/ROOT/pages/java-support.adoc"
)
SUPPORT_POLICY_URL = "https://docs.mulesoft.com/release-notes/mule-runtime/lts-edge-release-cadence"

CONNECTOR_TTL = 24 * 3600
RUNTIME_TTL = 7 * 24 * 3600
TIMEOUT_SECONDS = 20

# Fixed coordinates. Several connectors exist under more than one group; these are the current ones.
CONNECTORS: dict[str, tuple[str, str]] = {
    "http": ("org.mule.connectors", "mule-http-connector"),
    "db": ("org.mule.connectors", "mule-db-connector"),
    "sftp": ("org.mule.connectors", "mule-sftp-connector"),
    "ftp": ("org.mule.connectors", "mule-ftp-connector"),
    "file": ("org.mule.connectors", "mule-file-connector"),
    "jms": ("org.mule.connectors", "mule-jms-connector"),
    "vm": ("org.mule.connectors", "mule-vm-connector"),
    "email": ("org.mule.connectors", "mule-email-connector"),
    "objectstore": ("org.mule.connectors", "mule-objectstore-connector"),
    "sockets": ("org.mule.connectors", "mule-sockets-connector"),
    "wsc": ("org.mule.connectors", "mule-wsc-connector"),
    "apikit": ("org.mule.modules", "mule-apikit-module"),
    "validation": ("org.mule.modules", "mule-validation-module"),
    "salesforce": ("com.mulesoft.connectors", "mule-salesforce-connector"),
    "kafka": ("com.mulesoft.connectors", "mule-kafka-connector"),
    "s3": ("com.mulesoft.connectors", "mule-amazon-s3-connector"),
    "sqs": ("com.mulesoft.connectors", "mule-amazon-sqs-connector"),
    "mongodb": ("com.mulesoft.connectors", "mule-mongodb-connector"),
    "workday": ("com.mulesoft.connectors", "mule-workday-connector"),
    "sap": ("com.mulesoft.connectors", "mule-sap-connector"),
    "netsuite": ("com.mulesoft.connectors", "mule-netsuite-connector"),
    "anypoint-mq": ("com.mulesoft.connectors", "anypoint-mq-connector"),
}

# Build tooling lives in the MuleSoft releases repository, not in Exchange.
PLUGINS: dict[str, tuple[str, str]] = {
    "munit-runner": ("com.mulesoft.munit", "munit-runner"),
    "munit-tools": ("com.mulesoft.munit", "munit-tools"),
    "munit-maven-plugin": ("com.mulesoft.munit.tools", "munit-maven-plugin"),
    "mule-maven-plugin": ("org.mule.tools.maven", "mule-maven-plugin"),
}

PRERELEASE_RE = re.compile(r"[-.]?(dev|snapshot|rc|m|alpha|beta)\d*($|[-.])", re.IGNORECASE)
JAVA_FLAG_RE = re.compile(r"^is-java-(\d+)-supported$")


class NotFound(Exception):
    pass


class NetworkFailure(Exception):
    pass


# ---------------------------------------------------------------------------------------------
# Versions


def parse_version(version: str) -> tuple[int, ...]:
    numbers = re.match(r"\d+(?:\.\d+)*", version.strip())
    if not numbers:
        return (0,)
    return tuple(int(part) for part in numbers.group(0).split("."))


def version_key(version: str) -> tuple[int, ...]:
    parts = parse_version(version)
    return parts + (0,) * (4 - len(parts))


def is_prerelease(version: str) -> bool:
    version = version.strip()
    numbers = re.match(r"\d+(?:\.\d+)*", version)
    suffix = version[numbers.end() :] if numbers else version
    return bool(suffix) and bool(PRERELEASE_RE.search(suffix + "."))


def release_versions(versions: list[str]) -> list[str]:
    return sorted({v for v in versions if not is_prerelease(v)}, key=version_key)


def version_lte(left: str, right: str) -> bool:
    return version_key(left) <= version_key(right)


# ---------------------------------------------------------------------------------------------
# HTTP and cache


def cache_dir() -> Path:
    override = os.environ.get("MULE_VERSIONS_CACHE_DIR")
    if override:
        return Path(override)
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "mule-skills" / "versions"


def http_get(url: str) -> str:
    """Single network seam; tests replace this function."""
    request = urllib.request.Request(url, headers={"User-Agent": "mule-skills-versions/1"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise NotFound(url) from error
        if error.code in (401, 403):
            raise NetworkFailure(f"authentication required ({error.code}) for {url}") from error
        raise NetworkFailure(f"HTTP {error.code} for {url}") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise NetworkFailure(f"{url}: {error}") from error


class Fetcher:
    def __init__(self, use_cache: bool = True) -> None:
        self.use_cache = use_cache
        self.warnings: list[str] = []

    def get(self, url: str, ttl: int) -> tuple[str, str]:
        """Return (body, fetched_at ISO time). Retries transient failures; falls back to stale cache."""
        path = cache_dir() / (hashlib.sha1(url.encode()).hexdigest() + ".json")
        cached = self._read(path)
        if cached and self.use_cache and time.time() - cached["at"] < ttl:
            return cached["body"], iso(cached["at"])
        last: Exception | None = None
        for attempt in range(3):
            try:
                body = http_get(url)
            except NotFound:
                raise
            except NetworkFailure as error:
                last = error
                if "authentication" in str(error):
                    break
                if attempt < 2:
                    time.sleep(0.5 * (2**attempt))
                continue
            now = time.time()
            if self.use_cache:
                self._write(path, {"at": now, "body": body})
            return body, iso(now)
        if cached and self.use_cache:
            self.warnings.append(f"network failed; using stale cache from {iso(cached['at'])}")
            return cached["body"], iso(cached["at"])
        raise NetworkFailure(str(last))

    @staticmethod
    def _read(path: Path) -> dict[str, Any] | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    @staticmethod
    def _write(path: Path, payload: dict[str, Any]) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload), encoding="utf-8")
        except OSError:
            pass


def iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(message: str) -> None:
    print(message, file=sys.stderr)


# ---------------------------------------------------------------------------------------------
# Sources


def attributes_map(entry: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in entry.get("attributes") or []:
        key = item.get("key")
        if key:
            result[key] = str(item.get("value"))
    return result


def exchange_connector(fetcher: Fetcher, group: str, artifact: str) -> dict[str, Any]:
    body, fetched_at = fetcher.get(EXCHANGE_ASSET_URL.format(group=group, artifact=artifact), CONNECTOR_TTL)
    data = json.loads(body)
    entries = data.get("versions")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Exchange response has no versions list")
    releases: list[dict[str, Any]] = []
    for entry in entries:
        version = str(entry.get("version", ""))
        if not version or entry.get("isSnapshot") or is_prerelease(version):
            continue
        attrs = attributes_map(entry)
        java = sorted(
            int(match.group(1))
            for key, value in attrs.items()
            if (match := JAVA_FLAG_RE.match(key)) and value == "true"
        )
        known_java_flags = any(JAVA_FLAG_RE.match(key) for key in attrs)
        releases.append(
            {
                "version": version,
                "minMuleVersion": attrs.get("min-mule-version") or entry.get("runtimeVersion") or None,
                "java": java if known_java_flags else None,
            }
        )
    releases.sort(key=lambda item: version_key(item["version"]))
    return {"source": "exchange-asset-api", "fetchedAt": fetched_at, "releases": releases}


def maven_metadata_versions(xml_text: str) -> list[str]:
    root = ET.fromstring(xml_text)
    return [node.text.strip() for node in root.iter("version") if node.text and node.text.strip()]


def maven_connector(fetcher: Fetcher, group: str, artifact: str) -> dict[str, Any]:
    """Exchange Maven facade, then the MuleSoft releases repository. No compatibility metadata."""
    errors: list[str] = []
    attempts = [
        ("exchange-maven-facade", EXCHANGE_MAVEN_URL.format(group=group, artifact=artifact)),
        ("mulesoft-releases", RELEASES_URL.format(path=f"{group.replace('.', '/')}/{artifact}")),
    ]
    not_found = 0
    for source, url in attempts:
        try:
            body, fetched_at = fetcher.get(url, CONNECTOR_TTL)
            versions = release_versions(maven_metadata_versions(body))
        except NotFound:
            not_found += 1
            continue
        except (NetworkFailure, ET.ParseError) as error:
            errors.append(f"{source}: {error}")
            continue
        if versions:
            releases = [{"version": v, "minMuleVersion": None, "java": None} for v in versions]
            return {"source": source, "fetchedAt": fetched_at, "releases": releases}
    if not_found == len(attempts):
        raise NotFound(f"{group}:{artifact}")
    raise NetworkFailure("; ".join(errors) or "no usable source")


def connector_releases(fetcher: Fetcher, group: str, artifact: str) -> dict[str, Any]:
    try:
        return exchange_connector(fetcher, group, artifact)
    except NotFound:
        fetcher.warnings.append("not found in Exchange asset API; trying Maven sources")
    except (NetworkFailure, ValueError) as error:
        fetcher.warnings.append(f"Exchange asset API unusable ({error}); trying Maven sources")
    return maven_connector(fetcher, group, artifact)


def plugin_releases(fetcher: Fetcher, group: str, artifact: str) -> dict[str, Any]:
    url = RELEASES_URL.format(path=f"{group.replace('.', '/')}/{artifact}")
    body, fetched_at = fetcher.get(url, CONNECTOR_TTL)
    versions = release_versions(maven_metadata_versions(body))
    if not versions:
        raise NotFound(f"{group}:{artifact}")
    return {
        "source": "mulesoft-releases",
        "fetchedAt": fetched_at,
        "releases": [{"version": v, "minMuleVersion": None, "java": None} for v in versions],
    }


def parse_java_support(adoc: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    in_table = False
    for line in adoc.splitlines():
        if line.startswith("|==="):
            if in_table and rows:
                break
            in_table = not in_table
            continue
        if not in_table or not line.startswith("|") or "Java Version" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        match = re.match(r"(\d+\.\d+)\s*(LTS|Edge)?", cells[0]) if len(cells) >= 2 else None
        if not match:
            continue
        java = sorted({int(n) for n in re.findall(r"\d+", cells[1])})
        rows.append({"version": match.group(1), "channel": match.group(2) or "", "java": java})
    return rows


def runtime_support(fetcher: Fetcher) -> dict[str, Any]:
    body, fetched_at = fetcher.get(JAVA_SUPPORT_URL, RUNTIME_TTL)
    rows = parse_java_support(body)
    if not rows:
        raise ValueError("could not parse the Java support table")
    return {"source": "mulesoft-docs-general", "fetchedAt": fetched_at, "runtimes": rows}


# ---------------------------------------------------------------------------------------------
# Selection


def select(
    releases: list[dict[str, Any]], mule: str | None, java: int | None
) -> tuple[dict[str, Any] | None, list[str]]:
    """Newest release compatible with the given runtime and Java, plus caveats."""
    caveats: list[str] = []
    for release in reversed(releases):
        minimum = release.get("minMuleVersion")
        if mule and minimum and not version_lte(minimum, mule):
            continue
        if java is not None and release.get("java") is not None and java not in release["java"]:
            continue
        if mule and not minimum:
            caveats.append("minimum Mule version unknown from this source; verify before adopting")
        if java is not None and release.get("java") is None:
            caveats.append("Java support unknown from this source; verify before adopting")
        return release, caveats
    return None, caveats


def describe(release: dict[str, Any] | None) -> dict[str, Any] | None:
    return None if release is None else dict(release)


def resolve_connector(name: str) -> tuple[str, str]:
    if name in CONNECTORS:
        return CONNECTORS[name]
    if ":" in name:
        group, artifact = name.split(":", 1)
        if group and artifact:
            return group, artifact
    raise NotFound(f"unknown connector alias '{name}'; use group:artifact or one of: {', '.join(sorted(CONNECTORS))}")


def connector_result(
    fetcher: Fetcher, name: str, mule: str | None, java: int | None, offline: bool, snapshot: dict[str, Any]
) -> dict[str, Any]:
    group, artifact = resolve_connector(name)
    if offline:
        entry = snapshot.get("connectors", {}).get(name) or next(
            (v for v in snapshot.get("connectors", {}).values() if v.get("artifactId") == artifact and v.get("groupId") == group),
            None,
        )
        if not entry:
            raise NotFound(f"{group}:{artifact} is not in the snapshot")
        return {
            "groupId": group,
            "artifactId": artifact,
            "latest": entry["latest"],
            "minMuleVersion": entry.get("minMuleVersion"),
            "java": entry.get("java"),
            "verified": False,
            "asOf": snapshot.get("generatedAt"),
            "source": "snapshot",
            "note": "offline snapshot, unverified; compatibility filtering is not applied",
        }
    data = connector_releases(fetcher, group, artifact)
    releases = data["releases"]
    if not releases:
        raise NotFound(f"{group}:{artifact} has no release versions")
    latest = releases[-1]
    chosen, caveats = select(releases, mule, java)
    fetcher.warnings.extend(caveats)
    result = {
        "groupId": group,
        "artifactId": artifact,
        "latest": describe(latest),
        "latestCompatible": describe(chosen),
        "constraints": {"mule": mule, "java": java},
        "verified": True,
        "source": data["source"],
        "fetchedAt": data["fetchedAt"],
    }
    if chosen is None:
        result["note"] = "no release satisfies the given Mule and Java constraints"
    return result


def plugin_result(fetcher: Fetcher, name: str, offline: bool, snapshot: dict[str, Any]) -> dict[str, Any]:
    group, artifact = PLUGINS[name]
    if offline:
        entry = snapshot.get("plugins", {}).get(name)
        if not entry:
            raise NotFound(f"{name} is not in the snapshot")
        return {"groupId": group, "artifactId": artifact, "latest": entry["latest"], "verified": False,
                "asOf": snapshot.get("generatedAt"), "source": "snapshot"}
    data = plugin_releases(fetcher, group, artifact)
    return {
        "groupId": group,
        "artifactId": artifact,
        "latest": data["releases"][-1]["version"],
        "verified": True,
        "source": data["source"],
        "fetchedAt": data["fetchedAt"],
    }


# ---------------------------------------------------------------------------------------------
# POM check


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(node: ET.Element, name: str) -> str | None:
    for child in node:
        if strip_ns(child.tag) == name and child.text:
            return child.text.strip()
    return None


def pom_properties(root: ET.Element) -> dict[str, str]:
    properties: dict[str, str] = {}
    for child in root:
        if strip_ns(child.tag) == "properties":
            for prop in child:
                if prop.text:
                    properties[strip_ns(prop.tag)] = prop.text.strip()
    return properties


def resolve_property(value: str | None, properties: dict[str, str]) -> str | None:
    if value is None:
        return None
    for _ in range(5):
        replaced = re.sub(r"\$\{([^}]+)\}", lambda m: properties.get(m.group(1), m.group(0)), value)
        if replaced == value:
            break
        value = replaced
    return value


def read_project(pom: Path) -> dict[str, Any]:
    root = ET.parse(pom).getroot()
    properties = pom_properties(root)
    dependencies: list[dict[str, str | None]] = []
    plugins: list[dict[str, str | None]] = []
    for node in root.iter():
        name = strip_ns(node.tag)
        if name == "dependency" and child_text(node, "classifier") == "mule-plugin":
            dependencies.append(
                {
                    "groupId": resolve_property(child_text(node, "groupId"), properties),
                    "artifactId": resolve_property(child_text(node, "artifactId"), properties),
                    "version": resolve_property(child_text(node, "version"), properties),
                }
            )
        elif name == "plugin":
            artifact = resolve_property(child_text(node, "artifactId"), properties)
            if artifact in {a for _, a in PLUGINS.values()}:
                plugins.append(
                    {
                        "groupId": resolve_property(child_text(node, "groupId"), properties),
                        "artifactId": artifact,
                        "version": resolve_property(child_text(node, "version"), properties),
                    }
                )
    min_mule = None
    descriptor = pom.parent / "mule-artifact.json"
    if descriptor.is_file():
        try:
            min_mule = json.loads(descriptor.read_text(encoding="utf-8")).get("minMuleVersion")
        except ValueError:
            pass
    java = None
    for key in ("maven.compiler.release", "java.version", "maven.compiler.source", "maven.compiler.target"):
        value = properties.get(key)
        if value:
            match = re.match(r"(?:1\.)?(\d+)", value)
            if match:
                java = int(match.group(1))
                break
    return {"dependencies": dependencies, "plugins": plugins, "minMuleVersion": min_mule, "java": java}


def check_pom(fetcher: Fetcher, pom: Path, mule: str | None, java: int | None) -> dict[str, Any]:
    project = read_project(pom)
    mule = mule or project["minMuleVersion"]
    java = java if java is not None else project["java"]
    rows: list[dict[str, Any]] = []
    for dep in project["dependencies"]:
        group, artifact, current = dep["groupId"], dep["artifactId"], dep["version"]
        row: dict[str, Any] = {"groupId": group, "artifactId": artifact, "current": current}
        if not group or not artifact:
            row["status"] = "unresolved"
            rows.append(row)
            continue
        try:
            data = connector_releases(fetcher, group, artifact)
        except NotFound:
            row["status"] = "not-found"
            rows.append(row)
            continue
        except (NetworkFailure, ValueError) as error:
            row["status"] = "lookup-failed"
            row["error"] = str(error)
            rows.append(row)
            continue
        releases = data["releases"]
        chosen, caveats = select(releases, mule, java)
        row.update(
            {
                "latest": releases[-1]["version"],
                "latestCompatible": chosen["version"] if chosen else None,
                "source": data["source"],
            }
        )
        if caveats:
            row["caveats"] = sorted(set(caveats))
        if not current or "${" in current:
            row["status"] = "unresolved"
        elif chosen is None:
            row["status"] = "no-compatible-release"
        elif version_key(current) == version_key(chosen["version"]):
            row["status"] = "current"
        elif version_key(current) > version_key(chosen["version"]):
            row["status"] = "ahead-of-compatible"
        else:
            row["status"] = "outdated"
        rows.append(row)
    for plugin in project["plugins"]:
        group, artifact, current = plugin["groupId"], plugin["artifactId"], plugin["version"]
        row = {"groupId": group, "artifactId": artifact, "current": current, "kind": "build-plugin"}
        try:
            latest = plugin_releases(fetcher, *next(c for c in PLUGINS.values() if c[1] == artifact))["releases"][-1]["version"]
        except (NotFound, NetworkFailure) as error:
            row["status"] = "lookup-failed"
            row["error"] = str(error)
            rows.append(row)
            continue
        row["latest"] = latest
        if not current or "${" in current:
            row["status"] = "unresolved"
        else:
            row["status"] = "current" if version_key(current) == version_key(latest) else (
                "outdated" if version_key(current) < version_key(latest) else "ahead-of-compatible"
            )
        rows.append(row)
    return {
        "constraints": {"mule": mule, "java": java},
        "dependencies": rows,
        "note": "latestCompatible honors the project's minMuleVersion and Java level; verify against release notes before upgrading",
    }


# ---------------------------------------------------------------------------------------------
# Snapshot


def load_snapshot(path: Path = SNAPSHOT_PATH) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def build_snapshot(fetcher: Fetcher) -> dict[str, Any]:
    connectors: dict[str, Any] = {}
    for alias, (group, artifact) in sorted(CONNECTORS.items()):
        try:
            data = connector_releases(fetcher, group, artifact)
        except (NotFound, NetworkFailure, ValueError) as error:
            log(f"snapshot: skipping {alias}: {error}")
            continue
        latest = data["releases"][-1]
        connectors[alias] = {
            "groupId": group,
            "artifactId": artifact,
            "latest": latest["version"],
            "minMuleVersion": latest.get("minMuleVersion"),
            "java": latest.get("java"),
        }
    plugins: dict[str, Any] = {}
    for alias, (group, artifact) in sorted(PLUGINS.items()):
        try:
            plugins[alias] = {"latest": plugin_releases(fetcher, group, artifact)["releases"][-1]["version"]}
        except (NotFound, NetworkFailure) as error:
            log(f"snapshot: skipping {alias}: {error}")
    runtime = runtime_support(fetcher)["runtimes"]
    return {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "note": "Unverified offline fallback. Regenerate with mule_versions.py --refresh-snapshot.",
        "connectors": connectors,
        "plugins": plugins,
        "runtimes": runtime,
        "supportPolicy": SUPPORT_POLICY_URL,
    }


# ---------------------------------------------------------------------------------------------
# CLI


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        self.print_usage(sys.stderr)
        log(f"{self.prog}: error: {message}")
        raise SystemExit(EXIT_USAGE)


def build_parser() -> Parser:
    parser = Parser(
        description="Look up Mule connector, plugin, and runtime versions with compatibility evidence. "
        "Exit codes: 0 ok, 2 not found or no compatible release, 3 network or auth failure, 64 usage.",
    )
    parser.add_argument("--offline", action="store_true", help="read the bundled dated snapshot, no network")
    parser.add_argument("--no-cache", action="store_true", help="bypass the local response cache")
    parser.add_argument("--refresh-snapshot", action="store_true", help="rebuild the bundled snapshot from live sources")
    parser.add_argument("--snapshot-path", type=Path, default=SNAPSHOT_PATH, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command")

    connector = sub.add_parser("connector", help="latest and latest compatible release of connectors or modules")
    connector.add_argument("names", nargs="+", help="alias (e.g. salesforce) or group:artifact")
    connector.add_argument("--mule", help="target Mule runtime version, e.g. 4.6.0")
    connector.add_argument("--java", type=int, help="target Java major version, e.g. 17")

    plugins = sub.add_parser("plugins", help="latest MUnit and mule-maven-plugin releases")
    plugins.add_argument("names", nargs="*", help=f"subset of: {', '.join(PLUGINS)} (default: all)")

    sub.add_parser("runtime", help="Mule runtime channels with supported Java versions")

    check = sub.add_parser("check", help="compare a project's mule-plugin dependencies with latest compatible releases")
    check.add_argument("pom", type=Path)
    check.add_argument("--mule", help="override the project's minMuleVersion")
    check.add_argument("--java", type=int, help="override the project's Java level")
    return parser


def emit(command: str, query: Any, result: Any, fetcher: Fetcher, offline: bool) -> None:
    payload = {
        "command": command,
        "query": query,
        "result": result,
        "offline": offline,
        "fetchedAt": iso(time.time()),
        "warnings": sorted(set(fetcher.warnings)),
    }
    print(json.dumps(payload, indent=2))


def run(args: argparse.Namespace) -> int:
    fetcher = Fetcher(use_cache=not args.no_cache)
    if args.refresh_snapshot:
        snapshot = build_snapshot(fetcher)
        args.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        log(f"wrote {args.snapshot_path}")
        return EXIT_OK
    snapshot = load_snapshot(args.snapshot_path) if args.offline else {}
    if args.offline and not snapshot:
        log("offline snapshot missing or unreadable")
        return EXIT_NOT_FOUND
    try:
        if args.command == "connector":
            results = [connector_result(fetcher, n, args.mule, args.java, args.offline, snapshot) for n in args.names]
            emit("connector", args.names, results if len(results) > 1 else results[0], fetcher, args.offline)
            if any(r.get("latestCompatible", True) is None for r in results):
                return EXIT_NOT_FOUND
        elif args.command == "plugins":
            names = args.names or list(PLUGINS)
            bad = [n for n in names if n not in PLUGINS]
            if bad:
                raise NotFound(f"unknown plugin {', '.join(bad)}; choose from {', '.join(PLUGINS)}")
            emit("plugins", names, [plugin_result(fetcher, n, args.offline, snapshot) for n in names], fetcher, args.offline)
        elif args.command == "runtime":
            if args.offline:
                data = {"runtimes": snapshot.get("runtimes", []), "source": "snapshot", "verified": False,
                        "asOf": snapshot.get("generatedAt")}
            else:
                data = runtime_support(fetcher)
                data["verified"] = True
            data["supportPolicy"] = SUPPORT_POLICY_URL
            data["note"] = "standard and extended support end dates change; confirm on the support policy page"
            emit("runtime", None, data, fetcher, args.offline)
        elif args.command == "check":
            if args.offline:
                log("check requires network access; run without --offline")
                return EXIT_NETWORK
            if not args.pom.is_file():
                raise NotFound(f"pom not found: {args.pom}")
            emit("check", str(args.pom.name), check_pom(fetcher, args.pom, args.mule, args.java), fetcher, False)
    except NotFound as error:
        log(f"not found: {error}")
        return EXIT_NOT_FOUND
    except (NetworkFailure, ValueError, ET.ParseError) as error:
        log(f"lookup failed: {error}")
        return EXIT_NETWORK
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command and not args.refresh_snapshot:
        parser.error("a command is required (connector, plugins, runtime, check)")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
