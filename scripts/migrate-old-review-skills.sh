#!/usr/bin/env bash
#
# Cleanup old review sub-skill directories that were consolidated into
# `~/.claude/skills/review/` by the km:review redesign (issue #42).
#
# `install.sh` only copies templates → ~/.claude/ and ~/.agents/ without
# deleting old files. Run this script once after pulling the new templates.

set -euo pipefail

TARGETS=(
  "$HOME/.claude/skills/code-review"
  "$HOME/.claude/skills/doc-review"
  "$HOME/.claude/skills/intent-review"
  "$HOME/.claude/skills/quality-review"
  "$HOME/.agents/skills/code-review"
  "$HOME/.agents/skills/doc-review"
  "$HOME/.agents/skills/intent-review"
  "$HOME/.agents/skills/quality-review"
)

echo "km:review redesign migration"
echo "============================="
echo ""
echo "This will remove the following deprecated sub-skill directories:"
echo ""

found=0
for target in "${TARGETS[@]}"; do
  if [[ -e "$target" ]]; then
    echo "  - $target"
    found=1
  fi
done

if [[ "$found" -eq 0 ]]; then
  echo "  (nothing to remove — already clean)"
  echo ""
  echo "Done."
  exit 0
fi

echo ""
read -r -p "Proceed with deletion? [y/N] " reply
case "$reply" in
  y | Y | yes | YES)
    ;;
  *)
    echo "Aborted."
    exit 1
    ;;
esac

for target in "${TARGETS[@]}"; do
  if [[ -e "$target" ]]; then
    rm -rf -- "$target"
    echo "Removed: $target"
  fi
done

echo ""
echo "Done. New consolidated skill is at:"
echo "  ~/.claude/skills/review/"
echo ""
echo "If you have any references to /km:code-review or /km:doc-review etc. in scripts,"
echo "update them to /km:review."
