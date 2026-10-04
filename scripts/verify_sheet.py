#!/usr/bin/env python3
"""Printable phone-verification sheet for a city's safety-critical places.

    python3 scripts/verify_sheet.py --city kelowna [--out <file.html>]

One A4 card per place, ordered as the review checklist (care, shelters and crisis, settlement and
government, food, legal, police): what is on file (name, phone, address, hours as we hold them,
who can use it), an English script to read on the call, and boxes to tick or correct by hand.
After the calls, a confirmed record becomes src:'own' with this month's v (and corrections go into
the research file, then the importers are re-run).

The page is self-contained HTML (no network), meant to be printed or saved as PDF from a browser.
Output defaults to the operations folder outside the repository, because it is a working
document, not part of the product: ../<repo> - ops/verification/<date>-<city>-核实表.html
"""
import argparse, datetime, html, json, os, sys
_r = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_r))
import kamdata

SAFETY = ['hospital', 'pharmacy', 'support', 'gov', 'foodbank', 'legal', 'police', 'dental']
LABEL = {'hospital': '医疗', 'pharmacy': '药房', 'support': '庇护所与危机支持', 'gov': '安置与政府办事',
         'foodbank': '食物', 'legal': '法律', 'police': '警察', 'dental': '牙科'}
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

def fmt_hours(h):
    if not h: return '（无）'
    if h.get('a'): return '24 hours'
    out = []
    for d1, d2, o, c, _ in h.get('r', []):
        day = DAYS[d1 - 1] if d1 == d2 else '%s–%s' % (DAYS[d1 - 1], DAYS[d2 - 1])
        out.append('%s %02d:%02d–%02d:%02d' % (day, o // 60, o % 60, (c // 60) % 24, c % 60))
    return '; '.join(out) + (' (by appointment)' if h.get('q') == 'qAppt' else '')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--city', required=True); ap.add_argument('--out')
    a = ap.parse_args()
    kamdata.use(a.city)
    meta = kamdata.city_meta(); city = meta['title'].replace(' Life Guide', '')
    P = kamdata.load('P')
    try: prov = json.load(open(os.path.join(kamdata.city_dir(), 'import', 'provenance.json'), encoding='utf-8'))
    except FileNotFoundError: prov = {}
    order = {c: i for i, c in enumerate(SAFETY)}
    rows = sorted([p for p in P if p['c'] in SAFETY], key=lambda p: (order[p['c']], p['n']))
    today = datetime.date.today().isoformat()
    e = html.escape
    cards = []
    for i, p in enumerate(rows, 1):
        pv = prov.get(p['id'], {})
        who = pv.get('who') or ''
        note = pv.get('verify_notes') or ''
        cards.append('''<section class="card">
<div class="head"><span class="no">%d</span><span class="cat">%s</span><b>%s</b></div>
<table>
<tr><th>电话 Phone</th><td class="big">%s</td><td class="box">☐ 对 ☐ 改为：________________</td></tr>
<tr><th>地址 Address</th><td>%s, %s</td><td class="box">☐ 对 ☐ 改为：________________</td></tr>
<tr><th>时间 Hours</th><td>%s</td><td class="box">☐ 对 ☐ 改为：________________</td></tr>
<tr><th>谁能用 Who</th><td>%s</td><td class="box">☐ 对 ☐ 补充：________________</td></tr>
<tr><th>语言 Languages</th><td colspan="2" class="box">________________________ ☐ 可安排翻译 interpreter</td></tr>
<tr><th>能否直接去 Walk-in</th><td colspan="2" class="box">☐ 可以直接去 walk-in ☐ 要预约 appointment ☐ 先打电话 call first</td></tr>
</table>
%s
<div class="end">结果：☐ 全部确认 ☐ 有改动 ☐ 打不通（再试：____）　核实人：________　日期：________</div>
</section>''' % (i, e(LABEL[p['c']]), e(p['n']), e(p.get('p', '（无电话）')), e(p['a']), e(city if p['g'] != 'wk' else 'West ' + city),
                  e(fmt_hours(p.get('h'))), e(who[:160]) or '（未知）',
                  ('<p class="todo">调研时的疑问：%s</p>' % e(note[:260])) if note else ''))
    page = '''<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(city)s 电话核实表 %(today)s</title>
<style>
 @page { size: A4; margin: 12mm; }
 body { font: 12px/1.45 -apple-system, "PingFang SC", "Noto Sans CJK SC", sans-serif; color:#111; background:#fff; margin:0 auto; max-width: 186mm; padding: 8px 16px; }
 h1 { font-size: 18px; margin: 4px 0 6px; } .lead { margin: 0 0 10px; }
 .script { border: 1px solid #999; padding: 8px 10px; margin: 0 0 12px; background: #f6f6f6; }
 .script p { margin: 4px 0; }
 .card { border: 1px solid #333; border-radius: 4px; padding: 8px 10px; margin: 0 0 10px; break-inside: avoid; page-break-inside: avoid; }
 .head { font-size: 13px; margin-bottom: 4px; } .no { display:inline-block; min-width: 22px; font-weight:700; }
 .cat { display:inline-block; border:1px solid #333; border-radius: 3px; padding: 0 5px; margin-right: 6px; font-size: 11px; }
 table { width: 100%%; border-collapse: collapse; } th { text-align:left; width: 92px; font-weight:600; vertical-align: top; padding: 2px 4px 2px 0; }
 td { padding: 2px 4px; vertical-align: top; } .big { font-size: 14px; font-weight: 700; white-space: nowrap; } .box { color:#333; white-space: nowrap; }
 .todo { margin: 4px 0 0; font-size: 11px; color:#444; } .end { margin-top: 6px; border-top: 1px dashed #999; padding-top: 4px; font-size: 11px; }
 @media screen and (max-width: 600px) { .box { white-space: normal; } }
</style></head><body>
<h1>%(city)s 电话核实表（安全相关地点 %(n)d 个）</h1>
<p class="lead">生成于 %(today)s，来自本工具的数据。按"说错的后果"排序：医疗、庇护所与危机支持、安置与政府办事、食物、法律、警察。
每张卡上是我们<strong>现在</strong>记录的信息；打电话逐项确认，对的打勾，不对的写在横线上。全部打完后交回，用来更新数据（确认过的记录会标为"已电话核实"）。</p>
<div class="script"><b>打电话时可以这样说（英文）</b>
<p>"Hi, I'm checking information for a free multilingual guide that helps people who are new to %(city)s find local services. May I confirm a few details? It takes about a minute."</p>
<p>1. "Is this still the right address: … ?"　2. "What are your hours this week?"　3. "Who can use your service — is it open to anyone, or only to some people, for example permanent residents?"</p>
<p>4. "Can people just walk in, or do they need an appointment?"　5. "Do any of your staff speak languages other than English, or can you arrange an interpreter?"</p>
<p>结束时："Thank you very much — is there anything you'd like new residents to know about your service?"</p>
<p>如果对方不方便：记下"打不通 / 请回电"，换下一个。不要在电话里留个人信息。</p></div>
%(cards)s
</body></html>''' % {'city': e(city), 'today': today, 'n': len(rows), 'cards': '\n'.join(cards)}
    out = a.out or os.path.join(os.path.dirname(kamdata.ROOT), os.path.basename(kamdata.ROOT) + ' - ops',
                                'verification', '%s-%s-核实表.html' % (today, city))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(page)
    print('wrote %s (%d places)' % (out, len(rows)))

if __name__ == '__main__':
    main()
