#!/usr/bin/env python3
"""Create the skeleton of a new city under cities/<id>/.

    python3 scripts/new-city.py kelowna --name Kelowna --centre 49.888,-119.496

What it copies from Kamloops is only what is true for all of BC: statutory
holidays, the province-wide hotlines, the map tiles, the winter-driving season,
the province labels. Everything that belongs to one city is emptied or marked
`TODO:` — validate.py refuses a city that still contains a TODO, so an
unfinished skeleton cannot be deployed by accident.

Next steps are printed at the end (and in docs/guides/DATA-SCHEMA.md, "Adding a city").
"""
import argparse, json, os, re, sys

_r = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_r))
import kamdata

LANGS = ['zh', 'en', 'fr', 'es', 'ko', 'ja']

def city_block(cid, name, lat, lng, dlat, dlng):
    """Rewrite Kamloops' CITY object for the new city."""
    src = open(kamdata.data_template('kamloops'), encoding='utf-8').read()
    m = re.search(r'const CITY=\{.*?\n\};', src, re.S)
    c = m.group(0)
    names = ','.join("%s:'%s'" % (l, name) for l in LANGS)
    rep = [
        (r"key:'kamloops'", "key:'%s'" % cid),
        (r"name:\{zh:'Kamloops'[^}]*\}", "name:{%s}" % names),
        (r"centre:\[[^\]]*\], zoom:12", "centre:[%s,%s], zoom:12" % (lat, lng)),
        (r"bounds:\[\[[^\]]*\],\[[^\]]*\]\]",
         "bounds:[[%.3f,%.3f],[%.3f,%.3f]]" % (lat - dlat, lng - dlng, lat + dlat, lng + dlng)),
        (r"navSuffix:', Kamloops, BC'", "navSuffix:', %s, BC'" % name),
        (r"transit:\{name:'BC Transit', url:'[^']*'\}", "transit:{name:'BC Transit', url:'TODO: BC Transit page for %s'}" % name),
        (r"schoolDistrict:\{name:'SD73', url:'[^']*'\}", "schoolDistrict:{name:'TODO: school district (e.g. SD23)', url:'TODO: catchment finder URL'}"),
        (r"tasksChecked:'[^']*'", "tasksChecked:'TODO: YYYY-MM-DD the task cards were checked'"),
        (r"verified:'[^']*'", "verified:'TODO: YYYY-MM-DD of the last full desk check of the places'"),
        (r"help:\{settle:'[^']*'", "help:{settle:'TODO: settlement agency phone'"),
        # 2026-10-04: these three are city facts too, and used to be copied silently (the docs audit ran this script)
        (r"examples:\{campus:'[^']*', stop:'[^']*'\}", "examples:{campus:'TODO: main campus short name (or remove campus)', stop:'TODO: main downtown bus exchange'}"),
        (r"police:'[^']*'", "police:'TODO: local police non-emergency line'"),
        (r"upcc:\[[^\]]*\],", "upcc:[],   // TODO: ids of the city's urgent and primary care centres (places.json), once imported"),
    ]
    for pat, new in rep:
        c, n = re.subn(pat, new, c, count=1)
        if n != 1:
            sys.exit('new-city.py: Kamloops CITY no longer matches %r — update this script' % pat)
    # city-only lines: emptied; the reader still gets the province-wide hotlines
    c = re.sub(r"  localLines:\[.*?\n  \],", "  localLines:[],   // TODO: local 24-hour lines (shelters, crisis lines)", c, count=1, flags=re.S)
    c = re.sub(r"  localCrisis:\{.*?\}\}\n\};", "  localCrisis:null   // TODO: local non-police crisis team, if there is one\n};", c, count=1, flags=re.S)
    # the wildfire season links to Kamloops' own alert page: keep the season, drop that link
    c = re.sub(r"\n\s*\{u:'https://www\.kamloops\.ca/[^\n]*", '', c)
    # Kamloops' explanatory comments name Kamloops places (TRU, KAFS…); field meanings live in DATA-SCHEMA.md
    c = '\n'.join(l for l in c.splitlines() if not l.lstrip().startswith('//') or 'TODO' in l)
    if 'kamloops' in c.lower():
        left = [l.strip()[:80] for l in c.splitlines() if 'kamloops' in l.lower()]
        sys.exit('new-city.py: Kamloops-specific text left in CITY: %s' % left)
    return c

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('id', help='lowercase id, e.g. kelowna (also the storage prefix and the Worker name stem)')
    ap.add_argument('--name', required=True, help='display name, e.g. Kelowna')
    ap.add_argument('--centre', required=True, help='map centre "lat,lng"')
    ap.add_argument('--span', default='0.2,0.35', help='bounds half-size "dlat,dlng" (default 0.2,0.35)')
    a = ap.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9-]*|_[a-z][a-z0-9_]*', a.id):   # a leading _ marks a test city
        sys.exit('id must be lowercase letters, digits or -')
    d = os.path.join(kamdata.ROOT, 'cities', a.id)
    if os.path.exists(d):
        sys.exit('cities/%s already exists — not overwriting' % a.id)
    lat, lng = (float(x) for x in a.centre.split(','))
    dlat, dlng = (float(x) for x in a.span.split(','))
    worker = '%s-lifemap' % a.id

    os.makedirs(os.path.join(d, 'guide'))
    meta = {
        '_comment': 'Build-time settings for %s. See docs/guides/DATA-SCHEMA.md.' % a.name,
        'id': a.id,
        'country': 'ca', 'province': 'bc',   # this script copies BC-wide content; another province needs its own pack first
        'title': '%s Life Guide' % a.name,
        'description': 'What to do, where to go, what to bring — step by step — with a map of verified places across %s. Free, no sign-up, six languages.' % a.name,
        'siteUrl': 'https://%s.neilxiang.workers.dev/' % worker,
        'storagePrefix': a.id,
        'searchStopwords': [a.id, 'bc'],
        'leakMarkers': [],            # this city's facts no derived fingerprint catches (school-district code, fare, campus abbreviation)
        'status': 'draft',            # remove when the city is reviewed and ready to launch
        'validate': {'minPlaces': 0},
        'review': {'reference': 'kamloops'},   # add "targetPlaces" once PROFILE.md 由此决定 sets it
        'deploy': {
            'worker': worker, 'wranglerEnv': a.id, 'assetsDir': 'deploy/%s' % a.id, 'basePath': '/',
            'swCache': '%s-v1.0.0' % worker, 'pwaLabel': '%s Life Guide' % a.name,
            'pwaDescription': 'What to do, where to go, what to bring — step by step — with a map of verified places across %s. Free, no sign-up.' % a.name,
        },
    }
    json.dump(meta, open(os.path.join(d, 'city.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    tpl = open(kamdata.data_template('kamloops'), encoding='utf-8').read()
    body = tpl[tpl.index('const RI='):]
    body = re.sub(r'const FAV_MIGRATE=\{.*?\};', 'const FAV_MIGRATE={};', body, flags=re.S)
    body = re.sub(r'const LANDMARK_GLOSS=\{.*?\n\};', 'const LANDMARK_GLOSS={};', body, flags=re.S)
    # 2026-10-04: Kamloops' own texts and bus provenance are city facts — drop them so the engine's generic
    # defaults apply until this city writes its own (fares and bus coverage are required once it has routes,
    # licenceData once it uses open data; validate.py says so at that point)
    body = re.sub(r'const BUS_SOURCE=\{.*?\};\n', '', body, flags=re.S)
    body = re.sub(r"^UI\.(zh|en|fr|es|ko|ja)\.(busCoverage|busFareText|licenceData|noteCoverage|noteThirdParty|legalLocal|hcUpcc)=.*\n",
                  '', body, flags=re.M)
    # drop Kamloops' commentary between the blocks; keep the statements
    body = '\n'.join(l for l in body.splitlines() if not l.startswith('//')) + '\n'
    head = ('// %s city data. Created by scripts/new-city.py from the BC-wide parts of Kamloops.\n'
            '// Field reference: docs/guides/DATA-SCHEMA.md. Every TODO must go before validate.py passes.\n' % a.name)
    out = head + city_block(a.id, a.name, lat, lng, dlat, dlng) + '\n\n' + body
    # refuse to hand over a skeleton that still carries a known Kamloops fact (police, legal aid, UPCC, fares,
    # data source, campus, district, the UPCC's place id)
    # 2026-10-04: plus everything in Kamloops' derived fingerprint (kamdata.fingerprint: areas, landmarks, UPCCs,
    # local phones, city.json leakMarkers), so a fact added to Kamloops later is caught without editing this list
    marks = set(kamdata.fingerprint('kamloops')) | {'828-3000', '314-1900', '425-9121', 'KAFS', 'Google Places', '2.25',
                                                   'b29c9af7', 'Secw'}
    leaks = sorted(t for t in marks if re.search(r'(?<![\w$])%s(?!\w)' % re.escape(t), out[len(head):]))   # the header names its source
    if leaks:
        import shutil; shutil.rmtree(d)
        sys.exit('new-city.py: Kamloops facts would be copied (%s) — update this script' % ', '.join(leaks))
    open(os.path.join(d, 'data.js'), 'w', encoding='utf-8').write(out)

    def dump(name, value):
        with open(os.path.join(d, name), 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=1); f.write('\n')
    dump('places.json', [])
    dump('tasks.json', [])
    dump('bus-routes.json', {})
    dump('quarantine.json', [])
    dump('landmarks.json', [])
    dump('regions.json', {'c': {l: 'TODO: area name' for l in LANGS}})
    for l in LANGS:
        open(os.path.join(d, 'guide', l + '.html'), 'w', encoding='utf-8').write(
            '\n<h3>{CITY}</h3>\n<p>TODO: the "About this city" section of the guide (%s).</p>\n' % l)

    # 2026-10-04: the profile skeleton (methodology §4). Copying Kelowna's PROFILE.md as a template left its numbers in.
    open(os.path.join(d, 'PROFILE.md'), 'w', encoding='utf-8').write(PROFILE % {'name': a.name, 'id': a.id, 'today': kamdata.today().isoformat()})

    print('created cities/%s/  (Worker %s, storage prefix %s)' % (a.id, worker, a.id))
    print('''
next:
  0. city profile first: cities/%(id)s/PROFILE.md (prompt: docs/knowledge/prompts/城市画像.md)
  1. fill every TODO in cities/%(id)s/data.js, regions.json and guide/*.html
  2. add places to places.json (schema: schemas/place.schema.json)
  3. python3 build.py --city %(id)s && python3 scripts/validate.py --city %(id)s
  4. open build/%(id)s.html in a browser
  5. before the first deploy: add [env.%(id)s] to wrangler.toml (template at its end)''' % {'id': a.id})

PROFILE = """# %(name)s 城市画像（%(today)s 开始）

> 方法论第一步（`docs/guides/新城市扩展方法论与标准.md` 第四节，每张表该有哪些行见那里）；资料收集用 `docs/knowledge/prompts/城市画像.md`。
> 每个数字写出处（官方优先：统计局、省统计局、IRCC、CMHC、市政府）；没有官方出处的标"非官方"，写进对外内容前再查。
> 完整出处网址放 `cities/%(id)s/import/research/`。对照对象：Kamloops（必要时加 Kelowna）。

## 一、人口与人群

| 项 | %(name)s | Kamloops | 说明 |
|---|---|---|---|
| TODO | | | |

## 二、经济与生活成本

| 项 | %(name)s | Kamloops | 说明 |
|---|---|---|---|
| TODO | | | |

## 三、地方与特色

TODO：区域划分（每个区域一句地理提示）、原住民称谓（向当地确认，不套用别城）、地标、季节与灾害（雪、山火、洪水……）。

## 四、门户、交通、教育、医疗、安置

TODO：机场与长途交通、公交运营方、学区与高校、医院与 UPCC、安置机构。

## 官方来源清单

TODO：这座城市要用的市级、区域级（健康局、学区、区域警报）来源；省级和联邦来源见 `docs/knowledge/数据来源目录.md`，不在这里重复。

## 对人群和需求的含义

TODO：按 `docs/guides/新移民画像与需求.md` 逐节写这座城市的情况（规模信号、本地缺口、特别之处）。

## 五、由此决定

TODO：地点目标（写进 city.json `review.targetPlaces`）、优先类别、哪些商业类不收（`schemas/category-tiers.json`）、语言优先级、办事卡要本地改写哪些（操作手册第 6 步）。

已导入的数据不在这里手写数字：运行 `python3 scripts/review_checklist.py --city %(id)s`。
"""

if __name__ == '__main__':
    main()
