#!/usr/bin/env python3
"""The knowledge base: one registry of lessons, kept honest by the code it points at.

    python3 scripts/knowledge.py            # check, then (re)write docs/knowledge/经验库.md and 资产清单.md
    python3 scripts/knowledge.py --check    # check only; fails if anything is wrong or the pages are stale

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

AREAS = ['分发与运营', '数据来源与核实', '坐标与地址', '营业时间', '导入与合并', '引擎与城市分离', '测试与门禁',
         '多语言', '搜索与交互', '安全、法律与隐私', '部署与运维', '方法与流程']
STATUS = {'auto': '✅ 自动检查', 'tool': '🔧 工具保证', 'doc': '📄 只有文档', 'todo': '⏳ 待落实'}
AUTO_KINDS = {'validate', 'test', 'check', 'gate'}
KINDS = AUTO_KINDS | {'importer', 'tool', 'engine', 'doc', 'prompt', 'data'}
SCOPES = {'all': '所有城市', 'CA': '加拿大', 'BC': 'BC 省', 'city': '单个城市'}

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
            t = _read(e.get('ref', ''))
            if t is None: errs.append('%s: evidence file missing: %s' % (lid, e.get('ref')))
            elif e.get('section') and e['section'] not in t: errs.append('%s: section %r not in %s' % (lid, e['section'], e['ref']))
        kinds = set()
        for c in l.get('encoded', []):
            kinds.add(c.get('kind'))
            if c.get('kind') not in KINDS: errs.append('%s: unknown encoded kind %r' % (lid, c.get('kind')))
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
    for a in data.get('assets', []):
        for p in a.get('paths', []):
            if not os.path.exists(os.path.join(ROOT, p)): errs.append('asset %r: %s not found' % (a.get('name'), p))
    return errs

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

def main():
    only_check = '--check' in sys.argv
    data = json.load(open(SRC, encoding='utf-8'))
    errs = check(data)
    pages = {OUT_LESSONS: render_lessons(data), OUT_ASSETS: render_assets(data)}
    if only_check:
        for p, txt in pages.items():
            cur = _read(os.path.relpath(p, ROOT))
            if cur != txt: errs.append('%s is stale — run python3 scripts/knowledge.py' % os.path.relpath(p, ROOT))
    for e in errs: print('  ✗ ' + e)
    c = collections.Counter(l['status'] for l in data['lessons'])
    print('knowledge: %d lessons (%s), %d assets, %d problem(s)' % (
        len(data['lessons']), ', '.join('%s %d' % (s, c.get(s, 0)) for s in STATUS), len(data.get('assets', [])), len(errs)))
    if errs: sys.exit(1)
    if not only_check:
        for p, txt in pages.items():
            open(p, 'w', encoding='utf-8').write(txt)
        print('wrote %s, %s' % (os.path.relpath(OUT_LESSONS, ROOT), os.path.relpath(OUT_ASSETS, ROOT)))

if __name__ == '__main__':
    main()
