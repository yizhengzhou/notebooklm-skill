#!/usr/bin/env bash
# PreToolUse hook: validates --name argument in notebook creation commands.
# Reads Claude Code stdin JSON, extracts the Bash command, checks --name quality.
# Returns JSON with decision "block" + reason if name is bad.
# macOS-compatible (no GNU grep -P).

set -euo pipefail

# Read stdin JSON
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Only validate commands that create notebooks or add to library
if ! echo "$CMD" | grep -qE '(create_notebook\.py|notebook_manager\.py[[:space:]]+add)'; then
  exit 0
fi

# Extract --name value using sed (macOS-compatible)
# Handles: --name "value", --name 'value', --name value
NAME=$(echo "$CMD" | sed -nE 's/.*--name[[:space:]]+"([^"]+)".*/\1/p')
if [ -z "$NAME" ]; then
  NAME=$(echo "$CMD" | sed -nE "s/.*--name[[:space:]]+'([^']+)'.*/\1/p")
fi
if [ -z "$NAME" ]; then
  NAME=$(echo "$CMD" | sed -nE 's/.*--name[[:space:]]+([^[:space:]-][^[:space:]]*).*/\1/p')
fi

# If no --name found, block
if [ -z "$NAME" ]; then
  echo '{"decision":"block","reason":"❌ Notebook name is required. Use --name \"Descriptive Name\" (minimum 3 chars, no generic names like test/untitled/notebook)."}'
  exit 0
fi

# Strip role prefix [Research] or [Project] for validation
CORE_NAME=$(echo "$NAME" | sed -E 's/^\[(Research|Project)\][[:space:]]*//')

# Check length
if [ "${#CORE_NAME}" -lt 3 ]; then
  echo "{\"decision\":\"block\",\"reason\":\"❌ Notebook name too short: '$CORE_NAME' (${#CORE_NAME} chars, minimum 3). Use a descriptive name like project name or topic.\"}"
  exit 0
fi

# Check generic names
LOWER_NAME=$(echo "$CORE_NAME" | tr '[:upper:]' '[:lower:]')
GENERIC_NAMES="test testing notebook untitled new temp tmp draft sample example"
for GENERIC in $GENERIC_NAMES; do
  if [ "$LOWER_NAME" = "$GENERIC" ]; then
    echo "{\"decision\":\"block\",\"reason\":\"❌ Generic notebook name rejected: '$CORE_NAME'. Use a descriptive name (e.g., project name, topic, purpose).\"}"
    exit 0
  fi
done

# Name is valid — allow
exit 0
