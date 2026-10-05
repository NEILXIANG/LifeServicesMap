#!/usr/bin/env bash
# check-all.sh — 构建 + 全部检查，一条命令。多城市改造期间每一步都用它对照基线。
#
#   ./scripts/check-all.sh            # 构建 + validate + 一致性检查 + 全部浏览器测试（含每座城市的 tests/city_guitest.py --city <城市>）
#   ./scripts/check-all.sh --quick    # 只构建 + validate（不需要 Playwright）
#
# 浏览器测试需要 Playwright。优先用项目内的 .venv（见 CLAUDE.md），没有就用系统 python3。
# 输出：每个测试一行 PASS/FAIL 汇总；任何一项失败，退出码非 0。
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY=python3
[[ -x "$ROOT/.venv/bin/python" ]] && PY="$ROOT/.venv/bin/python"
QUICK=0; [[ "${1:-}" == "--quick" ]] && QUICK=1
LOGDIR="$(mktemp -d -t check-all.XXXXXX)"
FAILED=()

run() {  # run <名字> <命令...>；每项带耗时（2026-10-04：先量出哪一项慢，再决定要不要并行或合并）
  local name="$1"; shift
  local t0=$SECONDS
  if "$@" >"$LOGDIR/$name.log" 2>&1; then
    printf '  PASS  %-22s %4ss\n' "$name" "$((SECONDS - t0))"
  else
    printf '  FAIL  %-22s %4ss   (日志：%s)\n' "$name" "$((SECONDS - t0))" "$LOGDIR/$name.log"
    FAILED+=("$name")
  fi
}

echo "▸ 构建"
python3 build.py --city kamloops >"$LOGDIR/build.log" 2>&1 || { cat "$LOGDIR/build.log"; exit 1; }
echo "  md5  $(md5 -q build/kamloops.html 2>/dev/null || md5sum build/kamloops.html | cut -d' ' -f1)"
echo "  $(grep -oE "DATA_VERSION='[^']+'" build/kamloops.html | head -1)"

echo "▸ 静态校验（每座城市 + 测试城市）"
run validate python3 scripts/validate.py build/kamloops.html
for c in $(python3 -c 'import kamdata;print(" ".join(c for c in kamdata.cities() if c!="kamloops"))') _fixture; do
  python3 build.py --city "$c" >"$LOGDIR/build-$c.log" 2>&1 || { cat "$LOGDIR/build-$c.log"; exit 1; }
  run "validate-$c" python3 scripts/validate.py --city "$c"
done
# 2026-10-04: the knowledge base — every lesson's claimed check/tool must still exist, and the pages are current
run knowledge python3 scripts/knowledge.py --check
# 2026-10-04: cross-language numbers, phones and other cities' names inside each city's notes. A city still
# being compiled (draft) must be clean; for a live city the report is listed but does not block.
for c in $(python3 -c 'import kamdata;print(" ".join(c for c in kamdata.cities() if not c.startswith("_")))'); do
  if python3 -c "import kamdata,sys;sys.exit(0 if kamdata.city_meta('$c').get('status')=='draft' else 1)"; then
    run "consistency-$c" python3 scripts/consistency_check.py --city "$c" --strict
  else
    python3 scripts/consistency_check.py --city "$c" >"$LOGDIR/consistency-$c.log" 2>&1
    printf '  INFO  consistency-%s   %s\n' "$c" "$(head -1 "$LOGDIR/consistency-$c.log")"
  fi
done

if [[ $QUICK -eq 0 ]]; then
  if ! "$PY" -c 'import playwright' 2>/dev/null; then
    echo "✗ 没有 Playwright，跑不了浏览器测试（见 CLAUDE.md 的安装步骤，或加 --quick）"; exit 1
  fi
  echo "▸ 浏览器测试（$PY）"
  run engine-fixture "$PY" tests/engine/test_fixture_city.py
  run engine-empty "$PY" tests/engine/test_empty_city.py
  run engine-bc-time "$PY" tests/engine/test_bc_permanent_dst.py
  run engine-popup "$PY" tests/engine/test_popup_lifecycle.py
  run engine-back "$PY" tests/engine/test_back_navigation.py
  run regress "$PY" tests/kamloops/regress.py build/kamloops.html
  # every city's strict GUI run, one test file for all of them (2026-10-05)
  for c in $(python3 -c "import kamdata;print(' '.join(kamdata.cities()))"); do
    run "gui-$c" "$PY" tests/city_guitest.py --city "$c"
  done
  for t in tests/kamloops/phase*test.py tests/kamloops/audit*.py tests/kamloops/soci2.py tests/kamloops/tasktest.py; do
    [[ -f "$t" ]] || continue
    run "$(basename "$t" .py)" "$PY" "$t"
  done
fi

echo
if [[ ${#FAILED[@]} -eq 0 ]]; then
  echo "✓ 全部通过"
else
  echo "✗ ${#FAILED[@]} 项失败：${FAILED[*]}"
  exit 1
fi
