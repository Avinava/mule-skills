from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/mule-dependencies/scripts/mule_versions.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


mv = load_module(SCRIPT, "mule_versions")


def exchange_payload(entries: list[tuple[str, str, list[int] | None, bool]]) -> str:
    versions = []
    for version, minimum, java, snapshot in entries:
        attributes = [{"key": "min-mule-version", "value": minimum}]
        for level in java or []:
            attributes.append({"key": f"is-java-{level}-supported", "value": "true"})
        versions.append(
            {"version": version, "isSnapshot": snapshot, "runtimeVersion": minimum, "attributes": attributes}
        )
    return json.dumps({"versions": versions})


def maven_xml(versions: list[str]) -> str:
    body = "".join(f"<version>{v}</version>" for v in versions)
    return f"<metadata><versioning><versions>{body}</versions></versioning></metadata>"


SAMPLE_EXCHANGE = exchange_payload(
    [
        ("1.9.0", "4.1.1", [8, 11, 17], False),
        ("1.10.0", "4.3.0", [8, 11, 17], False),
        ("2.0.0", "4.6.0", [17], False),
        ("2.1.0-DEV1", "4.9.0", [17], False),
        ("2.1.0-SNAPSHOT", "4.9.0", [17], True),
        ("2.0.1", "4.6.0", [17], False),
    ]
)

JAVA_SUPPORT = """= Java Support
[%header%autowidth.spread]
|===
|Mule Version| Java Version
|4.13 Edge | 17
|4.9 LTS | 17
|4.6 LTS | 8, 11, and 17
|===
"""


class FakeHttp:
    def __init__(self, routes: dict[str, object]) -> None:
        self.routes = routes
        self.calls: list[str] = []

    def __call__(self, url: str) -> str:
        self.calls.append(url)
        for fragment, value in self.routes.items():
            if fragment in url:
                if isinstance(value, Exception):
                    raise value
                return str(value)
        raise mv.NotFound(url)


class IsolatedCacheCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        patcher = mock.patch.dict(os.environ, {"MULE_VERSIONS_CACHE_DIR": str(self.tmp / "cache")})
        patcher.start()
        self.addCleanup(patcher.stop)
        sleeper = mock.patch.object(mv.time, "sleep", lambda _: None)
        sleeper.start()
        self.addCleanup(sleeper.stop)

    def patch_http(self, routes: dict[str, object]) -> FakeHttp:
        fake = FakeHttp(routes)
        patcher = mock.patch.object(mv, "http_get", fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        return fake


class VersionLogicTests(unittest.TestCase):
    def test_numeric_sort_beats_lexical(self):
        self.assertEqual(mv.release_versions(["1.9.0", "1.10.0", "1.2.0"]), ["1.2.0", "1.9.0", "1.10.0"])

    def test_filters_prerelease_builds(self):
        versions = ["1.0.0", "1.1.0-DEV1", "1.1.0-SNAPSHOT", "1.2.0-RC2", "1.2.0-M1", "1.2.0-beta1", "1.2.0"]
        self.assertEqual(mv.release_versions(versions), ["1.0.0", "1.2.0"])

    def test_short_versions_compare_with_padding(self):
        self.assertTrue(mv.version_lte("4.6", "4.6.0"))
        self.assertTrue(mv.version_lte("4.6.0", "4.9"))
        self.assertFalse(mv.version_lte("4.10.0", "4.9.0"))

    def test_alias_resolution_uses_current_coordinates(self):
        self.assertEqual(mv.resolve_connector("kafka"), ("com.mulesoft.connectors", "mule-kafka-connector"))
        self.assertEqual(mv.resolve_connector("a.b:c"), ("a.b", "c"))
        with self.assertRaises(mv.NotFound):
            mv.resolve_connector("unknown")

    def test_java_support_table_parses(self):
        rows = mv.parse_java_support(JAVA_SUPPORT)
        self.assertEqual(rows[0], {"version": "4.13", "channel": "Edge", "java": [17]})
        self.assertEqual(rows[2]["java"], [8, 11, 17])


class ConnectorLookupTests(IsolatedCacheCase):
    def test_latest_ignores_dev_and_snapshot_and_filters_compatibility(self):
        self.patch_http({"exchange/api/v1/assets": SAMPLE_EXCHANGE})
        fetcher = mv.Fetcher()
        result = mv.connector_result(fetcher, "http", "4.6.0", 11, False, {})
        self.assertEqual(result["latest"]["version"], "2.0.1")
        self.assertEqual(result["latestCompatible"]["version"], "1.10.0")
        self.assertEqual(result["source"], "exchange-asset-api")
        self.assertIn("fetchedAt", result)

    def test_no_compatible_release_reports_none(self):
        self.patch_http({"exchange/api/v1/assets": exchange_payload([("3.0.0", "4.9.0", [17], False)])})
        result = mv.connector_result(mv.Fetcher(), "http", "4.6.0", 11, False, {})
        self.assertIsNone(result["latestCompatible"])
        self.assertIn("no release satisfies", result["note"])

    def test_falls_back_to_maven_sources_without_compatibility(self):
        self.patch_http(
            {
                "exchange/api/v1/assets": mv.NetworkFailure("down"),
                "maven.anypoint.mulesoft.com": maven_xml(["1.0.0", "1.10.0", "1.9.0", "1.11.0-DEV1"]),
            }
        )
        fetcher = mv.Fetcher()
        result = mv.connector_result(fetcher, "http", "4.6.0", 11, False, {})
        self.assertEqual(result["source"], "exchange-maven-facade")
        self.assertEqual(result["latest"]["version"], "1.10.0")
        self.assertTrue(any("unknown" in w for w in fetcher.warnings))

    def test_all_sources_missing_raises_not_found(self):
        self.patch_http({})
        with self.assertRaises(mv.NotFound):
            mv.connector_result(mv.Fetcher(), "a.b:c", None, None, False, {})

    def test_all_sources_down_raises_network_failure(self):
        self.patch_http({"": mv.NetworkFailure("down")})
        with self.assertRaises(mv.NetworkFailure):
            mv.connector_result(mv.Fetcher(), "http", None, None, False, {})

    def test_cache_serves_second_call_and_stale_on_failure(self):
        fake = self.patch_http({"exchange/api/v1/assets": SAMPLE_EXCHANGE})
        mv.connector_result(mv.Fetcher(), "http", None, None, False, {})
        mv.connector_result(mv.Fetcher(), "http", None, None, False, {})
        self.assertEqual(len(fake.calls), 1)

        self.patch_http({"": mv.NetworkFailure("down")})
        fetcher = mv.Fetcher()
        with mock.patch.object(mv, "CONNECTOR_TTL", -1):
            result = mv.connector_result(fetcher, "http", None, None, False, {})
        self.assertEqual(result["latest"]["version"], "2.0.1")
        self.assertTrue(any("stale cache" in w for w in fetcher.warnings))

    def test_maven_central_is_never_queried(self):
        fake = self.patch_http({"exchange/api/v1/assets": mv.NetworkFailure("down"), "": mv.NetworkFailure("down")})
        with self.assertRaises(mv.NetworkFailure):
            mv.connector_result(mv.Fetcher(), "http", None, None, False, {})
        self.assertFalse(any("maven.org" in url for url in fake.calls))


class PluginAndRuntimeTests(IsolatedCacheCase):
    def test_plugin_uses_releases_repo_and_filters_prereleases(self):
        self.patch_http({"repository.mulesoft.org": maven_xml(["3.7.4", "3.7.5", "3.8.0-DEV1"])})
        result = mv.plugin_result(mv.Fetcher(), "munit-runner", False, {})
        self.assertEqual(result["latest"], "3.7.5")
        self.assertEqual(result["source"], "mulesoft-releases")

    def test_runtime_support_parses_table(self):
        self.patch_http({"java-support.adoc": JAVA_SUPPORT})
        data = mv.runtime_support(mv.Fetcher())
        self.assertEqual([r["version"] for r in data["runtimes"]], ["4.13", "4.9", "4.6"])

    def test_runtime_unparseable_table_is_an_error(self):
        self.patch_http({"java-support.adoc": "nothing useful"})
        with self.assertRaises(ValueError):
            mv.runtime_support(mv.Fetcher())


class CheckTests(IsolatedCacheCase):
    POM = """<project xmlns="http://maven.apache.org/POM/4.0.0">
  <properties><http.version>1.9.0</http.version><java.version>11</java.version></properties>
  <dependencies>
    <dependency><groupId>org.mule.connectors</groupId><artifactId>mule-http-connector</artifactId>
      <version>${http.version}</version><classifier>mule-plugin</classifier></dependency>
    <dependency><groupId>org.mule.connectors</groupId><artifactId>mule-sftp-connector</artifactId>
      <version>1.10.0</version><classifier>mule-plugin</classifier></dependency>
    <dependency><groupId>junit</groupId><artifactId>junit</artifactId><version>4.13</version></dependency>
  </dependencies>
</project>
"""

    def test_flags_outdated_current_and_ignores_non_plugins(self):
        project = self.tmp / "project"
        project.mkdir()
        (project / "pom.xml").write_text(self.POM, encoding="utf-8")
        (project / "mule-artifact.json").write_text('{"minMuleVersion":"4.6.0"}', encoding="utf-8")

        self.patch_http({"mule-http-connector": SAMPLE_EXCHANGE, "mule-sftp-connector": SAMPLE_EXCHANGE})
        report = mv.check_pom(mv.Fetcher(), project / "pom.xml", None, None)
        self.assertEqual(report["constraints"], {"mule": "4.6.0", "java": 11})
        by_artifact = {row["artifactId"]: row for row in report["dependencies"]}
        self.assertEqual(set(by_artifact), {"mule-http-connector", "mule-sftp-connector"})
        self.assertEqual(by_artifact["mule-http-connector"]["status"], "outdated")
        self.assertEqual(by_artifact["mule-http-connector"]["latestCompatible"], "1.10.0")
        self.assertEqual(by_artifact["mule-sftp-connector"]["status"], "current")


RELEASE_NOTES_PAGE = """
<h1>Sample Connector Release Notes</h1>
<div class="sect1"><h2 id="3-0-0"><a class="anchor" href="#3-0-0"></a>3.0.0</h2>
<div class="sectionbody"><p><strong>July 1, 2026</strong></p>
<h3 id="whats-new">What&#8217;s New</h3>
<ul><li><p>The <strong>Basic</strong> connection type is removed.</p></li></ul>
<table><tr><td>Mule</td><td>4.9.0 and later</td></tr><tr><td>OpenJDK</td><td>17</td></tr></table>
</div></div>
<div class="sect1"><h2 id="2-1-0"><a class="anchor" href="#2-1-0"></a>2.1.0</h2>
<div class="sectionbody"><p><strong>March 3, 2025</strong></p>
<p>Adds the <strong>OAuth Client Credentials</strong> connection type.</p>
<table><tr><td>Mule</td><td>4.6.6 and later</td></tr><tr><td>OpenJDK</td><td>8, 11, and 17</td></tr></table>
</div></div>
<div class="sect1"><h2 id="2-0-0"><a class="anchor" href="#2-0-0"></a>2.0.0</h2>
<div class="sectionbody"><p><strong>January 9, 2025</strong></p><p>Initial release.</p></div></div>
<div class="sect1"><h2 id="see-also"><a class="anchor" href="#see-also"></a>See Also</h2>
<p>Mentions client credentials outside any version.</p></div>
"""


class ReleaseNotesTests(IsolatedCacheCase):
    def test_parses_versions_dates_and_compatibility(self):
        sections = mv.parse_release_notes(RELEASE_NOTES_PAGE)
        self.assertEqual([s["version"] for s in sections], ["3.0.0", "2.1.0", "2.0.0"])
        self.assertEqual(sections[0]["date"], "July 1, 2026")
        self.assertEqual(sections[0]["minMuleVersion"], "4.9.0")
        self.assertEqual(sections[0]["java"], [17])
        self.assertEqual(sections[1]["java"], [8, 11, 17])
        self.assertIsNone(sections[2]["minMuleVersion"])
        self.assertNotIn("outside any version", sections[2]["text"])

    def test_grep_reports_earliest_match_and_page_coverage(self):
        self.patch_http({"release-notes/connector/salesforce": RELEASE_NOTES_PAGE})
        result = mv.notes_result(mv.Fetcher(), "salesforce", "client credentials", None)
        self.assertEqual(result["earliestMatch"], "2.1.0")
        self.assertEqual(result["coverage"], {"oldest": "2.0.0", "newest": "3.0.0"})
        match = result["matches"][0]
        self.assertTrue(match["url"].endswith("#2-1-0"))
        self.assertIn("Client Credentials", match["snippets"][0])
        self.assertIn("lower bound", result["note"])

    def test_without_grep_lists_versions_newest_first(self):
        self.patch_http({"release-notes/connector/salesforce": RELEASE_NOTES_PAGE})
        result = mv.notes_result(mv.Fetcher(), "salesforce", None, None)
        self.assertEqual([v["version"] for v in result["versions"]], ["3.0.0", "2.1.0", "2.0.0"])
        self.assertNotIn("text", result["versions"][0])

    def test_unknown_alias_and_unparseable_page(self):
        with self.assertRaises(mv.NotFound):
            mv.notes_result(mv.Fetcher(), "no-such-connector", None, None)
        self.patch_http({"release-notes": "<html>moved</html>"})
        with self.assertRaises(ValueError):
            mv.notes_result(mv.Fetcher(), "salesforce", None, None)

    def test_every_connector_alias_has_a_notes_page(self):
        self.assertEqual(set(mv.RELEASE_NOTES), set(mv.CONNECTORS))


class OfflineAndCliTests(IsolatedCacheCase):
    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = mv.main(list(argv))
            except SystemExit as exit_:
                code = int(exit_.code or 0)
        return code, out.getvalue(), err.getvalue()

    def snapshot_file(self) -> Path:
        path = self.tmp / "snapshot.json"
        path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-01-01",
                    "connectors": {"http": {"groupId": "org.mule.connectors", "artifactId": "mule-http-connector",
                                            "latest": "9.9.9", "minMuleVersion": "4.1.1", "java": [17]}},
                    "plugins": {"munit-runner": {"latest": "1.2.3"}},
                    "runtimes": [{"version": "4.13", "channel": "Edge", "java": [17]}],
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_offline_never_touches_network_and_labels_unverified(self):
        fake = self.patch_http({"": AssertionError("network used")})
        path = self.snapshot_file()
        code, out, _ = self.run_cli("--offline", "--snapshot-path", str(path), "connector", "http")
        self.assertEqual(code, mv.EXIT_OK)
        payload = json.loads(out)
        self.assertFalse(payload["result"]["verified"])
        self.assertEqual(payload["result"]["asOf"], "2026-01-01")
        self.assertEqual(fake.calls, [])

    def test_exit_codes(self):
        path = self.snapshot_file()
        code, _, _ = self.run_cli("--offline", "--snapshot-path", str(path), "connector", "kafka")
        self.assertEqual(code, mv.EXIT_NOT_FOUND)
        self.patch_http({"": mv.NetworkFailure("down")})
        code, _, _ = self.run_cli("connector", "http")
        self.assertEqual(code, mv.EXIT_NETWORK)
        code, _, _ = self.run_cli()
        self.assertEqual(code, mv.EXIT_USAGE)

    def test_notes_cli_exit_codes(self):
        fake = self.patch_http({"release-notes": RELEASE_NOTES_PAGE})
        code, out, _ = self.run_cli("notes", "salesforce", "--grep", "client credentials")
        self.assertEqual(code, mv.EXIT_OK)
        self.assertEqual(json.loads(out)["result"]["earliestMatch"], "2.1.0")
        code, _, _ = self.run_cli("notes", "salesforce", "--grep", "not mentioned anywhere")
        self.assertEqual(code, mv.EXIT_NOT_FOUND)
        code, _, _ = self.run_cli("notes", "custom", "--url", "https://example.invalid/notes")
        self.assertEqual(code, mv.EXIT_NOT_FOUND)
        calls = len(fake.calls)
        code, _, _ = self.run_cli("--offline", "notes", "salesforce")
        self.assertEqual(code, mv.EXIT_NETWORK)
        self.assertEqual(len(fake.calls), calls)

    def test_json_on_stdout_and_diagnostics_on_stderr(self):
        self.patch_http({"exchange/api/v1/assets": SAMPLE_EXCHANGE})
        code, out, err = self.run_cli("connector", "http", "--mule", "4.6.0", "--java", "17")
        self.assertEqual(code, mv.EXIT_OK)
        self.assertEqual(json.loads(out)["result"]["latestCompatible"]["version"], "2.0.1")
        self.assertEqual(err, "")

    def test_refresh_snapshot_writes_file(self):
        self.patch_http(
            {
                "exchange/api/v1/assets": SAMPLE_EXCHANGE,
                "repository.mulesoft.org": maven_xml(["1.0.0"]),
                "java-support.adoc": JAVA_SUPPORT,
            }
        )
        target = self.tmp / "out" / "snapshot.json"
        code, _, _ = self.run_cli("--refresh-snapshot", "--snapshot-path", str(target))
        self.assertEqual(code, mv.EXIT_OK)
        written = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(written["connectors"]["http"]["latest"], "2.0.1")
        self.assertEqual(written["plugins"]["munit-runner"]["latest"], "1.0.0")

    def test_bundled_snapshot_is_well_formed(self):
        snapshot = mv.load_snapshot()
        self.assertTrue(snapshot.get("generatedAt"))
        self.assertIn("salesforce", snapshot["connectors"])
        self.assertTrue(snapshot["runtimes"])


if __name__ == "__main__":
    unittest.main()
