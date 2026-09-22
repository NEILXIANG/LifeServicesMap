#!/usr/bin/env python3
"""2026-09-22 — search improvements 1, 4 and 5 from the analytics review
(a real visitor searched "walk in clinic", got 0, and left via an unrelated card).

1. No exact match → show the closest places. A multi-word search that matches
   nothing now falls back to places matching at least half of its meaningful
   words (a word counts only on a name, alias, category, theme, tag or address
   hit — never on a stray word in the notes). The status line and a note say
   plainly that these are the closest matches, not exact ones. search_empty is
   still recorded for the typed query, so the gap stays visible in the data.
2. The matching task card leads the empty / closest state as a card (icon,
   title, one-line why, "Open this guide"), instead of a small secondary button
   under "Clear search".
3. Health searches get an answer box: the North Shore walk-in centre with its
   live open/closed status and hours from the data, 8-1-1, pharmacists for minor
   ailments, 911 — every line already stated on the "care without a family
   doctor" card. Not shown for dental / vet / legal clinics or crisis queries.
"""
import sys
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:100], n))
    return src.replace(old, new)

# ------------------------------------------------------------------ strings
anchor = "UI.zh.emptyGuideHint='是想办事？打开「{T}」';"
i = s.index(anchor); j = s.index('\n', i)
STR = r"""
UI.zh.searchClosestNote=(q,n)=>`没有完全匹配「${q}」的地点，地图上是最接近的 ${n} 个。`;UI.en.searchClosestNote=(q,n)=>`No exact match for “${q}” — the map shows the ${n} closest match${n===1?'':'es'}.`;UI.fr.searchClosestNote=(q,n)=>`Aucun résultat exact pour « ${q} » — la carte montre ${n===1?'le résultat le plus proche':'les '+n+' résultats les plus proches'}.`;UI.es.searchClosestNote=(q,n)=>`Ningún resultado exacto para «${q}»: el mapa muestra ${n===1?'el resultado más parecido':'los '+n+' resultados más parecidos'}.`;UI.ko.searchClosestNote=(q,n)=>`“${q}”와 정확히 일치하는 곳이 없어 가장 비슷한 결과 ${n}곳을 지도에 표시합니다.`;UI.ja.searchClosestNote=(q,n)=>`「${q}」に完全に一致する場所がないため、近い結果を${n}件表示しています。`;
UI.zh.searchClosestN=n=>`最接近的 ${n} 个`;UI.en.searchClosestN=n=>`${n} closest match${n===1?'':'es'}`;UI.fr.searchClosestN=n=>`${n} résultat${n===1?'':'s'} approchant${n===1?'':'s'}`;UI.es.searchClosestN=n=>`${n} resultado${n===1?'':'s'} aproximado${n===1?'':'s'}`;UI.ko.searchClosestN=n=>`비슷한 결과 ${n}곳`;UI.ja.searchClosestN=n=>`近い結果 ${n}件`;
UI.zh.shCardLead='这可能是你要找的';UI.en.shCardLead='This may be what you need';UI.fr.shCardLead='C’est peut-être ce que vous cherchez';UI.es.shCardLead='Quizá esto es lo que busca';UI.ko.shCardLead='찾으시는 내용일 수 있습니다';UI.ja.shCardLead='お探しの内容かもしれません';
UI.zh.shOpenCard='打开这张办事卡';UI.en.shOpenCard='Open this guide';UI.fr.shOpenCard='Ouvrir cette fiche';UI.es.shOpenCard='Abrir esta guía';UI.ko.shOpenCard='이 안내 열기';UI.ja.shOpenCard='この手順を開く';
UI.zh.hcTitle='今天要看病？';UI.en.hcTitle='Need to see someone today?';UI.fr.hcTitle='Besoin de voir quelqu’un aujourd’hui ?';UI.es.hcTitle='¿Necesita atención médica hoy?';UI.ko.hcTitle='오늘 진료가 필요하세요?';UI.ja.hcTitle='今日受診したいですか？';
UI.zh.hcUpcc='北岸急诊中心（UPCC，700 Tranquille Rd）：不需要家庭医生，直接去。当天名额满了就不再接收，尽量早去。';UI.en.hcUpcc='North Shore UPCC (700 Tranquille Rd): walk in, no family doctor needed. Go early — once the day’s list is full they stop taking people.';UI.fr.hcUpcc='UPCC de la rive nord (700 Tranquille Rd) : sans rendez-vous, sans médecin de famille. Allez-y tôt — une fois la liste du jour pleine, ils n’acceptent plus personne.';UI.es.hcUpcc='UPCC de la ribera norte (700 Tranquille Rd): sin cita y sin médico de familia. Vaya temprano: cuando se llena la lista del día, ya no reciben a nadie.';UI.ko.hcUpcc='노스쇼어 UPCC(700 Tranquille Rd): 예약 없이 바로 가면 되고 주치의가 없어도 됩니다. 그날 명단이 차면 더 받지 않으니 일찍 가세요.';UI.ja.hcUpcc='ノースショアのUPCC（700 Tranquille Rd）：予約不要、かかりつけ医がいなくても受診できます。その日の受付枠が埋まると締め切るので、早めに行きましょう。';
UI.zh.hcHours='营业时间';UI.en.hcHours='Hours';UI.fr.hcHours='Heures';UI.es.hcHours='Horario';UI.ko.hcHours='운영 시간';UI.ja.hcHours='受付時間';
UI.zh.hcOpenNow='现在开着';UI.en.hcOpenNow='Open now';UI.fr.hcOpenNow='Ouvert maintenant';UI.es.hcOpenNow='Abierto ahora';UI.ko.hcOpenNow='지금 운영 중';UI.ja.hcOpenNow='現在受付中';
UI.zh.hcClosedNow='现在已关门';UI.en.hcClosedNow='Closed now';UI.fr.hcClosedNow='Fermé en ce moment';UI.es.hcClosedNow='Cerrado ahora';UI.ko.hcClosedNow='지금은 닫혀 있음';UI.ja.hcClosedNow='現在は受付時間外';
UI.zh.hc811='不急或拿不准：打 8-1-1，24 小时有护士接听，可以要翻译。';UI.en.hc811='Not urgent, or not sure: call 8-1-1 — a nurse, 24 hours, with interpreters.';UI.fr.hc811='Pas urgent, ou pas sûr : appelez le 8-1-1 — une infirmière, 24 h sur 24, avec interprètes.';UI.es.hc811='Si no es urgente o no está seguro: llame al 8-1-1 — una enfermera, las 24 horas, con intérpretes.';UI.ko.hc811='급하지 않거나 잘 모르겠으면: 8-1-1에 전화하세요 — 24시간 간호사가 받고, 통역을 요청할 수 있습니다.';UI.ja.hc811='急ぎでない、または判断に迷うとき：8-1-1へ — 24時間看護師が対応し、通訳も頼めます。';
UI.zh.hcPharm='小病：药剂师可以评估并开药，BC 省共 21 种常见小病。';UI.en.hcPharm='Minor ailments: a pharmacist can assess and prescribe — 21 of them in BC.';UI.fr.hcPharm='Affections mineures : un pharmacien peut évaluer et prescrire — 21 en C.-B.';UI.es.hcPharm='Afecciones menores: un farmacéutico puede evaluar y recetar — 21 en BC.';UI.ko.hcPharm='가벼운 질환: 약사가 진찰하고 처방할 수 있습니다 — BC주에서 21가지.';UI.ja.hcPharm='軽い病気：薬剤師が判断して処方できます — BC州では21種類。';
UI.zh.hc911='胸痛、呼吸困难、大出血：打 911。';UI.en.hc911='Chest pain, trouble breathing, heavy bleeding: call 911.';UI.fr.hc911='Douleur thoracique, difficulté à respirer, saignement abondant : appelez le 911.';UI.es.hc911='Dolor de pecho, dificultad para respirar, sangrado abundante: llame al 911.';UI.ko.hc911='가슴 통증, 호흡 곤란, 심한 출혈: 911에 전화하세요.';UI.ja.hc911='胸の痛み、呼吸困難、大量の出血：911へ。';
UI.zh.hcShowUpcc='在地图上看';UI.en.hcShowUpcc='Show it on the map';UI.fr.hcShowUpcc='Voir sur la carte';UI.es.hcShowUpcc='Ver en el mapa';UI.ko.hcShowUpcc='지도에서 보기';UI.ja.hcShowUpcc='地図で見る';"""
s = s[:j] + STR + s[j:]

# ------------------------------------------------------------------ markup + css
s = rep(s, '<div class="empty-state" id="emptyState" role="status" aria-live="polite" hidden></div>\n',
           '<div class="empty-state" id="emptyState" role="status" aria-live="polite" hidden></div>\n'
           '<div class="search-help" id="searchHelp" hidden></div>\n')
s = rep(s, "  .empty-state[hidden]{display:none;}\n",
"""  .empty-state[hidden]{display:none;}
  /* 2026-09-22: the answer box for health searches, the closest-match note, and
     the task card that leads an empty result */
  .search-help{margin:10px 20px 0;padding:14px 16px;background:var(--card);border:1px solid var(--line);
    border-radius:10px;font-size:13px;color:var(--ink);line-height:1.55;text-align:left;}
  .search-help[hidden]{display:none;}
  .sh-title{margin:0 0 6px;font-weight:700;font-size:14px;}
  .sh-note{margin:0 0 8px;color:var(--sub-ink);}
  .sh-list{margin:0;padding-left:18px;}
  .sh-list li{margin:4px 0;}
  .sh-status{font-weight:700;}
  .sh-status.open{color:var(--sage);}
  .sh-btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;}
  .sh-btn{font-family:inherit;font-size:12.5px;font-weight:600;border-radius:8px;padding:7px 12px;cursor:pointer;
    background:var(--card);color:var(--accent-text);border:1px solid color-mix(in srgb,var(--accent) 35%,transparent);}
  .sh-btn.primary{background:var(--accent);color:#fff;border-color:transparent;}
  .sh-card{text-align:left;margin:0 0 12px;padding:12px 14px;border:1px solid color-mix(in srgb,var(--accent) 35%,transparent);
    border-radius:10px;background:color-mix(in srgb,var(--accent) 6%,var(--card));color:var(--ink);}
  .sh-card .sh-lead{margin:0 0 2px;font-size:11.5px;font-weight:600;color:var(--accent-text);}
  .sh-card .sh-card-t{margin:0 0 4px;font-weight:700;font-size:14px;}
  .sh-card .sh-card-why{margin:0 0 8px;font-size:12.5px;color:var(--sub-ink);}
  .sh-card .sh-card-t .ic{width:16px;height:16px;vertical-align:-3px;margin-right:4px;}
""")
s = rep(s, "    .empty-state{margin:10px 12px 0;padding:14px 16px;}\n",
           "    .empty-state{margin:10px 12px 0;padding:14px 16px;}\n    .search-help{margin:8px 12px 0;padding:12px 14px;}\n")

# ------------------------------------------------------------------ 1. closest-match fallback
s = rep(s, """  M.forEach(m=>{
    const sc=searching?matchScore(m.data,searchTerm):0;
    m.score=sc;
    const s=markerPasses(m,sc);
    if(s){showMarker(m);v++;bounds.push([m.data.lat,m.data.lng]);}else{hideMarker(m);}});
  const u=UI[L_];""",
"""  M.forEach(m=>{
    const sc=searching?matchScore(m.data,searchTerm):0;
    m.score=sc;
    const s=markerPasses(m,sc);
    if(s){showMarker(m);v++;bounds.push([m.data.lat,m.data.lng]);}else{hideMarker(m);}});
  // 2026-09-22: nothing matched every word — show the places that match most of
  // them rather than an empty map ("walk in clinic", "pharmacy near me").
  _exactN=v;_closest=false;
  if(searching&&v===0&&!isCrisisQuery(searchRaw||searchTerm)){
    // Only for a query of two or more words: a single word that finds nothing
    // is a typo or a gap, and guessing at it would hide that. Strictest first —
    // every meaningful word, then one fewer — and never below half of them.
    const words=_closestWords(searchTerm);
    if(String(searchTerm).trim().split(/\s+/).length>=2&&words.length>=1){
      const cand=[];
      M.forEach(m=>{
        if(!markerPasses(m,1))return;              // the active filters still apply
        let hit=0,sc=0;
        words.forEach(w=>{const x=matchScore1(m.data,w);if(x>=40){hit++;sc+=x;}});
        if(hit)cand.push({m,hit,sc});
      });
      const floor=Math.max(1,Math.ceil(words.length/2));
      for(let need=words.length;need>=floor&&!v;need--){
        cand.forEach(c=>{if(c.hit>=need){c.m.score=c.sc;showMarker(c.m);v++;bounds.push([c.m.data.lat,c.m.data.lng]);}});
      }
      _closest=v>0;
    }
  }
  const u=UI[L_];""")
s = rep(s, "let L_='en';\nconst map=L.map('map',",
"""let L_='en';
// 2026-09-22: Leaflet 1.9's map.hasLayer(undefined) throws. The cluster plugin's
// zoomToShowLayer asks exactly that when a new search hides the marker it was
// still panning to (rapid searches, pre-existing). Undefined is simply "not on
// the map".
(function(){const h=L.Map.prototype.hasLayer;L.Map.prototype.hasLayer=function(l){return !!l&&h.call(this,l);};})();
const map=L.map('map',""")
s = rep(s, "    st.textContent=u.searchResultsN(v);\n",
           "    st.textContent=_closest?u.searchClosestN(v):u.searchResultsN(v);\n")
s = rep(s, "let _lastFitKey='';\nfunction apply(){",
"""let _lastFitKey='';
// Exact-match count of the last apply() and whether the map is showing closest
// matches instead — logSearch reports the gap from the exact count.
let _exactN=0,_closest=false;
const _CLOSEST_STOP=/^(near|nearby|me|open|now|today|best|good|cheap|store|shop|place|places|kamloops|bc|please)$/;
function _closestWords(q){
  q=String(q||'').toLowerCase();
  if(/[\\u3400-\\u9fff\\uac00-\\ud7af\\u3040-\\u30ff]/.test(q))return [];   // CJK has no spaces to split on
  return q.replace(_Q_STOP,' ').replace(/[?¿!¡.,;:()"'“”]/g,' ').split(/\\s+/)
    .filter(w=>w.length>=3&&/[a-zà-ÿ]/.test(w)&&!_CLOSEST_STOP.test(w));
}
function apply(){""")
# logSearch: the gap is the exact count
s = rep(s, "  trackEvent('search_run',{q:raw,len:raw.length,n:lastVisible,filtered:filtered});",
           "  trackEvent('search_run',{q:raw,len:raw.length,n:lastVisible,filtered:filtered,closest:_closest||undefined});")
s = rep(s, "  if(lastVisible===0){\n    trackEvent('search_empty',{q:raw,len:raw.length,",
           "  if(_exactN===0){\n    trackEvent('search_empty',{q:raw,len:raw.length,closest:_closest?lastVisible:undefined,")

# ------------------------------------------------------------------ 4. the task card leads the empty state
s = rep(s, """  // "health card", 医疗卡, 학교 등록: the reader asked the map a guide question.
  if(searching){
    const q=(searchRaw||searchTerm||'').trim();
    const hit=q.length>=2?TASKS.find(t=>taskMatchesLoose(t,q)):null;
    if(hit){
      const go=document.createElement('button');go.className='empty-btn empty-guide';
      go.innerHTML=ico('guide')+esc(u.emptyGuideHint.replace('{T}',taskText(hit.t)));
      go.onclick=()=>openGuide('search_empty',hit.id);   // openGuide records guide_open itself
      el.appendChild(go);
    }
  }
}""",
"""  // "health card", 医疗卡, 학교 등록: the reader asked the map a guide question.
  // 2026-09-22: the card now LEADS the empty state instead of trailing it as a
  // small second button — the one visitor who hit this tapped past it.
  if(searching){
    const hit=_taskForQuery();
    if(hit&&!_isHealthQuery(searchRaw||searchTerm))el.insertBefore(_taskCardEl(hit,'search_empty'),el.firstChild);
  }
}
function _taskForQuery(){
  const q=(searchRaw||searchTerm||'').trim();
  return q.length>=2?TASKS.find(t=>taskMatchesLoose(t,q)):null;
}
function _firstSentence(s){s=String(s||'');const m=s.match(/^.+?[.!?。！？](\\s|$)/);return (m?m[0]:s).trim();}
function _taskCardEl(t,src){
  const u=UI[L_],box=document.createElement('div');box.className='sh-card';
  box.innerHTML='<p class="sh-lead">'+esc(u.shCardLead)+'</p><p class="sh-card-t">'+emojiIcon(t.icon)+esc(taskText(t.t))+'</p>'
    +'<p class="sh-card-why">'+esc(_firstSentence(taskText(t.why)))+'</p>';
  const b=document.createElement('button');b.type='button';b.className='sh-btn primary';b.textContent=u.shOpenCard;
  b.onclick=()=>openGuide(src,t.id);   // openGuide records guide_open itself
  box.appendChild(b);return box;
}
// ---- 2026-09-22: the answer box under the search bar ------------------------
const _HEALTH_RE=/doctor|clinic|walk.?in\\b|sick|urgent|nurse|\\bgp\\b|physician|medical|fever|médecin|clinique|malade|urgence|infirmi|médico|clínica|enfermo|urgencia|enfermer|医生|看病|诊所|診所|急诊|急診|生病|发烧|發燒|门诊|門診|醫生|의사|병원|진료|아파(?!트)|응급|医者|病院|診療|受診|病気|発熱/i;
const _NOT_HEALTH_RE=/\\bdent|\\bvet\\b|veterin|animal|\\bpets?\\b|legal|lawyer|\\blaw\\b|牙|兽医|獸醫|宠物|寵物|法律|치과|동물|歯|動物/i;
function _isHealthQuery(q){q=String(q||'');return _HEALTH_RE.test(q)&&!_NOT_HEALTH_RE.test(q);}
const _UPCC_ID='b29c9af7';
function renderSearchHelp(){
  const el=document.getElementById('searchHelp');if(!el)return;
  const q=(searchRaw||searchTerm||'').trim(),u=UI[L_];
  if(!searchTerm||isCrisisQuery(q)){el.hidden=true;el.innerHTML='';el.dataset.kind='';return;}
  const health=_isHealthQuery(q),upcc=P.find(p=>p.id===_UPCC_ID);
  if(!health&&!_closest){el.hidden=true;el.innerHTML='';el.dataset.kind='';return;}
  el.innerHTML='';el.hidden=false;
  if(_closest){const n=document.createElement('p');n.className='sh-note';n.textContent=u.searchClosestNote(q,lastVisible);el.appendChild(n);}
  if(health&&upcc){
    el.dataset.kind='health';
    const st=openState(upcc.h),hrs=fmtHours(upcc.h,L_);
    const stTxt=st?('<span class="sh-status'+(st.open?' open':'')+'">'+esc(st.open?u.hcOpenNow:u.hcClosedNow)+'</span> · '):'';
    const box=document.createElement('div');
    box.innerHTML='<p class="sh-title">'+esc(u.hcTitle)+'</p><ul class="sh-list">'
      +'<li>'+esc(u.hcUpcc)+'<br>'+stTxt+esc(u.hcHours)+u.colon+esc(hrs)+'</li>'
      +'<li>'+phoneHtml(esc(u.hc811))+'</li><li>'+esc(u.hcPharm)+'</li><li>'+esc(u.hc911).replace(/\\b911\\b/,'<a href="tel:911">911</a>')+'</li></ul>';
    const btns=document.createElement('div');btns.className='sh-btns';
    const b1=document.createElement('button');b1.type='button';b1.className='sh-btn primary';b1.textContent=u.hcShowUpcc;
    b1.onclick=()=>{const m=M.find(x=>x.data.id===_UPCC_ID);if(m){trackEvent('search_help_click',{kind:'upcc'});focusMarker(m,16);}};
    btns.appendChild(b1);
    const sick=TASKS.find(t=>t.id==='sick');
    if(sick){const b2=document.createElement('button');b2.type='button';b2.className='sh-btn';b2.textContent=u.emptyGuideHint.replace('{T}',taskText(sick.t));
      b2.onclick=()=>openGuide('search_help','sick');btns.appendChild(b2);}
    box.appendChild(btns);el.appendChild(box);
  }else{
    el.dataset.kind='closest';
    const hit=_taskForQuery();
    if(hit)el.appendChild(_taskCardEl(hit,'search_closest'));
  }
}""")
# apply() ends with renderEmptyState — add the help box right after
s = rep(s, "  writeURLState();\n  renderEmptyState(v,searching,filtered);\n}",
           "  writeURLState();\n  renderEmptyState(v,searching,filtered);\n  try{renderSearchHelp();}catch(e){}\n}")
open(E, 'w', encoding='utf-8').write(s)
print('p17 applied')
