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
import argparse, os, re, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'src')
MARKER = '/*__CITY_DATA__*/'


def build(city, out_path=None, inline_libs=True):
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

    if inline_libs:
        html = inline_dependencies(html)

    html = html.replace('{{BUILT}}', datetime.date.today().isoformat())

    out_path = out_path or os.path.join(HERE, '%s.html' % city)
    open(out_path, 'w', encoding='utf-8').write(html)
    return out_path, len(html.encode())


def inline_dependencies(html):
    """Fold Leaflet and the cluster plugin into the file.

    Without this the map is a blank rectangle whenever the CDN is unreachable —
    on a plane, behind a restrictive network, or for someone who has just landed
    and has no data plan yet. That is exactly the reader this tool is for.
    """
    libs = [
        ('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css',
         'node_modules/leaflet/dist/leaflet.css', 'css'),
        ('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js',
         'node_modules/leaflet/dist/leaflet.js', 'js'),
        ('https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.min.js',
         'node_modules/leaflet.markercluster/dist/leaflet.markercluster.js', 'js'),
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
    a = ap.parse_args()
    path, size = build(a.city, a.out, inline_libs=not a.cdn)
    print('built %s  (%d KB)' % (path, size // 1024))
