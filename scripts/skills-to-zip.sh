#!/bin/bash
set -euo pipefail

# ============================================================================
# skills-to-zip.sh
#
# Convert Agent Skills into ZIP files for uploading to Claude Desktop.
#
# Claude Desktop (Settings > Capabilities > Skills) requires skills to be
# uploaded as ZIP files with a specific structure:
#
#   <skill-name>.zip
#   └── <skill-name>/
#       ├── SKILL.md           (required)
#       └── (supporting files)  (optional)
#
# Usage:
#   ./scripts/skills-to-zip.sh                                 # Convert all
#   ./scripts/skills-to-zip.sh --source ~/.claude/skills       # Custom source
#   ./scripts/skills-to-zip.sh session-start-hook              # Specific skill
#   ./scripts/skills-to-zip.sh --help
#
# Output: dist/ (at repository root)
# ============================================================================

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
DIST_DIR="$REPO_ROOT/dist"
TARGET_SKILL=""

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS] [SKILL_NAME]

Convert Agent Skills into ZIP files for Claude Desktop upload.

Arguments:
  SKILL_NAME             Convert only the specified skill (directory name)

Options:
  --source DIR   Source directory containing skill folders (default: skills/)
  --out DIR      Output directory (default: dist/)
  --help         Show this help message

Examples:
  $(basename "$0")                                 # Convert all skills in skills/
  $(basename "$0") --source ~/.claude/skills       # Convert from another directory
  $(basename "$0") session-start-hook              # Convert a specific skill only

Output:
  dist/<skill-name>.zip   (one ZIP per skill, ready for Desktop upload)

Upload:
  Claude Desktop > Settings > Capabilities > Skills > + Add
EOF
  exit 0
}

# ---------------------------------------------------------------------------
# Parse a single field from YAML frontmatter (between --- markers)
# ---------------------------------------------------------------------------
parse_frontmatter() {
  local file="$1"
  local key="$2"
  sed -n '/^---$/,/^---$/p' "$file" \
    | grep -E "^${key}:" \
    | sed "s/^${key}:[[:space:]]*//" \
    | head -1
}

# ---------------------------------------------------------------------------
# Validate SKILL.md frontmatter against Claude Desktop requirements
# ---------------------------------------------------------------------------
validate_skill() {
  local skill_dir="$1"
  local folder_name
  folder_name="$(basename "$skill_dir")"

  local skill_md="$skill_dir/SKILL.md"
  if [[ ! -f "$skill_md" ]]; then
    echo "  SKIP: $folder_name/ (no SKILL.md)"
    return 1
  fi

  local name description
  name="$(parse_frontmatter "$skill_md" "name")"
  description="$(parse_frontmatter "$skill_md" "description")"

  # name is required
  if [[ -z "$name" ]]; then
    echo "  WARN: $folder_name/ - frontmatter 'name' is missing"
  fi

  # name max 64 characters
  if [[ -n "$name" ]] && [[ ${#name} -gt 64 ]]; then
    echo "  WARN: $folder_name/ - name exceeds 64 chars (${#name})"
  fi

  # description is required
  if [[ -z "$description" ]]; then
    echo "  WARN: $folder_name/ - frontmatter 'description' is missing"
  fi

  # description max 200 characters
  if [[ -n "$description" ]] && [[ ${#description} -gt 200 ]]; then
    echo "  WARN: $folder_name/ - description exceeds 200 chars (${#description}); Desktop may truncate"
  fi

  # folder name vs name mismatch
  if [[ -n "$name" ]] && [[ "$name" != "$folder_name" ]]; then
    echo "  WARN: $folder_name/ - folder name differs from frontmatter name '$name'"
  fi

  return 0
}

# ---------------------------------------------------------------------------
# Create a ZIP for one skill
# ---------------------------------------------------------------------------
package_skill() {
  local skill_dir="$1"
  local dest_dir="$2"
  local folder_name
  folder_name="$(basename "$skill_dir")"

  local tmp_parent="$dest_dir/_tmp_$$"
  mkdir -p "$tmp_parent/$folder_name"

  # Copy all files from the skill directory
  cp -r "$skill_dir"/. "$tmp_parent/$folder_name/"

  # Create ZIP with the folder as the root entry
  local zip_path="$dest_dir/${folder_name}.zip"
  (cd "$tmp_parent" && zip -rq "$zip_path" "$folder_name")

  rm -rf "$tmp_parent"
  echo "$zip_path"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      SKILLS_DIR="$2"
      shift 2
      ;;
    --out)
      DIST_DIR="$2"
      shift 2
      ;;
    --help|-h)
      usage
      ;;
    -*)
      echo "Unknown option: $1" >&2
      echo "" >&2
      usage
      ;;
    *)
      TARGET_SKILL="$1"
      shift
      ;;
  esac
done

# Resolve symlinks for display
SKILLS_DIR_RESOLVED="$(cd "$SKILLS_DIR" 2>/dev/null && pwd)" || {
  echo "Error: Source directory not found: $SKILLS_DIR" >&2
  exit 1
}

# Collect skill directories
skill_dirs=()
if [[ -n "$TARGET_SKILL" ]]; then
  target_path="$SKILLS_DIR_RESOLVED/$TARGET_SKILL"
  if [[ ! -d "$target_path" ]]; then
    echo "Error: Skill not found: $target_path" >&2
    exit 1
  fi
  skill_dirs+=("$target_path")
else
  for dir in "$SKILLS_DIR_RESOLVED"/*/; do
    [[ -d "$dir" ]] && skill_dirs+=("$dir")
  done
fi

if [[ ${#skill_dirs[@]} -eq 0 ]]; then
  echo "Error: No skill directories found in $SKILLS_DIR_RESOLVED" >&2
  exit 1
fi

# Prepare output directory
mkdir -p "$DIST_DIR"

echo "=== Skills to ZIP Converter (for Claude Desktop) ==="
echo ""
echo "Source:  $SKILLS_DIR_RESOLVED"
echo "Output:  $DIST_DIR"
echo "Skills:  ${#skill_dirs[@]} found"
echo ""

ok_count=0
skip_count=0

for skill_dir in "${skill_dirs[@]}"; do
  folder_name="$(basename "$skill_dir")"

  # Validate (prints warnings but continues)
  if ! validate_skill "$skill_dir"; then
    skip_count=$((skip_count + 1))
    continue
  fi

  # Package
  zip_path="$(package_skill "$skill_dir" "$DIST_DIR")"
  echo "  OK: $zip_path"
  ok_count=$((ok_count + 1))
done

echo ""
echo "Done. ${ok_count} ZIP(s) created, ${skip_count} skipped."

if [[ $ok_count -gt 0 ]]; then
  echo ""
  echo "Upload: Claude Desktop > Settings > Capabilities > Skills > + Add"
fi
