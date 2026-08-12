#!/usr/bin/env python3
"""Detect truncated Mule expressions embedded in XML CDATA blocks."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


# Match in document order so an XML comment is consumed before CDATA-like text
# serialized inside it. Mule Studio commonly preserves disabled processors this
# way, and those markers are metadata rather than active expressions.
XML_TOKEN_RE = re.compile(r"<!--.*?-->|<!\[CDATA\[(.*?)\]\]>", re.DOTALL)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    message: str


def check_file(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for match in XML_TOKEN_RE.finditer(text):
        content = match.group(1)
        if content is None:  # XML comment
            continue
        stripped = content.strip()
        if not stripped.startswith("#["):
            continue
        if stripped.endswith("]"):
            continue
        line = text.count("\n", 0, match.start(1)) + 1
        findings.append(
            Finding(
                path=path,
                line=line,
                message="CDATA starts with '#[' but does not end with the expression-closing ']'",
            )
        )
    return findings


def check_project(root: Path) -> list[Finding]:
    source_root = root / "src"
    if not source_root.is_dir():
        raise FileNotFoundError(f"Mule source directory not found: {source_root}")
    findings: list[Finding] = []
    for path in sorted(source_root.rglob("*.xml")):
        if path.is_file():
            findings.extend(check_file(path))
    return findings


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args in (["-h"], ["--help"]):
        print("usage: check_embedded_expressions.py <project-root>")
        return 0
    if len(args) != 1:
        print("usage: check_embedded_expressions.py <project-root>", file=sys.stderr)
        return 2

    root = Path(args[0]).expanduser().resolve()
    try:
        findings = check_project(root)
    except (OSError, UnicodeError) as exc:
        print(f"embedded-expression check failed: {exc}", file=sys.stderr)
        return 2

    for finding in findings:
        try:
            display_path = finding.path.relative_to(root)
        except ValueError:
            display_path = finding.path
        print(f"{display_path}:{finding.line}: {finding.message}")

    if findings:
        print(f"embedded-expression check: {len(findings)} finding(s)", file=sys.stderr)
        return 1

    print("embedded-expression check: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
