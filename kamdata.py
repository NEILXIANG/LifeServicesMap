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

def today(city=None):
    """城市当地日期（时区取 city.json 的 "timezone"，不写就是 America/Vancouver）。

    构建和巡检可能跑在任何时区的机器上（云端容器是 UTC），
    用机器的 date 会在当地傍晚之后跳到第二天——目录名和报告名都因此错过一次。

    2026-10-04：BC 从 2026-11-01 起全年夏令时（不再回拨，UTC-7）。机器的时区数据如果还是旧的，
    会在那天之后退回 UTC-8，这里按 UTC-7 纠正（与引擎 15-time-open-now.js 同一规则）。
    """
    try:
        tz = city_meta(city).get('timezone') or 'America/Vancouver'
    except Exception:
        tz = 'America/Vancouver'
    try:
        from zoneinfo import ZoneInfo
        now = datetime.datetime.now(ZoneInfo(tz))
        cutover = datetime.datetime(2026, 11, 1, 9, tzinfo=datetime.timezone.utc)
        if tz == 'America/Vancouver' and now >= cutover and now.utcoffset() == datetime.timedelta(hours=-8):
            now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-7)))
        return now.date()
    except Exception:
        return datetime.date.today()

def month(city=None):
    """核实月份 v 的格式（YYYY-MM），按城市当地日期。"""
    return today(city).strftime('%Y-%m')

def root(start=None):
    """向上找到项目根（放着 app/engine/parts.txt 的那一层），不写死层级。"""
    p = start or os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.exists(os.path.join(p, 'app', 'engine', 'parts.txt')):
            return p
        p = os.path.dirname(p)
    raise SystemExit('找不到项目根目录（需要 app/engine/parts.txt）')

ROOT = root()
# 当前城市：环境变量 LIFEGUIDE_CITY，或脚本解析 --city 后调用 use()；默认 kamloops
CITY = os.environ.get('LIFEGUIDE_CITY') or 'kamloops'

def cities():
    """cities/ 下的全部城市（以 _ 开头的是测试用城市，不算）。"""
    d = os.path.join(ROOT, 'cities')
    return sorted(c for c in os.listdir(d)
                  if not c.startswith(('_', '.')) and os.path.exists(os.path.join(d, c, 'city.json')))

def use(city):
    """切换当前城市；之后 load/save/data_text 默认都读写这座城市。"""
    global CITY, DATA
    if not os.path.exists(os.path.join(ROOT, 'cities', city, 'city.json')):
        raise SystemExit('没有这座城市：cities/%s/city.json 不存在（现有：%s）' % (city, ', '.join(cities())))
    CITY = city
    DATA = data_template(city)
    return city

def city_meta(city=None):
    """cities/<city>/city.json（构建期配置）。"""
    return json.load(open(os.path.join(city_dir(city), 'city.json'), encoding='utf-8'))

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
# 2026-10-04（脚本审计）：六种语言、导入文件路径、运营目录、证书、User-Agent 原来各脚本各写一份
# （六语列表 15 份，其中一份顺序不同；证书 4 种写法；运营目录 2 种算法）。新脚本一律用这里的。
LANGS = ['zh', 'en', 'fr', 'es', 'ko', 'ja']
USER_AGENT = 'Mozilla/5.0 (lifeguide-tools)'   # 不带 Mozilla 前缀时 workers.dev 回 403（builddocs 撞过）

def category_tiers():
    """schemas/category-tiers.json：安全相关、可不收的商业类、没有官方营业时间的类别（审核和导入脚本共用）。"""
    return json.load(open(os.path.join(ROOT, 'schemas', 'category-tiers.json'), encoding='utf-8'))

def city_obj(city=None):
    """城市的 CITY 设置（data.js 里的 JS 对象），用 node 求值。"""
    import subprocess
    js = ('const UI=new Proxy({},{get:(t,k)=>t[k]||(t[k]={})});' + data_text(city) +
          ';process.stdout.write(JSON.stringify(CITY))')
    r = subprocess.run(['node', '-'], input=js, capture_output=True, text=True)   # stdin: data is too big for argv
    if r.returncode != 0:
        raise SystemExit('node could not evaluate CITY for %s: %s' % (city or CITY, r.stderr[:300]))
    return json.loads(r.stdout)

_GENERIC_AREAS = {'Other', 'Suburbs', 'Downtown', 'North', 'South', 'East', 'West', 'Central', 'Rural', 'Outskirts'}

def fingerprint(city):
    """一座城市独有的字样：城市名、区域名、地标和 UPCC 的名字、本地电话、CITY.examples，加上 city.json 的
    "leakMarkers"（自动取不到的，如校名缩写、票价）。用来查"别城的事实"有没有漏进另一座城市（L-034）。

    2026-10-04：原来每座城市的测试手写一份别城禁用词，城市一多就是 N×(N−1) 份，漏一份就是 L-034。"""
    meta = city_meta(city); C = city_obj(city)
    out = {meta['title'].replace(' Life Guide', '')}
    out |= set(meta.get('leakMarkers', []))
    prev = CITY
    use(city)
    try:
        P = {p['id']: p['n'] for p in load('P')}
        for r in load('RI').values():
            for part in re.split(r'/', r.get('en', '').split(' (')[0]):
                if part.strip() and part.strip() not in _GENERIC_AREAS: out.add(part.strip())
        for i in load('LANDMARKS') + list(C.get('upcc') or []):
            if i in P: out.add(P[i])
    finally:
        use(prev)
    phones = [C.get('police'), (C.get('help') or {}).get('settle'), (C.get('localCrisis') or {}).get('n')]
    phones += [l.get('n') for l in C.get('localLines') or []]
    out |= {p for p in phones if p}
    out |= {v for v in (C.get('examples') or {}).values() if isinstance(v, str)}
    return sorted(out)

def leak_markers(target, others=None):
    """别的城市指纹里、target 自己的指纹里没有的字样（两城共有的如 Downtown、全区域电话自动排除）。
    不按 target 的数据排除：已经漏进 target 数据里的别城事实，正是要抓的。
    真正两城都该有的字样写进 target 的 city.json "leakAllow"。"""
    mine = set(fingerprint(target)) | set(city_meta(target).get('leakAllow', []))
    out = set()
    for c in (others if others is not None else [x for x in cities() if x != target]):
        out |= set(fingerprint(c)) - mine
    return sorted(out)

def import_path(name, city=None):
    """cities/<city>/import/<name>（导入、核实、复核的中间文件）。"""
    return os.path.join(city_dir(city), 'import', name)

def load_import(name, default=None, city=None):
    p = import_path(name, city)
    if not os.path.exists(p):
        return default
    return json.load(open(p, encoding='utf-8'))

def ops_dir():
    """运营资料目录（仓库外，决策 D4）：环境变量 LIFEGUIDE_OPS，默认同级的 "<仓库名> - ops"。"""
    return os.environ.get('LIFEGUIDE_OPS') or os.path.join(os.path.dirname(ROOT), os.path.basename(ROOT) + ' - ops')

_SSL = []
def ssl_context():
    """HTTPS 证书：python.org 版 Python 在 macOS 上不带系统根证书（2026-09-16 月度巡检所有链接都报 BLOCKED）。
    依次试 certifi、/etc/ssl/cert.pem、默认。只建一次。"""
    if not _SSL:
        import ssl
        ctx = None
        for cafile in (lambda: __import__('certifi').where(), lambda: '/etc/ssl/cert.pem'):
            try:
                ctx = ssl.create_default_context(cafile=cafile()); break
            except Exception:
                pass
        _SSL.append(ctx or ssl.create_default_context())
    return _SSL[0]
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
