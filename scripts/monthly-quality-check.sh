#!/usr/bin/env bash
# Monthly data-quality check — TIME-01 (stale-POI age) + TIME-02 (rotting deep
# links). Both feed the same single human-readable log, and both run on a 1st-of-
# the-month schedule, so one script keeps the cadence intact and the artefact
# names stable.
#
# What it does:
#   1. Reads the city data (cities/<city>/, via kamdata), scans every POI's `v` (YYYY-MM). Anything older
#      than 180 days lands in records/stale-POIs-YYYY-MM.md, grouped by age bucket.
#   2. Re-checks every link in the dataset (deep URLs are the ones that rot first
#      and dominate this output). Each run writes records/check-links-YYYY-MM-DD.log.
#   3. Appends a dated summary block to records/data-quality-log.md so the next
#      reviewer can scan one file instead of grepping two.
#
# Why a shell script and not cron-trigger on the Cloudflare Worker:
#   - It needs Python + filesystem access (the dataset lives here, not in the
#     worker); the schedule belongs on the host that owns the data.
#   - It is run by automation_update (monthly recurring) — see
#     ~/.workbuddy/config or the automation id stored in the project memory.
#
# Exit codes: 0 always (we surface status in the log, not in $?). A non-zero
# exit would page the user for nothing actionable when, say, the day's link
# check turned up fresh dead links.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
HERE="$(pwd)"   # 从项目根运行：bash scripts/monthly-quality-check.sh [城市，默认 kamloops]
CITY="${1:-kamloops}"
PY="python3"
# 日期按 Kamloops 当地算，不看跑这个脚本的机器在哪个时区
TODAY="$("$PY" -c 'import sys;sys.path.insert(0,".");import kamdata;print(kamdata.today())' 2>/dev/null || date +%Y-%m-%d)"
STAMP="${TODAY%-*}"
# 2026-10-04: every city has its own file names and log, so a run for one city never overwrites another's.
# Kamloops keeps the original names (records/data-quality-log.md, check-links-<date>.*).
if [[ "$CITY" == "kamloops" ]]; then SUF=""; QLOG="$HERE/records/data-quality-log.md"
else SUF="-$CITY"; QLOG="$HERE/records/data-quality-log-$CITY.md"; fi

echo "== monthly-quality-check @ $TODAY =="

# 1. Stale-POI report (TIME-01).
# stdout 和 stderr 分开：原来 2>&1 折在一起，export-open.py 一旦抛异常，
# traceback 的最后一行就被当成"本月过期数"原样写进了质量日志。
"$PY" "$HERE/scripts/export-open.py" --city "$CITY" --stale-threshold 180 >/tmp/stale_$$.out 2>/tmp/stale_$$.err
STALE_RC=$?
if [[ $STALE_RC -ne 0 ]]; then
  STALE_NOTE="脚本失败（rc=$STALE_RC）：$(tail -1 /tmp/stale_$$.err)"
else
  STALE_NOTE="$(grep '^stale report: ' /tmp/stale_$$.out | tail -1 | sed 's/^stale report: //')"
  STALE_NOTE="${STALE_NOTE:-未产出 stale 行（脚本返回 0 但没写报告）}"
fi
rm -f /tmp/stale_$$.out /tmp/stale_$$.err
echo "[TIME-01] $STALE_NOTE (rc=$STALE_RC)"

# 2. Deep-link health check (TIME-02).
# 计数从 --json 读，不再 grep 正文：正文格式一改（缩进、只打印异常）计数就
# 全变 0，而且是静默的——这个月度巡检曾经连续几个月报"0 OK / 0 DEAD"。
LINK_JSON="$HERE/records/check-links$SUF-$TODAY.json"
"$PY" "$HERE/scripts/check-links.py" --city "$CITY" --deep-only --json "$LINK_JSON" \
      >"$HERE/records/check-links$SUF-$TODAY.log" 2>&1
LINK_RC=$?
COUNTS="$("$PY" - "$LINK_JSON" <<'PYCOUNT'
import json, sys, collections
try:
    rows = json.load(open(sys.argv[1], encoding='utf-8'))
except Exception as e:
    print('ERR %s' % type(e).__name__); raise SystemExit
c = collections.Counter(r['status'] for r in rows)
print('%d %d %d %d %d' % (c['OK'], c['MOVED'], c['DEAD'], c['BLOCKED'], len(rows)))
PYCOUNT
)"
read -r OK MOVED DEAD BLOCKED TOTAL <<<"$COUNTS"
if [[ "${OK:-ERR}" == "ERR" || -z "${TOTAL:-}" ]]; then
  OK=0; MOVED=0; DEAD=0; BLOCKED=0; TOTAL=0
  LINK_NOTE="计数不可用（$LINK_JSON 没写出来或读不动）"
else
  LINK_NOTE="$OK OK, $MOVED MOVED, $DEAD DEAD, $BLOCKED BLOCKED（共 $TOTAL 条）"
fi
echo "[TIME-02] deep links: $LINK_NOTE (rc=$LINK_RC)"

# 3. Append a dated summary to the long-running quality log. We write before
#    the next step so the audit trail is preserved even if the script crashes
#    later (it doesn't, but defensive logging matches the rest of the project).
cat >>"$QLOG" <<EOF

### $TODAY · 月度巡检（$CITY）

- stale: $STALE_NOTE
- 深链: $LINK_NOTE
- 完整 log: records/check-links$SUF-$TODAY.log（计数取自同名 .json）
EOF

echo "== done =="
