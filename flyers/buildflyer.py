#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the A4 flyer, Google-grid version and Apple version, from one content
source so the two can never drift apart."""
import mapart

URL = 'kamloops-lifemap.neilxiang.workers.dev'
qr = open('/tmp/qr.svg').read()
QR_INNER = qr[qr.index('>') + 1:qr.rindex('</svg>')]
QR = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 41 41" shape-rendering="crispEdges">' + QR_INNER + '</svg>'

MAP_W, MAP_H = 1240, 300
# The band is ~4:1, so the geographic frame is cut to the same shape — otherwise
# cover-scaling crops away the lake and the confluence, which are the two things
# that say "Kamloops" at a glance.
BAND_BOUNDS = (50.6520, 50.7160, -120.6200, -120.2050)
MAP_COLOUR = mapart.build(MAP_W, MAP_H, tone='colour', labels=True, roads=True, bounds=BAND_BOUNDS)

# The four questions this tool exists to answer — the flyer's actual promise.
PROMISE = [
    ('🧭', 'Something to sort out?', 'Start from the problem, not a category'),
    ('📍', 'Where do I go?',         'The right office, on the map, with hours'),
    ('📄', 'What do I bring?',       'Documents, fees and how to book'),
    ('✅', 'How do I finish it?',    'Step by step, to done'),
]

CARDS = [
 ('en','English','Get to know this city, and live well in it',
  ['263 checked places: schools, clinics, groceries, housing, transit',
   'Life Guide: health card, SIN, driver’s licence, school — step by step']),
 ('fr','Français','Découvrez cette ville, et vivez-y bien',
  ['263 lieux vérifiés : écoles, cliniques, épiceries, logement, transport',
   'Guide pratique : carte santé, NAS, permis, école — pas à pas']),
 ('es','Español','Conozca esta ciudad y viva bien en ella',
  ['263 lugares verificados: escuelas, clínicas, mercados, vivienda, transporte',
   'Guía práctica: tarjeta de salud, NAS, licencia, escuela — paso a paso']),
 ('zh','中文','读懂这座城市，在这里好好生活',
  ['263 个逐条核实的地点：学校、诊所、超市、租房、公交',
   '生活指南：医保卡、工卡、驾照、入学——一步一步办完']),
 ('ko','한국어','이 도시를 알고, 이곳에서 잘 살기',
  ['확인을 거친 263곳: 학교·병원·마트·주거·대중교통',
   '생활 가이드: 의료카드, SIN, 운전면허, 학교 등록 — 단계별 안내']),
 ('ja','日本語','この街を知り、ここで心地よく暮らす',
  ['確認済みの263か所: 学校、クリニック、スーパー、住まい、交通',
   '生活ガイド: 医療カード、SIN、運転免許、就学 — 順を追って']),
]
BLESSING = ('May this small tool help you settle in sooner, make connections, '
            'and enjoy the good life this city has to offer.')
FOOT = ('Independently compiled community reference · not an official publication and not affiliated with any '
        'listed organization · hours, fees and procedures change — always confirm with the office itself · '
        'the map is a stylised illustration: places and roads come from the project\'s own verified records and '
        'BC Transit GTFS (2026-08-29), rivers and hills are drawn for recognition, not for navigation · '
        'CC BY-NC 4.0 · Neil Xiang · neilxiang@hotmail.com')

def cards_html(cls_tag='card-tag'):
    out = []
    for lang, tag, head, feats in CARDS:
        lis = ''.join('<li>%s</li>' % f for f in feats)
        out.append(f'<article class="card" lang="{lang}"><div class="{cls_tag}">{tag}</div>'
                   f'<h3>{head}</h3><ul>{lis}</ul></article>')
    return '\n'.join(out)

def promise_html():
    return '\n'.join(
        f'<div class="pr"><span class="pr-ic">{ic}</span><b>{q}</b><span>{a}</span></div>'
        for ic, q, a in PROMISE)

MAP_SVG = (f'<svg viewBox="0 0 {MAP_W} {MAP_H}" preserveAspectRatio="xMidYMid slice" '
           f'class="mapart">{MAP_COLOUR}</svg>')

GOOGLE = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Jesus Loves You — Kamloops Life Guide</title>
<style>
@page{{size:A4 portrait;margin:0}} *{{box-sizing:border-box}} html,body{{margin:0;padding:0}}
body{{font-family:"Roboto","Helvetica Neue",Arial,"Noto Sans CJK SC","Noto Sans CJK KR","Noto Sans CJK JP",sans-serif;
 color:#202124;background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.page{{width:210mm;height:297mm;overflow:hidden;background:#fff;padding:11mm 12mm 8mm;display:flex;flex-direction:column}}
.mast{{text-align:center}}
.cross{{display:block;margin:0 auto 3mm}}
h1{{margin:0;font-size:31pt;line-height:1.02;font-weight:700;letter-spacing:-.018em;color:#1a73e8}}
.lead{{margin:3mm auto 0;font-size:10.4pt;line-height:1.45;color:#3c4043;max-width:150mm;text-wrap:balance}}
.lead b{{color:#202124;font-weight:600}}
.rule{{height:3px;margin:3.5mm auto 0;width:88mm;border-radius:2px;
 background:linear-gradient(90deg,#1a73e8 0 25%,#188038 25% 50%,#f9ab00 50% 75%,#d93025 75% 100%)}}
/* the promise: four questions, one per column */
.promise{{margin-top:4.5mm;display:grid;grid-template-columns:repeat(4,1fr);gap:3mm}}
.pr{{background:#f8f9fa;border:1px solid #e8eaed;border-radius:9px;padding:3mm 3mm 3.2mm;text-align:center}}
.pr-ic{{display:block;font-size:14pt;line-height:1;margin-bottom:1.6mm}}
.pr b{{display:block;font-size:8.6pt;line-height:1.25;margin-bottom:1mm}}
.pr span:last-child{{display:block;font-size:7.3pt;line-height:1.35;color:#5f6368}}
/* the map band */
.mapwrap{{margin-top:4.5mm;border:1px solid #dadce0;border-radius:10px;overflow:hidden;position:relative;
 height:46mm;box-shadow:0 1px 2px rgba(60,64,67,.12)}}
.mapart{{width:100%;height:100%;display:block}}
.maptag{{position:absolute;left:3mm;bottom:2.6mm;background:rgba(255,255,255,.92);border:1px solid #dadce0;
 border-radius:6px;padding:1mm 2.4mm;font-size:7.4pt;font-weight:700;color:#3c4043;letter-spacing:.04em}}
.lb-city{{font:700 15px "Roboto",Arial,sans-serif;fill:#5f6368;letter-spacing:.13em;text-anchor:middle}}
.lb-water{{font:italic 500 14px "Roboto",Arial,sans-serif;fill:#5b93bf;text-anchor:middle}}
.lb-poi{{font:600 13px "Roboto",Arial,sans-serif;fill:#3c4043}} .lb-dot{{fill:#188038}}
/* the six languages */
.cards{{margin-top:4.5mm;display:grid;grid-template-columns:repeat(2,1fr);gap:3.4mm 4mm}}
.card{{border:1px solid #dadce0;border-radius:9px;padding:3.2mm 3.6mm 3.4mm;background:#fff}}
.card-tag{{font-size:7.2pt;font-weight:700;letter-spacing:.10em;text-transform:uppercase;color:#1a73e8;margin-bottom:1.2mm}}
.card h3{{margin:0 0 1.6mm;font-size:10pt;line-height:1.26;font-weight:700}}
.card ul{{margin:0;padding:0;list-style:none}}
.card li{{font-size:7.9pt;line-height:1.42;color:#5f6368;padding-left:3.6mm;position:relative;margin-bottom:.8mm}}
.card li::before{{content:'';position:absolute;left:0;top:1.5mm;width:1.6mm;height:1.6mm;border-radius:50%;background:#188038}}
.card[lang=zh] h3,.card[lang=ko] h3,.card[lang=ja] h3{{font-size:9.7pt}}
/* close */
.cta{{margin-top:auto;padding-top:4mm;display:grid;grid-template-columns:30mm 1fr;gap:5mm;align-items:center;
 border-top:1px solid #dadce0}}
.qr{{width:30mm;height:30mm;padding:1.8mm;background:#fff;border:1px solid #dadce0;border-radius:8px}}
.qr svg{{width:100%;height:100%;display:block}}
.cta h4{{margin:0 0 1.2mm;font-size:12pt;font-weight:700}}
.url{{display:inline-block;font-size:9pt;font-weight:700;color:#1a73e8;margin-bottom:1.4mm;word-break:break-all}}
.bless{{margin:0;font-size:8.4pt;line-height:1.5;color:#3c4043}}
.badges{{display:flex;flex-wrap:wrap;gap:1.6mm;margin-top:2mm}}
.badge{{font-size:7pt;font-weight:600;color:#3c4043;background:#f1f3f4;border:1px solid #e3e5e8;border-radius:999px;padding:.9mm 2.4mm}}
.foot{{margin-top:3mm;font-size:6.5pt;line-height:1.5;color:#80868b}}
</style></head><body><div class="page">
 <div class="mast">
  <svg class="cross" width="30" height="40" viewBox="0 0 24 32" aria-hidden="true">
   <path d="M12 1.6 v28.8 M2.6 10.4 h18.8" fill="none" stroke="#188038" stroke-width="4.2" stroke-linecap="round"/></svg>
  <h1>Jesus Loves You</h1>
  <p class="lead">A guide to knowing Kamloops and living well in it — made and given away as a gift,
   <b>free, no sign-up, no ads, nothing collected about you.</b></p>
  <div class="rule"></div>
 </div>
 <div class="promise">{promise_html()}</div>
 <div class="mapwrap"><span class="maptag">KAMLOOPS, BC</span>{MAP_SVG}</div>
 <div class="cards">{cards_html()}</div>
 <div class="cta">
  <div class="qr">{QR}</div>
  <div>
   <h4>Scan to open it</h4>
   <span class="url">{URL}</span>
   <p class="bless">{BLESSING}</p>
   <div class="badges"><span class="badge">Free</span><span class="badge">No sign-up</span><span class="badge">No ads</span>
    <span class="badge">Works offline</span><span class="badge">EN · FR · ES · 中文 · 한국어 · 日本語</span></div>
  </div>
 </div>
 <p class="foot">{FOOT}</p>
</div></body></html>'''
open('jesus-loves-you-flyer.html', 'w', encoding='utf-8').write(GOOGLE)
print('google flyer rebuilt: %d KB' % (len(GOOGLE) // 1024))
