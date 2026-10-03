#!/usr/bin/env python3
r"""kamdata.py — 一个地方读写城市数据和引擎源码，别的脚本都从这里取。

2026-10-03（多城市阶段 2）：城市数据从 src/data-kamloops.js 拆到 cities/<city>/：
data.js 是手写部分（注释、CITY、LANDMARK_GLOSS…），大块数据放在 places.json 等
独立 JSON 里，data.js 用 /*@json 文件名*/ 引用，guideCity 长文用 /*@text guide/<lang>.html*/。
data_text() 把它们展开回原来的完整 JS（与拆分前逐字节相同）；load/save 直接读写 JSON 文件。

以下是原来的说明：

为什么存在：在这之前，九个脚本各写了一遍
`json.loads(re.search(r'const P=(\[.*?\]);', ...))`，其中四个还会把结果写回去，
而且都用相对当前目录的 'src/data-kamloops.js' ——
在别的目录下跑，轻则 FileNotFoundError，重则写进另一个同名文件。
正则也有九个变体（`;\n` / `;` / `;\s*\n`），都悄悄依赖同一条不成文的约定：
`];` 只在语句结尾出现。这些现在只有这一份。

用法（任何位置的脚本都一样）：

    import os, sys
    _r = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.exists(os.path.join(_r, 'kamdata.py')): break
        _r = os.path.dirname(_r)
    sys.path.insert(0, _r)
    import kamdata

    P = kamdata.load('P')                 # 地点
    TASKS = kamdata.load('TASKS')         # 办事卡
    BR = kamdata.load('BR')               # 公交线
    CI = kamdata.load('CI', engine=True)  # 分类（在引擎 app/engine/ 里）
    kamdata.save('P', P)                  # 原地写回，只替换那一段
"""
import datetime, json, os, re

def today():
    """Kamloops 当地日期。

    构建和巡检可能跑在任何时区的机器上（云端容器是 UTC），
    用机器的 date 会在当地傍晚之后跳到第二天——目录名和报告名都因此错过一次。
    """
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo('America/Vancouver')).date()
    except Exception:
        return datetime.date.today()

def root(start=None):
    """向上找到项目根（放着 app/engine/parts.txt 的那一层），不写死层级。"""
    p = start or os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.exists(os.path.join(p, 'app', 'engine', 'parts.txt')):
            return p
        p = os.path.dirname(p)
    raise SystemExit('找不到项目根目录（需要 app/engine/parts.txt）')

ROOT = root()
CITY = 'kamloops'                    # 默认城市；阶段 3 起各脚本用 --city 覆盖

def city_dir(city=None):
    return os.path.join(ROOT, 'cities', city or CITY)

def data_template(city=None):
    return os.path.join(city_dir(city), 'data.js')

DATA = data_template()               # 兼容旧代码：手写部分所在的文件

# 大块数据各自一个 JSON 文件；"lines" 表示构建时数组一条记录一行（P 一直如此）
JSON_FILES = {'RI': 'regions.json', 'P': 'places.json', 'QUARANTINE': 'quarantine.json',
              'BR': 'bus-routes.json', 'LANDMARKS': 'landmarks.json', 'TASKS': 'tasks.json'}
_INCLUDE = re.compile(r'/\*@(json|text) ([^ *]+)( lines)?\*/')

def data_text(city=None):
    """完整的城市数据 JS：data.js 里的 /*@json*/ /*@text*/ 展开后的结果。"""
    d = city_dir(city)
    def expand(m):
        kind, rel, lines = m.group(1), m.group(2), bool(m.group(3))
        path = os.path.join(d, rel)
        if kind == 'text':
            return open(path, encoding='utf-8').read()
        return dumps(json.load(open(path, encoding='utf-8')), lines)
    return _INCLUDE.sub(expand, open(data_template(city), encoding='utf-8').read())

def data_files(city=None):
    """城市数据涉及的全部源文件（data.js + 它引用的文件）。"""
    d = city_dir(city)
    t = open(data_template(city), encoding='utf-8').read()
    return [data_template(city)] + [os.path.join(d, m.group(2)) for m in _INCLUDE.finditer(t)]

def data_mtime(city=None):
    return max(os.path.getmtime(p) for p in data_files(city))
ENGINE_DIR = os.path.join(ROOT, 'app', 'engine')

def engine_parts():
    """引擎各部分的路径，按拼接顺序（app/engine/parts.txt）。2026-10-03 起
    src/engine.html 拆成了这些文件；拼起来就是原来那个完整的 HTML。"""
    lst = os.path.join(ENGINE_DIR, 'parts.txt')
    names = [l.strip() for l in open(lst, encoding='utf-8')
             if l.strip() and not l.lstrip().startswith('#')]
    return [os.path.join(ENGINE_DIR, n) for n in names]

def engine_text():
    """完整的引擎 HTML（各部分按顺序拼接）。"""
    return ''.join(open(p, encoding='utf-8').read() for p in engine_parts())

def engine_mtime():
    return max(os.path.getmtime(p) for p in engine_parts() + [os.path.join(ENGINE_DIR, 'parts.txt')])

def _src(engine=False):
    return engine_text() if engine else data_text()

def _span(text, name):
    """返回 const <name>= 后面那个 JSON 字面量的 (start, end)。

    用括号配平扫描，不用非贪婪正则：正则要求 `];` 只在结尾出现，
    备注里多一个 `]` 就会截错，而且截错的时候是静默的。
    """
    m = re.search(r'const\s+%s\s*=\s*([\[{])' % re.escape(name), text)
    if not m:
        raise SystemExit('在数据文件里找不到 const %s=' % name)
    open_ch = m.group(1)
    close_ch = ']' if open_ch == '[' else '}'
    i = m.end(1)
    depth, in_str, esc = 1, False, False
    while i < len(text):
        c = text[i]
        if in_str:
            if esc:            esc = False
            elif c == '\\':    esc = True
            elif c == '"':     in_str = False
        elif c == '"':         in_str = True
        elif c == open_ch:     depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return m.start(1), i + 1
        i += 1
    raise SystemExit('const %s= 的括号没有配平，数据文件可能坏了' % name)

def load(name, engine=False):
    """读出一个顶层常量（P / TASKS / BR / RI / CI…）。"""
    if not engine and name in JSON_FILES:
        return json.load(open(os.path.join(city_dir(), JSON_FILES[name]), encoding='utf-8'))
    text = _src(engine)
    a, b = _span(text, name)
    return json.loads(text[a:b])

def load_all(*names, engine=False):
    """一次读多个，只读一遍文件。"""
    text = _src(engine)
    out = []
    for n in names:
        a, b = _span(text, n)
        out.append(json.loads(text[a:b]))
    return out

def dumps(value, one_per_line=False):
    """紧凑 JSON。one_per_line=True 时数组每个元素各占一行。"""
    if one_per_line and isinstance(value, list):
        return '[' + ',\n'.join(
            json.dumps(v, ensure_ascii=False, separators=(',', ':')) for v in value) + ']'
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))

def save(name, value, engine=False):
    """把一个顶层常量写回原文件，只替换它那一段，其余字节不动。

    排版跟着原来的来：P 本来是一条记录一行（`},\n{`），
    如果统统压成一行，改一个字段的 diff 会变成整个 45 万字符的行，没法看。
    """
    if not engine and name in JSON_FILES:
        # 独立 JSON 文件：整份重写，缩进一格，一个字段一行，diff 只落在改动的那几行
        path = os.path.join(city_dir(), JSON_FILES[name])
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=1)
            f.write('\n')
        return path
    if engine:
        # the constant lives in exactly one engine part; find it and edit only that file
        hits = [p for p in engine_parts()
                if re.search(r'const\s+%s\s*=' % re.escape(name), open(p, encoding='utf-8').read())]
        if len(hits) != 1:
            raise SystemExit('const %s 在引擎里出现在 %d 个文件中' % (name, len(hits)))
        path = hits[0]
    else:
        path = DATA
    text = open(path, encoding='utf-8').read()
    a, b = _span(text, name)
    one_per_line = '},\n{' in text[a:b]
    new = dumps(value, one_per_line)
    open(path, 'w', encoding='utf-8').write(text[:a] + new + text[b:])
    return path

# --- 数据约定：写在这里，让别的脚本可以引用，而不是各自记一遍 -----------------
V_RE = re.compile(r'^\d{4}-\d{2}$')   # 核实日期只到月：YYYY-MM

def bad_v(places):
    """返回 v 字段不符合 YYYY-MM 的记录。不合规不等于过期，要分开报。"""
    return [p for p in places if not V_RE.match(p.get('v') or '')]

if __name__ == '__main__':
    P, TASKS, BR = load_all('P', 'TASKS', 'BR')
    print('root  :', ROOT)
    print('places:', len(P), ' tasks:', len(TASKS), ' routes:', len(BR))
    print('cats  :', len(load('CI', engine=True)))
    bad = bad_v(P)
    print('v 不合规:', [(p['n'], p.get('v')) for p in bad] or '无')
