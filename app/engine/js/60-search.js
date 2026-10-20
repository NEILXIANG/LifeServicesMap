// Scores a place against the query instead of returning a flat yes/no, so results
// can be ordered by how well they match rather than dumped in data order.
// Field order below is the ranking: name-prefix beats name-contains beats category,
// and notes — the longest, noisiest field — rank last.
// "pharmacy north shore": a phrase that names a thing and a place fails as one
// string, so a multi-word query is tried whole first and then as words that
// must all hit (each on any field). The weakest word sets the score.
const _nameHitCache=new Map();
function _someNameHas(q){
  let r=_nameHitCache.get(q);
  if(r===undefined){r=P.some(p=>p.n.toLowerCase().includes(q));if(_nameHitCache.size>400)_nameHitCache.clear();_nameHitCache.set(q,r);}
  return r;
}
function matchScore(d,q){
  const whole=matchScore1(d,q);
  if(whole>0)return whole;
  const words=q.split(/\s+/).filter(w=>w.length>=2);
  if(words.length<2)return 0;
  if(_someNameHas(q))return 0;           // a whole name was typed: only whole-query matches
  let min=1e9;
  for(const w of words){const sc=matchScore1(d,w);if(sc<=0)return 0;if(sc<min)min=sc;}
  return Math.max(1,min-1);
}
function _wordStart(t,q){let i=t.indexOf(q);while(i>=0){if(i===0||!/[a-z0-9\u00c0-\u024f]/.test(t[i-1]))return true;i=t.indexOf(q,i+1);}return false;}
function matchScore1(d,q){
  const name=d.n.toLowerCase(), addr=(d.a||'').toLowerCase();
  const cat=catLabel(d.c).toLowerCase();
  // 2026-09-10: the area labels carry a geographic hint in brackets — "South
  // Kamloops/Downtown (south riverbank)", "Brocklehurst (west side, north
  // bank)". That hint is for a reader choosing an area, not a search index:
  // matching on it meant "bank" returned every place in two whole areas, 103
  // schools and parks and clinics ahead of the actual banks. Only the name is
  // searchable; the bracketed part is stripped first.
  const reg=regLabel(d.g).replace(/\s*[（(][^）)]*[）)]/g,'').toLowerCase();
  const note=(noteText(d)||'').toLowerCase();
  const tag=(d.tag&&UI[L_][d.tag]?UI[L_][d.tag]:'').toLowerCase();
  // Theme names are searchable in the reading language for the same reason
  // category names are: someone typing "亲子" or "scenic" is naming a real facet
  // of this data and should not have to find the filter panel first.
  const themes=(d.t||[]).map(k=>themeLabel(k).toLowerCase());
  // Alternate names a reader might actually type in their own language — 医院
  // rather than "Royal Inland", 驾照 rather than "ICBC". Without these the
  // search box quietly fails the readers the six languages exist for.
  const alias=(d.alias||[]).map(a=>String(a).toLowerCase());
  // 2026-10-04 (newcomer test): "sin" matched inside "Licensing", "Housing", "Crossing" and the Spanish
  // alias "clínica sin cita", so the SIN search led to ICBC and a laundromat. A Latin query of three
  // letters or fewer (SIN, ER, GP, TRU, MSP) must start a word; longer and CJK queries are unchanged.
  const short=q.length<=3&&/^[a-z0-9]+$/.test(q);
  const has=t=>short?_wordStart(t,q):t.includes(q);
  if(name.startsWith(q))return 100;
  if(has(name))return 80;
  if(alias.some(a=>a===q||a.startsWith(q)))return 70;
  if(alias.some(a=>has(a)))return 65;
  if(cat.startsWith(q)||has(cat))return 60;
  // the synonym table: any word for this kind of place, in any of the six languages
  if(synCats(q).has(d.c))return 58;
  if(themes.some(t=>has(t)))return 55;
  if(tag&&has(tag))return 50;
  if(has(addr))return 40;
  if(has(reg))return 30;
  // Notes are long prose, so a hit inside one only counts for a query with enough
  // information in it. Two CJK/Hangul characters are a whole word; two Latin
  // letters are not — so the threshold differs by script rather than raw length.
  if(note.includes(q)){
    const cjk=/[\u3400-\u9fff\uac00-\ud7af\u3040-\u30ff]/.test(q);
    return q.length>=(cjk?2:4)?10:0;
  }
  return 0;
}
const MIN_QUERY=2;
// Single source of truth for "does this marker belong on the map right now".
// apply() passes the score it has already computed; the focus cleanup in
// focusMarker() calls it for one marker with no score in hand.
function markerPasses(m,sc){
  // 2026-09-22: a search pauses the category filter (it says "what", like the
  // category did — the newer one wins). Areas, themes, open now, near me still apply.
  const inFilter=(aC.size===0||!!searchTerm||aC.has(m.ck))&&aR.has(m.gk)&&themeOk(m.data)&&openNowOk(m.data)&&nearOk(m.data);
  if(!inFilter)return false;
  if(!searchTerm)return true;
  return (sc===undefined?matchScore(m.data,searchTerm):sc)>0;
}
let _lastFitKey='';
// Exact-match count of the last apply() and whether the map is showing closest
// matches instead — logSearch reports the gap from the exact count.
let _exactN=0,_closest=false;
const _CLOSEST_STOP=new RegExp('^(near|nearby|me|open|now|today|best|good|cheap|store|shop|place|places|'+CITY_META.searchStopwords.join('|')+'|please)$');
function _closestWords(q){
  q=String(q||'').toLowerCase();
  if(/[\u3400-\u9fff\uac00-\ud7af\u3040-\u30ff]/.test(q))return [];   // CJK has no spaces to split on
  return q.replace(_Q_STOP,' ').replace(/[?¿!¡.,;:()"'“”]/g,' ').split(/\s+/)
    .filter(w=>w.length>=3&&/[a-zà-ÿ]/.test(w)&&!_CLOSEST_STOP.test(w));
}
function apply(){let v=0;
  // WCAG 2.4.4 / 4.1.3: capture the previous visible count so we can decide
  // whether to re-announce to the polite live region. Re-announcing on every
  // filter tweak would be noisy; only doing it when v genuinely changes is
  // both correct (the user actually sees a different map) and quiet.
  const prevVisible=lastVisible;
  const searching=!!searchTerm;
  const totalR=Object.keys(RI).length;
  // Search used to silently bypass the Area/Category filters — a "bank" search
  // while North Shore was selected quietly searched the whole city, which read as
  // the filter having stopped working rather than as intended behaviour. Search now
  // narrows within whatever is already filtered, the way typing into a filtered
  // spreadsheet does, so a filter chip stays true for as long as it's on screen.
  // 2026-09-10: 'open now' narrows the map like any other filter and is
  // counted as one — Reset, the empty state and the search note all read this.
  // categories do not narrow a search (see markerPasses)
  const filtered=aR.size<totalR||(aC.size>0&&!searching)||aT.size>0||openNow||nearOnly;
  const bounds=[];
  M.forEach(m=>{
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
      const cand=[];let bestAll=0,bestIn=0;
      M.forEach(m=>{
        let hit=0,sc=0;
        words.forEach(w=>{const x=matchScore1(m.data,w);if(x>=40){hit++;sc+=x;}});
        if(!hit)return;
        if(hit>bestAll)bestAll=hit;
        if(!markerPasses(m,1))return;              // the active filters still apply
        if(hit>bestIn)bestIn=hit;
        cand.push({m,hit,sc});
      });
      const floor=Math.max(1,Math.ceil(words.length/2));
      // a closer match exists outside the filters: say so (empty state), don't guess inside them
      if(bestIn<bestAll)cand.length=0;
      for(let need=words.length;need>=floor&&!v;need--){
        cand.forEach(c=>{if(c.hit>=need){c.m.score=c.sc;showMarker(c.m);v++;bounds.push([c.m.data.lat,c.m.data.lng]);}});
      }
      _closest=v>0;
    }
  }
  const u=UI[L_];
  const st=document.getElementById('statusText');
  if(searching){
    // 2026-10-20 (re-walk): above the 24-hour lines it said "No matching places found" — cold, and beside the point
    st.textContent=(v===0&&isCrisisQuery(searchRaw||searchTerm))?u.crisisStatus:_closest?u.searchClosestN(v):u.searchResultsN(v);
    st.dataset.count=st.textContent;st.dataset.region='';
    // 2026-09-13: fit (or focus) only when the search/filters actually changed.
    // The open-now minute tick, a tab coming back and a language switch all
    // re-run apply(); they used to throw the reader's zoomed-in view back to the
    // city and re-open a popup they had just closed. One result → focusMarker
    // alone (it zooms itself); fitBounds and focusMarker together let the popup
    // open at the old zoom and end up clipped above the map.
    const fitKey=searchTerm+'|'+[...aR].sort().join(',')+'||'+[...aT].sort().join(',')+'|'+(openNow?1:0)+'|'+(selectedRoute||'');
    if(fitKey!==_lastFitKey){
      _lastFitKey=fitKey;
      if(v===1){const only=M.find(m=>m.score>0&&_isShown(m));
        // jump (no animation) to street level first, then open — the popup then
        // auto-pans against the projection it will actually be shown in
        if(only){try{map.setView(only.getLatLng(),Math.max(map.getZoom(),16),{animate:false});}catch(e){}focusMarker(only);}}
      else if(v>0&&v<=40){map.fitBounds(bounds,{padding:[50,50],maxZoom:16});}
    }
  }else{
    _lastFitKey='';   // the next search fits again, even if it is the same term
    // On a short, narrow screen this line has to share a row with Reset, and the
    // count is the half worth keeping — which regions are on is already visible on
    // the Area button. The full sentence stays in the title attribute.
    // P2-G: "263 / 263" reads as a fraction with nothing to compare it to until a
    // reader already knows the total is 263 — which is exactly the thing this line
    // exists to tell them. Nothing filtered means nothing to divide, so it says the
    // total plainly instead; the v/t form is saved for once the two numbers differ.
    const countText=v===P.length?u.showingAll(P.length):u.showing(v,P.length);
    st.textContent=countText+(TIGHT.matches?'':' · '+regionLabel());
    st.dataset.count=countText;st.dataset.region=TIGHT.matches?'':regionLabel();
  }
  st.title=searching?st.textContent:((v===P.length?u.showingAll(P.length):u.showing(v,P.length))+' · '+regionLabel());
  st.dataset.base=st.textContent;
  updateStatusRoute();
  document.getElementById('applyBtn').textContent=u.doneBtn;
  lastVisible=v;
  updatePanelTitle();
  const totalC=Object.keys(CI).length;
  const areaBadge=document.getElementById('areaBadge');
  if(aR.size<totalR){areaBadge.hidden=false;areaBadge.textContent=aR.size;}else{areaBadge.hidden=true;}
  const catBadge=document.getElementById('catBadge');
  // One panel holds both axes, so its badge counts both — a badge of 1 with only
  // a theme on is what stops a theme filter from being invisible from outside.
  const catBadgeN=aC.size+aT.size;
  if(catBadgeN>0){catBadge.hidden=false;catBadge.textContent=catBadgeN;}else{catBadge.hidden=true;}
  const dims=(aR.size===totalR?0:1)+(aC.size>0?1:0)+(aT.size>0?1:0)+(openNow?1:0)+(nearOnly?1:0);
  // a preset whose every category has been unticked is no longer a preset
  if(aC.size===0&&selPresets.size){selPresets.clear();presetsAdjusted=false;}
  // P0-B: this used to unconditionally show Reset and only dim it (.idle) when
  // there was nothing to undo — a control that is always on screen implies there
  // is always something to press. updateResetState(), below, now decides real
  // visibility from the same state this dims from, so it is skipped here.
  // Area/Category and Quick Picks stay fully live while searching now, so nothing
  // dims them any more, and the active-filter chips stay visible too — they are
  // still true. The one thing worth saying is that a filter is narrowing the
  // search itself, since that's easy to miss if you set the filter a while ago.
  document.getElementById('searchNote').textContent=
    searching?[filtered?u.searchActive:'',aC.size?u.catsPausedNote:''].filter(Boolean).join(' · '):(searchRaw?u.searchTooShort:'');
  renderActiveFilters();
  updatePresetActive();
  try{updateRegionHulls();}catch(e){}
  lastDims=dims;
  if(dims>0||searching)dismissFirstUse('filter');
  // Polite live announcement only when the visible count actually moved. Tools
  // that listen (VoiceOver/NVDA) will queue and read this without barge-in, and
  // because the element is .sr-only it never affects sighted layout.
  if(v!==prevVisible&&(v===0||prevVisible===0||Math.abs(v-prevVisible)>=3)){
    const ann=document.getElementById('a11yAnnounce');
    if(ann)ann.textContent=u.aResultsAnnounce(v,P.length);
  }
  updateResetState();
  try{renderSeason();}catch(e){}   // the winter note steps aside while a search shows its places (2026-10-20)
  try{renderResultList(v,searching);}catch(e){}
  writeURLState();
  renderEmptyState(v,searching,filtered);
  try{renderSearchHelp();}catch(e){}
  // 2026-10-04 (newcomer tests): a card opened on the map itself (not on a marker — a clustered or
  // filtered place) is not closed when its marker leaves, so the last place's card stayed open through
  // later searches. Close it once a search or filter no longer includes its place.
  try{const op=map._popup;if(op&&op._kplace&&map.hasLayer(op)&&!(_focusPending&&_focusPending.data.id===op._kplace.id)){
    const mm=M.find(x=>x.data.id===op._kplace.id);if(mm&&!markerPasses(mm))map.closePopup(op);}}catch(e){}
}
// One honest explanation for each way the map can legitimately end up empty.
let lastVisible=0,lastDims=0;
// The count belongs in the title from the moment the panel opens, not only after the
// first change — so openPanel calls this too rather than writing its own title.
function updatePanelTitle(){
  if(!panel.classList.contains('open'))return;
  const u=UI[L_];
  const base=panelMode==='area'?u.regLabel:panelMode==='cat'?u.catLabel:
             panelMode==='bus'?u.busBtnLabel:u.favBtnLabel;
  const countText=lastVisible===P.length?u.showingAll(P.length):u.showing(lastVisible,P.length);
  document.getElementById('panelTitle').innerHTML=
    iconify(base)+((panelMode==='area'||panelMode==='cat')?' · '+esc(countText):'');
}
// P0-B: Reset is now genuinely absent — in the DOM's `hidden` sense, so assistive
// tech skips it too — the moment every axis is back at its default, rather than
// staying on screen in a dimmed .idle state implying there is still something to
// press. Drawing a bus route does not go through apply(), so renderRoute calls
// this too.
function updateResetState(){
  document.getElementById('resetBtn').hidden=(lastDims===0&&!searchTerm&&!selectedRoute);
}

// 2026-10-20 (launch review, phone and desktop): a search showed its places only as pins — some clustered, some under
// the winter note, none with a name until tapped. Up to six results are now listed by name and area under the
// answer box; a tap brings the map into view and opens that place's card. Not for crisis searches (the lines
// come first), and only when the search found something to list.
// four on a phone (the map is below the list there), six on a wider screen
const resultListMax=()=>window.matchMedia&&window.matchMedia('(max-width:600px)').matches?4:6;
function renderResultList(v,searching){
  const el=document.getElementById('resultList');if(!el)return;
  const q=searchRaw||searchTerm;
  // a health question is answered by the box above it (who is open now, 8-1-1, 911); a list of every place in the
  // health category under it repeated that, less well — "doctor" listed the hospice (launch review, 2026-10-20)
  if(!searching||!v||v>30||isCrisisQuery(q)||_isHealthQuery(q)){el.hidden=true;el.innerHTML='';return;}
  const u=UI[L_];
  const shown=M.filter(m=>_isShown(m)).sort((a,b)=>(b.score||0)-(a.score||0));
  const top=shown.slice(0,resultListMax());
  // the area's short name: "Sahali/Aberdeen", not its whole description
  const shortArea=g=>regLabel(g).split(/ \(|（/)[0];
  el.innerHTML=top.map((m,i)=>'<button type="button" class="rl-item" data-i="'+i+'"><b>'+esc(m.data.n)+'</b>'
      +(m.data.g?'<span class="rl-area">'+esc(shortArea(m.data.g))+'</span>':'')+'</button>').join('')
    +(shown.length>top.length?'<span class="rl-more">'+esc(u.resultMore(shown.length-top.length))+'</span>':'');
  el.hidden=false;
  el.querySelectorAll('.rl-item').forEach(b=>b.onclick=()=>{
    const m=top[+b.dataset.i];if(!m)return;
    const mapEl=document.getElementById('map');
    try{mapEl.scrollIntoView({block:'center',behavior:'smooth'});}catch(e){mapEl.scrollIntoView();}
    focusMarker(m,16);
  });
}
