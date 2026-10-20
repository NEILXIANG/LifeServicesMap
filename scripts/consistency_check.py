#!/usr/bin/env python3
"""Cross-checks inside a city's data that no single field rule can see.

    python3 scripts/consistency_check.py --city kelowna [--strict]

Why (2026-10-04): while translating Kelowna's notes, three facts turned out to differ between the
Chinese and English versions of the same note (a pharmacy's Sunday hours, a Mass time, an age limit).
Translation caught them by chance. These checks make that systematic:

1. Numbers across languages — every number in the English note must appear in each other language
   (allowing 12/24-hour forms: "5:30 p.m." = "17:30"), and the other way round. A missing or extra
   number usually means one version was edited and the others were not.
2. Phone numbers — a number written in a note must match across languages; one that differs from the
   record's own phone is listed (often legitimate: a second line), so a person can look.
3. "24 hours" in a note but hours on file that are not 24 hours (or the reverse).
4. Other cities' names in this city's addresses and notes (a copied record or a leaked sentence).
5. Area codes outside the province's (BC: 250/778/236/604/672 and toll-free) — a typo or a wrong record.

Exit status 1 with --strict when a numbers, phone, 24h or other-city finding remains (phone-note and
area-code are listed for a person to look at but do not fail); otherwise the report is informational.
"""
import argparse, os, re, sys
_r = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_r))
import kamdata

LANGS = kamdata.LANGS
# BC area codes + toll-free. A city outside BC sets its own in city.json "validate": {"areaCodes": [...]}
AREA_BC = {'250', '778', '236', '604', '672'}
TOLL_FREE = {'800', '833', '844', '855', '866', '877', '888'}
PHONE = re.compile(r'(?<!\d)(?:1[-. ]?)?\(?(\d{3})\)?[-. ]?(\d{3})[-. ](\d{4})(?!\d)')

WORDS = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
         'eleven': 11, 'twelve': 12, 'noon': 12, 'midnight': 24, 'january': 1, 'february': 2, 'march': 3, 'april': 4,
         'may': 5, 'june': 6, 'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
         'week': 7, 'weekly': 7, 'daily': 7}
CJK = {'一': 1, '两': 2, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
SMALL = {1, 2, 3, 13, 14, 15}   # "one hour", "2nd floor", "三家" — too often written as words to compare

def numbers(text, words=False):
    """Numbers a reader would compare, normalised so 12- and 24-hour forms meet. With words=True,
    number words ("five", "五") count too — used only for matching, so a word can never create a finding."""
    t = re.sub(r'24\s*/\s*7|24 h(?:eures)? sur 24, 7 jours sur 7|24 horas,? (?:los )?7 días(?: de la semana)?|24시간 연중무휴|24時間365日', '24', text)
    if words:
        t = re.sub(r'\b(%s)\b' % '|'.join(WORDS), lambda m: str(WORDS[m.group(1).lower()]), t, flags=re.I)
        t = re.sub(r'([一两二三四五六七八九十])(?=[楼层个家栋厅小時时分岁歳天周週年号번층개])', lambda m: str(CJK[m.group(1)]), t)
    t = PHONE.sub(' ', t)                          # phones are compared separately
    t = re.sub(r'\d+(?:[.,]\d+)?[\s-]*(?:(?:lbs?|kg|km|mi|m|metres?|meters?|mètres?|metros?)\b|磅|公斤|公里|米|파운드|킬로그램|킬로미터|미터|ポンド|キロ|メートル|°)', ' ', t, flags=re.I)   # units get converted between languages
    t = re.sub(r'https?://\S+', ' ', t)
    t = re.sub(r'(?<!\d)(19|20)\d\d(?!\d)', ' ', t)   # years (also "1996年", where \b does not apply)
    out = set()
    for m in re.finditer(r'(?<!\d)(\d{1,2})(?:[:h.](\d{2}))?(?!\d)\s*([ap])?\.?\s*m?\.?', t, re.I):
        h = int(m.group(1)); mn = m.group(2)
        if m.group(3) and m.group(3).lower() == 'p' and h < 12: h += 12
        if m.group(3) and m.group(3).lower() == 'a' and h == 12: h = 0   # 12:30 a.m. = 0:30
        if mn and mn != '00': out.add(int(mn))
        out.add(h)
    for m in re.finditer(r'\d+', t):
        n = int(m.group())
        if n >= 100 or n == 0: continue
        out.add(n)
    norm = set()
    for n in out:
        if n == 0: continue
        norm.add(n)
        if 13 <= n <= 23: norm.add(n - 12)      # 17 ⇔ 5
        if 1 <= n <= 11: norm.add(n + 12)
    return norm

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--city', required=True); ap.add_argument('--strict', action='store_true')
    a = ap.parse_args()
    others = [c for c in kamdata.cities() if c != a.city and not c.startswith('_')]
    other_names = {kamdata.city_meta(c)['title'].replace(' Life Guide', '') for c in others}
    kamdata.use(a.city)
    AREA_OK = set(kamdata.city_meta().get('validate', {}).get('areaCodes') or AREA_BC) | TOLL_FREE
    P = kamdata.load('P')
    found = []
    def flag(p, kind, msg): found.append((kind, p['id'], p['n'], msg))
    for p in P:
        note = p.get('note', {})
        en = note.get('en', '')
        # 1. numbers across languages
        base, base_w = numbers(en), numbers(en, True)
        for l in LANGS:
            if l == 'en' or l not in note: continue
            other, other_w = numbers(note[l]), numbers(note[l], True)
            miss = sorted(n for n in base if n <= 99 and n not in other_w and n not in SMALL)
            extra = sorted(n for n in other if n not in base_w and n <= 99 and n not in SMALL)
            # only report a number that is missing in its every 12/24-hour form
            miss = [n for n in miss if not ({n, n - 12, n + 12} & other_w)]
            extra = [n for n in extra if not ({n, n - 12, n + 12} & base_w)]
            if miss or extra:
                flag(p, 'numbers', '%s vs en — missing %s, extra %s' % (l, miss or '-', extra or '-'))
        # 2. phone numbers in notes
        phones = {l: {''.join(m.groups()) for m in PHONE.finditer(note.get(l, ''))} for l in LANGS if l in note}
        if phones and len({frozenset(v) for v in phones.values()}) > 1:
            flag(p, 'phone', 'phone numbers differ between languages: %s' % {l: sorted(v) for l, v in phones.items()})
        own = re.sub(r'\D', '', p.get('p', ''))[-10:]
        for n in phones.get('en', set()):
            if n != own:
                flag(p, 'phone-note', 'note gives %s-%s-%s, record phone is %s (second line? check)' % (n[:3], n[3:6], n[6:], p.get('p', '—')))
        # 3. 24 hours
        # the place itself, not a hotline it mentions ("Here2Talk 24/7")
        says24 = bool(re.search(r'\bopen 24|open around the clock|24-hour (shelter|pharmacy|service|care|clinic)', en, re.I))
        is24 = bool((p.get('h') or {}).get('a'))
        if says24 and p.get('h') and not is24:
            flag(p, '24h', 'note says 24 hours but the hours on file are not')
        # 4. other cities' names
        blob = ' '.join([p.get('a', '')] + list(note.values()))
        for nm in other_names:
            if re.search(r'\b%s\b' % re.escape(nm), blob):
                flag(p, 'other-city', 'mentions %s' % nm)
        # 5. area codes
        for f in [p.get('p', '')] + [note.get('en', '')]:
            for m in PHONE.finditer(f or ''):
                if m.group(1) not in AREA_OK:
                    flag(p, 'area-code', 'area code %s in %r' % (m.group(1), m.group(0)))
    kinds = {}
    for k, *_ in found: kinds[k] = kinds.get(k, 0) + 1
    print('%s: %d places, %d findings %s' % (a.city, len(P), len(found), kinds or ''))
    for k, i, n, msg in sorted(found):
        print('  [%s] %s %s — %s' % (k, i, n, msg))
    INFO = {'phone-note', 'area-code'}   # often legitimate (a second line; an operator's out-of-province mobile)
    sys.exit(1 if (a.strict and any(k not in INFO for k, *_ in found)) else 0)

if __name__ == '__main__':
    main()
