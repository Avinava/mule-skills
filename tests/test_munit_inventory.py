from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MUNIT_INVENTORY = ROOT / "skills/mule-testing/scripts/inventory_munit.py"
PROJECT_INVENTORY = ROOT / "skills/mule-docs/scripts/inventory_mule_project.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


munit_inventory = load_module(MUNIT_INVENTORY, "inventory_munit")
project_inventory = load_module(PROJECT_INVENTORY, "inventory_mule_project")


class MUnitInventoryTests(unittest.TestCase):
    def create_project(self, root: Path) -> None:
        (root / "mule-artifact.json").write_text(
            '{"minMuleVersion":"4.9.0"}\n', encoding="utf-8"
        )
        source = root / "src/main/mule/application.xml"
        source.parent.mkdir(parents=True)
        source.write_text('<mule><flow name="sample-flow"/></mule>\n', encoding="utf-8")

    def test_reports_structure_without_selector_values_or_fixture_contents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_project(root)
            fixture = root / "src/test/resources/request.json"
            fixture.parent.mkdir(parents=True)
            fixture.write_text('{"private":"fixture-content-must-not-appear"}\n', encoding="utf-8")
            suite = root / "src/test/munit/sample-suite.xml"
            suite.parent.mkdir(parents=True)
            suite.write_text(
                """<mule xmlns:munit="http://www.mulesoft.org/schema/mule/munit"
  xmlns:munit-tools="http://www.mulesoft.org/schema/mule/munit-tools">
  <munit:test name="sample-flow-success">
    <munit:behavior>
      <munit-tools:mock-when processor="http:request">
        <munit-tools:with-attributes>
          <munit-tools:with-attribute attributeName="method" whereValue="secret-selector-value"/>
        </munit-tools:with-attributes>
      </munit-tools:mock-when>
    </munit:behavior>
    <munit:execution><flow-ref name="sample-flow"/><set-payload value="request.json"/></munit:execution>
    <munit:validation><munit-tools:assert-that expression="#[payload]"/></munit:validation>
  </munit:test>
</mule>
""",
                encoding="utf-8",
            )

            result = munit_inventory.build_inventory(root)
            serialized = json.dumps(result)
            self.assertEqual(1, result["statistics"]["executable_test_count"])
            self.assertEqual(["method"], result["suites"][0]["mocks"][0]["selector_attributes"])
            self.assertEqual(
                ["src/test/resources/request.json"],
                result["suites"][0]["fixture_references"],
            )
            self.assertEqual("sample-flow", result["suites"][0]["inferred_flow_targets"][0]["name"])
            self.assertNotIn("secret-selector-value", serialized)
            self.assertNotIn("fixture-content-must-not-appear", serialized)

    def test_valid_project_without_tests_is_successful_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_project(root)
            result = subprocess.run(
                [sys.executable, str(MUNIT_INVENTORY), str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            inventory = json.loads(result.stdout)
            self.assertEqual(0, inventory["statistics"]["executable_test_count"])
            self.assertTrue(any(item["code"] == "no-executable-tests" for item in inventory["findings"]))

    def test_non_mule_target_exits_two(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [sys.executable, str(MUNIT_INVENTORY), temporary],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(2, result.returncode)


class ProjectInventoryPathTests(unittest.TestCase):
    def test_only_canonical_source_roots_are_inventoried(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "mule-artifact.json").write_text("{}\n", encoding="utf-8")
            expected = root / "src/main/mule/application.xml"
            expected.parent.mkdir(parents=True)
            expected.write_text('<mule><flow name="expected"/></mule>\n', encoding="utf-8")

            misplaced = root / "examples/src/main/mule/misplaced.xml"
            misplaced.parent.mkdir(parents=True)
            misplaced.write_text('<mule><flow name="misplaced"/></mule>\n', encoding="utf-8")

            backup = root / "backup/src/main/mule/backup.xml"
            backup.parent.mkdir(parents=True)
            backup.write_text('<mule><flow name="backup"/></mule>\n', encoding="utf-8")

            inventory = project_inventory.build_inventory(root)
            self.assertEqual(["src/main/mule/application.xml"], inventory["mule_xml_files"])
            self.assertEqual(["expected"], [item["name"] for item in inventory["flows"]])


if __name__ == "__main__":
    unittest.main()
