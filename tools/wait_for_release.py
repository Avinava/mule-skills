#!/usr/bin/env python3
"""Wait for exact public npm metadata without exposing npm configuration or errors."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path

PACKAGES = {"mule-lint", "mule-build", "anypoint-connect"}
SEMVER_RE = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)")
NODE_RE = re.compile(r">=\d+\.\d+\.\d+")
ERROR_CODES = {
    "E404", "E401", "E403", "E429", "E500", "E502", "E503", "E504",
    "ETARGET", "ENOTFOUND", "EAI_AGAIN", "ECONNRESET", "ECONNREFUSED",
    "ETIMEDOUT", "ESOCKETTIMEDOUT", "FETCH_ERROR", "CERT_HAS_EXPIRED",
    "UNABLE_TO_VERIFY_LEAF_SIGNATURE", "SELF_SIGNED_CERT_IN_CHAIN",
}


def safe_value(value: object) -> str:
    """Only successful public metadata fields are eligible for bounded logging."""
    if not isinstance(value, str):
        return "<missing>" if value is None else "<non-string>"
    return json.dumps(value[:80], ensure_ascii=True)


def error_code(stdout: str, stderr: str) -> str:
    """Extract only known code tokens; never print error text, paths, or config."""
    try:
        data = json.loads(stdout)
        error = data.get("error") if isinstance(data, dict) else None
        code = error.get("code") if isinstance(error, dict) else None
        if isinstance(code, str) and code in ERROR_CODES:
            return code
    except (ValueError, TypeError):
        pass
    match = re.search(r"(?:npm (?:ERR!|error) code) ([A-Z0-9_]+)\b", stderr)
    return match[1] if match and match[1] in ERROR_CODES else "UNKNOWN"


def wait_for_release(package: str, version: str, attempts: int = 31, delay: int = 10) -> tuple[int, str | None]:
    package = package.removeprefix("@sfdxy/")
    if package not in PACKAGES or not SEMVER_RE.fullmatch(version):
        raise ValueError("expected an allowlisted package and exact stable version")
    spec = f"@sfdxy/{package}@{version}"
    command = [
        "npm", "view", spec, "version", "engines.node", "--json",
        "--registry=https://registry.npmjs.org", "--fetch-retries=0", "--fetch-timeout=20000",
    ]
    # Publication can take minutes to reach registry readers; cap the whole poll window.
    deadline = time.monotonic() + 300
    status = 1
    for attempt in range(1, attempts + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=min(30, remaining), check=False)
        except FileNotFoundError:
            print("Registry check failed: npm executable unavailable (exit=127)")
            return 127, None
        except subprocess.TimeoutExpired:
            status, detail = 124, "npm query timed out (exit=124)"
        except OSError:
            print("Registry check failed: npm could not start (exit=126)")
            return 126, None
        else:
            if result.returncode:
                # Preserve npm's status, converting signal termination to shell convention.
                status = result.returncode if result.returncode > 0 else 128 - result.returncode
                detail = f"npm failed (exit={status}, code={error_code(result.stdout, result.stderr)})"
            else:
                status = 1
                try:
                    metadata = json.loads(result.stdout)
                except ValueError:
                    metadata = None
                if not isinstance(metadata, dict):
                    detail = "npm returned invalid metadata JSON"
                else:
                    published = metadata.get("version")
                    node = metadata.get("engines.node")
                    detail = f"version={safe_value(published)}, engines.node={safe_value(node)}"
                    if published == version and isinstance(node, str) and NODE_RE.fullmatch(node):
                        print(f"{spec}: verified {detail}")
                        return 0, node
                    if published == version and isinstance(node, str) and node:
                        print(f"{spec}: unsupported engines.node={safe_value(node)}")
                        return 1, None
        print(f"{spec}: registry check {attempt}/{attempts}: {detail}")
        if attempt < attempts:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(delay, remaining))
    print(f"{spec}: exact version and supported engines.node not verified within the retry budget")
    return status, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package")
    parser.add_argument("version")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    try:
        status, node = wait_for_release(args.package, args.version)
    except ValueError as exc:
        parser.error(str(exc))
    if status == 0 and args.github_output:
        # Only the validated single-line engine range enters the workflow output.
        with args.github_output.open("a", encoding="utf-8") as output:
            output.write(f"node_requirement={node}\n")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
