#!/usr/bin/env python3
"""
builddocs.py — 从 content/*.txt 重新生成对外说明材料（HTML + PDF），输出到运营资料目录（见下）。目前只做 Kamloops。

为什么存在：这批 PDF 原来是手工排版、没有源文件，改一句话都要动 PDF 内部。
现在正文写在 content/ 里的纯文本源里，数字（地点数、办事卡数、版本号、核实日期）
在构建时从 cities/kamloops/（经 kamdata）和 public/index.html 现取，改完跑一次就全部同步。

用法：
    python3 outreach/pdf/builddocs.py                 # 全部重建
    python3 outreach/pdf/builddocs.py zh-complete     # 只建一份（按文件名前缀）
    python3 outreach/pdf/builddocs.py --html-only     # 只出 HTML，不调 Chromium
    python3 outreach/pdf/builddocs.py --values        # 只核对 PDF 要印的每个数字都取得到（check-all 用）
    python3 outreach/pdf/builddocs.py --into 2026-09-16b   # 重建进已有的那一批（不新建目录）
    python3 outreach/pdf/builddocs.py --date 2026-09-16    # 指定日期（默认按 Kamloops 当地日期）

输出目录：<运营资料目录>/public/YYYY-MM-DD（默认是仓库同级的 "<仓库名> - ops"），同一天的第二批自动变成 …-DDb、…-DDc，
从不覆盖已有目录。

依赖：playwright（仅 PDF 步骤需要）。没有它时用 --html-only，再自己在浏览器里打印。
"""
import json, os, re, sys, html, base64, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
_r = HERE
for _ in range(6):
    if os.path.exists(os.path.join(_r, 'kamdata.py')): break
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
import kamdata

ROOT = kamdata.ROOT
CONTENT = os.path.join(HERE, 'content')
ASSETS = os.path.join(HERE, 'assets')
BUILDDIR = os.path.join(HERE, '_build')      # 中间产物 HTML，不进对外目录
# 2026-10-03（决策 D4）：对外成品移出代码仓库，放到同级的运营资料目录。
# 可用环境变量 LIFEGUIDE_OPS 指向别处（比如 iCloud 里的文件夹）。
OPS_DIR = kamdata.ops_dir()
PUBDIR = os.path.join(OPS_DIR, 'public')

def today():
    return kamdata.today().isoformat()     # 按 Kamloops 当地日期，见 kamdata.today

def out_dir(date_str=None, into=None):
    """本批产物的目录。

    命名沿用项目里已有的"日期 + 字母"惯例（版本号 2026.09.13f、报告 2026-09-07g）：
    当天第一批是 2026-09-16，同一天再出一批就是 2026-09-16b、2026-09-16c……
    绝不覆盖已存在的目录——旧批次是留着对照的，覆盖了就看不出变化了。
    """
    if into:
        return os.path.join(PUBDIR, into)
    d = date_str or today()
    if not os.path.exists(os.path.join(PUBDIR, d)):
        return os.path.join(PUBDIR, d)
    for ch in 'bcdefghijklmnopqrstuvwxyz':
        p = os.path.join(PUBDIR, d + ch)
        if not os.path.exists(p):
            return p
    raise SystemExit('%s 这一天已经有 26 批了，先整理一下再建' % d)

# ---------------------------------------------------------------- live values
def live_values():
    """现取事实，绝不写死：数错一个数字就会毁掉'每个数字都可核实'这件事。"""
    P, TASKS, BR = kamdata.load_all('P', 'TASKS', 'BR')
    places, tasks = len(P), len(TASKS)
    areas = len({p['g'] for p in P if p.get('g')})
    # 站名去重：475 是停靠条目数，同一个站被多条线经过会重复计数
    stops = len({st[0] for r in BR.values() for st in r.get('s', [])})
    approx = sum(1 for p in P if p.get('precision') == 'low')
    themes = len({t for p in P for t in (p.get('t') or [])})
    page = open(os.path.join(ROOT, 'public', 'index.html'), encoding='utf-8').read()
    version = re.search(r"VERSION='([^']+)'", page).group(1)
    # 2026-10-19: the engine split moved this into the city data (CITY.verified); the old page regex found nothing and
    # the first PDF build after the split crashed. Read the fact where it lives now (L-131).
    verified = kamdata.city_obj().get('verified') or ''
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', verified):
        sys.exit('builddocs: CITY.verified is %r, expected YYYY-MM-DD' % verified)
    defined = kamdata.load('CI', engine=True)
    # 只数真正有地点的分类：CI 里可能留着尚无地点的分类（如 cafe），
    # 说"地点分为 N 个分类"时把空分类算进去是不准的。
    cats = len({p['c'] for p in P if p.get('c')} & set(defined))
    d = kamdata.today()
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    return dict(PLACES=str(places), TASKS=str(tasks), VERSION=version, VERIFIED=verified,
                PREPARED='%s %d' % (months[d.month - 1], d.year), PREPARED_ZH='%d 年 %d 月' % (d.year, d.month),
                CATS=str(cats), AREAS=str(areas), ROUTES=str(len(BR)), STOPS=str(stops),
                APPROX=str(approx), THEMES=str(themes),
                URL='https://kamloops-lifemap.neilxiang.workers.dev',
                EMAIL='neilxiang@hotmail.com')

# ---------------------------------------------------------------- CSS (shared)
CSS = """
@page { size: Letter; margin: 48pt 48pt 40pt 48pt; }
:root{
  --ink:#1C1C1E; --ink-2:#3A3A3C; --sub:#6E6E73;
  /* 图形用蓝 = 传单的系统蓝，两边并排看是同一个蓝；
     文字用蓝保持更深的一档，#007AFF 在白底上对正文链接的对比度不够。 */
  --blue:#007AFF; --blue-ink:#0B6BE0; --blue-deep:#0A3D7A;
  /* 传单的六色（CARD_COLORS，顺序一致）：六种语言、编号步骤共用同一套含义 */
  --c1:#007AFF; --c2:#34C759; --c3:#FF9500; --c4:#FF2D55; --c5:#AF52DE; --c6:#5AC8FA;
  --rule:#E5E5EA; --rule-2:#D1D1D6; --panel:#F2F2F7; --panel-blue:#F2F6FC;
}
*{box-sizing:border-box;}
html,body{margin:0;padding:0;}
body{
  font-family:"Helvetica Neue",Helvetica,Arial,"PingFang SC","Noto Sans CJK SC",
              "Source Han Sans SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  font-size:10.6pt; line-height:1.55; color:var(--ink);
  -webkit-print-color-adjust:exact; print-color-adjust:exact;
}
.eyebrow{font-size:7.5pt;letter-spacing:.18em;text-transform:uppercase;color:var(--blue-deep);
  font-weight:600;margin:0 0 6pt;}
h1.title{font-size:24pt;line-height:1.15;margin:0 0 8pt;font-weight:700;letter-spacing:-.01em;}
p.lead{font-size:10.6pt;color:var(--ink-2);margin:0 0 10pt;max-width:44em;}
p.meta{font-size:8.6pt;color:var(--sub);margin:0 0 4pt;}
p.meta a{color:var(--sub);text-decoration:none;}

.stats{display:flex;gap:16pt;margin:16pt 0 18pt;}
.stat{flex:1;border-top:2.2pt solid var(--blue);padding-top:6pt;}
.stat .n{font-size:20pt;font-weight:700;line-height:1.1;letter-spacing:-.02em;}
.stat .c{font-size:8pt;color:var(--sub);line-height:1.4;margin-top:3pt;}

h2{font-size:14pt;font-weight:700;margin:18pt 0 8pt;letter-spacing:-.01em;
   break-after:avoid;page-break-after:avoid;}
h3{font-size:11.2pt;font-weight:700;margin:13pt 0 5pt;break-after:avoid;page-break-after:avoid;}
p{margin:0 0 7pt;}
strong{font-weight:700;}
a{color:var(--blue-ink);text-decoration:none;word-break:break-word;}

ul.marks{margin:0 0 8pt;padding-left:0;list-style:none;}
ul.marks li{position:relative;padding-left:12pt;margin:0 0 5pt;}
ul.marks li::before{content:"";position:absolute;left:2pt;top:.55em;width:3.4pt;height:3.4pt;
  border-radius:50%;background:var(--blue);}

table{width:100%;border-collapse:collapse;margin:0 0 10pt;font-size:9.4pt;}
th{text-align:left;font-weight:700;font-size:8.6pt;color:var(--sub);
   border-bottom:1pt solid var(--rule-2);padding:0 8pt 4pt 0;}
td{vertical-align:top;border-bottom:.6pt solid var(--rule);padding:5pt 8pt 5pt 0;}
td:first-child{width:27%;font-weight:600;padding-right:12pt;}
tr{break-inside:avoid;page-break-inside:avoid;}

dl.kv{margin:0 0 10pt;}
dl.kv .row{display:flex;gap:12pt;border-bottom:.6pt solid var(--rule);padding:5pt 0;
  break-inside:avoid;page-break-inside:avoid;}
dl.kv .k{width:27%;font-weight:600;font-size:9.4pt;}
dl.kv .v{flex:1;font-size:9.4pt;}

figure{margin:10pt 0 12pt;break-inside:avoid;page-break-inside:avoid;}
figure img{width:100%;height:auto;display:block;border:.6pt solid var(--rule-2);border-radius:4pt;}
figure.phone{float:right;width:20%;margin:2pt 0 8pt 14pt;}
figure.phone img{border-radius:8pt;}
figcaption{font-size:7.5pt;color:var(--sub);margin-top:4pt;line-height:1.4;}

.cards{display:grid;grid-template-columns:1fr 1fr;gap:8pt 14pt;background:var(--panel-blue);
  border-radius:6pt;padding:11pt 13pt;margin:0 0 12pt;break-inside:avoid;page-break-inside:avoid;}
.cards .ct{font-weight:700;font-size:9.6pt;margin-bottom:2pt;}
.cards .cb{font-size:8.8pt;color:var(--ink-2);line-height:1.5;}
.panel{background:var(--panel-blue);border-radius:6pt;padding:10pt 12pt;margin:0 0 10pt;
  break-inside:avoid;page-break-inside:avoid;}
.panel h3{margin-top:0;}
.note{font-size:8.6pt;color:var(--sub);}
.qrfig{float:right;width:104pt;margin:0 0 8pt 16pt;text-align:center;}
.qrfig img{width:104pt;height:104pt;border:none;border-radius:0;}
.qrfig figcaption{margin-top:3pt;}
.clear{clear:both;}
body.tight{line-height:1.5;}
body.tight h2{margin:13pt 0 6pt;}
body.tight h3{margin:10pt 0 4pt;}
body.tight p{margin:0 0 5.5pt;}
body.tight .stats{margin:12pt 0 13pt;}
body.tight ul.marks li{margin:0 0 4pt;}
body.tight .cards{padding:9pt 12pt;margin:0 0 9pt;gap:6pt 14pt;}
body.tight figure{margin:8pt 0 9pt;}
body.tight .legal{margin-top:10pt;padding-top:6pt;}
/* 六种语言：与传单同一套颜色、同一个含义。黑白打印时文字本身仍在。 */
.lg i{font-style:normal;font-weight:700;}
.lg i:nth-of-type(1){color:var(--c1);} .lg i:nth-of-type(2){color:var(--c2);}
.lg i:nth-of-type(3){color:var(--c3);} .lg i:nth-of-type(4){color:var(--c4);}
.lg i:nth-of-type(5){color:var(--c5);} .lg i:nth-of-type(6){color:var(--c6);}
.lg s{text-decoration:none;color:#AEAEB2;}
/* 编号步骤：沿用传单的编号圆点。灰度打印下圆点变灰，数字照样读得出。 */
ol.steps{margin:0 0 8pt;padding-left:0;list-style:none;counter-reset:st;}
ol.steps li{position:relative;padding-left:17pt;margin:0 0 6pt;counter-increment:st;
  break-inside:avoid;page-break-inside:avoid;}
ol.steps li::before{content:counter(st);position:absolute;left:0;top:.18em;
  width:11.5pt;height:11.5pt;border-radius:50%;background:var(--c1);color:#fff;
  font-size:7.4pt;font-weight:700;line-height:11.5pt;text-align:center;}
ol.steps li:nth-child(2)::before{background:var(--c2);}
ol.steps li:nth-child(3)::before{background:var(--c3);}
ol.steps li:nth-child(4)::before{background:var(--c4);}
ol.steps li:nth-child(5)::before{background:var(--c5);}
ol.steps li:nth-child(6)::before{background:var(--c6);}
body.tight ol.steps li{margin:0 0 5pt;}
.legal{font-size:7.5pt;color:var(--sub);line-height:1.5;margin-top:14pt;
  border-top:.6pt solid var(--rule);padding-top:8pt;}
.closing{background:var(--panel);border-radius:6pt;padding:10pt 12pt;margin:12pt 0 0;
  font-size:9.4pt;color:var(--ink-2);}
"""

FOOT_TPL = ('<div style="font-size:7pt;color:#6E6E73;width:100%;padding:0 48pt;'
            'display:flex;justify-content:space-between;">'
            '<span>{foot}</span>'
            '<span><span class="pageNumber"></span>/<span class="totalPages"></span></span>'
            '</div>')

# ---------------------------------------------------------------- content parse
def parse(path, vals):
    """极简块语法 -> (meta, blocks)。刻意保持可读，方便以后直接改正文。"""
    raw = open(path, encoding='utf-8').read()
    for k, v in vals.items():
        raw = raw.replace('{%s}' % k, v)
    meta, blocks, cur = {}, [], None
    lines = raw.split('\n')
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if s.startswith('@'):
            tag, _, rest = s[1:].partition(' ')
            rest = rest.strip()
            if tag == 'meta':
                cur = ('meta', [])
            elif tag in ('stats', 'table', 'kv', 'marks', 'panel', 'closing', 'cards', 'steps'):
                cur = (tag, [])
                blocks.append(cur)
            elif tag == 'h2':
                blocks.append(('h2', rest)); cur = None
            elif tag == 'h3':
                blocks.append(('h3', rest)); cur = None
            elif tag == 'p':
                blocks.append(('p', rest)); cur = None
            elif tag == 'note':
                blocks.append(('note', rest)); cur = None
            elif tag == 'legal':
                blocks.append(('legal', rest)); cur = None
            elif tag == 'figure':
                blocks.append(('figure', rest)); cur = None
            elif tag == 'phone':
                blocks.append(('phone', rest)); cur = None
            elif tag == 'qr':
                blocks.append(('qr', rest)); cur = None
            elif tag == 'clear':
                blocks.append(('clear', '')); cur = None
            elif tag == 'pagebreak':
                blocks.append(('pagebreak', '')); cur = None
            else:
                raise SystemExit(f'unknown tag @{tag} in {os.path.basename(path)}')
        elif s == '':
            pass
        elif cur and cur[0] == 'meta':
            k, _, v = s.partition(':')
            meta[k.strip()] = v.strip()
        elif cur:
            cur[1].append(s)
        else:
            blocks.append(('p', s))
        i += 1
    return meta, blocks

def _langs(m):
    """<<EN · FR · ...>> -> 每一项按传单的六色依次上色，分隔符保持灰色。"""
    parts = re.split(r'(\s*[·・]\s*)', m.group(1))
    outs = []
    for seg in parts:
        if re.fullmatch(r'\s*[·・]\s*', seg):
            outs.append('<s>%s</s>' % seg)
        elif seg.strip():
            outs.append('<i>%s</i>' % seg)
    return '<span class="lg">%s</span>' % ''.join(outs)

def md(t):
    """**粗体**、[文字](链接)、<<按语言上色>>；其余按纯文本转义。"""
    t = html.escape(t)
    t = re.sub(r'&lt;&lt;(.+?)&gt;&gt;', _langs, t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    return t

def img_data(name):
    p = os.path.join(ASSETS, name)
    ext = 'png' if name.endswith('.png') else 'jpeg'
    return 'data:image/%s;base64,%s' % (ext, base64.b64encode(open(p, 'rb').read()).decode())

def render(meta, blocks, vals):
    out = []
    for kind, body in blocks:
        if kind == 'h2':
            out.append(f'<h2>{md(body)}</h2>')
        elif kind == 'h3':
            out.append(f'<h3>{md(body)}</h3>')
        elif kind == 'p':
            out.append(f'<p>{md(body)}</p>')
        elif kind == 'note':
            out.append(f'<p class="note">{md(body)}</p>')
        elif kind == 'legal':
            out.append(f'<p class="legal">{md(body)}</p>')
        elif kind == 'clear':
            out.append('<div class="clear"></div>')
        elif kind == 'pagebreak':
            out.append('<div style="break-before:page;page-break-before:always;"></div>')
        elif kind == 'figure':
            src, _, cap = body.partition('|')
            out.append('<figure><img src="%s">%s</figure>' % (
                img_data(src.strip()),
                f'<figcaption>{md(cap.strip())}</figcaption>' if cap.strip() else ''))
        elif kind == 'qr':
            src, _, cap = body.partition('|')
            out.append('<figure class="qrfig"><img src="%s">%s</figure>' % (
                img_data(src.strip()),
                f'<figcaption>{md(cap.strip())}</figcaption>' if cap.strip() else ''))
        elif kind == 'phone':
            src, _, cap = body.partition('|')
            out.append('<figure class="phone"><img src="%s">%s</figure>' % (
                img_data(src.strip()),
                f'<figcaption>{md(cap.strip())}</figcaption>' if cap.strip() else ''))
        elif kind == 'stats':
            cells = []
            for row in body:
                n, _, c = row.partition('|')
                cells.append(f'<div class="stat"><div class="n">{md(n.strip())}</div>'
                             f'<div class="c">{md(c.strip())}</div></div>')
            out.append('<div class="stats">%s</div>' % ''.join(cells))
        elif kind == 'table':
            head, *rows = body
            hs = ''.join(f'<th>{md(c.strip())}</th>' for c in head.split('|'))
            rs = ''.join('<tr>%s</tr>' % ''.join(f'<td>{md(c.strip())}</td>' for c in r.split('|'))
                         for r in rows)
            out.append(f'<table><thead><tr>{hs}</tr></thead><tbody>{rs}</tbody></table>')
        elif kind == 'kv':
            rows = ''.join('<div class="row"><div class="k">%s</div><div class="v">%s</div></div>'
                           % (md(r.split('|')[0].strip()), md(r.split('|', 1)[1].strip()))
                           for r in body)
            out.append(f'<dl class="kv">{rows}</dl>')
        elif kind == 'marks':
            out.append('<ul class="marks">%s</ul>'
                       % ''.join(f'<li>{md(r)}</li>' for r in body))
        elif kind == 'steps':
            out.append('<ol class="steps">%s</ol>'
                       % ''.join(f'<li>{md(r)}</li>' for r in body))
        elif kind == 'cards':
            cells = []
            for row in body:
                t, _, d = row.partition('|')
                cells.append('<div class="card"><div class="ct">%s</div><div class="cb">%s</div></div>'
                             % (md(t.strip()), md(d.strip())))
            out.append('<div class="cards">%s</div>' % ''.join(cells))
        elif kind == 'panel':
            inner = ''.join(f'<p>{md(r)}</p>' for r in body)
            out.append(f'<div class="panel">{inner}</div>')
        elif kind == 'closing':
            inner = ''.join(f'<p style="margin:0">{md(r)}</p>' for r in body)
            out.append(f'<div class="closing">{inner}</div>')
    head = []
    if meta.get('eyebrow'):
        head.append(f'<p class="eyebrow">{md(meta["eyebrow"])}</p>')
    head.append(f'<h1 class="title">{md(meta["title"])}</h1>')
    if meta.get('lead'):
        head.append(f'<p class="lead">{md(meta["lead"])}</p>')
    if meta.get('meta'):
        head.append(f'<p class="meta">{md(meta["meta"])}</p>')
    return ('<!DOCTYPE html><html lang="%s"><head><meta charset="utf-8">'
            '<title>%s</title><style>%s</style></head><body class="%s">%s%s</body></html>'
            % (meta.get('lang', 'zh'), html.escape(meta['title']), CSS,
               meta.get('density', ''), ''.join(head), ''.join(out)))

def build(name, vals, html_only=False, outdir=None):
    meta, blocks = parse(os.path.join(CONTENT, name + '.txt'), vals)
    doc = render(meta, blocks, vals)
    outdir = outdir or out_dir()
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(BUILDDIR, exist_ok=True)
    hp = os.path.join(BUILDDIR, meta['out'] + '.html')
    open(hp, 'w', encoding='utf-8').write(doc)
    if html_only:
        return hp, None
    from playwright.sync_api import sync_playwright
    pdfp = os.path.join(outdir, meta['out'] + '.pdf')
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        pg.set_content(doc, wait_until='load')
        pg.emulate_media(media='print')
        pg.pdf(path=pdfp, format='Letter', print_background=True,
               margin={'top': '0.667in', 'bottom': '0.56in', 'left': '0.667in', 'right': '0.667in'},
               display_header_footer=True,
               header_template='<div></div>',
               footer_template=FOOT_TPL.format(foot=html.escape(meta.get('foot', ''))))
        b.close()
    return hp, pdfp

def _opt(flag):
    """--flag=value 或 --flag value"""
    for i, a in enumerate(sys.argv):
        if a == flag and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        if a.startswith(flag + '='):
            return a.split('=', 1)[1]
    return None

def main():
    skip = set()
    for flag in ('--date', '--into'):
        v = _opt(flag)
        if v:
            skip.add(v)
    args = [a for a in sys.argv[1:] if not a.startswith('--') and a not in skip]
    html_only = '--html-only' in sys.argv
    vals = live_values()
    if '--values' in sys.argv:          # check-all: every value the PDFs print can still be read (no network, no files)
        print('outreach values:', vals); return
    # 2026-10-04: the version printed on a PDF must be one a reader can actually open. public/index.html is a build,
    # not necessarily what is deployed (on 2026-10-04 it was 2026.10.04a while the site served 2026.09.24b).
    # Checked before anything is written; if the live version cannot be read, PDFs are not built (fail closed).
    if not html_only and '--allow-undeployed' not in sys.argv:
        import urllib.request, ssl
        try:
            import certifi; ctx = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            ctx = ssl.create_default_context(cafile='/etc/ssl/cert.pem') if os.path.exists('/etc/ssl/cert.pem') else None
        try:
            req = urllib.request.Request(vals['URL'] + '/', headers={'User-Agent': 'Mozilla/5.0 (builddocs version check)'})
            live = urllib.request.urlopen(req, timeout=15, context=ctx).read().decode('utf-8', 'replace')
            lv = re.search(r"DATA_VERSION='([^']+)'", live)
        except Exception as e:
            sys.exit('builddocs: could not read the live version (%s); PDFs not built. Pass --allow-undeployed for a draft '
                     'that will not be handed out' % e)
        if not lv or lv.group(1) != vals['VERSION']:
            sys.exit('builddocs: public/index.html is %s but the live site serves %s — deploy first, or pass '
                     '--allow-undeployed for a draft that will not be handed out' % (vals['VERSION'], lv.group(1) if lv else '?'))
    print('live values:', vals)
    outdir = out_dir(_opt('--date'), _opt('--into'))
    if not html_only:
        print('out dir:', os.path.relpath(outdir, ROOT))
    names = sorted(f[:-4] for f in os.listdir(CONTENT) if f.endswith('.txt'))
    if args:
        names = [n for n in names if any(n.startswith(a) for a in args)]
    for n in names:
        hp, pdfp = build(n, vals, html_only, outdir)
        print('built', os.path.basename(pdfp or hp))

if __name__ == '__main__':
    main()
