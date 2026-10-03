// Swipe-down to dismiss, on the handle or the header. Same physics as the
// filter sheet: past a third of the sheet, or a quick flick, and it goes.
function attachSheetDrag(back,modal){
  const grab=modal.querySelector('.sheet-grab'),head=modal.querySelector('.guide-head');
  if(!grab)return;
  let startY=0,startT=0,dy=0,dragging=false,pid=null;
  const end=(close)=>{
    if(!dragging)return;
    dragging=false;
    modal.classList.remove('dragging');
    if(close){modal.style.transform='';closeModal(back);return;}
    modal.classList.add('settling');
    modal.style.transform='';
    setTimeout(()=>modal.classList.remove('settling'),220);
  };
  const down=e=>{
    if(window.innerWidth>900||e.button)return;
    if(e.target.closest&&e.target.closest('button,a,input'))return;
    dragging=true;startY=e.clientY;startT=e.timeStamp;dy=0;pid=e.pointerId;
    modal.classList.add('dragging');
    try{e.currentTarget.setPointerCapture(e.pointerId);}catch(err){}
  };
  const move=e=>{if(!dragging||e.pointerId!==pid)return;dy=Math.max(0,e.clientY-startY);modal.style.transform='translateY('+dy+'px)';};
  const up=e=>{if(!dragging||e.pointerId!==pid)return;const dt=Math.max(1,e.timeStamp-startT);
    end(dy>modal.offsetHeight/3||(dy>24&&dy/dt>0.6));};
  [grab,head].forEach(el=>{if(!el)return;
    el.addEventListener('pointerdown',down);el.addEventListener('pointermove',move);
    el.addEventListener('pointerup',up);el.addEventListener('pointercancel',()=>end(false));});
}
function openModal(back,opts){
  // Idempotent: a second open (a ?task= link racing a header tap) used to
  // count the scroll lock twice and leave the page frozen after one close.
  if(back.classList.contains('open'))return;
  const noHistory=!!(opts&&opts.noHistory);
  lastFocused=document.activeElement;
  back.classList.add('open');
  back.setAttribute('role','dialog');
  back.setAttribute('aria-modal','true');
  // name the dialog by its own title so a screen reader says what opened
  const ttl=back.querySelector('.panel-title');
  if(ttl&&ttl.id)back.setAttribute('aria-labelledby',ttl.id);
  lockBodyScroll();
  // 2026-09-13: a card opened straight from a link (a flyer's QR, a shared
  // card) *is* the page the reader arrived at; Back should leave, not peel
  // three layers. No history entry is pushed for that opening.
  if(!noHistory)pushSheetState(back.id);
  back._openedAt=Date.now();
  const first=back.querySelector('.panel-close');
  if(first)first.focus();
}
// 2026-09-13 audit: a double tap on the header's guide/share button — the
// second tap landing 80-250ms later on the dimmed backdrop that had just slid
// in over the button — opened the sheet and shut it again. A backdrop tap
// inside the first 400ms is that second tap, not a decision to leave.
function justOpened(back){return !!(back._openedAt&&Date.now()-back._openedAt<400);}
function closeModal(back,fromPop){
  // Hooked here, not on the ✕ button: Escape and a tap on the dimmed backdrop
  // are how most people actually leave a modal, and each of those used to exit
  // without recording anything.
  if(back===guideBackdropEl)trackGuideClose();
  if(!back.classList.contains('open'))return;
  back.classList.remove('open');
  // the next opening starts from the list (openGuide already renders it), so the
  // card is no longer "open" — otherwise the next door-opened card would skip
  // its history entry and Back would close the whole guide
  if(back===guideBackdropEl){_taskOpen=null;try{writeURLState();}catch(e){}}
  back.removeAttribute('role');back.removeAttribute('aria-modal');
  const m=back.querySelector('.guide-modal');if(m){m.style.transform='';m.classList.remove('dragging','settling');}
  if(!fromPop)popSheetState(back.id);
  unlockBodyScroll();
  // The opener may have gone (the first-use card hides itself); fall back to
  // the guide button so focus never lands on <body>.
  const lf=lastFocused;
  lastFocused=null;
  if(lf&&lf.focus&&lf.isConnected&&lf.offsetParent!==null){lf.focus();return;}
  const gt=document.getElementById('guideToggle');if(gt&&gt.focus)gt.focus();
}
function trapTab(e,back){
  if(e.key!=='Tab')return;
  const f=[...back.querySelectorAll('button,a[href],input,[tabindex]:not([tabindex="-1"])')]
          .filter(el=>el.offsetParent!==null);
  if(!f.length)return;
  const first=f[0],last=f[f.length-1];
  if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
  else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
}
// First-use card. One localStorage key, one dismissal, never again in this
// browser. Nothing about it is sent anywhere.
const _FU_KEY=SP+'FirstUseSeen';
// The card goes away on the first thing the reader does — a search, a filter,
// a route, an opened place — as well as on its own ✕. It sat on top of place
// popups otherwise, hiding the name and the star of the very place just tapped.
let _fuDismissed=false;
// --- 2026-09-22: the seasonal reminder ------------------------------------
// One line on the map while a season from CITY.seasons is on. It waits for the
// first-use card, steps aside for a place card or a drawn route, and once
// closed stays closed for that season on this device.
function activeSeason(){
  const iso=cityISODate();if(!iso||!CITY.seasons)return null;
  const md=iso.slice(5);
  return CITY.seasons.find(x=>x.from<=x.to?(md>=x.from&&md<=x.to):(md>=x.from||md<=x.to))||null;
}
function seasonKey(x){
  const iso=cityISODate(),y=parseInt(iso.slice(0,4),10),md=iso.slice(5);
  // a season that wraps the new year belongs to the year it started in
  return SP+'Season_'+x.id+'_'+(x.from>x.to&&md<=x.to?y-1:y);
}
let _seasonClosedMem={},_seasonShown={};
function renderSeason(){
  const el=document.getElementById('seasonNote');if(!el)return;
  const x=activeSeason(),fu=document.getElementById('firstUse');
  let closed=false;
  if(x){closed=!!_seasonClosedMem[x.id];try{closed=closed||localStorage.getItem(seasonKey(x))==='1';}catch(e){}}
  const busy=(fu&&!fu.hidden)||!!selectedRoute||!!(typeof map!=='undefined'&&map._popup&&map._popup.isOpen&&map._popup.isOpen());
  if(!x||closed||busy){el.hidden=true;return;}
  const u=UI[L_];
  el.innerHTML='<span class="sn-ic">'+emojiIcon(x.icon)+'</span>'+esc(x.text[L_]||x.text.en)
    +'<span class="sn-links">'+x.links.map(k=>'<a href="'+esc(k.u)+'" target="_blank" rel="noopener" data-season-link="'+esc(x.id)+'">'+esc(k.t[L_]||k.t.en)+' ›</a>').join('')+'</span>'
    +'<button type="button" class="sn-x" id="seasonClose" aria-label="'+esc(u.aClose)+'">✕</button>';
  el.hidden=false;
  if(!_seasonShown[x.id]){_seasonShown[x.id]=1;trackEvent('season_shown',{id:x.id});}
  document.getElementById('seasonClose').onclick=()=>{
    _seasonClosedMem[x.id]=true;try{localStorage.setItem(seasonKey(x),'1');}catch(e){}
    el.hidden=true;trackEvent('season_close',{id:x.id});
  };
  el.querySelectorAll('[data-season-link]').forEach(a=>a.onclick=()=>trackEvent('season_link',{id:x.id,to:a.getAttribute('href').split('/')[2]}));
}
function dismissFirstUse(src){
  const el=document.getElementById('firstUse');
  if(!el||el.hidden)return;
  _fuDismissed=true;   // storage may be blocked (private mode); remember in memory for this sitting
  try{localStorage.setItem(_FU_KEY,'1');}catch(e){}
  el.hidden=true;
  try{renderSeason();}catch(e){}
  if(src&&src!=='card')trackEvent('firstuse_dismiss',{via:src});
}
// --- item 1: the search box asks the questions ------------------------------
let _phTimer=null,_phIdx=0;
function startPlaceholderRotation(){
  clearInterval(_phTimer);_phTimer=null;
  const si=searchInputEl;if(!si)return;
  const u=UI[L_];const rot=u.searchPhRot||[];
  si.placeholder=u.searchPlaceholder;
  if(!rot.length)return;
  let reduce=false;try{reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;}catch(e){}
  if(reduce)return;
  _phTimer=setInterval(()=>{
    if(document.visibilityState!=='visible'||si.value||document.activeElement===si)return;
    _phIdx=(_phIdx+1)%(rot.length+1);
    si.placeholder=_phIdx===0?u.searchPlaceholder:rot[_phIdx-1];
  },4000);
}
function searchSuggestions(){
  const u=UI[L_];
  const card=id=>{const t=typeof TASKS!=='undefined'&&TASKS.find(x=>x.id===id);return t?{ic:t.icon||'🧭',label:(t.q&&(t.q[L_]||t.q.en))||id,kind:u.ssKindGuide,go:()=>{trackEvent('search_suggest',{to:'task:'+id});openGuide('suggest',id);}}:null;};
  const out=[card('msp'),card('sin')].filter(Boolean);
  out.push({ic:'💊',label:u.ssOpenPharmacy,kind:u.ssKindMap,go:()=>{trackEvent('search_suggest',{to:'open_pharmacy'});
    aC=new Set(['pharmacy']);selPresets.clear();presetsAdjusted=false;openNow=true;updateOpenQuickpick();renderCats();renderThemes();apply();
    try{const b=M.filter(m=>_isShown(m)).map(m=>[m.data.lat,m.data.lng]);if(b.length)map.fitBounds(b,{padding:[40,40],maxZoom:15});}catch(e){}}});
  out.push({ic:'🚌',label:u.ssBusTru,kind:u.ssKindMap,go:()=>{trackEvent('search_suggest',{to:'bus_tru'});_busQ='TRU';openPanel('bus');const inp=document.getElementById('busSearch');if(inp){inp.value='TRU';}renderBusList();}});
  return out;
}
function showSearchSuggest(){
  const box=document.getElementById('searchSuggest');if(!box)return;
  if(searchInputEl.value){hideSearchSuggest();return;}
  const u=UI[L_];
  box.innerHTML='<div class="ss-h">'+esc(u.ssHead)+'</div>';
  searchSuggestions().forEach(sg=>{
    const b=document.createElement('button');b.type='button';
    b.innerHTML='<span class="ss-ic" aria-hidden="true">'+emojiIcon(sg.ic)+'</span><span></span><span class="ss-k"></span>';
    b.children[1].textContent=sg.label;b.children[2].textContent=sg.kind;
    // pointerdown, not click: the input's blur would hide the list first
    b.addEventListener('pointerdown',e=>{e.preventDefault();});
    b.onclick=()=>{hideSearchSuggest();searchInputEl.blur();sg.go();};
    box.appendChild(b);
  });
  try{const sb=document.querySelector('.search-bar').getBoundingClientRect();box.style.top=(sb.bottom+(window.scrollY||0)+6)+'px';}catch(e){}
  box.hidden=false;
  dismissFirstUse('search');
}
function hideSearchSuggest(){const box=document.getElementById('searchSuggest');if(box)box.hidden=true;}
(function(){
  const si=searchInputEl;if(!si)return;
  si.addEventListener('focus',()=>{if(!si.value)showSearchSuggest();});
  const box=document.getElementById('searchSuggest');
  const stillInside=()=>{const a=document.activeElement;return a===si||(box&&box.contains(a));};
  si.addEventListener('blur',()=>{setTimeout(()=>{if(!stillInside())hideSearchSuggest();},150);});
  if(box){box.addEventListener('focusout',()=>{setTimeout(()=>{if(!stillInside())hideSearchSuggest();},0);});
    box.addEventListener('keydown',e=>{if(e.key==='Escape'){hideSearchSuggest();si.focus();}});}
  si.addEventListener('input',()=>{if(si.value)hideSearchSuggest();else if(document.activeElement===si)showSearchSuggest();});
  si.addEventListener('keydown',e=>{if(e.key==='Escape'&&!si.value){hideSearchSuggest();si.blur();}});
})();
function renderFirstUse(){
  const el=document.getElementById('firstUse');if(!el)return;
  let seen=_fuDismissed;try{seen=seen||!!localStorage.getItem(_FU_KEY);}catch(e){}
  // On a very short screen the card would push the map — the thing that shows
  // what this page is — below the fold. There it is simply not shown (and not
  // marked seen, so a later visit on a taller screen still gets it once).
  // very short screens: the floating card would cover too much of the map
  if(!seen&&innerHeight<520)seen=true;
  if(seen){el.hidden=true;el.innerHTML='';return;}
  const u=UI[L_];
  el.hidden=false;
  // 2026-09-13 (items 1 & 2): someone who scanned a flyer gets the flyer's
  // three promises as three buttons; everyone else gets one honest line —
  // the search box now carries the doors (see showSearchSuggest).
  const fromFlyer=/^(flyer|card)/.test(LANDED_SRC||'');
  el.classList.toggle('flyer',fromFlyer);el.classList.toggle('slim',!fromFlyer);
  if(fromFlyer){
    const tl=id=>{const t=typeof TASKS!=='undefined'&&TASKS.find(x=>x.id===id);return t?((t.icon?t.icon+' ':'')+(t.t[L_]||t.t.en)):id;};
    // 2026-09-13 audit: this heading wore the .fu-hs "short variant" class, which
    // the >=700px layout hides in favour of a long variant the flyer card never
    // had — so on a tablet the card opened with an empty heading and the ✕
    // landed on the first button. The flyer heading is the same at every width.
    el.innerHTML='<div class="fu-h">'+esc(u.fuFlyerHead)+'</div>'
      +'<button type="button" class="fu-x" id="fuClose" aria-label="'+esc(u.aClose)+'">✕</button>'
      +'<div class="fu-rows">'
      +['msp','sin','settle'].map(id=>'<div class="fu-row"><button type="button" data-go="task:'+id+'">'+iconify(tl(id))+'</button></div>').join('')
      +'</div><div class="fu-safe">'+esc(u.fuSafe)+'</div>';
  }else{
    el.innerHTML='<div class="fu-safe">'+esc(u.fuSafe)+'</div>'
      +'<button type="button" class="fu-x" id="fuClose" aria-label="'+esc(u.aClose)+'">✕</button>';
  }
  const done=()=>dismissFirstUse('card');
  el.querySelector('#fuClose').onclick=()=>{trackEvent('firstuse_dismiss',{});done();};
  el.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>{
    trackEvent('firstuse_go',{to:b.dataset.go});done();
    const go=b.dataset.go;
    if(go.indexOf('task:')===0)openGuide('flyer',go.slice(5));
    else if(go==='guide')openGuide('firstuse');
    else if(go==='search')searchInputEl.focus();
    else{openNow=true;updateOpenQuickpick();apply();}
  });
}
