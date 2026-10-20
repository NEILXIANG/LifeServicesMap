#!/usr/bin/env python3
"""The knowledge base: one registry of lessons, kept honest by the code it points at.

    python3 scripts/knowledge.py            # check, then (re)write docs/knowledge/经验库.md and 资产清单.md
    python3 scripts/knowledge.py --check    # check only; fails if anything is wrong or the pages are stale
    python3 scripts/knowledge.py --brief 导入   # before a step: every rule for that phase (立项 调研 画像 骨架 导入 核实 翻译 城市内容 引擎 上线 维护)
    python3 scripts/knowledge.py --todo     # lessons still only written down or not in place: the hardening backlog

Source of truth: docs/knowledge/lessons.json — {"lessons": [...], "assets": [...]}.

A lesson says what happened (evidence, in which city and round), what rule came out of it, and where that
rule now lives. Its status is checked, not trusted:
  auto  a check fails or reports a gap by itself (validate.py, a test, consistency/review scripts, deploy gate)
  tool  a tool does it right by construction (an importer rule, an engine behaviour), but nothing fails
  doc   written down only — a person has to remember it
  todo  decided, not in place yet
Every "encoded" entry names a file and a marker string that must exist in it; an "auto" lesson needs at
least one entry of kind validate/test/check/gate. Evidence must point at a file and a section that exist.
So a lesson cannot claim a check that was renamed or deleted, and the pages cannot drift from the registry.

Why (2026-10-04): the same lesson was written in three places (iteration log, methodology §9, Kamloops
summary), the index was a month old, and nothing could answer "which lessons are actually enforced?".
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = os.path.join(ROOT, 'docs', 'knowledge')
SRC = os.path.join(KB, 'lessons.json')
OUT_LESSONS = os.path.join(KB, '经验库.md')
OUT_ASSETS = os.path.join(KB, '资产清单.md')
# 2026-10-04: the data-source catalogue — same pattern (registry checked against the repo, page generated)
SOURCES = os.path.join(KB, 'sources.json')
OUT_SOURCES = os.path.join(KB, '数据来源目录.md')
LEVEL_RE = re.compile(r'^(federal|province:[a-z]+|region:[a-z0-9-]+|operator:[a-z0-9-]+|municipal:[a-z0-9-]+|first-nation:[a-z0-9-]+)$')
LEVEL_ORDER = ['federal', 'province', 'region', 'operator', 'municipal', 'first-nation']
LEVEL_NAME = {'federal': '联邦', 'province': '省', 'region': '区域（健康局、学区、区域政府）', 'operator': '运营方',
              'municipal': '市', 'first-nation': '原住民政府'}

AREAS = ['分发与运营', '数据来源与核实', '坐标与地址', '营业时间', '导入与合并', '引擎与城市分离', '测试与门禁',
         '多语言', '搜索与交互', '安全、法律与隐私', '部署与运维', '方法与流程']
STATUS = {'auto': '✅ 自动检查', 'tool': '🔧 工具保证', 'doc': '📄 只有文档', 'todo': '⏳ 待落实'}
AUTO_KINDS = {'validate', 'test', 'check', 'gate'}
KINDS = AUTO_KINDS | {'importer', 'tool', 'engine', 'doc', 'prompt', 'data'}
SCOPES = {'all': '所有城市', 'CA': '加拿大', 'BC': 'BC 省', 'city': '单个城市'}

# 2026-10-19: main carries Kamloops only (decision D7). Paths listed in scripts/main-excludes.txt are left out of main
# by scripts/sync-main.sh; evidence that lives under them is skipped *only where the path is absent*, so on multi-city
# (where they exist) every reference is still checked.
def _excludes():
    t = _read_raw(os.path.join(ROOT, 'scripts', 'main-excludes.txt')) or ''
    return [x.strip().rstrip('/') for x in t.splitlines() if x.strip() and not x.lstrip().startswith('#')]
def _read_raw(p):
    return open(p, encoding='utf-8').read() if os.path.isfile(p) else None
LEFT_OUT = []
def left_out(rel):
    """True when rel is missing because this branch deliberately leaves it out (see scripts/main-excludes.txt)."""
    rel = (rel or '').rstrip('/')
    if os.path.exists(os.path.join(ROOT, rel)): return False
    if any(rel == x or rel.startswith(x + '/') for x in _excludes()):
        LEFT_OUT.append(rel); return True
    return False

def _read(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p): return None
    try: return open(p, encoding='utf-8').read()
    except UnicodeDecodeError: return open(p, encoding='latin-1').read()

def check(data):
    errs = []
    ids = [l.get('id') for l in data['lessons']]
    for i, n in collections.Counter(ids).items():
        if n > 1: errs.append('%s: id used %d times' % (i, n))
    for l in data['lessons']:
        lid = l.get('id', '?')
        if not re.fullmatch(r'L-\d{3}', lid or ''): errs.append('%s: id must look like L-001' % lid)
        for k in ('title', 'area', 'scope', 'lesson', 'rule', 'status', 'evidence', 'encoded'):
            if not l.get(k): errs.append('%s: missing %s' % (lid, k))
        if l.get('area') not in AREAS: errs.append('%s: unknown area %r' % (lid, l.get('area')))
        if l.get('status') not in STATUS: errs.append('%s: unknown status %r' % (lid, l.get('status')))
        if l.get('scope') not in SCOPES: errs.append('%s: unknown scope %r' % (lid, l.get('scope')))
        for e in l.get('evidence', []):
            if left_out(e.get('ref')): continue
            t = _read(e.get('ref', ''))
            if t is None: errs.append('%s: evidence file missing: %s' % (lid, e.get('ref')))
            elif e.get('section') and e['section'] not in t: errs.append('%s: section %r not in %s' % (lid, e['section'], e['ref']))
        kinds = set()
        for c in l.get('encoded', []):
            kinds.add(c.get('kind'))
            if c.get('kind') not in KINDS: errs.append('%s: unknown encoded kind %r' % (lid, c.get('kind')))
            if left_out(c.get('path')): continue
            t = _read(c.get('path', ''))
            if t is None: errs.append('%s: %s not found' % (lid, c.get('path')))
            elif c.get('marker') and c['marker'] not in t: errs.append('%s: marker %r not in %s' % (lid, c['marker'], c['path']))
        if l.get('status') == 'auto' and not (kinds & AUTO_KINDS):
            errs.append('%s: status auto but nothing of kind validate/test/check/gate' % lid)
        if l.get('status') == 'tool' and not (kinds & ({'importer', 'tool', 'engine'} | AUTO_KINDS)):
            errs.append('%s: status tool but no importer/tool/engine entry' % lid)
    # every "L-0xx" cited in the knowledge docs, the methodology and the prompts must exist
    known = set(ids)
    cited = ['docs/knowledge/README.md', 'docs/guides/新城市扩展方法论与标准.md', 'docs/guides/新城市操作手册.md']
    pdir = os.path.join(KB, 'prompts')
    if os.path.isdir(pdir): cited += [os.path.relpath(os.path.join(pdir, f), ROOT) for f in sorted(os.listdir(pdir)) if f.endswith('.md')]
    for rel in cited:
        t = _read(rel) or ''
        for ref in sorted(set(re.findall(r'\bL-\d{3}\b', t)) - known):
            errs.append('%s cites %s, which is not in the registry' % (rel, ref))
    # 2026-10-04 (closing the loop): every round of an iteration log must have produced at least one lesson —
    # a round whose findings never reach the registry is a lesson the next city has to learn again.
    # A round that genuinely taught nothing new says so in its heading: "（无新经验）".
    cited_sections = {e.get('section', '') for l in data['lessons'] for e in l.get('evidence', [])}
    for logf in sorted(f for f in os.listdir(os.path.join(ROOT, 'docs', 'reports')) if f.endswith('迭代日志.md')):
        rel = os.path.join('docs', 'reports', logf)
        for h in re.findall(r'^## 第 \d+ 轮[^\n]*', _read(rel) or '', re.M):
            key = h.split('：')[0]
            if '无新经验' in h: continue
            if not any(c == key or c.startswith(key + '：') for c in cited_sections):
                errs.append('%s "%s": no lesson cites this round — add its lessons to lessons.json' % (rel, h))
    for a in data.get('assets', []):
        for p in a.get('paths', []):
            if not os.path.exists(os.path.join(ROOT, p)) and not left_out(p): errs.append('asset %r: %s not found' % (a.get('name'), p))
    return errs

def check_sources(src):
    errs = []
    ids = [s.get('id') for s in src.get('sources', [])]
    for i, n in collections.Counter(ids).items():
        if n > 1: errs.append('source %s: id used %d times' % (i, n))
    for s in src.get('sources', []):
        sid = s.get('id', '?')
        for k in ('name', 'level', 'url', 'licence', 'kind', 'usedBy', 'evidence'):
            if not s.get(k): errs.append('source %s: missing %s' % (sid, k))
        if not LEVEL_RE.match(s.get('level', '')): errs.append('source %s: bad level %r' % (sid, s.get('level')))
        if left_out(s.get('evidence')): t = ''
        else: t = _read(s.get('evidence', ''))
        if t is None: errs.append('source %s: evidence file missing: %s' % (sid, s.get('evidence')))
        elif t and s.get('url') not in (None, 'unknown'):
            joined = re.sub(r"['\"]\s*\n\s*['\"]", '', t)        # a URL split over two string literals
            if s['url'] not in t and s['url'] not in joined:
                errs.append('source %s: url not found in %s' % (sid, s['evidence']))
        if s.get('importer') and not os.path.exists(os.path.join(ROOT, s['importer'])) and not left_out(s['importer']):
            errs.append('source %s: importer %s not found' % (sid, s['importer']))
    return errs

def render_sources(src):
    S = src.get('sources', [])
    out = ['# 数据来源目录', '',
           '> 由 `python3 scripts/knowledge.py` 从 `docs/knowledge/sources.json` 生成，**不要手改本文件**；每个网址由脚本核对仍写在出处文件里。',
           '> 两座城市实际用过的官方和开放数据来源，按层级。下一座 BC 城市只需要补"区域"和"市"两层；外省城市照"省"这一组逐项找对应来源。',
           '> 只收政府和官方机构；机构自己的官网、新闻不在这里。许可写 unknown 的，用于对外内容之前先查清。', '',
           '共 %d 个：%s。' % (len(S), '，'.join('%s %d' % (LEVEL_NAME[g], sum(s['level'].split(':')[0] == g for s in S)) for g in LEVEL_ORDER
                                                if any(s['level'].split(':')[0] == g for s in S)))]
    def cell(x): return (x or '').replace('|', '／').replace('\n', ' ')
    for g in LEVEL_ORDER:
        group = [s for s in S if s['level'].split(':')[0] == g]
        if not group: continue
        out += ['', '## %s' % LEVEL_NAME[g]]
        for lv in sorted({s['level'] for s in group}):
            out += ['', '### `%s`' % lv, '', '| 来源 | 类型 | 许可 | 用了什么 | 导入工具 | 城市 | 注意 |', '|---|---|---|---|---|---|---|']
            for s in sorted((x for x in group if x['level'] == lv), key=lambda x: x['name']):
                name = '[%s](%s)' % (cell(s['name']), s['url']) if s['url'].startswith('http') else cell(s['name'])
                out.append('| %s | %s | %s | %s | %s | %s | %s |' % (name, s['kind'], cell(s['licence']), cell(s.get('fields')),
                           '`%s`' % s['importer'] if s.get('importer') else '', ', '.join(s['usedBy']), cell(s.get('gotchas'))))
    return '\n'.join(out) + '\n'

def render_lessons(data):
    L = data['lessons']
    by_status = collections.Counter(l['status'] for l in L)
    out = ['# 经验库（Kamloops + Kelowna）', '',
           '> 由 `python3 scripts/knowledge.py` 从 `docs/knowledge/lessons.json` 生成，**不要手改本文件**。',
           '> 每条经验写明：发生了什么（证据）、变成了什么规则、规则现在落在哪里；状态由脚本对照代码核实。',
           '> 入口和用法见 `docs/knowledge/README.md`。', '',
           '## 总览', '',
           '共 %d 条：%s。' % (len(L), '，'.join('%s %d' % (STATUS[s], by_status.get(s, 0)) for s in STATUS)), '',
           '| 领域 | ' + ' | '.join(STATUS[s] for s in STATUS) + ' | 合计 |',
           '|---|' + '---|' * (len(STATUS) + 1)]
    for a in AREAS:
        c = collections.Counter(l['status'] for l in L if l['area'] == a)
        if not c: continue
        out.append('| %s | %s | %d |' % (a, ' | '.join(str(c.get(s, '')) or '' for s in STATUS), sum(c.values())))
    out += ['', '## 待办：还没有变成检查的经验', '',
            '"只有文档"的经验靠人记住，"待落实"的还没做。每轮迭代挑几条，变成检查或工具。', '',
            '| 编号 | 经验 | 状态 | 领域 |', '|---|---|---|---|']
    for l in L:
        if l['status'] in ('todo', 'doc'):
            out.append('| %s | %s | %s | %s |' % (l['id'], l['title'], STATUS[l['status']], l['area']))
    for a in AREAS:
        group = [l for l in L if l['area'] == a]
        if not group: continue
        out += ['', '## %s' % a]
        for l in group:
            out += ['', '### %s %s' % (l['id'], l['title']), '',
                    '%s · 适用：%s%s' % (STATUS[l['status']], SCOPES[l['scope']], (' · 阶段：' + l['phase']) if l.get('phase') else ''), '',
                    '**经验**：' + l['lesson'], '',
                    '**规则**：' + l['rule'], '']
            out.append('**证据**：')
            for e in l['evidence']:
                out.append('- %s：%s（`%s`%s）' % (e.get('city', ''), e.get('what', ''), e['ref'], (' · ' + e['section'].lstrip('# ')) if e.get('section') else ''))
            out.append('')
            out.append('**落在哪里**：')
            for c in l['encoded']:
                out.append('- %s：`%s`%s' % (c['kind'], c['path'], (' — 「%s」' % c['marker']) if c.get('marker') else ''))
    return '\n'.join(out) + '\n'

def render_assets(data):
    out = ['# 数字资产清单', '',
           '> 由 `python3 scripts/knowledge.py` 从 `docs/knowledge/lessons.json` 生成，**不要手改本文件**；路径由脚本核对存在。', '',
           '| 资产 | 类型 | 用途 | 可复用范围 | 路径 |', '|---|---|---|---|---|']
    for a in data.get('assets', []):
        out.append('| %s | %s | %s | %s | %s |' % (a['name'], a['type'], a['use'], a['reuse'], '<br>'.join('`%s`' % p for p in a['paths'])))
    return '\n'.join(out) + '\n'

PHASES = ['立项', '调研', '画像', '骨架', '导入', '核实', '翻译', '城市内容', '引擎', '上线', '维护']

def brief(data, phase):
    """Before a step: the rules that apply to it, the ones nothing enforces first (those are the ones people forget)."""
    if phase not in PHASES:
        sys.exit('phase must be one of: ' + ' '.join(PHASES))
    order = {'todo': 0, 'doc': 1, 'tool': 2, 'auto': 3}
    L = sorted((l for l in data['lessons'] if l.get('phase') == phase), key=lambda l: (order[l['status']], l['id']))
    print('# %s：%d 条经验（先列靠人记的，再列已有工具和检查兜底的）\n' % (phase, len(L)))
    for l in L:
        print('%s %s %s\n   规则：%s' % (STATUS[l['status']].split()[0], l['id'], l['title'], l['rule']))
    print('\n全文：docs/knowledge/经验库.md；开工前必读：docs/knowledge/README.md 第三节。')

def todo(data):
    L = [l for l in data['lessons'] if l['status'] in ('todo', 'doc')]
    print('# 待加固：%d 条经验还只靠人记或还没落实。每轮挑一两条变成检查或工具（改 status 和 encoded）。\n' % len(L))
    for l in sorted(L, key=lambda l: (l['status'] != 'todo', l['area'], l['id'])):
        print('%s %s [%s] %s' % (STATUS[l['status']].split()[0], l['id'], l['area'], l['title']))

def main():
    if '--brief' in sys.argv or '--todo' in sys.argv:
        data = json.load(open(SRC, encoding='utf-8'))
        if '--todo' in sys.argv: todo(data)
        else: brief(data, sys.argv[sys.argv.index('--brief') + 1] if len(sys.argv) > sys.argv.index('--brief') + 1 else '')
        return
    only_check = '--check' in sys.argv
    data = json.load(open(SRC, encoding='utf-8'))
    src = json.load(open(SOURCES, encoding='utf-8'))
    errs = check(data) + check_sources(src)
    pages = {OUT_LESSONS: render_lessons(data), OUT_ASSETS: render_assets(data), OUT_SOURCES: render_sources(src)}
    if only_check:
        for p, txt in pages.items():
            cur = _read(os.path.relpath(p, ROOT))
            if cur != txt: errs.append('%s is stale — run python3 scripts/knowledge.py' % os.path.relpath(p, ROOT))
    for e in errs: print('  ✗ ' + e)
    c = collections.Counter(l['status'] for l in data['lessons'])
    print('knowledge: %d lessons (%s), %d assets, %d sources, %d problem(s)' % (
        len(data['lessons']), ', '.join('%s %d' % (s, c.get(s, 0)) for s in STATUS), len(data.get('assets', [])),
        len(src.get('sources', [])), len(errs)))
    if LEFT_OUT: print('  (%d references point at paths this branch leaves out — scripts/main-excludes.txt; checked on multi-city)' % len(LEFT_OUT))
    if errs: sys.exit(1)
    if not only_check:
        for p, txt in pages.items():
            open(p, 'w', encoding='utf-8').write(txt)
        print('wrote ' + ', '.join(os.path.relpath(p, ROOT) for p in pages))

if __name__ == '__main__':
    main()
