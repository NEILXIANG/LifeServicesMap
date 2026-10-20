// A link straight to one card — what "I'll send you the steps for MSP" needs.
// Arrival date: asked once, kept in this browser only, never sent. It turns
// "90 days" into an actual date, and lets the list be sorted by what is due.
const _ARRIVE_KEY=SP+'Arrived';
let _arriveMem=null;   // storage may be blocked (private mode): the date still works for this sitting
// 2026-09-13 audit: typing a date into the field (rather than picking one)
// fires change with a partial year — "0002-09-01", "0020-09-01", "0202-09-01"
// — and the tax deadline for year 3 is an Invalid Date, which fmtDate's own
// fallback then threw on (uncaught, "page hit an error" toast), and a stored
// partial year made every later guide open throw too. Only a real calendar
// date between 1990 and today counts; anything else is treated as "not set".
function validArrival(v){
  if(!v||!/^\d{4}-\d{2}-\d{2}$/.test(v))return false;
  const y=+v.slice(0,4);if(y<1990||y>2100)return false;
  const d=new Date(v+'T12:00:00');if(isNaN(d)||localISODate(d)!==v)return false;   // 02-31 rolls over: reject
  return v<=localISODate();
}
function arrivalDate(){try{const v=localStorage.getItem(_ARRIVE_KEY);if(validArrival(v))return v;}catch(e){}return validArrival(_arriveMem)?_arriveMem:null;}
function setArrival(v){
  // A partial or future value clears nothing: the reader is still typing, or
  // the picker will correct it — the previous good date stays until a valid
  // one replaces it, and an empty value (the field's own clear) removes it.
  if(v&&!validArrival(v))return false;
  _arriveMem=v||null;try{if(v)localStorage.setItem(_ARRIVE_KEY,v);else localStorage.removeItem(_ARRIVE_KEY);}catch(e){}updateGuideProgress();return true;}
// The landing-screen strip: "3 of 14 done · licence by 30 Nov (51 days)".
// Shown only once there is something of the reader's own to show.
function updateGuideProgress(){
  const el=document.getElementById('guideProgress');if(!el||typeof TASKS==='undefined')return;
  const u=UI[L_];
  const doneN=TASKS.filter(t=>taskDone.has(t.id)).length;
  let next=null;
  if(arrivalDate()){
    TASKS.forEach(t=>{if(!t.deadline||taskDone.has(t.id))return;const d=deadlineDate(t);if(!d)return;const n=daysLeft(d);if(n<0)return;if(!next||n<next.n)next={t,d,n};});
  }
  const stepsAll=TASKS.reduce((a,t)=>a+stepsOf(t),0),stepsN=TASKS.reduce((a,t)=>a+stepsDoneN(t),0);
  // item 7: once the reader has started (a tick, a step, an arrival date),
  // the strip names the next week-1 card still open — "this week: get a SIN"
  const started=doneN>0||stepsN>0||!!arrivalDate();
  const week=started?TASKS.find(t=>t.due==='week1'&&!taskDone.has(t.id)):null;
  if(!started){el.hidden=true;el.innerHTML='';return;}
  el.hidden=false;
  el.innerHTML='<span class="gp-bar"><span style="width:'+Math.round(stepsN/Math.max(stepsAll,1)*100)+'%"></span></span>'
    +'<span>'+esc(u.taskProgress(doneN,TASKS.length))+'</span>'
    +(next?'<span class="gp-dl'+(next.n<=14?' soon':'')+'">'+esc(taskText(next.t.t))+' · '+esc(u.dlBy(fmtDate(next.d,L_),next.n))+'</span>'
      :(week?'<span class="gp-dl">'+esc(u.gpThisWeek)+esc(u.colon)+esc(taskText(week.t))+'</span>':''));
  el.onclick=()=>openGuide('progress',next?next.t.id:(week?week.id:undefined));
}
// The rule for each dated card, from its own source: licence 90 days from
// arrival; tax April 30 of the year after arrival (first return). MSP has no
// date — the wait starts when you apply, which is the reason to apply now.
// rights is deliberately NOT computed here: its one-year clock runs from the
// incident (see the card's own step 3 and note), a date this app never asks
// for. It used to stand in arrival+1yr as an "outside bound", but an incident
// almost always happens after arrival, so that silently understated the real
// time left and could show "past due" to someone who was not — see the
// 2026-09 QA report. The card states the rule as text instead.
// the cards whose deadline is counted from the arrival date — keep in step with deadlineDate below; only these offer
// "enter your arrival date to get the exact date" (the MSP card offered it and could never show a date, 2026-10-20)
function deadlineFromArrival(t){return t.id==='licence'||t.id==='tax';}
function deadlineDate(t){
  const a=arrivalDate();if(!a)return null;
  const d=new Date(a+'T12:00:00');
  if(t.id==='licence'){d.setDate(d.getDate()+90);return d;}
  if(t.id==='tax'){return new Date((d.getFullYear()+1)+'-04-30T12:00:00');}
  return null;
}
function fmtDate(d,l){
  if(!(d instanceof Date)||isNaN(d))return '';
  try{return new Intl.DateTimeFormat({zh:'zh-CN',en:'en-CA',fr:'fr-CA',es:'es',ko:'ko',ja:'ja'}[l]||l,{year:'numeric',month:'long',day:'numeric'}).format(d);}catch(e){return d.toISOString().slice(0,10);}
}
// 2026-09-13: whole calendar days between today and the deadline — Math.ceil
// against the deadline's noon said "91 days" all morning and "90" all afternoon
function daysLeft(d){const n=new Date();const a=Date.UTC(n.getFullYear(),n.getMonth(),n.getDate()),b=Date.UTC(d.getFullYear(),d.getMonth(),d.getDate());return Math.round((b-a)/86400000);}
function downloadIcs(t){
  const d=deadlineDate(t);if(!d)return;
  if(IN_APP_BROWSER){showToast(UI[L_].icsInApp,{ms:4500});return false;}
  const ymd=d.toISOString().slice(0,10).replace(/-/g,'');
  const stamp=new Date().toISOString().replace(/[-:]/g,'').slice(0,15)+'Z';
  const ics=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//'+CITY.key+' life guide//EN','BEGIN:VEVENT',
    'UID:'+t.id+'-'+ymd+'@'+CITY.key+'-lifeguide','DTSTAMP:'+stamp,'DTSTART;VALUE=DATE:'+ymd,
    'SUMMARY:'+taskText(t.t).replace(/[,;]/g,' '),'DESCRIPTION:'+taskLink(t.id),'BEGIN:VALARM','TRIGGER:-P7D','ACTION:DISPLAY','DESCRIPTION:'+taskText(t.t).replace(/[,;]/g,' '),'END:VALARM',
    'END:VEVENT','END:VCALENDAR'].join('\r\n');
  const a=document.createElement('a');
  a.href='data:text/calendar;charset=utf-8,'+encodeURIComponent(ics);a.download=t.id+'.ics';
  document.body.appendChild(a);a.click();a.remove();
  return true;
}
async function shareTask(t){
  const u=UI[L_];
  const link=taskLink(t.id), text=taskText(t.t)+' — '+link;
  trackEvent('task_share',{id:t.id,native:!!navigator.share});
  if(navigator.share){try{await navigator.share({title:taskText(t.t),text:taskText(t.q),url:link});return;}catch(e){}}
  let ok=false;try{await navigator.clipboard.writeText(text);ok=true;}catch(e){}
  if(!ok){
    // file:// and older WebViews: the textarea + execCommand path still works
    try{const ta=document.createElement('textarea');ta.value=text;ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.left='-9999px';
      document.body.appendChild(ta);ta.select();ok=document.execCommand('copy');ta.remove();}catch(e){}
  }
  if(ok){showToast(u.taskLinkCopied);return;}
  // last resort: put the link where it can be selected by hand, not in a toast that vanishes
  const host=document.getElementById('guideTasks');
  const box=host&&host.querySelector('.task-tools');
  if(box){let inp=box.querySelector('.task-link-box');
    if(!inp){inp=document.createElement('input');inp.className='task-link-box task-search';inp.readOnly=true;box.appendChild(inp);}
    inp.value=link;inp.focus();inp.select();}
  else showToast(link);
}
function taskLink(id){
  try{
    const url=new URL(location.href);
    url.search='';url.hash='';
    const q=new URLSearchParams();q.set('city',CITY.key);if(L_!=='en')q.set('lang',L_);q.set('task',id);
    url.search='?'+q.toString();return url.toString();
  }catch(e){return location.href;}
}
let _guideOpenedAt=0;
// One opener for every door into the guide — the header button, the Quick
// Pick, and a place popup — so the dwell timer and the src on the event are
// set the same way whichever one was used. `task` pre-opens a card, which is
// what the popup door needs: the reader is standing at Service Canada asking
// what to do there, not browsing.
function openGuide(src,task){
  // one open, one event: a double tap on the button opens the sheet once
  if(!guideBackdropEl.classList.contains('open')){
    _guideOpenedAt=Date.now();
    trackEvent('guide_open',{src:src||'header',task:task||undefined});
  }
  openModal(guideBackdropEl,{noHistory:src==='link'});
  // 2026-09-13 audit: closeModal clears _taskOpen but leaves the card's markup
  // in place, so the next opening showed the stale card with no entry under it
  // (Back then closed the whole guide). A leftover card means "render the list".
  if(task){openTask(task,src||'guide');}else if(_taskOpen||document.getElementById('taskBack')){renderTaskList();}
}
document.getElementById('guideToggle').onclick=()=>openGuide('header');
document.getElementById('qpOpen').onclick=()=>{
  openNow=!openNow;
  trackEvent('open_now_toggle',{action:openNow?'on':'off'});
  updateOpenQuickpick();renderCats();renderThemes();apply();
};
document.getElementById('map').addEventListener('click',e=>{
  const rb=e.target.closest&&e.target.closest('.pv-route');
  if(rb){e.preventDefault();e.stopPropagation();trackEvent('popup_route',{route:rb.dataset.route});selectRoute(rb.dataset.route,{keepView:true,src:'popup'});return;}
  const go=e.target.closest&&e.target.closest('.pv-task-go');
  if(!go)return;
  e.preventDefault();e.stopPropagation();
  map.closePopup();
  openGuide('popup',go.dataset.task);
});
// Every path out of the guide runs through closeModal, so the close event is
// hooked there rather than on the ✕ button alone — Escape and a backdrop tap
// are the two commonest ways people actually leave it.
function trackGuideClose(){
  if(!_guideOpenedAt)return;
  trackEvent('guide_close',{ms:Math.min(Date.now()-_guideOpenedAt,3600000)});
  _guideOpenedAt=0;
}
document.getElementById('guideClose').onclick=()=>closeModal(guideBackdropEl);
guideBackdropEl.onclick=(e)=>{if(e.target===guideBackdropEl&&!justOpened(guideBackdropEl))closeModal(guideBackdropEl);};
guideBackdropEl.addEventListener('keydown',e=>trapTab(e,guideBackdropEl));

// Expand every placeholder once, for every language, before the first render.
// Doing it per render site would mean any site I forget silently ships "{CITY}".
// ---------------------------------------------------------------------------
// URL state. A filtered view is the thing people want to send each other
// ("here are the banks on the North Shore, in Korean"), and until now every
// share opened the default view. ?city= is reserved now, while there are no
// links in circulation to break, even though only one city exists.
// Favourites deliberately stay out of the URL — they are personal, not shareable.
// ---------------------------------------------------------------------------
let urlWriteBlocked=true;
// `obj[key]` is truthy for anything inherited from Object.prototype, so a plain
// truth test let ?lang=constructor and ?route=toString through the validation and
// blanked the page. Only own keys are real data.
function owns(obj,k){return typeof k==='string'&&Object.prototype.hasOwnProperty.call(obj,k);}
function readURLState(){
  let q;
  try{q=new URLSearchParams(location.search);}catch(e){return null;}
  if(q.get('city')&&q.get('city')!==CITY.key)return null; // a link for another city
  const out={};
  const lang=q.get('lang');
  if(owns(UI,lang))out.lang=lang;
  const r=(q.get('r')||'').split(',').filter(k=>owns(RI,k));
  if(r.length)out.regions=r;
  const c=(q.get('c')||'').split(',').filter(k=>owns(CI,k));
  if(c.length)out.cats=c;
  // Themes ride in the link like everything else, so a shared "free + indoor in
  // North Shore" view arrives as that view rather than as the default map.
  const t=(q.get('t')||'').split(',').filter(k=>owns(TI,k));
  if(t.length)out.themes=t;
  const qq=(q.get('q')||'').trim();
  if(qq)out.q=qq;
  const rt=q.get('route');
  if(owns(BR,rt))out.route=rt;
  // 2026-09-13: "open now" is a filter like the others; a shared or reloaded
  // link keeps it (it is re-evaluated against the clock on arrival, of course)
  if(q.get('o')==='1')out.open=true;
  // ?task=msp opens that card. It says *which* card, never whether it was
  // ticked — that stays in localStorage and never enters a link.
  const tk=q.get('task');
  if(tk&&typeof TASKS!=='undefined'&&TASKS.some(t=>t.id===tk))out.task=tk;
  return out;
}
function writeURLState(){
  if(urlWriteBlocked)return;
  try{
    const q=new URLSearchParams();
    q.set('city',CITY.key);
    if(L_!=='en')q.set('lang',L_);
    if(aR.size&&aR.size<Object.keys(RI).length)q.set('r',[...aR].join(','));
    if(aC.size)q.set('c',[...aC].join(','));
    if(aT.size)q.set('t',[...aT].join(','));
    // 2026-09-21: the search box stays out of the address bar — it is what
    // lands in browser history on a shared device. A share adds it on purpose.
    if(selectedRoute)q.set('route',selectedRoute);
    if(openNow)q.set('o','1');
    if(_taskOpen&&guideBackdropEl&&guideBackdropEl.classList.contains('open'))q.set('task',_taskOpen);
    // ?debug=1 is the maintainer's own flag; dropping it on the first rewrite
    // meant a reload silently turned the debug panel and env:'dev' tagging off
    if(_IS_DEBUG)q.set('debug','1');
    // replaceState, not pushState: filtering is not navigation and should not
    // fill the back button with dozens of intermediate states
    history.replaceState(history.state||null,'',location.pathname+'?'+q.toString()+location.hash);
  }catch(e){/* file:// and sandboxed frames disallow this; the app works regardless */}
}
(function expandUI(){
  Object.keys(UI).forEach(l=>{
    Object.keys(UI[l]).forEach(k=>{
      if(typeof UI[l][k]==='string')UI[l][k]=tpl(UI[l][k],l);
    });
  });
})();
wireFavIO();
// 2026-09-08 audit: public/sw.js has been written, documented, deployed and
// version-bumped since the PWA shipped — and nothing ever registered it, so the
// offline shell it describes did not exist. That matters here more than for most
// sites: manifest.json advertises an installable standalone app, session_start
// reports a `pwa` flag as though one were running, and the offline notice tells
// the reader in five languages that "place details, search, filters and the
// resident guide all work without a connection" — which, on a cold offline load
// with no service worker, was simply not true.
// Registered defensively: only over http(s) (a file:// copy has no origin to
// scope to), only after load so it never competes with first paint, and inside
// try/catch because a rejected registration must never surface to the reader.
if('serviceWorker' in navigator&&location.protocol.indexOf('http')===0){
  window.addEventListener('load',()=>{
    try{
      navigator.serviceWorker.register('sw.js').catch(e=>{
        trackEvent('sw_register',{ok:false,msg:String(e&&e.message||e).slice(0,80)});
      }).then(reg=>{if(reg)trackEvent('sw_register',{ok:true});});
    }catch(e){}
  });
}
// #map has no measured height until layout runs; take the real one now.
setTimeout(syncPanPad,0);
// P1-A ONB-02 (2026-09-05): a first-time visitor with no stored choice falls
// back to navigator.languages instead of bare 'en' — zh users on zh devices
// were bouncing off English before noticing the language buttons.
//
// 2026-09-07, settled after this had been flipped three times: keep the browser
// guess. The objection to it was that an English speaker whose browser merely
// lists zh somewhere would land on Chinese — but detectLang() returns the FIRST
// entry of navigator.languages that we support, so ['en-US','zh-CN'] resolves to
// en and only ['zh-CN',...] resolves to zh. Verified all four paths in a browser:
//   ['en-US','zh-CN'] -> en      ['zh-CN','en-US'] -> zh
//   ['de-DE']         -> en      zh browser + a saved choice of fr -> fr
// So the guess is only ever the reader's own first preference, and an explicit
// choice still beats it. Please do not swap this back to a hard-coded 'en'
// without a concrete case where the first-preference rule gets it wrong.
// 2026-09-07: the explicit choice a returning reader already made is restored
// ahead of that guess. It had been dropped in the September rewrite, so someone
// who switched to 中文 landed back on the browser guess every single visit.
// Precedence is: ?lang= in the link  >  what you picked last time  >  browser
// language  >  English.
const LANG_KEY=SP+'Lang';
function getStoredLang(){
  try{const v=localStorage.getItem(LANG_KEY);return owns(UI,v)?v:null;}catch(e){return null;}
}
function setStoredLang(l){try{localStorage.setItem(LANG_KEY,l);}catch(e){}}
function detectLang(){
  const cands=(navigator.languages&&navigator.languages.length)?navigator.languages:[navigator.language||''];
  for(let i=0;i<cands.length;i++){
    const base=(cands[i]||'').toLowerCase().split('-')[0];
    if(owns(UI,base))return base;
  }
  return 'en';
}
(function applyURLState(){
  // Read the address bar *before* writeURLState() rewrites it below — the
  // ?src= flyer tag and ?source=pwa were being read afterwards, from a URL
  // that no longer carried them, so neither had ever been recorded.
  const landedSearch=location.search;
  const st=readURLState();
  if(st){
    if(st.regions){aR=new Set(st.regions);}
    if(st.cats){aC=new Set(st.cats);}
    if(st.themes){aT=new Set(st.themes);}
    if(st.open){openNow=true;}
    // a link whose categories equal a Quick Pick exactly lights that chip again
    if(st.cats){Object.keys(PRESETS).forEach(k=>{if(setEq(aC,PRESETS[k]))selPresets.add(k);});}
    if(st.q){searchInputEl.value=st.q;searchRaw=st.q.toLowerCase();
      if(st.q.length>=MIN_QUERY)searchTerm=st.q.toLowerCase();
      searchClearEl.hidden=false;}
  }
  // URL ?lang= 永远胜出；其次是上次手动选过的语言（记在 localStorage 里）；
  // 再次才按 navigator.languages 猜；都没有则退回英文。
  setLang(st&&st.lang?st.lang:(getStoredLang()||detectLang()));
  bumpVisitCount();applyQuickPickOrder(true);
  if(st&&st.route)renderRoute(st.route,true);
  if(st&&st.task)setTimeout(()=>openGuide('link',st.task),80);
  urlWriteBlocked=false;
  writeURLState();
  // session_start is the denominator every other rate is measured against:
  // without it "12 sessions" only counts people who happened to click something,
  // and a visitor who loaded the map, found nothing, and left is invisible.
  // Fires once per page load, after URL state is applied, so lang/region/cats
  // reflect what the visitor actually landed on.
  trackEvent('session_start',{
    ver:DATA_VERSION,
    lang:L_,
    ref:document.referrer?(new URL(document.referrer)).host:'direct',
    // ?src=flyer-2609 etc.: which printed thing brought this person here. The
    // only way to learn whether a flyer on a noticeboard is worth reprinting.
    src:(function(){try{const v=new URLSearchParams(landedSearch).get('src')||'';return /^[a-z0-9-]{1,24}$/.test(v)?v:undefined;}catch(e){return undefined;}})(),
    // which of the three layouts this reader is actually looking at
    dev:(innerWidth<600?'phone':innerWidth<1024?'tablet':'desktop'),
    // installed to the home screen, or opened from the browser? The manifest
    // has advertised ?source=pwa since the PWA shipped and nothing ever read it,
    // so "is anyone installing this" has never been answerable.
    pwa:(function(){try{
      return /[?&]source=pwa\b/.test(landedSearch)
        ||(window.matchMedia&&window.matchMedia('(display-mode: standalone)').matches)
        ||navigator.standalone===true;}catch(e){return false;}})(),
    // arrived on a shared link that already carried filters — a different
    // journey from landing on the default map, and one the share feature exists
    // to create, so its share of traffic is worth knowing
    deep:!!(st&&(st.regions||st.cats||st.themes||st.q||st.route)),
    lead:!!(st&&st.lang),
    // 1 on a first visit; the Quick Picks row starts treating the reader as a
    // resident from 3. Capped, never identifying.
    visits:visitCount()
  });
})();
