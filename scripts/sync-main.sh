#!/usr/bin/env bash
# sync-main.sh — bring main up to date with multi-city, leaving out what main does not carry.
#
#   ./scripts/sync-main.sh            # on a clean tree: checkout main, merge multi-city, drop the excluded paths, commit
#   ./scripts/sync-main.sh <branch>   # merge another branch instead of multi-city
#
# Decision D7 (2026-10-19, Neil): "main 只要 Kamloops". main is what is live, so it carries the engine, the tools
# and Kamloops — not draft cities. The paths it leaves out are listed in scripts/main-excludes.txt; a later sync
# that touches them hits a modify/delete conflict, which this script resolves by removing them again.
# It only commits locally: pushing main and deploying stay Neil's decision, each time (lesson L-117).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
SRC="${1:-multi-city}"
fail() { printf '✗ %s\n' "$*" >&2; exit 1; }

[[ -z "$(git status --porcelain --untracked-files=no)" ]] || fail "uncommitted changes — commit or stash first"
EXCL=()
while IFS= read -r line; do
  line="${line%%#*}"; line="$(printf '%s' "$line" | sed 's/[[:space:]]*$//')"
  [[ -n "$line" ]] && EXCL+=("$line")
done < scripts/main-excludes.txt
[[ ${#EXCL[@]} -gt 0 ]] || fail "scripts/main-excludes.txt lists nothing"

git checkout -q main
git merge --no-ff --no-commit "$SRC" >/dev/null 2>&1 || true
for p in "${EXCL[@]}"; do git rm -rq --ignore-unmatch -- "$p"; done
LEFT="$(git diff --name-only --diff-filter=U)"
[[ -z "$LEFT" ]] || fail "conflicts outside the excluded paths — resolve by hand:
$LEFT"
if git diff --cached --quiet && ! git rev-parse -q --verify MERGE_HEAD >/dev/null; then echo "main already has $SRC"; exit 0; fi
git commit -q -m "合并 $SRC 到 main（只含 Kamloops：去掉 $(IFS=', '; echo "${EXCL[*]}")）"
for p in "${EXCL[@]}"; do
  if [[ -e "$p" ]]; then echo "⚠ $p still on disk (untracked files) — delete it before building, or check-all will see it"; fi
done
echo "✓ main = $SRC minus the excluded paths ($(git rev-parse --short HEAD)). Next: ./scripts/check-all.sh — then push/deploy only with Neil's yes."
