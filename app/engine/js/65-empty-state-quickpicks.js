// Which empty-state reason was last reported, so the event fires on the way in
// rather than once per keystroke. null means "the map currently has results".
let _lastEmptyKind=null;
// The lines that answer at 3 a.m. Built once, shown wherever a reader may be
// standing when everything else is closed: the open-now empty state, the top of
// the guide's "when you need help" bucket, and the first-use card.
function localCrisisHtml(){
  const line=c=>'<p class="help-local">'+esc(c.note[L_]||c.note.en)+' <a href="tel:'+esc(c.n.replace(/[^\d]/g,''))+'"><b>'+esc(c.n)+'</b></a></p>';
  return (CITY.localLines||[]).map(line).join('')+(CITY.localCrisis?line(CITY.localCrisis):'');
}
function hotlineHtml(compact){
  const u=UI[L_];
  const items=(CITY.hotlines||[]).map(h=>'<a class="hl-line" href="tel:'+esc(h.n.replace(/[^\d]/g,''))+'"><b>'+esc(h.n)+'</b> '+esc(u['hot_'+h.t]||h.t)+'</a>');
  return '<div class="hotlines'+(compact?' compact':'')+'"><span class="hl-lead">'+iconify(u.hotlinesLead)+'</span>'+items.join('')+'</div>';
}
// closest known word for a one-word Latin query that found nothing: synonyms, category names, and the words
// of place names and aliases; spaces ignored ("foodbank" → "food bank"); 1 edit for 4–5 letters, 2 for longer
let _dymVocab=null;
function _editDist(a,b){if(Math.abs(a.length-b.length)>2)return 9;const d=[];for(let i=0;i<=a.length;i++){d[i]=[i];}
  for(let j=1;j<=b.length;j++)d[0][j]=j;
  for(let i=1;i<=a.length;i++)for(let j=1;j<=b.length;j++){d[i][j]=Math.min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+(a[i-1]===b[j-1]?0:1));
    if(i>1&&j>1&&a[i-1]===b[j-2]&&a[i-2]===b[j-1])d[i][j]=Math.min(d[i][j],d[i-2][j-2]+1);}
  return d[a.length][b.length];}
function _didYouMean(q){
  q=String(q||'').toLowerCase().trim();
  if(!/^[a-z][a-z' -]{3,}$/.test(q)||q.split(/\s+/).length>2)return null;
  if(!_dymVocab){
    const v=new Set();
    _SYN_IDX.forEach((cs,t)=>{if(/^[a-z][a-z' -]{3,}$/.test(t))v.add(t);});
    Object.keys(CI).forEach(c=>{const l=catLabel(c).toLowerCase();if(/^[a-z][a-z' &-]{3,}$/.test(l))v.add(l.replace(/ & .*$/,''));});
    P.forEach(p=>[p.n].concat(p.alias||[]).forEach(s=>String(s).toLowerCase().split(/[^a-z']+/).forEach(w=>{if(w.length>=4)v.add(w);})));
    _dymVocab=[...v];
  }
  const qs=q.replace(/[\s-]/g,''),lim=qs.length>=6?2:1;
  let best=null,bd=9;
  _dymVocab.forEach(w=>{const ws=w.replace(/[\s-]/g,'');if(ws===qs&&w!==q){if(bd>0||w.length<best.length){best=w;bd=0;}return;}
    const d=_editDist(qs,ws);if(d<=lim&&(d<bd||(d===bd&&w.length<(best||'').length))){best=w;bd=d;}});
  return best&&best!==q?best:null;
}
function crisisHtml(){
  const u=UI[L_];
  return '<div class="crisis-block"><p class="crisis-lead">'+esc(u.crisisLead)+'</p>'+hotlineHtml(false)+localCrisisHtml()
    +'<p class="crisis-more">'+esc(u.crisisMore)+'</p></div>';
}
function renderEmptyState(v,searching,filtered){
  const el=document.getElementById('emptyState'),u=UI[L_];
  const crisis=searching&&isCrisisQuery(searchRaw||searchTerm);
  // 2026-10-04: a health question with no place matching its words ("找医生") is answered by the health box
  // above; "no matching places — check the spelling" under it contradicted that answer.
  if(v===0&&searching&&!crisis&&!filtered&&_isHealthQuery(searchRaw||searchTerm)){
    _lastEmptyKind=null;el.hidden=true;el.innerHTML='';el.dataset.kind='';return;
  }
  if(v>0){
    _lastEmptyKind=null;
    if(crisis){el.hidden=false;el.dataset.kind='crisis';el.innerHTML=crisisHtml();}
    else{el.hidden=true;el.innerHTML='';}
    return;
  }
  el.hidden=false;
  let msg,label,act;
  const clearFiltersAct=()=>{aR=new Set(Object.keys(RI));aC.clear();aT.clear();selPresets.clear();presetsAdjusted=false;openNow=false;updateOpenQuickpick();nearOnly=false;updateNearQuickpick();renderRegs();renderCats();renderThemes();if(selectedRoute)renderRoute(null,false);apply();};
  const onlyOpen=openNow&&(aC.size===0||searching)&&aT.size===0&&aR.size===Object.keys(RI).length;
  if(searching&&onlyOpen){
    // "library" + open now at 9 pm: the libraries exist, they are closed. Say
    // that, and offer to show their hours — never "check the spelling".
    msg=u.noResultOpenNow.replace('{Q}',esc(searchRaw||searchTerm));label=u.emptyOpenSearchBtn;act=()=>{openNow=false;updateOpenQuickpick();apply();};
  }else if(searching&&filtered){
    // Combining a search with an active area/category filter can legitimately find
    // nothing (a "bank" search while only a bankless area is selected) — the honest
    // fix offers to drop the filter, not to imply the search itself came up empty.
    msg=u.noResultFiltered;label=u.emptyFiltersBtn;act=clearFiltersAct;
  }else if(searching&&!crisis&&_didYouMean(searchRaw||searchTerm)){
    // 2026-10-04 (newcomer test): "foodbank", "libary", "docter" ended at "check the spelling" with only a
    // Clear button. One word, one or two letters off a word the map knows: offer that word.
    const w=_didYouMean(searchRaw||searchTerm);
    msg=u.dymMsg.replace('{Q}',esc(searchRaw||searchTerm)).replace('{W}',esc(w));label=u.dymBtn.replace('{W}',w);
    act=()=>{searchInputEl.value=w;clearTimeout(searchTimer);runSearch();};
  }else if(searching){
    msg=u.noResultHint;label=u.clearSearchBtn;act=()=>{searchInputEl.value='';clearTimeout(searchTimer);runSearch();};
  }else if(onlyOpen){
    // Nothing is open. Say so — and, since the person asking at this hour may
    // be in trouble, show the lines that answer anyway. Never a bare zero.
    msg=isHolidayToday()?u.holidayOpenNote:u.emptyOpenNow;label=u.emptyOpenBtn;act=()=>{openNow=false;updateOpenQuickpick();apply();};
  }else{
    msg=u.emptyFilters;label=u.emptyFiltersBtn;act=clearFiltersAct;
  }
  // The hotline block belongs to "nothing in the city is open" — not to a
  // closed library. The chip row already carries it while open-now is on.
  el.innerHTML=(crisis?crisisHtml():'')+'<p>'+msg+'</p>'+(selectedRoute?'<p class="empty-route">'+esc(u.emptyRouteNote)+'</p>':'')+(onlyOpen&&!searching?hotlineHtml(false):'');
  const btn=document.createElement('button');btn.className='empty-btn';btn.textContent=label;
  // 2026-09-08 audit: this button is the app's clearest "I hit a dead end and
  // tried to get out of it" signal, and it recorded nothing — so the one moment
  // worth knowing about was invisible in the data. The `kind` distinguishes the
  // three honest ways to arrive here, which is what makes the row actionable.
  const kind=searching&&onlyOpen?'search_open_now':searching&&filtered?'search_and_filters':searching?'search':onlyOpen?'open_now':'filters';
  el.dataset.kind=kind;
  // apply() runs this on every keystroke and every filter tap, so fire only on
  // the transition into an empty result (or when the reason for it changes) —
  // otherwise one fruitless search would bill a dozen identical rows.
  if(_lastEmptyKind!==kind){
    _lastEmptyKind=kind;
    trackEvent('empty_state_shown',{kind:kind,cats:aC.size,themes:aT.size,
      areas:aR.size<Object.keys(RI).length,route:!!selectedRoute});
  }
  btn.onclick=()=>{trackEvent('empty_state_recover',{kind:kind});act();};el.appendChild(btn);
  // "health card", 医疗卡, 학교 등록: the reader asked the map a guide question.
  // 2026-09-22: the card now LEADS the empty state instead of trailing it as a
  // small second button — the one visitor who hit this tapped past it.
  if(searching){
    const hit=_taskForQuery();
    // a card never goes above the 24-hour lines ("safe place" once led with the rental-scam card, 2026-10-04): after them
    if(hit&&!_isHealthQuery(searchRaw||searchTerm)){const c=_taskCardEl(hit,'search_empty');if(crisis)el.appendChild(c);else el.insertBefore(c,el.firstChild);}
  }
}
// 2026-09-24: strongest match first. (1) a card with this exact alias; (2) the
// query in a card's own text, starting at a word boundary; (3) only then the loose
// rule that finds an alias inside a longer phrase — and never for a query that is
// itself a kind of place or a place's own alias ("食物银行" is a food bank, not a
// bank; "동물병원" is a vet, not a clinic). A lone generic word suggests nothing.
const _TASK_GENERIC=new Set(['free','help','card','cheap','info','service','services','centre','center','office','support',
  'gratuit','gratuite','gratis','aide','ayuda','免费','免費','帮助','幫助','무료','도움','無料','助け']);
function _isPlaceWord(q){
  if(synCats(q).size)return true;
  const lq=q.toLowerCase();
  return P.some(p=>(p.alias||[]).some(a=>String(a).toLowerCase()===lq));
}
function _taskForQuery(){
  const q=(searchRaw||searchTerm||'').trim();
  if(q.length<2)return null;
  const lq=q.toLowerCase();
  if(_TASK_GENERIC.has(lq))return null;
  const exact=TASKS.find(t=>(t.alias||[]).some(a=>String(a).toLowerCase()===lq));
  if(exact)return exact;
  // a card's own question or title, typed as is (2026-10-04: "No tengo médico de familia" suggested the sick card,
  // whose title contains it, once the translations used the same term for family doctor)
  const own=TASKS.find(t=>[t.q,t.t].some(x=>x&&String(taskText(x)).toLowerCase()===lq));
  if(own)return own;
  const strong=TASKS.find(t=>taskMatchesLoose(t,q,true));
  if(strong)return strong;
  return _isPlaceWord(q)?null:(TASKS.find(t=>taskMatchesLoose(t,q))||null);
}
function _firstSentence(s){s=String(s||'');const m=s.match(/^.+?[.!?。！？](\s|$)/);return (m?m[0]:s).trim();}
function _taskCardEl(t,src){
  const u=UI[L_],box=document.createElement('div');box.className='sh-card';
  box.innerHTML='<p class="sh-lead">'+esc(u.shCardLead)+'</p><p class="sh-card-t">'+emojiIcon(t.icon)+esc(taskText(t.t))+'</p>'
    +'<p class="sh-card-why">'+esc(_firstSentence(taskText(t.why)))+'</p>';
  const b=document.createElement('button');b.type='button';b.className='sh-btn primary';b.textContent=u.shOpenCard;
  b.onclick=()=>openGuide(src,t.id);   // openGuide records guide_open itself
  box.appendChild(b);return box;
}
// ---- 2026-09-22: the answer box under the search bar ------------------------
// 2026-10-04: + common misspellings (docter, doctr, clinc, clinik) — the newcomer test's "docter" got nothing
const _HEALTH_RE=/doct[eo]?r|dokter|clini?[ck]|clinc|walk.?in\b|sick|urgent|nurs[e](?!ry)|\bgp\b|\ber\b|physician|medical|fever|médecin|clinique|malade|urgence|infirmi|médico|clínica|enfermo|urgencia|enfermer|医生|看病|诊所|診所|急诊|急診|生病|发烧|發燒|门诊|門診|醫生|의사|병원|진료|아파(?!트)|응급|医者|病院|診療|受診|病気|発熱/i;
const _NOT_HEALTH_RE=/\bdent|\bvet\b|veterin|animal|\bpets?\b|legal|lawyer|\blaw\b|牙|兽医|獸醫|宠物|寵物|法律|치과|동물|수의|歯|動物|獣医|\beyes?\b|optom|glasses|lunettes|gafas|眼科|眼镜|眼鏡|안과|안경|目医者|insurance|seguro|assurance|保险|保險|보험|保険/i;
function _isHealthQuery(q){q=String(q||'');return _HEALTH_RE.test(q)&&!_NOT_HEALTH_RE.test(q);}
// 2026-10-04: the city's urgent and primary care centres come from CITY.upcc (place ids). This used
// to be one Kamloops id written here, so in any other city the whole health answer silently vanished.
function _upccs(){return (CITY.upcc||[]).map(id=>P.find(p=>p.id===id)).filter(Boolean);}
function renderSearchHelp(){
  const el=document.getElementById('searchHelp');if(!el)return;
  const q=(searchRaw||searchTerm||'').trim(),u=UI[L_];
  if(!searchTerm||isCrisisQuery(q)){el.hidden=true;el.innerHTML='';el.dataset.kind='';return;}
  const health=_isHealthQuery(q),ups=_upccs();
  const exactCard=!health&&!_closest&&_exactN>0?_exactTaskForQuery():null;   // with no places, the empty state already shows it
  if(exactCard){el.innerHTML='';el.hidden=false;el.dataset.kind='task';el.appendChild(_taskCardEl(exactCard,'search_alias'));return;}
  if(!health&&!_closest){el.hidden=true;el.innerHTML='';el.dataset.kind='';return;}
  el.innerHTML='';el.hidden=false;
  if(_closest){const n=document.createElement('p');n.className='sh-note';n.textContent=u.searchClosestNote(q,lastVisible);el.appendChild(n);}
  if(health){
    el.dataset.kind='health';
    const stOf=p=>{const st=openState(p.h);return st?('<span class="sh-status'+(st.open?' open':'')+'">'+esc(st.open?u.hcOpenNow:u.hcClosedNow)+'</span> · '):'';};
    // one centre: the line reads as before; several: each centre by name, with its own status and hours
    const upccLi=!ups.length?'':'<li>'+esc(u.hcUpcc)+(ups.length===1
      ?'<br>'+stOf(ups[0])+esc(u.hcHours)+u.colon+esc(fmtHours(ups[0].h,L_))
      :ups.map(p=>'<br><b>'+esc(p.n)+'</b> · '+esc(p.a)+'<br>'+stOf(p)+esc(u.hcHours)+u.colon+esc(fmtHours(p.h,L_))).join(''))+'</li>';
    const box=document.createElement('div');
    // at night every centre can be closed: say where to go instead of pointing at a closed door
    const anyOpen=ups.some(p=>{const st=openState(p.h);return st&&st.open;});
    box.innerHTML='<p class="sh-title">'+esc(u.hcTitle)+'</p><ul class="sh-list">'
      +(ups.length&&!anyOpen?'<li><b>'+phoneHtml(esc(u.hcNight))+'</b></li>':'')
      +upccLi
      +'<li>'+phoneHtml(esc(u.hc811))+'</li><li>'+esc(u.hcPharm)+'</li><li>'+esc(u.hc911).replace(/\b911\b/,'<a href="tel:911">911</a>')+'</li></ul>';
    const btns=document.createElement('div');btns.className='sh-btns';
    // the map button goes to a centre that is open now when there is one
    const target=ups.find(p=>{const st=openState(p.h);return st&&st.open;})||ups[0];
    if(target){
      const b1=document.createElement('button');b1.type='button';b1.className='sh-btn primary';b1.textContent=u.hcShowUpcc;
      b1.onclick=()=>{const m=M.find(x=>x.data.id===target.id);if(m){trackEvent('search_help_click',{kind:'upcc'});focusMarker(m,16);}};
      btns.appendChild(b1);
    }
    const sick=TASKS.find(t=>t.id==='sick');
    if(sick){const b2=document.createElement('button');b2.type='button';b2.className='sh-btn';b2.textContent=u.emptyGuideHint.replace('{T}',taskText(sick.t));
      b2.onclick=()=>openGuide('search_help','sick');btns.appendChild(b2);}
    box.appendChild(btns);el.appendChild(box);
  }else{
    el.dataset.kind='closest';
    const hit=_taskForQuery();
    if(hit)el.appendChild(_taskCardEl(hit,'search_closest'));
  }
}
// 2026-10-04 (newcomer test): "SIN", "bank account" found places (a clinic whose Spanish alias contains "sin")
// and never the card that answers the question. A query that IS one of a card's aliases gets that card above
// the results, whatever the map finds.
function _exactTaskForQuery(){
  const lq=(searchRaw||searchTerm||'').trim().toLowerCase();
  if(lq.length<2||_TASK_GENERIC.has(lq))return null;
  return TASKS.find(t=>(t.alias||[]).some(a=>String(a).toLowerCase()===lq))||null;
}
const PRESETS={
  daily:['grocery','asian','hospital','pharmacy','bank','transit','gas','laundry','post','conv'],
  // 2026-10-03: + library — free Wi-Fi, computers, printing and English conversation circles are
  // used by almost everyone who has just arrived (child care stays under Kids: 100+ centres would
  // bury what a single person or a student needs).
  newcomer:['gov','foodbank','bank','post','secondhand','apt','propmgmt','hardware','transit','schoolbus','hospital','asian','driving','religious','commctr','legal','library'],
  kids:['park','splash','pool','library','museum','cinema','rink','beach','elem','school','schoolbus','daycare','playcenter','tutor'],
  sports:['gym','pool','rink','park','trail','beach','dogpark'],
  edu:['school','elem','schoolbus','library','tutor'],
  health:['hospital','dental','pharmacy','vet'],
  outdoor:['park','trail','beach','dogpark','splash'],
  shopping:['grocery','asian','mall','secondhand','hardware','conv','gas'],
  auto:['taxi','driving','usedcar','autorepair','gas']
};
function setEq(setA,arr){if(setA.size!==arr.length)return false;return arr.every(x=>setA.has(x));}
function updatePresetActive(){
  Object.keys(PRESETS).forEach(key=>{
    const el=document.getElementById(key);
    if(!el)return;
    el.classList.toggle('active',selPresets.has(key));
    el.setAttribute('aria-pressed',selPresets.has(key)?'true':'false');
    el.classList.toggle('adjusted',selPresets.has(key)&&presetsAdjusted);
    el.title=(selPresets.has(key)&&presetsAdjusted)?UI[L_].presetAdjusted:'';
    if(selPresets.has(key)&&presetsAdjusted)el.dataset.adjLabel=' '+UI[L_].presetAdjustedShort;
    else delete el.dataset.adjLabel;
  });
}
const qpRowEl=document.getElementById('qpRow'),presetRowEl=document.getElementById('presetRow');
// Only 3 of 9 Quick Picks chips fit on a narrow phone, and the row has no
// scrollbar (deliberately, for a cleaner look), so nothing on screen said "there
// are six more chips to the right." Toggle the fade+chevron in CSS purely from
// actual overflow, so it appears exactly while scrolling right would reveal more,
// and disappears at the end instead of hanging there uselessly.
function updateQpFade(){
  if(!qpRowEl||!presetRowEl)return;
  const hasMore=presetRowEl.scrollWidth-presetRowEl.scrollLeft-presetRowEl.clientWidth>4;
  qpRowEl.classList.toggle('has-more',hasMore);
}
if(presetRowEl){
  presetRowEl.addEventListener('scroll',updateQpFade,{passive:true});
  window.addEventListener('resize',updateQpFade);
}
// P2-I — see the HTML comment above #qpFree/#qpFamily/#qpIndoor. Each button
// just toggles one theme, exactly like a chip in the Category panel's theme
// section would; renderThemes() already runs after every path that can change
// aT, so calling updateThemeQuickpicks() from inside it keeps these in sync
// without a second set of call sites to remember.
const THEME_QUICKPICKS=['free','family','indoor'];
function tqpId(k){return 'qp'+k.charAt(0).toUpperCase()+k.slice(1);}
THEME_QUICKPICKS.forEach(k=>{
  const el=document.getElementById(tqpId(k));
  if(!el)return;
  el.onclick=()=>{
    const had=aT.has(k);
    if(had)aT.delete(k);else aT.add(k);
    trackEvent('theme_toggle',{id:k,action:had?'remove':'add',active:aT.size,src:'quickpick'});
    renderThemes();renderCats();apply();
  };
});
function updateOpenQuickpick(){
  const el=document.getElementById('qpOpen');
  if(!el)return;
  el.innerHTML=ico('clock')+esc(UI[L_].openNowLabel);
  el.classList.toggle('active',openNow);
  el.setAttribute('aria-pressed',openNow?'true':'false');
}
function updateNearQuickpick(){
  const el=document.getElementById('qpNear');
  if(!el)return;
  el.innerHTML=ico('walk')+esc(UI[L_].nearLabel);
  el.classList.toggle('active',nearOnly);
  el.setAttribute('aria-pressed',nearOnly?'true':'false');
}
document.getElementById('qpNear').onclick=()=>{
  const u=UI[L_];
  if(!userPos){showToast(u.nearNeedsLocation,{ms:4500});trackEvent('near_toggle',{action:'no_location'});return;}
  nearOnly=!nearOnly;
  trackEvent('near_toggle',{action:nearOnly?'on':'off'});
  updateNearQuickpick();apply();
  if(nearOnly){try{map.setView(userPos,15);}catch(e){}}
};
function updateThemeQuickpicks(){
  updateOpenQuickpick();updateNearQuickpick();
  THEME_QUICKPICKS.forEach(k=>{
    const el=document.getElementById(tqpId(k));
    if(!el)return;
    el.innerHTML=emojiIcon(TIC[k])+esc(themeLabel(k));
    el.classList.toggle('active',aT.has(k));
    el.setAttribute('aria-pressed',aT.has(k)?'true':'false');
  });
  // "Indoor / Winter" is off the row outside winter unless it is switched on
  if(_qpClock)applyQuickPickOrder();
}
// 2026-09-11 — Quick Picks in context. A phone shows three chips; make them the
// three this reader is likeliest to want *now*. Pure function of a context
// object so the rules can be tested without faking the clock:
//   evening (17:00+) or Sunday  → "Open now" right after the guide
//   Saturday / Sunday           → "Kids & Family" moves up
//   November–March              → "Indoor / Winter" appears (hidden otherwise;
//                                  it stays in the Category sheet all year)
//   arrived from a flyer/card   → "Resident Essentials" (the newcomer set) first
//   third visit or later        → the newcomer set drops behind the themes
// The guide is always first, "More" always last, and rules never hide a chip
// the reader has already switched on.
const _VISITS_KEY=SP+'Visits';
function visitCount(){try{return parseInt(localStorage.getItem(_VISITS_KEY)||'0',10)||0;}catch(e){return 0;}}
function bumpVisitCount(){try{localStorage.setItem(_VISITS_KEY,String(Math.min(visitCount()+1,999)));}catch(e){}}
// read before writeURLState() ever rewrites the address bar (urlWriteBlocked
// is still true here), so the flyer tag survives the rewrite
const LANDED_SRC=(function(){try{const v=new URLSearchParams(location.search).get('src')||'';return /^[a-z0-9-]{1,24}$/.test(v)?v:'';}catch(e){return '';}})();
// The clock part of the context is frozen per sitting (refreshed when the tab
// comes back into view), so the row never reorders under a thumb at 17:00.
let _qpClock=null;
function quickPickContext(fresh){
  if(fresh||!_qpClock){const now=cityNow();_qpClock={h:Math.floor(now.m/60),d:now.d,mo:cityMonth()};}
  return {h:_qpClock.h,d:_qpClock.d,mo:_qpClock.mo,src:LANDED_SRC,visits:visitCount(),on:{indoor:aT.has('indoor'),near:!!userPos}};
}
function quickPickOrder(ctx){
  const r={daily:10,newcomer:20,qpFree:30,qpFamily:40,qpIndoor:Infinity,qpOpen:50,qpNear:Infinity};
  if(ctx.on&&ctx.on.near)r.qpNear=2;   // located: "15-min walk" sits right after the guide
  const winter=ctx.mo>=11||ctx.mo<=3,weekend=ctx.d>=6,evening=ctx.h>=17||ctx.d===7;
  if(winter||(ctx.on&&ctx.on.indoor))r.qpIndoor=25;
  if(/^(flyer|card)/.test(ctx.src||''))r.newcomer=5;
  else if(ctx.visits>=3)r.newcomer=45;
  if(weekend)r.qpFamily=15;
  if(evening)r.qpOpen=1;
  const ids=Object.keys(r).filter(k=>r[k]!==Infinity).sort((a,b)=>r[a]-r[b]);
  return ['qpGuide'].concat(ids,['qpMore']);
}
function applyQuickPickOrder(fresh){
  const row=document.getElementById('presetRow');if(!row)return;
  const order=quickPickOrder(quickPickContext(fresh));
  const all=['qpGuide','daily','newcomer','qpFree','qpFamily','qpIndoor','qpOpen','qpNear','qpMore'];
  all.forEach(id=>{const el=document.getElementById(id);if(el)el.hidden=order.indexOf(id)<0;});
  const cur=Array.prototype.filter.call(row.children,c=>!c.hidden).map(c=>c.id);
  const same=cur.length===order.length&&cur.every((id,i)=>id===order[i]);
  if(!same)order.forEach(id=>{const el=document.getElementById(id);if(el)row.appendChild(el);});
  requestAnimationFrame(updateQpFade);
}
(function(){
  const el=document.getElementById('qpMore');
  if(el)el.onclick=()=>{trackEvent('qp_more',{});openPanel('cat');};
})();
function renderActiveFilters(){
  const root=document.getElementById('activeFilters');root.innerHTML='';
  const u=UI[L_];
  const totalR=Object.keys(RI).length,totalC=Object.keys(CI).length;
  if(aR.size===totalR&&aC.size===0&&aT.size===0&&!openNow&&!selectedRoute&&!nearOnly)return;
  // The route is a filter-like state: it changes what the map shows and Reset
  // undoes it, so it gets a chip here like everything else it sits beside.
  if(selectedRoute&&owns(BR,selectedRoute)){
    const chip=document.createElement('div');chip.className='af-chip af-route';
    chip.innerHTML='<span>'+ico('bus')+u.routeLabel(selectedRoute)+'</span><button class="x" data-kind="route" data-k="'+esc(selectedRoute)+'" aria-label="'+esc(u.routeExit)+'">✕</button>';
    chip.querySelector('.x').onclick=()=>selectRoute(null);
    root.appendChild(chip);
  }
  if(aR.size<totalR){
    [...aR].forEach(k=>{
      const chip=document.createElement('div');chip.className='af-chip';
      // data-kind/data-k feed the delegated tracker above; without them the chip
      // "×" was the one filter control in the app that recorded nothing.
      chip.innerHTML='<span>📍 '+RI[k][L_]+'</span><button class="x" data-kind="region" data-k="'+k+'" aria-label="'+u.aClose+'">✕</button>';
      chip.querySelector('.x').onclick=()=>{aR.delete(k);if(aR.size===0)aR=new Set(Object.keys(RI));renderRegs();renderCats();renderThemes();apply();};
      root.appendChild(chip);
    });
  }
  // Themes get one chip each rather than a count: there are at most ten of them,
  // they read as words, and dropping one without losing the rest is the common
  // correction ("free AND indoor" was too narrow — drop indoor).
  [...aT].forEach(k=>{
    const chip=document.createElement('div');chip.className='af-chip';
    chip.innerHTML='<span>'+TIC[k]+' '+themeLabel(k)+'</span><button class="x" data-kind="theme" data-k="'+k+'" aria-label="'+u.aClose+'">✕</button>';
    chip.querySelector('.x').onclick=()=>{aT.delete(k);trackEvent('theme_toggle',{id:k,action:'remove_chip',active:aT.size});renderThemes();renderCats();apply();};
    root.appendChild(chip);
  });
  if(openNow){
    const chip=document.createElement('div');chip.className='af-chip';
    chip.innerHTML='<span>🕒 '+u.openNowLabel+'</span><button class="x" data-kind="open" data-k="now" aria-label="'+u.aClose+'">✕</button>';
    chip.querySelector('.x').onclick=()=>{openNow=false;updateOpenQuickpick();apply();};
    root.appendChild(chip);
  }
  if(nearOnly){
    const chip=document.createElement('div');chip.className='af-chip';
    chip.innerHTML='<span>🚶 '+u.nearLabel+'</span><button class="x" data-kind="near" data-k="now" aria-label="'+u.aClose+'">✕</button>';
    chip.querySelector('.x').onclick=()=>{nearOnly=false;updateNearQuickpick();apply();};
    root.appendChild(chip);
  }
  // 2026-09-24: the 24-hour lines used to ride along here whenever "open now"
  // was on — a row of crisis lines under a search for an open pharmacy at 2 pm.
  // They stay where they answer a real need: the Help button, a crisis search,
  // and the empty state when nothing at all is open. On a statutory holiday the
  // row still says listed hours may not hold.
  if(openNow&&isHolidayToday()){
    const hn=document.createElement('div');hn.className='af-note';
    hn.innerHTML='<p class="af-holiday">'+esc(u.holidayChipNote)+'</p>';
    root.appendChild(hn);
  }
  if(aC.size>0){
    const chip=document.createElement('div');chip.className='af-chip'+(searchTerm?' af-paused':'');
    chip.innerHTML='<span>🏷️ '+u.catsSelected(aC.size)+(searchTerm?' · '+esc(u.catsPausedShort):'')+'</span><button class="x" data-kind="cat" data-k="all" aria-label="'+u.aClose+'">✕</button>';
    chip.querySelector('.x').onclick=clearCatFilter;
    root.appendChild(chip);
  }
  // "Clear all" only when there are two or more things to clear (the hotline
  // strip is not a chip), and it clears the route too — a bar that empties
  // while the map stays greyed-out was the most-reported confusion in testing.
  if(root.querySelectorAll('.af-chip').length>1){
    const clear=document.createElement('button');clear.className='af-clear';clear.textContent=u.clearAll;
    clear.onclick=()=>{const snap=filterSnapshot();aR=new Set(Object.keys(RI));aC.clear();aT.clear();selPresets.clear();presetsAdjusted=false;openNow=false;updateOpenQuickpick();renderRegs();renderCats();renderThemes();if(selectedRoute)renderRoute(null,false);apply();
      showToast(u.clearedAll,{action:u.undo,onAction:()=>restoreSnapshot(snap)});};
    root.appendChild(clear);
  }
}

// header-links buttons/links are all "{emoji} {label}" strings. Splitting them into
// an icon span and a text span lets narrow phones drop just the text (CSS hides
// .hl-tx) and keep the row to one line, without losing the accessible name — that
// stays on the element itself via aria-label regardless of which part is visible.

function stripEmoji(str){for(let i=0;i<_EMOJI_KEYS.length;i++){const k=_EMOJI_KEYS[i];if(str.indexOf(k)===0)return str.slice(k.length).replace(/^\s+/,'');}return str;}
function setHL(id,label){
  const el=document.getElementById(id),sp=label.indexOf(' ');
  const em=sp>-1?label.slice(0,sp):label;
  el.querySelector('.hl-ic').innerHTML=emojiIcon(em);
  el.querySelector('.hl-tx').textContent=sp>-1?label.slice(sp+1):'';
  el.setAttribute('aria-label',stripEmoji(label));   // a screen reader says the words, not the pictogram
}
