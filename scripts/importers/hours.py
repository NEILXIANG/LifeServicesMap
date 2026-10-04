"""Turn opening hours as an official page states them into the engine's structure.

    from hours import parse_hours
    parse_hours('Monday to Friday: 8:30 a.m. to 4:30 p.m.')
    # -> {'r': [[1, 5, 510, 990, 0]]}

Engine format (see fmtHours / openState): {'r': [[day_from, day_to, open_min, close_min, approx]]},
days 1=Mon … 7=Sun, minutes since midnight; optional 'q' qualifier ('qAppt' = by appointment).

Rule (methodology §5.4 "营业时间"): only text that is understood completely is converted. Anything
with a lunch break, seasonal hours, "varies", "by appointment only", or a part the parser cannot
read returns None — the page then says "hours unknown" rather than claiming the door is open.
A text that says appointments are required but gives clear hours gets q='qAppt', which shows the
hours yet keeps the place out of "open now".
"""
import re

DAYS = {'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6, 'sun': 7}
DAY_RE = r'(mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?'
TIME_RE = r'(\d{1,2})(?:[:.](\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?|noon|midnight'
UNSAFE = re.compile(r'lunch|closed between|season|summer|winter|varies|vary|holiday hours|by appointment only|'
                    r'call (?:for|to confirm)|until further notice|temporar|except|alternat|every other|'
                    r'first|second|third|last \w+ of', re.I)

def _minutes(m):
    s = m.group(0).lower().strip()
    if s == 'noon': return 720
    if s == 'midnight': return 1440
    h = int(m.group(1)); mi = int(m.group(2) or 0); ap = (m.group(3) or '').replace('.', '').lower()   # 'PM' as well as 'p.m.'
    if h > 24 or mi > 59: raise ValueError(s)
    if ap == 'pm' and h != 12: h += 12
    if ap == 'am' and h == 12: h = 0
    return h * 60 + mi

def _days(txt):
    """'Monday to Friday' / 'Mon-Fri' / 'Mon, Wed & Fri' / 'Daily' / 'Weekdays' -> sorted day list."""
    t = txt.lower().strip(' :,;')
    if re.fullmatch(r'(daily|every day|7 days a week|seven days a week|open daily|all week)', t): return list(range(1, 8))
    if re.fullmatch(r'weekdays?', t): return [1, 2, 3, 4, 5]
    if re.fullmatch(r'weekends?', t): return [6, 7]
    m = re.fullmatch(DAY_RE + r'\s*(?:-|–|—|to|through|thru)\s*' + DAY_RE, t)
    if m:
        a, b = DAYS[m.group(1)], DAYS[m.group(2)]
        return list(range(a, b + 1)) if a <= b else None
    parts = re.split(r'\s*(?:,|&|\band\b|/)\s*', t)
    out = []
    for p in parts:
        mm = re.fullmatch(DAY_RE, p)
        if not mm: return None
        out.append(DAYS[mm.group(1)])
    return sorted(set(out)) if out else None

def _ranges(days):
    out, start = [], None
    for i, d in enumerate(days):
        if start is None: start = d
        if i + 1 == len(days) or days[i + 1] != d + 1:
            out.append((start, d)); start = None
    return out

def parse_hours(text):
    if not text: return None
    t = re.sub(r'\s+', ' ', text).strip()
    t = re.sub(r'^(store|clinic|office|opening|open|regular|hours of operation|hours)\s*hours?\s*:?\s*', '', t, flags=re.I)
    # open around the clock (shelters, some pharmacies): the engine's own 24-hour flag
    if re.fullmatch(r'(?:open\s+)?(?:24/7|24 hours(?: a day)?,? 7 days a week|7 days a week,? 24 hours a day|24 hours,? daily)[.;]?(?:\s.*)?', t, re.I) \
            and not re.search(r'except|closed|season', t, re.I):
        return {'a': 1}
    # "(closed statutory holidays)", "excluding statutory holidays": holidays are the engine's job
    t = re.sub(r'\(?[,;]?\s*(?:closed|excluding|except)\s+(?:on\s+)?(?:all\s+)?stat(?:utory)?\s+holidays\)?', '', t, flags=re.I)
    t = re.sub(r'\s*PT\b|\s*Pacific Time', '', t)
    appt = bool(re.search(r'appointment', t, re.I))
    # statutory holidays are the engine's job (CITY.holidays -> "unknown"), so "Sunday & Holidays" is just Sunday
    t = re.sub(r'\s*(?:&|and|/)\s*(?:stat(?:utory)?\s+)?holidays?\b', '', t, flags=re.I)
    t = re.sub(r'\s*\|\s*', ' ', t)
    if UNSAFE.search(t): return None
    t = re.sub(r'\.?\s*(appointments?[^.;]*|walk-?ins?[^.;]*)(\.|$)', '. ', t, flags=re.I).strip(' .')
    # a sentence break, but not the dot of "A.M. To"
    segs = [s.strip(' .') for s in re.split(r';|(?<![aApP]\.[mM])\.\s+(?=[A-Z])|\n', t) if s.strip(' .')]
    rows, seen = [], set()
    for seg in segs:
        if re.search(r'\bclosed\b', seg, re.I) and not re.search(r'\d', seg):
            continue                                   # "Sunday: Closed" — absent days are closed anyway
        # time first, days after: "8:30am - 4:30pm Monday to Friday" -> days first
        mt = re.match(r'^((?:' + TIME_RE + r'))\s*(?:-|–|—|to)\s*((?:' + TIME_RE + r'))\s+(.+)$', seg, re.I)
        if mt: seg = '%s %s - %s' % (mt.group(9), mt.group(1), mt.group(5))
        # split hours within one day: "8:30am – 12:00pm & 1:00pm – 4:30pm" -> two ranges for the same days
        two = re.match(r'^(.*?)\s*:?\s*((?:' + TIME_RE + r'))\s*(?:-|–|—|to)\s*((?:' + TIME_RE + r'))\s*(?:&|and|,)\s*((?:' + TIME_RE + r'))\s*(?:-|–|—|to)\s*((?:' + TIME_RE + r'))\s*$', seg, re.I)
        if two:
            d2 = _days(two.group(1))
            if not d2 or seen & set(d2): return None
            spans = []
            for oi, ci in ((2, 6), (10, 14)):
                o2 = _minutes(re.match(TIME_RE, two.group(oi), re.I)); c2 = _minutes(re.match(TIME_RE, two.group(ci), re.I))
                if c2 <= o2 and not re.search(r'[ap]\.?m', two.group(ci), re.I): c2 += 720
                if c2 <= o2: return None
                spans.append((o2, c2))
            if spans[1][0] < spans[0][1]: return None
            seen |= set(d2)
            for a, b in _ranges(d2):
                for o2, c2 in spans: rows.append([a, b, o2, c2, 0])
            continue
        m = re.match(r'^(.*?)\s*:?\s*((?:' + TIME_RE + r'))\s*(?:-|–|—|to)\s*((?:' + TIME_RE + r'))\s*$', seg, re.I)
        if not m: return None
        days_txt = m.group(1)
        days = _days(days_txt) if days_txt else None
        if not days: return None
        o = _minutes(re.match(TIME_RE, m.group(2), re.I)); c = _minutes(re.match(TIME_RE, m.group(6), re.I))
        if not re.search(r'[ap]\.?m|noon|midnight', m.group(2) + m.group(6), re.I) and (o < 300 or c < 300):
            # office style "8:30-4:30": a morning start and an afternoon close; anything else is ambiguous
            if 360 <= o < 720 and c < o and 12 * 60 <= c + 720 <= 20 * 60: c += 720
            else: return None
        if c <= o:
            if re.search(r'[ap]\.?m', m.group(6), re.I): return None
            c += 720
            if c <= o: return None
        if seen & set(days): return None
        seen |= set(days)
        for a, b in _ranges(days):
            rows.append([a, b, o, c, 0])
    if not rows: return None
    h = {'r': sorted(rows)}
    if appt: h['q'] = 'qAppt'
    return h

if __name__ == '__main__':
    tests = {
     'Monday to Friday: 8:30 a.m. to 4:30 p.m.': {'r': [[1, 5, 510, 990, 0]]},
     'Store Hours: Mon-Sat: 9:00 AM-10:00 PM; Sunday: 9:00 AM-8:00 PM': {'r': [[1, 6, 540, 1320, 0], [7, 7, 540, 1200, 0]]},
     'Daily 8:00-22:00': {'r': [[1, 7, 480, 1320, 0]]},
     'Monday - Friday: 9am - 5pm': {'r': [[1, 5, 540, 1020, 0]]},
     'Monday: 8:30 am – 4:30 pm; Tuesday: 8:30 am – 5:30 pm': {'r': [[1, 1, 510, 990, 0], [2, 2, 510, 1050, 0]]},
     'Monday to Friday 8:30 a.m. to 4:30 p.m. Closed between 12:00 pm and 1:00 pm for lunch.': None,
     'Seasonal: runs for a few weeks each May': None,
     '8am - 4:30pm | Monday - Friday': {'r': [[1, 5, 480, 990, 0]]},
     'Mon-Sat: 9:00 AM-10:00 PM; Sunday & Holidays: 9:00 AM-8:00 PM': {'r': [[1, 6, 540, 1320, 0], [7, 7, 540, 1200, 0]]},
     'Monday - Friday: 9:00 AM - 4:00 PM; Saturday - Sunday: Closed; Holidays: Closed': {'r': [[1, 5, 540, 960, 0]]},
     '10 A.M. To 4 P.M. Daily': {'r': [[1, 7, 600, 960, 0]]},
     'Open 24/7; once you have a bed, there is no set wake-up time.': {'a': 1},
     'Monday - Friday: 8:30-4:30; Saturday and Sunday closed.': {'r': [[1, 5, 510, 990, 0]]},
     'Our offices are open Monday to Friday from 8:30 am – 4:30 pm, excluding statutory holidays.': None,
     'Mon – Fri, 8:30am – 12:00pm & 1:00pm – 4:30pm': {'r': [[1, 5, 510, 720, 0], [1, 5, 780, 990, 0]]},
     'Monday - Friday 8:30 am - 4:30 pm (closed statutory holidays).': {'r': [[1, 5, 510, 990, 0]]},
    }
    bad = 0
    for k, want in tests.items():
        got = parse_hours(k)
        ok = got == want
        bad += not ok
        print('ok ' if ok else 'BAD', repr(k)[:60], '->', got)
    raise SystemExit(1 if bad else 0)
