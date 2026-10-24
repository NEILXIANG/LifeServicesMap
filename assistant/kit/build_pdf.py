#!/usr/bin/env python3
"""assistant/kit/build_pdf.py — 把演示脚本和机构说明（docs/assistant/kit/*.md）排成 PDF。

    .venv/bin/python assistant/kit/build_pdf.py            # → ../Guide to Life in Canada - ops/assistant-kit/<日期>/

对外成品不进仓库（CLAUDE.md），放在 ops 文件夹；源文件是仓库里的 Markdown，改了重新跑一次即可。
Markdown 只用到标题、段落、列表、表格、引用、粗体、斜体、链接，这里自带一个够用的转换，不另装库。
"""
import datetime, html, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, 'docs', 'assistant', 'kit')
sys.path.insert(0, ROOT)
import kamdata

DOCS = [('demo-questions-en.md', 'Demo-Script-EN.pdf', 'en'), ('demo-questions-zh.md', '演示脚本-中文.pdf', 'zh-Hans'),
        ('brief-en.md', 'Brief-for-Organisations-EN.pdf', 'en'), ('brief-zh.md', '给机构的说明-中文.pdf', 'zh-Hans')]


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', t)
    t = re.sub(r'(?<![">])(https?://[^\s<）)]+)', r'<a href="\1">\1</a>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])', r'<em>\1</em>', t)
    return t


def md_to_html(md):
    out, lines, i = [], md.split('\n'), 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1; continue
        m = re.match(r'^(#{1,3}) (.*)', ln)
        if m:
            n = len(m.group(1)); out.append('<h%d>%s</h%d>' % (n, inline(m.group(2)), n)); i += 1; continue
        if ln.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                # 分隔线（|---|---|）跳过；空的表头行（| | |）要保留，否则第一行数据会被当成表头
                if not (any(cells) and all(re.fullmatch(r':?-+:?', c) for c in cells)): rows.append(cells)
                i += 1
            head, body = rows[0], rows[1:]
            th = '' if not any(head) else '<thead><tr>%s</tr></thead>' % ''.join('<th>%s</th>' % inline(c) for c in head)
            out.append('<table>%s<tbody>%s</tbody></table>' % (th, ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % inline(c) for c in r) for r in body)))
            continue
        if ln.startswith('> '):
            q = []
            while i < len(lines) and lines[i].startswith('>'):
                q.append(lines[i][1:].strip()); i += 1
            out.append('<blockquote>%s</blockquote>' % inline(' '.join(q))); continue
        m = re.match(r'^(\d+)\. |^- ', ln)
        if m:
            tag = 'ol' if ln[0].isdigit() else 'ul'
            items = []
            while i < len(lines) and re.match(r'^(\d+\. |- )', lines[i]):
                items.append(re.sub(r'^(\d+\. |- )', '', lines[i])); i += 1
            out.append('<%s>%s</%s>' % (tag, ''.join('<li>%s</li>' % inline(x) for x in items), tag)); continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|\||> |\d+\. |- )', lines[i]):
            para.append(lines[i].strip()); i += 1
        out.append('<p>%s</p>' % inline(' '.join(para)))
    return '\n'.join(out)


CSS = """
@page { size: Letter; margin: 16mm 16mm 18mm; }
body { font-family: -apple-system, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif;
       color: #1c1c1e; font-size: 10.5pt; line-height: 1.5; }
h1 { font-size: 18pt; margin: 0 0 4pt; color: #0a5fc9; }
h1 + p { color: #6e6e73; font-size: 9.5pt; margin-top: 0; }
h2 { font-size: 13pt; margin: 16pt 0 6pt; border-bottom: 1px solid #d1d1d6; padding-bottom: 3pt; }
h3 { font-size: 11pt; margin: 12pt 0 4pt; }
p, li { margin: 0 0 6pt; }
ul, ol { margin: 0 0 6pt; padding-left: 18pt; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 8pt; font-size: 9.5pt; }
th, td { border: 1px solid #d1d1d6; padding: 5pt 6pt; vertical-align: top; text-align: left; }
th { background: #f2f2f7; }
td:first-child { width: 28%; }
blockquote { margin: 6pt 0; padding: 6pt 10pt; background: #f2f2f7; border-left: 3pt solid #0b6be0; }
a { color: #0a5fc9; text-decoration: none; word-break: break-all; }
h2, h3 { break-after: avoid; } table, blockquote { break-inside: avoid; }
"""


def main():
    from playwright.sync_api import sync_playwright
    day = kamdata.today().isoformat()
    out_dir = os.path.join(kamdata.ops_dir(), 'assistant-kit', day)
    os.makedirs(out_dir, exist_ok=True)
    with sync_playwright() as pw:
        # 和项目里所有浏览器启动一样屏蔽地图瓦片服务（经验 L-145；这几页本来也不加载地图）
        b = pw.chromium.launch(args=['--host-resolver-rules=MAP api.maptiler.com 127.0.0.1, MAP tiles.stadiamaps.com 127.0.0.1'])
        pg = b.new_page()
        for src, name, lang in DOCS:
            body = md_to_html(open(os.path.join(SRC, src), encoding='utf-8').read())
            pg.set_content('<!doctype html><html lang="%s"><head><meta charset="utf-8"><style>%s</style></head><body>%s</body></html>' % (lang, CSS, body))
            path = os.path.join(out_dir, name)
            pg.pdf(path=path, format='Letter', print_background=True,
                   display_header_footer=True, header_template='<span></span>',
                   footer_template='<div style="font-size:8px;color:#888;width:100%;text-align:center;">'
                                   'Kamloops Newcomer Assistant · test version · <span class="pageNumber"></span>/<span class="totalPages"></span></div>',
                   margin={'top': '16mm', 'bottom': '18mm', 'left': '16mm', 'right': '16mm'})
            print('wrote', os.path.relpath(path, os.path.dirname(ROOT)))
        b.close()


if __name__ == '__main__':
    main()
