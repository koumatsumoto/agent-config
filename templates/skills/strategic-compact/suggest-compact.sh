#!/bin/bash
set -euo pipefail

THRESHOLD=${COMPACT_THRESHOLD:-50}
REMINDER_INTERVAL=${COMPACT_REMINDER_INTERVAL:-25}
STALE_SECONDS=${COMPACT_COUNTER_STALE_SECONDS:-21600}

hash_text() {
  if command -v sha1sum >/dev/null 2>&1; then
    printf '%s' "$1" | sha1sum | awk '{print $1}'
    return
  fi

  if command -v shasum >/dev/null 2>&1; then
    printf '%s' "$1" | shasum | awk '{print $1}'
    return
  fi

  printf '%s' "$1" | md5sum | awk '{print $1}'
}

session_source="${CLAUDE_SESSION_ID:-${CLAUDE_TRANSCRIPT_PATH:-${PWD}}}"
session_key=$(hash_text "$session_source")
COUNTER_FILE="/tmp/claude-tool-count-${session_key}"

get_mtime() {
  local file="$1"

  if stat -c %Y "$file" >/dev/null 2>&1; then
    stat -c %Y "$file"
    return
  fi

  if stat -f %m "$file" >/dev/null 2>&1; then
    stat -f %m "$file"
    return
  fi

  date +%s
}

if [ -f "$COUNTER_FILE" ]; then
  now=$(date +%s)
  last_modified=$(get_mtime "$COUNTER_FILE")

  if [ $((now - last_modified)) -gt "$STALE_SECONDS" ]; then
    rm -f "$COUNTER_FILE"
  fi
fi

count=1
if [ -f "$COUNTER_FILE" ]; then
  previous=$(cat "$COUNTER_FILE" 2>/dev/null || echo "0")

  if [[ "$previous" =~ ^[0-9]+$ ]]; then
    count=$((previous + 1))
  fi
fi

printf '%s\n' "$count" > "$COUNTER_FILE"

if [ "$count" -eq "$THRESHOLD" ]; then
  echo "[StrategicCompact] ${THRESHOLD} tool calls reached - consider /compact at this phase boundary" >&2
  exit 0
fi

if [ "$count" -gt "$THRESHOLD" ] && [ $((count % REMINDER_INTERVAL)) -eq 0 ]; then
  echo "[StrategicCompact] ${count} tool calls - consider /compact if context is stale" >&2
fi
