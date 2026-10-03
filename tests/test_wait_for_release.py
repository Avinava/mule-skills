from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("wait_for_release", ROOT / "tools/wait_for_release.py")
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)


def response(metadata=None, code=0, stderr=""):
    return subprocess.CompletedProcess([], code, json.dumps(metadata), stderr)


class RegistryReadinessTests(unittest.TestCase):
    def run_check(self, results, attempts=2):
        log = io.StringIO()
        with patch.object(registry.subprocess, "run", side_effect=results) as run, \
                patch.object(registry.time, "sleep") as sleep, contextlib.redirect_stdout(log):
            result = registry.wait_for_release("mule-lint", "2.0.0", attempts=attempts)
        return result, log.getvalue(), run, sleep

    def test_exact_json_metadata_works_independently_of_npm_output_defaults(self):
        result, log, run, sleep = self.run_check([response({"version": "2.0.0", "engines.node": ">=20.0.0"})])
        self.assertEqual((0, ">=20.0.0"), result)
        self.assertIn("--json", run.call_args.args[0])
        self.assertIn("--registry=https://registry.npmjs.org", run.call_args.args[0])
        self.assertEqual(30, run.call_args.kwargs["timeout"])
        sleep.assert_not_called()

    def test_not_yet_visible_retries_then_succeeds(self):
        result, log, run, sleep = self.run_check([
            response({"error": {"code": "E404", "summary": "DO_NOT_LOG"}}, 1, "PRIVATE"),
            response({"version": "2.0.0", "engines.node": ">=20.0.0"}),
        ])
        self.assertEqual((0, ">=20.0.0"), result)
        self.assertIn("exit=1, code=E404", log)
        self.assertNotIn("DO_NOT_LOG", log)
        self.assertNotIn("PRIVATE", log)
        sleep.assert_called_once_with(10)

    def test_terminal_npm_failure_preserves_status_and_only_known_codes(self):
        result, log, _, _ = self.run_check([
            response(None, 7, "npm error code ENOTFOUND\nPRIVATE"),
            response({"error": {"code": "TOKEN_secret"}}, 9, "PRIVATE"),
        ])
        self.assertEqual((9, None), result)
        self.assertIn("code=ENOTFOUND", log)
        self.assertIn("exit=9, code=UNKNOWN", log)
        self.assertNotIn("secret", log)
        self.assertNotIn("PRIVATE", log)

    def test_missing_executable_and_start_failure_are_distinct(self):
        for exc, code in ((FileNotFoundError("PRIVATE"), 127), (PermissionError("PRIVATE"), 126)):
            with self.subTest(code=code):
                result, log, _, sleep = self.run_check([exc])
                self.assertEqual((code, None), result)
                self.assertNotIn("PRIVATE", log)
                sleep.assert_not_called()

    def test_timeout_is_bounded_and_does_not_print_captured_output(self):
        result, log, _, _ = self.run_check([
            subprocess.TimeoutExpired("PRIVATE", 30, output="PRIVATE", stderr="PRIVATE")
        ], attempts=1)
        self.assertEqual((124, None), result)
        self.assertIn("timed out", log)
        self.assertNotIn("PRIVATE", log)

    def test_polling_stops_at_five_minute_deadline(self):
        log = io.StringIO()
        with patch.object(registry.time, "monotonic", side_effect=[0, 0, 300]), \
                patch.object(registry.time, "sleep") as sleep, \
                patch.object(registry.subprocess, "run", return_value=response(None, 1)) as run, \
                contextlib.redirect_stdout(log):
            self.assertEqual((1, None), registry.wait_for_release("mule-lint", "2.0.0"))
        run.assert_called_once()
        sleep.assert_not_called()

    def test_bad_or_missing_metadata_cannot_pass(self):
        cases = [[], None, {}, {"version": "1.0.0", "engines.node": ">=20.0.0"},
                 {"version": "2.0.0"}, {"version": "2.0.0", "engines.node": 20}]
        for metadata in cases:
            with self.subTest(metadata=metadata):
                result, _, _, _ = self.run_check([response(metadata)], attempts=1)
                self.assertEqual((1, None), result)
        result, log, _, _ = self.run_check([
            subprocess.CompletedProcess([], 0, "INVALID PRIVATE", "PRIVATE")
        ], attempts=1)
        self.assertEqual((1, None), result)
        self.assertIn("invalid metadata JSON", log)
        self.assertNotIn("PRIVATE", log)

    def test_unsupported_engine_fails_without_retry_and_escapes_log_lines(self):
        value = "^22\n::error::" + "x" * 200
        result, log, _, sleep = self.run_check([
            response({"version": "2.0.0", "engines.node": value})
        ])
        self.assertEqual((1, None), result)
        self.assertIn("unsupported engines.node", log)
        self.assertNotIn("\n::error::", log)
        self.assertLess(len(log), 160)
        sleep.assert_not_called()

    def test_inputs_are_allowlisted_before_starting_npm(self):
        for package, version in (("unknown", "2.0.0"), ("mule-lint", "2.0.0\n"),
                                 ("mule-lint", "latest"), ("--help", "2.0.0")):
            with self.subTest(package=package, version=version), \
                    patch.object(registry.subprocess, "run") as run:
                with self.assertRaises(ValueError):
                    registry.wait_for_release(package, version)
                run.assert_not_called()

    def test_github_output_written_only_after_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            output.write_text("existing=value\n")
            args = ["wait_for_release.py", "mule-lint", "2.0.0", "--github-output", str(output)]
            with patch("sys.argv", args), patch.object(registry, "wait_for_release", return_value=(0, ">=20.0.0")):
                self.assertEqual(0, registry.main())
            self.assertEqual("existing=value\nnode_requirement=>=20.0.0\n", output.read_text())
            before = output.read_text()
            with patch("sys.argv", args), patch.object(registry, "wait_for_release", return_value=(7, None)):
                self.assertEqual(7, registry.main())
            self.assertEqual(before, output.read_text())


if __name__ == "__main__":
    unittest.main()
