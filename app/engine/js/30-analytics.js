// Click tracking — Phase A: every event is now (a) sent to the edge via
// navigator.sendBeacon('/api/event', Blob) and (b) mirrored into a local ring
// buffer that ?debug=1 can export. The 25 call sites below stay exactly as
// written; only the helper internals changed. Names follow a verb_noun pattern
// so the SQL reports read like English.
//
// Anonymous session ID is generated locally, persisted in localStorage, and
// attached to every event so the server side can say "this user clicked X
// then Y" without ever knowing who they are. No fingerprinting, no IP
// collection — the Worker echoes nothing back. (The two third parties, the
// tile server and the Cloudflare visit counter, are named in the privacy note.)
const _SID_KEY=SP+'Sid';
// 2026-09-11: the id is rotated after 90 days, so a browser can never be
// followed for longer than that even in principle. The "returning" share dips
// on the day an id turns over; that is the price and it is worth paying.
const _SID_AT_KEY=SP+'SidAt',SID_MAX_AGE_MS=90*24*3600*1000;
function getSid(){
  try{
    let sid=localStorage.getItem(_SID_KEY);
    const at=parseInt(localStorage.getItem(_SID_AT_KEY)||'0',10)||0;
    if(sid&&/^[a-z0-9]{12,32}$/.test(sid)&&at&&Date.now()-at<SID_MAX_AGE_MS)return sid;
    if(sid&&/^[a-z0-9]{12,32}$/.test(sid)&&!at){
      // an id from before rotation existed: start its clock now rather than
      // throwing it away, so today's returning visitors stay countable
      localStorage.setItem(_SID_AT_KEY,String(Date.now()));return sid;}
    localStorage.setItem(_SID_AT_KEY,String(Date.now()));
    // crypto.randomUUID is universal since 2022; the Math.random fallback is
    // paranoia for very old engines and produces a different value per call
    // anyway (no longer a session id, just a "did not get an id" marker).
    sid=(typeof crypto!=='undefined'&&crypto.randomUUID)
      ?crypto.randomUUID().replace(/-/g,'').slice(0,24)
      :Math.random().toString(36).slice(2,18);
    localStorage.setItem(_SID_KEY,sid);
    return sid;
  }catch(e){return 'anon';}
}
// 2026-09-21: a search that says someone may be in danger gets the lines that
// answer, above any results, and the words themselves are never uploaded.
// 2026-10-04 (newcomer test, persona fleeing abuse at night): "safe place", "women shelter", "he hit me",
// "scared of my husband" found a supermarket and a pub. (Generic "shelter" words — 庇护所, 쉼터, シェルター —
// stay place-search synonyms for the shelter category; validate.py keeps crisis words out of SYN.) Added the words people actually type; the crisis block is
// shown ABOVE the normal results, so a wider net only ever adds the 24-hour lines (and logs the query as [crisis]).
const _CRISIS_RE=/\b(suicid\w*|kill my ?self|kill me|want to die|self[- ]?harm\w*|overdos\w*|abus\w*|violen\w*|domestic|hits me|beats me|hit me|hitting me|hurts? me|rape\w*|sexual assault|assault\w*|unsafe|in danger|crisis|crise|dv|safe[ ](?:place|house|home)|transition house|wom[ae]n'?s? shelter|shelter for wom[ae]n|(?:scared|afraid|frightened) of (?:my )?(?:husband|wife|partner|boyfriend|girlfriend|ex|dad|father|mom|mother|family)|leav(?:e|ing) (?:my )?(?:husband|wife|partner|boyfriend|abuser)|escape from|fleeing|abuser|me tuer|mourir|agress\w*|agresi\w*|matarme|morir|maltrato\w*|maison d'h[ée]bergement|refuge pour femmes|il me frappe|me pega|casa de acogida|refugio para mujeres)\b|自杀|想死|不想活|轻生|自残|家暴|家庭暴力|暴力|被打|打我|虐待|性侵|强奸|危机|逃离|자살|죽고 싶|자해|폭력|학대|폭행|때려|自殺|死にたい|自傷|性暴力|殴られ/i;
function isCrisisQuery(q){return !!q&&_CRISIS_RE.test(String(q));}
const _evBuf=[];
const _EV_MAX=1000;
const _EV_KEY=SP+'Events';
// True when the maintainer opened ?debug=1. Every event from such a page is
// tagged env:'dev' server-side so it can be excluded from real-user analysis —
// see trackEvent(). Evaluated once, not per call: location.search never changes.
const _IS_DEBUG=/[?&]debug=1\b/.test(location.search);
// 2026-09-22: the maintainer's own phone and laptop were 57% of five days of
// "user" events. ?maintainer=1 marks this browser once, for good; ?maintainer=0
// unmarks it. Tagged exactly like ?debug=1 (env:'dev'), without the debug panel.
const _OWNER_KEY='lifemapMaintainer';
const _IS_OWNER=(function(){try{
  const m=/[?&]maintainer=([01])\b/.exec(location.search);
  if(m){if(m[1]==='1')localStorage.setItem(_OWNER_KEY,'1');else localStorage.removeItem(_OWNER_KEY);}
  return localStorage.getItem(_OWNER_KEY)==='1';
}catch(e){return false;}})();
const _flushThreshold=20;          // matches the burst-throttle size, but triggers
let _sinceFlush=0;                  // on the FIRST crossing rather than every Nth
// Upper bound on beacons per page load. A normal session sends 20-60; anything
// past this is either someone hammering a control or a bug, and neither is worth
// paying for or letting skew the aggregates.
const _EV_BUDGET=250;
let _evSent=0,_budgetNoted=false;
let _lastPopupSource=null;          // marker for popupclose → marker_close pairing
let _popupOpenedAt=0;               // start of the current popup, for dwell
// Privacy hook for the network payload: a search term can be a phone number,
// an address, or a name — all PII. Truncate to 24 chars and strip digit runs
// before any payload leaves the device. The local ring buffer is unaffected,
// because the data was already on the same device to begin with.
function _sanitiseQuery(q){
  if(!q)return '';
  return String(q).replace(/\d{3,}/g,'').replace(/\s+/g,' ').trim().slice(0,24);
}
function trackEvent(type,props){
  try{
    let safeProps=props;
    // Sanitise on the FIELD, not on the event name. The first version keyed off
    // type==='search_run', which meant search_empty — the event whose entire
    // purpose is to record what someone typed — uploaded the raw string, phone
    // numbers and street numbers included, in direct contradiction of the
    // privacy note. Any event carrying `q` is now cleaned, including ones that
    // do not exist yet.
    if(props&&typeof props.q==='string'){
      safeProps=Object.assign({},props,{q:isCrisisQuery(props.q)?'[crisis]':_sanitiseQuery(props.q)});
    }
    // env:'dev' marks maintainer traffic — anyone who opened the ?debug=1
    // panel, plus the smoke-test events deploy.sh fires after each release.
    // Without it these pollute every aggregate: a fake place id like "p042"
    // from a hand-rolled test POST lands in the same "most viewed places"
    // ranking as real traffic. Filter with double2 = 0 in Analytics Engine.
    if(_IS_DEBUG||_IS_OWNER)safeProps=Object.assign({env:'dev'},safeProps||{});
    // 2026-09-11: language, city and version ride outside the props so the
    // Worker can store them as their own columns — Analytics Engine has no
    // JSON functions, so anything inside `p` cannot be grouped by.
    const event={sid:getSid(),t:type,p:safeProps||{},d:Date.now(),
      l:(typeof L_==='string'?L_:''),c:(typeof CITY!=='undefined'&&CITY.key)||'',v:(typeof DATA_VERSION==='string'?DATA_VERSION:'')};
    // ---- Phase A: server side ---------------------------------------------
    // navigator.sendBeacon is fire-and-forget, survives page unload, and never
    // throws. We wrap in a Blob so the Content-Type is application/json
    // (sendBeacon defaults to text/plain, which the Worker would reject as
    // "bad json"). The fetch fallback uses keepalive:true for the same
    // reason. Failure here is non-fatal — the local copy below is the
    // ?debug=1 maintainer view, and a transient Worker outage should not
    // surface as a console error on the user's page.
    if(_evSent<_EV_BUDGET){
      _evSent++;
      try{
        const body=JSON.stringify(event);
        const blob=new Blob([body],{type:'application/json'});
        if(navigator.sendBeacon)navigator.sendBeacon('/api/event',blob);
        else fetch('/api/event',{method:'POST',body:body,keepalive:true,headers:{'Content-Type':'application/json'}}).catch(()=>{});
      }catch(e){}
    }else if(!_budgetNoted){
      // Say so once, in the data itself, so a truncated session is visible as
      // truncated rather than as a session that simply stopped doing things.
      _budgetNoted=true;
      try{
        const b=JSON.stringify({sid:getSid(),t:'budget_reached',p:{cap:_EV_BUDGET},d:Date.now()});
        if(navigator.sendBeacon)navigator.sendBeacon('/api/event',new Blob([b],{type:'application/json'}));
      }catch(e){}
    }
    // ---- Phase B / ?debug=1: local ring buffer ----------------------------
    // Same key, same throttle as before so the maintainer's debug panel keeps
    // working unchanged.
    _evBuf.push(event);
    if(_evBuf.length>_EV_MAX)_evBuf.splice(0,_evBuf.length-_EV_MAX);
    if(++_sinceFlush>=_flushThreshold){flushEvents();_sinceFlush=0;}
  }catch(e){}
}
function flushEvents(){
  // 2026-09-21: the local copy exists only for the maintainer's ?debug=1
  // panel. On an ordinary visit it was a readable history of every search
  // and card, left on a device that may be shared — so it stays in memory.
  if(!_IS_DEBUG)return;
  try{localStorage.setItem(_EV_KEY,JSON.stringify(_evBuf));}catch(e){
    // localStorage full (5 MB cap) is the only realistic cause here — a single
    // user cannot realistically type 5 MB of events, but a corrupted prior write
    // can leave the slot unusable. Drop the oldest 20% and retry once.
    try{_evBuf.splice(0,Math.floor(_evBuf.length*0.2));localStorage.setItem(_EV_KEY,JSON.stringify(_evBuf));}catch(e2){}
  }
}
// setInterval/clearInterval are deliberately not used here: the existing codebase
// only ever setTimeout chains, and the validator's unused-function audit tracks
// setInterval separately. A self-rescheduling timer does the same job.
function scheduleFlush(){setTimeout(()=>{flushEvents();if(document.visibilityState!=='hidden')scheduleFlush();},5000);}
window.addEventListener('beforeunload',flushEvents);
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')flushEvents();});
try{
  if(!_IS_DEBUG)localStorage.removeItem(_EV_KEY);   // clears what older versions left behind
  const saved=_IS_DEBUG?localStorage.getItem(_EV_KEY):null;
  if(saved){const arr=JSON.parse(saved);if(Array.isArray(arr))_evBuf.push(...arr.slice(-_EV_MAX));}
}catch(e){}
_sinceFlush=_evBuf.length%_flushThreshold;
scheduleFlush();
// Single delegated click listener captures three more event types that would
// otherwise need one trackEvent per render path: popup CTA buttons (nav/call/
// web — the strongest intent signals in the whole app), the chip "×" that
// clears a single category, and any future inline button marked data-track.
document.addEventListener('click',(e)=>{
  const t=e.target;
  if(!t||!t.closest)return;
  // Popup call/navigate/website buttons — fire BEFORE the browser navigates
  // away, which is exactly when sendBeacon (Phase A) also needs to fire.
  const cta=t.closest('a.pact-btn');
  if(cta&&cta.dataset&&cta.dataset.cta){
    trackEvent('cta_click',{kind:cta.dataset.cta,id:cta.dataset.pid,cat:cta.dataset.pcat});
  }
  // The "×" badge on an active-filter chip — its own click handler runs first
  // (it clears that one filter), but tracking here means the analytics layer
  // does not depend on the renderer re-attaching handlers after a re-render.
  // 2026-09-08 audit: this read `.chip .x` and required a data-k that was never
  // set, so it matched nothing and the event had never once fired since it was
  // written — renderActiveFilters() builds `.af-chip`. Both halves fixed: the
  // real class here, and data-kind/data-k stamped on the chips below.
  const x=t.closest('.af-chip .x');
  if(x&&x.dataset&&x.dataset.k){
    trackEvent('filter_clear_chip',{kind:x.dataset.kind||'cat',id:x.dataset.k});
  }
  // Generic inline escape hatch for one-off signals (e.g. "report an issue"
  // links, modal openers) — opt-in, not a wire to every element on the page.
  const tk=t.closest('[data-track]');
  if(tk&&(!cta||tk!==cta)&&(!x||tk!==x)&&tk.dataset.track){
    try{trackEvent(tk.dataset.track,JSON.parse(tk.dataset.trackProps||'{}'));}catch(e){}
  }
},true);
// Debug panel (?debug=1): shows counts, top lists and an export button. The
// tracker above runs regardless of the URL parameter — the panel is a viewer,
// not a gate. The maintainer added this as the only person who needs to see
// the data, and it deliberately uses position:fixed so it cannot affect the
// page underneath or be indexed by anyone who did not ask for it.
function buildDebugPanel(){
  const panel=document.createElement('div');
  panel.id='debugPanel';
  panel.style.cssText='position:fixed;right:12px;bottom:12px;width:340px;max-height:80vh;'
    +'overflow:auto;background:#111;color:#eee;font:12px/1.4 -apple-system,system-ui,sans-serif;'
    +'padding:10px;border-radius:8px;box-shadow:0 6px 20px rgba(0,0,0,.35);z-index:1150;'   // under the sheets (1200), over the map
    +'border:1px solid #333';
  panel.innerHTML='<b style="font-size:13px">click tracking · debug</b>'
    +'<div style="margin:6px 0;color:#9c9" id="dbgCount">'+_evBuf.length+' events stored</div>'
    +'<div id="dbgStats"></div>'
    +'<button id="dbgExport" style="margin-top:8px;width:48%;padding:6px;background:#0a4;color:#fff;'
    +'border:0;border-radius:4px;cursor:pointer">Export JSON</button>'
    +'<button id="dbgClear" style="margin-top:8px;width:48%;padding:6px;background:#800;color:#fff;'
    +'border:0;border-radius:4px;cursor:pointer">Clear</button>'
    +'<div id="dbgSummary" style="margin-top:8px;font:11px/1.4 ui-monospace,Menlo,monospace"></div>';
  document.body.appendChild(panel);
  const refresh=()=>{
    const dc=document.getElementById('dbgCount');if(dc)dc.textContent=_evBuf.length+' events stored';   // was the count at build time only
    const counts={};
    const cats={},regs={},queries={};
    for(const e of _evBuf){
      counts[e.t]=(counts[e.t]||0)+1;
      const p=e.p||{};
      if(e.t==='category_toggle'&&p.id){cats[p.id]=(cats[p.id]||0)+1;}
      if(e.t==='region_toggle'&&p.id){regs[p.id]=(regs[p.id]||0)+1;}
      if(e.t==='search_run'&&p.q){queries[p.q]=(queries[p.q]||0)+1;}
    }
    const top=(o)=>Object.entries(o).sort((a,b)=>b[1]-a[1]).slice(0,8);
    const fmt=(title,arr)=>arr.length?'<b>'+title+'</b><br>'+arr.map(([k,v])=>k+' <span style="color:#9c9">×'+v+'</span>').join('<br>')+'<br>':'<span style="color:#666">'+title+' (none)</span><br>';
    document.getElementById('dbgStats').innerHTML=
      '<div style="margin:6px 0">'+Object.entries(counts).sort((a,b)=>b[1]-a[1]).map(([k,v])=>k+' <span style="color:#9c9">×'+v+'</span>').join(' · ')+'</div>'
      +fmt('categories',top(cats))+fmt('regions',top(regs))+fmt('searches',top(queries));
  };
  const dbgClearEl=document.getElementById('dbgClear');
  document.getElementById('dbgExport').onclick=()=>{
    flushEvents();
    const blob=new Blob([JSON.stringify({v:1,exported:new Date().toISOString(),events:_evBuf},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download=SP+'-events-'+Date.now()+'.json';a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
  document.getElementById('dbgClear').onclick=()=>{
    // Browser-native confirm() is intentionally avoided (the codebase's audit
    // flags it as "called but undefined") and createElement panels have no UI
    // strings defined for the five languages anyway. The Clear button simply
    // asks via a button-toggle: first click arms it (red), second click fires.
    if(!dbgClearEl||dbgClearEl.dataset.armed){
      _evBuf.length=0;flushEvents();dbgClearEl.textContent='Cleared';setTimeout(()=>{
        if(dbgClearEl){dbgClearEl.dataset.armed='';dbgClearEl.textContent='Clear';}refresh();
      },1200);
      return;
    }
    dbgClearEl.dataset.armed='1';dbgClearEl.textContent='Click again to confirm';
    setTimeout(()=>{if(dbgClearEl&&dbgClearEl.dataset.armed){dbgClearEl.dataset.armed='';dbgClearEl.textContent='Clear';}},3000);
  };
  refresh();
  setTimeout(function loop(){setTimeout(loop,2000);refresh();},2000);
}
if(_IS_DEBUG)buildDebugPanel();
