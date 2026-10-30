# Contributing

When adding or changing a reusable skill:

1. Keep the workflow focused and give its `SKILL.md` a precise trigger description.
2. Put project-specific identity, topology, and operating facts in the consuming repository, never
   in this reusable repository.
3. Use neutral examples and mechanism-based guidance; do not retain prior-project fingerprints or
   numeric tuning values.
4. Add `agents/openai.yaml` and only the references, scripts, or assets the skill needs.
5. Refer to bundled scripts through `<skill-root>` or `<skills-root>`, never a host-specific path.
6. Validate the skill, test it with neutral representative tasks, and inspect outputs for unsupported
   claims or sensitive data.
7. Update the README, `docs/`, and `install/install.sh` when discovery, installation, routing, or
   required resources change.

Run before opening a pull request:

```bash
python3 -m unittest discover -s tests -v
python3 tools/generate_ecosystem.py --check
python3 tools/validate_repository.py .
python3 tools/compatibility_smoke.py --require-report-v1
python3 skills/mule-docs/scripts/audit_documentation.py .
claude plugin validate . --strict
claude plugin validate .claude-plugin/plugin.json --strict
shellcheck install/install.sh
uv run --with-requirements requirements-docs.txt mkdocs build --strict
```

The validator enforces the invariants that documentation alone cannot: MCP pins agree everywhere,
every page under `docs/` is reachable from the site navigation, and the skills that need authorized
runtime evidence route through the shared readiness reference.

The executable smoke uses the exact published host pins with an isolated home and synthetic lint
fixtures; it never calls authenticated platform tools. For built local repositories use
`--source-root <source-root> --require-report-v1`. See [compatibility policy](docs/ecosystem.md) for
legacy coverage limits, artifact identity handoff, and tool ownership.

CI runs the same checks. See [CHANGELOG.md](CHANGELOG.md) for release history, including the skill
rename table.


## Repository layout

```text
mule-skills/
├── .claude-plugin/                 # Plugin and marketplace manifests
├── .mcp.json                       # Pinned MCP servers shipped with the plugin
├── skills/                         # The ten reusable skills, host-neutral
│   ├── mule-api-design/            # HTTP design, RAML/OAS contracts, and safe Design Center workflow
│   ├── mule-docs/                  # Documentation workflow, references, and audit tools
│   ├── mule-development/           # Implementation workflow and post-change checklist
│   ├── mule-testing/               # Behavior-focused MUnit authoring and repair
│   ├── mule-troubleshooting/       # Root-cause analysis workflow
│   ├── mule-ops/                   # Runtime health workflow
│   ├── mule-review/                # Change, project, and release-readiness review
│   ├── mule-dependencies/          # Live connector, plugin, and runtime version lookup
│   ├── mule-connectors/            # Connector profiles: auth, identity, sources, signatures
│   └── mule-build/                 # Validate, package, run, version, and tag locally
├── install/
│   ├── install.sh                  # Vendored install for non-plugin hosts
│   ├── hosts/                      # Codex, VS Code, and generic JSON MCP configurations
│   └── templates/                  # Project-owned AGENTS, Claude, Copilot, and Gemini guidance
├── tools/                          # Dependency-free repository validation
├── tests/                          # Validator and checker tests
├── docs/                           # Documentation site source, published with GitHub Pages
├── mkdocs.yml                      # Site configuration and navigation
├── requirements-docs.txt           # Site build dependency, pinned
├── README.md
└── SETUP.md                        # Redirect to docs/
```

Each skill has a required `SKILL.md` and may include:

- `agents/openai.yaml` for interface metadata;
- `references/` for guidance loaded on demand by the workflow, one level deep from `SKILL.md`;
- `scripts/` for deterministic, repeatable inspection and validation;
- `assets/` for data files and templates the scripts or workflow consume.

No other folders are allowed inside a skill. `SKILL.md` stays at or under 500 lines, and any
reference over 100 lines starts with a table of contents. Each `SKILL.md` link to a reference says
when to read it. Scripts are Python standard library only, never prompt for input, support `--help`,
print results as JSON on stdout and diagnostics on stderr, and use exit code 0 for success, 1 for
reported findings, 2 for usage errors or invalid input, and 3 for network or access failure where
applicable.

Skills refer to bundled scripts through `<skill-root>` and `<skills-root>` placeholders rather than a
fixed path, so the same file works under a plugin install and a vendored install.
