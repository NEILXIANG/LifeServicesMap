const searchInputEl=document.getElementById('searchInput'),searchClearEl=document.getElementById('searchClear');
// Debounced: every keystroke used to re-fit the map, so the view lurched around
// while you were still typing. preSearchView remembers where you were so that
// clearing the search puts the map back instead of stranding you at the last hit.
let searchTimer=null,preSearchView=null,searchRaw='';
let _lastCountedTerm='';
function runSearch(){
  const wasSearching=!!searchTerm;
  const raw=searchInputEl.value.trim().toLowerCase();
  // one character matched almost everything (the note field is long prose), so a
  // query only counts once it is specific enough to mean something
  searchRaw=raw;
  searchTerm=raw.length>=MIN_QUERY?raw:'';
  searchClearEl.hidden=!raw;
  if(searchTerm&&!wasSearching)preSearchView={c:map.getCenter(),z:map.getZoom()};
  if(!searchTerm&&preSearchView){map.setView(preSearchView.c,preSearchView.z);preSearchView=null;}
  apply();
  // panel counts follow the search term (see renderCats / themeCount)
  if(searchTerm!==_lastCountedTerm){_lastCountedTerm=searchTerm;renderCats();renderThemes();}
  scheduleSearchLog();
}
// Logging waits for typing to stop, and never logs the same settled query twice
// in a row, so one intent produces one row. lastVisible is read here rather than
// captured earlier because apply() has by then written the count this query
// actually produced — which is the number that makes the row worth having.
let searchLogTimer=null,_lastLoggedQuery=null;
const SEARCH_SETTLE_MS=1100;
function logSearch(){
  clearTimeout(searchLogTimer);
  const raw=searchRaw;
  if(!raw||raw.length<MIN_QUERY){_lastLoggedQuery=null;return;}
  if(raw===_lastLoggedQuery)return;
  _lastLoggedQuery=raw;
  const totalR=Object.keys(RI).length;
  const filtered=aR.size<totalR||aT.size>0;   // categories pause during a search
  trackEvent('search_run',{q:raw,len:raw.length,n:lastVisible,filtered:filtered,closest:_closest||undefined,catsPaused:aC.size>0||undefined});
  // "What did people look for and find nothing?" points straight at content
  // gaps, so it keeps its own event type: Analytics Engine indexes the type
  // column, and a dedicated type is a cheap scan instead of a filter over every
  // search ever run.
  if(_exactN===0){
    trackEvent('search_empty',{q:raw,len:raw.length,closest:_closest?lastVisible:undefined,
      filters:{areas:aR.size<totalR,catsPaused:aC.size>0,theme:aT.size>0,route:!!selectedRoute}});
  }
}
function scheduleSearchLog(){clearTimeout(searchLogTimer);searchLogTimer=setTimeout(logSearch,SEARCH_SETTLE_MS);}
searchInputEl.oninput=()=>{clearTimeout(searchTimer);searchTimer=setTimeout(runSearch,260);};
searchInputEl.onkeydown=(e)=>{
  // Enter is an explicit submit, so it settles the query immediately rather
  // than waiting out the timer.
  if(e.key==='Enter'){clearTimeout(searchTimer);runSearch();logSearch();}
  if(e.key==='Escape'&&searchInputEl.value){searchInputEl.value='';clearTimeout(searchTimer);runSearch();}
};
searchClearEl.onclick=()=>{
  // 2026-09-08 audit: abandoning a search is as informative as running one —
  // it says the query went nowhere — and this path recorded nothing at all.
  trackEvent('search_clear',{had:searchRaw.length,n:lastVisible});
  searchInputEl.value='';clearTimeout(searchTimer);runSearch();searchInputEl.focus();
};
const guideBackdropEl=document.getElementById('guideBackdrop');
// the three sheets learn the downward swipe once their elements exist
setTimeout(()=>{try{
  attachSheetDrag(guideBackdropEl,document.getElementById('guideModal'));
  attachSheetDrag(noteBackdropEl,document.getElementById('noteModal'));
  attachSheetDrag(shareBackdropEl,document.getElementById('shareModal'));
  attachSheetDrag(helpBackdropEl,document.getElementById('helpModal'));
}catch(e){}},0);
// Every overlay (the two centred modals here, and the four bottom-sheet panels in
// openPanel/closePanel below) sits on a position:fixed backdrop, but fixed
// positioning alone does not stop the page underneath from scrolling — a wheel or
// touch gesture that lands on the dimmed area outside the modal's own scroll
// region falls through to the document, since nothing there is a scroll container.
// The result: reading the Resident Guide with a mouse wheel or a swipe could drag
// the whole page (header, quick picks) along with it. Locking body scroll while
// any overlay is open — reference-counted, so two overlays cannot unlock each
// other early — fixes that for all six.
let scrollLockCount=0,savedScrollY=0;
function lockBodyScroll(){
  if(scrollLockCount===0){
    savedScrollY=window.scrollY||window.pageYOffset||0;
    document.body.style.position='fixed';
    document.body.style.top=(-savedScrollY)+'px';
    document.body.style.left='0';document.body.style.right='0';document.body.style.width='100%';
  }
  scrollLockCount++;
}
function unlockBodyScroll(){
  scrollLockCount=Math.max(0,scrollLockCount-1);
  if(scrollLockCount===0){
    document.body.style.position='';document.body.style.top='';
    document.body.style.left='';document.body.style.right='';document.body.style.width='';
    window.scrollTo(0,savedScrollY);
  }
}
// Modal plumbing shared by the guide and the data notes: remember what had focus,
// move focus inside, keep Tab within the dialog, restore focus on close.
let lastFocused=null;
// ---- sheets and the Back gesture (2026-09-11) ------------------------------
// On a phone the system Back gesture used to leave the site with a sheet still
// open — the most common way to close anything on iOS/Android did the one
// thing nobody wanted. Opening a sheet now pushes one history entry carrying
// its id; Back pops it and the sheet closes; closing by any other means pops
// the entry itself so Back never has a stale sheet to return to.
const _SHEET_KEY='kSheet';
let _popSelf=false,_popSelfTimer=null;
// 2026-10-05 (newcomer test): "Open it on the map" from a card closed the guide and took its history entries
// with it, so the next Back left the site. It now leaves one entry behind; Back from the map reopens that card.
const _FROM_TASK='kFromTask';
let _afterPop=null,_onTaskMap=null;
function leaveTaskForMap(id){
  const st=Object.assign({},history.state||{});delete st[_SHEET_KEY];st[_FROM_TASK]=id;
  _onTaskMap=id;
  // closing the guide may still be stepping back through history: add the entry once that has landed
  if(_popSelf)_afterPop=st;else{try{history.pushState(st,'',location.href);}catch(e){}}
}
function pushSheetState(id){
  try{
    if(history.state&&history.state[_SHEET_KEY]===id)return;
    const st=Object.assign({},history.state||{});st[_SHEET_KEY]=id;
    history.pushState(st,'',location.href);
  }catch(e){}
}
function popSheetState(id){
  try{
    const cur=history.state&&history.state[_SHEET_KEY];
    let n=0;
    if(cur===id)n=1;
    else if(id==='guideBackdrop'&&cur==='guideTask')n=2;   // closing the guide from inside a card (a card entry only ever sits on a guide entry — see openTask)
    if(!n)return;
    _popSelf=true;
    clearTimeout(_popSelfTimer);
    _popSelfTimer=setTimeout(()=>{_popSelf=false;},600);   // never swallow a real Back
    history.go(-n);
  }catch(e){_popSelf=false;}
}
window.addEventListener('popstate',e=>{
  // Whatever entry we land on, the address bar must describe the filters as
  // they are now — the popped entry carries the URL from before the sheet
  // opened, and filters are usually changed *inside* the sheet.
  if(_popSelf){_popSelf=false;clearTimeout(_popSelfTimer);writeURLState();
    if(_afterPop){const st=_afterPop;_afterPop=null;try{history.pushState(st,'',location.href);}catch(err){}}
    return;}
  // Back from the map we reached through a card: return to that card
  if(_onTaskMap&&!(e.state&&e.state[_FROM_TASK])){const id=_onTaskMap;_onTaskMap=null;
    if(!guideBackdropEl.classList.contains('open')){try{map.closePopup();}catch(err){}openGuide('back',id);return;}}
  const id=(e.state&&e.state[_SHEET_KEY])||null;
  // Back from an open card returns to the list
  if(id==='guideBackdrop'&&guideBackdropEl.classList.contains('open')&&_taskOpen){renderTaskList();return;}
  const wasOpen=[guideBackdropEl,noteBackdropEl,shareBackdropEl,helpBackdropEl].some(b=>b&&b.classList.contains('open'))||panel.classList.contains('open');
  [guideBackdropEl,noteBackdropEl,shareBackdropEl,helpBackdropEl].forEach(b=>{
    if(b&&b.classList.contains('open')&&id!==b.id)closeModal(b,true);
  });
  if(panel.classList.contains('open')&&id!=='panel')closePanel(true);
  writeURLState();
  // 2026-09-13: a reload with a card open leaves the older sheet entries in
  // history. Landing on one of them with nothing open is a dead Back press;
  // step over it so the next press does what the reader meant.
  if(id&&!wasOpen){_popSelf=true;clearTimeout(_popSelfTimer);_popSelfTimer=setTimeout(()=>{_popSelf=false;},600);history.go(-1);}
});
// 2026-09-11: "open now" and the deadline countdown were computed only on
// interaction — a tab left open overnight kept last night's answer. They are
// recomputed when the tab becomes visible again, and open-now once a minute
// while it is on and the tab is visible.
window.addEventListener('appinstalled',()=>{try{trackEvent('pwa_install',{});}catch(e){}});
// WeChat and other in-app browsers silently ignore mailto: and file downloads.
// Rather than a tap that does nothing, copy the address and say so.
const IN_APP_BROWSER=/MicroMessenger|; wv\)|FBAN|FBAV|Instagram|Line\//i.test(navigator.userAgent||'');
function copyText(txt){
  try{const ta=document.createElement('textarea');ta.value=txt;ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.left='-9999px';
    document.body.appendChild(ta);ta.select();const ok=document.execCommand('copy');ta.remove();if(ok)return true;}catch(e){}
  try{if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt);return true;}}catch(e){}
  return false;
}
// 2026-09-22 tracking audit: outbound links and the feedback mail link were
// invisible in the data — a card's official source, links in the guide text, and
// "Report an issue". One listener, capture phase so it runs before the in-app
// browser mailto handler below can stop anything. Records the destination host
// only. The Help sheet and every tel: link are left out on purpose.
function _linkHost(href){try{return new URL(href,location.href).hostname.replace(/^www\./,'');}catch(e){return '';}}
document.addEventListener('click',e=>{
  try{
    const a=e.target&&e.target.closest?e.target.closest('a[href]'):null;
    if(!a||a.closest('#helpModal'))return;
    const href=a.getAttribute('href')||'';
    if(/^mailto:/i.test(href)){
      if(a.classList.contains('pv-report')){
        const box=a.closest('.leaflet-popup-content'),pv=box&&box.querySelector('[data-pid]');
        trackEvent('feedback_click',{kind:'place',id:pv?pv.dataset.pid:undefined,cat:pv?pv.dataset.pcat:undefined});
      }else if(a.id==='feedbackLink')trackEvent('feedback_click',{kind:'general'});
      else if(a.closest('#guideTasks')&&a.closest('.task-checked'))trackEvent('feedback_click',{kind:'task',id:_taskOpen||undefined});
      return;
    }
    // 2026-09-22 (maintainer's decision): a phone tap inside a task card is
    // counted as the card only — which number was dialled is never sent.
    if(/^tel:/i.test(href)){if(a.closest('#guideTasks'))trackEvent('task_call',{id:_taskOpen||undefined});return;}
    if(!/^https?:/i.test(href))return;
    if(a.closest('#guideTasks')){
      trackEvent(a.closest('.task-src')?'task_src':'task_link',{id:_taskOpen||undefined,to:_linkHost(href)});
    }else if(a.closest('#guideBody')){
      trackEvent('guide_link',{to:_linkHost(href)});
    }
  }catch(err){}
},true);
if(IN_APP_BROWSER)document.addEventListener('click',e=>{
  const a=e.target&&e.target.closest?e.target.closest('a[href^="mailto:"]'):null;
  if(!a)return;
  e.preventDefault();
  const href=a.getAttribute('href');
  const addr=decodeURIComponent(href.slice(7).split('?')[0]);
  const u=UI[L_];
  // 2026-09-13: the share sheet's ✉️ is "mailto:?subject=…&body=<link>" — no
  // address. Copying "" and announcing it was the bug; copy the link instead.
  if(!addr){
    let body='';try{body=decodeURIComponent((new URLSearchParams(href.split('?')[1]||'')).get('body')||'');}catch(err){}
    const link=body||location.href;
    showToast(copyText(link)?u.linkCopied:u.copyFailedLink.replace('{L}',link),{ms:4500});
    trackEvent('mailto_fallback',{kind:'share'});
    return;
  }
  showToast((copyText(addr)?u.copiedEmail:u.copyFailedEmail).replace('{E}',addr),{ms:6000});
  trackEvent('mailto_fallback',{kind:'contact'});
});
window.addEventListener('afterprint',()=>document.body.classList.remove('print-task'));
const _sessionStartedAt=Date.now();let _lastEndSent=0;
document.addEventListener('visibilitychange',()=>{
  if(document.visibilityState==='hidden'){
    // sendBeacon survives the tab closing; one row per real leave, not per glance
    const now=Date.now();
    if(now-_lastEndSent>30000){_lastEndSent=now;try{trackEvent('session_end',{dur:Math.round((now-_sessionStartedAt)/1000)});}catch(e){}}
    return;
  }
  if(document.visibilityState!=='visible')return;
  try{if(openNow)apply();updateGuideProgress();applyQuickPickOrder(true);
    // only the list below the search box is refreshed — replacing the box
    // itself would close the keyboard on a phone mid-typing
    if(guideBackdropEl.classList.contains('open')&&!_taskOpen)renderTaskBuckets();}catch(e){}
});
setInterval(()=>{try{if(openNow&&document.visibilityState==='visible')apply();}catch(e){}},60000);
// 2026-10-16 (visit log): a phone kept a tab of 2026.09.24 open for three weeks — mobile browsers resume a tab
// without reloading, so it went on showing three-week-old phone numbers and hours. When a tab that has been open
// for hours comes back to the front, ask the server (a HEAD request, no body) whether the page has changed since
// it loaded; if it has, offer a reload. Nothing happens on file:// or offline.
let _pageStamp=null,_lastVerCheck=0;
function _headStamp(){
  if(!/^https?:$/.test(location.protocol))return Promise.resolve(null);
  return fetch(location.pathname,{method:'HEAD',cache:'no-store'})
    .then(r=>r.ok?(r.headers.get('etag')||r.headers.get('last-modified')):null).catch(()=>null);
}
setTimeout(()=>{_headStamp().then(s=>{_pageStamp=s;});},15000);
const VER_CHECK_AFTER=6*3600e3;
document.addEventListener('visibilitychange',()=>{
  if(document.visibilityState!=='visible'||!_pageStamp)return;
  const now=Date.now();
  if(now-_sessionStartedAt<VER_CHECK_AFTER||now-_lastVerCheck<3600e3)return;
  _lastVerCheck=now;
  _headStamp().then(s=>{
    if(!s||s===_pageStamp)return;
    const u=UI[L_];
    try{trackEvent('update_offer',{});}catch(e){}
    showToast(u.updateAvail,{action:u.updateReload,ms:20000,onAction:()=>{try{trackEvent('update_reload',{});flushEvents();}catch(e){}location.reload();}});
  });
});
// A reload with a sheet open leaves its marker in history.state; treat the
// fresh page as having nothing open, or the next ✕ would navigate away.
try{if(history.state&&history.state[_SHEET_KEY]){const st=Object.assign({},history.state);delete st[_SHEET_KEY];history.replaceState(st,'',location.href);}}catch(e){}
