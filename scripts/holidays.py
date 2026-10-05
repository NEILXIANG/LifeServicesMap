#!/usr/bin/env python3
"""Statutory holidays for a province → provinces/<prov>/province.json "holidays" (and, with --apply, every city in it).

    python3 scripts/holidays.py                      # BC, from 2026-09-01 to the end of 2028: print and update the province file
    python3 scripts/holidays.py --until 2030         # extend
    python3 scripts/holidays.py --until 2030 --apply # also rewrite CITY.holidays in each BC city's data.js (page changes: bump DATA_VERSION)

Why: on a statutory holiday no listed hours are trusted ("open now" says so instead), and validate.py warns 120 days
before the list runs out. The generator was a one-off patch (p3_patch.py, 2026-09-21, now in docs/archive/scripts/);
by 2028 every BC city would have needed the list extended by hand. 2026-10-04: brought back as a tool, rules unchanged.
BC (Employment Standards Act): New Year's Day, Family Day (3rd Mon Feb), Good Friday, Victoria Day (Mon on or before
May 24), Canada Day, BC Day (1st Mon Aug), Labour Day, National Day for Truth and Reconciliation (Sep 30),
Thanksgiving (2nd Mon Oct), Remembrance Day, Christmas Day. Only BC so far; another province adds its own rule function.
"""
import argparse, datetime as dt, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kamdata

def easter(y):
    a=y%19;b=y//100;c=y%100;e=b//4;f=b%4;g=(b+8)//25;h=(b-g+1)//3;i=(19*a+b-e-h+15)%30;k=c//4;l=c%4;m=(32+2*f+2*k-i-l)%7;n=(a+11*i+22*m)//451
    mo=(i+m-7*n+114)//31;da=((i+m-7*n+114)%31)+1
    return dt.date(y,mo,da)

def nth_mon(y, m, n):
    x = dt.date(y, m, 1); x += dt.timedelta(days=(0 - x.weekday()) % 7); return x + dt.timedelta(weeks=n - 1)

def bc(y):
    v = dt.date(y, 5, 24)
    while v.weekday() != 0: v -= dt.timedelta(days=1)
    return [dt.date(y,1,1), nth_mon(y,2,3), easter(y)-dt.timedelta(days=2), v, dt.date(y,7,1), nth_mon(y,8,1),
            nth_mon(y,9,1), dt.date(y,9,30), nth_mon(y,10,2), dt.date(y,11,11), dt.date(y,12,25)]

RULES = {'bc': bc}
assert easter(2026) == dt.date(2026,4,5) and easter(2027) == dt.date(2027,3,28)

def days(prov, start, until):
    return sorted(x.isoformat() for y in range(start.year, until + 1) for x in RULES[prov](y) if x >= start)

def province_file(prov):
    return os.path.join(kamdata.ROOT, 'provinces', prov, 'province.json')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--province', default='bc'); ap.add_argument('--from', dest='start', default='2026-09-01')
    ap.add_argument('--until', type=int, default=2028); ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    hd = days(a.province, dt.date.fromisoformat(a.start), a.until)
    f = province_file(a.province); d = json.load(open(f, encoding='utf-8'))
    d['holidays'] = hd
    with open(f, 'w', encoding='utf-8') as out:
        json.dump(d, out, ensure_ascii=False, indent=1); out.write('\n')
    print('%s: %d holidays, %s … %s → %s' % (a.province, len(hd), hd[0], hd[-1], os.path.relpath(f, kamdata.ROOT)))
    if a.apply:
        lit = 'holidays:' + json.dumps(hd).replace('"', "'").replace("','", "', '") + ','
        for c in kamdata.cities():
            if kamdata.city_meta(c).get('province') != a.province: continue
            p = kamdata.data_template(c); s = open(p, encoding='utf-8').read()
            s2, n = re.subn(r"holidays:\[[^\]]*\],", lit, s)
            if n != 1: sys.exit('%s: expected one holidays:[…] line, found %d' % (p, n))
            open(p, 'w', encoding='utf-8').write(s2)
            print('  updated', os.path.relpath(p, kamdata.ROOT))

if __name__ == '__main__':
    main()
