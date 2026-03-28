#!/bin/bash
# Claude Code Status Line
# Reads JSON from stdin (provided by Claude Code), outputs a formatted status bar.
# Displays: model name, context usage (colored progress bar), session cost, git branch.

export PATH="/usr/local/bin:/usr/bin:/bin"

# Read stdin with timeout (5s) and size limit (64KB) to prevent hang and memory exhaustion
INPUT=$(timeout 5 head -c 65536 2>/dev/null) || INPUT=""

# Flatten to single line once (reduces fork/exec cost for subsequent json_val calls)
INPUT=$(printf '%s' "$INPUT" | tr -d '\n\r')

# Sanitize: strip control characters and ANSI escape sequence remnants from external values
# tr removes control chars (including ESC 0x1B), sed removes CSI parameter remnants like [31m
sanitize() {
  printf '%s' "$1" | tr -d '\000-\037\177' | sed 's/\[[0-9;]*[a-zA-Z]//g'
}

# Simple JSON value extractor (no jq dependency)
# INPUT is already flattened to single line.
# Uses printf (not echo) to avoid backslash expansion.
json_val() {
  printf '%s' "$INPUT" | grep -o "\"$1\"[[:space:]]*:[^,}]*" | head -1 | sed 's/.*://;s/^[[:space:]]*//;s/[[:space:]]*$//;s/"//g'
}

# Ensure value is numeric, fallback to 0
ensure_num() {
  local val="$1"
  if [[ "$val" =~ ^[0-9]+\.?[0-9]*$ ]]; then
    printf '%s' "$val"
  else
    printf '0'
  fi
}

MODEL=$(sanitize "$(json_val "display_name")")
CONTEXT_PCT=$(ensure_num "$(json_val "used_percentage")")
CONTEXT_USED=$(ensure_num "$(json_val "current_usage")")
CONTEXT_TOTAL=$(ensure_num "$(json_val "context_window_size")")
COST=$(ensure_num "$(json_val "total_cost_usd")")
BRANCH=$(sanitize "$(json_val "branch")")

MODEL=${MODEL:-"?"}
CONTEXT_PCT=${CONTEXT_PCT:-0}
CONTEXT_USED=${CONTEXT_USED:-0}
CONTEXT_TOTAL=${CONTEXT_TOTAL:-0}
COST=${COST:-0}

# Format token count (e.g., 350000 -> 350K, 1000000 -> 1.0M)
format_tokens() {
  local t="$1"
  [[ "$t" =~ ^[0-9]+$ ]] || t=0
  if [ "$t" -ge 1000000 ] 2>/dev/null; then
    local m
    local r
    m=$((t / 1000000))
    r=$(( (t % 1000000) / 100000 ))
    printf '%s' "${m}.${r}M"
  elif [ "$t" -ge 1000 ] 2>/dev/null; then
    printf '%s' "$((t / 1000))K"
  else
    printf '%s' "$t"
  fi
}

USED_FMT=$(format_tokens "$CONTEXT_USED")
TOTAL_FMT=$(format_tokens "$CONTEXT_TOTAL")

# Progress bar with color (green < 50%, yellow < 80%, red >= 80%)
BAR_WIDTH=20
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

# Output using printf — %b for the color bar, %s for sanitized text values
printf '%s  │  %b %s%% (%s/%s)  │  $%s.%s' \
  "$MODEL" "$BAR" "$PCT_INT" "$USED_FMT" "$TOTAL_FMT" "${COST_INT:-0}" "${COST_DEC:-00}"

if [ -n "$BRANCH" ]; then
  printf '  │  %s' "$BRANCH"
fi

printf '\n'
