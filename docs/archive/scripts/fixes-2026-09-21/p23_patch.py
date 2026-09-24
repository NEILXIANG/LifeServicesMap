#!/usr/bin/env python3
"""2026-09-24 — a source label for provincial open data, and the attribution it requires.

Records are about to arrive from the Province of British Columbia's own open
data (the Child Care Map). That is neither "the organisation's own website" nor
"third-party map data", so it gets its own label, in six languages, with the
same honesty as the others: it says where it came from and that the reader
should call ahead.

The Open Government Licence – British Columbia requires attribution, so the
licence panel now says which datasets are used and under what licence.
"""
import sys, re
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:110], n))
    return src.replace(old, new)

# ---- the label itself
LAB = {
 'zh': ("省政府开放数据", "该条目来自 BC 省政府的公开数据（每日更新），未逐条致电核对，出发前建议先打电话确认。"),
 'en': ("BC government open data", "From the Province of British Columbia’s own open data (updated daily). Not confirmed by phone one by one — call ahead before you go."),
 'fr': ("Données ouvertes du gouvernement de la C.-B.", "Provient des données ouvertes du gouvernement de la Colombie-Britannique (mises à jour quotidiennement). Non vérifié un par un par téléphone — appelez avant de vous déplacer."),
 'es': ("Datos abiertos del gobierno de BC", "Proviene de los datos abiertos del Gobierno de Columbia Británica (actualizados a diario). No se confirmó uno por uno por teléfono: llame antes de ir."),
 'ko': ("BC주 정부 공개 데이터", "BC주 정부의 공개 데이터에서 가져왔습니다(매일 갱신). 한 곳씩 전화로 확인하지는 않았으니 가기 전에 전화해 보세요."),
 'ja': ("BC州政府のオープンデータ", "BC州政府のオープンデータより（毎日更新）。1件ずつ電話で確認はしていないので、行く前に電話してください。"),
}
anchor = "UI.zh.srcStub='未确认"
for l, (label, tip) in LAB.items():
    m = re.search(r"UI\.%s\.srcOwnTip='[^']*';" % l, s)
    if not m: sys.exit('no srcOwnTip anchor for %s' % l)
    s = s.replace(m.group(0), m.group(0) + "UI.%s.srcOpenData='%s';UI.%s.srcOpenDataTip='%s';" % (l, label, l, tip), 1)

s = rep(s, """const SRC_KINDS={official:['srcOfficial','srcOfficialTip'],
                 places:['srcPlaces','srcPlacesTip'],
                 own:['srcOwn','srcOwnTip'],""",
"""const SRC_KINDS={official:['srcOfficial','srcOfficialTip'],
                 places:['srcPlaces','srcPlacesTip'],
                 // 2026-09-24: a government dataset is its own kind of source — more
                 // reliable than a third-party map, less than the organisation's own page
                 opendata:['srcOpenData','srcOpenDataTip'],
                 own:['srcOwn','srcOwnTip'],""")

s = rep(s, "  .pv-src.src-own{background:#fff3d6;color:#7a5c00;}",
           "  .pv-src.src-own{background:#fff3d6;color:#7a5c00;}\n"
           "  .pv-src.src-opendata{background:#e8f0fb;color:#1d4e8f;}")

# ---- the attribution the licence requires
ATTR = {
 'zh': '<p><b>省政府开放数据：</b>本页面的部分地点（持牌托儿机构、K–12 学校的位置）来自 BC 省政府公开数据，依 <a href="https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc" target="_blank" rel="noopener">Open Government Licence – British Columbia</a> 使用。</p>',
 'en': '<p><b>Provincial open data:</b> some places on this page — licensed child care centres and K–12 school locations — contain information licensed under the <a href="https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc" target="_blank" rel="noopener">Open Government Licence – British Columbia</a>.</p>',
 'fr': '<p><b>Données ouvertes provinciales :</b> certains lieux de cette page — garderies autorisées et emplacements des écoles de la maternelle à la 12e année — contiennent de l’information visée par l’<a href="https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc" target="_blank" rel="noopener">Open Government Licence – British Columbia</a>.</p>',
 'es': '<p><b>Datos abiertos provinciales:</b> algunos lugares de esta página — guarderías con licencia y ubicaciones de escuelas de K a 12 — contienen información bajo la <a href="https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc" target="_blank" rel="noopener">Open Government Licence – British Columbia</a>.</p>',
 'ko': '<p><b>주 정부 공개 데이터:</b> 이 페이지의 일부 장소(허가받은 어린이집, K–12 학교 위치)에는 <a href="https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc" target="_blank" rel="noopener">Open Government Licence – British Columbia</a>에 따라 제공되는 정보가 포함되어 있습니다.</p>',
 'ja': '<p><b>州政府のオープンデータ：</b>このページの一部の場所（認可保育施設、K–12学校の位置）には、<a href="https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc" target="_blank" rel="noopener">Open Government Licence – British Columbia</a> に基づく情報が含まれています。</p>',
}
for l, para in ATTR.items():
    m = re.search(r"UI\.%s\.licenceNote='(.*?)';" % l, s, re.S)
    if not m: sys.exit('no licenceNote for %s' % l)
    if 'Open Government Licence' in m.group(1): sys.exit('attribution already present for %s' % l)
    s = s.replace(m.group(0), "UI.%s.licenceNote='%s%s';" % (l, m.group(1), para), 1)

open(E, 'w', encoding='utf-8').write(s)
print('p23 applied')
