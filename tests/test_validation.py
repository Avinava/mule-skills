from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "skills/mule-development/scripts/check_embedded_expressions.py"
VALIDATOR = ROOT / "tools/validate_repository.py"
INSTALLER = ROOT / "install/install.sh"


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


validator = load_module(VALIDATOR, "validate_repository")


class PluginManifestTests(unittest.TestCase):
    """The plugin and portability checks must fail on the breakage they were added for."""

    def copy_repository(self, temporary: str) -> Path:
        root = Path(temporary) / "repo"
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        return root

    def assert_finding(self, root: Path, fragment: str):
        findings = validator.validate_repository(root)
        self.assertTrue(
            any(fragment in finding for finding in findings),
            f"expected a finding containing {fragment!r}, got: {findings}",
        )

    def edit(self, path: Path, old: str, new: str):
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding="utf-8")

    def test_baseline_repository_is_clean(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.assertEqual([], validator.validate_repository(root))

    def test_rejects_unresolvable_plugin_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(root / ".claude-plugin/marketplace.json", '"source": "./"', '"source": "./nope"')
            self.assert_finding(root, "source does not resolve")

    def test_rejects_version_disagreement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(
                root / ".claude-plugin/marketplace.json",
                '"source": "./"',
                '"source": "./", "version": "9.9.9"',
            )
            self.assert_finding(root, "disagrees with plugin.json")

    def test_rejects_name_disagreement_at_marketplace_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(
                root / ".claude-plugin/marketplace.json",
                '"name": "mule-skills",\n      "source": "./"',
                '"name": "other-name",\n      "source": "./"',
            )
            self.assert_finding(root, "must match plugin.json")

    def test_rejects_invalid_manifest_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            (root / ".claude-plugin/plugin.json").write_text("{ not json", encoding="utf-8")
            self.assert_finding(root, "invalid JSON")

    def test_rejects_hardcoded_vendored_path_in_a_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            path = root / "skills/mule-ops/SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\nRun `.agents/skills/mule-ops/scripts/x.py`.\n",
                encoding="utf-8",
            )
            self.assert_finding(root, "hardcodes '.agents/skills/'")

    def test_rejects_unknown_sibling_skill_reference(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            path = root / "skills/mule-review/SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\nSee <skills-root>/mule-absent/SKILL.md\n",
                encoding="utf-8",
            )
            self.assert_finding(root, "references unknown sibling skill: mule-absent")

    def test_rejects_mcp_configuration_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(root / "install/hosts/mcp.json", "@sfdxy/mule-lint@1.28.0", "@sfdxy/mule-lint@9.9.9")
            self.assert_finding(root, "disagree; every host must get the same pins")

    def test_rejects_marketplace_named_for_the_publisher(self):
        """The invariant #5 settled, which nothing enforced until now.

        Marketplace names are global per user, so a catalog name shared across
        repositories silently displaces the other repository's marketplace and
        orphans the plugins installed from it.
        """
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(
                root / ".claude-plugin/marketplace.json",
                '"name": "mule-skills",\n  "description"',
                '"name": "sfdxy",\n  "description"',
            )
            self.assert_finding(root, "must match the repository name")

    def test_rejects_entry_missing_discovery_metadata(self):
        """A marketplace browser reads the entry, not plugin.json."""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(root / ".claude-plugin/marketplace.json", '"license": "MIT",', "")
            self.assert_finding(root, "missing non-empty license")

    def test_rejects_entry_drifting_from_plugin_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(
                root / ".claude-plugin/marketplace.json",
                '"repository": "https://github.com/Avinava/mule-skills"',
                '"repository": "https://github.com/Avinava/somewhere-else"',
            )
            self.assert_finding(root, "disagrees with plugin.json")

    def test_rejects_entry_author_owner_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(
                root / ".claude-plugin/marketplace.json",
                '"author": {\n        "name": "Avi",',
                '"author": {\n        "name": "Nobody",',
            )
            self.assert_finding(root, "author must match the marketplace owner")

    def test_rejects_display_name(self):
        """Not in either schema, and ignored by the CLI, which renders `name`."""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(
                root / ".claude-plugin/plugin.json",
                '"name": "mule-skills",',
                '"name": "mule-skills",\n  "displayName": "Mule Skills",',
            )
            self.assert_finding(root, "remove displayName")

    def test_rejects_reintroduced_skills_key(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(
                root / ".claude-plugin/plugin.json",
                '"name": "mule-skills",',
                '"name": "mule-skills",\n  "skills": "./skills/",',
            )
            self.assert_finding(root, 'remove "skills"')

    def test_rejects_documented_pin_that_drifts_from_the_mcp_config(self):
        """A user installing one version while reading instructions for another."""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(root / "README.md", "@sfdxy/mule-lint@1.28.0", "@sfdxy/mule-lint@9.9.9")
            self.assert_finding(root, "disagrees with .mcp.json pin")

    def test_rejects_ecosystem_manifest_pin_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(
                root / "ecosystem.json",
                '"version": "1.28.0"',
                '"version": "9.9.9"',
            )
            self.assert_finding(root, "disagrees with .mcp.json pin")

    def test_rejects_documented_pin_for_a_server_that_is_not_launched(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            path = root / "docs/mcp-servers.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\nAlso `@sfdxy/mule-ghost@1.0.0`.\n",
                encoding="utf-8",
            )
            self.assert_finding(root, "which .mcp.json does not launch")

    def test_rejects_registry_link_version_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(
                root / "README.md",
                "@sfdxy%2Fanypoint-connect/0.12.0",
                "@sfdxy%2Fanypoint-connect/9.9.9",
            )
            self.assert_finding(root, "registry link for @sfdxy/anypoint-connect@9.9.9")

    def test_rejects_documentation_page_missing_from_the_site_nav(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            (root / "docs/orphan.md").write_text("# Orphan\n", encoding="utf-8")
            self.assert_finding(root, "docs/orphan.md: not in the mkdocs.yml nav")

    def test_rejects_nav_entry_without_a_page(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            self.edit(root / "mkdocs.yml", "- FAQ: faq.md", "- FAQ: absent.md")
            self.assert_finding(root, "nav entry does not resolve: absent.md")

    def test_rejects_skill_that_skips_the_anypoint_readiness_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            path = root / "skills/mule-ops/SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace("references/anypoint-readiness.md", "nowhere"),
                encoding="utf-8",
            )
            self.assert_finding(root, "does not route through references/anypoint-readiness.md")

    def test_rejects_readiness_reference_missing_an_access_state(self):
        """Each state maps to a different user action, so a dropped row is a dropped fix."""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_repository(temporary)
            path = root / "skills/mule-ops/references/anypoint-readiness.md"
            lines = [
                line
                for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
                if not line.startswith("| Not authenticated |")
            ]
            path.write_text("".join(lines), encoding="utf-8")
            self.assert_finding(root, "missing access state 'Not authenticated'")


class RepositoryValidationTests(unittest.TestCase):
    def test_api_design_skill_has_contract_and_mutation_boundaries(self):
        skill = (ROOT / "skills/mule-api-design/SKILL.md").read_text(encoding="utf-8")
        anypoint = (ROOT / "skills/mule-api-design/references/anypoint-design.md").read_text(
            encoding="utf-8"
        )
        for required in (
            "Guided design workshop",
            "Contract-only assessment",
            "mule-lint api validate",
            "Project creation, file sync, and publication are three",
            "Never place a client",
        ):
            self.assertIn(required, skill)
        for required in (
            "list_design_center_projects",
            "preview_design_center_sync",
            "preview_exchange_publication",
            "Do not require `list_environments`",
        ):
            self.assertIn(required, anypoint)

    def test_installer_discovers_new_skills_from_the_source_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            target.mkdir()
            result = subprocess.run(
                [
                    "bash",
                    str(INSTALLER),
                    "--target",
                    str(target),
                    "--hosts",
                    "none",
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("would install mule-testing", result.stdout)

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
