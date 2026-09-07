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

LANGS = ['zh', 'en', 'fr', 'es', 'ko']

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
    # fr/es/ko are optional per record (the engine falls back to English), but a
    # half-translated note is worse than none: it means one language silently shows
    # another's text while its neighbours are translated.
    extra = [k for k in ('fr', 'es', 'ko') if nt.get(k)]
    if extra and len(extra) != 3:
        fail('%r note has %s but not the rest — translate all three or none'
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
for p in P:
    for t in (p.get('note') or {}).values():
        if '新移民' in t:
            fail('%r note uses 新移民; the house wording is 新居民' % p['n'])

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
BUILTIN = {'if','for','while','switch','catch','return','typeof','function','new','JSON',
           'Number','String','Set','Map','Array','Object','Math','parseInt','parseFloat',
           'setTimeout','clearTimeout','encodeURIComponent','isNaN','L','require','console',
           'Boolean','Date','RegExp','alert','fetch','performance','getComputedStyle',
           'requestAnimationFrame'}
for name in sorted(called - defined - BUILTIN):
    if name.isupper() or name[0].isupper(): continue
    fail('calls %s() but nothing in the script defines it' % name)

# --------------------------------------------------- 14. hidden-attribute traps
for m in re.finditer(r'\.([\w-]+)\s*\{[^}]*display:\s*(flex|grid|block|inline-flex)', flat):
    cls = m.group(1)
    if re.search(r"getElementById\('[^']*'\)\.hidden\s*=", script) and cls in ('active-filters','fhint','empty-state','search-note'):
        if not re.search(re.escape('.'+cls)+r'\[hidden\]', flat):
            fail('.%s sets display but has no [hidden] override — .hidden=true will not hide it' % cls)


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
    for v in ('const P=', 'const BR=', 'const CITY=', 'const RI='):
        if v in eng:
            fail('city data %r leaked back into the engine' % v)
    if 'guideCity' in eng.replace('GUIDE_ORDER', ''):
        if re.search(r"UI\.\w+\.guideCity=`", eng):
            fail('guideCity (city-tier guide) leaked back into the engine')

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
