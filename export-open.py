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
import argparse, csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OPEN_KINDS = {'official', 'own'}


def load_places(city):
    path = os.path.join(HERE, 'src', 'data-%s.js' % city)
    if not os.path.exists(path):
        sys.exit('missing %s' % path)
    s = open(path, encoding='utf-8').read()
    i = s.index('const P=[') + len('const P=')
    depth = 0
    for k in range(i, len(s)):
        if s[k] == '[':
            depth += 1
        elif s[k] == ']':
            depth -= 1
            if depth == 0:
                return json.loads(s[i:k + 1])
    sys.exit('could not find the end of P')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', default='kamloops')
    ap.add_argument('--csv', action='store_true', help='also write a CSV')
    ap.add_argument('--all', action='store_true',
                    help='export every record with its src, not just the open subset')
    a = ap.parse_args()

    places = load_places(a.city)
    counts = {}
    for p in places:
        counts[p.get('src', 'missing')] = counts.get(p.get('src', 'missing'), 0) + 1

    picked = places if a.all else [p for p in places if p.get('src') in OPEN_KINDS]

    stem = os.path.join(HERE, 'all-records' if a.all else 'open-subset')
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


if __name__ == '__main__':
    main()
