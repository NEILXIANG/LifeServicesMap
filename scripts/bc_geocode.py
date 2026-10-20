#!/usr/bin/env python3
"""Locate BC addresses with the Province's own BC Address Geocoder (tier-1 source).

    from bc_geocode import geocode
    hit = geocode('1141 Harvey Ave', 'Kelowna')
    # -> {'lat':49.883, 'lng':-119.475, 'score':100, 'precision':'CIVIC_NUMBER', 'full':'1141 Harvey Ave, Kelowna, BC'} or None

Rule (docs/guides/新城市扩展方法论与标准.md, coordinates): a result is *trusted* when
its score is >= 95 and it matched a civic number or a site; anything weaker is
returned with trusted=False so the caller marks the record precision:'low' or keeps
it off the map. Answers are cached in provinces/bc/geocode-cache.json so re-runs are cheap
and reproducible, and the public API is called at most once a second.

API: https://geocoder.api.gov.bc.ca/ (no key needed for this volume; Open
Government Licence – British Columbia).
"""
import json, os, re, sys, time, urllib.parse, urllib.request

_r = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_r)
if ROOT not in sys.path: sys.path.insert(0, ROOT)
import kamdata
CACHE = os.path.join(ROOT, 'provinces', 'bc', 'geocode-cache.json')   # BC-wide; was data/ until 2026-10-04
API = 'https://geocoder.api.gov.bc.ca/addresses.json'
TRUSTED_PRECISION = {'CIVIC_NUMBER', 'SITE', 'UNIT', 'OCCUPANT'}
_last = [0.0]

SSL_CTX = kamdata.ssl_context()     # certifi / system bundle (macOS python.org builds ship without roots)

def _load():
    try:
        return json.load(open(CACHE, encoding='utf-8'))
    except (FileNotFoundError, ValueError):
        return {}

def _save(c):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(c, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)

def clean_address(a):
    """'#20-301 Hwy 33 W' -> '301 Hwy 33 W': the geocoder places buildings, not units."""
    a = re.sub(r'^\s*(#|unit\s+|suite\s+)?[0-9A-Za-z]+\s*-\s*(?=\d)', '', a, flags=re.I)
    a = re.sub(r',?\s*(#|unit|suite)\s*\w+\s*$', '', a, flags=re.I)
    return a.strip()

def geocode(address, locality, province='BC'):
    q = '%s, %s, %s' % (clean_address(address), locality, province)
    cache = _load()
    if q in cache:
        return cache[q]
    wait = 1.0 - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    url = API + '?' + urllib.parse.urlencode({'addressString': q, 'maxResults': 1, 'outputSRS': 4326})
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'lifeguide-data-import'}), timeout=30, context=SSL_CTX) as r:
        d = json.load(r)
    _last[0] = time.time()
    hit = None
    if d.get('features'):
        f = d['features'][0]; pr = f['properties']; lng, lat = f['geometry']['coordinates']
        hit = {'lat': round(lat, 7), 'lng': round(lng, 7), 'score': pr.get('score'),
               'precision': pr.get('matchPrecision'), 'full': pr.get('fullAddress'),
               'trusted': (pr.get('score') or 0) >= 95 and pr.get('matchPrecision') in TRUSTED_PRECISION}
    cache[q] = hit
    _save(cache)
    return hit

if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit('usage: bc_geocode.py "<address>" <locality>')
    print(json.dumps(geocode(sys.argv[1], sys.argv[2]), ensure_ascii=False))
