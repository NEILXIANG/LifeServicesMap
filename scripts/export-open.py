#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export the part of the dataset that is unambiguously yours to license.

    python3 export-open.py                 # -> open-subset.json  (+ a summary)
    python3 export-open.py --csv           # also write open-subset.csv
    python3 export-open.py --all           # every record, with its src, for review

Why this exists
---------------
Three kinds of material sit in one file:

  * what you wrote — the notes, the 44-category taxonomy, the curation of 250 from
    thousands, the guide. Yours outright.
  * facts you can point at an authoritative source for (src='official') or checked
    yourself (src='own'). Re-derivable from that source; safe to pass on.
  * facts resting on third-party map data (src='places'). Redistribution of those
    is governed by the platform's terms, not by your licence.

Nothing about the map changes when you run this. It just lets you answer, at any
moment, "which part of this can I hand to a library / a newcomer centre / another
city with a clear conscience?" — without going back through 250 records by hand.

The export always carries your notes, because those are yours regardless of where
the address came from.
"""
import argparse, csv, datetime as dt, json, re
import os, sys
_r = os.path.dirname(os.path.abspath(__file__))
for _ in range(6):
    if os.path.exists(os.path.join(_r, 'kamdata.py')): break
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
import kamdata

HERE = kamdata.ROOT
OPEN_KINDS = {'official', 'own'}


def load_places(city):
    kamdata.use(city)            # 2026-10-03: any city under cities/
    return kamdata.load('P')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', default=kamdata.CITY)
    ap.add_argument('--csv', action='store_true', help='also write a CSV')
    ap.add_argument('--all', action='store_true',
                    help='export every record with its src, not just the open subset')
    ap.add_argument('--stale-threshold', type=int, default=0,
                    help='emit a stale-records report for any POI whose v (YYYY-MM)'
                         ' is older than N days; 0 disables (default: 0).')
    a = ap.parse_args()

    places = load_places(a.city)
    counts = {}
    for p in places:
        counts[p.get('src', 'missing')] = counts.get(p.get('src', 'missing'), 0) + 1

    picked = places if a.all else [p for p in places if p.get('src') in OPEN_KINDS]

    stem = os.path.join(HERE, 'build', ('all-records' if a.all else 'open-subset')
                        + ('' if a.city == 'kamloops' else '-' + a.city))
    os.makedirs(os.path.dirname(stem), exist_ok=True)   # build/ 被 gitignore，全新 clone 上没有
    with open(stem + '.json', 'w', encoding='utf-8') as f:
        json.dump({'city': a.city,
                   'licence': 'CC BY-NC 4.0',
                   'attribution': 'Neil Xiang',
                   'basis': 'src in %s' % sorted(OPEN_KINDS) if not a.all else 'all records',
                   'count': len(picked),
                   'places': picked}, f, ensure_ascii=False, indent=1)

    if a.csv:
        cols = ['id', 'n', 'a', 'lat', 'lng', 'c', 'g', 'p', 'w', 'src', 'v']
        with open(stem + '.csv', 'w', encoding='utf-8-sig', newline='') as f:
            wr = csv.writer(f)
            wr.writerow(cols + ['note_zh', 'note_en'])
            for p in picked:
                nt = p.get('note') or {}
                wr.writerow([p.get(c, '') for c in cols] + [nt.get('zh', ''), nt.get('en', '')])

    print('records by source:')
    for k in sorted(counts):
        print('  %-9s %d' % (k, counts[k]))
    print('\nwrote %s.json — %d records%s'
          % (os.path.basename(stem), len(picked), ' (+ .csv)' if a.csv else ''))
    if not a.all:
        held = len(places) - len(picked)
        print('held back: %d records whose facts rest on third-party map data.' % held)
        print('To move one across, verify it against the operator and set src to')
        print("'official' (with its website) or 'own'.")

    # Stale-POI report — TIME-01 in the diagnostic. Every place stores a 'v'
    # (YYYY-MM) marking when its facts were last verified; nothing currently scans
    # the file for places whose 'v' has aged past the freshness bar. A monthly
    # run with --stale-threshold 180 writes a markdown table grouped by age
    # bucket and source, which is exactly what a human reviewer needs to
    # triage the next refresh pass. We deliberately do NOT auto-edit the data
    # file — that would hide what changed and bypass the verification step.
    if a.stale_threshold > 0:
        today = kamdata.today()   # 按 Kamloops 当地日期，不按构建机器时区
        MID = '%dd\u20131y' % a.stale_threshold      # 桶名跟着阈值走，不再写死 180
        bucketed = {'>1y': [], MID: [], '90\u2013180d': [], '<90d': []}
        malformed = []                                # v 字段不合规——是格式问题，不是过期
        for p in places:
            v = p.get('v', '')
            if not kamdata.V_RE.match(v or ''):
                malformed.append(p)
                continue
            y, m = (int(x) for x in v.split('-'))
            last = dt.date(y, m, 1)
            age = (today - last).days
            age_str = '%dd' % age
            if age > 365:
                bucketed['>1y'].append((p, age, age_str))
            elif age > a.stale_threshold:
                bucketed[MID].append((p, age, age_str))
            elif age > 90:
                bucketed['90\u2013180d'].append((p, age, age_str))
            else:
                bucketed['<90d'].append((p, age, age_str))
        out_dir = os.path.join(HERE, 'data')
        os.makedirs(out_dir, exist_ok=True)
        out_name = 'stale-POIs-%s%s.md' % ('' if a.city == 'kamloops' else a.city + '-',
                                           today.strftime('%Y-%m'))
        out_path = os.path.join(out_dir, out_name)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('# Stale-POI report (%s)\n\n' % today.isoformat())
            f.write('Generated by `export-open.py --stale-threshold %d`.\n\n'
                    % a.stale_threshold)
            f.write('A POI is **stale** when its `v` (YYYY-MM) is more than %d days'
                    ' old. The dataset has no CI hook for this \u2014 we rely on this\n' % a.stale_threshold)
            f.write('monthly report to keep the verification churn visible to the'
                    ' next reviewer.\n\n')
            total_stale = len(bucketed['>1y']) + len(bucketed[MID])
            f.write('**%d stale** (>%dd): %d in %s, %d over a year.'
                    % (total_stale, a.stale_threshold,
                       len(bucketed[MID]), MID, len(bucketed['>1y'])))
            if malformed:
                f.write('\n\n> **%d record(s) have a `v` that is not `YYYY-MM`** — a schema'
                        ' problem, not a stale one; they are excluded from the buckets'
                        ' below: %s'
                        % (len(malformed),
                           ', '.join('%s (`%s`)' % (p['n'], p.get('v')) for p in malformed)))
            f.write('\n\n## Freshness distribution\n\n')
            f.write('| Bucket | Count |\n|---|---|\n')
            for b in ('<90d', '90\u2013180d', MID, '>1y'):
                f.write('| %s | %d |\n' % (b, len(bucketed[b])))
            for b in (MID, '>1y'):
                rows = bucketed[b]
                if not rows:
                    continue
                f.write('\n## %s\n\n' % b)
                f.write('| id | name | cat | region | src | v | age | action |\n')
                f.write('|---|---|---|---|---|---|---|---|\n')
                rows.sort(key=lambda r: (r[1] is None, -(r[1] or 0)))
                for p, age, age_str in rows:
                    act = {'official': 're-fetch w',
                           'own': 'phone-verify / visit',
                           'places': 'cross-check OSM'}.get(
                        p.get('src', ''), 'review src')
                    f.write('| %s | %s | %s | %s | %s | %s | %s | %s |\n'
                            % (p.get('id', '?'),
                               (p.get('n', '') or '').replace('|', '\\|'),
                               p.get('c', ''), p.get('g', ''),
                               p.get('src', ''), p.get('v', ''),
                               age_str, act))
        if total_stale > 0:
            print('\nstale report: %d POI over %dd \u2014 see %s'
                  % (total_stale, a.stale_threshold, out_name))
        else:
            print('\nstale report: 0 POI over %dd. nothing to do this cycle.'
                  % a.stale_threshold)


if __name__ == '__main__':
    main()
