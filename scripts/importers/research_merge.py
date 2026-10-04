#!/usr/bin/env python3
"""Merge researched records (from official websites) into a city's places.

    python3 scripts/importers/research_merge.py --city kelowna cities/kelowna/import/research/R2-*.json

Input: {"places": [...]} with the research schema used for Kelowna (2026-10-03):
  n, c, g, a, locality, p, w, hours_text, who, languages, cost, appointment, bring,
  note_en, note_zh, alias, source_url, verify_notes
Each file is one source key in provenance (its file name), so re-running a file replaces its
records and nothing else.

Rules (methodology §5):
- Tier 2 (the organisation's own site) → src:'official' when `w` is present, else 'stub-pending-verify'.
- Coordinates from the BC geocoder only (score >= 95, civic level); a record that cannot be
  placed is NOT put on the map — it is listed for review instead.
- Hours: parse_hours() converts only fully understood text; the official wording is kept in
  provenance either way, so a person can finish the rest.
- Themes are inferred conservatively: 'free' only when the official cost says free; 'multi'
  only when a non-English language is stated; category defaults otherwise.
- A confidential address is never published: records whose `a` is empty or says
  "confidential" are skipped (their phone belongs in CITY.localLines).
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CityImport
from hours import parse_hours
import kamdata

CAT_THEMES = {'gov': ['life'], 'post': ['life'], 'bank': ['life'], 'pharmacy': ['life'], 'grocery': ['life'],
              'asian': ['life', 'multi'], 'library': ['family', 'free', 'indoor'], 'museum': ['history', 'culture', 'indoor'],
              'heritage': ['history'], 'indigenous': ['culture'], 'religious': ['multi'], 'pool': ['family', 'indoor'],
              'rink': ['family', 'indoor'], 'gym': ['indoor'], 'commctr': ['family'], 'secondhand': ['free'],
              'foodbank': ['free'], 'legal': ['free'], 'support': ['free']}
TORDER = ["life", "family", "fun", "scenic", "history", "culture", "free", "multi", "student", "indoor"]
NON_EN = re.compile(r'punjabi|mandarin|cantonese|chinese|tagalog|filipino|spanish|korean|arabic|french|hindi|urdu|'
                    r'farsi|persian|ukrainian|russian|german|japanese|vietnamese|interpret', re.I)

def phone(p):
    d = re.sub(r'\D', '', p or '')
    if len(d) == 11 and d[0] == '1': d = d[1:]
    return '%s-%s-%s' % (d[:3], d[3:6], d[6:]) if len(d) == 10 else None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--city', required=True); ap.add_argument('files', nargs='+')
    a = ap.parse_args()
    CI = kamdata.load('CI', engine=True)
    review = []
    for f in a.files:
        src = 'research:' + os.path.basename(f)
        imp = CityImport(a.city, src)
        # researched records are distinct services by construction: a class held in a library or a
        # clinic inside a health centre is its own record (linked as same building), so only the
        # "one name contains the other" rule counts as a duplicate here
        imp.word_radius = 0
        imp.phone_dedupe = False
        cfg = json.load(open(os.path.join(imp.dir, 'import', 'config.json'), encoding='utf-8'))
        wk = {k.lower(): v for k, v in cfg.get('bc_childcare', {}).get('localities', {}).items() if v}
        for r in json.load(open(f, encoding='utf-8'))['places']:
            name, addr = (r.get('n') or '').strip(), (r.get('a') or '').strip()
            if not addr or re.search(r'confidential|private|not published', addr, re.I):
                review.append((name, 'no public address (keep phone only)')); continue
            if r.get('c') not in CI:
                review.append((name, 'unknown category %r' % r.get('c'))); continue
            loc = (r.get('locality') or ('West Kelowna' if r.get('g') == 'wk' else 'Kelowna')).strip()
            lat, lng, approx = imp.locate(addr, loc)
            if lat is None or approx:
                review.append((name, 'address not placed by the BC geocoder: ' + addr)); continue
            note = {'zh': (r.get('note_zh') or '').strip(), 'en': (r.get('note_en') or '').strip()}
            if not note['zh'] or not note['en']:
                review.append((name, 'note missing in zh or en')); continue
            t = list(CAT_THEMES.get(r['c'], []))
            if re.search(r'\bfree\b|no cost|no charge', r.get('cost') or '', re.I) and 'free' not in t: t.append('free')
            if NON_EN.search(r.get('languages') or '') and 'multi' not in t: t.append('multi')
            if re.search(r'student', r.get('who') or '', re.I) and 'student' not in t: t.append('student')
            rec = {'n': name, 'c': r['c'], 'lat': lat, 'lng': lng, 'a': re.sub(r',?\s*(West )?Kelowna.*$', '', addr),
                   'note': note, 'v': kamdata.MONTH if hasattr(kamdata, 'MONTH') else None}
            rec.pop('v')
            ph = phone(r.get('p'))
            if ph: rec['p'] = ph
            h = parse_hours(r.get('hours_text'))
            if h: rec['h'] = h
            if t: rec['t'] = sorted(set(t), key=TORDER.index)
            if r.get('alias'): rec['alias'] = [x for x in r['alias'] if isinstance(x, str)][:12]
            if r.get('w', '').startswith('http'):
                rec['w'] = r['w']; rec['src'] = 'official'
            else:
                rec['src'] = 'stub-pending-verify'
            # a programme of the organisation already on the map at this address (same phone, same
            # building: "English Corner" in a library) is folded into that record — its note says
            # "also here", its name becomes a search word — instead of a second pin on the same spot
            imp.phone_dedupe = True
            host = imp.duplicate_of(name, rec['c'], lat, lng, rec.get('p'))
            imp.phone_dedupe = False
            SAFETY = {'hospital', 'pharmacy', 'dental', 'support', 'foodbank', 'legal', 'police'}
            if host and (rec['c'] in SAFETY or host['c'] in SAFETY):
                host = None      # safety-critical services always keep their own pin (a shelter is never a footnote)
            if host and host['c'] not in ('library', 'school'):
                host = None      # only a library or a campus hosts programmes; anything else keeps its own record
            if host and host.get('p') == rec.get('p') and not re.sub(r'[^a-z]', '', host['n'].lower()) in re.sub(r'[^a-z]', '', name.lower()):
                first = lambda s, sep: (re.split(sep, s)[0] + ('.' if sep == r'(?<=\.)\s' else '。')).replace('..', '.').replace('。。', '。')
                prog = re.sub(r'\s*\(.*?\)', '', name).strip()
                if prog not in host['note']['en']:
                    host['note']['en'] += ' Also here — %s: %s' % (prog, first(note['en'], r'(?<=\.)\s'))
                    host['note']['zh'] += '此处还有：%s——%s' % (prog, first(note['zh'], r'(?<=。)'))
                    for l in ('fr', 'es', 'ko', 'ja'):
                        host['note'].pop(l, None)    # keep all-or-nothing: the other four are re-translated later
                    host.setdefault('alias', [])
                    if prog not in host['alias']: host['alias'].append(prog)
                review.append((name, 'folded into "%s"' % host['n']))
                continue
            got = imp.add(rec, name, loc if loc.lower() in wk else None)
            if got:
                imp.prov[got['id']].update({'hours_text': r.get('hours_text'), 'who': r.get('who'),
                                            'languages': r.get('languages'), 'cost': r.get('cost'),
                                            'appointment': r.get('appointment'), 'bring': r.get('bring'),
                                            'source_url': r.get('source_url'), 'verify_notes': r.get('verify_notes')})
        imp.save()
    if review:
        print('\nnot placed — for the review list:')
        for n, why in review: print('   %-50s %s' % (n[:50], why))

if __name__ == '__main__':
    main()
