#!/usr/bin/env python3
"""Audit generated documentation and skill text for common safety and quality failures."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote


IGNORED_DIRECTORIES = {".git", ".m2", "__MACOSX", "node_modules", "target"}
TEXT_SUFFIXES = {".json", ".md", ".properties", ".py", ".txt", ".yaml", ".yml"}
DOCUMENT_SUFFIXES = {".json", ".md", ".properties", ".txt", ".yaml", ".yml"}
ALLOWED_MERMAID_DIRECTIVES = {
    "classDiagram",
    "erDiagram",
    "flowchart",
    "graph",
    "journey",
    "sequenceDiagram",
    "stateDiagram-v2",
}
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
ABSOLUTE_LOCAL_PATH_RE = re.compile(
    r"(?:/Users/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/|[A-Za-z]:\\Users\\[^\\\s]+\\)"
)
PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
AWS_ACCESS_KEY_RE = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~-]{20,}")
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(password|passwd|client[_-]?secret|api[_-]?key|access[_-]?token|refresh[_-]?token)\b\s*[:=]\s*['\"]?([^\s,'\"}]+)"
)
SCAFFOLD_RE = re.compile(r"\[TODO|TODO:|TBD:|PLACEHOLDER_TEXT|Replace with the first main section")


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    line: int
    code: str
    message: str


def is_within(root: Path, candidate: Path) -> bool:
    try:
        return os.path.commonpath((str(root), str(candidate))) == str(root)
    except ValueError:
        return False


def walk_text_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in TEXT_SUFFIXES:
            yield root
        return

    for directory, names, filenames in os.walk(root, topdown=True, followlinks=False):
        current = Path(directory)
        names[:] = sorted(
            name
            for name in names
            if name not in IGNORED_DIRECTORIES
            and not (current / name).is_symlink()
            and is_within(root, (current / name).resolve(strict=False))
        )
        for filename in sorted(filenames):
            path = current / filename
            if path.is_symlink() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if is_within(root, path.resolve(strict=False)):
                yield path


def display_path(root: Path, path: Path) -> str:
    if root.is_file():
        return path.name
    return path.relative_to(root).as_posix()


def link_boundary(path: Path) -> Path:
    start = path if path.is_dir() else path.parent
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def load_denylist(path: Path | None) -> list[str]:
    if path is None:
        return []
    terms: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        term = line.strip()
        if term and not term.startswith("#"):
            terms.append(term)
    return terms


def placeholder_value(value: str) -> bool:
    lowered = value.casefold()
    return (
        "${" in value
        or "<redacted>" in lowered
        or "<encrypted>" in lowered
        or "example.invalid" in lowered
        or value.startswith("${")
    )


def audit_markdown(
    root: Path, path: Path, lines: list[str], findings: list[Finding]
) -> None:
    shown = display_path(root, path)
    boundary = link_boundary(root)
    fence_open = False
    fence_language = ""
    fence_start = 0
    mermaid_first_line: tuple[int, str] | None = None
    mermaid_line_count = 0

    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if not fence_open:
                fence_open = True
                fence_language = stripped[3:].strip().split()[0] if stripped[3:].strip() else ""
                fence_start = number
                mermaid_first_line = None
                mermaid_line_count = 0
            else:
                if fence_language == "mermaid":
                    if mermaid_first_line is None:
                        findings.append(
                            Finding("error", shown, fence_start, "empty-mermaid", "Mermaid block is empty")
                        )
                    elif mermaid_first_line[1].split()[0] not in ALLOWED_MERMAID_DIRECTIVES:
                        findings.append(
                            Finding(
                                "error",
                                shown,
                                mermaid_first_line[0],
                                "mermaid-directive",
                                f"Unsupported Mermaid directive: {mermaid_first_line[1]}",
                            )
                        )
                    if mermaid_line_count > 80:
                        findings.append(
                            Finding(
                                "warning",
                                shown,
                                fence_start,
                                "large-mermaid",
                                "Mermaid block exceeds 80 non-empty lines; consider splitting it",
                            )
                        )
                fence_open = False
                fence_language = ""
            continue

        if fence_open and fence_language == "mermaid" and stripped:
            mermaid_line_count += 1
            if mermaid_first_line is None:
                mermaid_first_line = (number, stripped)
            if re.match(r"(?i)^click\s+", stripped):
                findings.append(
                    Finding("error", shown, number, "mermaid-click", "Mermaid click handlers are not allowed")
                )

    if fence_open:
        findings.append(
            Finding("error", shown, fence_start, "unclosed-fence", "Markdown code fence is not closed")
        )

    for number, line in enumerate(lines, start=1):
        for match in MARKDOWN_LINK_RE.finditer(line):
            target = match.group(1).strip().strip("<>")
            if (
                not target
                or target.startswith(("#", "http://", "https://", "mailto:", "app://"))
                or "<" in target
                or "{" in target
            ):
                continue
            clean_target = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not clean_target:
                continue
            resolved = (path.parent / clean_target).resolve(strict=False)
            if not is_within(boundary, resolved) or not resolved.exists():
                findings.append(
                    Finding(
                        "error",
                        shown,
                        number,
                        "broken-link",
                        f"Relative link does not resolve: {target}",
                    )
                )


def audit_file(
    root: Path, path: Path, denylist: list[str], findings: list[Finding]
) -> None:
    shown = display_path(root, path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        findings.append(
            Finding("error", shown, 0, "unreadable", f"Could not read file: {error.__class__.__name__}")
        )
        return

    lines = text.splitlines()
    if path.suffix.lower() == ".md":
        audit_markdown(root, path, lines, findings)

    casefolded = text.casefold()
    for term in denylist:
        if term.casefold() in casefolded:
            line = text[: casefolded.index(term.casefold())].count("\n") + 1
            findings.append(
                Finding("error", shown, line, "denylist", "Private denylist term is present")
            )

    for number, line in enumerate(lines, start=1):
        if PRIVATE_KEY_RE.search(line):
            findings.append(
                Finding("error", shown, number, "private-key", "Private key material is present")
            )
        if AWS_ACCESS_KEY_RE.search(line):
            findings.append(
                Finding("error", shown, number, "access-key", "Access-key-like value is present")
            )
        if BEARER_RE.search(line):
            findings.append(
                Finding("error", shown, number, "bearer-token", "Bearer-token-like value is present")
            )
        if path.suffix.lower() in DOCUMENT_SUFFIXES and SCAFFOLD_RE.search(line):
            findings.append(
                Finding("error", shown, number, "scaffold", "Unresolved scaffold text is present")
            )

        if path.suffix.lower() in DOCUMENT_SUFFIXES:
            if ABSOLUTE_LOCAL_PATH_RE.search(line):
                findings.append(
                    Finding("error", shown, number, "local-path", "Local absolute path is present")
                )
            assignment = SECRET_ASSIGNMENT_RE.search(line)
            if assignment and not placeholder_value(assignment.group(2)):
                findings.append(
                    Finding(
                        "error",
                        shown,
                        number,
                        "secret-assignment",
                        f"Possible literal value assigned to {assignment.group(1)}",
                    )
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit documentation for privacy, link, placeholder, and Mermaid issues."
    )
    parser.add_argument("path", help="Documentation file, documentation directory, or skill root")
    parser.add_argument(
        "--denylist-file", help="Optional UTF-8 file containing one forbidden term per line"
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.path).expanduser().resolve()
    if not root.exists():
        print(f"error: audit path does not exist: {root}", file=sys.stderr)
        return 2

    denylist_path = Path(args.denylist_file).expanduser().resolve() if args.denylist_file else None
    if denylist_path is not None and not denylist_path.is_file():
        print(f"error: denylist file does not exist: {denylist_path}", file=sys.stderr)
        return 2

    try:
        denylist = load_denylist(denylist_path)
    except (OSError, UnicodeDecodeError) as error:
        print(f"error: could not read denylist: {error.__class__.__name__}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    files = list(walk_text_files(root))
    for path in files:
        audit_file(root, path, denylist, findings)

    findings.sort(key=lambda item: (item.path, item.line, item.severity, item.code))
    errors = sum(item.severity == "error" for item in findings)
    warnings = sum(item.severity == "warning" for item in findings)

    if args.json:
        print(
            json.dumps(
                {
                    "files_checked": len(files),
                    "errors": errors,
                    "warnings": warnings,
                    "findings": [asdict(item) for item in findings],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        for item in findings:
            location = f"{item.path}:{item.line}" if item.line else item.path
            print(f"{item.severity.upper()} {location} [{item.code}] {item.message}")
        print(f"Checked {len(files)} files: {errors} errors, {warnings} warnings")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
