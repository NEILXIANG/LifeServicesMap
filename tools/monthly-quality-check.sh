#!/usr/bin/env bash
# Monthly data-quality check — TIME-01 (stale-POI age) + TIME-02 (rotting deep
# links). Both feed the same single human-readable log, and both run on a 1st-of-
# the-month schedule, so one script keeps the cadence intact and the artefact
# names stable.
#
# What it does:
#   1. Reads src/data-<city>.js, scans every POI's `v` (YYYY-MM). Anything older
#      than 180 days lands in data/stale-POIs-YYYY-MM.md, grouped by age bucket.
#   2. Re-checks every link in the dataset (deep URLs are the ones that rot first
#      and dominate this output). Each run writes data/check-links-YYYY-MM-DD.log.
#   3. Appends a dated summary block to data/data-quality-log.md so the next
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
HERE="$(pwd)"
PY="python3"
STAMP="$(date +%Y-%m)"
TODAY="$(date +%Y-%m-%d)"

echo "== monthly-quality-check @ $TODAY =="

# 1. Stale-POI report (TIME-01).
"$PY" "$HERE/export-open.py" --stale-threshold 180 >/tmp/stale_$$.out 2>&1
STALE_RC=$?
STALE_NOTE="$(tail -1 /tmp/stale_$$.out | sed 's/^stale report: //')"
rm -f /tmp/stale_$$.out
echo "[TIME-01] $STALE_NOTE (rc=$STALE_RC)"

# 2. Deep-link health check (TIME-02).
"$PY" "$HERE/check-links.py" --deep-only >"$HERE/data/check-links-$TODAY.log" 2>&1
LINK_RC=$?
# grep -c prints "0\n" when a file has no matches. The Python script emits
# one DEAD/MOVED/OK/BLOCKED line per URL, so we just need the count of each
# header prefix — tr strips the trailing newline so the printf stays single-line.
DEAD=$(  grep -c '^DEAD '    "$HERE/data/check-links-$TODAY.log" 2>/dev/null | tr -d '\n')
MOVED=$( grep -c '^MOVED '   "$HERE/data/check-links-$TODAY.log" 2>/dev/null | tr -d '\n')
OK=$(    grep -c '^OK '      "$HERE/data/check-links-$TODAY.log" 2>/dev/null | tr -d '\n')
BLOCKED=$(grep -c '^BLOCKED ' "$HERE/data/check-links-$TODAY.log" 2>/dev/null | tr -d '\n')
# Default empty values to 0 — the assignment above produces an empty string if
# the file is missing or grep fails; that's the only path that lands us here.
DEAD=${DEAD:-0}; MOVED=${MOVED:-0}; OK=${OK:-0}; BLOCKED=${BLOCKED:-0}
echo "[TIME-02] deep links: $OK OK, $MOVED MOVED, $DEAD DEAD, $BLOCKED BLOCKED (rc=$LINK_RC)"
echo "[TIME-02] deep links: $OK OK, $MOVED MOVED, $DEAD DEAD, $BLOCKED BLOCKED (rc=$LINK_RC)"

# 3. Append a dated summary to the long-running quality log. We write before
#    the next step so the audit trail is preserved even if the script crashes
#    later (it doesn't, but defensive logging matches the rest of the project).
cat >>"$HERE/data/data-quality-log.md" <<EOF

### $TODAY · 月度巡检

- stale: $STALE_NOTE
- 深链: $OK OK, $MOVED MOVED, $DEAD DEAD, $BLOCKED BLOCKED
- 完整 log: data/check-links-$TODAY.log
EOF

echo "== done =="
