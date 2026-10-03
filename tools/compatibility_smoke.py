#!/usr/bin/env python3
"""Exercise pinned MCP executables with disposable, credential-free fixtures.

No third-party Python dependencies. Only discovery, public lint resources and
synthetic lint are allowed; build and connector tools are never called.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
SERVER_BINS = {
    "anypoint-connect": "dist/cli.js",
    "mule-build": "dist/bin/mule-build.js",
    "mule-lint": "dist/bin/mule-lint.js",
}
PUBLIC_RESOURCES = {"mule-lint://standards", "mule-lint://rules"}
DISCOVERY_METHODS = {"initialize", "notifications/initialized", "tools/list", "resources/list"}


class SmokeError(Exception):
    """An executable or consumer contract was not satisfied."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise SmokeError(message)


def isolated_env(home: Path) -> dict[str, str]:
    """Do not inherit tokens, NODE_OPTIONS, personal profiles or npm credentials."""
    home.mkdir(parents=True, exist_ok=True)
    # Keep configured network transport and CA trust so registry downloads work in managed
    # environments; do not inherit npm credentials, registries, project config or NODE_OPTIONS.
    transport_keys = (
        "PATH", "SystemRoot", "WINDIR", "PATHEXT", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
        "http_proxy", "https_proxy", "no_proxy", "ALL_PROXY", "all_proxy",
        "NPM_CONFIG_PROXY", "NPM_CONFIG_HTTPS_PROXY", "NPM_CONFIG_NOPROXY",
        "npm_config_proxy", "npm_config_https_proxy", "npm_config_noproxy",
        "NODE_EXTRA_CA_CERTS", "SSL_CERT_FILE", "NODE_USE_ENV_PROXY",
    )
    env = {key: os.environ[key] for key in transport_keys if key in os.environ}
    env.update({
        "HOME": str(home), "USERPROFILE": str(home),
        "XDG_CONFIG_HOME": str(home / "config"), "XDG_CACHE_HOME": str(home / "cache"),
        "NPM_CONFIG_CACHE": str(home / "npm-cache"),
        "NPM_CONFIG_USERCONFIG": str(home / "npmrc"),
        "NPM_CONFIG_GLOBALCONFIG": str(home / "global-npmrc"),
        "NPM_CONFIG_IGNORE_SCRIPTS": "true", "NPM_CONFIG_AUDIT": "false",
        "NPM_CONFIG_FUND": "false", "NO_COLOR": "1", "CI": "true",
        "ANYPOINT_PROFILE": "compatibility-smoke",
        "TMPDIR": str(home), "TEMP": str(home), "TMP": str(home),
    })
    (home / "npmrc").touch()
    (home / "global-npmrc").touch()
    return env


def launch_commands(root: Path, source_root: Path | None) -> dict[str, list[str]]:
    """Accept only the checked-in exact-pin host form, never arbitrary launch config."""
    manifest = json.loads((root / "ecosystem.json").read_text(encoding="utf-8"))
    config = json.loads((root / "install/hosts/mcp.json").read_text(encoding="utf-8"))["mcpServers"]
    require(set(config) == set(SERVER_BINS), "Host configuration must contain the three ecosystem servers")
    commands = {}
    for name, binary in SERVER_BINS.items():
        package = manifest["packages"][name]
        require(package["npm"] == f"@sfdxy/{name}", "Unexpected package identity")
        require(re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", package["version"]), "Package pin must be exact stable semver")
        expected = {"command": "npx", "args": ["-y", f'{package["npm"]}@{package["version"]}', "mcp"]}
        require(config[name] == expected, f"{name}: host command must match the exact manifest pin without environment overrides")
        if source_root is None:
            executable = shutil.which("npx")
            require(executable, "npx is required for released-package checks")
            commands[name] = [executable, *expected["args"]]
        else:
            local = source_root / name
            metadata = json.loads((local / "package.json").read_text(encoding="utf-8"))
            require(metadata.get("name") == package["npm"], f"{name}: local source package identity mismatch")
            entry = local / binary
            require(entry.is_file(), f"{name}: build the local source before running compatibility smoke")
            executable = shutil.which("node")
            require(executable, "node is required for local-source checks")
            commands[name] = [executable, str(entry.resolve()), "mcp"]
    return commands


class StdioClient:
    """Small newline-delimited JSON-RPC client with bounded requests and cleanup."""

    def __init__(self, command: list[str], cwd: Path, env: dict[str, str], timeout: float):
        self.timeout = timeout
        self.fixture_root = cwd.resolve()
        self.sequence = 0
        self.messages: queue.Queue = queue.Queue()
        self.process = subprocess.Popen(
            command, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
            start_new_session=os.name == "posix",
        )
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self) -> None:
        try:
            while True:
                line = self.process.stdout.readline(16 * 1024 * 1024 + 1)
                if not line:
                    raise SmokeError("MCP process closed before responding")
                require(len(line) <= 16 * 1024 * 1024, "MCP response exceeded the smoke size limit")
                if line.strip():
                    message = json.loads(line)
                    require(isinstance(message, dict), "MCP response must be an object")
                    self.messages.put(message)
        except SmokeError as exc:
            self.messages.put(exc)
        except (ValueError, OSError) as exc:
            self.messages.put(SmokeError(f"Invalid MCP transport: {type(exc).__name__}"))

    def request(self, method: str, params: dict | None = None, *, notify: bool = False) -> dict:
        params = params or {}
        safe = method in DISCOVERY_METHODS
        if method == "resources/read":
            safe = params.get("uri") in PUBLIC_RESOURCES
        if method == "tools/call":
            arguments = params.get("arguments", {})
            target = Path(arguments.get("projectPath", "")).resolve()
            safe = (
                params.get("name") == "run_lint_analysis"
                and set(arguments) <= {"projectPath", "profile"}
                and target.is_relative_to(self.fixture_root)
            )
        require(safe, "Request is outside the smoke's discovery and synthetic-lint allowlist")
        self.sequence += 1
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        if not notify:
            payload["id"] = self.sequence
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()
        if notify:
            return {}
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                message = self.messages.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise SmokeError(f"Timed out waiting for {method}") from exc
            if isinstance(message, Exception):
                raise message
            if "method" in message:
                require("id" not in message, "Unexpected server request; interactive access is not supported")
                continue
            require(message.get("jsonrpc") == "2.0" and message.get("id") == self.sequence,
                    "Unexpected JSON-RPC response identity")
            require("error" not in message, f"{method} returned an RPC error")
            require(isinstance(message.get("result"), dict), f"{method} returned no result object")
            return message["result"]

    def list_all(self, method: str, key: str) -> list[dict]:
        items, seen, params = [], set(), {}
        while True:
            result = self.request(method, params)
            require(isinstance(result.get(key), list), f"{method} must return {key}")
            require(all(isinstance(item, dict) for item in result[key]), f"{method} entries must be objects")
            items.extend(result[key])
            cursor = result.get("nextCursor")
            if cursor is None:
                return items
            require(isinstance(cursor, str) and cursor not in seen, "Invalid or repeated discovery cursor")
            seen.add(cursor)
            params = {"cursor": cursor}

    def close(self) -> None:
        if self.process.stdin:
            self.process.stdin.close()
        stop_owned_process(self.process)
        self.reader.join(timeout=2)
        self.process.stdout.close()


def stop_owned_process(process: subprocess.Popen) -> None:
    """Reap only the subprocess/session created by this smoke, including npx children."""
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    # npx can exit before a descendant closes stdio. Its session is still ours.
    def terminate(sig: int) -> None:
        try:
            if os.name == "posix":
                os.killpg(process.pid, sig)
            elif process.poll() is None:
                process.kill() if sig == signal.SIGKILL else process.terminate()
        except ProcessLookupError:
            pass
    terminate(signal.SIGTERM)
    if os.name == "posix":
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            process.poll()
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            terminate(signal.SIGKILL)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        terminate(signal.SIGKILL)
        process.wait(timeout=2)


def object_field(value: dict, key: str) -> dict:
    result = value.get(key)
    require(isinstance(result, dict), f"{key} must be an object")
    return result


def validate_report(report: object, expected_status: str) -> dict:
    """Validate the fields the skills consume, with additive v1 fields allowed."""
    require(isinstance(report, dict), "Canonical report must be a top-level object")
    require(type(report.get("schemaVersion")) is int and report["schemaVersion"] == 1,
            "Unsupported or missing canonical schemaVersion")
    tool = object_field(report, "tool")
    require(all(isinstance(tool.get(key), str) and tool[key] for key in ("name", "version")), "Tool identity missing")
    execution = object_field(report, "execution")
    require(execution.get("status") == expected_status, f"Expected execution.status={expected_status}")
    diagnostics = execution.get("diagnostics")
    require(isinstance(diagnostics, list), "Execution diagnostics must be present")
    require(not diagnostics if expected_status == "complete" else bool(diagnostics),
            "Execution diagnostics disagree with completeness")
    require(all(isinstance(d, dict) and d.get("kind") in {"parse-error", "rule-error", "no-files"}
                and isinstance(d.get("message"), str) for d in diagnostics), "Invalid execution diagnostic")
    if expected_status == "no-files":
        require(all(d["kind"] == "no-files" for d in diagnostics),
                "No-files diagnostic kind disagrees with status")
    scan = object_field(report, "scan")
    require(scan.get("scopeKnown") is True, "Executable scan scope must be known")
    require(isinstance(scan.get("target"), dict) and scan["target"].get("kind") in {"file", "project"},
            "Scan target missing")
    require(all(isinstance(scan.get(key), list) for key in ("enabledRuleIds", "include", "exclude")),
            "Rule selection and scan scope must be present")
    require(isinstance(object_field(report, "selection").get("quiet"), bool), "Selection context missing")
    gate = object_field(report, "gate").get("status")
    require(gate in {"not-evaluated", "passed", "warning", "failed"}, "Gate status missing")
    require(expected_status == "complete" or gate not in {"passed", "warning"},
            "Incomplete/no-files scan must never pass a gate")
    findings = report.get("findings")
    require(isinstance(findings, list), "Canonical findings must be a top-level list")
    counts = {"error": 0, "warning": 0, "info": 0}
    occurrences = {}
    for finding in findings:
        require(isinstance(finding, dict), "Invalid finding")
        require(finding.get("severity") in counts, "Invalid finding severity")
        require(all(isinstance(finding.get(key), str) and finding[key] for key in ("ruleId", "message", "fingerprint")),
                "Finding identity missing")
        require(finding.get("fingerprintVersion") == "muleLint/v1", "Unsupported fingerprint version")
        fingerprint = finding["fingerprint"]
        occurrences[fingerprint] = occurrences.get(fingerprint, 0) + 1
        require(type(finding.get("occurrence")) is int and finding["occurrence"] == occurrences[fingerprint],
                "Duplicate occurrence identity is invalid")
        require(isinstance(finding.get("standardIds"), list), "Standards references missing")
        location = object_field(finding, "location")
        require(location.get("scope") in {"project", "file"}, "Location scope missing")
        if location["scope"] == "file":
            require(isinstance(location.get("path"), str) and location["path"] and not Path(location["path"]).is_absolute()
                    and ".." not in Path(location["path"]).parts
                    and not re.match(r"^[A-Za-z]:", location["path"]),
                    "File location must be relative")
        for key in ("line", "column"):
            require(key not in location or (type(location[key]) is int and location[key] > 0), "Invalid source position")
        counts[finding["severity"]] += 1
    summary = object_field(report, "summary")
    require(all(type(summary.get(key)) is int and summary[key] >= 0 for key in ("totalFiles", "totalIssues")),
            "Summary counts must be nonnegative integers")
    require(summary.get("totalIssues") == len(findings) and summary.get("bySeverity") == counts,
            "Finding counts do not match the canonical report")
    require(summary.get("totalFiles", -1) == 0 if expected_status == "no-files" else summary.get("totalFiles", 0) > 0,
            "File count disagrees with execution status")
    return report


def canonical_result(result: dict, status: str, *, advertised: bool, required: bool) -> dict | None:
    if "structuredContent" not in result:
        require(not advertised and not required, "Canonical report-v1 structuredContent is required but missing")
        return None
    # A malformed/unknown structured report is an error, never a legacy fallback.
    report = validate_report(result["structuredContent"], status)
    require(result.get("isError", False) is (status != "complete"), "MCP isError disagrees with execution status")
    return report


def cli_json(command: list[str], target: Path, output_format: str, cwd: Path,
             env: dict[str, str], timeout: float) -> tuple[object, int]:
    process = subprocess.Popen(
        [*command[:-1], str(target), "--format", output_format, "--profile", "recommended"],
        cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8", start_new_session=os.name == "posix",
    )
    try:
        stdout, _ = process.communicate(timeout=timeout)
    finally:
        stop_owned_process(process)
        process.stdout.close()
    require(process.returncode >= 0, "Lint CLI terminated unexpectedly")
    try:
        return json.loads(stdout), process.returncode
    except ValueError as exc:
        raise SmokeError(f"Lint CLI did not emit valid {output_format}") from exc


def lint_checks(client: StdioClient, tool: dict, command: list[str], root: Path,
                env: dict[str, str], timeout: float, required: bool) -> str:
    valid = root / "example.xml"
    valid.write_text('<mule xmlns="http://www.mulesoft.org/schema/mule/core"><flow name="example"><set-payload value="ok"/></flow></mule>', encoding="utf-8")
    invalid = root / "invalid.xml"
    invalid.write_text("", encoding="utf-8")
    empty = root / "empty"
    empty.mkdir()
    schema = tool.get("outputSchema", {})
    require(isinstance(schema, dict), "Tool outputSchema must be an object when present")
    require(isinstance(schema.get("properties", {}), dict), "Tool schema properties must be an object")
    advertised = "schemaVersion" in schema.get("properties", {})
    result = client.request("tools/call", {"name": "run_lint_analysis", "arguments": {"projectPath": str(valid), "profile": "recommended"}})
    report = canonical_result(result, "complete", advertised=advertised, required=required)
    legacy, _ = cli_json(command, valid, "json", root, env, timeout)
    require(isinstance(legacy, list), "Legacy CLI json must remain a flat array")
    if report is None:
        require(result.get("isError") is not True, "Legacy synthetic lint returned an error")
        content = result.get("content", [])
        require(any(item.get("type") == "text" and item.get("text") for item in content), "Legacy MCP text missing")
        return "legacy text/flat-json only; execution completeness and report-v1 NOT verified"
    required_keys = schema.get("required", [])
    require(advertised and all(key in required_keys for key in ("schemaVersion", "execution", "findings")),
            "MCP must advertise the top-level canonical outputSchema")
    for target, status, expected_exit in ((valid, "complete", None), (invalid, "incomplete", 3), (empty, "no-files", 2)):
        if target != valid:
            result = client.request("tools/call", {"name": "run_lint_analysis", "arguments": {"projectPath": str(target), "profile": "recommended"}})
            report = canonical_result(result, status, advertised=True, required=True)
        cli, exit_code = cli_json(command, target, "report-json", root, env, timeout)
        validate_report(cli, status)
        require(exit_code in {0, 1} if expected_exit is None else exit_code == expected_exit, f"{status}: wrong CLI exit code")
        require(cli["findings"] == report["findings"], f"{status}: CLI/MCP findings diverged")
    return "report-v1 complete/incomplete/no-files, CLI/MCP parity and legacy flat-json verified"


def accepts_example(value: object, schema: dict) -> bool:
    """Bounded discovery checks for representative inputs, never a tool invocation."""
    require(isinstance(schema, dict), "Input schema node must be an object")
    for union in ("anyOf", "oneOf"):
        if union in schema:
            alternatives = schema[union]
            require(isinstance(alternatives, list) and all(isinstance(item, dict) for item in alternatives), "Invalid schema alternatives")
            matches = sum(accepts_example(value, item) for item in alternatives)
            return matches > 0 if union == "anyOf" else matches == 1
    if "enum" in schema and value not in schema["enum"]:
        return False
    if "const" in schema and value != schema["const"]:
        return False
    kind = schema.get("type")
    matches = {
        "string": isinstance(value, str), "boolean": isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "object": isinstance(value, dict), "array": isinstance(value, list), "null": value is None,
    }
    if kind and not any(matches.get(item, False) for item in (kind if isinstance(kind, list) else [kind])):
        return False
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        require(isinstance(properties, dict) and isinstance(required, list), "Malformed object input schema")
        if not set(required).issubset(value):
            return False
        for key, item in value.items():
            if key not in properties or not accepts_example(item, properties[key]):
                return False
    return True


def validate_capabilities(tools: list[dict], resources: list[dict], expected: dict) -> None:
    """Check consumer-owned minimum contracts without calling platform/build tools."""
    require(isinstance(expected, dict) and isinstance(expected.get("tools"), dict)
            and isinstance(expected.get("resources"), list), "Capability expectations missing")
    catalog = {tool.get("name"): tool for tool in tools}
    for name, fields in expected["tools"].items():
        require(name in catalog, f"Required tool missing: {name}")
        require(isinstance(fields, dict), f"Invalid field expectations: {name}")
        input_schema = catalog[name].get("inputSchema", {})
        require(isinstance(input_schema, dict), f"Malformed input schema: {name}")
        properties = input_schema.get("properties", {})
        require(isinstance(properties, dict), f"Malformed input properties: {name}")
        for field, kind in fields.items():
            schema = properties.get(field, {})
            require(isinstance(schema, dict), f"Malformed input field: {name}.{field}")
            alternatives = schema.get("anyOf", [])
            require(isinstance(alternatives, list) and all(isinstance(value, dict) for value in alternatives), "Malformed input alternatives")
            require(any(value.get("type") == kind for value in [schema, *alternatives]),
                    f"Required input missing or incompatible: {name}.{field} ({kind})")
        for example in expected.get("examples", {}).get(name, []):
            require(accepts_example(example, input_schema), f"Representative input no longer accepted: {name}")
    uris = {resource.get("uri") for resource in resources}
    for uri in expected["resources"]:
        require(uri in uris, f"Required resource missing: {uri}")


def run(root: Path, source_root: Path | None, required: bool, timeout: float) -> None:
    commands = launch_commands(root, source_root)
    capabilities = json.loads((root / "ecosystem.json").read_text(encoding="utf-8"))["capabilities"]
    with tempfile.TemporaryDirectory(prefix="ecosystem-smoke-") as temporary:
        workspace = Path(temporary)
        env = isolated_env(workspace / "home")
        for name, command in commands.items():
            cwd = workspace / name
            cwd.mkdir()
            server_env = env.copy()
            if name == "anypoint-connect":
                # Discovery requires a configured client, but never a real credential or login.
                server_env.update({
                    "ANYPOINT_CLIENT_ID": "synthetic-discovery-client",
                    "ANYPOINT_CLIENT_SECRET": "synthetic-not-a-credential",
                    "ANYPOINT_BASE_URL": "http://127.0.0.1:9",
                    "ANYPOINT_CALLBACK_URL": "http://127.0.0.1:9/callback",
                })
            client = StdioClient(command, cwd, server_env, timeout)
            try:
                hello = client.request("initialize", {
                    "protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "ecosystem-compatibility-smoke", "version": "1.0.0"},
                })
                require(hello.get("protocolVersion") in {"2024-11-05", "2025-03-26", "2025-06-18"},
                        f"{name}: unsupported MCP protocol version")
                require(hello.get("serverInfo", {}).get("version"), f"{name}: server version missing")
                require(all(key in hello.get("capabilities", {}) for key in ("tools", "resources")),
                        f"{name}: discovery capabilities missing")
                client.request("notifications/initialized", notify=True)
                tools = client.list_all("tools/list", "tools")
                resources = client.list_all("resources/list", "resources")
                require(tools and resources, f"{name}: empty tool or resource catalog")
                validate_capabilities(tools, resources, capabilities[name])
                detail = "discovery and capability contract verified; no tool or resource content calls"
                if name == "mule-lint":
                    for uri in sorted(PUBLIC_RESOURCES):
                        require(any(item.get("uri") == uri for item in resources), "Public standards/rules resource missing")
                        require(client.request("resources/read", {"uri": uri}).get("contents"), "Public resource is empty")
                    tool = next((item for item in tools if item.get("name") == "run_lint_analysis"), None)
                    require(tool, "run_lint_analysis is missing")
                    detail = lint_checks(client, tool, command, cwd, env, timeout, required)
                print(f"{name}: {len(tools)} tools, {len(resources)} resources; {detail}", flush=True)
            except SmokeError as exc:
                raise SmokeError(f"{name}: {exc}") from exc
            finally:
                client.close()
    print("Executable compatibility smoke passed (synthetic local checks only).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source-root", type=Path, help="Parent of the three built local source repositories; does not modify pins")
    parser.add_argument("--require-report-v1", action="store_true", help="Reject legacy lint servers without the canonical report contract")
    parser.add_argument("--timeout", type=float, default=120, help="Per-request/CLI deadline in seconds (default: 120)")
    args = parser.parse_args(argv)
    try:
        require(math.isfinite(args.timeout) and args.timeout > 0, "Timeout must be finite and positive")
        run(args.root.resolve(), args.source_root.resolve() if args.source_root else None,
            args.require_report_v1, args.timeout)
    except (SmokeError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(f"Executable compatibility smoke failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
