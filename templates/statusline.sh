#!/bin/bash
# Claude Code Status Line
# Reads JSON from stdin (provided by Claude Code), outputs a formatted status bar.
# Two-line layout:
#   Line 1: 🤖 model [agent] [style] │ bar pct% │ $cost │ 5h:rate% ~reset
#   Line 2: 🌳 branch Nfiles +A/-R (only when git branch exists)

export PATH="/usr/local/bin:/usr/bin:/bin"

# Read stdin with timeout (5s) and size limit (64KB) to prevent hang and memory exhaustion
INPUT=$(timeout 5 head -c 65536 2>/dev/null) || INPUT=""

# Flatten to single line once (reduces fork/exec cost for subsequent json_val calls)
INPUT=$(printf '%s' "$INPUT" | tr -d '\n\r')

# Sanitize: strip control characters and ANSI escape sequence remnants from external values
# tr removes control chars (including ESC 0x1B), sed removes CSI parameter remnants like [31m
sanitize() {
  printf '%s' "$1" | tr -d '\000-\037\177\200-\237' | sed 's/\[[0-9;]*[a-zA-Z]//g'
}

# Simple JSON value extractor (no jq dependency)
# INPUT is already flattened to single line.
# Uses printf (not echo) to avoid backslash expansion.
# IMPORTANT: Arguments must be literal strings only. Do not pass external input.
json_val() {
  [[ "$1" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || return 1
  printf '%s' "$INPUT" | grep -o "\"$1\"[[:space:]]*:[^,}]*" | head -1 | sed 's/.*://;s/^[[:space:]]*//;s/[[:space:]]*$//;s/"//g'
}

# Extract value from nested JSON by parent key context
# Usage: json_nested_val "five_hour" "used_percentage"
# IMPORTANT: Arguments must be literal strings only. Do not pass external input.
json_nested_val() {
  [[ "$1" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || return 1
  [[ "$2" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || return 1
  local parent="$1"
  local key="$2"
  printf '%s' "$INPUT" | grep -o "\"$parent\"[^}]*" | grep -o "\"$key\"[[:space:]]*:[^,}]*" | head -1 | sed 's/.*://;s/^[[:space:]]*//;s/[[:space:]]*$//;s/"//g'
}

# Ensure value is numeric, fallback to 0
ensure_num() {
  local val="$1"
  if [[ "$val" =~ ^[0-9]{1,10}\.?[0-9]{0,4}$ ]]; then
    printf '%s' "$val"
  else
    printf '0'
  fi
}

# Format Unix epoch to local time (e.g., "10AM", "2PM")
format_reset_time() {
  local epoch="${1%.*}"  # truncate decimal part (e.g., 1711699200.0 -> 1711699200)
  [[ "$epoch" =~ ^[0-9]+$ ]] && [ "$epoch" -gt 0 ] 2>/dev/null || return
  date -d "@$epoch" '+%-I%p' 2>/dev/null || date -r "$epoch" '+%-I%p' 2>/dev/null
}

MODEL=$(sanitize "$(json_val "display_name")")
CONTEXT_PCT=$(ensure_num "$(json_nested_val "context_window" "used_percentage")")
COST=$(ensure_num "$(json_val "total_cost_usd")")
RATE_5H=$(ensure_num "$(json_nested_val "five_hour" "used_percentage")")
RATE_5H_RESETS=$(ensure_num "$(json_nested_val "five_hour" "resets_at")")
LINES_ADDED=$(ensure_num "$(json_val "total_lines_added")")
LINES_REMOVED=$(ensure_num "$(json_val "total_lines_removed")")
# JSON branch (worktree session only); fall back to git for normal sessions
BRANCH=$(sanitize "$(json_val "branch")")
[ -z "$BRANCH" ] && BRANCH=$(sanitize "$(timeout 2 git branch --show-current 2>/dev/null)")
AGENT_NAME=$(sanitize "$(json_nested_val "agent" "name")")
OUTPUT_STYLE=$(sanitize "$(json_nested_val "output_style" "name")")

MODEL=${MODEL:-"?"}
CONTEXT_PCT=${CONTEXT_PCT:-0}
COST=${COST:-0}
RATE_5H=${RATE_5H:-0}
LINES_ADDED=${LINES_ADDED:-0}
LINES_REMOVED=${LINES_REMOVED:-0}

# Progress bar with color (green < 50%, yellow < 80%, red >= 80%)
BAR_WIDTH=10
PCT_INT=$(printf "%.0f" "$CONTEXT_PCT" 2>/dev/null || echo 0)
[[ "$PCT_INT" =~ ^[0-9]+$ ]] || PCT_INT=0
FILLED=$(( PCT_INT * BAR_WIDTH / 100 ))
EMPTY=$(( BAR_WIDTH - FILLED ))

if [ "$PCT_INT" -ge 80 ] 2>/dev/null; then
  COLOR=$'\033[31m'
elif [ "$PCT_INT" -ge 50 ] 2>/dev/null; then
  COLOR=$'\033[33m'
else
  COLOR=$'\033[32m'
fi
RESET=$'\033[0m'

BAR="${COLOR}"
for ((i=0; i<FILLED; i++)); do BAR+="█"; done
for ((i=0; i<EMPTY; i++)); do BAR+="░"; done
BAR+="${RESET}"

# Format cost (handle both integer and decimal inputs)
if [[ "$COST" == *.* ]]; then
  COST_INT=${COST%.*}
  COST_DEC=${COST#*.}
  COST_DEC=${COST_DEC:0:2}
  [[ ${#COST_DEC} -eq 1 ]] && COST_DEC="${COST_DEC}0"
else
  COST_INT=$COST
  COST_DEC="00"
fi

# Format rate limit
RATE_5H_INT=$(printf "%.0f" "$RATE_5H" 2>/dev/null || echo 0)
[[ "$RATE_5H_INT" =~ ^[0-9]+$ ]] || RATE_5H_INT=0

# Git changed file count (working tree + staged)
GIT_FILES=$(timeout 2 git diff --numstat HEAD 2>/dev/null | wc -l | tr -d ' ')
[[ "$GIT_FILES" =~ ^[0-9]+$ ]] || GIT_FILES=0

# Line 1: 🤖 Model [Agent] [Style] │ Bar PCT% │ $Cost │ 5h:Rate% ~Reset
RESET_TIME=$(format_reset_time "$RATE_5H_RESETS")

LINE1="🤖 ${MODEL}"
[ -n "$AGENT_NAME" ] && LINE1+=" ${AGENT_NAME}"
[ -n "$OUTPUT_STYLE" ] && LINE1+=" [${OUTPUT_STYLE}]"
printf '%s │ %s %s%% │ $%s.%s │ 5h:%s%%' \
  "$LINE1" "$BAR" "$PCT_INT" "${COST_INT:-0}" "${COST_DEC:-00}" "$RATE_5H_INT"
[ -n "$RESET_TIME" ] && printf ' ~%s' "$RESET_TIME"

# Line 2: 🌳 Branch Nfiles +A/-R (only when branch exists)
if [ -n "$BRANCH" ]; then
  printf '\n🌳 %s' "$BRANCH"
  [ "$GIT_FILES" -gt 0 ] 2>/dev/null && printf ' %s files' "$GIT_FILES"
  { [ "$LINES_ADDED" -gt 0 ] || [ "$LINES_REMOVED" -gt 0 ]; } 2>/dev/null && \
    printf ' +%s/-%s' "$LINES_ADDED" "$LINES_REMOVED"
fi

printf '\n'
