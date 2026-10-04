#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build one self-contained HTML file from the reusable engine plus one city's data.

    python3 build.py                 # -> kamloops.html
    python3 build.py --city kelowna  # -> build/kelowna.html from cities/kelowna/

The single-file output is deliberate: no server, no build step for the reader, and
anyone can keep their own copy. The split exists so that an engine improvement
reaches every city at once instead of being re-applied to each one by hand.
"""
import argparse, os, re, sys, datetime, json, shutil
from html import escape as html_escape

def _project_root(p):
    """向上找到项目根（放着 app/engine/parts.txt 的那一层），
    整个项目换个目录、或脚本被挪走，都仍然能正确定位。"""
    for _ in range(6):
        if os.path.exists(os.path.join(p, 'app', 'engine', 'parts.txt')):
            return p
        p = os.path.dirname(p)
    raise SystemExit('找不到项目根目录（需要 app/engine/parts.txt）')

HERE = _project_root(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'src')
sys.path.insert(0, HERE)
import kamdata
MARKER = '/*__CITY_DATA__*/'
META_MARKER = '/*__CITY_META__*/'


PWA = os.path.join(HERE, 'app', 'pwa')

def render_pwa(name, meta, deploy):
    """app/pwa/<name> with the city's values filled in."""
    t = open(os.path.join(PWA, name), encoding='utf-8').read()
    vals = {'{{BASE}}': deploy['basePath'], '{{SW_CACHE}}': deploy['swCache'],
            '{{PWA_LABEL}}': deploy['pwaLabel'], '{{TITLE}}': meta['title'],
            '{{PWA_DESC}}': deploy['pwaDescription']}
    for k, v in vals.items():
        t = t.replace(k, v)
    left = re.findall(r'\{\{[A-Z_]+\}\}', t)
    if left:
        sys.exit('app/pwa/%s: unfilled %s' % (name, sorted(set(left))))
    return t

def write_deploy_folder(assets, html, meta, deploy):
    os.makedirs(assets, exist_ok=True)
    open(os.path.join(assets, 'index.html'), 'w', encoding='utf-8').write(html)
    for name in ('sw.js', 'manifest.json'):
        open(os.path.join(assets, name), 'w', encoding='utf-8').write(render_pwa(name, meta, deploy))
    for name in ('icon.svg', 'icon-180.png', 'icon-512.png'):
        shutil.copyfile(os.path.join(PWA, name), os.path.join(assets, name))


def build(city, out_path=None, inline_libs=True, sync_public=True):
    if not os.path.exists(kamdata.data_template(city)):
        sys.exit('missing %s' % kamdata.data_template(city))

    # 2026-10-03 (multi-city phase 2): the engine is split into app/engine/*,
    # concatenated in the order of app/engine/parts.txt.
    engine = kamdata.engine_text()
    # 2026-10-03 (phase 2): cities/<city>/data.js with its JSON / guide includes expanded
    data = kamdata.data_text(city)

    if MARKER not in engine:
        sys.exit('the engine (app/engine/) has lost its %s marker' % MARKER)
    html = engine.replace(MARKER, data, 1)

    # 2026-10-03 (multi-city phase 1): build-time city settings — page title,
    # description, site URL, localStorage prefix, search stopwords.
    meta_path = os.path.join(HERE, 'cities', city, 'city.json')
    if not os.path.exists(meta_path):
        sys.exit('missing %s' % meta_path)
    meta = json.load(open(meta_path, encoding='utf-8'))
    meta.pop('_comment', None)
    meta.pop('validate', None)      # validate.py's settings; the page never needs them
    deploy = meta.pop('deploy', None)  # deploy settings; used below, not shipped in the page
    for k in ('id', 'title', 'description', 'siteUrl', 'storagePrefix', 'searchStopwords'):
        if k not in meta:
            sys.exit('%s: missing "%s"' % (meta_path, k))
    if META_MARKER not in html:
        sys.exit('the engine (app/engine/) has lost its %s marker' % META_MARKER)
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

    # 2026-09-08: the deploy folder must never drift from the build — every build of
    # a deployable city refreshes it (public/ for Kamloops). 2026-10-03 (phase 4):
    # driven by city.json "deploy" instead of `city == 'kamloops'`, and the folder is
    # complete: index.html plus the manifest, service worker and icons rendered from
    # app/pwa/ (Kamloops' render is byte-identical to the files it has always served).
    # Pass sync_public=False (--no-sync-public) for one-off test builds.
    synced_public = False
    if sync_public and deploy:
        assets = os.path.join(HERE, deploy['assetsDir'])
        if os.path.abspath(out_path) != os.path.abspath(os.path.join(assets, 'index.html')):
            write_deploy_folder(assets, html, meta, deploy)
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
        print('also refreshed the deploy folder (index.html, sw.js, manifest.json, icons)')
