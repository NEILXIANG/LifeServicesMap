#!/usr/bin/env python3
"""2026-09-24 — school hours: say what is true instead of a number nobody checked.

The 10 elementary schools already on the map carried Mon–Fri 8:30–15:30. No
source publishes that: SD73 does not list office hours, bell times differ by
school and change with the year, and the province's dataset has no hours at
all. So "open now" was answering a question the data could not answer.

The hours come off all elementary records, which makes the app say "hours
unknown", and every elementary note now ends with the honest instruction:
office hours and bell times differ by school — call the school or check its
page before going. The phone and the website are on every one of the 25 cards.
"""
import json, re, sys

D = 'src/data-kamloops.js'
J = lambda o: json.dumps(o, separators=(',', ':'), ensure_ascii=False)

TAIL = {
 "zh": "上课和办公时间各校不同，也会随学年变化——去之前先打电话或看学校网页确认。",
 "en": "Office hours and bell times differ by school and change from year to year — call the school or check its page before you go.",
 "fr": "Les heures de bureau et les horaires de classe varient d’une école à l’autre et changent d’une année à l’autre — téléphonez à l’école ou consultez sa page avant de vous déplacer.",
 "es": "El horario de oficina y el de clases varían según la escuela y cambian cada año: llame a la escuela o consulte su página antes de ir.",
 "ko": "사무실 운영 시간과 수업 시간은 학교마다 다르고 해마다 바뀝니다 — 가기 전에 학교에 전화하거나 홈페이지를 확인하세요.",
 "ja": "事務室の受付時間や授業時間は学校ごとに異なり、年度によっても変わります — 行く前に学校に電話するか、学校のページで確認してください。",
}

lines = open(D, encoding='utf-8').read().split('\n')
n_h = n_note = 0
for k, line in enumerate(lines):
    m = re.match(r'^(\s*(?:const P=\[)?)(\{.*\})(,|\];)?\s*$', line)
    if not m: continue
    try: o = json.loads(m.group(2))
    except Exception: continue
    if not isinstance(o, dict) or o.get('c') != 'elem': continue
    assert J(o) == m.group(2), o.get('n')
    if 'h' in o:
        del o['h']; n_h += 1
    note = o.get('note')
    if isinstance(note, dict) and TAIL['en'] not in (note.get('en') or ''):
        for l, t in TAIL.items():
            base = (note.get(l) or '').rstrip()
            sep = '' if base.endswith(('。', '.', '！', '!', '?', '？')) else ('。' if l in ('zh', 'ja') else '. ')
            note[l] = re.sub(r'\s{2,}', ' ', (base + sep + ' ' + t).replace('。 ', '。')).strip()
        n_note += 1
    lines[k] = m.group(1) + J(o) + (m.group(3) or '')

if n_h == 0 and n_note == 0:
    sys.exit('nothing changed — already applied?')
open(D, 'w', encoding='utf-8').write('\n'.join(lines))
print('p24 applied: hours removed from %d schools, note extended on %d' % (n_h, n_note))
