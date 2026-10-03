// One query object, consulted wherever the tight layout changes behaviour, so the
// CSS breakpoint and the JS can never drift apart.
const TIGHT=window.matchMedia('(max-height:680px) and (max-width:600px)');
const M=[];
// aC empty === no category filter (everything shows). It used to hold all 44 keys,
// which made "nothing selected" and "everything selected" the same value — that
// ambiguity is why clicking a category used to mean "hide it".
let aC=new Set(),aR=new Set(Object.keys(RI));
// aT follows the same convention: empty means "no theme filter", never "all ten".
let aT=new Set();
let presetsAdjusted=false;
// Groups a resident reaches for first are open on arrival; the rest stay collapsed
// so the panel does not open as 44 undifferentiated chips.
const DEFAULT_OPEN_GROUPS=['services','health','housing','shop'];
let selPresets=new Set();
let searchTerm='';
let favorites=new Set(),favMigrated=false;
try{
  const raw=JSON.parse(localStorage.getItem(SP+'Favorites')||'[]');
  // Older versions stored place NAMES. Names change when data is corrected, which
  // silently orphaned saved entries, so storage moved to a stable per-place id and
  // anything still held under an old name is translated across once.
  const mapped=raw.map(v=>FAV_MIGRATE[v]||v);
  favorites=new Set(mapped);
  if(mapped.some((v,i)=>v!==raw[i]))favMigrated=true;
}catch(e){}
if(favMigrated)saveFavorites();
// Favourites are keyed by place name, so a renamed or removed place would otherwise
// leave an invisible entry that still counted toward the badge. Prune on load so the
// badge and the list can never disagree.
(function pruneFavorites(){
  const live=new Set(P.map(p=>p.id)),before=favorites.size;
  favorites=new Set([...favorites].filter(id=>live.has(id)));
  if(favorites.size!==before)saveFavorites();
})();
function saveFavorites(){try{localStorage.setItem(SP+'Favorites',JSON.stringify([...favorites]));}catch(e){}}
const toastEl=document.getElementById('toast');
let toastTimer=null;
// opts.action / opts.onAction: an Undo-style button inside the toast (it then
// stays up longer, since a choice is being offered, not just a confirmation).
function showToast(msg,opts){
  if(!toastEl)return;
  clearTimeout(toastTimer);
  toastEl.textContent=msg;toastEl.hidden=false;
  if(opts&&opts.action){
    const b=document.createElement('button');b.type='button';b.className='toast-act';b.textContent=opts.action;
    b.onclick=()=>{clearTimeout(toastTimer);toastEl.classList.remove('show');toastEl.hidden=true;try{opts.onAction&&opts.onAction();}catch(e){}};
    toastEl.appendChild(b);
  }
  // Two rAFs so the browser paints the [hidden]->block change before the opacity
  // transition starts; one is sometimes not enough for it to register as a change.
  requestAnimationFrame(()=>requestAnimationFrame(()=>toastEl.classList.add('show')));
  toastTimer=setTimeout(()=>{
    toastEl.classList.remove('show');
    setTimeout(()=>{if(!toastEl.classList.contains('show'))toastEl.hidden=true;},200);
  },(opts&&opts.ms)||(opts&&opts.action?5000:1600));
}
// Everything Reset and "Clear all" throw away, kept for one Undo. Forgiveness
// is cheaper than a confirmation dialog and never gets in the way.
function filterSnapshot(){
  return {aR:[...aR],aC:[...aC],aT:[...aT],sp:[...selPresets],pa:presetsAdjusted,on:openNow,near:nearOnly,
          q:searchInputEl?searchInputEl.value:'',route:selectedRoute,view:{c:map.getCenter(),z:map.getZoom()}};
}
function restoreSnapshot(sn){
  if(!sn)return;
  aR=new Set(sn.aR);aC=new Set(sn.aC);aT=new Set(sn.aT);selPresets=new Set(sn.sp);presetsAdjusted=sn.pa;
  openNow=sn.on;updateOpenQuickpick();nearOnly=!!sn.near;updateNearQuickpick();
  if(searchInputEl){searchInputEl.value=sn.q;clearTimeout(searchTimer);searchRaw=sn.q.trim().toLowerCase();searchTerm=searchRaw.length>=MIN_QUERY?searchRaw:'';searchClearEl.hidden=!searchRaw;}
  renderRegs();renderCats();renderThemes();
  if(sn.route)renderRoute(sn.route,false);
  apply();
  try{if(sn.view)map.setView(sn.view.c,sn.view.z);}catch(e){}
  trackEvent('reset_undo',{});
}
