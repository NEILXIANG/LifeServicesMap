#!/usr/bin/env python3
"""Apply independent desk-check results (docs/knowledge/prompts/官网独立复核.md) to a city's data.

    python3 scripts/apply_verification.py --city kamloops out1.json out2.json …            # report only
    python3 scripts/apply_verification.py --city kamloops out*.json --apply --review review.md

What is applied automatically (each change is listed in import/verification.json under "fixed"):
- phone: the official number when the checker marked it wrong (normalised to 250-555-0100 / 1-800-555-0100);
- address: the official street address when marked wrong — never for a record that has no address on file
  (a shelter's address is kept private on purpose);
- hours: the official wording is stored in import/hours.json; it replaces the structured hours when it was marked
  wrong or missing and the parser understands it fully (otherwise it goes to the review list);
- src: a record from a third-party listing (src "places") confirmed on the organisation's own page becomes
  "official" (with that page as its website if it had none); v = this month for every record checked.
What goes to the review list instead (a person decides, all six languages change together): a different name,
"closed", claims in the note that the official page contradicts, hours the parser does not understand.

Why (2026-10-04): Kelowna's 243-record desk check was applied by hand in a one-off script; Kamloops' 307 records
needed the same. Same input format, same rules, so the next city gets it for free (lesson L-118).
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'importers'))
import kamdata
from hours import parse_hours

NOT_OFFICIAL = ('google.', 'facebook.', 'yelp.', 'yellowpages', 'canada411', 'instagram.', 'tripadvisor', 'mapquest', 'bing.')

def phone(s):
    d = re.sub(r'\D', '', s or '')
    if len(d) == 11 and d[0] == '1': return '1-%s-%s-%s' % (d[1:4], d[4:7], d[7:])
    if len(d) == 10: return '%s-%s-%s' % (d[:3], d[3:6], d[6:])
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', required=True); ap.add_argument('files', nargs='+')
    ap.add_argument('--apply', action='store_true'); ap.add_argument('--review', help='write the review list (markdown) here')
    a = ap.parse_args()
    kamdata.use(a.city)
    P = kamdata.load('P'); byid = {p['id']: p for p in P}
    ver = kamdata.load_import('verification.json', {}) or {}
    hours = kamdata.load_import('hours.json', {}) or {}
    today, month = kamdata.today().isoformat(), kamdata.month()
    results = []
    for f in a.files:
        results += [r for r in json.load(open(f, encoding='utf-8')) if isinstance(r, dict) and r.get('id')]
    stats = {'confirmed': 0, 'corrected': 0, 'unresolved': 0, 'closed': 0}
    review, changed = [], 0
    for r in results:
        p = byid.get(r['id'])
        if not p:
            review.append((r['id'], '?', 'not in places.json')); continue
        st = r.get('status', 'unresolved'); stats[st] = stats.get(st, 0) + 1
        fixed = []
        def field(k): return r.get(k) or {}
        ph = field('phone')
        if ph.get('ok') is False and phone(ph.get('official')):
            new = phone(ph['official'])
            if new != p.get('p'): fixed.append('phone %s → %s' % (p.get('p'), new)); p['p'] = new
        ad = field('address')
        if ad.get('ok') is False and ad.get('official') and p.get('a'):
            fixed.append('address %s → %s' % (p['a'], ad['official'])); p['a'] = ad['official']
        hr = field('hours')
        if hr.get('official_text'):
            hours[p['id']] = {'hours_text': hr['official_text'], 'source_url': (r.get('checked_urls') or [None])[0], 'fetched': today}
            if hr.get('ok') is False or not p.get('h'):
                h = parse_hours(hr['official_text'])
                if h and h != p.get('h'):
                    fixed.append('hours replaced from official text' if p.get('h') else 'hours added'); p['h'] = h
                elif not h:
                    review.append((p['id'], p['n'], 'hours not understood: %s' % hr['official_text'][:160]))
        nm = field('name')
        if nm.get('ok') is False and nm.get('official'):
            review.append((p['id'], p['n'], 'name differs — official: %s' % nm['official']))
        if st == 'closed':
            review.append((p['id'], p['n'], 'CLOSED? %s' % (r.get('remarks') or '')))
        for issue in (field('note_claims').get('issues') or []):
            review.append((p['id'], p['n'], 'note: %s' % issue))
        if st in ('confirmed', 'corrected'):
            if p.get('src') == 'places':
                # the place's own page only: not a PDF, a news story or another organisation's page that mentions it
                urls = [u for u in (r.get('checked_urls') or []) if not any(x in u for x in NOT_OFFICIAL)
                        and not re.search(r'\.pdf($|\?)|/news|/stories|city-stories|/fares|bc\.211|/portfolio', u, re.I)]
                if p.get('w') or urls:
                    if not p.get('w'): p['w'] = urls[0]; fixed.append('website %s' % urls[0])
                    p['src'] = 'official'; fixed.append('src places → official')
            p['v'] = month
        if st == 'unresolved':
            review.append((p['id'], p['n'], 'unresolved: %s' % (r.get('remarks') or '')))
        changed += bool(fixed)
        prev = ver.get(p['id']) if isinstance(ver.get(p['id']), dict) else None
        ver[p['id']] = {'checked': today, 'method': 'desk', 'result': st, 'urls': r.get('checked_urls') or [],
                        'remarks': r.get('remarks') or '', 'fixed': fixed}
        if prev and prev.get('checked') != today:
            ver[p['id']]['previous'] = {k: prev[k] for k in ('checked', 'result', 'fixed') if k in prev}
    print('%s: %d results %s; %d records changed; %d items for review' % (a.city, len(results), stats, changed, len(review)))
    if a.review:
        with open(a.review, 'w', encoding='utf-8') as out:
            out.write('# %s desk check — items for a person (%s)\n\n| id | place | what |\n|---|---|---|\n' % (a.city, today))
            for i, n, w in review: out.write('| %s | %s | %s |\n' % (i, n.replace('|', '/'), w.replace('|', '/').replace('\n', ' ')))
        print('review list →', a.review)
    if a.apply:
        os.makedirs(os.path.dirname(kamdata.import_path('x')), exist_ok=True)
        kamdata.save('P', P)
        for name, data in (('verification.json', ver), ('hours.json', hours)):
            with open(kamdata.import_path(name), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True); f.write('\n')
        print('applied to cities/%s/' % a.city)

if __name__ == '__main__':
    main()
