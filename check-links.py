#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check that every website in the data still resolves.

    python3 check-links.py              # check them all
    python3 check-links.py --deep-only  # only the links with a path, which rot fastest
    python3 check-links.py --json out.json

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
import argparse, json, os, re, ssl, sys, time
from concurrent.futures import ThreadPoolExecutor
from urllib import request, error, parse

HERE = os.path.dirname(os.path.abspath(__file__))
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')
TIMEOUT = 12


def load_places(city):
    path = os.path.join(HERE, 'src', 'data-%s.js' % city)
    if not os.path.exists(path):
        sys.exit('missing %s' % path)
    s = open(path, encoding='utf-8').read()
    i = s.index('const P=[') + len('const P=')
    depth = 0
    for k in range(i, len(s)):
        if s[k] == '[':
            depth += 1
        elif s[k] == ']':
            depth -= 1
            if depth == 0:
                return json.loads(s[i:k + 1])
    sys.exit('could not find the end of P')


def check(url):
    """HEAD first (cheap); some servers refuse it, so fall back to a GET."""
    ctx = ssl.create_default_context()
    for method in ('HEAD', 'GET'):
        req = request.Request(url, method=method, headers={
            'User-Agent': UA, 'Accept': '*/*', 'Accept-Language': 'en-CA,en;q=0.9'})
        try:
            with request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
                final = r.geturl()
                same = parse.urlparse(final).netloc.lower().lstrip('www.') == \
                       parse.urlparse(url).netloc.lower().lstrip('www.')
                path_same = parse.urlparse(final).path.rstrip('/') == \
                            parse.urlparse(url).path.rstrip('/')
                if same and path_same:
                    return ('OK', r.status, final)
                return ('MOVED', r.status, final)
        except error.HTTPError as e:
            if e.code in (405, 501) and method == 'HEAD':
                continue                       # server dislikes HEAD; retry with GET
            if e.code in (403, 429):
                return ('BLOCKED', e.code, url)
            if e.code in (404, 410):
                return ('DEAD', e.code, url)
            return ('BLOCKED', e.code, url)
        except (error.URLError, TimeoutError, OSError) as e:
            reason = getattr(e, 'reason', e)
            if 'Name or service not known' in str(reason) or 'nodename' in str(reason):
                return ('DEAD', 0, 'host does not resolve')
            return ('BLOCKED', 0, str(reason)[:60])
    return ('BLOCKED', 0, 'no method accepted')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', default='kamloops')
    ap.add_argument('--deep-only', action='store_true',
                    help='only URLs with a path — the ones that rot fastest')
    ap.add_argument('--json', default=None, help='also write the full result here')
    ap.add_argument('--workers', type=int, default=6,
                    help='parallel requests; keep it small, these are small sites')
    a = ap.parse_args()

    places = [p for p in load_places(a.city) if p.get('w')]
    if a.deep_only:
        places = [p for p in places
                  if parse.urlparse(p['w']).path.rstrip('/') not in ('', )]
    print('checking %d links with %d workers…\n' % (len(places), a.workers))

    results = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for p, (status, code, final) in zip(places, ex.map(lambda p: check(p['w']), places)):
            results.append({'name': p['n'], 'id': p['id'], 'url': p['w'],
                            'status': status, 'code': code, 'final': final})
            if status != 'OK':
                print('  %-8s %-38s %s' % (status, p['n'][:38], p['w']))
                if final and final != p['w']:
                    print('           → %s' % final)

    counts = {}
    for r in results:
        counts[r['status']] = counts.get(r['status'], 0) + 1
    print('\n' + ' · '.join('%s %d' % (k, counts[k]) for k in sorted(counts)))

    # If nothing at all got through, the problem is this machine's network, not 150
    # websites that all died on the same day. Say so instead of reporting a disaster.
    if results and counts.get('BLOCKED', 0) == len(results):
        print('\nEvery request was blocked, which means the network here is filtered '
              '— not that the links are broken.\nRun this from a normal terminal on a '
              'machine with unrestricted internet access.')
        sys.exit(2)

    if a.json:
        json.dump(results, open(a.json, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print('wrote %s' % a.json)

    # MOVED and BLOCKED are for a human to look at; only DEAD is unambiguous.
    sys.exit(1 if counts.get('DEAD') else 0)


if __name__ == '__main__':
    main()
