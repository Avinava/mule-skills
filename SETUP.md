# MuleSoft Skills — Agent Setup Instructions

> **This file is an instruction set for AI coding agents.** When a user pastes the URL to this file, the agent should read and execute these steps to configure a MuleSoft project with reusable development skills.

---

## Prerequisites

Before starting, verify:
1. The current working directory contains a `pom.xml` (it's a Maven/Mule project)
2. The `pom.xml` contains `mule-maven-plugin` or `mule-application` packaging (it's a Mule 4 project)
3. `git` is available on the system

If any prerequisite fails, inform the user and stop.

---

## Step 1: Clone the Skills Repository

```bash
git clone https://github.com/Avinava/mule-skills.git /tmp/mule-skills
```

If the clone fails (private repo, no access), ask the user to provide access or download the repo manually.

---

## Step 2: Create the Agent Directory Structure

Create the `.agents/` directory in the project root if it doesn't exist:

```bash
mkdir -p .agents/skills
mkdir -p .agents/workflows
```

> **Note:** Some tooling uses `.agent/` (singular). Use `.agents/` (plural) as the standard. If the project already has `.agent/`, rename it to `.agents/` and update any references.

---

## Step 3: Copy Universal Skills

Copy these skill directories from the cloned repo into the project:

```bash
cp -r /tmp/mule-skills/skills/document-mulesoft-project .agents/skills/
cp -r /tmp/mule-skills/skills/mule-development .agents/skills/
cp -r /tmp/mule-skills/skills/mule-troubleshooting .agents/skills/
cp -r /tmp/mule-skills/skills/mule-ops .agents/skills/
```

---

## Step 4: Copy Workflows

```bash
cp -r /tmp/mule-skills/workflows/build.md .agents/workflows/
```

---

## Step 5: Configure MCP Servers

The MuleSoft MCP servers give AI agents direct access to your Anypoint Platform (logs, metrics, deployments), build tooling, and static analysis. This step configures them for your IDE.

### 5a. Determine the IDE

Ask the user: **"Which IDE/agent are you using?"**

| IDE / Agent | Config file | Config format |
|-------------|-------------|---------------|
| **VS Code + Gemini Code Assist** | `.vscode/mcp.json` | `{ "servers": { ... } }` |
| **VS Code + GitHub Copilot** | `.vscode/mcp.json` | `{ "servers": { ... } }` |
| **Claude Desktop** | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) | `{ "mcpServers": { ... } }` |
| **Cursor** | Project root `mcp.json` or `.cursor/mcp.json` | `{ "mcpServers": { ... } }` |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` | `{ "mcpServers": { ... } }` |

### 5b. Copy the Appropriate Config

**For VS Code (Gemini Code Assist / GitHub Copilot):**

```bash
mkdir -p .vscode
cp /tmp/mule-skills/mcp/.vscode/mcp.json .vscode/mcp.json
```

This creates `.vscode/mcp.json` with:
```json
{
  "servers": {
    "anypoint-connect": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@sfdxy/anypoint-connect", "mcp"]
    },
    "mule-build": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@sfdxy/mule-build", "mcp"]
    },
    "mule-lint": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@sfdxy/mule-lint", "mcp"]
    }
  }
}
```

**For Claude Desktop / Cursor / Windsurf:**

Copy the root `mcp.json` from the mule-skills repo:
```bash
cp /tmp/mule-skills/mcp/mcp.json ./mcp.json
```

This creates `mcp.json` with:
```json
{
  "mcpServers": {
    "anypoint-connect": {
      "command": "npx",
      "args": ["-y", "@sfdxy/anypoint-connect", "mcp"]
    },
    "mule-build": {
      "command": "npx",
      "args": ["-y", "@sfdxy/mule-build", "mcp"]
    },
    "mule-lint": {
      "command": "npx",
      "args": ["-y", "@sfdxy/mule-lint", "mcp"]
    }
  }
}
```

> For **Claude Desktop**, merge the `mcpServers` block into the existing `claude_desktop_config.json` rather than creating a project-level file.

### 5c. Configure Anypoint Connect Authentication

The `anypoint-connect` MCP server requires a one-time OAuth2 setup with Anypoint Platform:

1. Ask the user: **"Have you already run `anc config init` and `anc auth login`?"**
2. If **no**, instruct them to:
   ```bash
   # Install the CLI
   npm install -g @sfdxy/anypoint-connect

   # Initialize config (creates OAuth2 profile)
   anc config init

   # Authenticate via browser
   anc auth login

   # Verify
   anc auth status
   ```
3. Bind the project to the correct profile:
   ```bash
   anc config use <PROFILE_NAME>
   ```
   This creates `.anypoint-connect.json` in the project root, which the MCP server auto-detects.

> **Multi-org support:** If the user manages multiple Anypoint orgs, they can create named profiles (`anc config init --profile client-a`) and bind each project to a different profile.

### 5d. MCP Server Summary

| Server | npm Package | Purpose |
|--------|-------------|---------|
| **anypoint-connect** | `@sfdxy/anypoint-connect` | Anypoint Platform operations — logs, metrics, deployments, API management, Exchange, Design Center, Anypoint MQ, Object Store |
| **mule-build** | `@sfdxy/mule-build` | Local build, run, and release — Maven packaging, version bumps, security scanning, local Mule runtime |
| **mule-lint** | `@sfdxy/mule-lint` | Static analysis — 56 rules covering error handling, security, naming, logging, performance. HTML/SARIF/CSV reports |

---

## Step 6: Verify Bundled Resources

The `mule-development` skill includes `resources/post-development-checklist.md` which was copied in Step 3. Verify it exists:

```bash
ls .agents/skills/mule-development/resources/post-development-checklist.md
ls .agents/skills/document-mulesoft-project/references/privacy-and-evidence.md
python3 .agents/skills/document-mulesoft-project/scripts/inventory_mule_project.py . --pretty
```

> This checklist is a starting point. Add your own project-specific gotchas to the "Project-Specific Gotchas" section at the bottom as you discover them.

The inventory command is read-only and returns a repository-relative JSON index. It must identify the
current directory as a Mule project before the documentation skill is used. Do not commit inventory
output unless the project explicitly wants it as a maintained artifact.

---

## Step 7: Configure the Mule Ops Skill

Open `.agents/skills/mule-ops/SKILL.md` and replace the placeholder values at the top of the file:

1. Ask the user: **"What is the name of your Process API (PAPI) application as deployed in CloudHub?"**
   - Replace all instances of `<YOUR_PAPI_APP>` with the answer
2. Ask the user: **"What is the name of your System API (SAPI) application as deployed in CloudHub?"**
   - Replace all instances of `<YOUR_SAPI_APP>` with the answer
3. Ask the user: **"What environment should be the default for log analysis?"** (default: `Production`)

If the project doesn't have a PAPI/SAPI architecture, skip this step or adapt the skill to the project's architecture.

---

## Step 8: Generate AGENTS.md

Read the template at `/tmp/mule-skills/templates/AGENTS.md` and generate a project-specific version.

Ask the user the following questions to fill in the template:

1. **What does this project do?** (one paragraph description)
2. **What systems does it integrate?** (e.g., Salesforce, NetSuite, Ramp, SAP, Workday)
3. **Is this a Process API (PAPI), System API (SAPI), or Experience API (XAPI)?**
4. **What is the companion API name?** (if PAPI, what SAPI does it call? If SAPI, what PAPI calls it?)
5. **What environments exist?** (e.g., Development, Sandbox, Production)
6. **How is it deployed?** (CloudHub 1.0, CloudHub 2.0, Runtime Fabric, On-Prem)

Generate `AGENTS.md` in the project root with the user's answers filling the template placeholders.

---

## Step 9: Generate GEMINI.md and CLAUDE.md

Read the templates at `/tmp/mule-skills/templates/GEMINI.md` and `/tmp/mule-skills/templates/CLAUDE.md`.

Generate both files in the project root, filling in:
- Project name from Step 8
- Build instructions (reference the `/build` workflow)
- Salesforce org alias — ask the user: **"What is your Salesforce org alias?"** (if applicable)
- Any project-specific agent directives the user wants to add

---

## Step 10: Update .gitignore

Ensure the project's `.gitignore` does NOT ignore the `.agents/` or `.vscode/` directories. If it contains `.*` patterns, add exceptions:

```gitignore
!.agents/
!.vscode/
```

---

## Step 11: Cleanup

```bash
rm -rf /tmp/mule-skills
```

---

## Step 12: Commit

```bash
git add .agents/ .vscode/ AGENTS.md GEMINI.md CLAUDE.md
git commit -m "feat: add AI agent skills, MCP servers, and project configuration

- Added mule-development skill (best practices, patterns, gotchas)
- Added mule-troubleshooting skill (RCA methodology)
- Added mule-ops skill (production log analysis)
- Added document-mulesoft-project skill (evidence-backed documentation and Mermaid diagrams)
- Added build workflow
- Configured MCP servers (anypoint-connect, mule-build, mule-lint)
- Generated project-specific AGENTS.md, GEMINI.md, CLAUDE.md
- Added post-development checklist"
```

---

## Step 13: Report

After setup is complete, report to the user:

1. ✅ Skills installed: `document-mulesoft-project`, `mule-development`, `mule-troubleshooting`, `mule-ops`
2. ✅ Workflow installed: `build`
3. ✅ MCP servers configured: `anypoint-connect`, `mule-build`, `mule-lint`
4. ✅ Project files generated: `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`
5. ✅ Post-development checklist: `.agents/skills/mule-development/resources/post-development-checklist.md`
6. 📋 Remind the user to review and customize:
   - `AGENTS.md` — add specific flow details, configuration, and architecture patterns
   - Post-development checklist — add project-specific gotchas as they're discovered
   - `mule-ops/SKILL.md` — verify app names and scheduler patterns match their project
7. 📋 Remind the user to complete auth setup if not done:
   - `anc config init` → `anc auth login` → `anc config use <profile>`

---

## Updating Skills

To update skills from the upstream repo:

```bash
git clone https://github.com/Avinava/mule-skills.git /tmp/mule-skills
cp -r /tmp/mule-skills/skills/document-mulesoft-project .agents/skills/
cp -r /tmp/mule-skills/skills/mule-development .agents/skills/
cp -r /tmp/mule-skills/skills/mule-troubleshooting .agents/skills/
# Don't overwrite mule-ops — it has project-specific config
# Don't overwrite templates — they have project-specific content
rm -rf /tmp/mule-skills
```

> **`document-mulesoft-project`**, **`mule-development`**, and **`mule-troubleshooting`** are safe to overwrite — they're universal. **`mule-ops`** has project-specific app names — merge manually.
