#!/usr/bin/env python3
"""Update one approved ecosystem pin, then regenerate all derived files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from generate_ecosystem import generated_files, load_manifest


SEMVER_RE = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", help="manifest key or @sfdxy package name")
    parser.add_argument("version", help="exact stable semantic version")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()

    if not SEMVER_RE.fullmatch(args.version):
        parser.error("version must be an exact stable semantic version such as 1.26.0")

    manifest = load_manifest(root)
    packages = manifest["packages"]
    requested = args.package.removeprefix("@sfdxy/")
    if requested not in packages:
        parser.error(f"package must be one of: {', '.join(packages)}")

    package = packages[requested]
    old_version = package["version"]
    package["version"] = args.version
    (root / "ecosystem.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Pin references in prose, skills, and installer guidance remain useful to readers. Keep them
    # synchronized mechanically while generated host files come directly from the manifest.
    pattern = re.compile(rf'{re.escape(package["npm"])}@{re.escape(old_version)}\b')
    candidates = [root / "README.md", root / "install/install.sh"]
    for directory in ("docs", "install", "skills"):
        for suffix in ("*.md", "*.json", "*.toml", "*.sh", "*.yaml", "*.yml"):
            candidates.extend((root / directory).rglob(suffix))
    for path in sorted(set(candidates)):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        updated = pattern.sub(f'{package["npm"]}@{args.version}', text)
        updated = updated.replace(
            f"@sfdxy%2F{requested}/{old_version}",
            f"@sfdxy%2F{requested}/{args.version}",
        )
        if updated != text:
            path.write_text(updated, encoding="utf-8")

    for path, content in generated_files(root, manifest).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    print(f'{package["npm"]}: {old_version} -> {args.version}')
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"ecosystem update failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
