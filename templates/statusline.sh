#!/bin/bash
# Claude Code Status Line
# Reads JSON from stdin (provided by Claude Code), outputs a formatted status bar.
# Two-line layout:
#   Line 1: 🤖 model [agent] [style] │ bar pct% │ $cost │ 5h:N% ~reset │ 7d:N% ~DAY.hAM
#   Line 2: 🌳 branch Nfiles +A/-R (only when git branch exists)
# Rate limits: 5h/7d always shown. Yellow >= 50%, red >= 80%.
# Context bar turns red-background at >= 90%.

# --- Environment hardening ---
# Include /mingw64/bin for Git Bash (Git for Windows) compatibility
if [ -d "/mingw64/bin" ]; then
  export PATH="/mingw64/bin:/usr/local/bin:/usr/bin:/bin"
else
  export PATH="/usr/local/bin:/usr/bin:/bin"
fi
# Clear git env vars to prevent repo/config redirection attacks
unset GIT_DIR GIT_WORK_TREE GIT_CONFIG GIT_CONFIG_GLOBAL GIT_EXEC_PATH GIT_EXTERNAL_DIFF 2>/dev/null

# timeout fallback: use timeout if available, otherwise run without it
_timeout() {
  if command -v timeout >/dev/null 2>&1; then
    timeout "$@"
  else
    # skip the first arg (duration) and run the rest directly
    shift
    "$@"
  fi
}

# Read stdin with timeout (5s) and size limit (64KB) to prevent hang and memory exhaustion
INPUT=$(_timeout 5 head -c 65536 2>/dev/null) || INPUT=""

# Flatten to single line (pure bash, no fork)
INPUT="${INPUT//$'\n'/}"
INPUT="${INPUT//$'\r'/}"

# Sanitize: strip control characters and ANSI CSI remnants from external values
# tr removes C0 (0x00-0x1F), DEL (0x7F), C1 (0x80-0x9F) in byte mode (LC_ALL=C).
# sed removes CSI parameter remnants (e.g., [31m [0K) using typical SGR/cursor terminators only,
# avoiding false positives on legitimate text like "[JIRA-123]".
sanitize() {
  LC_ALL=C printf '%s' "$1" | tr -d '\000-\037\177\200-\237' | sed 's/\[[0-9;]*[mGHJKsu]//g'
}

# Pure bash JSON value extractor (no fork, no jq dependency)
# Uses parameter expansion only. No eval.
# LIMITATION: Cannot handle values containing commas or nested objects.
# IMPORTANT: Arguments must be literal strings only. Do not pass external input.
json_val() {
  [[ "$1" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || return 1
  local key="\"$1\""
  local rest="${INPUT#*$key}"
  [[ "$rest" == "$INPUT" ]] && return 1
  rest="${rest#*:}"
  rest="${rest#"${rest%%[! ]*}"}"  # ltrim spaces
  rest="${rest%%[,\}]*}"           # until , or }
  rest="${rest//\"/}"              # remove quotes
  printf '%s' "$rest"
}

# Pure bash nested JSON value extractor (no fork)
# Usage: json_nested_val "five_hour" "used_percentage"
# LIMITATION: No scoping — searches for child key anywhere after parent key.
# Works when child key is unique or appears first within the parent object.
# IMPORTANT: Arguments must be literal strings only. Do not pass external input.
json_nested_val() {
  [[ "$1" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || return 1
  [[ "$2" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || return 1
  local parent_key="\"$1\""
  local child_key="\"$2\""
  local rest="${INPUT#*$parent_key}"
  [[ "$rest" == "$INPUT" ]] && return 1
  # Scoping removed: %%\}* broke when parent contained nested objects (e.g.,
  # context_window.current_usage). First match of child_key after parent is used.
  # For reliable parsing, the jq-based extraction path is preferred.
  local inner="${rest#*$child_key}"
  [[ "$inner" == "$rest" ]] && return 1
  inner="${inner#*:}"
  inner="${inner#"${inner%%[! ]*}"}"  # ltrim spaces
  inner="${inner%%[,\}]*}"            # until , or }
  inner="${inner//\"/}"               # remove quotes
  printf '%s' "$inner"
}

# Ensure value is numeric, fallback to 0
ensure_num() {
  local val="$1"
  if [[ "$val" =~ ^[0-9]{1,10}\.?[0-9]{0,10}$ ]]; then
    printf '%s' "$val"
  else
    printf '0'
  fi
}

# Format Unix epoch to local time
# Usage: format_reset_time "epoch"             → "6PM"
#        format_reset_time "epoch" '+%^a.%-I%p' → "MON.3PM"
# fmt argument must be a literal format string starting with "+".
format_reset_time() {
  local epoch="${1%.*}"  # truncate decimal part
  local fmt="${2:-+%-I%p}"
  [[ "$epoch" =~ ^[0-9]+$ ]] && [ "$epoch" -gt 0 ] 2>/dev/null || return
  [[ "$fmt" == +* ]] || return 1  # format must start with +
  LC_TIME=C date -d "@$epoch" "$fmt" 2>/dev/null || LC_TIME=C date -r "$epoch" "$fmt" 2>/dev/null
}

# Format rate limit section with conditional display and color
# Usage: format_rate_section "$RATE_INT" "$RESET_TIME" "5h" [min_pct]
# Displays nothing if rate < min_pct (default 20%). Pass 0 to always show.
format_rate_section() {
  local rate_int="$1" reset_time="$2" label="$3" min_pct="${4:-20}"
  local rate_color="" reset_clr=$'\033[0m'
  [ "$rate_int" -lt "$min_pct" ] 2>/dev/null && return
  if [ "$rate_int" -ge 80 ] 2>/dev/null; then
    rate_color=$'\033[31m'
  elif [ "$rate_int" -ge 50 ] 2>/dev/null; then
    rate_color=$'\033[33m'
  fi
  if [ -n "$rate_color" ]; then
    printf ' │ %s%s:%s%%%s' "$rate_color" "$label" "$rate_int" "$reset_clr"
  else
    printf ' │ %s:%s%%' "$label" "$rate_int"
  fi
  [ -n "$reset_time" ] && printf ' ~%s' "$reset_time"
}

# --- Data extraction ---

# Primary: jq (single fork, reliable JSON parsing for nested objects)
if command -v jq >/dev/null 2>&1; then
  JQ_OUT=$(printf '%s' "$INPUT" | jq -r '[
    (.model.display_name // ""),
    ((.context_window.used_percentage // 0) | tostring),
    ((.cost.total_cost_usd // 0) | tostring),
    ((.rate_limits.five_hour.used_percentage // 0) | tostring),
    ((.rate_limits.five_hour.resets_at // 0) | tostring),
    ((.rate_limits.seven_day.used_percentage // 0) | tostring),
    ((.rate_limits.seven_day.resets_at // 0) | tostring),
    (.output_style.name // ""),
    (.agent.name // ""),
    (.worktree.branch // "")
  ] | @tsv' 2>/dev/null)

  if [ -n "$JQ_OUT" ]; then
    IFS=$'\t' read -r MODEL CONTEXT_PCT COST RATE_5H RATE_5H_RESETS RATE_7D RATE_7D_RESETS OUTPUT_STYLE AGENT_NAME BRANCH <<< "$JQ_OUT"
    # Apply same defenses as bash fallback path
    MODEL=$(sanitize "$MODEL")
    AGENT_NAME=$(sanitize "$AGENT_NAME")
    OUTPUT_STYLE=$(sanitize "$OUTPUT_STYLE")
    BRANCH=$(sanitize "$BRANCH")
    CONTEXT_PCT=$(ensure_num "$CONTEXT_PCT")
    COST=$(ensure_num "$COST")
    RATE_5H=$(ensure_num "$RATE_5H")
    RATE_5H_RESETS=$(ensure_num "$RATE_5H_RESETS")
    RATE_7D=$(ensure_num "$RATE_7D")
    RATE_7D_RESETS=$(ensure_num "$RATE_7D_RESETS")
  fi
fi

# Fallback: pure bash extraction (for systems without jq)
if [ -z "$MODEL" ]; then
  MODEL=$(sanitize "$(json_val "display_name")")
  CONTEXT_PCT=$(ensure_num "$(json_nested_val "context_window" "used_percentage")")
  COST=$(ensure_num "$(json_val "total_cost_usd")")
  RATE_5H=$(ensure_num "$(json_nested_val "five_hour" "used_percentage")")
  RATE_5H_RESETS=$(ensure_num "$(json_nested_val "five_hour" "resets_at")")
  RATE_7D=$(ensure_num "$(json_nested_val "seven_day" "used_percentage")")
  RATE_7D_RESETS=$(ensure_num "$(json_nested_val "seven_day" "resets_at")")
  # JSON branch (worktree session only); git fallback handled below
  BRANCH=$(sanitize "$(json_val "branch")")
  AGENT_NAME=$(sanitize "$(json_nested_val "agent" "name")")
  OUTPUT_STYLE=$(sanitize "$(json_nested_val "output_style" "name")")
fi


MODEL=${MODEL:-"?"}
CONTEXT_PCT=${CONTEXT_PCT:-0}
COST=${COST:-0}
RATE_5H=${RATE_5H:-0}
RATE_7D=${RATE_7D:-0}

# --- Git data (single timeout for branch + numstat) ---
# git trusts the CWD repo (.git/config). core.fsmonitor is disabled to prevent
# arbitrary code execution from malicious repositories.

if [ -z "$BRANCH" ]; then
  # head -n 10001: 1 branch line + up to 10000 numstat lines
  GIT_DATA=$(_timeout 2 sh -c '
    b=$(git -c core.fsmonitor= rev-parse --abbrev-ref HEAD 2>/dev/null)
    [ "$b" = "HEAD" ] && b=""  # detached HEAD → empty
    printf "B:%s\n" "$b"
    git -c core.fsmonitor= diff --numstat HEAD 2>/dev/null
  ' 2>/dev/null | head -n 10001)
  BRANCH=$(sanitize "${GIT_DATA%%$'\n'*}")
  BRANCH="${BRANCH#B:}"
  if [[ "$GIT_DATA" == *$'\n'* ]]; then
    GIT_NUMSTAT="${GIT_DATA#*$'\n'}"
  else
    GIT_NUMSTAT=""
  fi
else
  GIT_NUMSTAT=$(_timeout 2 git -c core.fsmonitor= diff --numstat HEAD 2>/dev/null | head -n 10000)
fi

# Git stats: file count, lines added, lines removed (tracked files only)
GIT_FILES=$(printf '%s' "$GIT_NUMSTAT" | grep -c .)
GIT_ADDED=$(printf '%s' "$GIT_NUMSTAT" | awk '$1 != "-" {s+=$1} END {printf "%d", s+0}')
GIT_REMOVED=$(printf '%s' "$GIT_NUMSTAT" | awk '$2 != "-" {s+=$2} END {printf "%d", s+0}')
[[ "$GIT_FILES" =~ ^[0-9]+$ ]] || GIT_FILES=0
[[ "$GIT_ADDED" =~ ^[0-9]+$ ]] || GIT_ADDED=0
[[ "$GIT_REMOVED" =~ ^[0-9]+$ ]] || GIT_REMOVED=0

# --- Progress bar (4-level color, no fork) ---

BAR_WIDTH=6
PCT_INT=$(printf "%.0f" "$CONTEXT_PCT" 2>/dev/null || echo 0)
[[ "$PCT_INT" =~ ^[0-9]+$ ]] || PCT_INT=0
FILLED=$(( PCT_INT * BAR_WIDTH / 100 ))
EMPTY=$(( BAR_WIDTH - FILLED ))

if [ "$PCT_INT" -ge 90 ] 2>/dev/null; then
  COLOR=$'\033[41;97m'   # red background + bright white
elif [ "$PCT_INT" -ge 80 ] 2>/dev/null; then
  COLOR=$'\033[31m'      # red
elif [ "$PCT_INT" -ge 50 ] 2>/dev/null; then
  COLOR=$'\033[33m'      # yellow
else
  COLOR=$'\033[32m'      # green
fi
RST=$'\033[0m'

printf -v bar_filled '%*s' "$FILLED" ''
bar_filled="${bar_filled// /█}"
printf -v bar_empty '%*s' "$EMPTY" ''
bar_empty="${bar_empty// /░}"
BAR="${COLOR}${bar_filled}${bar_empty}${RST}"

# --- Format cost ---

if [[ "$COST" == *.* ]]; then
  COST_INT=${COST%.*}
  COST_DEC=${COST#*.}
  COST_DEC=${COST_DEC:0:2}
  [[ ${#COST_DEC} -eq 1 ]] && COST_DEC="${COST_DEC}0"
else
  COST_INT=$COST
  COST_DEC="00"
fi

# --- Format rate limits ---

RATE_5H_INT=$(printf "%.0f" "$RATE_5H" 2>/dev/null || echo 0)
[[ "$RATE_5H_INT" =~ ^[0-9]+$ ]] || RATE_5H_INT=0
RATE_7D_INT=$(printf "%.0f" "$RATE_7D" 2>/dev/null || echo 0)
[[ "$RATE_7D_INT" =~ ^[0-9]+$ ]] || RATE_7D_INT=0

RESET_5H=$(format_reset_time "$RATE_5H_RESETS")
RESET_7D=$(format_reset_time "$RATE_7D_RESETS" '+%^a.%-I%p')

# --- Output ---

# Line 1: 🤖 Model [Agent] [Style] │ Bar PCT% │ $Cost │ 5h:N% ~reset │ 7d:N% ~DAY.hAM
LINE1="🤖 ${MODEL}"
[ -n "$AGENT_NAME" ] && LINE1+=" ${AGENT_NAME}"
[ -n "$OUTPUT_STYLE" ] && LINE1+=" [${OUTPUT_STYLE}]"
printf '%s │ %s %s%% │ $%s.%s' \
  "$LINE1" "$BAR" "$PCT_INT" "${COST_INT:-0}" "${COST_DEC:-00}"
format_rate_section "$RATE_5H_INT" "$RESET_5H" "5h" 0    # always show
format_rate_section "$RATE_7D_INT" "$RESET_7D" "7d" 0    # always show

# Line 2: 🌳 Branch Nfiles +A/-R (only when branch exists)
if [ -n "$BRANCH" ]; then
  printf '\n🌳 %s' "$BRANCH"
  if [ "$GIT_FILES" -gt 0 ] 2>/dev/null; then
    printf ' %s files' "$GIT_FILES"
    { [ "$GIT_ADDED" -gt 0 ] || [ "$GIT_REMOVED" -gt 0 ]; } 2>/dev/null && \
      printf ' +%s/-%s' "$GIT_ADDED" "$GIT_REMOVED"
  fi
fi

printf '\n'
