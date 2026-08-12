from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "skills/mule-development/scripts/check_embedded_expressions.py"
VALIDATOR = ROOT / "scripts/validate_repository.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


checker = load_module(CHECKER, "check_embedded_expressions")


class EmbeddedExpressionTests(unittest.TestCase):
    def write_xml(self, root: Path, content: str) -> Path:
        path = root / "src/main/mule/example.xml"
        path.parent.mkdir(parents=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_accepts_valid_expression_with_whitespace_and_array_suffix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_xml(
                root,
                "<mule><value><![CDATA[  #[output application/java --- [1, 2]]  ]]></value></mule>",
            )
            self.assertEqual([], checker.check_project(root))

    def test_reports_truncated_expression_with_line(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.write_xml(
                root,
                "<mule>\n<value><![CDATA[#[output application/java\n---\n{a: 1}\n]]></value>\n</mule>",
            )
            findings = checker.check_project(root)
            self.assertEqual(1, len(findings))
            self.assertEqual(path, findings[0].path)
            self.assertEqual(2, findings[0].line)

    def test_ignores_direct_dataweave_cdata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_xml(
                root,
                "<mule><ee:set-payload><![CDATA[%dw 2.0\n---\n{a: 1}]]></ee:set-payload></mule>",
            )
            self.assertEqual([], checker.check_project(root))

    def test_ignores_cdata_markers_serialized_in_studio_comment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_xml(
                root,
                """<mule>
<!-- [STUDIO:<set-payload><![CDATA[#[output application/json
---
{a: 1}&#93;&#93;&#93;></set-payload> [STUDIO] -->
</mule>""",
            )
            self.assertEqual([], checker.check_project(root))

    def test_reports_each_invalid_block(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_xml(
                root,
                "<mule><a><![CDATA[#[{a: 1}]]></a><b><![CDATA[#[{b: 2}]]></b></mule>",
            )
            self.assertEqual(2, len(checker.check_project(root)))

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_xml(root, "<mule><a><![CDATA[#[{a: 1}]]></a></mule>")
            result = subprocess.run(
                [sys.executable, str(CHECKER), str(root)], capture_output=True, text=True, check=False
            )
            self.assertEqual(1, result.returncode)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_xml(root, "<mule><a><![CDATA[#[{a: 1}]]]></a></mule>")
            result = subprocess.run(
                [sys.executable, str(CHECKER), str(root)], capture_output=True, text=True, check=False
            )
            self.assertEqual(0, result.returncode)
            self.assertIn("clean", result.stdout)
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [sys.executable, str(CHECKER), temporary], capture_output=True, text=True, check=False
            )
            self.assertEqual(2, result.returncode)
        result = subprocess.run(
            [sys.executable, str(CHECKER)], capture_output=True, text=True, check=False
        )
        self.assertEqual(2, result.returncode)
        result = subprocess.run(
            [sys.executable, str(CHECKER), "--help"], capture_output=True, text=True, check=False
        )
        self.assertEqual(0, result.returncode)
        self.assertIn("usage:", result.stdout)


class RepositoryValidationTests(unittest.TestCase):
    def test_help(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--help"], capture_output=True, text=True, check=False
        )
        self.assertEqual(0, result.returncode)
        self.assertIn("usage:", result.stdout)

    def test_repository_is_structurally_valid(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(ROOT)], capture_output=True, text=True, check=False
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
