#!/usr/bin/env bash
set -u

fail() {
  echo "open-file: $1" >&2
  exit 1
}

[ "$#" -eq 1 ] || fail "対象パスを1つ指定してください"
target=$1
[ -n "$target" ] || fail "対象パスが空です"

command -v uname >/dev/null 2>&1 || fail "必要なcommandがありません: uname"
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) path_tool=cygpath ;;
  *)
    command -v grep >/dev/null 2>&1 || fail "必要なcommandがありません: grep"
    grep -qi microsoft /proc/version 2>/dev/null \
      && path_tool=wslpath \
      || fail "未対応の環境です（WSL / Git Bashのみ）"
    ;;
esac

command -v "$path_tool" >/dev/null 2>&1 \
  || fail "必要なcommandがありません: $path_tool"
command -v explorer.exe >/dev/null 2>&1 \
  || fail "必要なcommandがありません: explorer.exe"

case "$target" in
  [A-Za-z]:[\\/]* | *\\*)
    normalized=$("$path_tool" -u -- "$target") \
      || fail "path変換に失敗しました"
    [ -n "$normalized" ] || fail "path変換に失敗しました"
    target=$normalized
    ;;
esac

[ -e "$target" ] || fail "対象が見つかりません"
winpath=$("$path_tool" -w -- "$target") \
  || fail "path変換に失敗しました"
[ -n "$winpath" ] || fail "path変換に失敗しました"

if [ -d "$target" ]; then
  explorer.exe "$winpath" || true
elif [[ "${target,,}" == *.html || "${target,,}" == *.htm ]]; then
  explorer.exe "$winpath" || true
else
  MSYS2_ARG_CONV_EXCL='*' explorer.exe "/select,$winpath" || true
fi

echo "open-file: Windows側へ起動要求を送信しました"
