#!/usr/bin/env python3
"""Store official opening hours and apply them to every place (imported or hand-written).

    python3 scripts/importers/apply_hours.py --city kelowna [--add hours-out.json ...]

--add merges a researcher's output ({id: {hours_text, services_text, source_url, notes}}) into
cities/<city>/import/hours.json with today's date. Then every place without structured hours gets
them when the stored wording is fully understood (scripts/importers/hours.py); the rest are listed
so a person can finish them. Worship times become the engine's service-times list (h.s).
"""
import argparse, datetime, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_hours, apply_hours, hours_path
import kamdata

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--city', required=True); ap.add_argument('--add', nargs='*', default=[])
    a = ap.parse_args()
    kamdata.use(a.city)
    P = kamdata.load('P'); ids = {p['id'] for p in P}
    H = load_hours(a.city)
    for f in a.add:
        for i, e in json.load(open(f, encoding='utf-8')).items():
            if i in ids and (e.get('hours_text') or e.get('services_text')):
                H[i] = {k: e.get(k) for k in ('hours_text', 'services_text', 'source_url', 'notes')}
                H[i]['fetched'] = datetime.date.today().isoformat()
    json.dump(H, open(hours_path(a.city), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    done = 0; left = []
    for p in P:
        if apply_hours(p, H): done += 1
        elif p['id'] in H and not p.get('h'): left.append((p['n'], H[p['id']].get('hours_text') or H[p['id']].get('services_text')))
    kamdata.save('P', P)
    print('%s: %d places got hours from hours.json; %d stored wordings not understood (left for a person):' % (a.city, done, len(left)))
    for n, t in left[:60]: print('   %-40s %s' % (n[:40], (t or '')[:90]))

if __name__ == '__main__':
    main()
