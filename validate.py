# -*- coding: utf-8 -*-
"""
Invariant checker for kamloops.html.

Run after every batch of edits. Exits non-zero if any invariant is violated.
Written because the previous round's six regressions were all of the form
"changed A, forgot to update B" — exactly the class a mechanical check catches.
"""
import re, sys, os, glob, json, subprocess, math
from collections import Counter

# Relative to this file, so it runs from any working directory and on any machine.
HERE = os.path.dirname(os.path.abspath(__file__))

def find_built(here, argv_path=None):
    """The built file. Named kamloops.html here; readers often rename their copy,
    so fall back to the only .html sitting next to this script."""
    if argv_path:
        return argv_path
    default = os.path.join(here, 'kamloops.html')
    if os.path.exists(default):
        return default
    found = [f for f in glob.glob(os.path.join(here, '*.html'))
             if not os.path.basename(f).startswith('test_')]
    if len(found) == 1:
        return found[0]
    if not found:
        sys.exit('no built HTML found next to this script — run build.py first')
    sys.exit('several .html files here; name one: %s <file>' % os.path.basename(__file__))

PATH = find_built(HERE, sys.argv[1] if len(sys.argv) > 1 else None)
FAIL = []
WARN = []

def fail(msg): FAIL.append(msg)
def warn(msg): WARN.append(msg)

html = open(PATH, encoding='utf-8').read()

def extract(varname, src=None):
    s = src if src is not None else script
    idx = s.index('const ' + varname + '=')
    i = s.index('=', idx) + 1
    while s[i] in ' \n\t': i += 1
    o = s[i]; c = '}' if o == '{' else ']'
    d = 0; instr = False; esc = False; j = i
    while j < len(s):
        ch = s[j]
        if instr:
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == '"': instr = False
        else:
            if ch == '"': instr = True
            elif ch == o: d += 1
            elif ch == c:
                d -= 1
                if d == 0: j += 1; break
        j += 1
    return json.loads(s[i:j])

LANGS = ['zh', 'en', 'fr', 'es', 'ko', 'ja']

# ---------------------------------------------------------------- 1. syntax
# Only the app's own script — never a vendored library that build.py inlined.
_m = re.search(r'<script id="app">(.*?)</script>', html, re.S)
if not _m:
    _m = re.search(r'<script>(.*)</script>', html, re.S)   # un-built source
script = _m.group(1)
open('/tmp/_v.js', 'w', encoding='utf-8').write(script)
r = subprocess.run(['node', '--check', '/tmp/_v.js'], capture_output=True, text=True)
if r.returncode != 0:
    # node prints a stack trace; the useful part is the file:line and the message.
    lines = [l.strip() for l in r.stderr.splitlines() if l.strip()]
    where = next((l for l in lines if l.startswith('/tmp/_v.js:')), '')
    what = next((l for l in lines if 'Error' in l and 'at ' not in l), lines[0] if lines else '')
    fail('the app script does not parse — %s %s' % (where, what))

# ---------------------------------------------------------------- 2. data shape
P = extract('P'); CI = extract('CI'); RI = extract('RI'); GN = extract('GN'); UI = extract('UI')
BR = extract('BR'); CO = extract('CO'); CD = extract('CD'); IC = extract('IC')

if len(P) < 240: fail('P shrank to %d places' % len(P))
for i, p in enumerate(P):
    for k in ('n', 'c', 'g', 'lat', 'lng', 'a'):
        if k not in p: fail('P[%d] %r missing required field %r' % (i, p.get('n'), k))
    if p['c'] not in CI: fail('P[%d] %r has unknown category %r' % (i, p['n'], p['c']))
    if p['g'] not in RI: fail('P[%d] %r has unknown region %r' % (i, p['n'], p['g']))
    if not (50.5 < p['lat'] < 50.9 and -120.7 < p['lng'] < -120.0):
        fail('P[%d] %r coordinates out of Kamloops bounds' % (i, p['n']))

names = [p['n'] for p in P]
dupes = [n for n, c in Counter(names).items() if c > 1]
if dupes: fail('duplicate place names: %s' % dupes)

# A ⭐ prefix is decoration, not identity. "⭐⭐ Kamloops Immigrant Services" and
# "Kamloops Immigrant Services" are the same place, and the exact-string check above
# happily passed both — which is how one agency ended up listed twice, in two
# categories, with coordinates 1.4 km apart.
def bare(n):
    return re.sub(r'^[⭐\s]+', '', n).strip().lower()
bare_dupes = [n for n, c in Counter(bare(p['n']) for p in P).items() if c > 1]
if bare_dupes:
    fail('places whose names differ only by a ⭐ prefix: %s' % bare_dupes)

# Sharing an address and a website is a duplicate *candidate*, not proof: a Costco
# warehouse and its gas bar legitimately share both, and are two destinations with
# different hours. This can only flag them for a human to look at.
def host(u):
    m = re.match(r'https?://(?:www\.)?([^/]+)', u or '')
    return m.group(1).lower() if m else None
seen = {}
for p in P:
    h = host(p.get('w'))
    if not h: continue
    key = (p['a'].strip().lower(), h)
    if key in seen:
        a, b = bare(seen[key]), bare(p['n'])
        # One name containing the other is the shape a real duplicate takes.
        if a in b or b in a:
            fail('%r and %r look like the same place listed twice (same address, same '
                 'website, one name inside the other)' % (seen[key], p['n']))
        else:
            warn('%r and %r share an address and a website — check they are really two '
                 'places' % (seen[key], p['n']))
    seen[key] = p['n']

# ---------------------------------------------------------------- 3. no re-introduced risk content
def note_strings(p):
    nt = p.get('note')
    if not nt: return []
    if isinstance(nt, str): return [nt]
    return list(nt.values())

for p in P:
    if 'r' in p: fail('%r re-introduced a hard-coded rating' % p['n'])
    for t in note_strings(p):
        if re.search(r'\$\s?\d', t): fail('%r note contains a $ figure again' % p['n'])
        if re.search(r'\d\.\d\s*★', t): fail('%r note contains a ★ score again' % p['n'])
    if '@' in (p.get('p') or ''):
        fail('%r has an email back inside the phone field' % p['n'])

# ------------------------------------------------- 3b. bilingual content contract
CJK = re.compile(r'[\u4e00-\u9fff]')
ids = [p.get('id') for p in P]
if any(not i for i in ids): fail('some places have no stable id')
if len(set(ids)) != len(ids): fail('place ids are not unique — favourites would collide')
for p in P:
    nt = p.get('note')
    if nt is None: continue
    if isinstance(nt, str):
        fail('%r note is still a bare string, not {zh,en}' % p['n']); continue
    for k in ('zh', 'en'):
        if not nt.get(k): fail('%r note is missing the %s text' % (p['n'], k))
    # fr/es/ko/ja are optional per record (the engine falls back to English), but a
    # half-translated note is worse than none: it means one language silently shows
    # another's text while its neighbours are translated.
    extra = [k for k in ('fr', 'es', 'ko', 'ja') if nt.get(k)]
    if extra and len(extra) != 4:
        fail('%r note has %s but not the rest — translate all four or none'
             % (p['n'], '/'.join(extra)))
    for k in extra:
        if nt[k].strip() == (nt.get('en') or '').strip():
            fail('%r %s note is byte-identical to the English — not translated'
                 % (p['n'], k))
    if CJK.search(nt.get('en', '')):
        fail('%r English note still contains Chinese: %r' % (p['n'], nt['en'][:40]))
# ------------------------------------------------- 3b2. addresses are read by everyone
# The address is shown verbatim in every language and handed to the maps app. Chinese
# inside it is unreadable for four of the five audiences and is noise in a navigation
# string. The no-Chinese rule used to cover notes and names but not this field.
for p in P:
    if CJK.search(p.get('a', '')):
        fail('%r has Chinese in its address field: %r' % (p['n'], p['a']))

# ------------------------------------------------- 3b3. what "open 24 hours" asserts
# A municipal park is almost certainly under a bylaw closing time, so h:{a:true} on an
# open-air place states something we cannot support. The engine already renders
# "hours posted on site" for open-air records with no `h` — that is the honest answer.
OPEN_AIR = set(re.findall(r"openAir:\[([^\]]*)\]", html)[0].replace("'", '').split(',')) \
           if re.search(r"openAir:\[", html) else set()
for p in P:
    h = p.get('h')
    if p['c'] in OPEN_AIR and isinstance(h, dict) and h.get('a'):
        fail('%r (%s) claims 24-hour opening; open-air places should fall back to '
             '"hours posted on site"' % (p['n'], p['c']))

# ------------------------------------------------- 3b4. house wording
# 2026.09.07h: the site's own branding moved from "新居民" (newcomer) to the
# plainer "居民" (resident) — 新移民 stays forbidden (always has been the wrong
# register for a note), and 新居民 joins it now that it is the deprecated form.
# A note describing a program whose real eligibility is immigration-specific
# (e.g. SWIS's "新移民家庭") is not a house-wording violation — 新移民 there
# names an actual status, not the site's own generic term for its readers.
for p in P:
    for t in (p.get('note') or {}).values():
        if '新移民' in t:
            fail('%r note uses 新移民; the house wording is 居民' % p['n'])
        if '新居民' in t:
            fail('%r note uses 新居民 (the old house wording); it is now 居民' % p['n'])

# ------------------------------------------------- 3b5. coordinate precision
# Three decimal places is roughly 110 m — the marker lands mid-block. Not a failure
# (the data may simply be all anyone published), but it should stay visible.
coarse = [p['n'] for p in P
          if min(len(str(p['lat']).split('.')[-1]), len(str(p['lng']).split('.')[-1])) <= 3]
if coarse:
    warn('%d record(s) have coordinates to 3 decimal places (~110 m): %s'
         % (len(coarse), ', '.join(coarse[:6]) + (' …' if len(coarse) > 6 else '')))

# ------------------------------------------------- 3b6. where the data is thin
# Neither of these is a defect — you cannot invent a second veterinary clinic — but
# both are the kind of gap that becomes invisible once you stop looking at it. Kept
# as warnings so every run says out loud where the coverage is weakest.
_by_cat = Counter(p['c'] for p in P)
_thin = sorted(k for k, v in _by_cat.items() if v <= 1)
if _thin:
    warn('%d categor%s with a single entry: %s — genuinely rare in this city, or '
         'simply not finished?' % (len(_thin), 'y' if len(_thin) == 1 else 'ies',
                                   ', '.join(_thin)))
_by_reg = Counter(p['g'] for p in P)
if _by_reg:
    _busiest = max(_by_reg.values())
    _thin_regions = sorted((k for k, v in _by_reg.items() if v * 4 < _busiest),
                           key=lambda k: _by_reg[k])
    if _thin_regions:
        warn('region coverage is uneven — %s vs %d in the best-covered area'
             % (', '.join('%s %d' % (k, _by_reg[k]) for k in _thin_regions), _busiest))

# Every website is a promise that a page still exists. validate.py cannot test that
# (no egress here by design); check-links.py does, and wants running now and then.
_deep = [p for p in P if p.get('w') and re.match(r'https?://[^/]+/.+', p['w'])]
if _deep:
    warn('%d of %d websites are deep links, which rot fastest — run check-links.py '
         'on a networked machine now and then'
         % (len(_deep), sum(1 for p in P if p.get('w'))))

# ------------------------------------------------- 3c. provenance
# Every record has to say where its facts come from. 'official' additionally has to
# be checkable — a claim of an official source with no link to it is exactly the
# kind of unfalsifiable credibility marker this field exists to avoid.
SRC_OK = {'official', 'places', 'own', 'stub-pending-verify'}
for p in P:
    sv = p.get('src')
    if sv is None:
        fail('%r has no src (provenance) field' % p['n'])
    elif sv not in SRC_OK:
        fail('%r has an unknown src %r (allowed: %s)' % (p['n'], sv, ', '.join(sorted(SRC_OK))))
    elif sv == 'official' and not p.get('w'):
        fail('%r claims src=official but has no website to check it against' % p['n'])
for lang in LANGS:
    for k in ('lSource', 'srcOfficial', 'srcPlaces', 'srcOwn',
              'srcOfficialTip', 'srcPlacesTip', 'srcOwnTip'):
        if not re.search(r"UI\.%s\.%s\s*=" % (lang, k), html):
            fail('%s is missing the %s label' % (lang, k))

# ------------------------------------------------- 3c2. sameComplex is symmetric
# Two markers on one coordinate read as duplicate data unless the popup explains
# them, so the relation has to be complete: it points at ids that exist, never at
# itself, and both ends agree. A one-way link renders on one marker and not its
# twin, which is worse than none.
_by_id = {p['id']: p for p in P if p.get('id')}
for p in P:
    sc = p.get('sameComplex')
    if sc is None: continue
    if not isinstance(sc, list):
        fail('%r sameComplex is not a list (it holds a group, not one id)' % p['n']); continue
    for other in sc:
        if other == p.get('id'):
            fail('%r lists itself in sameComplex' % p['n'])
        elif other not in _by_id:
            fail('%r sameComplex points at id %r, which no place has' % (p['n'], other))
        elif p.get('id') not in (_by_id[other].get('sameComplex') or []):
            fail('sameComplex is one-way: %r points at %r but not the reverse'
                 % (p['n'], _by_id[other]['n']))

# ------------------------------------------------------- 3c2b. LANDMARKS resolve
# P1-F: an optional per-city array of place ids the engine labels persistently on
# the map. Optional, so a city that defines none is fine — but one that defines
# the array at all is naming ids by hand, and a stale or mistyped id would just
# silently draw one fewer label with nothing in the console to say why.
_landmarks_m = re.search(r'const LANDMARKS\s*=\s*(\[.*?\]);', script, re.S)
if _landmarks_m:
    try:
        _landmark_ids = json.loads(_landmarks_m.group(1))
    except Exception as e:
        fail('LANDMARKS does not parse as JSON: %s' % e); _landmark_ids = []
    if not isinstance(_landmark_ids, list):
        fail('LANDMARKS is not a list')
    else:
        for _lid in _landmark_ids:
            if _lid not in _by_id:
                fail('LANDMARKS lists id %r, which no place has' % _lid)
        dupes = [x for x in set(_landmark_ids) if _landmark_ids.count(x) > 1]
        if dupes: fail('LANDMARKS repeats id(s) %s' % dupes)
        # One per area is the whole design: the labels exist to spread real names
        # across the map so a reader can tell the areas apart. Two in one area
        # gives that area two names and leaves another with none, and because the
        # labels hide each other on overlap, two neighbours downtown can end up
        # showing as one. Nothing about a hand-written id list makes that visible,
        # so it is checked here rather than noticed later on a screenshot.
        _lm_by_reg = {}
        for _lid in _landmark_ids:
            _lp = _by_id.get(_lid)
            if not _lp: continue
            _lm_by_reg.setdefault(_lp.get('g'), []).append(_lp.get('n'))
        for _reg, _names in sorted(_lm_by_reg.items()):
            if len(_names) > 1:
                fail('LANDMARKS puts %d labels in area %r (%s) — one per area'
                     % (len(_names), _reg, ', '.join(_names)))
        # A label is a bare place name. Editorial ⭐ markers belong to the list and
        # the popup; the engine strips them off the label, and this says so out
        # loud so the two never drift apart silently.
        for _lid in _landmark_ids:
            _lp = _by_id.get(_lid)
            if _lp and _lp.get('n', '').lstrip()[:1] in '⭐★☆':
                warn('LANDMARKS id %r is a starred place (%s) — the engine strips '
                     'the star from the map label; check that reads right'
                     % (_lid, _lp['n']))

# ------------------------------------------------- 3c3. impossible coordinates
# Two different civic numbers on the same street cannot be metres apart. When it
# happens, one row has borrowed the other's coordinate — the failure that put a
# clinic inside a pharmacy's plaza. Same civic number is fine (that is what
# sameComplex describes) and so is an unflagged pair where one is already marked
# approximate, since the map then says so.
def civic(a):
    m = re.search(r'(\d{2,5})\s+([A-Za-z].*)$', (a or '').replace('#', ' '))
    if not m: return None
    street = re.sub(r'\b(unit|suite|ste)\b.*', '', m.group(2), flags=re.I)
    return m.group(1), re.sub(r'[^a-z]', '', street.lower())[:14]
for i in range(len(P)):
    for j in range(i + 1, len(P)):
        a, b = P[i], P[j]
        ca, cb = civic(a['a']), civic(b['a'])
        if not ca or not cb or ca[1] != cb[1] or ca[0] == cb[0]: continue
        d = math.hypot((a['lat'] - b['lat']) * 111000,
                       (a['lng'] - b['lng']) * 111000 * 0.635)
        if d < 30 and 'low' not in (a.get('precision'), b.get('precision')):
            fail('%r (%s) and %r (%s) are %dm apart but have different civic '
                 'numbers on the same street — one coordinate is borrowed'
                 % (a['n'], a['a'], b['n'], b['a'], d))

# ------------------------------------------------- 3c4. coordinates vs street geometry
# The pair check above only fires when a bad coordinate happens to land near
# another record; a lone one is caught here. On a straight street, position is
# very nearly linear in the civic number, so a line through the surveyed rows
# predicts where every other row belongs. The fit has to be robust or it defeats
# itself — the first version of this check used plain least squares, the bad rows
# were inside the sample, they dragged the line toward themselves and inflated the
# tolerance until a 231 m error passed. So: fit, drop residuals past 3x the
# median, refit, and only use streets whose surviving rows agree tightly.
def _dp(x): return len(str(x).split('.')[-1]) if '.' in str(x) else 0
def _linfit(xs, vals):
    mx = sum(xs) / len(xs); my = sum(vals) / len(vals)
    den = sum((x - mx) ** 2 for x in xs)
    if not den: return None
    return (sum((x - mx) * (v - my) for x, v in zip(xs, vals)) / den, my, mx)
def _ruler(rows):
    keep = list(rows)
    for _ in range(6):
        if len(keep) < 8: return None
        xs = [r[0] for r in keep]
        if len(set(xs)) < 5: return None
        fa = _linfit(xs, [r[1] for r in keep]); fo = _linfit(xs, [r[2] for r in keep])
        if not fa or not fo: return None
        def pred(n, fa=fa, fo=fo):
            return (fa[1] + fa[0] * (n - fa[2]), fo[1] + fo[0] * (n - fo[2]))
        res = []
        for n, la, ln in keep:
            pla, pln = pred(n)
            res.append(math.hypot((la - pla) * 111000, (ln - pln) * 111000 * 0.635))
        cut = max(3 * sorted(res)[len(res) // 2], 60)
        nxt = [r for r, d in zip(keep, res) if d <= cut]
        if len(nxt) == len(keep):
            return pred, (sum(d * d for d in res) / len(res)) ** 0.5, len(keep)
        keep = nxt
    return None
_street = {}
for p in P:
    c = civic(p['a'])
    if c: _street.setdefault(c[1], []).append((int(c[0]), p))
for _st, _items in sorted(_street.items()):
    if len(_items) < 8: continue
    _anch = [(n, p['lat'], p['lng']) for n, p in _items
             if min(_dp(p['lat']), _dp(p['lng'])) >= 5 and p.get('precision') != 'low']
    _r = _ruler(_anch)
    if not _r: continue
    _pred, _rms, _kept = _r
    if _rms > 60: continue
    for n, p in _items:
        la, ln = _pred(n)
        d = math.hypot((p['lat'] - la) * 111000, (p['lng'] - ln) * 111000 * 0.635)
        if d > 200:
            fail('%r (%s) sits %.0f m from where its street number puts it — %d rows '
                 'on that street fit a straight line to %.0f m rms, so this '
                 'coordinate is almost certainly borrowed from elsewhere'
                 % (p['n'], p['a'], d, _kept, _rms))

# ------------------------------------------------- 3d. the theme axis
# Themes overlap categories on purpose, so nothing about a place's category can
# be used to check its themes. What can be checked is that every key a record
# claims exists, is translated everywhere, has an icon and a position in the
# reading order, and that no theme is a dead chip.
TI = extract('TI'); TIC = extract('TIC'); TORDER = extract('TORDER')
if set(TORDER) != set(TI):
    fail('TORDER and TI disagree: only in TORDER=%s, only in TI=%s'
         % (sorted(set(TORDER) - set(TI)), sorted(set(TI) - set(TORDER))))
if len(TORDER) != len(set(TORDER)):
    fail('TORDER lists a theme twice')
for k, v in TI.items():
    miss = [l for l in LANGS if not v.get(l)]
    if miss: fail('TI[%r] missing languages %s' % (k, miss))
    if k not in TIC: fail('TIC has no icon for theme %r' % k)
_theme_n = Counter()
for i, p in enumerate(P):
    t = p.get('t')
    if t is None: continue
    if not isinstance(t, list):
        fail('%r has a non-list t (themes must stay an array)' % p['n']); continue
    if len(set(t)) != len(t):
        fail('%r lists the same theme twice: %r' % (p['n'], t))
    if [k for k in TORDER if k in t] != t:
        fail('%r themes are out of TORDER order: %r' % (p['n'], t))
    for k in t:
        if k not in TI: fail('%r has unknown theme %r' % (p['n'], k))
        else: _theme_n[k] += 1
_empty = [k for k in TORDER if not _theme_n[k]]
if _empty:
    fail('theme(s) with no places at all — a chip that can only ever show (0): %s'
         % ', '.join(_empty))
_thin_t = [k for k in TORDER if 0 < _theme_n[k] <= 5]
if _thin_t:
    warn('thin theme(s): %s — honest, but the chip will look broken next to the '
         'others; either grow the data or reconsider the theme'
         % ', '.join('%s %d' % (k, _theme_n[k]) for k in _thin_t))
_untagged = sum(1 for p in P if not p.get('t'))
if _untagged > len(P) * 0.4:
    warn('%d of %d places carry no theme at all (%.0f%%) — the theme axis only '
         'helps where it is populated' % (_untagged, len(P), 100.0 * _untagged / len(P)))

tagset = set(re.findall(r"UI\.zh\.(t[A-Za-z0-9]+)\s*=", html))
for p in P:
    if p.get('tag') and p['tag'] not in tagset:
        fail('%r uses tag %r which no language defines' % (p['n'], p['tag']))

# ---------------------------------------------------------------- 4. structured hours
for p in P:
    h = p.get('h')
    if h is None: continue
    if isinstance(h, str):
        fail('%r hours reverted to a plain string' % p['n']); continue
    if not any(k in h for k in ('a', 'r', 's', 'k')):
        fail('%r hours object has no renderable content: %r' % (p['n'], h))
    for rng in h.get('r', []):
        if len(rng) != 5: fail('%r malformed hours range %r' % (p['n'], rng))
        d1, d2, o, c, ap = rng
        if not (1 <= d1 <= 7 and 1 <= d2 <= 7 and d1 <= d2):
            fail('%r bad day range %r' % (p['n'], rng))
        if o is not None and not (0 <= o < 1440): fail('%r bad open minute %r' % (p['n'], rng))
        if o is not None and c is not None and c <= o:
            fail('%r close is not after open: %r' % (p['n'], rng))
        # fmtHours() would render 1560 as "2 AM" but openState() cannot evaluate it
        if c is not None and c > 1440:
            fail('%r close minute past midnight (%r) — encode overnight hours as a note, not a range' % (p['n'], rng))

# ---------------------------------------------------------------- 5. i18n parity
base = set(UI['zh'].keys())
for l in LANGS:
    if l not in UI: fail('UI missing language %r' % l); continue
    d = set(UI[l].keys())
    if d != base:
        fail('UI[%s] key mismatch: missing=%s extra=%s' % (l, sorted(base - d), sorted(d - base)))

post = {l: set(re.findall(r'UI\.' + l + r'\.([A-Za-z0-9_]+)\s*=', html)) for l in LANGS}
for l in LANGS[1:]:
    d = post['zh'] ^ post[l]
    if d: fail('post-assigned UI keys differ for %s: %s' % (l, sorted(d)))

for name, obj in (('CI', CI), ('RI', RI), ('GN', GN)):
    for k, v in obj.items():
        miss = [l for l in LANGS if l not in v]
        if miss: fail('%s[%r] missing languages %s' % (name, k, miss))

for k in CI:
    for m, nm in ((CO, 'CO'), (CD, 'CD'), (IC, 'IC')):
        if k not in m: fail('%s missing entry for category %r' % (nm, k))

# every UI key referenced in code must exist in every language
used = set(re.findall(r'\bu\.([A-Za-z0-9_]+)', script)) | set(re.findall(r'UI\[[^\]]+\]\.([A-Za-z0-9_]+)', script))
known = base | post['zh']
# `u` is also used as a local Set/Array in a couple of places
SHADOW = {'add','delete','has','size','clear','forEach','map','filter','push','join','d'}
for k in sorted(used - known - SHADOW):
    fail('code reads u.%s but no language defines it' % k)

# ------------------------------------------------- 5b. one language's punctuation
# The list separator between closed days was written inline as the ideographic
# comma because the Chinese copy was drafted first, so English readers were shown
# "Closed: Tue、Thu、Sun" for months and nobody read that branch's English output.
# Punctuation is per-language copy and belongs in UI, never in the code that
# assembles a sentence. This strips every UI assignment — the legitimate home for
# such characters — and fails on what is left.
_cjk_punct = '、，：；！？（）【】「」『』〜･'
_code = re.sub(r'UI\.\w+\.\w+\s*=\s*`(?:[^`\\]|\\.)*`\s*;', '', script, flags=re.S)
_code = re.sub(r"UI\.\w+\.\w+\s*=\s*'(?:[^'\\]|\\.)*'\s*;", '', _code)
_code = re.sub(r'UI\.\w+\.\w+\s*=\s*"(?:[^"\\]|\\.)*"\s*;', '', _code)
_code = re.sub(r'UI\.\w+\.\w+\s*=\s*[^;\n]*;', '', _code)          # arrow-function labels
_code = re.sub(r'const UI=\{.*?\n', '', _code, flags=re.S, count=1)
for _m in re.finditer(r"'([^'\n]{0,6})'", _code):
    _hit = [c for c in _m.group(1) if c in _cjk_punct]
    if _hit:
        fail("CJK punctuation %r is hard-coded in the code that builds a sentence "
             "(%r) — it renders in all five languages; move it into UI as a "
             "per-language key" % (''.join(_hit), _m.group(0)))

# ------------------------------------------------- 5c. the language switcher
# Two of the five buttons happened to be self-describing because their scripts
# are distinctive; the other three announced as bare letters in the wrong voice.
# Whatever the visible label, every button must carry the language it switches to
# and a name in that language — the same rule for all five, not for the ones that
# needed it least.
_lang_btns = re.findall(r'<button class="lang-btn[^>]*>', html)
if len(_lang_btns) != len(LANGS):
    fail('expected %d language buttons, found %d' % (len(LANGS), len(_lang_btns)))
for _b in _lang_btns:
    _dl = re.search(r'data-lang="(\w+)"', _b)
    _key = _dl.group(1) if _dl else '?'
    for _attr in ('lang', 'aria-label', 'title'):
        if not re.search(r'\b%s="[^"]+"' % _attr, _b):
            fail('the %s language button has no %s attribute — a screen reader '
                 'reads it in the wrong language' % (_key, _attr))

# ---------------------------------------------------------------- 6. DOM contract
ids_used = set(re.findall(r"getElementById\('([\w-]+)'\)", html))
ids_def = set(re.findall(r'id="([\w-]+)"', html))
missing = ids_used - ids_def
if missing: fail('getElementById targets that do not exist: %s' % sorted(missing))

# ---------------------------------------------------------------- 7. no interactive non-buttons
_bs = html.index('<style id="app-css">') if '<style id="app-css">' in html else html.index('<style>')
body = html[html.index('</style>', _bs):]
for m in re.finditer(r'<(div|span)\b[^>]*\bid="(allCat2|noCat2)"', body):
    fail('%s#%s is still a non-button interactive control' % (m.group(1), m.group(2)))
for m in re.finditer(r'<(div|span)([^>]*)\sonclick=', body):
    fail('non-button element with inline onclick: <%s%s' % (m.group(1), m.group(2)[:60]))
for m in re.finditer(r"createElement\('(div|span)'\);\s*(\w+)\.className='([\w-]+)[^']*';", script):
    tag, var, cls = m.groups()
    seg = script[m.end():m.end() + 900]
    if re.search(r'\b' + var + r'\.onclick\s*=', seg):
        fail("dynamically created <%s class=%s> gets an onclick — should be a <button>" % (tag, cls))

# ---------------------------------------------------------------- 8. button chrome reset
_c = re.search(r'<style id="app-css">(.*?)</style>', html, re.S) or re.search(r'<style>(.*?)</style>', html, re.S)
css = _c.group(1)
btn_classes = set()
for m in re.finditer(r"createElement\('button'\);\s*\w+\.className='([\w-]+)", script):
    btn_classes.add(m.group(1))
for m in re.finditer(r"<button[^>]*class=\"([\w-]+)", body):
    btn_classes.add(m.group(1))
for m in re.finditer(r'<button[^>]*class=\\?"([\w-]+)', script):
    btn_classes.add(m.group(1))
# NOTE: `appearance:none` does NOT clear Chrome's UA `border:2px outset` /
# `background:ButtonFace`. A button class must explicitly set BOTH, or supply
# its own background+border, or it renders as a grey 3-D system button.
flat = re.sub(r'\s+', ' ', css)
sets_bg = set(); sets_border = set()
for m in re.finditer(r'([^{}]+)\{([^}]*)\}', flat):
    sel, decl = m.group(1), m.group(2)
    cls = set(re.findall(r'\.([\w-]+)', sel))
    if re.search(r'(^|;)\s*background(-color)?\s*:', decl): sets_bg |= cls
    if re.search(r'(^|;)\s*border\s*:', decl): sets_border |= cls
for c in sorted(btn_classes):
    missing_props = []
    if c not in sets_bg: missing_props.append('background')
    if c not in sets_border: missing_props.append('border')
    if missing_props:
        fail('button class .%s never sets %s — will render as a grey system button'
             % (c, ' and '.join(missing_props)))

# ---------------------------------------------------------------- 9. nested buttons
plain = re.sub(r'/\*.*?\*/', '', body, flags=re.S)
if re.search(r'<button[^>]*>(?:(?!</button>).)*<button', plain, re.S):
    fail('nested <button> found in markup')
if re.search(r"'<button[^>]*>[^']*<button", script):
    fail('nested <button> found in a generated HTML string')

# ------------------------------------------------- 9b. external link hygiene
# Modern browsers imply noopener, older ones do not. Two quoting styles exist in
# this file: plain HTML in the markup, and escaped quotes inside the serialised UI
# object — the first pass at this missed the second kind entirely.
_missing = (re.findall(r'<a [^>]*?target="_blank"(?![^>]*rel=)[^>]*?>', html)
            + re.findall(r'<a [^>]*?target=\\"_blank\\"(?![^>]*rel=)[^>]*?>', html))
if _missing:
    fail('%d external link(s) with target=_blank but no rel=noopener, e.g. %s'
         % (len(_missing), _missing[0][:70]))

# ------------------------------------------------- 9c. bus coverage honesty
# The copy used to say "14 main routes included", which reads as "we picked 14 of
# more". The operator's own feed has exactly 14 regular routes; 8/11/12/15 do not
# exist. If BR ever changes size, the sentence has to change with it.
_br_n = len(BR)
for lang in LANGS:
    m = re.search(r"UI\.%s\.busCoverage='([^']*)'" % lang, html)
    if not m:
        fail('%s has no busCoverage line' % lang); continue
    if str(_br_n) not in m.group(1):
        fail('%s busCoverage does not state the route count (%d)' % (lang, _br_n))
if not re.search(r"const BUS_SOURCE=\{", script):
    fail('BUS_SOURCE provenance block is missing')

# ---------------------------------------------------------------- 10. duplicate affordances
if 'search-cancel-button' not in css and 'type="search"' in body:
    fail('input[type=search] without hiding the native clear button (duplicate ✕)')
for lang in LANGS:
    m = re.search(r"UI\.%s\.searchPlaceholder='([^']*)'" % lang, html)
    if m and '🔍' in m.group(1):
        fail('%s search placeholder still contains a magnifier (duplicate icon)' % lang)

# ---------------------------------------------------------------- 11. dead CSS
defined = set(re.findall(r'\.([a-zA-Z][\w-]*)\s*(?=[,{:.\s])', css))
SKIP = {'leaflet','open','active','show','searching','all','none','partial','s','m','l',
        'c','w','n','x','primary','hi','mid','lo','ok','new','total','kcluster'}
for cls in sorted(defined - SKIP):
    if cls.startswith('leaflet'): continue
    # Boundary set includes a bare backslash too: a class referenced only inside
    # the UI JSON literal (e.g. class=\"footer-emergency\") is escaped there, so
    # the character actually adjacent to the name is \ , not a quote.
    if re.search(r'["\'\\\s.]' + re.escape(cls) + r'["\'\\\s.]', body): continue
    if ("'" + cls + "'") in script or ('"' + cls + '"') in script: continue
    if re.search(r"className='" + re.escape(cls), script): continue
    # Names built by concatenation, e.g. 'src-'+p.src -> .src-official. Count the
    # class as used if its prefix is assembled that way anywhere in the script.
    if '-' in cls and (cls.rsplit('-', 1)[0] + "-'+") in script.replace(' ', ''):
        continue
    warn('CSS class .%s appears unused' % cls)

# ---------------------------------------------------------------- 12. head/meta
for need, label in (('name="description"', 'meta description'),
                    ('rel="icon"', 'favicon'),
                    ('property="og:title"', 'og:title')):
    if need not in html: warn('missing %s' % label)


# --------------------------------------------------- 13. runtime symbol sanity
# node --check only proves the file parses; these catch "called but never defined"
# strip every string/template literal first — prose inside them ("de la (…)")
# otherwise looks like a function call
code_only = re.sub(r'`(?:[^`\\]|\\.)*`', '``', script, flags=re.S)
code_only = re.sub(r"'(?:[^'\\\n]|\\.)*'", "''", code_only)
code_only = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', code_only)
code_only = re.sub(r'//[^\n]*', '', code_only)
code_only = re.sub(r'/\*.*?\*/', '', code_only, flags=re.S)
called = set(re.findall(r'(?<![.\w])([a-zA-Z_][\w]*)\s*\(', code_only))
defined = set(re.findall(r'function\s+([A-Za-z_][\w]*)', script))
defined |= set(re.findall(r'(?:const|let|var)\s+([A-Za-z_][\w]*)\s*=', script))
defined |= set(re.findall(r'([A-Za-z_][\w]*)\s*=\s*(?:function|\()', script))
defined |= set(re.findall(r'(?:function|catch|forEach\()\s*\(?\s*([a-z]\w*)', script))
# A named function's OWN parameters are legitimate callable symbols inside its
# body (a callback passed in and invoked, e.g. `function f(x,onDone){onDone()}`)
# but the patterns above only ever pick up a single identifier right after
# function/catch/forEach( — for a named function that is the function's own name,
# not any of its parameters. Every parameter of every named function declaration
# is added here too, so a higher-order function that calls its own callback
# parameter does not read as "calls onDone() but nothing defines it".
for _params in re.findall(r'function\s+[A-Za-z_]\w*\s*\(([^)]*)\)', script):
    for _p in _params.split(','):
        _p = _p.strip().split('=')[0].strip()
        if re.match(r'^[A-Za-z_]\w*$', _p): defined.add(_p)
BUILTIN = {'if','for','while','switch','catch','return','typeof','function','new','JSON',
           'Number','String','Set','Map','Array','Object','Math','parseInt','parseFloat',
           'setTimeout','clearTimeout','encodeURIComponent','isNaN','L','require','console',
           'Boolean','Date','RegExp','alert','fetch','performance','getComputedStyle',
           'requestAnimationFrame','setInterval','clearInterval','decodeURIComponent'}
for name in sorted(called - defined - BUILTIN):
    if name.isupper() or name[0].isupper(): continue
    fail('calls %s() but nothing in the script defines it' % name)

# --------------------------------------------------- 14. hidden-attribute traps
# The trap: `hidden` is a user-agent stylesheet rule ([hidden]{display:none}), and
# ANY author rule that sets a display on the same element beats it regardless of
# specificity. An element that JS hides with .hidden=true, or that ships with a
# static hidden attribute, then stays on screen — usually only under the media
# query that supplied the display, which is why these survive desktop testing.
#
# This used to check a hardcoded list of four classes, and so missed every real
# instance of the bug: #shareNative (visible on any browser without
# navigator.share), #searchClear (visible on every touch device) and #busIndicator
# (visible, but left in `hidden` and therefore mute to screen readers). It now
# derives both sides — which elements are hideable, and which selectors give them
# a display — from the file itself.
# Variables that alias an element, so `fooEl.hidden=` counts as hiding #foo. Built
# from the actual declarations rather than guessed from the name — `panelAreaEl`
# aliases #panelArea, not #panel, and a prefix match would flag the wrong element.
alias = {}
for m in re.finditer(r"\b([A-Za-z_]\w*)\s*=\s*document\.getElementById\('([^']+)'\)", script):
    alias[m.group(1)] = m.group(2)
hidden_ids = set()
for m in re.finditer(r"document\.getElementById\('([^']+)'\)\.hidden\s*=", script):
    hidden_ids.add(m.group(1))
for m in re.finditer(r"\b([A-Za-z_]\w*)\.hidden\s*=", script):
    if m.group(1) in alias:
        hidden_ids.add(alias[m.group(1)])

hideable = {}          # id -> set of classes, for every element that can carry `hidden`
for m in re.finditer(r'<([a-z]+)\b([^>]*)>', body, re.I):
    attrs = m.group(2)
    eid = re.search(r'\bid="([^"]+)"', attrs)
    if not eid:
        continue
    cls = re.search(r'\bclass="([^"]*)"', attrs)
    classes = set((cls.group(1) if cls else '').split())
    static_hidden = re.search(r'\shidden(?=[\s>/=])', attrs) is not None
    if static_hidden or eid.group(1) in hidden_ids:
        hideable[eid.group(1)] = classes

# Every author rule that gives some selector a display other than none, mapped
# back to the bare .class / #id tokens it applies to.
display_selectors = {}
for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', flat):
    sel, decls = m.group(1), m.group(2)
    d = re.search(r'(?:^|;)\s*display:\s*([a-z-]+)', decls)
    if not d or d.group(1) == 'none':
        continue
    if '[hidden]' in sel:
        continue
    for tok in re.findall(r'[.#][\w-]+', sel):
        display_selectors.setdefault(tok, set()).add(d.group(1))

for eid, classes in sorted(hideable.items()):
    tokens = ['#' + eid] + ['.' + c for c in sorted(classes)]
    offenders = [t for t in tokens if t in display_selectors]
    if not offenders:
        continue
    # An override on the id, or on any class the element carries, defuses it.
    guarded = any(re.search(re.escape(t) + r'\[hidden\]', flat) for t in tokens)
    if not guarded:
        fail('#%s can be hidden but %s sets a display — [hidden] will not hide it; '
             'add %s[hidden]{display:none}' % (eid, '/'.join(offenders), tokens[0]))


# ------------------------------------------------- 15. city coupling stays in CITY
# Checked against the actual translated strings rather than a slice of the file:
# once the data moved into its own file it sits between UI and CI, and place names
# legitimately contain the city name.
m = re.search(r"const CITY=\{(.*?)\n\};", html, re.S)
if not m:
    fail('CITY config block is missing')
else:
    cn = re.search(r"name:\{zh:'([^']+)'", m.group(1))
    cityname = cn.group(1) if cn else None
    copy_strings = []
    for lang in LANGS:
        copy_strings += [v for v in UI[lang].values() if isinstance(v, str)]
    copy_strings += re.findall(r"UI\.(?:zh|en|fr|es|ko)\.[A-Za-z0-9_]+=`(.*?)\n`;", script, re.S)
    copy_strings += re.findall(r"UI\.(?:zh|en|fr|es|ko)\.[A-Za-z0-9_]+='((?:[^'\\]|\\.)*)';", script)
    blob = '\n'.join(copy_strings)
    checks = [(cityname, '{CITY}')] if cityname else []
    checks += [('BC Transit', '{TRANSIT}'), ('SD73', '{SD}')]
    for lit, ph in checks:
        n = blob.count(lit)
        if n:
            where = [c[:70] for c in copy_strings if lit in c][:2]
            fail('%d literal %r in translated copy — should be %s (e.g. %s)' % (n, lit, ph, where))

# ------------------------------------------------- 16. the split stays buildable
import os as _os
if _os.path.exists('src/engine.html'):
    eng = open('src/engine.html', encoding='utf-8').read()
    if '/*__CITY_DATA__*/' not in eng:
        fail('src/engine.html has lost its data marker — build.py cannot fill it')
    for v in ('const P=', 'const BR=', 'const CITY=', 'const RI=', 'const TASKS='):
        if v in eng:
            fail('city data %r leaked back into the engine' % v)
    # 2026-09-11: the engine must not carry this city's phone numbers or offices
    # outside the UI strings that are already placeholder-checked above. Local
    # numbers in code are the surest sign a city fact has crept into the engine.
    _eng_script = eng[eng.find('<script id="app">'):]
    _eng_code = re.sub(r"UI\.[a-z]{2}\.[A-Za-z0-9_]+=(?:'(?:[^'\\]|\\.)*'|`[^`]*`);", '', _eng_script)
    _eng_code = _eng_code[:_eng_code.find('const UI=')] + _eng_code[_eng_code.find('\n', _eng_code.find('const UI=')):] if 'const UI=' in _eng_code else _eng_code
    _local_numbers = set(re.findall(r'\b(?:250|778|236)-\d{3}-\d{4}\b', _eng_code))
    if _local_numbers:
        warn('local phone number(s) in engine code (should live in data or UI strings): %s' % sorted(_local_numbers)[:5])
    if 'guideCity' in eng.replace('GUIDE_ORDER', ''):
        if re.search(r"UI\.\w+\.guideCity=`", eng):
            fail('guideCity (city-tier guide) leaked back into the engine')

# ------------------------------------------------- 16b. the three clocks agree
# (2026-09-11) VERIFIED (the page-wide "last checked" date), DATA_VERSION and
# the per-record stamps are kept by hand. The page tells readers the whole set
# was checked on VERIFIED; if a release ships weeks after that date without
# anyone touching it, that sentence is stale on the day it is deployed.
_vm = re.search(r"const VERIFIED='(\d{4})-(\d{2})-(\d{2})'", html)
_dm = re.search(r"const DATA_VERSION='(\d{4})\.(\d{2})\.(\d{2})[a-z]?'", html)
if not _vm or not _dm:
    fail('VERIFIED or DATA_VERSION missing or malformed')
else:
    import datetime as _dt2
    _vd = _dt2.date(int(_vm.group(1)), int(_vm.group(2)), int(_vm.group(3)))
    _dd = _dt2.date(int(_dm.group(1)), int(_dm.group(2)), int(_dm.group(3)))
    if (_dd - _vd).days > 45:
        fail('VERIFIED (%s) is %d days behind DATA_VERSION (%s) — recheck the data or update the date honestly'
             % (_vd, (_dd - _vd).days, _dd))
    if _vd > _dd:
        fail('VERIFIED (%s) is later than DATA_VERSION (%s)' % (_vd, _dd))
    # (2026-09-13) the task cards carry their own check date (CITY.tasksChecked),
    # shown at the foot of every card. Same rule: it must exist and not go stale.
    _tm = re.search(r"tasksChecked:'(\d{4})-(\d{2})-(\d{2})'", html)
    if not _tm:
        fail("CITY.tasksChecked missing — the card footer's check date has nowhere to come from")
    else:
        _td = _dt2.date(int(_tm.group(1)), int(_tm.group(2)), int(_tm.group(3)))
        if (_dd - _td).days > 60:
            fail('CITY.tasksChecked (%s) is %d days behind DATA_VERSION (%s) — reread the 14 cards against their sources'
                 % (_td, (_dd - _td).days, _dd))
    if '{TD}' in html and "replace('{TD}'" not in html:
        fail('taskVerified uses {TD} but nothing substitutes it')
# (2026-09-13) the map imagery host must be one whose terms allow a public app, and
# the Worker's CSP must allow exactly that host — a mismatch is a blank map in production
_tile = re.search(r"L\.tileLayer\('https://\{s\}\.([a-z0-9.\-]+)/", html)
if not _tile:
    fail('tile layer URL not found')
else:
    _host = _tile.group(1)
    if 'tile.openstreetmap.org' in _host:
        fail("map tiles come from OpenStreetMap's volunteer servers — their policy forbids a distributed app and they blocked this site on 2026-09-13")
    _wpath = os.path.join(HERE, "worker.js")
    if os.path.exists(_wpath):
        _w = open(_wpath, encoding='utf-8').read()
        if _host.split('.',1)[-1] not in _w:
            fail('worker.js CSP img-src does not allow the tile host %s' % _host)

# ------------------------------------------------- 17. data has a shelf life
# (2026-09-10) Hours and phone numbers are the first fields to go stale, and a
# row that says "checked" but was checked a year ago is worse for trust than a
# row that says nothing. The stamp `v` (YYYY-MM) is compared to the build date:
# past six months is a warning, past twelve is a failure — "stale" becomes
# something the build says out loud rather than something someone remembers.
import datetime as _dt
_today = _dt.date.today()
def _months_old(v):
    m = re.match(r'^(\d{4})-(\d{2})', str(v or ''))
    if not m: return None
    y, mo = int(m.group(1)), int(m.group(2))
    return (_today.year - y) * 12 + (_today.month - mo)
_stale6 = [p['n'] for p in P if (_months_old(p.get('v')) or 0) > 6 and (_months_old(p.get('v')) or 0) <= 12]
_stale12 = [p['n'] for p in P if (_months_old(p.get('v')) or 0) > 12]
_nostamp = [p['n'] for p in P if _months_old(p.get('v')) is None]
if _stale6:
    warn('%d row(s) last checked more than 6 months ago — due for a recheck: %s'
         % (len(_stale6), ', '.join(_stale6[:8]) + ('…' if len(_stale6) > 8 else '')))
if _stale12:
    fail('%d row(s) last checked more than 12 months ago: %s' % (len(_stale12), ', '.join(_stale12[:8])))
if _nostamp:
    fail('%d row(s) carry no verification stamp: %s' % (len(_nostamp), ', '.join(_nostamp[:6])))

# ------------------------------------------------- 18. quarantine stays out
# A row in QUARANTINE was looked for and not found. It must never also be in P:
# the whole point of the list is that the app does not show it.
_qm = re.search(r'const QUARANTINE=(\[.*?\]);', script, re.S)
if _qm:
    try:
        _q = json.loads(_qm.group(1))
        _qn = {x.get('n') for x in _q}
        _leak = [p['n'] for p in P if p['n'] in _qn]
        if _leak: fail('quarantined row(s) are back in P: %s' % _leak)
        for x in _q:
            if not x.get('quarantined'): fail('QUARANTINE row %r has no reason recorded' % x.get('n'))
    except ValueError as e:
        fail('QUARANTINE does not parse: %s' % e)

# ------------------------------------------------- 19. a card sends you to the right kind of place
# The card's "where do I go" is a place id; nothing stopped it pointing at a
# restaurant. Each card names the categories an office for it may have.
_TASK_CATS = {
  'settle': {'gov'}, 'sin': {'gov'}, 'msp': {'gov'}, 'licence': {'gov'}, 'bank': {'bank'},
  'connect': {'commctr','library','indigenous'}, 'sick': {'hospital'}, 'hardship': {'foodbank','support'},
  'legal': {'legal'}, 'eldercare': {'commctr','hospital','support'},
}
_tm = re.search(r'const TASKS=(\[.*?\]);\n', html, re.S)
if not _tm:
    fail('TASKS (task cards) missing from the built file — the data file must define them')
if _tm:
    try:
        _tasks = json.loads(_tm.group(1))
        # every card complete in every language, every place id real
        for t in _tasks:
            for k in ('q', 't'):
                if not all(isinstance(t.get(k, {}).get(l), str) and t[k][l].strip() for l in LANGS):
                    fail('task %r field %r is not complete in all six languages' % (t.get('id'), k))
            for st in t.get('steps', []):
                if not all(isinstance(st.get(l), str) and st[l].strip() for l in LANGS):
                    fail('task %r has a step missing a language' % t.get('id'))
            if t.get('place') and t['place'] not in _by_id:
                fail('task %r points at unknown place id %r' % (t.get('id'), t['place']))
        for t in _tasks:
            if t.get('place') and t['id'] in _TASK_CATS:
                pl = _by_id.get(t['place'])
                if pl and pl['c'] not in _TASK_CATS[t['id']]:
                    fail('task %r points at %r, a %s — expected one of %s'
                         % (t['id'], pl['n'], pl['c'], sorted(_TASK_CATS[t['id']])))
    except ValueError as e:
        fail('TASKS does not parse: %s' % e)

# ---------------------------------------------------------------- report
print('places=%d categories=%d regions=%d routes=%d  size=%dKB'
      % (len(P), len(CI), len(RI), len(BR), len(html.encode()) // 1024))
if WARN:
    print('\n%d warning(s):' % len(WARN))
    for w in WARN: print('  ~ ' + w)
if FAIL:
    print('\n%d FAILURE(S):' % len(FAIL))
    for f in FAIL: print('  ✗ ' + f)
    sys.exit(1)
print('\nall invariants hold')
