#!/usr/bin/env python3
"""2026-09-24 — the place popup, rebuilt around one chip vocabulary.

What the audit found, and what this does about it:

P0  The three action buttons (Directions / Call / Website) sat at the very bottom
    of a scrolling box, so on a 430x930 phone they were below the fold in every
    popup measured. The row is now sticky: it stays on screen while the rest
    scrolls under it, with a hairline above it so it reads as a bar.

P1  The region chip was a dark solid pill carrying a parenthetical explanation —
    wider than the place name and wrapping onto its own line. The explanation
    moves into the chip's tooltip; the chip keeps only the area name and joins
    the quiet meta family.

P1  Six chip styles lived in one popup (solid category, solid region, outline
    qualifier, theme pill, source badge, open/closed pill) at five font sizes and
    three radii. There are three roles now and they all share a size, a radius
    and a height: identity (the category), state (open / closed / holiday), and
    meta (everything else).

P1  The category chip was a saturated solid block in an interface with one blue
    accent — 51 competing brand colours, one per popup. It is now a tint of its
    own colour with the colour as text, and it carries the category's icon, so
    the chip, the map pin and the filter panel finally say the same thing. The
    text colour is darkened until it clears 4.5:1 on its own tint (catInk).

P2  Phone / email / hours had no alignment axis: when the hours wrapped, the
    value slid under its own label. They are one two-column grid now, which also
    required moving the task card below them (where it belongs anyway — it used
    to push the core facts down by about 90px).

P2  Five blocks of information were separated by margin alone. Two hairlines now
    mark the two real boundaries: facts | provenance | actions.

P2  The least important line in the popup was the most decorated one: a green
    badge, grey text and a blue link at 10.5px. The badge becomes a coloured dot
    and the line becomes one quiet grey row — the colour still carries which of
    the four source kinds it is.

P3  Two solid blue buttons competed (the task card's "How to" and the primary
    Directions). The task button becomes secondary; solid blue now means one
    thing in a popup.

    The favourite star was a text glyph — thin, amber, and the only character in
    a popup full of 1.8px line icons. It uses the icon set's star, filled when on.

Deliberately not touched:
- The leading ⭐ in 132 place notes. 425 ⭐ occur across the data and most are
  mid-sentence; converting only the leading one would make the set inconsistent,
  and running the note through iconify() would escape the HTML some notes carry.
- `.tag` / `.tag2` / `.tag3`: the bus-route popups still use them with a solid
  route colour and white text, which is correct there.
"""
import re, sys
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:120], n))
    s = s.replace(old, new)

# --------------------------------------------------------------------------
# 1. the chip system
# --------------------------------------------------------------------------
rep("""  .pv-theme{display:inline-block;font-size:9.5px;font-weight:600;padding:2px 8px;border-radius:999px;background:var(--paper);border:1px solid var(--line);color:var(--sub-ink);}""",
    """  /* 2026-09-24 — one chip vocabulary for the place popup. Three roles, one
     size, one radius, one height; only the fill differs.
       .pchip-id    the category — a tint of its own colour, with its icon
       .pchip-meta  region, qualifier, theme — quiet, bordered, grey
       .pchip-pick  the editor's pick, the one warm exception
     .pv-open (state) keeps its own rule below; it is the only chip allowed a
     semantic colour, because "open now" is the only thing worth a colour. */
  .pchip{display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:600;
    padding:2px 9px;border-radius:999px;line-height:1.6;margin:0 4px 4px 0;max-width:100%;}
  .pchip .ic{width:12px;height:12px;flex:none;}
  .pchip-id{background:color-mix(in srgb,var(--cc) 11%,var(--card));color:var(--ci);
    border:1px solid color-mix(in srgb,var(--cc) 26%,transparent);}
  .pchip-meta{background:var(--paper);border:1px solid var(--line);color:var(--sub-ink);}
  .pchip-pick{background:#fdf3d8;border:1px solid #f0dda6;color:#6b4e00;}
  .pchip-meta.pv-cut{display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
  .pv-theme{display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:600;padding:2px 9px;border-radius:999px;background:var(--paper);border:1px solid var(--line);color:var(--sub-ink);}
  .pv-theme .ic{width:12px;height:12px;flex:none;}""")

# --------------------------------------------------------------------------
# 2. name, tag row, label/value grid, provenance line
# --------------------------------------------------------------------------
rep("""  .pt{font-family:var(--font);font-size:14px;font-weight:500;margin:2px 0 3px;}
  .ptags{margin:0 0 6px;}""",
    """  .pt{font-family:var(--font);font-size:14px;font-weight:700;letter-spacing:-.15px;margin:2px 0 5px;}
  .ptags{margin:0 0 7px;}""")

rep("""  .pr{margin:4px 0;}
  .pl{color:var(--sub-ink);display:inline-block;min-width:38px;padding-right:6px;}
  .pq{color:var(--sub-ink);font-size:11px;}
  .pv{font-size:11px;color:var(--sub-ink);margin-top:7px;}""",
    """  .pr{margin:4px 0;}
  /* phone / email / hours share one two-column grid, so the values line up on a
     single axis and a wrapped opening-hours string no longer slides back under
     its own label. */
  .pkv{display:grid;grid-template-columns:auto 1fr;gap:4px 9px;margin:6px 0 2px;align-items:baseline;}
  .pl{color:var(--sub-ink);white-space:nowrap;}
  .pq{color:var(--sub-ink);font-size:11px;}
  .pv{font-size:11px;color:var(--sub-ink);margin-top:9px;padding-top:8px;border-top:1px solid var(--line);}""")

rep("""  .pr a[href^="tel:"]{color:var(--accent-text);text-decoration:none;font-weight:600;}""",
    """  .pr a[href^="tel:"],.pkv a[href^="tel:"]{color:var(--accent-text);text-decoration:none;font-weight:600;}""")

# --------------------------------------------------------------------------
# 3. the provenance line loses its badge and keeps its colour as a dot
# --------------------------------------------------------------------------
rep("""  .pv-src{display:inline-block;padding:1px 6px;border-radius:5px;font-size:10.5px;
    background:#eef2f7;color:#4b5b6b;cursor:help;}
  .pv-verified{cursor:help;}
  .pv-src.src-official{background:#e6f4ea;color:#1e6b38;}
  .pv-src.src-own{background:#fff3d6;color:#7a5c00;}
  .pv-src.src-opendata{background:#e8f0fb;color:#1d4e8f;}
  .pv-src.src-stub{background:#fde8e6;color:#8c2f22;}""",
    """  /* 2026-09-24: this used to be a filled badge — the most decorated element in
     the popup on its least important line. The four source kinds still differ by
     colour, but the colour is now a 6px dot and the text is the same grey as the
     rest of the row. */
  .pv-src{display:inline-flex;align-items:center;gap:5px;font-size:11px;
    font-weight:600;color:var(--sub-ink);cursor:help;}
  .pv-src::before{content:'';width:6px;height:6px;border-radius:999px;background:#4b5b6b;flex:none;}
  .pv-verified{cursor:help;}
  .pv-src.src-official::before{background:#1e6b38;}
  .pv-src.src-own::before{background:#7a5c00;}
  .pv-src.src-opendata::before{background:#1d4e8f;}
  .pv-src.src-stub::before{background:#8c2f22;}""")

# --------------------------------------------------------------------------
# 4. the task card: secondary button, and it no longer leads
# --------------------------------------------------------------------------
rep("""  .pv-task-go{display:inline-block;margin-top:3px;background:var(--accent);color:#fff;border:none;border-radius:999px;
    padding:6px 11px;font-weight:600;font-size:12px;line-height:1;font-family:inherit;cursor:pointer;min-height:30px;}""",
    """  /* secondary, not solid: the popup's one filled blue button is "Directions". */
  .pv-task-go{display:inline-block;margin-top:3px;background:var(--card);color:var(--accent-text);
    border:1px solid color-mix(in srgb,var(--accent) 45%,transparent);border-radius:999px;
    padding:6px 11px;font-weight:700;font-size:12px;line-height:1;font-family:inherit;cursor:pointer;min-height:30px;}
  .pv-task-go:hover{background:color-mix(in srgb,var(--accent) 8%,var(--card));}""")

# --------------------------------------------------------------------------
# 5. the action row stays on screen
# --------------------------------------------------------------------------
rep("""  .pact{display:flex;align-items:center;gap:6px;margin-top:10px;flex-wrap:wrap;}""",
    """  /* 2026-09-24: sticky. Leaflet gives a tall popup its own scrollbox, and these
     three buttons sat at the bottom of it — below the fold in every popup the
     audit measured. Sticky keeps them in view without covering anything: the row
     is still in flow, so the last line of content is never hidden behind it. */
  .pact{display:flex;align-items:center;gap:6px;margin-top:10px;flex-wrap:wrap;
    position:sticky;bottom:0;z-index:2;background:var(--card);
    padding:9px 0 1px;border-top:1px solid var(--line);}""")

# --------------------------------------------------------------------------
# 6. the favourite star becomes a line icon
# --------------------------------------------------------------------------
rep("""  .fav-star{background:none;border:none;cursor:pointer;font-size:16px;line-height:1;padding:0 0 0 6px;vertical-align:middle;color:#8a5a00;}  /* 2026-09-13: was #f2a900 (2.0:1); the empty ☆ is text and needs 4.5:1 */
  .fav-star.active{color:#a66300;}""",
    """  /* 2026-09-24: was the ☆ / ★ characters — thin, amber, and the only glyph in a
     popup otherwise built from 1.8px line icons. Same icon, filled when on. */
  .fav-star{background:none;border:none;cursor:pointer;font-size:16px;line-height:1;padding:0 0 0 6px;vertical-align:middle;color:#8a5a00;}
  .fav-star .ic{width:17px;height:17px;display:block;}
  .fav-star.active{color:#a66300;}
  .fav-star.active .ic{fill:currentColor;}""")

# --------------------------------------------------------------------------
# 7. catInk(): the category colour, darkened until it clears AA on its own tint
# --------------------------------------------------------------------------
rep("""function catColour(c){return CD[c]||'#6b7676';}""",
    """function catColour(c){return CD[c]||'#6b7676';}
// The identity chip prints the category's colour on an 11% tint of itself. Most
// of the 51 clear 4.5:1 that way; the rest are stepped 10% darker until they do,
// so no chip in the set is ever below AA. Pure function, memoised by colour.
function _srgb(v){v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);}
function _lum(c){return 0.2126*_srgb(c[0])+0.7152*_srgb(c[1])+0.0722*_srgb(c[2]);}
function _rgb(h){h=String(h).replace('#','');return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)];}
function _contrast(a,b){const x=_lum(a),y=_lum(b);return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05);}
const _INK={};
function catInk(c){
  const col=catColour(c);
  if(_INK[col])return _INK[col];
  const base=_rgb(col), bg=base.map(v=>Math.round(v*0.11+255*0.89));
  let t=base.slice();
  for(let i=0;i<24&&_contrast(t,bg)<4.5;i++)t=t.map(v=>Math.round(v*0.9));
  _INK[col]='#'+t.map(v=>('0'+v.toString(16)).slice(-2)).join('');
  return _INK[col];
}
// The area name carries a parenthetical for readers who do not know the city
// ("Sahali/Aberdeen (hillside south of Downtown, home to TRU)"). That sentence is
// worth keeping, but not at the width of a chip sitting under the place name —
// the chip shows the name and the tooltip carries the rest.
function regShort(g){return regLabel(g).split(/\\s*[（(]/)[0].trim();}""")

# --------------------------------------------------------------------------
# 8. popup(): the markup
# --------------------------------------------------------------------------
rep("""  let b='<div class="pt">'+esc(nm)+'<button class="fav-star'+starActive+'" data-i="'+idx+'" onclick="toggleFav(this,event)" aria-pressed="'+faved+'" aria-label="'+(faved?u.favRemove:u.favAdd)+'">'+starChar+'</button></div>';
  b+='<div class="ptags"><span class="tag" style="background:'+catColour(p.c)+'">'+catLabel(p.c)+'</span><span class="tag tag2">'+regLabel(p.g)+'</span>';""",
    """  let b='<div class="pt">'+esc(nm)+'<button class="fav-star'+starActive+'" data-i="'+idx+'" onclick="toggleFav(this,event)" aria-pressed="'+faved+'" aria-label="'+(faved?u.favRemove:u.favAdd)+'">'+starChar+'</button></div>';
  b+='<div class="ptags"><span class="pchip pchip-id" style="--cc:'+catColour(p.c)+';--ci:'+catInk(p.c)+'">'
    +emojiIcon(IC[p.c])+catLabel(p.c)+'</span>'
    +'<span class="pchip pchip-meta pv-cut" title="'+esc(regLabel(p.g))+'">'+esc(regShort(p.g))+'</span>';""")

rep("""  if(p.tag&&u[p.tag])b+='<span class="tag tag3">'+u[p.tag]+'</span>';""",
    """  if(p.tag&&u[p.tag])b+='<span class="pchip pchip-meta">'+u[p.tag]+'</span>';""")

rep("""  if(pick)b+='<span class="tag tag-pick">⭐ '+esc(u.recPick)+'</span>';""",
    """  if(pick)b+='<span class="pchip pchip-pick">'+ico('star')+esc(u.recPick)+'</span>';""")

# the star button's glyph is now an icon
rep("""  const starChar=favorites.has(p.id)?'★':'☆',starActive=favorites.has(p.id)?' active':'';""",
    """  const starChar=ico('star'),starActive=favorites.has(p.id)?' active':'';""")

# phone / email / hours into one grid, with the task card moved below them
rep("""  const tks=(typeof TASKS!=='undefined')?TASKS.filter(t=>t.place===p.id):[];
  if(tks.length){
    b+='<div class="pv-task"><b>'+u.pvTaskLead+'</b>'
      +tks.map(t=>'<div>'+esc(taskText(t.t))+' <button type="button" class="pv-task-go" data-task="'+esc(t.id)+'">'+esc(u.pvTaskGo)+'</button></div>').join('')
      +'</div>';
  }
  if(p.p)b+='<div class="pr"><span class="pl">'+u.lPhone+'</span>'+phoneHtml(p.p)
    +(p.pq&&u[p.pq]?' <span class="pq">('+u[p.pq]+')</span>':'')+'</div>';
  if(p.e)b+='<div class="pr"><span class="pl">'+u.lEmail+'</span><a href="mailto:'+p.e+'">'+p.e+'</a></div>';""",
    """  const tks=(typeof TASKS!=='undefined')?TASKS.filter(t=>t.place===p.id):[];
  // 2026-09-24: phone, email and hours are one grid so their values share a
  // single left edge. The task card used to sit above them and pushed the core
  // facts down by about 90px; it now follows the hours.
  let kv='';
  if(p.p)kv+='<span class="pl">'+u.lPhone+'</span><span class="pval">'+phoneHtml(p.p)
    +(p.pq&&u[p.pq]?' <span class="pq">('+u[p.pq]+')</span>':'')+'</span>';
  if(p.e)kv+='<span class="pl">'+u.lEmail+'</span><span class="pval"><a href="mailto:'+p.e+'">'+p.e+'</a></span>';""")

rep("""  b+='<div class="pr"><span class="pl">'+u.lHours+'</span>'+pill+hTxt+'</div>';
  b+=themesHtml;""",
    """  kv+='<span class="pl">'+u.lHours+'</span><span class="pval">'+pill+hTxt+'</span>';
  b+='<div class="pkv">'+kv+'</div>';
  if(tks.length){
    b+='<div class="pv-task"><b>'+u.pvTaskLead+'</b>'
      +tks.map(t=>'<div>'+esc(taskText(t.t))+' <button type="button" class="pv-task-go" data-task="'+esc(t.id)+'">'+esc(u.pvTaskGo)+'</button></div>').join('')
      +'</div>';
  }
  b+=themesHtml;""")

open(E, 'w', encoding='utf-8').write(s)
print('p27 applied')
