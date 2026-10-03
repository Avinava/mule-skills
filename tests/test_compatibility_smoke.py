from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("compatibility_smoke", ROOT / "tools/compatibility_smoke.py")
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


def report(status="complete"):
    return {
        "schemaVersion": 1,
        "tool": {"name": "mule-lint", "version": "1.0.0"},
        "execution": {"status": status, "diagnostics": [] if status == "complete" else [
            {"kind": "no-files" if status == "no-files" else "parse-error", "message": "synthetic"}
        ]},
        "scan": {"scopeKnown": True, "target": {"kind": "file", "path": "."},
                 "enabledRuleIds": [], "include": [], "exclude": []},
        "selection": {"quiet": False},
        "gate": {"status": "not-evaluated"},
        "summary": {"totalFiles": 0 if status == "no-files" else 1, "totalIssues": 0,
                    "bySeverity": {"error": 0, "warning": 0, "info": 0}},
        "findings": [],
    }


class ContractTests(unittest.TestCase):
    def test_accepts_all_execution_states_and_additive_fields(self):
        for status in ("complete", "incomplete", "no-files"):
            value = report(status)
            value["futureField"] = True
            self.assertEqual(value, smoke.validate_report(value, status))

    def test_missing_or_unknown_envelopes_do_not_fall_back_to_legacy(self):
        for value in (None, [], {"schemaVersion": 2}, {"report": report()}, {**report(), "schemaVersion": True}):
            with self.subTest(value=value), self.assertRaises(smoke.SmokeError):
                smoke.canonical_result({"structuredContent": value}, "complete", advertised=False, required=False)

    def test_legacy_is_allowed_only_when_neither_advertised_nor_required(self):
        self.assertIsNone(smoke.canonical_result({}, "complete", advertised=False, required=False))
        for advertised, required in ((True, False), (False, True)):
            with self.assertRaises(smoke.SmokeError):
                smoke.canonical_result({}, "complete", advertised=advertised, required=required)

    def test_incomplete_cannot_pass_or_warn_at_gate(self):
        for status in ("incomplete", "no-files"):
            for gate in ("passed", "warning"):
                value = report(status)
                value["gate"]["status"] = gate
                with self.assertRaises(smoke.SmokeError):
                    smoke.validate_report(value, status)

    def test_tool_error_must_match_execution(self):
        for status in ("complete", "incomplete", "no-files"):
            with self.assertRaises(smoke.SmokeError):
                smoke.canonical_result({"structuredContent": report(status), "isError": status == "complete"},
                                       status, advertised=True, required=True)

    def test_rejects_unknown_scope_malformed_nested_fields_and_missing_diagnostics(self):
        for key in ("tool", "execution", "scan", "selection", "gate", "summary"):
            for bad in (None, [], "invalid"):
                value = report()
                value[key] = bad
                with self.subTest(key=key, bad=bad), self.assertRaises(smoke.SmokeError):
                    smoke.validate_report(value, "complete")
        value = report()
        value["scan"]["scopeKnown"] = False
        with self.assertRaises(smoke.SmokeError):
            smoke.validate_report(value, "complete")
        value = report("incomplete")
        value["execution"]["diagnostics"] = []
        with self.assertRaises(smoke.SmokeError):
            smoke.validate_report(value, "incomplete")

    def test_finding_identity_counts_and_location(self):
        value = report()
        finding = {"ruleId": "EXAMPLE-001", "message": "synthetic", "severity": "warning",
                   "fingerprintVersion": "muleLint/v1", "fingerprint": "same", "occurrence": 1,
                   "standardIds": [], "location": {"scope": "project"}}
        value["findings"] = [finding, {**finding, "occurrence": 2}]
        value["summary"]["totalIssues"] = 2
        value["summary"]["bySeverity"]["warning"] = 2
        smoke.validate_report(value, "complete")
        for location in ({"scope": "file", "path": "/private/file.xml"},
                         {"scope": "file", "path": "../outside.xml"},
                         {"scope": "file", "path": "C:\\private\\file.xml"},
                         {"scope": "project", "line": 0}):
            changed = copy.deepcopy(value)
            changed["findings"][0]["location"] = location
            with self.subTest(location=location), self.assertRaises(smoke.SmokeError):
                smoke.validate_report(changed, "complete")
        value["findings"][1]["occurrence"] = 1
        with self.assertRaises(smoke.SmokeError):
            smoke.validate_report(value, "complete")


class ProcessTests(unittest.TestCase):
    def test_default_launch_uses_only_exact_host_pins(self):
        with patch.object(smoke.shutil, "which", return_value="/synthetic/npx"):
            commands = smoke.launch_commands(ROOT, None)
        config = json.loads((ROOT / "install/hosts/mcp.json").read_text())["mcpServers"]
        for name, command in commands.items():
            self.assertEqual(["/synthetic/npx", *config[name]["args"]], command)

    def test_rejects_host_env_override_and_unpinned_command(self):
        for override in ({"env": {"TOKEN": "synthetic"}}, {"args": ["-y", "@sfdxy/mule-lint@latest", "mcp"]}):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / "install/hosts").mkdir(parents=True)
                (root / "ecosystem.json").write_bytes((ROOT / "ecosystem.json").read_bytes())
                config = json.loads((ROOT / "install/hosts/mcp.json").read_text())
                config["mcpServers"]["mule-lint"].update(override)
                (root / "install/hosts/mcp.json").write_text(json.dumps(config))
                with self.assertRaises(smoke.SmokeError):
                    smoke.launch_commands(root, None)

    def test_source_mode_verifies_identity_and_built_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            for name, entry in smoke.SERVER_BINS.items():
                package = source / name
                (package / entry).parent.mkdir(parents=True)
                (package / "package.json").write_text(json.dumps({"name": f"@sfdxy/{name}"}))
                (package / entry).write_text("// synthetic")
            commands = smoke.launch_commands(ROOT, source)
            self.assertEqual(str((source / "mule-lint" / smoke.SERVER_BINS["mule-lint"]).resolve()), commands["mule-lint"][1])
            (source / "mule-lint/package.json").write_text('{"name":"unexpected"}')
            with self.assertRaises(smoke.SmokeError):
                smoke.launch_commands(ROOT, source)

    def test_environment_excludes_credentials_and_disables_lifecycle_scripts(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {
            "ANYPOINT_TOKEN": "synthetic", "NODE_OPTIONS": "--require=/synthetic", "NPM_TOKEN": "synthetic",
            "HTTPS_PROXY": "http://proxy.example:8080", "NODE_EXTRA_CA_CERTS": "/synthetic/ca.pem"
        }):
            env = smoke.isolated_env(Path(temporary) / "home")
            for key in ("ANYPOINT_TOKEN", "NODE_OPTIONS", "NPM_TOKEN"):
                self.assertNotIn(key, env)
            self.assertEqual("true", env["NPM_CONFIG_IGNORE_SCRIPTS"])
            self.assertTrue(Path(env["NPM_CONFIG_USERCONFIG"]).is_file())
            self.assertEqual(env["HOME"], env["TMPDIR"])
            self.assertEqual("http://proxy.example:8080", env["HTTPS_PROXY"])
            self.assertEqual("/synthetic/ca.pem", env["NODE_EXTRA_CA_CERTS"])

    def test_real_stdio_discovery_and_mutation_allowlist(self):
        script = '''import json, sys
for line in sys.stdin:
    request = json.loads(line)
    if "id" in request:
        print(json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": {"tools": [{"name": "synthetic"}]}}), flush=True)
'''
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            client = smoke.StdioClient([sys.executable, "-u", "-c", script], root, smoke.isolated_env(root / "home"), 2)
            try:
                self.assertEqual([{"name": "synthetic"}], client.list_all("tools/list", "tools"))
                for method, params in (("tools/call", {"name": "publish_app_jar"}),
                                       ("tools/call", {"name": "whoami"}),
                                       ("resources/read", {"uri": "anypoint://credentials"}),
                                       ("tools/call", {"name": "run_lint_analysis", "arguments": {"projectPath": str(root.parent)}})):
                    with self.assertRaises(smoke.SmokeError):
                        client.request(method, params)
            finally:
                client.close()
            self.assertIsNotNone(client.process.poll())

    def test_request_timeout_reaps_its_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            client = smoke.StdioClient([sys.executable, "-c", "import time; time.sleep(60)"],
                                      root, smoke.isolated_env(root / "home"), 0.02)
            try:
                with self.assertRaisesRegex(smoke.SmokeError, "Timed out"):
                    client.request("initialize")
            finally:
                client.close()
            self.assertIsNotNone(client.process.poll())


if __name__ == "__main__":
    unittest.main()


class CapabilityTests(unittest.TestCase):
    def test_rejects_removed_tools_inputs_types_and_resources(self):
        expected = {"tools": {"scan": {"path": "string"}}, "resources": ["example://rules"]}
        tool = {"name": "scan", "inputSchema": {"properties": {"path": {"type": "string"}}}}
        resources = [{"uri": "example://rules"}]
        smoke.validate_capabilities([tool], resources, expected)
        smoke.validate_capabilities([tool, {"name": "additive"}], resources, expected)
        cases = [([], resources), ([{**tool, "inputSchema": {}}], resources),
                 ([{**tool, "inputSchema": {"properties": {"path": {"type": "number"}}}}], resources),
                 ([tool], [])]
        for tools, actual_resources in cases:
            with self.subTest(tools=tools, resources=actual_resources), self.assertRaises(smoke.SmokeError):
                smoke.validate_capabilities(tools, actual_resources, expected)

    def test_detects_required_argument_and_enum_drift_without_invocation(self):
        expected = {"tools": {"scan": {"path": "string", "profile": "string"}}, "resources": [],
                    "examples": {"scan": [{"path": "/synthetic"}, {"path": "/synthetic", "profile": "recommended"}]}}
        schema = {"type": "object", "properties": {"path": {"type": "string"},
                  "profile": {"type": "string", "enum": ["recommended", "strict"]}}, "required": ["path"]}
        smoke.validate_capabilities([{"name": "scan", "inputSchema": schema}], [], expected)
        for changed in ({**schema, "required": ["path", "profile"]},
                        {**schema, "required": ["path", "newArgument"]},
                        {**schema, "properties": {**schema["properties"], "profile": {"type": "string", "enum": ["strict"]}}},
                        {**schema, "properties": {"path": {"anyOf": "invalid"}}}):
            with self.subTest(schema=changed), self.assertRaises(smoke.SmokeError):
                smoke.validate_capabilities([{"name": "scan", "inputSchema": changed}], [], expected)
