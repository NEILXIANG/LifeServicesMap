"""Shared helpers for the city importers (scripts/importers/*.py).

Every importer follows the same contract, so any city can run any of them:

* It writes into cities/<city>/places.json through kamdata (indented JSON).
* Re-runnable: records it created earlier (looked up in cities/<city>/import/provenance.json
  under its own source key) are replaced, never duplicated. A record whose `src` has since been
  promoted by a person (`own`, or `official` with a verified `v`) is left alone.
* Coordinates follow the methodology rule (docs/guides/新城市扩展方法论与标准.md §5.3): the
  government geocoder's point is used when it scores >= 95 at civic level and agrees with the
  dataset's own point within 150 m; otherwise the dataset's point is kept and marked
  precision:'low'.
* Area (`g`) comes from the nearest hand-assigned records (majority of the 5 nearest), so an
  importer needs no hand-drawn boundaries; West-of-the-lake style splits can be forced by
  locality through `area_by_locality`.
* De-duplication: a similar name within 400 m, or the same phone number within 40 m, counts as
  already listed. Two DIFFERENT operators in one building are both kept and linked with
  `sameComplex` (2026-10-03, Kelowna: the Kamloops rule "same category within 40 m = duplicate"
  dropped real centres sharing a building — each has its own phone, a parent needs both).
"""
import datetime, hashlib, json, math, os, re, sys

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(_here)))
sys.path.insert(0, os.path.dirname(_here))
import kamdata
from bc_geocode import geocode

# local date of the city being imported (kamdata.today), not the machine's: MONTH goes into every record's `v`
TODAY = kamdata.today()
MONTH = TODAY.strftime('%Y-%m')

def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

def dist_m(a_lat, a_lng, b_lat, b_lng):
    return math.hypot((a_lat - b_lat) * 111000, (a_lng - b_lng) * 111000 * math.cos(math.radians(a_lat)))

ACRONYM = {'bgc': 'BGC', 'ece': 'ECE', 'ymca': 'YMCA', 'ywca': 'YWCA', 'ubc': 'UBC', 'ubco': 'UBCO', 'bc': 'BC', 'sd23': 'SD23',
           'ccrr': 'CCRR', 'ltd': 'Ltd', 'inc': 'Inc', 'csf': 'CSF', 'kcr': 'KCR', 'ok': 'OK'}
SMALL = {'and', 'of', 'the', 'at', 'in', 'for', 'de', 'la', 'le', 'du', 'des'}

def tidy(s):
    """'LITTLE  BEARS CHILD CARE-' -> 'Little Bears Child Care' (keeps acronyms and ordinals)."""
    s = re.sub(r'\s+', ' ', s or '').strip(' -–—')
    out = []
    for i, t in enumerate(s.split(' ')):
        low = t.lower()
        if low in ACRONYM: out.append(ACRONYM[low])
        elif low in SMALL and i > 0: out.append(low)
        elif re.match(r'^\d+(st|nd|rd|th)$', low): out.append(low)
        elif low.startswith('mc') and len(low) > 2: out.append('Mc' + low[2].upper() + low[3:])
        else: out.append(re.sub(r'(^|[-/(])([a-z])', lambda m: m.group(1) + m.group(2).upper(), low))
    return ' '.join(out)

GENERIC = {'the', 'and', 'of', 'at', 'centre', 'center', 'child', 'care', 'childcare', 'daycare', 'inc', 'ltd',
           'society', 'academy', 'preschool', 'early', 'learning', 'kids', 'program', 'programme', 'unit',
           'out', 'school', 'before', 'after', 'club', 'clubhouse', 'years', 'group', 'montessori',
           # place words: every record in a city shares them
           'north', 'south', 'east', 'west', 'upper', 'lower', 'downtown', 'okanagan', 'kelowna', 'kamloops',
           'rutland', 'glenmore', 'mission', 'westbank', 'city', 'park', 'road', 'street', 'avenue', 'drive'}

def similar(a, b, words=True):
    """Same place under two spellings: one name contains the other, or they share most words."""
    na, nb = norm(a), norm(b)
    if na and nb and (na in nb or nb in na): return True
    if not words: return False
    wa = {w for w in re.findall(r'[a-z0-9]+', a.lower()) if w not in GENERIC and len(w) > 2}
    wb = {w for w in re.findall(r'[a-z0-9]+', b.lower()) if w not in GENERIC and len(w) > 2}
    return bool(wa and wb) and len(wa & wb) / min(len(wa), len(wb)) >= 0.6

LANG4 = ('fr', 'es', 'ko', 'ja')

def translations_path(city):
    return kamdata.import_path('translations.json', city)

def load_translations(city):
    """cities/<city>/import/translations.json: {id: {"src_en": <English it was made from>, "fr", "es", "ko", "ja"}}.
    Kept apart from places.json so re-running an importer never throws translations away."""
    try:
        return json.load(open(translations_path(city), encoding='utf-8'))
    except FileNotFoundError:
        return {}

def apply_translation(rec, translations):
    """Add fr/es/ko/ja when they were made from exactly this English note; a changed English
    note makes the old translation stale (it is not applied, and shows up as untranslated)."""
    t = translations.get(rec.get('id'))
    if not t or 'note' not in rec: return False
    if t.get('src_en') != rec['note'].get('en'): return False
    if not all(t.get(l) for l in LANG4): return False
    for l in LANG4: rec['note'][l] = t[l]
    return True

def hours_path(city):
    return kamdata.import_path('hours.json', city)

def load_hours(city):
    """cities/<city>/import/hours.json: {id: {"hours_text", "services_text", "source_url", "fetched"}} —
    hours copied verbatim from each place's own page, kept apart so re-imports never lose them."""
    try:
        return json.load(open(hours_path(city), encoding='utf-8'))
    except FileNotFoundError:
        return {}

def apply_hours(rec, hours):
    """Structured hours from the stored official wording, only where it is fully understood."""
    from hours import parse_hours, parse_services
    e = hours.get(rec.get('id'))
    if not e or rec.get('h'): return False
    h = parse_hours(e.get('hours_text'))
    if not h and e.get('services_text'):
        s = parse_services(e['services_text'])
        if s: h = {'s': s}
    if h: rec['h'] = h; return True
    return False

class CityImport:
    def __init__(self, city, source, area_by_locality=None):
        kamdata.use(city)
        self.city, self.source = city, source
        self.dir = kamdata.city_dir(city)
        self.prov_path = os.path.join(self.dir, 'import', 'provenance.json')
        try:
            self.prov = json.load(open(self.prov_path, encoding='utf-8'))
        except FileNotFoundError:
            self.prov = {}
        self.places = kamdata.load('P')
        mine = {i for i, v in self.prov.items() if v.get('source') == source}
        # keep what people have verified since the last run
        self.kept_verified = [p for p in self.places if p['id'] in mine and p.get('src') in ('own',)]
        self.places = [p for p in self.places if p['id'] not in mine or p in self.kept_verified]
        for i in list(mine):
            if not any(p['id'] == i for p in self.kept_verified):
                self.prov.pop(i, None)
        live = {p['id'] for p in self.places}
        for p in self.places:
            if 'sameComplex' in p:
                p['sameComplex'] = [i for i in p['sameComplex'] if i in live]
                if not p['sameComplex']: del p['sameComplex']
        self.seed = [p for p in self.places if p['id'] not in self.prov]   # hand-assigned records
        self.area_by_locality = area_by_locality or {}
        self.name_suffix = None   # e.g. 'child care': appended when the name exists in another category
        self.phone_dedupe = True   # research merges turn it off: one switchboard serves several services
        self.word_radius = 40   # schools and other one-of-a-kind names can use more (bc_schools: 400)
        # area anchors (cities/<city>/import/config.json "areaAnchors"): a few points per area;
        # a place gets the area of its nearest anchor. Explicit and stable, unlike voting among
        # whatever records happen to exist (Glenmore had one hand-assigned record and got no
        # child care at all under the voting rule).
        try:
            self.anchors = json.load(open(os.path.join(self.dir, 'import', 'config.json'), encoding='utf-8')).get('areaAnchors')
        except FileNotFoundError:
            self.anchors = None
        self.new, self.skipped, self.approx = [], [], []
        self.translations = load_translations(city)
        self.hours = load_hours(city)
        self.bounds = None
        m = re.search(r'bounds:\[\[([-\d.]+),([-\d.]+)\],\[([-\d.]+),([-\d.]+)\]\]', kamdata.data_text(city))
        if m:
            a, b, c, d = map(float, m.groups()); self.bounds = (a, b, c, d)

    def area(self, lat, lng, locality=None):
        if locality and locality.lower() in self.area_by_locality:
            return self.area_by_locality[locality.lower()]
        if self.anchors:
            return min(((g, dist_m(lat, lng, a, b)) for g, pts in self.anchors.items() if not g.startswith('_')
                        for a, b in pts), key=lambda x: x[1])[0]
        pool = self.seed or self.places
        near = sorted(pool, key=lambda p: dist_m(lat, lng, p['lat'], p['lng']))[:5]
        return max(set(p['g'] for p in near), key=lambda g: sum(1 for p in near if p['g'] == g))

    def locate(self, address, locality, lat=None, lng=None):
        """(lat, lng, approx) per the coordinate rule; (None, None, None) if nothing usable."""
        h = geocode(address, locality) if address else None
        if h and h['trusted'] and (lat is None or dist_m(lat, lng, h['lat'], h['lng']) <= 150):
            return h['lat'], h['lng'], False
        if lat is not None:
            return round(lat, 7), round(lng, 7), True
        if h and h['trusted']:
            return h['lat'], h['lng'], False
        return None, None, None

    def duplicate_of(self, name, cat, lat, lng, phone=None):
        for p in self.places + self.new:
            d = dist_m(lat, lng, p['lat'], p['lng'])
            if d < 400 and p['c'] == cat and similar(p['n'], name, words=False): return p   # one name inside the other
            # (a school and the after-school care in its building are different places: kept, linked)
            if d < self.word_radius and p['c'] == cat and similar(p['n'], name): return p   # same building, same words
            if d < 40 and phone and self.phone_dedupe and p['c'] == cat and p.get('p') == phone: return p   # same switchboard, same kind of place
        return None

    def link_same_building(self, rec):
        """Different places at (nearly) the same point know about each other, both ways."""
        for p in self.places + self.new:
            if p is rec or dist_m(rec['lat'], rec['lng'], p['lat'], p['lng']) > 25: continue
            rec.setdefault('sameComplex', [])
            if p['id'] not in rec['sameComplex']: rec['sameComplex'].append(p['id'])
            p.setdefault('sameComplex', [])
            if rec['id'] not in p['sameComplex']: p['sameComplex'].append(rec['id'])

    def add(self, rec, key, locality=None):
        """rec needs n, c, a, lat, lng (+ anything else). Returns the record or None if skipped."""
        if self.bounds:
            a, b, c, d = self.bounds
            if not (a < rec['lat'] < c and b < rec['lng'] < d):
                self.skipped.append((rec['n'], 'outside CITY.bounds')); return None
        dup = self.duplicate_of(rec['n'], rec['c'], rec['lat'], rec['lng'], rec.get('p'))
        if dup:
            self.skipped.append((rec['n'], 'already listed as ' + dup['n'])); return None
        # the same name in another category (a school and the child care licensed in its
        # name) — both are real; the one being imported says what it is
        # Deterministic whichever importer runs first: child care licensed in a school's name
        # always carries the suffix, so the school keeps its plain name.
        clash = [p for p in self.places + self.new if norm(p['n']) == norm(rec['n'])]
        for p in clash:
            if p['c'] == rec['c']:
                self.skipped.append((rec['n'], 'same name already on the map')); return None
            if p['c'] == 'daycare':
                p['n'] = '%s (child care)' % p['n']
            elif rec['c'] == 'daycare':
                rec['n'] = '%s (child care)' % rec['n']
            elif self.name_suffix:
                rec['n'] = '%s (%s)' % (rec['n'], self.name_suffix)
            else:
                self.skipped.append((rec['n'], 'same name already on the map')); return None
        rec.setdefault('g', self.area(rec['lat'], rec['lng'], locality))
        rec.setdefault('src', 'opendata'); rec.setdefault('v', MONTH)
        rec['id'] = hashlib.sha1(('%s:%s:%s' % (self.city, self.source, key)).encode()).hexdigest()[:8]
        apply_translation(rec, self.translations)    # needs the id (2026-10-03: was applied before it existed)
        apply_hours(rec, self.hours)
        if rec.get('precision') == 'low': self.approx.append(rec['n'])
        self.new.append(rec)
        if rec.get('precision') != 'low': self.link_same_building(rec)
        self.prov[rec['id']] = {'source': self.source, 'key': key, 'imported': TODAY.isoformat()}
        return rec

    def save(self):
        order = ['n', 'c', 'g', 'lat', 'lng', 'a', 'p', 'h', 'note', 'src', 'v', 't', 'alias', 'tag',
                 'precision', 'sameComplex', 'pick', 'id', 'w', 'e', 'pq']
        out = self.places + [{k: r[k] for k in order if k in r} for r in self.new]
        kamdata.save('P', out)
        os.makedirs(os.path.dirname(self.prov_path), exist_ok=True)
        json.dump(self.prov, open(self.prov_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
        print('%s/%s: +%d records (%d approximate), %d skipped as already listed or out of bounds'
              % (self.city, self.source, len(self.new), len(self.approx), len(self.skipped)))
        for n, why in self.skipped[:40]:
            print('   skip  %-48s %s' % (n[:48], why))
