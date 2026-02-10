#!/bin/bash
set -euo pipefail

# ============================================================================
# skills-to-zip.sh
#
# Convert Agent Skills in the skills/ directory into Claude Code plugin ZIP
# files. Each skill is packaged as an independent plugin that can be loaded
# with `claude --plugin-dir <extracted-dir>` or installed via a marketplace.
#
# Usage:
#   ./scripts/skills-to-zip.sh              # Package each skill individually
#   ./scripts/skills-to-zip.sh --all        # Also create a combined ZIP
#   ./scripts/skills-to-zip.sh --help       # Show usage
#
# Output directory: dist/ (at repository root)
# ============================================================================

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
DIST_DIR="$REPO_ROOT/dist"

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Convert Agent Skills into Claude Code plugin ZIP files.

Options:
  --all       Also create a single ZIP containing all skills as one plugin
  --out DIR   Output directory (default: dist/)
  --help      Show this help message

Each skill in skills/ is packaged as an independent plugin ZIP:
  dist/<skill-name>.zip

With --all, an additional combined ZIP is created:
  dist/all-skills.zip
EOF
  exit 0
}

# ---------------------------------------------------------------------------
# Parse frontmatter from SKILL.md
#   Extracts key: value pairs from YAML frontmatter (between --- markers)
# ---------------------------------------------------------------------------
parse_frontmatter() {
  local file="$1"
  local key="$2"
  # Read lines between the first pair of --- markers, then extract the value
  sed -n '/^---$/,/^---$/p' "$file" \
    | grep -E "^${key}:" \
    | sed "s/^${key}:[[:space:]]*//" \
    | head -1
}

# ---------------------------------------------------------------------------
# Build a plugin directory from a single skill
# ---------------------------------------------------------------------------
build_plugin_dir() {
  local skill_dir="$1"
  local dest="$2"
  local skill_name
  skill_name="$(basename "$skill_dir")"

  local skill_md="$skill_dir/SKILL.md"
  if [[ ! -f "$skill_md" ]]; then
    echo "  SKIP: $skill_name (no SKILL.md found)" >&2
    return 1
  fi

  # Extract metadata from frontmatter
  local name description
  name="$(parse_frontmatter "$skill_md" "name")"
  description="$(parse_frontmatter "$skill_md" "description")"

  # Fallback to directory name if frontmatter name is missing
  name="${name:-$skill_name}"

  # Create plugin structure
  mkdir -p "$dest/.claude-plugin"
  mkdir -p "$dest/skills/$skill_name"

  # Generate plugin.json manifest
  cat > "$dest/.claude-plugin/plugin.json" <<MANIFEST
{
  "name": "${name}",
  "description": "${description}",
  "version": "1.0.0"
}
MANIFEST

  # Copy all skill files (SKILL.md + any supporting files)
  cp -r "$skill_dir"/. "$dest/skills/$skill_name/"
}

# ---------------------------------------------------------------------------
# Create a ZIP from a directory
# ---------------------------------------------------------------------------
create_zip() {
  local source_dir="$1"
  local zip_path="$2"
  local base_name
  base_name="$(basename "$source_dir")"

  # Create ZIP from the parent directory so the archive root is the plugin dir
  (cd "$(dirname "$source_dir")" && zip -rq "$zip_path" "$base_name")
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CREATE_ALL=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      CREATE_ALL=true
      shift
      ;;
    --out)
      DIST_DIR="$2"
      shift 2
      ;;
    --help|-h)
      usage
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      ;;
  esac
done

# Validate skills directory
if [[ ! -d "$SKILLS_DIR" ]]; then
  echo "Error: Skills directory not found at $SKILLS_DIR" >&2
  exit 1
fi

# Collect skill directories
skill_dirs=()
for dir in "$SKILLS_DIR"/*/; do
  [[ -d "$dir" ]] && skill_dirs+=("$dir")
done

if [[ ${#skill_dirs[@]} -eq 0 ]]; then
  echo "Error: No skill directories found in $SKILLS_DIR" >&2
  exit 1
fi

# Prepare output directory
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

TMPDIR_BASE="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_BASE"' EXIT

echo "=== Skills to ZIP Converter ==="
echo ""
echo "Source:  $SKILLS_DIR"
echo "Output:  $DIST_DIR"
echo ""

count=0

# --- Package each skill as an individual plugin ZIP ---
for skill_dir in "${skill_dirs[@]}"; do
  skill_name="$(basename "$skill_dir")"
  plugin_tmp="$TMPDIR_BASE/individual/$skill_name"
  mkdir -p "$plugin_tmp"

  if build_plugin_dir "$skill_dir" "$plugin_tmp"; then
    zip_path="$DIST_DIR/${skill_name}.zip"
    create_zip "$plugin_tmp" "$zip_path"
    echo "  OK: $zip_path"
    count=$((count + 1))
  fi
done

# --- Optionally create a combined ZIP with all skills ---
if [[ "$CREATE_ALL" == true ]] && [[ $count -gt 0 ]]; then
  combined_tmp="$TMPDIR_BASE/combined/all-skills"
  mkdir -p "$combined_tmp/.claude-plugin"
  mkdir -p "$combined_tmp/skills"

  # Build combined plugin.json
  cat > "$combined_tmp/.claude-plugin/plugin.json" <<MANIFEST
{
  "name": "all-skills",
  "description": "All Agent Skills bundled as a single plugin",
  "version": "1.0.0"
}
MANIFEST

  # Copy each skill into the combined plugin
  for skill_dir in "${skill_dirs[@]}"; do
    skill_name="$(basename "$skill_dir")"
    if [[ -f "$skill_dir/SKILL.md" ]]; then
      mkdir -p "$combined_tmp/skills/$skill_name"
      cp -r "$skill_dir"/. "$combined_tmp/skills/$skill_name/"
    fi
  done

  zip_path="$DIST_DIR/all-skills.zip"
  create_zip "$combined_tmp" "$zip_path"
  echo "  OK: $zip_path (combined)"
fi

echo ""
echo "Done. $count skill(s) converted."
echo ""
echo "--- How to use ---"
echo "1. Extract the ZIP:     unzip dist/<name>.zip -d /tmp/plugin"
echo "2. Load in Claude Code: claude --plugin-dir /tmp/plugin/<name>"
echo "3. Or copy skills to:   ~/.claude/skills/"
