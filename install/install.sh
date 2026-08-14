#!/usr/bin/env bash
#
# Install the mule-skills toolkit into a MuleSoft project.
#
# Claude Code users should prefer the plugin install instead:
#   /plugin marketplace add Avinava/mule-skills
#   /plugin install mule-skills@mule-skills
#
# This script covers every other agent host by vendoring the skills into
# .agents/skills/ and merging host MCP configuration without clobbering it.
#
# Usage:
#   install/install.sh [options]
#   curl -fsSL https://raw.githubusercontent.com/Avinava/mule-skills/main/install/install.sh | bash
#
set -euo pipefail

REPO_URL="${MULE_SKILLS_REPO:-https://github.com/Avinava/mule-skills.git}"
REPO_REF="${MULE_SKILLS_REF:-main}"
SKILL_NAMES="mule-build mule-development mule-docs mule-ops mule-review mule-troubleshooting"
LEGACY_SKILL_NAMES="document-mulesoft-project review-mulesoft-project"

TARGET="$PWD"
HOSTS="auto"
DRY_RUN=0
WITH_MCP=1
FORCE=0
CLONE_DIR=""

usage() {
  cat <<'EOF'
Usage: install.sh [options]

Options:
  --target DIR    Project to install into (default: current directory)
  --hosts LIST    Comma-separated: claude, codex, copilot, vscode, gemini,
                  auto (detect, default), all, none
  --dry-run       Print what would change and exit without writing
  --no-mcp        Install skills and instruction files but no MCP configuration
  --force         Overwrite existing instruction files (never AGENTS.md)
  --ref REF       Git ref to fetch when the script bootstraps itself
  -h, --help      Show this help

Re-running is safe: skills are replaced, everything else is only added when missing.
EOF
}

log()  { printf '%s\n' "$*"; }
info() { printf '  %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }

act() {
  # act <description> <command...>
  local description="$1"; shift
  if [ "$DRY_RUN" -eq 1 ]; then
    info "would $description"
  else
    info "$description"
    "$@"
  fi
}

cleanup() {
  [ -n "$CLONE_DIR" ] && [ -d "$CLONE_DIR" ] && rm -rf "$CLONE_DIR"
  return 0
}
trap cleanup EXIT

while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="${2:?--target needs a directory}"; shift 2 ;;
    --hosts)  HOSTS="${2:?--hosts needs a value}"; shift 2 ;;
    --ref)    REPO_REF="${2:?--ref needs a value}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --no-mcp)  WITH_MCP=0; shift ;;
    --force)   FORCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1 (try --help)" ;;
  esac
done

command -v python3 >/dev/null 2>&1 || die "python3 is required"

# --- Locate the toolkit source, cloning it when run standalone (curl | bash) ---

SRC=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [ -d "$script_dir/../skills" ]; then
    SRC="$(cd "$script_dir/.." && pwd)"
  fi
fi

if [ -z "$SRC" ]; then
  command -v git >/dev/null 2>&1 || die "git is required to fetch mule-skills"
  CLONE_DIR="$(mktemp -d)"
  log "Fetching mule-skills ($REPO_REF)..."
  git clone --depth 1 --branch "$REPO_REF" --quiet "$REPO_URL" "$CLONE_DIR/mule-skills" \
    || die "could not clone $REPO_URL at $REPO_REF"
  SRC="$CLONE_DIR/mule-skills"
fi

[ -d "$SRC/skills" ] || die "no skills/ directory found in $SRC"

VERSION="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["version"])' \
  "$SRC/.claude-plugin/plugin.json" 2>/dev/null || echo "unknown")"

# --- Resolve the target ---

[ -d "$TARGET" ] || die "target directory does not exist: $TARGET"
TARGET="$(cd "$TARGET" && pwd)"
[ "$TARGET" = "$SRC" ] && die "target is the mule-skills repository itself"

# --- Decide which hosts to configure ---

detect_hosts() {
  # 'claude' is deliberately not auto-detected. Claude Code should install the plugin
  # instead of vendoring a second copy of the skills and MCP servers. Pass
  # --hosts claude explicitly to vendor anyway.
  local found=""
  if [ -d "$TARGET/.codex" ] || command -v codex >/dev/null 2>&1; then
    found="$found codex"
  fi
  if [ -d "$TARGET/.vscode" ] || command -v code >/dev/null 2>&1; then
    found="$found vscode"
  fi
  if [ -d "$TARGET/.github" ] || command -v copilot >/dev/null 2>&1; then
    found="$found copilot"
  fi
  if [ -f "$TARGET/GEMINI.md" ] || command -v gemini >/dev/null 2>&1; then
    found="$found gemini"
  fi
  printf '%s' "$found"
}

case "$HOSTS" in
  auto)
    SELECTED="$(detect_hosts)"
    if [ -d "$TARGET/.claude" ] || command -v claude >/dev/null 2>&1; then
      warn "Claude Code detected. Prefer the plugin over this vendored install:"
      warn "  /plugin marketplace add Avinava/mule-skills"
      warn "  /plugin install mule-skills@mule-skills"
      warn "Pass --hosts claude to vendor a copy anyway."
    fi
    ;;
  all)  SELECTED="claude codex vscode copilot gemini" ;;
  none) SELECTED="" ;;
  *)    SELECTED="$(printf '%s' "$HOSTS" | tr ',' ' ')" ;;
esac

for host in $SELECTED; do
  case "$host" in
    claude|codex|vscode|copilot|gemini) ;;
    *) die "unknown host: $host" ;;
  esac
done

has_host() { case " $SELECTED " in *" $1 "*) return 0 ;; *) return 1 ;; esac; }

# --- Helpers ---

merge_json_mcp() {
  # merge_json_mcp <destination> <top-level key> <add "type":"stdio">
  local dest="$1" key="$2" add_type="$3"
  local label="${dest#"$TARGET"/}"
  if [ "$DRY_RUN" -eq 1 ]; then
    info "would merge missing MCP servers into $label"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  python3 - "$dest" "$key" "$add_type" "$SRC/install/hosts/mcp.json" "$label" <<'PY'
import json, os, sys

dest, key, add_type, source, label = sys.argv[1], sys.argv[2], sys.argv[3] == "1", sys.argv[4], sys.argv[5]

servers = json.load(open(source, encoding="utf-8"))["mcpServers"]

config = {}
if os.path.exists(dest):
    with open(dest, encoding="utf-8") as handle:
        text = handle.read().strip()
    if text:
        try:
            config = json.loads(text)
        except json.JSONDecodeError as exc:
            # VS Code accepts JSONC (comments, trailing commas), which json cannot read.
            # Skip this host rather than aborting an install that already placed skills.
            print(f"    SKIPPED {label}: not plain JSON ({exc}). Add these by hand:")
            for name in servers:
                print(f"      {name}")
            raise SystemExit(0)
    if not isinstance(config, dict):
        print(f"    SKIPPED {label}: top level is not an object. Merge by hand.")
        raise SystemExit(0)

existing = config.setdefault(key, {})
if not isinstance(existing, dict):
    print(f"    SKIPPED {label}: '{key}' is not an object. Merge by hand.")
    raise SystemExit(0)
added = []
for name, entry in servers.items():
    if name in existing:
        continue
    entry = dict(entry)
    if add_type:
        entry = {"type": "stdio", **entry}
    existing[name] = entry
    added.append(name)

if added:
    with open(dest, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")
    print(f"    added to {label}: {', '.join(added)}")
else:
    print(f"    {label} already has every server")
PY
}

merge_codex_toml() {
  local dest="$TARGET/.codex/config.toml"
  if [ "$DRY_RUN" -eq 1 ]; then
    info "would merge missing MCP servers into .codex/config.toml"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  python3 - "$dest" "$SRC/install/hosts/codex/config.toml" <<'PY'
import os, re, sys

dest, source = sys.argv[1], sys.argv[2]
source_text = open(source, encoding="utf-8").read()

existing_text = open(dest, encoding="utf-8").read() if os.path.exists(dest) else ""

# Codex accepts [mcp_servers.name], [mcp_servers."name"], and an inline
# mcp_servers = { ... } table. Miss any of them and we append a duplicate table,
# which makes Codex fail to parse its own config.
present = set(
    re.findall(r'^\s*\[\s*mcp_servers\s*\.\s*"?([A-Za-z0-9_-]+)"?\s*\]', existing_text, re.MULTILINE)
)
inline = re.search(r"^\s*mcp_servers\s*=\s*\{(.*)$", existing_text, re.MULTILINE)
if inline:
    present.update(re.findall(r'"?([A-Za-z0-9_-]+)"?\s*=\s*\{', inline.group(1)))

# Split the source into one block per [mcp_servers.<name>] table.
blocks, current, name = {}, [], None
for line in source_text.splitlines():
    match = re.match(r"^\s*\[mcp_servers\.([A-Za-z0-9_-]+)\]", line)
    if match:
        if name:
            blocks[name] = "\n".join(current).strip()
        name, current = match.group(1), [line]
    elif name:
        current.append(line)
if name:
    blocks[name] = "\n".join(current).strip()

added = [n for n in blocks if n not in present]
if not added:
    print("    .codex/config.toml already has every server")
    raise SystemExit(0)

parts = [existing_text.rstrip("\n")] if existing_text.strip() else []
parts.extend(blocks[n] for n in added)
with open(dest, "w", encoding="utf-8") as handle:
    handle.write("\n\n".join(parts) + "\n")
print(f"    added to .codex/config.toml: {', '.join(added)}")
PY
}

install_template() {
  # install_template <template file> <destination> <skills location line> [protected]
  # A protected destination is never overwritten, not even with --force: AGENTS.md holds
  # project context the user wrote and cannot be regenerated from a template.
  local template="$1" dest="$2" location="$3" protected="${4:-0}"
  local label="${dest#"$TARGET"/}"
  if [ -e "$dest" ] && { [ "$FORCE" -eq 0 ] || [ "$protected" -eq 1 ]; }; then
    if [ -e "$dest" ] && [ "$FORCE" -eq 1 ] && [ "$protected" -eq 1 ]; then
      info "kept existing $label (--force never overwrites it)"
    else
      info "kept existing $label"
    fi
    return 0
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    info "would write $label"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  python3 - "$SRC/install/templates/$template" "$dest" "$(basename "$TARGET")" "$location" <<'PY'
import sys
source, dest, project, location = sys.argv[1:5]
text = open(source, encoding="utf-8").read()
text = text.replace("<!-- SKILLS_LOCATION -->", location)
text = text.replace("<!-- PROJECT_NAME -->", project)
open(dest, "w", encoding="utf-8").write(text)
PY
  info "wrote $label"
}

# --- Report the plan ---

log ""
log "mule-skills $VERSION"
log "  source: $SRC"
log "  target: $TARGET"
log "  hosts:  ${SELECTED:-none (skills only)}"
[ "$DRY_RUN" -eq 1 ] && log "  mode:   dry run, nothing will be written"
log ""

# --- 1. Skills ---

log "Skills"
SKILLS_DEST="$TARGET/.agents/skills"
act "create .agents/skills/" mkdir -p "$SKILLS_DEST"

for legacy in $LEGACY_SKILL_NAMES; do
  if [ -d "$SKILLS_DEST/$legacy" ]; then
    act "remove renamed skill $legacy" rm -rf "$SKILLS_DEST/$legacy"
  fi
done
if [ -f "$TARGET/.agents/workflows/build.md" ]; then
  act "remove .agents/workflows/build.md (now the mule-build skill)" \
    rm -f "$TARGET/.agents/workflows/build.md"
  [ "$DRY_RUN" -eq 1 ] || rmdir "$TARGET/.agents/workflows" 2>/dev/null || true
fi

for skill in $SKILL_NAMES; do
  [ -d "$SRC/skills/$skill" ] || die "missing skill in source: $skill"
  if [ "$DRY_RUN" -eq 1 ]; then
    info "would install $skill"
  else
    rm -rf "${SKILLS_DEST:?}/$skill"
    cp -R "$SRC/skills/$skill" "$SKILLS_DEST/$skill"
    find "$SKILLS_DEST/$skill" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
    info "installed $skill"
  fi
done

if [ "$DRY_RUN" -eq 0 ]; then
  printf 'version=%s\nref=%s\n' "$VERSION" "$REPO_REF" > "$SKILLS_DEST/.mule-skills-version"
fi

# --- 2. MCP configuration ---

if [ "$WITH_MCP" -eq 1 ] && [ -n "$SELECTED" ]; then
  log ""
  log "MCP configuration"
  if has_host claude || has_host copilot || has_host gemini; then
    merge_json_mcp "$TARGET/.mcp.json" "mcpServers" 0
  fi
  if has_host vscode; then
    merge_json_mcp "$TARGET/.vscode/mcp.json" "servers" 1
  fi
  if has_host codex; then
    merge_codex_toml
  fi
elif [ "$WITH_MCP" -eq 0 ]; then
  log ""
  log "MCP configuration skipped (--no-mcp)"
fi

# --- 3. Instruction files ---

LOCATION_LINE="The reusable Mule skills are installed under \`.agents/skills/\`. Read
\`.agents/skills/<skill>/SKILL.md\` for any skill named below, and its referenced resources only as
the workflow directs."

log ""
log "Instruction files"
install_template "AGENTS.md" "$TARGET/AGENTS.md" "$LOCATION_LINE" 1
if has_host claude; then
  install_template "CLAUDE.md" "$TARGET/CLAUDE.md" "$LOCATION_LINE"
fi
if has_host gemini; then
  install_template "GEMINI.md" "$TARGET/GEMINI.md" "$LOCATION_LINE"
fi
if has_host copilot || has_host vscode; then
  install_template "copilot-instructions.md" "$TARGET/.github/copilot-instructions.md" "$LOCATION_LINE"
fi

# --- 4. Make sure .agents/ is not ignored ---

GITIGNORE="$TARGET/.gitignore"
if [ -f "$GITIGNORE" ] && grep -Eq '^\s*\.agents/?\s*$' "$GITIGNORE"; then
  if [ "$DRY_RUN" -eq 1 ]; then
    log ""
    info "would add .agents/ negations to .gitignore"
  else
    log ""
    printf '\n# mule-skills: keep the vendored skills tracked\n!.agents/\n!.agents/**\n' >> "$GITIGNORE"
    info "added .agents/ negations to .gitignore"
  fi
fi

# --- Done ---

log ""
if [ "$DRY_RUN" -eq 1 ]; then
  log "Dry run complete. Re-run without --dry-run to apply."
  exit 0
fi

log "Done. Next:"
log "  1. Fill in AGENTS.md from this project's actual evidence — see docs/project-setup.md."
log "  2. Verify MCP: codex mcp list | copilot mcp list | reload VS Code"
log "  3. Optional Anypoint access: npx -y @sfdxy/anypoint-connect@0.10.0 auth login"
log ""
