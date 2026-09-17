#!/usr/bin/env python3
"""kamdata.py — 一个地方读写 src/data-kamloops.js，别的脚本都从这里取。

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
    CI = kamdata.load('CI', engine=True)  # 分类（在 engine.html 里）
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
    """向上找到项目根（放着 src/data-kamloops.js 的那一层），不写死层级。"""
    p = start or os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.exists(os.path.join(p, 'src', 'data-kamloops.js')):
            return p
        p = os.path.dirname(p)
    raise SystemExit('找不到项目根目录（需要 src/data-kamloops.js）')

ROOT = root()
DATA = os.path.join(ROOT, 'src', 'data-kamloops.js')
ENGINE = os.path.join(ROOT, 'src', 'engine.html')

def _src(engine=False):
    return open(ENGINE if engine else DATA, encoding='utf-8').read()

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
    path = ENGINE if engine else DATA
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
