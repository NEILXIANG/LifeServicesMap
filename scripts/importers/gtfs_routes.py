#!/usr/bin/env python3
"""Bus routes (BR) and transit exchanges for any city, from the operator's own GTFS feed.

    python3 scripts/importers/gtfs_routes.py --city kelowna --gtfs <dir-or-zip> [--date 20261007]

Works for any GTFS feed (BC Transit, US agencies alike). Tier 1: the operator's official
timetable data. Writes:
- BR (cities/<city>/bus-routes.json): one entry per public route, keyed by route_short_name:
    n  = route_long_name          co = route_color
    s  = ordered stops [name, lat, lng]: the busiest pattern in direction 0, then the stops
         of the busiest direction-1 pattern not already listed
    p  = the shape of those two patterns, thinned to a point every ~15 m
    f/l = first and last departure of the day (GTFS times, may run past 24:00)
- transit places for every "... Exchange" (all bays averaged into one point), updating the
  coordinates of exchanges already on the map instead of adding a second one.
Prints the BUS_SOURCE line and the route count for the city's data.js / busCoverage note.

Rules
- The service day is a representative weekday (default: the first Wednesday on or after the
  feed's start date that is not in CITY.holidays).
- School-only routes are left out (name contains "School", or no service on that weekday),
  the same choice Kamloops made for its school-day routes 70-81.
"""
import argparse, csv, datetime, io, json, math, os, re, sys, zipfile
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CityImport, dist_m, norm, similar
import kamdata

def reader(src):
    if os.path.isdir(src):
        return lambda n: csv.DictReader(open(os.path.join(src, n), encoding='utf-8-sig'))
    z = zipfile.ZipFile(src)
    return lambda n: csv.DictReader(io.TextIOWrapper(z.open(n), encoding='utf-8-sig'))

def thin(pts, min_m=15):
    out = []
    for p in pts:
        if not out or dist_m(out[-1][0], out[-1][1], p[0], p[1]) >= min_m:
            out.append(p)
    if pts and out[-1] != pts[-1]: out.append(pts[-1])
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', required=True); ap.add_argument('--gtfs', required=True)
    ap.add_argument('--date', help='service day YYYYMMDD (default: first ordinary Wednesday)')
    ap.add_argument('--skip-name', default=r'school', help='regex of route names to leave out')
    a = ap.parse_args()
    R = reader(a.gtfs)
    feed = next(R('feed_info.txt'), {}) if True else {}
    active = defaultdict(set)
    try:
        for r in R('calendar.txt'):
            s, e = r['start_date'], r['end_date']
            d = datetime.datetime.strptime(s, '%Y%m%d').date()
            while d.strftime('%Y%m%d') <= e:
                if r[d.strftime('%A').lower()] == '1': active[d.strftime('%Y%m%d')].add(r['service_id'])
                d += datetime.timedelta(days=1)
    except (FileNotFoundError, KeyError):
        pass
    for r in R('calendar_dates.txt'):
        (active[r['date']].add if r['exception_type'] == '1' else active[r['date']].discard)(r['service_id'])
    kamdata.use(a.city)
    holidays = set(re.findall(r"'(\d{4}-\d{2}-\d{2})'", re.search(r'holidays:\[(.*?)\]', kamdata.data_text()).group(1)))
    day = a.date
    if not day:
        d = datetime.datetime.strptime(feed.get('feed_start_date') or min(active), '%Y%m%d').date()
        while d.weekday() != 2 or d.isoformat() in holidays: d += datetime.timedelta(days=1)
        day = d.strftime('%Y%m%d')
    services = active[day]
    print('service day %s: %d service ids' % (day, len(services)))

    stops = {r['stop_id']: (r['stop_name'].strip(), float(r['stop_lat']), float(r['stop_lon'])) for r in R('stops.txt')}
    routes = {r['route_id']: r for r in R('routes.txt')}
    trips = {r['trip_id']: r for r in R('trips.txt') if r['service_id'] in services}
    seq = defaultdict(list); first_dep = {}
    for r in R('stop_times.txt'):
        if r['trip_id'] in trips:
            seq[r['trip_id']].append((int(r['stop_sequence']), r['stop_id'], r['departure_time'] or r['arrival_time']))
    shapes = defaultdict(list)
    for r in R('shapes.txt'):
        shapes[r['shape_id']].append((int(r['shape_pt_sequence']), float(r['shape_pt_lat']), float(r['shape_pt_lon'])))

    BR = {}; skipped = []
    by_route = defaultdict(list)
    for t in trips.values(): by_route[t['route_id']].append(t)
    for rid, rt in routes.items():
        key, name = rt['route_short_name'].strip(), rt['route_long_name'].strip()
        if re.search(a.skip_name, name, re.I): skipped.append('%s %s (name)' % (key, name)); continue
        ts = by_route.get(rid, [])
        if not ts: skipped.append('%s %s (no service on %s)' % (key, name, day)); continue
        pats = defaultdict(Counter)
        deps = []
        for t in ts:
            st = sorted(seq[t['trip_id']]); deps.append(st[0][2])
            pats[t.get('direction_id') or '0'][(tuple(s for _, s, _ in st), t.get('shape_id'))] += 1
        stop_ids, shape_pts = [], []
        for dirn in sorted(pats):
            (ids, shp), _ = pats[dirn].most_common(1)[0]
            stop_ids += [s for s in ids if s not in stop_ids]
            pts = [(la, lo) for _, la, lo in sorted(shapes.get(shp, []))]
            shape_pts += pts
        BR[key] = {'n': name, 'co': '#' + (rt.get('route_color') or '555555').upper(),
                   's': [[stops[s][0], round(stops[s][1], 5), round(stops[s][2], 5)] for s in stop_ids],
                   'p': [[round(la, 5), round(lo, 5)] for la, lo in thin(shape_pts)],
                   'f': min(deps)[:5], 'l': max(deps)[:5]}
    BR = dict(sorted(BR.items(), key=lambda kv: (int(re.sub(r'\D', '', kv[0]) or 0), kv[0])))
    kamdata.save('BR', BR)
    n_stops = len({tuple(x) for r in BR.values() for x in r['s']})
    print('%d routes, %d distinct stops written; left out: %s' % (len(BR), n_stops, '; '.join(skipped) or 'none'))
    ed = feed.get('feed_start_date', day)
    print("BUS_SOURCE={feed:'%s GTFS', edition:'%s-%s-%s', stopsChecked:%d};"
          % (next(R('agency.txt'))['agency_name'].strip(), ed[:4], ed[4:6], ed[6:], n_stops))

    # exchanges: one point per exchange (mean of its bays)
    ex = defaultdict(list)
    for sid, (nm, la, lo) in stops.items():
        # only "<Name> Exchange" or "<Name> Exchange Bay X" — not "Cooper Rd at Orchard Park Exchange"
        m = re.match(r'^([^@]+?\bExchange)(?:\s+Bay\s+\w+)?$', nm)
        if m and ' at ' not in m.group(1): ex[m.group(1).strip()].append((la, lo))
    imp = CityImport(a.city, 'gtfs-exchanges')
    for nm, pts in sorted(ex.items()):
        la, lo = round(sum(p[0] for p in pts) / len(pts), 6), round(sum(p[1] for p in pts) / len(pts), 6)
        old = next((p for p in imp.places if p['c'] == 'transit' and norm(p['n']) == norm(nm)), None)
        if old:
            old['lat'], old['lng'] = la, lo; old.pop('precision', None)
            print('   moved  %-28s to the mean of its %d bays (GTFS)' % (old['n'], len(pts)))
            continue
        imp.add({'n': nm, 'c': 'transit', 'lat': la, 'lng': lo, 'a': nm.replace(' Exchange', '') + ' (bus exchange)',
                 'note': {'zh': '公交换乘站（%d 个站台）；线路和时间见"公交路线"。' % len(pts),
                          'en': 'Bus exchange (%d bays); routes and times under Bus Routes.' % len(pts)},
                 't': ['life'], 'src': 'opendata'}, nm)
    imp.save()

if __name__ == '__main__':
    main()
