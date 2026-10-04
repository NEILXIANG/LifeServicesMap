#!/usr/bin/env python3
"""Generate a city's review checklist and launch-readiness report from its data.

    python3 scripts/review_checklist.py --city kelowna [--out docs/reports/<date>-<City>审核清单.md]

What it does (methodology §8 上线标准):
1. Launch-readiness: checks the city against the launch standard — safety-critical coverage, categories,
   six languages, hours share, approximate positions, themes, areas, task cards, transit, draft status.
2. A review list ordered by consequence: safety-critical places first (care, shelters and crisis,
   settlement, government offices, food, legal), each with phone, source and the researcher's
   uncertainty notes from import/provenance.json; then every other record that carries an
   uncertainty note; then records held back from the map (research files' _held_for_review).
A person phones down the list and promotes each confirmed record to src:'own' with this month's v.
"""
import argparse, collections, datetime, glob, json, os, re, sys
_r = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_r))
import kamdata

SAFETY = ['hospital', 'pharmacy', 'support', 'gov', 'foodbank', 'legal', 'police', 'dental']
L6 = ['zh', 'en', 'fr', 'es', 'ko', 'ja']

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--city', required=True); ap.add_argument('--out')
    a = ap.parse_args()
    kamdata.use(a.city)
    meta = kamdata.city_meta()
    P = kamdata.load('P'); T = kamdata.load('TASKS'); BR = kamdata.load('BR'); LM = kamdata.load('LANDMARKS')
    prov = {}
    try: prov = json.load(open(os.path.join(kamdata.city_dir(), 'import', 'provenance.json'), encoding='utf-8'))
    except FileNotFoundError: pass
    held = []
    for f in sorted(glob.glob(os.path.join(kamdata.city_dir(), 'import', 'research', '*.json'))):
        d = json.load(open(f, encoding='utf-8'))
        held += [(x.get('n'), x.get('verify_notes', '')) for x in d.get('_held_for_review', [])]
    today = datetime.date.today().isoformat()
    name = meta['title'].replace(' Life Guide', '')
    n = len(P)
    six = sum(all(l in p.get('note', {}) for l in L6) for p in P)
    # open-air places have no hours; child care and schools are left out on both sides of the
    # comparison because the government datasets they come from carry no hours (Kamloops: 3/84, 6/33)
    no_hours = {'park', 'trail', 'beach', 'dogpark', 'splash', 'daycare', 'elem', 'school'}
    hours_base = [p for p in P if p['c'] not in no_hours]
    with_h = sum('h' in p for p in hours_base)
    kamdata.use('kamloops'); KP = kamdata.load('P'); kamdata.use(a.city)
    # methodology §8: a category the reference city has must be collected here too if it exists here;
    # one that does not exist (or is deliberately left out) is explained in import/config.json
    try: absent = json.load(open(os.path.join(kamdata.city_dir(), 'import', 'config.json'), encoding='utf-8')).get('categoriesNotCollected', {})
    except FileNotFoundError: absent = {}
    missing = sorted({p['c'] for p in KP} - {p['c'] for p in P} - set(absent))
    kb = [p for p in KP if p['c'] not in no_hours]; kref = 100.0 * sum('h' in p for p in kb) / max(1, len(kb))
    approx = [p for p in P if p.get('precision') == 'low']
    approx_safety = [p for p in approx if p['c'] in SAFETY]
    src = collections.Counter(p.get('src') for p in P)
    areas = collections.Counter(p['g'] for p in P)
    cats = collections.Counter(p['c'] for p in P)
    own = src.get('own', 0)
    safety = [p for p in P if p['c'] in SAFETY]
    def row(ok, item, detail):
        return '| %s | %s | %s |' % ('✅' if ok is True else '❌' if ok is False else '⚠️', item, detail)
    rows = [
        row(n >= 450, '地点数量（目标见 PROFILE.md）', '%d' % n),
        row(six == n, '六种语言', '%d / %d' % (six, n)),
        row(100.0 * with_h / max(1, len(hours_base)) >= min(60, kref), '有营业时间（不含露天、托儿、学校；目标不低于 Kamloops 同口径）',
            '%d / %d（%.0f%%）；Kamloops 同口径 %.0f%%' % (with_h, len(hours_base), 100.0 * with_h / max(1, len(hours_base)), kref)),
        row(len(approx) <= 0.1 * n and not approx_safety, '"大致位置" ≤ 10%，且不含安全相关地点', '%d 个；其中安全相关 %d 个' % (len(approx), len(approx_safety))),
        row(own >= len(safety), '安全相关地点电话核实（src: own）', '已核实 %d / 安全相关 %d' % (own, len(safety))),
        row(not missing, 'Kamloops 有的分类这里也有（不存在的写进 config.json 的 categoriesNotCollected）',
            ('缺 %d 类：%s' % (len(missing), '、'.join(missing))) if missing else '齐全' + ('（%d 类已说明不收）' % len(absent) if absent else '')),
        row(len(T) > 0, '办事卡', '%d 张' % len(T)),
        row(None if not BR else True, '公交（运营方 GTFS）', '%d 条线路' % len(BR)),
        row(len(LM) > 0, '地标', '%d 个' % len(LM)),
        row(meta.get('status') != 'draft', '草稿状态已去掉', meta.get('status', 'live')),
    ]
    out = ['# %s 审核清单与上线差距（%s 自动生成）' % (name, today), '',
           '> 由 `python3 scripts/review_checklist.py --city %s` 生成，每次数据变化后重跑。按"说错的后果"排序：先核实安全相关的地点。' % a.city,
           '> 核实方法：打电话或到场确认地址、电话、营业时间和"谁能用"；确认后把该记录的 `src` 改为 `own`、`v` 改为当月。', '',
           '## 一、上线差距', '', '| 状态 | 项目 | 现状 |', '|---|---|---|'] + rows + ['',
           '来源：' + '、'.join('%s %d' % (k, v) for k, v in src.most_common()) + '。',
           '区域：' + '、'.join('%s %d' % (k, v) for k, v in sorted(areas.items())) + '。', '',
           '## 二、先核实：安全相关的地点（%d 个）' % len(safety), '',
           '| 类别 | 名称 | 电话 | 地址 | 来源网址 | 待核实说明 |', '|---|---|---|---|---|---|']
    order = {c: i for i, c in enumerate(SAFETY)}
    for p in sorted(safety, key=lambda p: (order[p['c']], p['n'])):
        pv = prov.get(p['id'], {})
        out.append('| %s | %s | %s | %s | %s | %s |' % (p['c'], p['n'].replace('|', '/'), p.get('p', '—'), p['a'].replace('|', '/'),
                   (p.get('w') or pv.get('source_url') or ''), (pv.get('verify_notes') or '').replace('|', '/').replace('\n', ' ')[:300]))
    others = [p for p in P if p['c'] not in SAFETY and (prov.get(p['id'], {}).get('verify_notes'))]
    out += ['', '## 三、其他带"待核实说明"的地点（%d 个）' % len(others), '', '| 类别 | 名称 | 待核实说明 |', '|---|---|---|']
    for p in sorted(others, key=lambda p: (p['c'], p['n'])):
        out.append('| %s | %s | %s |' % (p['c'], p['n'].replace('|', '/'), prov[p['id']]['verify_notes'].replace('|', '/').replace('\n', ' ')[:300]))
    out += ['', '## 四、暂不上地图、需要先确认的（%d 个）' % len(held), '']
    out += ['- **%s**：%s' % (h, (v or '').replace('\n', ' ')[:300]) for h, v in held] or ['（无）']
    out += ['', '## 五、各类别数量', '', '、'.join('%s %d' % (k, v) for k, v in cats.most_common()), '']
    path = a.out or os.path.join(kamdata.ROOT, 'docs', 'reports', '%s-%s审核清单.md' % (today, name))
    open(path, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('wrote %s' % os.path.relpath(path, kamdata.ROOT))
    for r in rows: print('  ' + r)

if __name__ == '__main__':
    main()
