#!/usr/bin/env python3
"""assistant/build.py — 把生活指南的已核实内容整理成助手读取的知识文件。

    python3 assistant/build.py                 # → assistant/build/knowledge.json、assistant/build/crisis.js
    python3 assistant/build.py --city kamloops

为什么存在：助手只能根据指南里已核实的内容回答（说明 §11"不另存副本"）。
这里每次从 cities/<城市>/ 和引擎源码现读，生成的文件在 assistant/build/（不入仓），
指南的数据一改，重新构建助手就跟着变。

读的内容：
- 办事卡 TASKS（六语标题、步骤、费用、要带的东西、来源、核实日期）；
- 地点 P（名称、分类、地址、电话、网址、备注、来源分级、核实月份）；
- 分类名 CI（引擎）；
- 热线：CITY.hotlines / localLines / localCrisis / help（城市 data.js），热线名称取引擎 UI 的 hot_* 文字；
- 危机识别规则 _CRISIS_RE：原样从引擎 30-analytics.js 抄出，助手和指南用同一条规则。
"""
import argparse, json, os, re, subprocess, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import kamdata

LANGS = ['zh', 'en', 'fr', 'es', 'ko', 'ja']
TASK_TEXT = ['t', 'q', 'why', 'cost', 'bring', 'deadline', 'wait', 'note', 'confid', 'help']


def city_obj():
    m = re.search(r"const CITY=\{.*?\n\};", kamdata.data_text(), re.S)
    if not m:
        sys.exit('data.js 里找不到 const CITY')
    r = subprocess.run(['node', '-e', m.group(0) + ';process.stdout.write(JSON.stringify(CITY))'],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit('CITY 求值失败：' + r.stderr[-400:])
    return json.loads(r.stdout)


def engine_file(name):
    with open(os.path.join(kamdata.ROOT, 'app', 'engine', 'js', name), encoding='utf-8') as f:
        return f.read()


def crisis_regex():
    m = re.search(r"^const _CRISIS_RE=(/.*/[a-z]*);$", engine_file('30-analytics.js'), re.M)
    if not m:
        sys.exit('引擎里找不到 _CRISIS_RE（30-analytics.js）')
    return m.group(1)


def hotline_labels():
    out = {}
    for lang, key, val in re.findall(r"UI\.([a-z]{2})\.hot_([a-z]+)='((?:[^'\\]|\\.)*)'",
                                     engine_file('00-ui-strings.js')):
        out.setdefault(key, {})[lang] = val
    return out


def task_record(t, city, checked_default):
    url = city['siteUrl'].rstrip('/') + '/'
    rec = {'id': 'task:' + t['id'], 'kind': 'task',
           'src': t.get('src'), 'srcName': t.get('srcName'),
           'srcL': t.get('srcL') or {}, 'srcNameL': t.get('srcNameL') or {},
           # 卡片自己的核实日期优先；没有就用全部卡片统一核实的日期
           'checked': (t.get('checked') or checked_default or '')[:7],
           'guide': {l: url + '?city=%s%s&task=%s' % (city['key'], '' if l == 'en' else '&lang=' + l, t['id'])
                     for l in LANGS},
           'place': t.get('place'), 'alias': t.get('alias') or []}
    for k in TASK_TEXT:
        if isinstance(t.get(k), dict):
            rec[k] = t[k]
    rec['steps'] = [s for s in (t.get('steps') or []) if isinstance(s, dict)]
    return rec


def place_record(p, ci, city):
    url = city['siteUrl'].rstrip('/') + '/'
    q = urllib.parse.quote(p['n'])
    return {'id': 'place:' + p['id'], 'kind': 'place', 'n': p['n'], 'c': p['c'],
            # 在指南地图上找：打开指南并搜索这个地点的名字（指南本来就支持 ?q=）
            'map': {l: url + '?city=%s%s&q=%s' % (city['key'], '' if l == 'en' else '&lang=' + l, q) for l in LANGS},
            'cat': ci.get(p['c'], {}), 'a': p.get('a'), 'p': p.get('p'), 'w': p.get('w'),
            'note': p.get('note') or {}, 'srcTier': p.get('src'), 'checked': p.get('v') or '',
            'alias': p.get('alias') or []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', default='kamloops')
    a = ap.parse_args()
    kamdata.use(a.city)
    city = city_obj()
    meta = kamdata.city_meta(a.city)
    city['siteUrl'] = meta['siteUrl']
    ci = kamdata.load('CI', engine=True)
    tasks = kamdata.load('TASKS')
    places = kamdata.load('P')
    labels = hotline_labels()

    know = {
        'city': {'key': city['key'], 'name': city['name'], 'siteUrl': meta['siteUrl'],
                 'title': meta.get('title')},
        'builtFrom': {'tasksChecked': city.get('tasksChecked'), 'today': kamdata.today(a.city).isoformat()},
        'help': city.get('help') or {},
        'hotlines': [dict(h, label=labels.get(h['t'], {})) for h in city.get('hotlines') or []],
        'localLines': city.get('localLines') or [],
        'localCrisis': city.get('localCrisis'),
        'infoLabel': labels.get('info', {}),
        'docs': [task_record(t, city, city.get('tasksChecked')) for t in tasks]
              + [place_record(p, ci, city) for p in places],
    }
    out = os.path.join(HERE, 'build')
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'knowledge.json'), 'w', encoding='utf-8') as f:
        json.dump(know, f, ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(out, 'crisis.js'), 'w', encoding='utf-8') as f:
        f.write('// 生成文件：assistant/build.py 从 app/engine/js/30-analytics.js 原样抄出，不要手改。\n')
        f.write('export const CRISIS_RE=%s;\n' % crisis_regex())
        f.write('export function isCrisis(q){return !!q&&CRISIS_RE.test(String(q));}\n')
    n_t = sum(1 for d in know['docs'] if d['kind'] == 'task')
    print('assistant/build: %d 张办事卡、%d 个地点、%d 条热线 → %s'
          % (n_t, len(know['docs']) - n_t, len(know['hotlines']), os.path.relpath(out, kamdata.ROOT)))


if __name__ == '__main__':
    main()
