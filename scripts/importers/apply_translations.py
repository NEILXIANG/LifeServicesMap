#!/usr/bin/env python3
"""Apply cities/<city>/import/translations.json to every place (imported or hand-written).

    python3 scripts/importers/apply_translations.py --city kelowna [--add file.out.json ...]

--add merges a translator's output ({id: {fr, es, ko, ja}}) into translations.json first, stamping
each entry with the English note it was made from (src_en), so a later change to the English
makes that translation stale instead of silently wrong. Prints what is still untranslated or stale.
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import LANG4, load_translations, apply_translation, translations_path
import kamdata

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--city', required=True); ap.add_argument('--add', nargs='*', default=[])
    a = ap.parse_args()
    kamdata.use(a.city)
    P = kamdata.load('P')
    byid = {p['id']: p for p in P}
    tr = load_translations(a.city)
    for f in a.add:
        for i, t in json.load(open(f, encoding='utf-8')).items():
            if i in byid and all(t.get(l) for l in LANG4):
                tr[i] = {'src_en': byid[i]['note']['en'], **{l: t[l].strip() for l in LANG4}}
    json.dump(tr, open(translations_path(a.city), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    done = stale = missing = 0
    for p in P:
        if 'note' not in p: continue
        if all(l in p['note'] for l in LANG4) and p['id'] not in tr: continue   # translated at the source (importer templates)
        if apply_translation(p, tr): done += 1
        else:
            for l in LANG4: p['note'].pop(l, None)                              # all-or-nothing
            if p['id'] in tr: stale += 1
            else: missing += 1
    kamdata.save('P', P)
    print('%s: %d translated from translations.json, %d stale (English changed), %d not yet translated'
          % (a.city, done, stale, missing))

if __name__ == '__main__':
    main()
