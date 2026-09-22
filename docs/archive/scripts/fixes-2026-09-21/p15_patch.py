#!/usr/bin/env python3
"""2026-09-22 — follow-up to p14: five place notes told the reader to "call", but
their unverifiable phone number is no longer shown. The advice now points to the
website where there is one, or simply states the fact. Six languages each."""
import sys, json, re
sys.path.insert(0, '.')
import kamdata
D = 'src/data-kamloops.js'
d = open(D, encoding='utf-8').read()
J = lambda o: json.dumps(o, separators=(',', ':'), ensure_ascii=False)
P0 = {p['id']: p for p in kamdata.load('P')}
def pid(n):
    ids = [i for i, p in P0.items() if p['n'] == n]; assert len(ids) == 1, n; return ids[0]
def edit_place(i, fn):
    global d
    lines = d.split('\n')
    hit = [k for k, l in enumerate(lines) if ('"id":"%s"' % i) in l]; assert len(hit) == 1
    mm = re.match(r'^(\s*(?:const P=\[)?)(\{.*\})(,|\];)?\s*$', lines[hit[0]])
    o = json.loads(mm.group(2)); assert J(o) == mm.group(2)
    fn(o); lines[hit[0]] = mm.group(1) + J(o) + (mm.group(3) or ''); d = '\n'.join(lines)
EDITS = {
 'Tranquille Market': {
  'zh': ('各目录上的营业时间不一致——晚上去之前先打电话。', '各目录上的营业时间不一致。'),
  'en': (' — call if you are going late.', '.'), 'fr': (' — appelez si vous y allez tard.', '.'),
  'es': (': llame si va tarde.', '.'), 'ko': ('목록마다 영업시간이 달라 늦게 갈 때는 전화하세요.', '목록마다 영업시간이 다릅니다.'),
  'ja': ('掲載ごとに営業時間が違うので、遅い時間は電話で確認を。', '掲載ごとに営業時間が違います。')},
 'Beem Credit Union (Valleyview)': {
  'zh': ('分行营业时间请先电话确认。', '分行营业时间请以 Beem 官网为准。'),
  'en': ('call to confirm current branch hours.', 'check current branch hours on the Beem website.'),
  'fr': ('appelez pour confirmer les heures de la succursale.', 'vérifiez les heures de la succursale sur le site de Beem.'),
  'es': ('llame para confirmar el horario de la sucursal.', 'consulte el horario de la sucursal en el sitio de Beem.'),
  'ko': ('지점 영업시간은 전화로 확인하세요.', '지점 영업시간은 Beem 웹사이트에서 확인하세요.'),
  'ja': ('支店の営業時間は電話で確認を。', '支店の営業時間はBeemのサイトで確認を。')},
 'The View Apartments': {
  'zh': ('当前租金以官网或电话为准。', '当前租金以官网为准。'),
  'en': ('check the website or call for current rents.', 'check the website for current rents.'),
  'fr': ('loyers actuels sur le site ou par téléphone.', 'loyers actuels sur le site.'),
  'es': ('consulte el sitio o llame para saber los alquileres actuales.', 'consulte el sitio para saber los alquileres actuales.'),
  'ko': ('현재 임대료는 웹사이트나 전화로 확인하세요.', '현재 임대료는 웹사이트에서 확인하세요.'),
  'ja': ('現在の家賃はサイトか電話で確認を。', '現在の家賃はサイトで確認を。')},
 'The Success Formula Tutoring': {
  'zh': ('不同目录上的地址不一样——去之前先打电话。', '不同目录上的地址不一样。'),
  'en': (' — call before you go.', '.'), 'fr': (' — appelez avant d’y aller.', '.'),
  'es': (': llame antes de ir.', '.'), 'ko': ('목록마다 주소가 다르니 가기 전에 전화하세요.', '목록마다 주소가 다릅니다.'),
  'ja': ('掲載によって住所が違うので、行く前に電話を。', '掲載によって住所が違います。')},
 'Church of Jesus Christ of Latter-day Saints (Kamloops)': {
  'zh': ('具体礼拜时间请致电确认', '各堂区礼拜时间不同'),
  'en': (', so call to confirm service times', ', and service times differ by ward'),
  'fr': (", appelez pour confirmer les heures d'office", ", et les heures d'office diffèrent selon la paroisse"),
  'es': (', llame para confirmar los horarios', ', y los horarios varían según la congregación'),
  'ko': ('사용하므로 예배 시간은 전화로 확인하세요', '사용하며 와드마다 예배 시간이 다릅니다'),
  'ja': ('使うため礼拝時間は電話で確認を', '使い、ワードごとに礼拝時間が異なります')},
}
for n, per in EDITS.items():
    def f(o, per=per, n=n):
        assert not o.get('p'), n
        for l, (a, b) in per.items():
            assert o['note'][l].count(a) == 1, (n, l, a)
            o['note'][l] = o['note'][l].replace(a, b)
    edit_place(pid(n), f)
open(D, 'w', encoding='utf-8').write(d)
P1 = {p['id']: p for p in kamdata.load('P')}
changed = {i for i in P0 if P0[i] != P1[i]}
assert changed == {pid(n) for n in EDITS}, changed
assert all({k for k in set(P0[i]) | set(P1[i]) if P0[i].get(k) != P1[i].get(k)} == {'note'} for i in changed)
print('p15 applied: %d notes' % len(changed))
