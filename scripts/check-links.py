#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check that every website in the data still resolves.

    python3 check-links.py              # check them all
    python3 check-links.py --deep-only  # only the links with a path, which rot fastest
    python3 check-links.py --json out.json
    python3 check-links.py --pages data/link-pages.json
                                        # every link in the page (places, task cards,
                                        # guide text, seasonal notes): status, final URL,
                                        # title and heading, so a human can check that
                                        # each one opens the RIGHT page, not just a page

Run this from a normal terminal on a machine with unrestricted internet access.
Neither the cloud sandbox this project is built in nor the desktop workspace has
general egress — both sit behind a proxy that returns 403 for everything — which is
why `validate.py` deliberately does not attempt this check. If every single link
comes back BLOCKED, that is the network, and the script says so.

Why it exists
-------------
150 of the 249 records carry an official website, and a third of those are deep
links into a site's own structure:

    kamloops.ca/recreation-culture/facilities/westsyde-pool-fitness-centre

A page like that outlives its URL by about one redesign. Nothing else in this
project would ever notice: the link keeps looking fine in the popup, and the first
person to find out is a reader who clicked it. Once a month is plenty.

What the output means
---------------------
    OK        200-299, or a redirect chain ending in one
    MOVED     redirected somewhere else — still works, but the recorded URL is stale
              and the new one is worth copying into the data
    DEAD      404/410, or the host no longer resolves — needs a human
    BLOCKED   403/429, or a timeout. Often a bot filter rather than a real failure;
              open it by hand before changing anything
"""
import argparse, json, re, ssl, time
from concurrent.futures import ThreadPoolExecutor
from urllib import request, error, parse
import os, sys
_r = os.path.dirname(os.path.abspath(__file__))
for _ in range(6):
    if os.path.exists(os.path.join(_r, 'kamdata.py')): break
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
import kamdata

HERE = kamdata.ROOT
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')
TIMEOUT = 12
HOST_DELAY = 3.0                   # 同一域名两次请求之间的间隔，秒
# 3 秒是试出来的：数据里 11 个地点同属 kelsongroup.com，1.5 秒仍会被它限流。
# 宁可慢——整轮也就一两分钟，一个月才跑一次。
# 证书库只建一次：原来每个 URL 都 create_default_context()，188 条链接就把
# 整个系统 CA 库读了 188 遍（带 GET 重试是 376 遍）。
def _ssl_ctx():
    """macOS 上 python.org 版的 Python 不带系统钥匙串里的根证书，默认 context
    会对每一个 HTTPS 站点报 CERTIFICATE_VERIFY_FAILED。结果是 56 条链接全部
    BLOCKED，看起来像"整个互联网都挂了"，其实是本机证书库没配——2026-09-16
    月度巡检第一次真正跑起来时就撞上了这个。有 certifi 就用它的证书包。"""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()

SSL_CTX = _ssl_ctx()


def load_places(city):
    if city != 'kamloops':
        sys.exit('只有 kamloops 一座城市的数据；收到 --city %s' % city)
    return kamdata.load('P')


def check(url):
    """HEAD first (cheap); some servers refuse it, so fall back to a GET."""
    try:
        return _check(url)
    except Exception as e:                      # 一条坏链接不该带走整轮结果
        return ('DEAD', 0, '%s: %s' % (type(e).__name__, str(e)[:48]))


def _check(url):
    for method in ('HEAD', 'GET'):
        req = request.Request(url, method=method, headers={
            'User-Agent': UA, 'Accept': '*/*', 'Accept-Language': 'en-CA,en;q=0.9'})
        try:
            with request.urlopen(req, timeout=TIMEOUT, context=SSL_CTX) as r:
                final = r.geturl()
                # 注意不能用 lstrip('www.')：它按字符集剥，
                # westsyde.sd73.bc.ca 会被剥成 estsyde.sd73.bc.ca
                strip = lambda h: h[4:] if h.startswith('www.') else h
                same = strip(parse.urlparse(final).netloc.lower()) == \
                       strip(parse.urlparse(url).netloc.lower())
                path_same = parse.urlparse(final).path.rstrip('/') == \
                            parse.urlparse(url).path.rstrip('/')
                if same and path_same:
                    return ('OK', r.status, final)
                return ('MOVED', r.status, final)
        except error.HTTPError as e:
            # HEAD 失败一律不作数，改用 GET 复核再下结论。
            # 原来只对 405/501 重试，于是对 HEAD 回 404 的站点（Wix、Shopify、
            # 部分 WordPress 和 CDN 很常见）直接判 DEAD——2026-09-16 第一次拿到
            # 真实数据时，两条 "DEAD" 里就有一条是这么来的，页面其实好好的。
            if method == 'HEAD':
                continue
            if e.code in (403, 429):
                return ('BLOCKED', e.code, url)
            if e.code in (404, 410):
                return ('DEAD', e.code, url)
            return ('BLOCKED', e.code, url)
        except (error.URLError, TimeoutError, OSError) as e:
            if method == 'HEAD':
                continue                       # 同上：超时/连接问题也用 GET 复核
            reason = getattr(e, 'reason', e)
            if 'Name or service not known' in str(reason) or 'nodename' in str(reason):
                return ('DEAD', 0, 'host does not resolve')
            return ('BLOCKED', 0, str(reason)[:60])
    return ('BLOCKED', 0, 'no method accepted')


def all_links():
    """Every outbound link a reader can click, with what it is supposed to be.
    Places carry `w`; task cards `src`; the guide text and the city block carry
    hrefs and `u:`/`src:` entries (seasonal notes, local crisis line)."""
    P, T = kamdata.load_all('P', 'TASKS')
    out, seen = [], set()
    def add(url, kind, ref, what):
        if not url or not url.startswith('http') or url in seen:
            if url in seen:
                for o in out:
                    if o['url'] == url: o['used_for'].append(what)
            return
        seen.add(url); out.append({'url': url, 'kind': kind, 'ref': ref, 'used_for': [what]})
    for p in P:
        add(p.get('w'), 'place', p['id'], 'place "%s" (%s) at %s' % (p['n'], p['c'], p.get('a')))
    for t in T:
        add(t.get('src'), 'task', t['id'], 'task card "%s"' % t['t']['en'])
    for f in ('src/engine.html', 'src/data-kamloops.js'):
        txt = open(os.path.join(HERE, f), encoding='utf-8').read()
        for u in re.findall(r'href=\\?"(https?://[^"\\]+)', txt) + re.findall(r"(?:u|src|w):'(https?://[^']+)'", txt):
            if "'+" in u or any(h in u for h in ('maptiler', 'arcgisonline', 'openstreetmap.org/copyright', 'esri.com', 'cdnjs.', 'google.com/maps')):
                continue
            add(u, 'text', f, 'link in %s' % f)
    return out


def fetch_page(url):
    """GET the page and keep just enough to tell what it is."""
    req = request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,*/*',
                                        'Accept-Language': 'en-CA,en;q=0.9'})
    row = {'status': '', 'code': 0, 'final': '', 'title': '', 'h1': '', 'site': '', 'desc': '', 'text': ''}
    try:
        with request.urlopen(req, timeout=TIMEOUT + 8, context=SSL_CTX) as r:
            row['code'], row['final'] = r.status, r.geturl()
            raw = r.read(600000).decode(r.headers.get_content_charset() or 'utf-8', 'replace')
    except error.HTTPError as e:
        row['code'], row['final'] = e.code, url
        row['status'] = 'DEAD' if e.code in (404, 410) else 'BLOCKED'
        return row
    except Exception as e:
        row['status'] = 'DEAD' if 'nodename' in str(e) or 'not known' in str(e) else 'BLOCKED'
        row['final'] = str(e)[:80]
        return row
    grab = lambda pat: (re.search(pat, raw, re.I | re.S) or [None, ''])[1]
    clean = lambda x: re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', x or '')).strip()
    row['title'] = clean(grab(r'<title[^>]*>(.*?)</title>'))[:140]
    row['h1'] = clean(grab(r'<h1[^>]*>(.*?)</h1>'))[:140]
    row['site'] = clean(grab(r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']*)'))[:80]
    row['desc'] = clean(grab(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)'))[:200]
    body = re.sub(r'<(script|style|noscript)[^>]*>.*?</\1>', ' ', raw, flags=re.I | re.S)
    row['text'] = clean(grab(r'<main[^>]*>(.*?)</main>') or body)[:400]
    same = parse.urlparse(row['final']).netloc.lower().replace('www.', '') == parse.urlparse(url).netloc.lower().replace('www.', '')
    row['status'] = 'OK' if same and parse.urlparse(row['final']).path.rstrip('/') == parse.urlparse(url).path.rstrip('/') else 'MOVED'
    return row


def pages_mode(path, workers):
    links = all_links()
    print('fetching %d pages (one host at a time, %gs apart)…' % (len(links), HOST_DELAY))
    by_host = {}
    for l in links:
        by_host.setdefault(parse.urlparse(l['url']).netloc.lower(), []).append(l)
    def run(group):
        for i, l in enumerate(group):
            if i: time.sleep(HOST_DELAY)
            l.update(fetch_page(l['url']))
            print('%-8s %-60s %s' % (l['status'], l['url'][:60], l['title'][:60]), flush=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(run, by_host.values()))
    json.dump(links, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    counts = {}
    for l in links: counts[l['status']] = counts.get(l['status'], 0) + 1
    print('\n' + ' · '.join('%s %d' % (k, counts[k]) for k in sorted(counts)))
    print('wrote %s — send it back for the page-by-page check' % path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', default='kamloops')
    ap.add_argument('--deep-only', action='store_true',
                    help='only URLs with a path — the ones that rot fastest')
    ap.add_argument('--json', default=None, help='also write the full result here')
    ap.add_argument('--host', default=None,
                    help='只查这一个域名（子串匹配）。复查某个站点时用，'
                         '免得为了一条链接把其余 26 个站再惊动一遍')
    ap.add_argument('--workers', type=int, default=6,
                    help='并发的域名数（同一域名始终串行）；这些都是小站，别调大')
    ap.add_argument('--pages', default=None,
                    help='fetch every link in the page and record title/heading/final URL here')
    a = ap.parse_args()
    if a.pages:
        return pages_mode(a.pages, a.workers)

    places = [p for p in load_places(a.city) if p.get('w')]
    if a.deep_only:
        places = [p for p in places
                  if parse.urlparse(p['w']).path.rstrip('/') != '']
    if a.host:
        places = [p for p in places if a.host.lower() in parse.urlparse(p['w']).netloc.lower()]
        if not places:
            sys.exit('没有链接属于域名 %r' % a.host)
    print('checking %d links with %d workers…\n' % (len(places), a.workers))

    # 同一个域名串行、并留出间隔；并发只跨域名。
    # 数据里有 11 个地点同属 kelsongroup.com，原来 6 个并发一起打过去，
    # 加上 HEAD 失败后补一次 GET，等于瞬间十几个请求砸向一个小站——
    # 2026-09-16 第一次拿到真实数据时，那 11 条全被限流成 429，
    # 报告里看起来像"这家网站挂了"，其实是我们自己造成的。
    by_host = {}
    for p in places:
        by_host.setdefault(parse.urlparse(p['w']).netloc.lower(), []).append(p)

    def check_host(group):
        out = []
        for i, p in enumerate(group):
            if i:
                time.sleep(HOST_DELAY)          # 对同一台服务器留口气
            out.append((p, check(p['w'])))
        return out

    results = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        pairs = [pair for group in ex.map(check_host, by_host.values()) for pair in group]
    # 打印顺序回到数据里的原始顺序，方便和上一次的日志对照
    order = {id(p): i for i, p in enumerate(places)}
    pairs.sort(key=lambda kv: order[id(kv[0])])
    for p, (status, code, final) in pairs:
        results.append({'name': p['n'], 'id': p['id'], 'url': p['w'],
                        'status': status, 'code': code, 'final': final})
        # 行首顶格、每条都打印：月度脚本按行首 grep，缩进和"只打印异常"
        # 这两件事让它这几个月一直数到 0 OK / 0 DEAD。
        print('%-8s %-38s %s' % (status, p['n'][:38], p['w']))
        if status != 'OK' and final and final != p['w']:
            print('         → %s' % final)

    counts = {}
    for r in results:
        counts[r['status']] = counts.get(r['status'], 0) + 1
    print('\n' + ' · '.join('%s %d' % (k, counts[k]) for k in sorted(counts)))

    # 先落盘再判断：全被拦截时也该留下证据文件，
    # 否则月度巡检只能报"计数不可用"，看不到到底发生了什么。
    if a.json:
        json.dump(results, open(a.json, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print('wrote %s' % a.json)

    # If nothing at all got through, the problem is this machine's network, not 150
    # websites that all died on the same day. Say so instead of reporting a disaster.
    if results and counts.get('BLOCKED', 0) == len(results):
        if all('CERTIFICATE_VERIFY' in (r['final'] or '') for r in results):
            print('\n全部 56 条都是证书验证失败 —— 这是本机 Python 的根证书没配，'
                  '不是链接坏了。\n装一下证书包再跑：'
                  '\n    pip3 install --upgrade certifi'
                  '\n（macOS 上也可以跑 Python 安装目录里的 "Install Certificates.command"）')
        else:
            print('\nEvery request was blocked, which means the network here is filtered '
                  '— not that the links are broken.\nRun this from a normal terminal on a '
                  'machine with unrestricted internet access.')
        sys.exit(2)

    # MOVED and BLOCKED are for a human to look at; only DEAD is unambiguous.
    sys.exit(1 if counts.get('DEAD') else 0)


if __name__ == '__main__':
    main()
