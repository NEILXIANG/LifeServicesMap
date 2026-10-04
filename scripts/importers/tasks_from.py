#!/usr/bin/env python3
"""Build a city's task cards from another city's cards plus local overrides.

    python3 scripts/importers/tasks_from.py --city kelowna --from kamloops
    python3 scripts/importers/tasks_from.py --city kelowna --from kamloops --export-missing out.json

The steps on most cards are province-wide (SIN, MSP, ICBC, tax, deposits…); what changes from
city to city is the office ("place"), the local organisations and phone numbers. Those live in
cities/<city>/import/task-overrides.json:

  {"places": {"<task id>": "<name prefix of a place in this city>" | null},
   "fields": {"<task id>": {"src": ..., "srcName": ...,
                            "<field>": {"en": ..., "zh": ..., "fr": ..., ...},   # replaces the field
                            "steps": [{...}, ...],                               # replaces all steps
                            "steps_replace": {"2": {...}}}}}                    # replaces one step

Every replaced text must exist in all six languages before the cards are written (the guide's
all-or-nothing rule). --export-missing writes what still needs translating, for a translator.
The source city's own local names must not survive: the build fails if any of
the source city's name, its places' names or its local phone numbers remain in the output.
"""
import argparse, copy, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: F401  (puts the project root on sys.path)
import kamdata

L6 = ['zh', 'en', 'fr', 'es', 'ko', 'ja']

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', required=True); ap.add_argument('--from', dest='src', required=True)
    ap.add_argument('--export-missing')
    a = ap.parse_args()
    kamdata.use(a.src); base = kamdata.load('TASKS'); src_places = kamdata.load('P')
    kamdata.use(a.city); places = kamdata.load('P')
    ov = json.load(open(os.path.join(kamdata.city_dir(a.city), 'import', 'task-overrides.json'), encoding='utf-8'))
    missing = {}
    # any English sentence that already exists in the source cards keeps its six-language text
    known = {}
    def collect(x):
        if isinstance(x, dict):
            if 'en' in x and all(x.get(l) for l in L6): known.setdefault(x['en'], x)
            for v in x.values(): collect(v)
        elif isinstance(x, list):
            for v in x: collect(v)
    collect(base)
    def need(path, v):
        if isinstance(v, dict) and v.get('en') in known:
            for l in L6: v.setdefault(l, known[v['en']][l])
        if isinstance(v, dict) and 'en' in v:
            gap = [l for l in L6 if not v.get(l)]
            if gap: missing[path] = {'en': v['en'], 'zh': v.get('zh', ''), 'need': gap}
    out = []
    for t in base:
        t = copy.deepcopy(t); tid = t['id']
        f = ov.get('fields', {}).get(tid, {})
        for k, v in f.items():
            if k == 'steps_replace':
                for i, step in v.items():
                    t['steps'][int(i)] = step; need('%s.steps.%s' % (tid, i), step)
            elif k == 'steps':
                t['steps'] = v
                for i, step in enumerate(v): need('%s.steps.%d' % (tid, i), step)
            else:
                t[k] = v; need('%s.%s' % (tid, k), v)
        pref = ov.get('places', {}).get(tid, 'KEEP')
        if pref is None:
            t.pop('place', None)
        elif pref != 'KEEP':
            m = [p for p in places if p['n'].startswith(pref)]
            if not m: sys.exit('task %s: no place starting with %r in %s' % (tid, pref, a.city))
            t['place'] = m[0]['id']
        elif t.get('place') and not any(p['id'] == t['place'] for p in places):
            sys.exit('task %s still points at %s place %s — map it in task-overrides.json "places"' % (tid, a.src, t['place']))
        out.append(t)
    if missing:
        if a.export_missing:
            json.dump(missing, open(a.export_missing, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print('%d texts need translating -> %s' % (len(missing), a.export_missing)); return
        sys.exit('%d texts are missing languages (run with --export-missing): %s' % (len(missing), ', '.join(list(missing)[:6])))
    # no local leftovers from the source city
    blob = json.dumps(out, ensure_ascii=False)
    src_name = kamdata.city_meta(a.src)['title'].split(' ')[0]
    local_names = {p['n'] for p in src_places if len(p['n']) > 12 and not any(q['n'] == p['n'] for q in places)}
    left = [n for n in local_names if n in blob]
    if src_name in blob: left.append(src_name)
    src_phones = set(re.findall(r'\b\d{3}-\d{3}-\d{4}\b', json.dumps(src_places))) - set(re.findall(r'\b\d{3}-\d{3}-\d{4}\b', json.dumps(places)))
    left += sorted(ph for ph in src_phones if ph in blob and not ph.startswith(('1-8', '800', '888', '877', '866', '855', '844', '833')))
    if left:
        sys.exit('source-city leftovers in the cards: %s' % left[:10])
    kamdata.save('TASKS', out)
    print('%s: %d task cards written (from %s + %d overridden cards)' % (a.city, len(out), a.src, len(ov.get('fields', {}))))

if __name__ == '__main__':
    main()
