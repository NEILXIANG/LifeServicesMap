#!/usr/bin/env python3
"""Parks, beaches and off-leash areas from a city's own ArcGIS open-data layer.

    python3 scripts/importers/arcgis_parks.py --city kelowna

Many Canadian and US municipalities publish parks as an ArcGIS MapServer/FeatureServer
layer; only the field names and the selection rules differ, so those live in
cities/<city>/import/config.json under "arcgis_parks":

  {"url": ".../MapServer/14", "licence": "Open Government Licence – City of Kelowna",
   "fields": {"name": "LOCATIONDESC", "address": "NOTE9", "class": "STATUS_CLASS",
              "dogs": "DOG_STATUS_DESC", "hectares": "NOTE1"},
   "classes": {"DEVELOPED CITY WIDE": 0, "DEVELOPED REGIONAL": 0, "DEVELOPED NATURAL AREA": 5, ...},
   "beach": "beach park$", "offLeash": ["Off leash"], "offLeashArea": ["On leash and off leash area"]}

"classes" maps an allowed class to a minimum size in hectares (0 = all of them). Tier 1
(municipal open data) → src:'opendata'. Point = the BC geocoder's point for the park's
address (where people arrive) when trusted, else the centre of the park polygon.
No hours (open-air: the page says "hours posted on site") and no web link unless verified.
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CityImport, tidy
import bc_geocode

L6 = ['zh', 'en', 'fr', 'es', 'ko', 'ja']
KIND = {
 'park':     {'zh': '公园', 'en': 'Park', 'fr': 'Parc', 'es': 'Parque', 'ko': '공원', 'ja': '公園'},
 'regional': {'zh': '区域公园', 'en': 'Regional park', 'fr': 'Parc régional', 'es': 'Parque regional', 'ko': '광역 공원', 'ja': '広域公園'},
 'provincial': {'zh': '省立公园', 'en': 'Provincial park', 'fr': 'Parc provincial', 'es': 'Parque provincial', 'ko': '주립공원', 'ja': '州立公園'},
 'natural':  {'zh': '自然保护区（步道为主）', 'en': 'Natural area (mostly trails)', 'fr': 'Aire naturelle (surtout des sentiers)', 'es': 'Área natural (sobre todo senderos)', 'ko': '자연 보호 구역(주로 산책로)', 'ja': '自然エリア（主に遊歩道）'},
 'beach':    {'zh': '湖滩公园（Okanagan 湖）', 'en': 'Lake beach park (Okanagan Lake)', 'fr': 'Parc-plage (lac Okanagan)', 'es': 'Parque de playa (lago Okanagan)', 'ko': '호숫가 해변 공원(오카나간 호수)', 'ja': '湖のビーチ公園（オカナガン湖）'},
 'dog':      {'zh': '狗狗可不牵绳的遛狗区', 'en': 'Off-leash dog area', 'fr': 'Aire canine sans laisse', 'es': 'Zona para perros sin correa', 'ko': '목줄 없이 개를 풀어놓을 수 있는 구역', 'ja': 'リードなしで犬を遊ばせられるエリア'},
}
DOGS = {
 'No dogs':  {'zh': '禁止带狗', 'en': 'no dogs', 'fr': 'chiens interdits', 'es': 'no se permiten perros', 'ko': '개 출입 금지', 'ja': '犬の立ち入り禁止'},
 'On leash': {'zh': '狗须牵绳', 'en': 'dogs on leash', 'fr': 'chiens en laisse', 'es': 'perros con correa', 'ko': '개는 목줄 필수', 'ja': '犬はリード着用'},
 'area':     {'zh': '设有不牵绳的遛狗区', 'en': 'has an off-leash dog area', 'fr': 'aire canine sans laisse sur place', 'es': 'tiene zona para perros sin correa', 'ko': '목줄 없는 반려견 구역 있음', 'ja': 'リードなしのドッグエリアあり'},
 'Off leash': {'zh': '狗可不牵绳', 'en': 'dogs off leash allowed', 'fr': 'chiens sans laisse permis', 'es': 'perros sin correa permitidos', 'ko': '목줄 없이 가능', 'ja': 'リードなし可'},
}
SRC = {'zh': '（市政府开放数据）', 'en': ' (City open data)', 'fr': ' (données ouvertes de la Ville)', 'es': ' (datos abiertos de la Ciudad)', 'ko': '(시 공개 데이터)', 'ja': '（市のオープンデータ）'}
BEACH_TIP = {'zh': '夏天游泳的人多；没有救生员时自己注意安全，带孩子要寸步不离。',
             'en': 'Busy for swimming in summer; where there is no lifeguard, swim with care and keep children within reach.',
             'fr': 'Très fréquenté l’été pour la baignade ; sans surveillant, prudence, et gardez les enfants à portée de main.',
             'es': 'Muy concurrido para nadar en verano; si no hay socorrista, nade con cuidado y mantenga a los niños a su alcance.',
             'ko': '여름에 수영하는 사람이 많습니다. 안전요원이 없을 때는 조심하고, 아이는 손 닿는 곳에 두세요.',
             'ja': '夏は泳ぐ人で混みます。監視員がいないときは注意し、子どもからは目を離さないでください。'}

def centroid(geom):
    ring = max(geom.get('rings', [[]]), key=len)
    if not ring: return None, None
    xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
    return sum(ys) / len(ys), sum(xs) / len(xs)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--city', required=True)
    a = ap.parse_args()
    imp = CityImport(a.city, 'arcgis-parks')
    cfg = json.load(open(os.path.join(imp.dir, 'import', 'config.json'), encoding='utf-8'))['arcgis_parks']
    F = cfg['fields']
    q = urllib.parse.urlencode({'where': '1=1', 'outFields': ','.join(F.values()), 'returnGeometry': 'true',
                                'outSR': 4326, 'f': 'json'})
    with urllib.request.urlopen(cfg['url'] + '/query?' + q, timeout=120, context=bc_geocode.SSL_CTX) as r:
        feats = json.load(r)['features']
    locality = cfg.get('locality', imp.city.title())
    for f in feats:
        at = f['attributes']
        cls = (at.get(F['class']) or '').strip()
        ha = float(at.get(F['hectares']) or 0)
        if cls not in cfg['classes'] or ha < cfg['classes'][cls]: continue
        name = (at.get(F['name']) or '').strip()
        dogs = (at.get(F['dogs']) or '').strip()
        if not name: continue
        if cfg.get('excludeName') and re.search(cfg['excludeName'], name, re.I): continue   # cemeteries, stormwater ponds
        if re.search(cfg['beach'], name, re.I): cat, kind = 'beach', 'beach'
        elif dogs in cfg['offLeash']: cat, kind = 'dogpark', 'dog'
        elif 'NATURAL' in cls: cat, kind = 'trail' if ha >= 20 else 'park', 'natural'
        elif 'REGIONAL' in cls: cat, kind = 'park', 'regional'
        elif 'PROVINCIAL' in cls: cat, kind = 'park', 'provincial'
        else: cat, kind = 'park', 'park'
        addr = (at.get(F['address']) or '').strip()
        clat, clng = centroid(f.get('geometry') or {})
        lat = lng = None
        if re.match(r'^\d+\s', addr):
            lat, lng, approx = imp.locate(addr, locality)
            if approx: lat = lng = None
        if lat is None:
            if clat is None: imp.skipped.append((name, 'no geometry')); continue
            lat, lng = round(clat, 6), round(clng, 6)
        if not re.match(r'^\d+\s', addr):
            addr = addr or name
        dog_key = 'area' if dogs in cfg['offLeashArea'] else dogs if dogs in DOGS else None
        note = {}
        for l in L6:
            sep = '，' if l in ('zh', 'ja') else ', '
            size = {'zh': '约 %.0f 公顷', 'en': 'about %.0f ha', 'fr': 'environ %.0f ha', 'es': 'unas %.0f ha',
                    'ko': '약 %.0f헥타르', 'ja': '約%.0fヘクタール'}[l] % ha if ha >= 1 else None
            bits = [KIND[kind][l]] + ([size] if size else [])
            if dog_key and kind != 'dog': bits.append(DOGS[dog_key][l])
            txt = sep.join(bits) + SRC[l] + ('。' if l in ('zh', 'ja') else '.')
            if kind == 'beach': txt += (' ' if l not in ('zh', 'ja') else '') + BEACH_TIP[l]
            note[l] = txt
        t = {'beach': ['family', 'scenic', 'free'], 'dog': ['free'], 'natural': ['scenic', 'free'],
             'regional': ['family', 'scenic', 'free'], 'provincial': ['scenic', 'free']}.get(kind, ['family', 'free'])
        imp.add({'n': name, 'c': cat, 'lat': lat, 'lng': lng, 'a': addr, 'note': note, 't': t}, name, locality)
    imp.save()

if __name__ == '__main__':
    main()
