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

## Step 5: Copy and Customize Templates

Copy templates into the project root:

```bash
cp /tmp/mule-skills/templates/post-development-checklist.md .agents/skills/mule-development/resources/post-development-checklist.md
```

> The post-development checklist goes into the mule-development skill's resources folder so it's referenced by the skill.

---

## Step 6: Configure the Mule Ops Skill

Open `.agents/skills/mule-ops/SKILL.md` and replace the placeholder values at the top of the file:

1. Ask the user: **"What is the name of your Process API (PAPI) application as deployed in CloudHub?"**
   - Replace all instances of `<YOUR_PAPI_APP>` with the answer
2. Ask the user: **"What is the name of your System API (SAPI) application as deployed in CloudHub?"**
   - Replace all instances of `<YOUR_SAPI_APP>` with the answer
3. Ask the user: **"What environment should be the default for log analysis?"** (default: `Production`)

If the project doesn't have a PAPI/SAPI architecture, skip this step or adapt the skill to the project's architecture.

---

## Step 7: Generate AGENTS.md

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

## Step 8: Generate GEMINI.md and CLAUDE.md

Read the templates at `/tmp/mule-skills/templates/GEMINI.md` and `/tmp/mule-skills/templates/CLAUDE.md`.

Generate both files in the project root, filling in:
- Project name from Step 7
- Build instructions (reference the `/build` workflow)
- Salesforce org alias — ask the user: **"What is your Salesforce org alias?"** (if applicable)
- Any project-specific agent directives the user wants to add

---

## Step 9: Update .gitignore

Ensure the project's `.gitignore` does NOT ignore the `.agents/` directory. If it contains `.*` patterns, add an exception:

```gitignore
!.agents/
```

---

## Step 10: Cleanup

```bash
rm -rf /tmp/mule-skills
```

---

## Step 11: Commit

```bash
git add .agents/ AGENTS.md GEMINI.md CLAUDE.md
git commit -m "feat: add AI agent skills and project configuration

- Added mule-development skill (best practices, patterns, gotchas)
- Added mule-troubleshooting skill (RCA methodology)
- Added mule-ops skill (production log analysis)
- Added build workflow
- Generated project-specific AGENTS.md, GEMINI.md, CLAUDE.md
- Added post-development checklist"
```

---

## Step 12: Report

After setup is complete, report to the user:

1. ✅ Skills installed: `mule-development`, `mule-troubleshooting`, `mule-ops`
2. ✅ Workflow installed: `build`
3. ✅ Project files generated: `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`
4. ✅ Post-development checklist: `.agents/skills/mule-development/resources/post-development-checklist.md`
5. 📋 Remind the user to review and customize:
   - `AGENTS.md` — add specific flow details, configuration, and architecture patterns
   - Post-development checklist — add project-specific gotchas as they're discovered
   - `mule-ops/SKILL.md` — verify app names and scheduler patterns match their project

---

## Updating Skills

To update skills from the upstream repo:

```bash
git clone https://github.com/Avinava/mule-skills.git /tmp/mule-skills
cp -r /tmp/mule-skills/skills/mule-development .agents/skills/
cp -r /tmp/mule-skills/skills/mule-troubleshooting .agents/skills/
# Don't overwrite mule-ops — it has project-specific config
# Don't overwrite templates — they have project-specific content
rm -rf /tmp/mule-skills
```

> **`mule-development`** and **`mule-troubleshooting`** are safe to overwrite — they're universal. **`mule-ops`** has project-specific app names — merge manually.
