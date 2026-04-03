#!/usr/bin/env bash
set -euo pipefail

# Install Thistlewing into an existing Claude Code installation
# Usage: bash install.sh

CLAUDE_CONFIG="${HOME}/.claude.json"
CLAUDE_CONFIG_ALT="${HOME}/.claude/.config.json"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPANION_FILE="${SCRIPT_DIR}/companion.json"

# Find Claude config
if [ -f "$CLAUDE_CONFIG" ]; then
  CONFIG="$CLAUDE_CONFIG"
elif [ -f "$CLAUDE_CONFIG_ALT" ]; then
  CONFIG="$CLAUDE_CONFIG_ALT"
else
  echo "Error: Claude Code config not found at $CLAUDE_CONFIG or $CLAUDE_CONFIG_ALT"
  echo "Is Claude Code installed?"
  exit 1
fi

echo "Found Claude config at: $CONFIG"

# Check for jq
if ! command -v jq &>/dev/null; then
  echo "Error: jq is required. Install it with:"
  echo "  macOS:  brew install jq"
  echo "  Linux:  sudo apt install jq"
  exit 1
fi

# Backup existing config
BACKUP="${CONFIG}.backup-$(date +%s)"
cp "$CONFIG" "$BACKUP"
echo "Backed up config to: $BACKUP"

# Read companion data
NAME=$(jq -r '.name' "$COMPANION_FILE")
PERSONALITY=$(jq -r '.personality' "$COMPANION_FILE")
HATCHED_AT=$(jq -r '.hatchedAt' "$COMPANION_FILE")

# Apply companion to Claude config
jq --arg name "$NAME" \
   --arg personality "$PERSONALITY" \
   --argjson hatchedAt "$HATCHED_AT" \
   '.companion = {name: $name, personality: $personality, hatchedAt: $hatchedAt}' \
   "$CONFIG" > "${CONFIG}.tmp" && mv "${CONFIG}.tmp" "$CONFIG"

echo ""
echo "Thistlewing installed!"
echo ""
echo "   /\\  /\\"
echo "  ((·)(·))"
echo "  (  ><  )"
echo "   \`----´"
echo ""
echo "Name:        $NAME"
echo "Personality: $PERSONALITY"
echo ""
echo "Restart Claude Code to see your new buddy."
echo ""
echo "Note: This sets the name and personality. The buddy's visual species"
echo "depends on your account's UUID + the binary salt. If you see a different"
echo "species and want an owl, install any-buddy and run:"
echo "  npx any-buddy --species owl --rarity uncommon"
