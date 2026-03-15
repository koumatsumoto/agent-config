#!/usr/bin/env bash
set -euo pipefail

# pack-md.sh
# AI に渡す前の Markdown から、意味を持ちにくい空白や装飾を減らす。
#
# 何をするか:
# - 連続空行を 1 行に圧縮
# - コードフェンス外の HTML コメントを削除
# - テーブルの `| cell |` を `|cell|` に圧縮
# - 末尾空白を整理（Markdown hard break の 2 スペースは保持）
# - fenced code block と YAML front matter は保持
#
# 想定用途:
# - 人間向けの元ファイルはそのままにして、AI 入力用の packed 版だけ作る
# - `./scripts/pack-md.sh input.md > input.llm.md`
# - `./scripts/pack-md.sh -i README.md`
#
# 非対象:
# - 人間向け formatter の置き換え
# - テーブルを箇条書きへ変換するような構造変更
# - Markdown 仕様を完全保持した厳密な minify

usage() {
  cat <<'EOF'
Usage:
  pack-md.sh [FILE]
  pack-md.sh -i FILE...
  pack-md.sh -h

Reduce low-value Markdown whitespace for AI-oriented input packing.

Behavior:
  - preserve fenced code blocks and YAML front matter
  - collapse consecutive blank lines to one
  - remove HTML comments outside fenced code blocks
  - compact table padding around pipe separators
  - trim trailing whitespace while preserving Markdown hard breaks

Examples:
  ./scripts/pack-md.sh README.md > README.llm.md
  ./scripts/pack-md.sh -i README.md
EOF
}

pack_stream() {
  awk '
    function emit(line) {
      if (pending_blank && emitted_any) {
        print ""
      }
      print line
      emitted_any = 1
      pending_blank = 0
      last_line = line
    }

    function strip_comments(line,    out, start, stop) {
      out = ""

      while (1) {
        if (in_comment) {
          stop = index(line, "-->")
          if (stop == 0) {
            return out
          }
          line = substr(line, stop + 3)
          in_comment = 0
          continue
        }

        start = index(line, "<!--")
        if (start == 0) {
          return out line
        }

        out = out substr(line, 1, start - 1)
        line = substr(line, start + 4)
        stop = index(line, "-->")
        if (stop == 0) {
          in_comment = 1
          return out
        }
        line = substr(line, stop + 3)
      }
    }

    function trim_trailing(line) {
      if (line ~ /[^[:space:]][[:space:]][[:space:]]$/) {
        sub(/[[:space:]]+$/, "  ", line)
        return line
      }

      sub(/[[:space:]]+$/, "", line)
      return line
    }

    function compact_table(line) {
      sub(/^[[:space:]]+/, "", line)
      sub(/[[:space:]]+$/, "", line)
      gsub(/[[:space:]]*\|[[:space:]]*/, "|", line)
      return line
    }

    BEGIN {
      in_code = 0
      in_comment = 0
      in_front_matter = 0
      pending_front_matter = 0
      front_matter_open = ""
      front_matter_lines = 0
      pending_blank = 0
      emitted_any = 0
      last_line = ""
    }

    {
      raw = $0
      sub(/\r$/, "", raw)

      # Treat a leading --- as front matter only when the next line looks
      # like YAML metadata. This avoids swallowing a top-of-file horizontal rule.
      if (pending_front_matter) {
        if (raw ~ /^[[:space:]]*[A-Za-z0-9_.\[\]-]+:[[:space:]]*.*$/ || raw ~ /^(\-\-\-|\.\.\.)[[:space:]]*$/) {
          print front_matter_open
          print raw
          emitted_any = 1
          last_line = raw
          pending_front_matter = 0
          front_matter_open = ""

          if (raw !~ /^(\-\-\-|\.\.\.)[[:space:]]*$/) {
            in_front_matter = 1
            front_matter_lines = 2
          }
          next
        }

        emit(front_matter_open)
        pending_front_matter = 0
        front_matter_open = ""
      }

      if (in_front_matter) {
        print raw
        front_matter_lines++
        if (front_matter_lines > 1 && raw ~ /^(\-\-\-|\.\.\.)[[:space:]]*$/) {
          in_front_matter = 0
          emitted_any = 1
          last_line = raw
        }
        next
      }

      if (!emitted_any && raw ~ /^\-\-\-[[:space:]]*$/) {
        pending_front_matter = 1
        front_matter_open = raw
        next
      }

      if (in_code) {
        emit(raw)
        if (raw ~ /^[[:space:]]*```/ || raw ~ /^[[:space:]]*~~~/) {
          in_code = 0
        }
        next
      }

      if (raw ~ /^[[:space:]]*```/ || raw ~ /^[[:space:]]*~~~/) {
        emit(raw)
        in_code = 1
        next
      }

      line = strip_comments(raw)
      line = trim_trailing(line)

      if (line ~ /^[[:space:]]*$/) {
        if (emitted_any) {
          pending_blank = 1
        }
        next
      }

      if (line ~ /^[[:space:]]*\|.*\|[[:space:]]*$/) {
        line = compact_table(line)
      }

      emit(line)
    }
  '
}

in_place=false

while getopts ":ih" opt; do
  case "$opt" in
    i)
      in_place=true
      ;;
    h)
      usage
      exit 0
      ;;
    \?)
      usage >&2
      exit 1
      ;;
  esac
done
shift "$((OPTIND - 1))"

if "$in_place"; then
  if [[ "$#" -eq 0 ]]; then
    echo "pack-md.sh: -i requires at least one file" >&2
    exit 1
  fi

  for file in "$@"; do
    if [[ ! -f "$file" ]]; then
      echo "pack-md.sh: file not found: $file" >&2
      exit 1
    fi

    tmp_file="$(mktemp)"
    trap 'rm -f "$tmp_file"' EXIT
    pack_stream <"$file" >"$tmp_file"
    mv "$tmp_file" "$file"
    trap - EXIT
  done
  exit 0
fi

if [[ "$#" -gt 1 ]]; then
  usage >&2
  exit 1
fi

if [[ "$#" -eq 1 ]]; then
  if [[ ! -f "$1" ]]; then
    echo "pack-md.sh: file not found: $1" >&2
    exit 1
  fi
  pack_stream <"$1"
  exit 0
fi

pack_stream
