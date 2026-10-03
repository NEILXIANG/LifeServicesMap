let panelMode='area';
let selectedRoute=null;
const busLayer=L.layerGroup().addTo(map);
// Leaflet draws vector lines in overlayPane (z 400), under markerPane (z 600):
// with every place un-clustered in route mode the line vanished exactly where
// riders need it — downtown and at the exchanges. Own panes put the line over
// the pins and the stop dots over the line; tooltips (650) and popups (700)
// still win.
map.createPane('routePane').style.zIndex=640;
// ---- where an area is (2026-09-11) ------------------------------------------
// "North Shore (north riverbank)" is a name; a reader new to the city has no
// picture for it. Each area's places already say where it is: their convex
// hull, drawn as a faint tinted shape while that area is selected (and, on a
// mouse, while its button is hovered), shows the extent without any hand-drawn
// boundary that could be wrong. 'ot' (everywhere else) is too scattered for a
// shape and is left out.
map.createPane('hullPane').style.zIndex=395;
function convexHull(pts){
  pts=pts.slice().sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
  if(pts.length<3)return pts;
  const cross=(o,a,b)=>(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);
  const lower=[];for(const p of pts){while(lower.length>=2&&cross(lower[lower.length-2],lower[lower.length-1],p)<=0)lower.pop();lower.push(p);}
  const upper=[];for(let i=pts.length-1;i>=0;i--){const p=pts[i];while(upper.length>=2&&cross(upper[upper.length-2],upper[upper.length-1],p)<=0)upper.pop();upper.push(p);}
  upper.pop();lower.pop();return lower.concat(upper);
}
const REGION_HULL={};
Object.keys(RI).forEach(k=>{
  if(k==='ot')return;
  const pts=P.filter(p=>p.g===k).map(p=>[p.lat,p.lng]);
  const hull=convexHull(pts);
  if(hull.length<3)return;
  REGION_HULL[k]=L.polygon(hull,{pane:'hullPane',color:'#0b6be0',weight:1.5,dashArray:'5 5',fillColor:'#0b6be0',fillOpacity:.08,interactive:false,className:'region-hull'});
});
let _hullShown=new Set(),_hullPreview=null;
function updateRegionHulls(){
  const total=Object.keys(RI).length;
  const want=new Set(_hullPreview?[_hullPreview]:(aR.size<total?[...aR]:[]));
  Object.keys(REGION_HULL).forEach(k=>{
    const on=want.has(k), has=map.hasLayer(REGION_HULL[k]);
    if(on&&!has)REGION_HULL[k].addTo(map);
    if(!on&&has)map.removeLayer(REGION_HULL[k]);
  });
  _hullShown=want;
}
function previewRegionHull(k){_hullPreview=k;updateRegionHulls();}
// what you picked is what you see: the map moves to the chosen area(s)
function fitRegions(){
  const total=Object.keys(RI).length;
  if(aR.size>=total)return;
  let b=null;
  [...aR].forEach(k=>{const h=REGION_HULL[k];if(!h)return;b=b?b.extend(h.getBounds()):h.getBounds();});
  if(b&&b.isValid())map.fitBounds(b,{padding:[30,30],maxZoom:14});
}
map.createPane('stopPane').style.zIndex=645;
let busStopMarkers=[];

function busIcon(color){
  return L.divIcon({className:'',html:'<div style="width:10px;height:10px;border-radius:50%;background:'+color+';border:2px solid #fff;box-shadow:0 0 0 1px '+color+';"></div>',iconSize:[14,14],iconAnchor:[7,7]});
}
function isKeyStop(name){ return CITY.keyStop.test(name); }
function labelRect(el,pt,dx,dy){
  // Leaflet centres a stop tooltip above its point. Measure the element we are
  // actually going to show rather than assuming a fixed radius: "Lansdowne Exch
  // Bay I" needs roughly three times the clearance of "8th St", and a single
  // fixed distance can only be right for one of them.
  const w=el?el.offsetWidth:60, h=el?el.offsetHeight:14;
  const ox=dx||0, oy=dy||0;
  return {l:pt.x-w/2-2+ox, r:pt.x+w/2+2+ox, t:pt.y-h-8+oy, b:pt.y+2+oy};
}
// Where a label may sit, in order of preference: directly above the point (what
// Leaflet does), then below it, then out to either side. Offsets are relative to
// the default box, and depend on the label's own size, so they are computed per
// element rather than fixed here.
function labelSlots(el){
  const w=el?el.offsetWidth:60, h=el?el.offsetHeight:14;
  return [[0,0],[0,h+14],[w/2+14,h/2+6],[-(w/2+14),h/2+6]];
}
function rectsClear(a,b){
  return a.r<b.l||b.r<a.l||a.b<b.t||b.b<a.t;
}
function labelObstacles(){
  // The labels also have to clear the place-cluster bubbles: a stop name sitting
  // on top of a "59" is unreadable in both directions, and this layer was never
  // considered before.
  //
  // 2026-09-10: individual place pins were never in this set at all, so a label
  // could sit squarely on a pharmacy pin and the algorithm called that clear.
  // They are obstacles now — except while a bus route is selected, where they
  // have been dimmed to 30% and are deliberately background. Treating faded
  // context as something to dodge would take the stop names back down to two.
  const sel=routeFocus
    ? ''                                    // collapsed grey dots are background, not obstacles
    : '.kcluster, .leaflet-marker-icon.marker-cluster, .leaflet-marker-icon.kpin';
  const out=[];
  // the floating route bar and first-use card cover the top of the map
  document.querySelectorAll('#busIndicator.show, #firstUse:not([hidden])').forEach(el=>{
    const r=el.getBoundingClientRect();if(!r.width)return;
    const box=map.getContainer().getBoundingClientRect();
    out.push({l:r.left-box.left,r:r.right-box.left,t:r.top-box.top,b:r.bottom-box.top});
  });
  if(sel)document.querySelectorAll(sel).forEach(el=>{
    const r=el.getBoundingClientRect();
    if(!r.width)return;
    const box=map.getContainer().getBoundingClientRect();
    out.push({l:r.left-box.left-2,r:r.right-box.left+2,t:r.top-box.top-2,b:r.bottom-box.top+2});
  });
  return out;
}
// Shared by bus-stop labels and the P1-F landmark labels: given a list of
// {marker,lat,lng,name} items each already carrying a permanent tooltip, decide
// which currently have room and hide the rest. `forceFn(item,idx,items)` marks
// items that must always try to claim space first (bus routes use it for the
// first/last stop and any named terminus; landmarks pass none — with only a
// handful of them, none needs to jump the queue over the others).
// `slots` (2026-09-09): when true, a label blocked above its point may try below
// it and then either side before giving up. It exists because re-picking the six
// landmarks exposed the flaw: the names most worth showing are downtown, which is
// exactly where the cluster bubbles are densest, so a single fixed position meant
// the two best labels — the hospital and the North Shore library — never drew at
// all. Off for bus stops: there are dozens of them, their current placement is
// covered by its own checks, and a label that moves is only worth the risk where
// each individual name was chosen by hand.
// `allowFn` (2026-09-10): decides which non-forced items are even candidates.
// Sixty stop names cannot all be on screen and no real transit map tries. But
// "forced only" is not the answer either — a loop route's first and last stop
// are the same place, so route 6 came out with a single name on it. What a
// reader needs zoomed out is a handful of names *spread along the line*, so the
// caller samples at a stride and this only has to honour the choice.
function computeLabelVisibility(items,forceFn,slots,allowFn){
  if(!items.length)return;
  // Measure first, decide second. A label hidden by the previous pass reports
  // offsetWidth 0, so measuring in place made every hidden label look tiny,
  // "fit" anywhere, and reappear on top of its neighbour — the labels oscillated
  // instead of settling. Everything is made visible for the measuring pass and
  // only then hidden.
  const entries=[];
  items.forEach((item,idx)=>{
    const tt=item.marker.getTooltip();
    const el=tt&&tt.getElement();
    if(el)el.style.display='';
    let pt=null;
    try{pt=map.latLngToContainerPoint([item.lat,item.lng]);}catch(e){}
    entries.push({idx,el,pt,txt:item.name,force:forceFn?forceFn(item,idx,items):false,
                  allow:allowFn?allowFn(item,idx,items):true});
  });
  entries.forEach(e=>{
    if(!e.el||!e.pt){e.rect=null;return;}
    e.rect=labelRect(e.el,e.pt);
  });
  // Against another label, any touch at all is disqualifying — two names on top of
  // each other are unreadable in both directions. Against a cluster bubble the bar
  // is lower: the bubbles are big and numerous, and vetoing every label that merely
  // grazes one left just 3 of 31 names on screen. Only a bite out of the middle of
  // the text actually costs legibility, so clusters block a label at 30% coverage.
  const overlapFrac=(a,b)=>{
    const w=Math.min(a.r,b.r)-Math.max(a.l,b.l), h=Math.min(a.b,b.b)-Math.max(a.t,b.t);
    if(w<=0||h<=0)return 0;
    const area=(a.r-a.l)*(a.b-a.t);
    return area>0?(w*h)/area:0;
  };
  const clusters=labelObstacles();
  const show=new Set();
  // Forced items are the anchors a reader orients by, so they always claim their
  // space first — processing in list order used to let an ordinary item take a
  // slot a forced one then drew over.
  const placed=[];
  // 2026-09-13: a label straddling the map's edge is clipped to a fragment
  // ("…t Park"); a slot that does not fit inside the container is no slot
  let W=Infinity,H=Infinity;try{const sz=map.getSize();W=sz.x;H=sz.y;}catch(e){}
  const inside=r=>r.l>=0&&r.t>=0&&r.r<=W&&r.b<=H;
  const clear=r=>inside(r)&&placed.every(t=>rectsClear(r,t));    // never touch another label, never hang off the edge
  // A loop bus route can pass the same exchange bay twice, so two forced labels
  // carry the identical name and land on top of each other. The second one adds
  // nothing a reader can use, so it is dropped rather than smudged over the first.
  //
  // 2026-09-10: forced labels used to be exempt from overlap entirely, on the
  // reasoning that they are the anchors and must win. They must win *against
  // ordinary labels* — which they still do, by being placed first — but two
  // anchors printed over each other are two labels nobody can read, and at wide
  // zoom on a 60-stop route that is exactly what happened. A forced label now
  // takes another slot if its first is taken, and stands down if none is free.
  entries.forEach(e=>{
    if(!e.force||!e.rect)return;
    const dup=placed.some(t=>!rectsClear(e.rect,t)&&t.txt===e.txt);
    if(dup)return;
    const cand=slots&&e.el?labelSlots(e.el):[[0,0]];
    for(let i=0;i<cand.length;i++){
      const r=i===0?e.rect:labelRect(e.el,e.pt,cand[i][0],cand[i][1]);
      if(!clear(r))continue;
      r.txt=e.txt; e.off=cand[i]; show.add(e.idx); placed.push(r); return;
    }
  });
  const fits=r=>clear(r)&&!clusters.some(c=>overlapFrac(r,c)>0.30);
  // 2026-09-13 audit: 30% of the *label* let a wide label sit fully over a small
  // bubble and hide its count ("68" under "North Kamloops Library"). Slots that
  // also leave every bubble's own count readable are tried first; only when a
  // landmark has no such slot does it take one the old rule allowed — a name
  // over a number still beats no name at all on a 390px opening view.
  const fitsWell=r=>fits(r)&&!clusters.some(c=>overlapFrac(c,r)>0.35);
  entries.forEach(e=>{
    if(e.force||!e.rect||!e.allow)return;
    const cand=slots&&e.el?labelSlots(e.el):[[0,0]];
    const rects=cand.map((c,i)=>i===0?e.rect:labelRect(e.el,e.pt,c[0],c[1]));
    for(const ok of [fitsWell,fits]){
      for(let i=0;i<cand.length;i++){
        const r=rects[i];
        if(!ok(r))continue;
        e.off=cand[i];placed.push(r);show.add(e.idx);return;
      }
    }
  });
  entries.forEach(e=>{
    if(!e.el)return;
    e.el.style.display=show.has(e.idx)?'':'none';
    // Leaflet positions the tooltip with a transform, so the chosen slot is
    // applied as a margin on top of it — no fighting over the same property, and
    // it is re-set from scratch on every pass rather than accumulating.
    e.el.style.marginLeft=(e.off?e.off[0]:0)+'px';
    e.el.style.marginTop=(e.off?e.off[1]:0)+'px';
  });
}
// Which stop names are worth the space depends on how close the reader is, and
// the two questions are different ones. Zoomed out they are asking "where does
// this line go" — the ends and the exchanges answer that and forty more names
// only obscure it. Zoomed in they are asking "which stop do I get off at", and
// then every name earns its place.
const STOP_LABEL_ALL_ZOOM=16;   // at and above this, every stop is a candidate
const STOP_LABEL_TARGET=8;      // out beyond that, roughly this many names, spread out
function updateStopLabelVisibility(){
  const z=map.getZoom();
  const n=busStopMarkers.length;
  // Zoomed in, the reader is asking "which stop do I get off at" and every name
  // earns its place. Zoomed out they are asking "where does this line go", and
  // eight names along its length answer that better than sixty fighting for room.
  const stride=(z>=STOP_LABEL_ALL_ZOOM||n<=STOP_LABEL_TARGET)
    ? 1 : Math.ceil(n/STOP_LABEL_TARGET);
  computeLabelVisibility(busStopMarkers,
    (item,idx,items)=>idx===0||idx===items.length-1||isKeyStop(item.name),
    true,                                   // a blocked name may try below or to the side
    (item,idx)=>stride===1||idx%stride===0);
}
function updateLandmarkLabelVisibility(){
  computeLabelVisibility(landmarkMarkers,null,true);
}
map.on('zoomend',()=>setTimeout(updateStopLabelVisibility,340));
let _busQ='';
function renderBusList(){
  const root=document.getElementById('busList');root.innerHTML='';
  const u=UI[L_];
  const q=_busQ.trim().toLowerCase();
  let shown=0;
  Object.keys(BR).sort((a,b)=>Number(a)-Number(b)).forEach(k=>{
    const r=BR[k];
    // a route matches by its name, its number, or any stop along it
    let stopHit=null;
    if(q){
      if(!(k===q||r.n.toLowerCase().indexOf(q)>=0)){
        const st=r.s.find(x=>String(x[0]).toLowerCase().indexOf(q)>=0);
        if(!st)return;
        stopHit=st[0];
      }
    }
    shown++;
    const item=document.createElement('button');item.className='bus-item'+(selectedRoute===k?' active':'');
    item.innerHTML='<span class="dot" style="background:'+r.co+'"></span><span class="rt-num">'+k+'</span><span class="rt-name">'+esc(r.n)+(stopHit?'<span class="rt-stop">↳ '+esc(stopHit)+'</span>':'')+'</span><span class="rt-count">'+u.stopsN(r.s.length)+'</span>';
    item.onclick=()=>selectRoute(selectedRoute===k?null:k);
    root.appendChild(item);
  });
  if(q&&!shown){const e=document.createElement('div');e.className='fav-empty';e.textContent=u.busSearchNone;root.appendChild(e);}
  const inp=document.getElementById('busSearch');
  if(inp&&!inp.dataset.wired){
    inp.dataset.wired='1';
    inp.oninput=e=>{if(e&&e.isComposing)return;_busQ=inp.value;renderBusList();};
    inp.addEventListener('compositionend',()=>{_busQ=inp.value;renderBusList();});
  }
  if(inp)inp.placeholder=u.busSearchPh;
}
function fmtBusTime(t){
  const u=UI[L_];
  let [h,m]=t.split(':').map(Number);
  let nextDay=false;
  if(h>=24){h-=24;nextDay=true;}
  const hh=String(h).padStart(2,'0');
  const timeStr=hh+':'+String(m).padStart(2,'0');
  return nextDay?(u.nextDayPrefix||'')+timeStr:timeStr;
}
function routeInfoHtml(key){
  const r=BR[key],u=UI[L_];
  return '<div class="pr"><span class="pl">'+u.lStops+'</span>'+u.stopsN(r.s.length)+'</div>'
    +'<div class="pr"><span class="pl">'+u.lService+'</span>'+fmtBusTime(r.f)+' – '+fmtBusTime(r.l)+'</div>'
    +'<div class="pr"><span class="pl">'+u.lFare+'</span>'+u.busFareText+'</div>'
    +'<div class="pn">'+u.busCaveat+'</div>';
}
function renderRoute(key,fit){
  if(key&&!owns(BR,key))key=null;
  selectedRoute=key;
  busLayer.clearLayers();
  busStopMarkers=[];
  const ind=document.getElementById('busIndicator');
  // Before anything is drawn: put the place layer into the background (or take
  // it out again), so the labels below are placed against the picture the
  // reader will actually see rather than the one that is about to change.
  setRouteFocus(!!key);
  if(key){
    const r=BR[key],u=UI[L_];
    const bounds=[];
    const lineHtml='<div class="tag" style="background:'+r.co+'">'+u.routeLabel(key)+'</div><div class="pt">'+r.n+'</div>'+routeInfoHtml(key);
    if(r.p&&r.p.length){
      // a white casing under the coloured line keeps it readable over any tile
      L.polyline(r.p,{color:'#fff',weight:8,opacity:0.9,lineJoin:'round',pane:'routePane',className:'stop-casing',interactive:false}).addTo(busLayer);
      L.polyline(r.p,{color:r.co,weight:4,opacity:0.95,lineJoin:'round',pane:'routePane'}).bindPopup(lineHtml,POPUP_OPTS).addTo(busLayer);
      r.p.forEach(pt=>bounds.push(pt));
    }
    r.s.forEach(([name,lat,lng],idx)=>{
      const m=L.marker([lat,lng],{icon:busIcon(r.co),pane:'stopPane'});
      const seq='<div class="pr"><span class="pl">'+u.lStopSeq+'</span>'+u.stopSeqN(idx+1,r.s.length)+'</div>';
      m.bindPopup('<div class="tag" style="background:'+r.co+'">'+u.routeLabel(key)+'</div><div class="pt">'+name+'</div><div class="pr">'+r.n+'</div>'+seq+routeInfoHtml(key),POPUP_OPTS);
      // 2026-09-10: this was direction:'right', but labelRect() models every
      // label as centred *above* its point — the geometry the avoidance pass
      // reasons about was roughly a label's width off from where the label
      // actually was, so it declared collisions clear and clear ones colliding.
      // Both label families now sit above their point, so one model is true for
      // both, and labelSlots() moves them from there when the space is taken.
      m.bindTooltip(name,{permanent:true,direction:'top',offset:[0,-4],className:'stop-label',opacity:0.95});
      m.addTo(busLayer);
      busStopMarkers.push({marker:m,lat,lng,name});
      bounds.push([lat,lng]);
    });
    if(fit&&bounds.length){
      map.fitBounds(bounds,{padding:[40,40]});
      map.once('moveend',()=>setTimeout(updateStopLabelVisibility,340));
    }
    updateStopLabelVisibility();
    ind.innerHTML='<span>'+ico('bus')+u.routeLabel(key)+' '+r.n+u.parenL+u.stopsN(r.s.length)+u.parenR+'</span><span class="bi-hint">'+esc(u.routeModeHint)+'</span><button class="x" type="button" aria-label="'+esc(u.routeExit)+'" title="'+esc(u.routeExit)+'">✕</button>';
    // 2026-09-08 audit: the markup ships with a static `hidden` attribute that
    // nothing ever cleared. .bus-indicator.show{display:flex} is an author rule,
    // so it beat [hidden] and the bar appeared on screen — but `hidden` also
    // takes an element out of the accessibility tree, so this role="status"
    // aria-live region announced the selected route to nobody. Keep the
    // attribute in step with the class so both audiences agree.
    ind.hidden=false;
    ind.classList.add('show');
    ind.querySelector('.x').onclick=()=>selectRoute(null);
  }else{
    ind.classList.remove('show');ind.innerHTML='';ind.hidden=true;
  }
  // the bar changes how much of the map a popup may use (see panPad): push the
  // new padding to every bound popup, and nudge an open one out from under it
  syncPanPad();
  relayoutOpenPopup();
  renderBusList();
  updateResetState();
  renderActiveFilters();
  updateStatusRoute();
  writeURLState();
}
// The status line says "279 places" whether or not a route is drawn; the route
// is appended so the two numbers a reader sees (places, stops) both have a name.
function updateStatusRoute(){
  const st=document.getElementById('statusText');if(!st)return;
  const u=UI[L_];
  // count · route · region — the route before the region, so it is the region
  // (already shown on the Area button) that gets clipped on a narrow phone
  const count=st.dataset.count||st.textContent, region=st.dataset.region||'';
  st.textContent=count+(selectedRoute?' · 🚌 '+u.routeLabel(selectedRoute):'')+(region?' · '+region:'');
}
function selectRoute(key,opts){
  trackEvent('route_select',{id:key||selectedRoute,action:key?'select':'deselect',src:opts&&opts.src||undefined});
  // from a place card the reader is looking at *this* place; drawing the line
  // without re-fitting keeps the card open (a zoom-out re-clusters the marker)
  renderRoute(key,!(opts&&opts.keepView));
  closePanel();
  try{renderSeason();}catch(e){}
  if(key)dismissFirstUse('route');
}
