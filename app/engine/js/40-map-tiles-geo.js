let L_='en';
// 2026-09-22: Leaflet 1.9's map.hasLayer(undefined) throws. The cluster plugin's
// zoomToShowLayer asks exactly that when a new search hides the marker it was
// still panning to (rapid searches, pre-existing). Undefined is simply "not on
// the map".
(function(){const h=L.Map.prototype.hasLayer;L.Map.prototype.hasLayer=function(l){return !!l&&h.call(this,l);};})();
const map=L.map('map',{scrollWheelZoom:true}).setView(CITY.centre,CITY.zoom);
// Place data, search and the guide all work with no network because everything is
// in this file. Only the background imagery needs one — say so rather than leaving
// a grey rectangle that looks like a broken app.
// 2026-09-13: the map imagery is a city-data setting (CITY.tiles), not an engine
// constant: OpenStreetMap's volunteer servers blocked this site (their policy
// forbids distributed apps), CARTO's free basemaps turned out to need an API key,
// and the next provider may change its terms too. Swapping providers is now one
// object in data-kamloops.js plus the Worker's img-src. The attribution must keep
// crediting the OpenStreetMap contributors wherever the imagery uses their data.
const _T=(CITY.tiles&&CITY.tiles.url)?CITY.tiles:{url:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',attribution:'Tiles &copy; Esri',maxZoom:18};
function makeTileLayer(t){
  const o={subdomains:t.subdomains||'abc',maxZoom:t.maxZoom||18,attribution:(t.attribution||'')+' &middot; &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'};
  if(t.tileSize){o.tileSize=t.tileSize;o.zoomOffset=t.zoomOffset||0;}
  if(t.crossOrigin)o.crossOrigin=true;
  return L.tileLayer(t.url,o);
}
let tiles=makeTileLayer(_T);
// If the primary provider refuses us (quota spent, key revoked, outage), the
// fallback provider takes over after the first few failures — a blank map is
// the one thing this page must never show when the network itself is fine.
let _tileFallbackDone=false;
function swapToFallbackTiles(){
  if(_tileFallbackDone||!(CITY.tiles&&CITY.tiles.fallback&&CITY.tiles.fallback.url))return;
  _tileFallbackDone=true;
  try{map.removeLayer(tiles);}catch(e){}
  tiles=makeTileLayer(CITY.tiles.fallback);
  wireTileEvents(tiles);
  tiles.addTo(map);
  trackEvent('tile_fallback',{});
}
let tileFails=0,offlineDismissed=false,offlineCompactTimer=null;
const offlineEl=document.getElementById('offlineNote');
const offlineTextEl=document.getElementById('offlineText');
// It sits inside the map container, so without this a click on the dismiss button
// would also reach the map underneath it.
if(offlineEl&&L.DomEvent)L.DomEvent.disableClickPropagation(offlineEl);
const firstUseEl=document.getElementById('firstUse');
if(firstUseEl&&L.DomEvent){L.DomEvent.disableClickPropagation(firstUseEl);L.DomEvent.disableScrollPropagation(firstUseEl);}
let _offlineLogged=false;
// 2026-09-13 audit: the offline note and the location explainer are anchored a
// fixed 56-64px up from the map's bottom edge, but the corner they share with
// the locate control is taller than that on a phone (48px button + margin + a
// two-line attribution): the note's ✕ was under the button — tapping it opened
// the explainer — and the explainer's "Not now" was half covered. Measure the
// control and lift the notes just above it; CSS keeps the old values as fallback.
function placeMapNotes(){
  try{
    const mapEl=document.getElementById('map'),ctrl=mapEl&&mapEl.querySelector('.geo-ctrl');
    if(!mapEl||!ctrl)return;
    const m=mapEl.getBoundingClientRect(),c=ctrl.getBoundingClientRect();
    if(!c.height)return;
    mapEl.style.setProperty('--note-lift',Math.round(m.bottom-c.top+8)+'px');
  }catch(e){}
}
function offlineShowExpanded(){
  if(!offlineEl)return;
  placeMapNotes();
  if(!_offlineLogged){_offlineLogged=true;trackEvent('offline_shown',{online:navigator.onLine!==false});}
  offlineEl.hidden=false;offlineEl.classList.remove('compact');
  offlineTextEl.innerHTML=iconify(UI[L_].offlineTiles);
  clearTimeout(offlineCompactTimer);
  // Long enough to read once (5 lines max, five languages), then get out of the
  // way. Any tap on the badge — including the one that expands it — restarts this.
  offlineCompactTimer=setTimeout(()=>{if(!offlineEl.hidden)offlineEl.classList.add('compact');},6000);
}
offlineEl.addEventListener('click',(e)=>{
  if(offlineEl.classList.contains('compact')&&e.target!==document.getElementById('offlineClose')){
    offlineShowExpanded();
  }
});
document.getElementById('offlineClose').addEventListener('click',()=>{
  // How often readers actually hit the offline state — and dismiss the notice
  // rather than leave — was not being recorded anywhere.
  trackEvent('offline_note',{action:'dismiss',fails:tileFails});
  offlineDismissed=true;offlineEl.hidden=true;clearTimeout(offlineCompactTimer);});
let _tileOk=0;
function wireTileEvents(layer){
layer.on('tileerror',()=>{
  // the primary provider failing while nothing has loaded yet: try the fallback
  // before telling the reader they are offline
  tileFails++;
  if(!_tileFallbackDone&&_tileOk===0&&tileFails>=2&&navigator.onLine!==false){swapToFallbackTiles();return;}
  if(tileFails<6||offlineDismissed)return;
  // Don't pop back over a popup that made it yield a moment ago.
  if(offlineEl&&offlineEl.dataset.yielded)return;
  if(offlineEl&&offlineEl.hidden)offlineShowExpanded();
});
map.on('popupopen',e=>{
  // a phone has room for the card or the locate button, not both (it sat on the card's corner, 2026-10-20)
  document.getElementById('map').classList.add('pop-open');
  try{document.getElementById('seasonNote').hidden=true;}catch(_){}
  // The popup is the only way to reach a place's detail, so every popup-open
  // is exactly a "this place was inspected" event. The marker's index and the
  // category are on m.data / m.ck; cluster spiderfy opens synthetic layers
  // without those, so guard with m?.data. Stash the source so popupclose can
  // attribute the close to the same place and produce marker_view/close pairs.
  const m=e.popup&&e.popup._source;
  // standalone popups (favourites / guide hand-off for a filtered-out place)
  // carry their place on the popup itself; pair their close the same way
  _lastPopupSource=(m&&m.data)?m:(e.popup&&e.popup._kplace?{data:e.popup._kplace,ck:e.popup._kplace.c,gk:e.popup._kplace.g,_standalone:true}:null);
  // Popups were built once at load, so a tab left open across an evening — or
  // an installed PWA — kept saying "● Open now · until 4:30 PM" at 3 a.m. The
  // card is rebuilt at the moment it opens, so the pill and the open-now
  // filter can never disagree, and a language switch reaches standalone
  // popups too (they carry their place on the popup itself).
  try{
    if(m&&m.data)e.popup.setContent(popup(m.data,m.i));
    else if(e.popup&&e.popup._kplace)e.popup.setContent(popup(e.popup._kplace,e.popup._kidx||0));
  }catch(err){}
  try{const cb=e.popup&&e.popup._closeButton;if(cb){cb.title=UI[L_].aClosePopup;cb.setAttribute('aria-label',UI[L_].aClosePopup);}}catch(err){}
  dismissFirstUse('popup');
  if(m&&m.data){_popupOpenedAt=Date.now();trackEvent('marker_view',{id:m.data.id,cat:m.ck,reg:m.gk});}
  else if(e.popup&&e.popup._kplace)_popupOpenedAt=Date.now();
  if(offlineEl&&!offlineEl.hidden){offlineEl.hidden=true;offlineEl.dataset.yielded='1';clearTimeout(offlineCompactTimer);}
  // 2026-09-13 audit: Leaflet's auto-pan keeps a popup inside the *map*, not
  // the window — on a 1024x768 tablet the map runs past the fold, and "open it
  // on the map" from a card left the popup's action row below the screen.
  // Once it has settled, scroll the page just enough to show the whole card.
  setTimeout(()=>{try{
    if(scrollLockCount>0)return;
    const c=e.popup&&e.popup._container;if(!c||!e.popup.isOpen())return;
    const r=c.getBoundingClientRect(),vh=window.innerHeight;
    let dy=0;
    if(r.top<8)dy=r.top-8;                                   // header clipped: scroll up
    else if(r.bottom>vh-8)dy=Math.min(r.bottom-vh+8,r.top-8); // buttons clipped: scroll down, but keep the header on screen
    if(Math.abs(dy)>2)window.scrollBy({top:dy,behavior:window.matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'});
  }catch(err){}},350);
});
map.on('popupclose',()=>{
  document.getElementById('map').classList.remove('pop-open');
  setTimeout(()=>{try{renderSeason();}catch(_){}},0);
  // The popupclose event fires for every Leaflet popup — include cluster
  // spiderfies by guarding on m?.data, then the (id,cat,reg) matches the
  // marker_view for clean funnel reports. _source may be null when Leaflet
  // removes a popup without a marker, in which case there is nothing to
  // attribute the close to.
  const pe=_lastPopupSource;
  // Dwell separates "opened it" from "read it". Without it, telling a glance
  // apart from a real look needs a self-join between marker_view and
  // marker_close on (sid, id) — expensive, and impossible to do at all when a
  // session opens the same place twice.
  if(pe&&pe.data){
    const ms=_popupOpenedAt?Math.min(Date.now()-_popupOpenedAt,600000):null;
    trackEvent('marker_close',Object.assign({id:pe.data.id,cat:pe.ck,reg:pe.gk},
      ms===null?{}:{ms:ms}));
    _popupOpenedAt=0;
  }
  if(offlineEl&&offlineEl.dataset.yielded){delete offlineEl.dataset.yielded;
    if(!offlineDismissed)offlineShowExpanded();}
});
layer.on('tileload',()=>{
  _tileOk++;
  // Tiles are back: hide it, and let it speak again if the network drops later.
  if(offlineEl&&!offlineEl.hidden)offlineEl.hidden=true;
  if(offlineEl){delete offlineEl.dataset.yielded;offlineEl.classList.remove('compact');}
  clearTimeout(offlineCompactTimer);
  offlineDismissed=false;tileFails=0;
});
}
wireTileEvents(tiles);
tiles.addTo(map);
// A provider that *answers* with an image saying "invalid key" / "quota
// exceeded" never raises tileerror — the picture loads fine. So one real tile
// is fetched and its status read: anything but 2xx (MapTiler answers 403 to a
// missing origin — e.g. a file:// copy — or a spent quota) hands the map to
// the fallback provider at once. A network failure is left to tileerror.
(function probePrimaryTiles(){
  if(!(CITY.tiles&&CITY.tiles.fallback&&CITY.tiles.fallback.url)||typeof fetch!=='function')return;
  try{
    const c=map.getCenter(),zUrl=Math.max(1,Math.min(map.getZoom(),12)+(_T.zoomOffset||0));
    const n=Math.pow(2,zUrl),lat=c.lat*Math.PI/180;
    const x=Math.floor((c.lng+180)/360*n),y=Math.floor((1-Math.log(Math.tan(lat)+1/Math.cos(lat))/Math.PI)/2*n);
    const url=_T.url.replace('{z}',zUrl).replace('{x}',x).replace('{y}',y).replace('{s}',(_T.subdomains||'abc').charAt(0)).replace('{r}','');
    fetch(url,{mode:'cors',cache:'no-store',credentials:'omit'}).then(r=>{
      if(!r.ok){trackEvent('tile_probe',{status:r.status});swapToFallbackTiles();}
    }).catch(()=>{});
  }catch(e){}
})();

// P0-A — "Near me". A Leaflet control, not a header button: the header is under
// active pressure from P0-B to give the map more first-screen height, and this
// needs none of that space — it lives on the map itself, bottom-right, stacking
// above Leaflet's own attribution the way most map UIs place a locate button.
// navigator.geolocation is only ever touched from inside a click handler — never
// on load, never from a timer — and the position this receives lives in this
// closure alone: it centres the map and draws one temporary dot, and is never
// passed to trackEvent, never written to the URL, never logged anywhere.
let geoExplained=false;
try{geoExplained=localStorage.getItem(SP+'GeoExplained')==='1';}catch(e){}
let geoMarker=null,geoAccCircle=null;
// 2026-09-13 (items 10A / 11): where the reader is (only while the page is
// open, never stored), and metres between two points
let userPos=null;
function distM(a,b,c,d){const R=6371000,toR=Math.PI/180;const dLat=(c-a)*toR,dLng=(d-b)*toR;const x=Math.sin(dLat/2)**2+Math.cos(a*toR)*Math.cos(c*toR)*Math.sin(dLng/2)**2;return 2*R*Math.asin(Math.sqrt(x));}
// 2026-09-13 audit: toFixed(1) on binary halves gave 949 m -> "950 m", 950 ->
// "0.9 km", 951 -> "1.0 km" — a place 950 m away read as nearer than one at
// 949. Round to the nearest 100 m on an integer first, so the scale is monotonic.
function fmtDist(m){return m<950?Math.round(m/10)*10+' m':(Math.round(m/100)/10).toFixed(1)+' km';}
function distFromUser(p){return userPos?distM(userPos[0],userPos[1],p.lat,p.lng):null;}
const NEAR_M=1200;   // ~15 minutes on foot
let nearOnly=false;
function nearOk(p){return !nearOnly||(userPos&&distFromUser(p)<=NEAR_M);}
// nearest stop across all routes, with every route that serves a stop of that
// name within 80 m (exchanges list the same bay under several routes)
let _stopIndex=null;
function nearestStop(p){
  if(typeof BR==='undefined')return null;
  if(!_stopIndex){_stopIndex=[];Object.keys(BR).forEach(k=>{(BR[k].s||[]).forEach(st=>_stopIndex.push({k:k,n:st[0],lat:st[1],lng:st[2]}));});}
  let best=null;
  _stopIndex.forEach(st=>{const d=distM(p.lat,p.lng,st.lat,st.lng);if(!best||d<best.d)best={d:d,st:st};});
  if(!best||best.d>800)return null;
  const routes=[];_stopIndex.forEach(st=>{if(routes.indexOf(st.k)<0&&distM(best.st.lat,best.st.lng,st.lat,st.lng)<=80)routes.push(st.k);});
  routes.sort((a,b)=>parseInt(a,10)-parseInt(b,10));
  return {name:best.st.n,d:best.d,routes:routes};
}
const GeoControl=L.Control.extend({
  options:{position:'bottomright'},
  onAdd:function(){
    const div=L.DomUtil.create('div','geo-ctrl');
    const btn=L.DomUtil.create('button','geo-btn',div);
    btn.type='button';
    btn.innerHTML='<svg width="21" height="21" viewBox="0 0 24 24" aria-hidden="true">'
      +'<circle cx="12" cy="12" r="3" fill="currentColor"/>'
      +'<path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>'
      +'</svg><span class="geo-btn-tx"></span>';
    // Leaflet controls sit inside the map's own click/drag surface, so without
    // this a tap here would also reach the map underneath (panning it, or, worse,
    // landing on whatever marker happens to be behind bottom-right at the time).
    L.DomEvent.disableClickPropagation(div);
    L.DomEvent.on(btn,'click',onGeoClick);
    this._btn=btn;
    return div;
  }
});
const geoControl=new GeoControl();
geoControl.addTo(map);
const geoNoteEl=(function(){
  const d=document.createElement('div');
  d.id='geoNote';
  d.className='geo-note';
  d.hidden=true;
  d.innerHTML='<p id="geoNoteText"></p><div class="geo-note-act">'
    +'<button type="button" id="geoNoteOk" class="geo-note-btn"></button>'
    +'<button type="button" id="geoNoteCancel" class="geo-note-btn"></button></div>';
  document.getElementById('map').appendChild(d);
  if(L.DomEvent)L.DomEvent.disableClickPropagation(d);
  return d;
})();
function onGeoClick(){
  if(!('geolocation' in navigator)){
    geoMessage(UI[L_].geoUnsupported,'geoUnsupported');
    trackEvent('geo_locate',{result:'unsupported'});
    return;
  }
  // The explanation is shown once, ever (per browser) — not once per session —
  // because its whole job is to say what happens *before* the browser's own
  // permission prompt appears the first time. Once that has happened, a second
  // "here's what this does" only stands between a returning reader and the map.
  if(!geoExplained){showGeoExplain();return;}
  runGeolocate();
}
function showGeoExplain(){
  const u=UI[L_];
  _geoNoteKey='explain';
  document.getElementById('geoNoteText').textContent=u.geoExplainText;
  const ok=document.getElementById('geoNoteOk'),cancel=document.getElementById('geoNoteCancel');
  ok.textContent=u.geoExplainOk;ok.classList.add('primary');ok.hidden=false;
  cancel.textContent=u.geoExplainCancel;
  ok.onclick=()=>{
    geoExplained=true;
    try{localStorage.setItem(SP+'GeoExplained','1');}catch(e){}
    geoNoteEl.hidden=true;
    runGeolocate();
  };
  cancel.onclick=()=>{geoNoteEl.hidden=true;_geoNoteKey=null;trackEvent('geo_locate',{result:'explain_declined'});};
  geoNoteEl.classList.remove('err');
  placeMapNotes();
  geoNoteEl.hidden=false;
}
let _geoNoteKey=null;   // which note is on screen, so a language switch can redraw it
function geoMessage(msg,key){
  _geoNoteKey=key||null;
  const ok=document.getElementById('geoNoteOk'),cancel=document.getElementById('geoNoteCancel');
  document.getElementById('geoNoteText').textContent=msg;
  ok.hidden=true;
  cancel.textContent=UI[L_].geoDismiss;
  cancel.onclick=()=>{geoNoteEl.hidden=true;};
  geoNoteEl.classList.add('err');
  placeMapNotes();
  geoNoteEl.hidden=false;
}
function runGeolocate(){
  const btn=geoControl._btn;
  btn.classList.add('loading');
  navigator.geolocation.getCurrentPosition(
    pos=>{
      btn.classList.remove('loading');
      const lat=pos.coords.latitude,lng=pos.coords.longitude;
      if(geoMarker)map.removeLayer(geoMarker);
      if(geoAccCircle)map.removeLayer(geoAccCircle);
      // A plain dot looked like just another place marker, so a first-time tap
      // on Near Me didn't obviously read as "this one is me". A pulsing ring
      // plus a permanent, translated "Your location" tooltip make that
      // unambiguous without the reader having to guess what a lone dot means.
      const hereIcon=L.divIcon({className:'geo-here-icon',
        html:'<div class="geo-here"><div class="geo-here-pulse"></div><div class="geo-here-dot"></div></div>',
        iconSize:[22,22],iconAnchor:[11,11]});
      geoMarker=L.marker([lat,lng],{icon:hereIcon,keyboard:false,zIndexOffset:1000}).addTo(map);
      geoMarker.bindTooltip(UI[L_].geoHereLabel,
        {permanent:true,direction:'top',offset:[0,-10],className:'geo-here-tip'});
      const acc=Math.min(pos.coords.accuracy||0,2000);
      if(acc>30)geoAccCircle=L.circle([lat,lng],{radius:acc,color:'#1a73e8',weight:1,fillColor:'#1a73e8',fillOpacity:.08}).addTo(map);
      map.setView([lat,lng],15);
      userPos=[lat,lng];
      // distances appear in open cards and the favourites list from now on
      try{M.forEach(m=>m.setPopupContent(popup(m.data,m.i)));if(map._popup&&map._popup._kplace)map._popup.setContent(popup(map._popup._kplace,map._popup._kidx||0));renderFavList();updateNearQuickpick();applyQuickPickOrder();if(nearOnly)apply();}catch(e){}
      const ann=document.getElementById('a11yAnnounce');
      if(ann)ann.textContent=UI[L_].geoFoundAnnounce;
      trackEvent('geo_locate',{result:'success'});
    },
    err=>{
      btn.classList.remove('loading');
      const key=err.code===1?'geoDenied':err.code===2?'geoUnavailable':'geoTimeout';
      geoMessage(UI[L_][key],key);
      trackEvent('geo_locate',{result:key==='geoDenied'?'denied':key==='geoUnavailable'?'unavailable':'timeout'});
    },
    {enableHighAccuracy:false,timeout:8000,maximumAge:60000}
  );
}

// Leaflet's zoom control sits above popups and outside their pane, so on a wide
// screen it clipped the place name — the one line in the popup that matters most.
// Padding the auto-pan makes Leaflet shift the map until the popup clears it.
// On a phone the control is hidden altogether (pinch to zoom), and there the same
// padding would push the popup off the right edge instead — so it is conditional.
// 2026-09-13 audit: the route bar (.bus-indicator, top:10px) sits over the map
// too, so while a route is drawn the popup has to clear it as well — otherwise
// choosing a route from a place card laid the bar over the card's name, ★ and ✕.
function busBarH(){const bi=document.getElementById('busIndicator');return (bi&&bi.classList.contains('show'))?bi.offsetHeight+10:0;}
function panPad(){return L.point(window.innerWidth>600?58:14,12+busBarH());}
// The longest note runs to 287 characters, and French and Spanish come out longer
// still. Uncapped, that popup was 456px tall on a 568px phone — most of the screen,
// with its top edge outside the map. Leaflet's own maxHeight adds an internal scroll
// and keeps the name and the action buttons where they belong.
// Basing this on the viewport was wrong: on a short screen the map is a fraction of
// it, and a popup taller than the map can never satisfy autoPan — Leaflet kept
// panning and the popup closed itself about 300ms after opening. Measure the map.
function popMaxH(){
  const el=document.getElementById('map');
  const h=el?el.getBoundingClientRect().height:window.innerHeight*0.6;
  // ~86px goes to the popup's own wrapper padding, tip and close button.
  return Math.max(150,Math.min(440,Math.round(h-86-busBarH())));
}
const POPUP_OPTS={autoPanPaddingTopLeft:panPad(),autoPanPaddingBottomRight:L.point(14,14),
                  maxHeight:popMaxH()};
// Leaflet copies options into each popup at bind time, so a later change has to be
// pushed to the bound popups rather than just to POPUP_OPTS.
function syncPanPad(){
  const pad=panPad(),mh=popMaxH();
  POPUP_OPTS.autoPanPaddingTopLeft=pad;POPUP_OPTS.maxHeight=mh;
  M.forEach(m=>{const pu=m.getPopup();
    if(pu){pu.options.autoPanPaddingTopLeft=pad;pu.options.maxHeight=mh;}});
}
