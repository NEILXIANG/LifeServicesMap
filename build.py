#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build one self-contained HTML file from the reusable engine plus one city's data.

    python3 build.py                 # -> kamloops.html
    python3 build.py --city kelowna  # -> kelowna.html from src/data-kelowna.js

The single-file output is deliberate: no server, no build step for the reader, and
anyone can keep their own copy. The split exists so that an engine improvement
reaches every city at once instead of being re-applied to each one by hand.
"""
import argparse, os, re, sys, datetime, json
from html import escape as html_escape

def _project_root(p):
    """向上找到项目根（放着 src/data-kamloops.js 的那一层），
    整个项目换个目录、或脚本被挪走，都仍然能正确定位。"""
    for _ in range(6):
        if os.path.exists(os.path.join(p, 'src', 'data-kamloops.js')):
            return p
        p = os.path.dirname(p)
    raise SystemExit('找不到项目根目录（需要 src/data-kamloops.js）')

HERE = _project_root(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'src')
MARKER = '/*__CITY_DATA__*/'
META_MARKER = '/*__CITY_META__*/'


def build(city, out_path=None, inline_libs=True, sync_public=True):
    engine_path = os.path.join(SRC, 'engine.html')
    data_path = os.path.join(SRC, 'data-%s.js' % city)
    for p in (engine_path, data_path):
        if not os.path.exists(p):
            sys.exit('missing %s' % p)

    engine = open(engine_path, encoding='utf-8').read()
    data = open(data_path, encoding='utf-8').read()

    if MARKER not in engine:
        sys.exit('engine.html has lost its %s marker' % MARKER)
    html = engine.replace(MARKER, data, 1)

    # 2026-10-03 (multi-city phase 1): build-time city settings — page title,
    # description, site URL, localStorage prefix, search stopwords.
    meta_path = os.path.join(HERE, 'cities', city, 'city.json')
    if not os.path.exists(meta_path):
        sys.exit('missing %s' % meta_path)
    meta = json.load(open(meta_path, encoding='utf-8'))
    meta.pop('_comment', None)
    for k in ('id', 'title', 'description', 'siteUrl', 'storagePrefix', 'searchStopwords'):
        if k not in meta:
            sys.exit('%s: missing "%s"' % (meta_path, k))
    if META_MARKER not in html:
        sys.exit('engine.html has lost its %s marker' % META_MARKER)
    html = html.replace(META_MARKER, json.dumps(meta, ensure_ascii=False), 1)
    for ph, val in (('{{CITY_TITLE}}', meta['title']),
                    ('{{CITY_DESC}}', meta['description']),
                    ('{{CITY_SITE_URL}}', meta['siteUrl'])):
        html = html.replace(ph, html_escape(val, quote=True))
    left = re.findall(r'\{\{CITY_[A-Z_]+\}\}', html)
    if left:
        sys.exit('unfilled placeholders: %s' % sorted(set(left)))

    if inline_libs:
        html = inline_dependencies(html)

    html = html.replace('{{BUILT}}', datetime.date.today().isoformat())

    out_path = out_path or os.path.join(HERE, 'build', '%s.html' % city)
    # build/ is gitignored, so a fresh clone does not have it yet — create it
    # rather than crashing with FileNotFoundError on the very first build.
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    open(out_path, 'w', encoding='utf-8').write(html)

    # deploy.sh's own [1/5] step rebuilds public/index.html — that is the file
    # actually served by the Cloudflare Worker — but that only happens when
    # someone runs deploy.sh. Anyone (including this build script's other
    # callers, e.g. a plain `--city kamloops` run used only to feed
    # validate.py/regress.py during local iteration) who rebuilds root
    # kamloops.html without also running deploy.sh leaves public/index.html
    # silently behind (this is exactly what happened 2026.09.07→08: root was
    # rebuilt many times, public/index.html sat untouched since 04:56).
    # So for kamloops specifically, every build keeps both copies in sync by
    # default — the deploy artifact can no longer drift just because deploy.sh
    # wasn't the thing that was run. Pass sync_public=False (or --no-sync-public
    # from the CLI) for the rare case of a one-off test build (e.g. --cdn) that
    # should not touch the real deploy artifact.
    public_dir = os.path.join(HERE, 'public')
    public_index = os.path.join(public_dir, 'index.html')
    synced_public = False
    if (sync_public and city == 'kamloops' and os.path.isdir(public_dir)
            and os.path.abspath(out_path) != os.path.abspath(public_index)):
        open(public_index, 'w', encoding='utf-8').write(html)
        synced_public = True

    return out_path, len(html.encode()), synced_public


def inline_dependencies(html):
    """Fold Leaflet and the cluster plugin into the file.

    Without this the map is a blank rectangle whenever the CDN is unreachable —
    on a plane, behind a restrictive network, or for someone who has just landed
    and has no data plan yet. That is exactly the reader this tool is for.
    """
    libs = [
        ('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css',
         'vendor/leaflet-1.9.4/leaflet.css', 'css'),
        ('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js',
         'vendor/leaflet-1.9.4/leaflet.js', 'js'),
        ('https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.min.js',
         'vendor/leaflet.markercluster-1.5.3/leaflet.markercluster.js', 'js'),
    ]
    for url, local, kind in libs:
        path = os.path.join(HERE, local)
        if not os.path.exists(path):
            print('  ! %s not found locally — leaving the CDN reference in place' % local)
            continue
        body = open(path, encoding='utf-8').read()
        if kind == 'css':
            # Leaflet's CSS refers to marker images that are not used here (the app
            # supplies its own SVG icons), so no asset rewriting is needed.
            tag = '<link rel="stylesheet" href="%s" />' % url
            repl = '<style>\n/* Leaflet 1.9.4 */\n' + body + '\n</style>'
        else:
            tag = '<script src="%s"></script>' % url
            repl = '<script>\n/* %s */\n' % os.path.basename(local) + body + '\n</script>'
        if tag not in html:
            print('  ! could not find the tag for %s' % local)
            continue
        html = html.replace(tag, repl, 1)
    return html


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', default='kamloops')
    ap.add_argument('--out', default=None,
                    help='output path (default <city>.html; pass your own name if you keep the file under a different one)')
    ap.add_argument('--cdn', action='store_true',
                    help='keep the CDN <script> tags instead of inlining (smaller file, needs a network)')
    ap.add_argument('--no-sync-public', action='store_true',
                    help="don't also refresh public/index.html for a kamloops build "
                         "(default: kept in sync automatically — see comment in build())")
    a = ap.parse_args()
    path, size, synced_public = build(a.city, a.out, inline_libs=not a.cdn,
                                       sync_public=not a.no_sync_public)
    print('built %s  (%d KB)' % (path, size // 1024))
    if synced_public:
        print('also synced public/index.html (the Cloudflare deploy artifact) to match')
