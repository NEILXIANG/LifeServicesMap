#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the flyers and the QR card sheet from one content source.

Outputs (all from the same content, so they cannot drift):
  jesus-loves-you-flyer-letter.html / -a4.html       faith edition
  kamloops-life-guide-flyer-letter.html / -a4.html   secular edition
  kamloops-life-guide-cards-letter.html              ten wallet cards on one sheet

2026-09-10, after the flyer critique:
  · Letter first. Every printer this flyer will actually meet — a library, a
    clinic, a settlement agency — is loaded with 8.5×11. A4 stays as the
    secondary edition for anyone printing abroad.
  · Every edition carries a date and its QR code carries ?src=…, so a flyer on
    a noticeboard can be told apart from a stale one, and the app can say
    whether any of them bring people in.
  · The six language cards used to say the same sentence six times. Each now
    carries the three questions a reader asks in their first week, with the
    answer and the address — the same six-tenths of the page, from "about the
    product" to "useful standing at the board".
  · Type is larger. A noticeboard is read standing, at arm's length.
  · The four promise cards are numbered, not emoji: institutions copy in
    black and white, and emoji copy as grey blocks.
"""
import io, re, json, sys
import mapart
import qrcode

URL_HOST = 'kamloops-lifemap.neilxiang.workers.dev'
EDITION = '2026-09'          # printed on every page; bump when content changes

def qr_svg(src_tag):
    """A QR for this edition/source, as an inline SVG of unit squares."""
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
    q.add_data('https://%s/?src=%s' % (URL_HOST, src_tag))
    q.make()
    n = q.modules_count
    rects = []
    for y, row in enumerate(q.modules):
        x = 0
        while x < n:
            if row[x]:
                x0 = x
                while x < n and row[x]: x += 1
                rects.append('<rect x="%d" y="%d" width="%d" height="1"/>' % (x0, y, x - x0))
            else:
                x += 1
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" shape-rendering="crispEdges">'
            '<rect width="%d" height="%d" fill="#fff"/><g fill="#202124">%s</g></svg>' % (n, n, n, n, ''.join(rects)))

# ---- facts from the data, never typed twice ---------------------------------
_d = io.open('src/data-kamloops.js', encoding='utf-8').read()
P = json.loads(re.search(r'const P=(\[.*?\]);', _d, re.S).group(1))
N_PLACES = len(P)
def place(name):
    return next(x for x in P if re.sub(r'^[⭐\s]+', '', x['n']) == name)
SERVICE_BC = place('Service BC Centre')
SERVICE_CA = place('Service Canada')
KIS = place('Kamloops Immigrant Services')

MAP_W, MAP_H = 1240, 300
BAND_BOUNDS = (50.6520, 50.7160, -120.6200, -120.2050)
# The band used to be scenery (parks, TRU). Now it carries the three offices
# the cards below point at, numbered to match: ① Service BC ② Service Canada
# ③ Immigrant Services. ① and ② are a block apart downtown, so ② sits offset.
PINS = [(1, SERVICE_BC['lat'], SERVICE_BC['lng'], -14, 0),
        (2, SERVICE_CA['lat'], SERVICE_CA['lng'], 14, 0),
        (3, KIS['lat'], KIS['lng'], 0, 0)]
MAP_COLOUR = mapart.build(MAP_W, MAP_H, tone='colour', labels=True, roads=True, bounds=BAND_BOUNDS, pins=PINS)

# The four questions this tool exists to answer — numbered, because the sequence
# is real (you cannot bring documents before you know where to go).
PROMISE = [
    ('Something to sort out?', 'Start from the problem, not a category'),
    ('Where do I go?',         'The right office, on the map, with hours'),
    ('What do I bring?',       'Documents, fees and how to book'),
    ('How do I finish it?',    'Step by step, to done'),
]

# Each language card: the three things a reader asks in week one, answered.
# Same three for every language — they are the universal first week — but each
# in the reader's own words, with the address they can walk to.
def qa(lang):
    short = lambda a: re.sub(r'\s+(Rm|Unit|Suite|F)\s*\d+\w*$', '', a)
    sb, sc, ki = short(SERVICE_BC['a']), short(SERVICE_CA['a']), short(KIS['a'])
    return {
     'en': [('Health card (MSP)?',        'Service BC · ' + sb),
            ('Work number (SIN)?',        'Service Canada · ' + sc),
            ('Don’t know where to start?','Immigrant Services · ' + ki + ' · free, interpreters')],
     'fr': [('Carte santé (MSP) ?',       'Service BC · ' + sb),
            ('NAS pour travailler ?',     'Service Canada · ' + sc),
            ('Par où commencer ?',        'Immigrant Services · ' + ki + ' · gratuit, interprètes')],
     'es': [('¿Tarjeta de salud (MSP)?',  'Service BC · ' + sb),
            ('¿Número para trabajar (SIN)?','Service Canada · ' + sc),
            ('¿No sabe por dónde empezar?','Immigrant Services · ' + ki + ' · gratis, intérpretes')],
     'zh': [('办医保（MSP）去哪？',         'Service BC · ' + sb),
            ('办工卡号（SIN）去哪？',        'Service Canada · ' + sc),
            ('不知道从哪开始？',            'Immigrant Services · ' + ki + ' · 免费、有翻译')],
     'ko': [('의료카드(MSP)는 어디서?',     'Service BC · ' + sb),
            ('일하려면 SIN은 어디서?',      'Service Canada · ' + sc),
            ('어디서 시작할지 모르겠다면?', 'Immigrant Services · ' + ki + ' · 무료, 통역')],
     'ja': [('医療カード（MSP）はどこで？', 'Service BC · ' + sb),
            ('働くためのSINはどこで？',     'Service Canada · ' + sc),
            ('何から始めればいい？',        'Immigrant Services · ' + ki + ' · 無料、通訳あり')],
    }[lang]

CARDS = [('en','English','Your first week, answered'),
         ('fr','Français','Votre première semaine, répondue'),
         ('es','Español','Su primera semana, respondida'),
         ('zh','中文','第一周最常问的三件事'),
         ('ko','한국어','첫 주에 가장 많이 묻는 세 가지'),
         ('ja','日本語','最初の一週間でよく聞かれる三つのこと')]

def cards_html():
    out = []
    for lang, tag, head in CARDS:
        rows = ''.join('<li><b>%s</b><span><i class="n">%d</i>%s</span></li>' % (q, i + 1, a) for i, (q, a) in enumerate(qa(lang)))
        out.append('<article class="card" lang="%s"><div class="card-tag">%s</div><h3>%s</h3><ul>%s</ul></article>' % (lang, tag, head, rows))
    return '\n'.join(out)

def promise_html():
    return '\n'.join('<div class="pr"><span class="pr-n">%d</span><b>%s</b><span>%s</span></div>' % (i + 1, q, a)
                     for i, (q, a) in enumerate(PROMISE))

MAP_SVG = '<svg viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid slice" class="mapart">%s</svg>' % (MAP_W, MAP_H, MAP_COLOUR)

_logo = io.open('logo.svg', encoding='utf-8').read()
LOGO_SVG = _logo[_logo.index('<svg'):]
def logo(size):
    return LOGO_SVG.replace('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"',
                            '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 192 192"' % (size, size))

# Lines every edition shares
LEAD_BOLD = '<b>free, no sign-up, no ads, nothing collected about you.</b>'
FOR_WHOM = 'For people who have just arrived — and for anyone who has lived here for years and wants to help someone who just did.'
NO_PHONE = 'No smartphone? Any library will open it for you at the desk. Or dial 2-1-1 and ask, in your language.'
FOOT = ('Please print and post freely — black and white is fine, Letter paper · A personal reference, not an official publication · every entry carries a verification date and a source · '
        'hours and fees change, phone before you go · CC BY-NC 4.0 · Neil Xiang · neilxiang@hotmail.com · edition ' + EDITION)

# ---- editions ------------------------------------------------------------------
FAITH = dict(
    file='jesus-loves-you-flyer', src='flyer-f',
    mark='<svg class="mark" width="10" height="13" viewBox="0 0 24 32" aria-hidden="true"><path d="M12 1.6 v28.8 M2.6 10.4 h18.8" fill="none" stroke="#1a73e8" stroke-width="4.6" stroke-linecap="round"/></svg>',
    eyebrow='Kamloops · Community welcome',
    h1='Jesus <em>Loves</em> You',
    sub='Kamloops Life Guide — six languages, free',
    # the sentence that joins the signature to the product: not preaching, an
    # explanation of why this is free
    lead='This guide is a gift, because we believe every person deserves to be treated well. '
         'It is here to help you know Kamloops and live well in it — ' + LEAD_BOLD,
    closing='May this small tool help you settle in sooner, make connections, and enjoy the good life this city has to offer.',
    title='Jesus Loves You — Kamloops Life Guide')
SECULAR = dict(
    file='kamloops-life-guide-flyer', src='flyer-s',
    mark='<span class="mark">' + logo(13) + '</span>',
    eyebrow='Kamloops · For everyone who lives here',
    h1='Kamloops <em>Life</em> Guide',
    sub='Welcome to Kamloops — and to the people who will help you settle in',
    lead='A guide to knowing this city and living well in it — made and given away as a gift, ' + LEAD_BOLD,
    closing='Made so that you can settle in sooner, find your people, and enjoy the good life this city has to offer.',
    title='Kamloops Life Guide — flyer')

PAPER = {'letter': ('Letter', '215.9mm', '279.4mm', '26mm'), 'a4': ('A4', '210mm', '297mm', '36mm')}

def page_css(paper):
    name, w, h, band = PAPER[paper]
    return f'''
@page{{size:{name} portrait;margin:0}} *{{box-sizing:border-box}} html,body{{margin:0;padding:0}}
body{{font-family:"Roboto","Helvetica Neue",Arial,"Noto Sans CJK SC","Noto Sans CJK KR","Noto Sans CJK JP",sans-serif;
 color:#202124;background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.page{{width:{w};height:{h};overflow:hidden;background:#fff;padding:8mm 11mm 6mm;display:flex;flex-direction:column}}
/* 2026-09-10: borrowed from the earlier "Apple-style" sheet — the QR sits
   top-right beside the title (the first thing a passer-by can scan), the four
   pills say "why trust it" in one row, the palette is blue + black + grey only
   so a black-and-white photocopy loses nothing, and the address is repeated in
   a solid bar at the foot for anyone who has to copy it by hand. */
.mast{{display:grid;grid-template-columns:1fr 40mm;gap:6mm;align-items:start}}
.eyebrow{{display:inline-flex;align-items:center;gap:2mm;background:#e8f0fe;color:#1a73e8;border-radius:999px;
 padding:1.2mm 3.4mm 1.2mm 2mm;font-size:7.6pt;font-weight:700;letter-spacing:.14em;text-transform:uppercase;margin-bottom:2.4mm}}
.eyebrow .mark{{display:inline-block;line-height:0}}
h1{{margin:0;font-size:31pt;line-height:1.0;font-weight:700;letter-spacing:-.022em;color:#202124}}
h1 em{{font-style:normal;color:#1a73e8}}
.h1sub{{margin:1.4mm 0 0;font-size:11pt;color:#3c4043;font-weight:500}}
.lead{{margin:2mm 0 0;font-size:10pt;line-height:1.34;color:#3c4043;max-width:150mm;text-wrap:balance}}
.lead b{{color:#202124;font-weight:600}}
.who{{margin:1.2mm 0 0;font-size:8.8pt;line-height:1.35;color:#5f6368;max-width:150mm;text-wrap:balance}}
.qrbox{{border:1px solid #dadce0;border-radius:10px;padding:2.6mm 2.6mm 2.2mm;text-align:center;background:#fff;
 box-shadow:0 1px 3px rgba(60,64,67,.14)}}
.qr{{width:34mm;height:34mm;margin:0 auto}}
.qr svg{{width:100%;height:100%;display:block}}
.qrbox h4{{margin:1.6mm 0 .6mm;font-size:8.6pt;font-weight:700;letter-spacing:.12em;color:#1a73e8;text-transform:uppercase}}
.qrbox .url{{display:block;font-size:6.9pt;line-height:1.3;color:#5f6368;word-break:break-all}}
.badges{{display:flex;justify-content:center;flex-wrap:wrap;gap:2.2mm;margin-top:3mm}}
.badge{{font-size:8pt;font-weight:600;color:#3c4043;background:#f1f3f4;border:1px solid #e3e5e8;border-radius:999px;padding:1.3mm 4mm}}
.promise{{margin-top:3.2mm;display:grid;grid-template-columns:repeat(4,1fr);gap:3mm}}
.pr{{background:#f8f9fa;border:1px solid #e8eaed;border-radius:9px;padding:2.2mm 2.6mm 2.4mm;text-align:center}}
.pr-n{{display:inline-block;width:6mm;height:6mm;line-height:6mm;border-radius:50%;background:#1a73e8;color:#fff;font-size:10pt;font-weight:700;margin-bottom:1.4mm}}
.pr b{{display:block;font-size:9.6pt;line-height:1.25;margin-bottom:.8mm}}
.pr span:last-child{{display:block;font-size:8.4pt;line-height:1.35;color:#5f6368}}
.mapwrap{{margin-top:3.2mm;border:1px solid #dadce0;border-radius:10px;overflow:hidden;position:relative;
 flex:0 0 {band};box-shadow:0 1px 2px rgba(60,64,67,.12)}}
.mapart{{width:100%;height:100%;display:block}}
.maptag{{position:absolute;left:3mm;bottom:2.6mm;background:rgba(255,255,255,.92);border:1px solid #dadce0;
 border-radius:6px;padding:1mm 2.4mm;font-size:7.6pt;font-weight:700;color:#3c4043;letter-spacing:.04em}}
.lb-city{{font:700 15px "Roboto",Arial,sans-serif;fill:#5f6368;letter-spacing:.13em;text-anchor:middle}}
.lb-water{{font:italic 500 14px "Roboto",Arial,sans-serif;fill:#5b93bf;text-anchor:middle}}
.lb-poi{{font:600 13px "Roboto",Arial,sans-serif;fill:#3c4043}} .lb-dot{{fill:#5f6368}}
.cards{{margin-top:3.2mm;display:grid;grid-template-columns:repeat(2,1fr);gap:2.4mm 4mm}}
.card{{border:1px solid #dadce0;border-radius:9px;padding:2.2mm 3.2mm 2.4mm;background:#fff}}
.card-tag{{font-size:7.4pt;font-weight:700;letter-spacing:.10em;text-transform:uppercase;color:#1a73e8;margin-bottom:.8mm}}
.card h3{{margin:0 0 1mm;font-size:9.4pt;line-height:1.25;font-weight:700}}
.card ul{{margin:0;padding:0;list-style:none}}
.card li{{font-size:8.3pt;line-height:1.28;margin-bottom:.5mm;display:grid;grid-template-columns:auto 1fr;gap:0 2mm}}
.card li b{{color:#202124;white-space:nowrap}} .card li span{{color:#5f6368}}
.card li i.n{{display:inline-block;width:3.4mm;height:3.4mm;line-height:3.4mm;border-radius:50%;background:#1a73e8;color:#fff;font:700 6.6pt/3.4mm Roboto,Arial,sans-serif;text-align:center;margin-right:1.2mm;vertical-align:-.3mm}}
.card[lang=zh] h3,.card[lang=ko] h3,.card[lang=ja] h3{{font-size:9.4pt}}
.tail{{margin-top:auto;padding-top:2.6mm;border-top:1px solid #dadce0}}
.closing{{margin:0;font-size:8.6pt;line-height:1.4;color:#3c4043;text-align:center;text-wrap:balance}}
.nophone{{margin:1mm 0 0;font-size:8.4pt;line-height:1.4;color:#5f6368;text-align:center}}
.urlbar{{margin:2.6mm auto 0;width:150mm;background:#1a73e8;color:#fff;border-radius:999px;padding:3mm 6mm;
 text-align:center;font-size:12.5pt;font-weight:700;letter-spacing:.01em}}
.foot{{margin-top:2mm;font-size:6.8pt;line-height:1.45;color:#80868b;text-align:center}}
'''

def flyer_html(ed, paper):
    sub = ('<p class="h1sub">%s</p>' % ed['sub']) if ed.get('sub') else ''
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>{ed['title']}</title>
<style>{page_css(paper)}</style></head><body><div class="page">
 <div class="mast">
  <div>
   <div class="eyebrow">{ed['mark']}<span>{ed['eyebrow']}</span></div>
   <h1>{ed['h1']}</h1>{sub}
   <p class="lead">{ed['lead']}</p>
   <p class="who">{FOR_WHOM}</p>
  </div>
  <div class="qrbox">
   <div class="qr">{qr_svg(ed['src'] + '-' + EDITION.replace('-', '')[2:])}</div>
   <h4>Scan to open</h4>
   <span class="url">{URL_HOST}</span>
  </div>
 </div>
 <div class="badges"><span class="badge">Free · No ads</span><span class="badge">No sign-up</span>
  <span class="badge">6 languages</span><span class="badge">{N_PLACES} verified places</span><span class="badge">Works offline</span></div>
 <div class="promise">{promise_html()}</div>
 <div class="mapwrap"><span class="maptag">KAMLOOPS, BC</span>{MAP_SVG}</div>
 <div class="cards">{cards_html()}</div>
 <div class="tail">
  <p class="closing">{ed['closing']}</p>
  <p class="nophone">{NO_PHONE}</p>
  <div class="urlbar">{URL_HOST}</div>
 </div>
 <p class="foot">{FOOT}</p>
</div></body></html>'''

# ---- the wallet card sheet: ten on a Letter page ------------------------------
def cards_sheet_html():
    qr = qr_svg('card-' + EDITION.replace('-', '')[2:])
    card = f'''<div class="wc">
  <div class="wc-l">{logo(28)}<div><b>Kamloops Life Guide</b><span>What to do · where to go · what to bring</span></div></div>
  <div class="wc-q">{qr}</div>
  <div class="wc-u">{URL_HOST}</div>
  <div class="wc-b">Free · No sign-up · EN FR ES 中文 한국어 日本語</div>
</div>'''
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Kamloops Life Guide — QR cards</title>
<style>
@page{{size:Letter portrait;margin:0}} *{{box-sizing:border-box}} html,body{{margin:0;padding:0}}
body{{font-family:"Roboto","Helvetica Neue",Arial,"Noto Sans CJK SC","Noto Sans CJK KR","Noto Sans CJK JP",sans-serif;color:#202124;background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.sheet{{width:215.9mm;height:279.4mm;padding:12mm 15mm;display:grid;grid-template-columns:repeat(2,88.9mm);grid-auto-rows:50.8mm;gap:0 8mm;justify-content:center;align-content:start;position:relative}}
.wc{{width:88.9mm;height:50.8mm;border:.3mm dashed #c4c7c5;border-radius:3mm;padding:4mm 4.5mm;display:grid;grid-template-columns:1fr 30mm;grid-template-rows:auto 1fr auto;gap:1mm 3mm}}
.wc-l{{display:flex;align-items:center;gap:2.2mm;grid-column:1}} .wc-l svg{{flex:0 0 auto}}
.wc-l b{{display:block;font-size:10.5pt;line-height:1.1}} .wc-l span{{display:block;font-size:7.2pt;color:#5f6368;margin-top:.6mm}}
.wc-q{{grid-column:2;grid-row:1/4;align-self:center;width:30mm;height:30mm;padding:1mm;background:#fff}}
.wc-q svg{{width:100%;height:100%;display:block}}
.wc-u{{grid-column:1;align-self:end;font-size:8.2pt;font-weight:700;color:#1a73e8;word-break:break-all}}
.wc-b{{grid-column:1;font-size:6.8pt;color:#5f6368}}
.note{{position:absolute;left:15mm;bottom:6mm;font-size:7pt;color:#80868b}}
</style></head><body><div class="sheet">{card * 10}
<div class="note">Cut on the dashed lines · 3.5 × 2 in · give one to anyone who has just arrived · edition {EDITION}</div>
</div></body></html>'''

# ---- write everything -------------------------------------------------------------
outputs = []
for ed in (FAITH, SECULAR):
    for paper in ('letter', 'a4'):
        html = flyer_html(ed, paper)
        if ed is SECULAR:
            # the whole point of this edition is that nothing religious survives into it
            for word in ('Jesus', 'cross', 'bless', 'God', 'church'):
                if word.lower() in html.lower():
                    raise SystemExit('secular edition still contains %r' % word)
        name = '%s-%s.html' % (ed['file'], paper)
        io.open(name, 'w', encoding='utf-8').write(html); outputs.append(name)
sheet = 'kamloops-life-guide-cards-letter.html'
io.open(sheet, 'w', encoding='utf-8').write(cards_sheet_html()); outputs.append(sheet)
for o in outputs: print('built', o)
