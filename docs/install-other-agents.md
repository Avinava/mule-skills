# Install for Codex, Copilot, Gemini, and other agents

Hosts without a plugin system read skills from the repository. `install/install.sh` vendors the six
skills into `.agents/skills/`, merges MCP configuration for the hosts you use, and adds instruction
files — without overwriting anything you already have.

## Install

From the root of the Mule project you want to configure:

```bash
curl -fsSL https://raw.githubusercontent.com/Avinava/mule-skills/main/install/install.sh | bash
```

Or, from a clone of this repository:

```bash
./install/install.sh --target /path/to/your-mule-project
```

By default the script detects which hosts you use and configures only those. Claude Code is
deliberately excluded from detection — [install the plugin](install-claude-code.md) instead of
vendoring a second copy. Pass `--hosts claude` if you want the vendored copy anyway.

Always preview first:

```bash
./install/install.sh --target /path/to/project --dry-run
```

## Options

| Option | Effect |
| --- | --- |
| `--target DIR` | Project to install into (default: current directory) |
| `--hosts LIST` | `claude`, `codex`, `copilot`, `vscode`, `gemini`, or `auto` (default), `all`, `none` |
| `--dry-run` | Print every change and exit without writing |
| `--no-mcp` | Install skills and instruction files but no MCP configuration |
| `--force` | Overwrite existing instruction files (never `AGENTS.md`) |
| `--ref REF` | Git ref to fetch when the script bootstraps itself |

The script is idempotent. Skills are replaced on every run; MCP entries, instruction files, and
`AGENTS.md` are only ever added when missing.

## What it writes

```text
your-mule-project/
├── .agents/skills/                  # the six mule-* skills
├── .mcp.json                        # Claude Code, Copilot CLI, Gemini
├── .vscode/mcp.json                 # VS Code and Copilot Chat
├── .codex/config.toml               # Codex
├── .github/copilot-instructions.md  # GitHub Copilot
├── AGENTS.md                        # shared project context
├── CLAUDE.md                        # only when the claude host is selected
└── GEMINI.md                        # only when the gemini host is selected
```

Existing MCP servers in those files are preserved — the script adds only the entries that are
missing. If a config file is not plain JSON (VS Code allows comments and trailing commas, which the
merger cannot read), the script skips that file, prints the server names to add by hand, and
continues with the rest of the install rather than guessing or aborting halfway.

`AGENTS.md` is never overwritten, including with `--force`. It holds project context you wrote and
cannot be regenerated from a template.

## Host reference

| Host | Instructions read | MCP configuration | Verify with |
| --- | --- | --- | --- |
| Codex CLI, desktop, IDE extension | `AGENTS.md` | `.codex/config.toml` | `codex mcp list` |
| GitHub Copilot in VS Code | `.github/copilot-instructions.md`, `AGENTS.md` | `.vscode/mcp.json` | Reload VS Code, check its MCP server list |
| GitHub Copilot CLI | `.github/copilot-instructions.md`, `AGENTS.md` | `.mcp.json` | `copilot mcp list` |
| Gemini coding agents | `GEMINI.md`, `AGENTS.md` | `.mcp.json` where supported | The host's MCP status view |
| Other compatible agents | `AGENTS.md` plus whatever the host supports | `.mcp.json` when the host accepts `mcpServers` | The host's documented MCP check |

Codex discovers repository skills from `.agents/skills/` in directories between the working
directory and the repository root — see the
[Codex skills documentation](https://developers.openai.com/codex/skills/) and
[Codex MCP documentation](https://developers.openai.com/codex/mcp/).

Local MCP files do not configure GitHub-hosted Copilot agents or code review; configure hosted MCP
access through repository settings.

## Manual install

If you cannot run the script, clone this repository and copy the six directories under `skills/`
into `.agents/skills/`, then merge the matching file from `install/hosts/` into your host's MCP
config and copy the instruction templates from `install/templates/`.

The templates carry two placeholders the script normally fills in. Replace them by hand:

| Placeholder | Replace with |
| --- | --- |
| `<!-- SKILLS_LOCATION -->` | A line stating that the skills live under `.agents/skills/` |
| `<!-- PROJECT_NAME -->` | Your project's name |

The agent-followable version of this procedure is in [agent-install.md](agent-install.md).

## Next

Fill in `AGENTS.md` from this project's actual evidence — see [project-setup.md](project-setup.md).

For runtime logs, metrics, or deployment evidence, authenticate the one server that needs it:
[Anypoint access](anypoint-access.md). Skills that use runtime evidence check for access themselves
and offer alternatives, so this is optional.
