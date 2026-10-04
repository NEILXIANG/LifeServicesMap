// 250 pins at the default zoom used to pile into an unreadable clump over downtown,
// and exactly-co-located places (a pharmacy and a clinic in one building) hid each
// other completely. Clustering fixes both: counts at low zoom, spiderfied pins at high.
// If the cluster plugin fails to load, markers fall back to going straight on the map.
let cluster=null;
if(typeof L.markerClusterGroup==='function'){
  cluster=L.markerClusterGroup({
    showCoverageOnHover:false,
    spiderfyDistanceMultiplier:1.6,
    maxClusterRadius:z=>z>=16?24:z>=14?45:60,
    iconCreateFunction:c=>{
      const n=c.getChildCount(),size=n<10?'s':n<40?'m':'l';
      // The number was already visible, but what it means ("N places — tap to
      // expand") lived only in the aria-label, invisible to a sighted mouse user
      // who never triggers a screen reader. A native title tooltip surfaces the
      // same sentence on hover without needing more room in a 34px circle.
      const label=UI[L_].clusterLabel(n);
      return L.divIcon({html:'<div class="kcluster '+size+'" role="img" aria-label="'+label+'" title="'+label.replace(/"/g,'&quot;')+'">'+n+'</div>',className:'',
        iconSize:null,iconAnchor:[size==='s'?17:size==='m'?21:25,size==='s'?17:size==='m'?21:25]});
    }
  });
  map.addLayer(cluster);
}
// 2026-09-11: while a bus route is selected the line is the subject and the
// places are context. Earlier versions un-clustered all 287 places and faded
// them, which read as "pin soup" and hid the line downtown. The Apple Maps
// idiom is the opposite: context is *collapsed*, not faded — the cluster
// bubbles shrink to small grey dots with no number ("there is something
// here", not "how many"), and individual pins only appear where the reader
// zooms in. Nothing migrates between layers any more, so there is nothing
// to leave behind (the Undo-after-Reset bug came from that migration).
let routeFocus=false;
function markerHome(){return cluster||map;}
function setRouteFocus(on){
  on=!!on;
  if(routeFocus===on)return;
  routeFocus=on;
  const mc=map.getContainer();
  if(mc)mc.classList.toggle('route-focus',on);
}
// A marker inside a collapsed cluster cannot just be told to open its popup —
// the cluster has to expand to it first.
// The marker a cluster zoom is currently flying toward, if any. See hideMarker().
let _focusPending=null,_focusGen=0;
function focusMarker(m,zoom,_settled){
  // 2026-09-08 audit: tapping a saved place and then changing a filter before
  // the zoom landed threw twice ("Cannot use 'in' operator to search for
  // '_leaflet_id' in undefined") and, through the global error trap, showed the
  // reader "the page hit an error — please refresh" for something they had not
  // broken. The stack puts the throw inside markercluster's own moveend handler,
  // not in this callback: zoomToShowLayer keeps a reference to the layer and
  // reads layer.__parent when the animation ends, and removing the marker from
  // the cluster in the meantime leaves that undefined. So guarding the callback
  // is too late — the marker has to survive the flight. It is held here and
  // released on arrival, and only then hidden if the filters still exclude it.
  // 2026-09-13: a zoom animation still in flight (Reset's flight home, a
  // fitBounds) lands *after* the zoom-to-marker and pulls the map away from the
  // card it just opened. Wait for it to finish, then focus.
  // The animation only starts on the next frame, so it cannot be seen
  // synchronously: look one frame later, and if it is running, wait it out.
  if(!_settled){
    requestAnimationFrame(()=>{if(map._animatingZoom)map.once('zoomend',()=>focusMarker(m,zoom,true));else focusMarker(m,zoom,true);});
    return;
  }
  // A marker whose add is queued behind a cluster animation is not in the
  // cluster yet: wait for the animation, apply the queue, then focus. (A marker
  // already in the cluster goes straight on — zoomToShowLayer waits by itself.)
  if(_clusterBusy()&&m._want===true&&!(cluster&&cluster.hasLayer(m))){
    let again=false;const go=()=>{if(again)return;again=true;focusMarker(m,zoom,true);};
    if(cluster)cluster.once('animationend',()=>setTimeout(go,0));
    map.once('zoomend',()=>setTimeout(go,0));setTimeout(go,700);
    return;
  }
  _flushMarkers();
  const gen=++_focusGen;
  if(cluster&&cluster.hasLayer(m)){
    _focusPending=m;
    let shown=false;
    // 2026-09-08, second pass: m.openPopup() is silent when the marker is still
    // inside a collapsed cluster, and a marker can stay there after the zoom —
    // two places at one address (109 Victoria St has two) sit on identical
    // coordinates, so no zoom level ever separates them. The reader tapped
    // "where do I go" and got a silent map. Whatever state the cluster ends in,
    // something has to open: the marker's own popup when it is on the map,
    // otherwise the same popup opened on the map at its coordinates.
    const standalone=()=>{
      const sp=L.popup(POPUP_OPTS).setLatLng(m.getLatLng()).setContent(popup(m.data,m.i));
      sp._kplace=m.data;sp._kidx=m.i;
      map.openPopup(sp);
      trackEvent('marker_view',{id:m.data.id,cat:m.ck,reg:m.gk,src:'clustered'});
    };
    const show=()=>{
      if(shown||gen!==_focusGen)return;   // the reader has asked for another place since
      shown=true;
      try{
        if(map.hasLayer(m)){
          m.openPopup();
          // 2026-10-04: marker changes queued while the cluster was busy (a few searches in a row leave
          // some) are applied a moment later, and can fold this marker into a cluster. Leaflet closes a
          // marker's card when the marker leaves the map, so the reader saw it flash and vanish (found
          // by tests/kelowna/guitest.py: "Show it on the map" after three searches). If that happens
          // right after opening, the same card stays open at the place instead.
          const keep=()=>{if(gen===_focusGen)try{standalone();}catch(e){}};
          m.once('remove',keep);setTimeout(()=>m.off('remove',keep),2500);
          return;
        }
        standalone();
      }catch(e){}
    };
    const settle=()=>{
      if(_focusPending!==m)return;
      _focusPending=null;
      if(!markerPasses(m))hideMarker(m);
    };
    cluster.zoomToShowLayer(m,()=>{show();settle();});
    // zoomToShowLayer only calls back once its animation ends; if the map never
    // moves, or the plugin bails early, that can be never. Never leave a marker
    // pinned to the map by a hold nothing releases — or a tap with no answer.
    setTimeout(()=>{show();settle();},1600);
    return;
  }
  // 2026-09-13: an animated setView followed by a synchronous openPopup let the
  // popup auto-pan against the pre-animation projection and land clipped above
  // the map (title, star and close button off-screen). Jump, then open.
  if(zoom)map.setView(m.getLatLng(),zoom,{animate:false});
  if(markerHome().hasLayer(m)){m.openPopup();return;}
  // The marker is filtered off the map. Tapping a saved place used to close the
  // panel, pan the map and then show nothing at all — a dead end with no
  // explanation. Open the place's own card at its location instead: the reader
  // asked for this one place, and answering does not require quietly breaking
  // the promise the filter chips make about what is on the map.
  const sp=L.popup(POPUP_OPTS).setLatLng(m.getLatLng()).setContent(popup(m.data,m.i));
  sp._kplace=m.data;sp._kidx=m.i;
  map.openPopup(sp);
  trackEvent('marker_view',{id:m.data.id,cat:m.ck,reg:m.gk,src:'hidden_by_filter'});
}
// 2026-09-24 — markercluster rewrites a spatial grid per zoom level while it
// animates a zoom, and a marker added or removed inside that window leaves an
// orphaned grid entry that makes every later add near it throw (seen at Reset
// right after a search on a CPU-throttled phone). While it animates, the wanted
// state is recorded on the marker and applied when the animation ends. "Busy"
// expires after 1.5 s so a counter the plugin fails to reset can never freeze
// the map, and a throw that still gets through is caught and repaired.
let _busySince=0,_syncT=0,_repairT=0;
function _clusterBusy(){
  const b=!!(cluster&&cluster._inZoomAnimation>0);
  if(!b){_busySince=0;return false;}
  const now=Date.now();if(!_busySince)_busySince=now;
  return now-_busySince<1500;
}
function _queueMarker(m,want){m._want=want;clearTimeout(_syncT);_syncT=setTimeout(_flushMarkers,90);}
function _flushMarkers(){
  if(_clusterBusy()){clearTimeout(_syncT);_syncT=setTimeout(_flushMarkers,90);return;}
  M.forEach(m=>{if(m._want===undefined)return;const w=m._want;delete m._want;if(w)showMarker(m);else hideMarker(m);});
}
function _clusterCall(fn){
  try{fn();}catch(e){clearTimeout(_repairT);_repairT=setTimeout(_repairCluster,120);}
}
// Rebuild the cluster from scratch: empty it, then let apply() put back exactly
// what the filters show. Only when nothing animates and no card is in flight —
// emptying the cluster under a zoomToShowLayer is the older crash in focusMarker.
function _repairCluster(){
  if(!cluster)return;
  if(_clusterBusy()||_focusPending){clearTimeout(_repairT);_repairT=setTimeout(_repairCluster,150);return;}
  try{M.forEach(m=>{delete m._want;});cluster.clearLayers();apply();}catch(e){}
}
// what apply() decided for this marker, even if the cluster has not caught up yet
function _isShown(m){return m._want!==undefined?m._want:markerHome().hasLayer(m);}
function showMarker(m){
  const h=markerHome();
  if(h===cluster&&_clusterBusy()){_queueMarker(m,true);return;}
  delete m._want;
  if(!h.hasLayer(m))_clusterCall(()=>h.addLayer(m));}
function hideMarker(m){
  // Removing the marker a cluster zoom is animating toward is what made
  // markercluster throw on arrival (see focusMarker). Hold it until the
  // animation lands; focusMarker's settle() hides it a moment later if the
  // filters still exclude it, so the filter stays honest either way.
  if(_focusPending===m)return;
  // From both homes, not just the current one: a marker that stayed in the
  // cluster while route focus moved the home to the map was left showing.
  if(map.hasLayer(m))map.removeLayer(m);
  if(cluster&&_clusterBusy()&&(cluster.hasLayer(m)||m._want!==undefined)){_queueMarker(m,false);return;}
  delete m._want;
  if(cluster&&cluster.hasLayer(m))_clusterCall(()=>cluster.removeLayer(m));}
if(cluster){cluster.on('animationend',()=>setTimeout(_flushMarkers,0));}
map.on('zoomend',()=>setTimeout(_flushMarkers,0));
P.forEach((p,idx)=>{
  // keyboard:false keeps 250 markers out of the tab order — a keyboard user used to
  // have to tab through every one of them to reach the footer.
  const m=L.marker([p.lat,p.lng],{icon:mkIcon(p.c),keyboard:false});
  m.bindPopup(popup(p,idx),POPUP_OPTS);m.ck=p.c;m.gk=p.g;m.data=p;m.i=idx;M.push(m);
  showMarker(m);
});

// P1-F — a handful of persistent place-name labels, so a reader with no mental
// map of this city yet gets a few real names to anchor on rather than only
// anonymous cluster-count bubbles. These are their own tiny, non-interactive
// markers — not the real POI marker above — because at the city-wide starting
// zoom the real markers are usually absorbed into a cluster bubble (see
// maxClusterRadius above) and a tooltip bound to a marker inside a cluster never
// renders. LANDMARKS is an optional array of place ids a city's data file may
// define (data-<city>.js); a city that defines none just gets no labels.
const landmarkMarkers=[];
if(typeof LANDMARKS!=='undefined'&&Array.isArray(LANDMARKS)){
  LANDMARKS.forEach(id=>{
    const src=P.find(p=>p.id===id);
    if(!src)return;
    const dot=L.circleMarker([src.lat,src.lng],{radius:0,opacity:0,fillOpacity:0,interactive:false,keyboard:false}).addTo(map);
    // A name may carry ⭐ markers in the data — an editorial signal for the list
    // and the popup, and noise on a map label, where the label's whole job is to
    // be a bare place name. Strip them here rather than forbidding stars in the
    // data: whether a place is starred and whether it is a landmark are two
    // independent decisions, and either can change without breaking the other.
    const label=src.n.replace(/^[\s⭐★☆]+/,'');
    dot.bindTooltip(label,{permanent:true,direction:'top',offset:[0,-4],className:'landmark-label',opacity:0.95,interactive:false});
    landmarkMarkers.push({marker:dot,lat:src.lat,lng:src.lng,name:label,id:src.id});
  });
}
if(landmarkMarkers.length){
  map.on('zoomend',()=>setTimeout(updateLandmarkLabelVisibility,340));
  // Unlike the bus-stop labels (only ever shown after fitBounds to a selected
  // route, effectively stationary), these persist through ordinary panning, so
  // they need to re-check overlap on moveend too, not only on zoom.
  map.on('moveend',()=>setTimeout(updateLandmarkLabelVisibility,340));
  setTimeout(updateLandmarkLabelVisibility,340);
}

function renderRegs(){
  const r=document.getElementById('regRow');r.innerHTML='';
  const all=document.createElement('button');all.className='reg-btn'+(aR.size===Object.keys(RI).length?' active':'');
  all.textContent=UI[L_].allReg;
  all.onclick=()=>{trackEvent('region_select_all',{});aR=new Set(Object.keys(RI));renderRegs();renderCats();renderThemes();apply();};
  r.appendChild(all);
  const allSel=aR.size===Object.keys(RI).length;
  Object.keys(RI).forEach(k=>{const n=P.filter(p=>p.g===k).length;
    const b=document.createElement('button');b.className='reg-btn'+((aR.has(k)&&!allSel)?' active':'');
    // P1-E: RI labels now carry a short geographic cue for someone with no
    // mental map of the city yet (see data-<city>.js), which is itself a
    // parenthetical — a second, differently-styled pair right after it would
    // read as noise, so the place count switches to the middot the rest of the
    // toolbar already uses for "label · detail" instead of its own parens.
    b.textContent=RI[k][L_]+' · '+n;
    b.onclick=()=>{
      let action='toggle';
      if(aR.size===Object.keys(RI).length){action='first';aR=new Set([k]);}
      else if(aR.has(k)){action='remove';aR.delete(k);
        // Deselecting the last remaining region used to leave an unrecoverable
        // empty map with an empty category panel, so falling to zero reverts to
        // "all areas" — the same guard the filter chips already had.
        if(aR.size===0){action='last_collapsed';aR=new Set(Object.keys(RI));}}
      else{action='add';aR.add(k);}
      trackEvent('region_toggle',{id:k,action:action});
      renderRegs();renderCats();renderThemes();apply();fitRegions();};
    if(REGION_HULL[k]&&window.matchMedia&&window.matchMedia('(hover:hover)').matches){
      b.onmouseenter=()=>previewRegionHull(k);
      b.onmouseleave=()=>previewRegionHull(null);
    }
    r.appendChild(b);});
}
// The count beside a theme is honest about the other two filters: it says how many
// places carry that theme *within the areas and categories currently selected*,
// which is the number the reader will actually get if they tick it. A theme with
// none left in the current view stays listed and muted, for the same reason a
// zero-count category does — "none here" and "not tracked" must not look alike.
// Ticking two themes means "both", not "either". Two reasons: it is the only
// reading under which adding a chip can never grow the result set (the same
// promise the area and category filters make), and the useful queries are
// conjunctions — "free AND indoor" on a wet Tuesday, "family AND scenic" for a
// weekend. A place with no themes at all is simply out while any theme is on.
function themeOk(d){
  if(aT.size===0)return true;
  if(!d.t||!d.t.length)return false;
  for(const k of aT){if(d.t.indexOf(k)<0)return false;}
  return true;
}
function themeCount(k){
  // Because themes combine with AND, the number worth showing is what you would
  // be left with after ticking this one — i.e. counted against the themes already
  // on, not against none of them. For a theme that is already on, that is simply
  // its current contribution, so one expression serves both states.
  const want=new Set(aT);want.add(k);
  // 2026-09-13: "open now" and the search term narrow the map, so they narrow
  // this number too — the panel promised "what you get if you tick it"
  return P.filter(p=>p.t&&aR.has(p.g)&&(aC.size===0||!!searchTerm||aC.has(p.c))
    &&[...want].every(t=>p.t.indexOf(t)>=0)&&openNowOk(p)&&(!searchTerm||matchScore(p,searchTerm)>0)).length;
}
function renderThemes(){
  const row=document.getElementById('themeRow');
  if(!row)return;
  row.innerHTML='';
  TORDER.forEach(k=>{
    const n=themeCount(k);
    const b=document.createElement('button');
    b.className='theme-btn'+(aT.has(k)?' active':'')+(n===0?' zero':'');
    b.type='button';
    b.setAttribute('aria-pressed',aT.has(k)?'true':'false');
    if(n===0)b.title=UI[L_].themeZeroHint;
    b.innerHTML='<span class="icon">'+emojiIcon(TIC[k])+'</span><span>'+themeLabel(k)+'</span><span class="cnt">('+n+')</span>';
    b.onclick=()=>{
      const action=aT.has(k)?'remove':'add';
      if(aT.has(k))aT.delete(k);else aT.add(k);
      trackEvent('theme_toggle',{id:k,action:action,active:aT.size});
      renderThemes();renderCats();apply();
    };
    row.appendChild(b);
  });
  updateThemeQuickpicks();
}
const expandedGroups=new Set(DEFAULT_OPEN_GROUPS);
function renderCats(){
  const root=document.getElementById('catGrid');root.innerHTML='';
  if(searchTerm&&aC.size){const n=document.createElement('p');n.className='cat-paused-note';n.textContent=UI[L_].catsPausedNote;root.appendChild(n);}
  GRP.forEach(grp=>{
    // Categories with nothing in the areas currently selected used to disappear
    // from this panel entirely, which reads as "this app doesn't track that" —
    // indistinguishable from a gap in the data — rather than "there's none of that
    // *here*". Every category now stays listed at every area selection, muted with
    // a (0) count when the current areas have none, so the panel's shape never
    // shifts under a reader just because they picked an area.
    const cats=grp.cats;
    const card=document.createElement('div');card.className='cat-group'+(expandedGroups.has(grp.k)?' open':'');
    const selCount=cats.filter(k=>aC.has(k)).length;
    const state=selCount===cats.length?'all':selCount===0?'none':'partial';
    const label=document.createElement('div');label.className='cat-group-label';
    label.innerHTML='<button class="grp-check '+state+'" aria-label="'+GN[grp.k][L_]+'" aria-pressed="'+(state==='all')+'">'+(state==='all'?'✓':state==='partial'?'–':'')+'</button>'
      +'<button class="grp-expand" aria-expanded="'+(expandedGroups.has(grp.k)?'true':'false')+'">'
      +'<span class="grp-name">'+GN[grp.k][L_]+'</span>'
      +(state!=='all'?'<span class="grp-count">'+selCount+'/'+cats.length+'</span>':'')
      +'<span class="car">▸</span></button>';
    label.querySelector('.grp-check').onclick=(e)=>{
      e.stopPropagation();
      const allIn=cats.length>0&&cats.every(k=>aC.has(k));
      if(!allIn)_endSearchFor('category');
      // ticking a group means "show me these"; ticking it again clears them
      if(allIn){cats.forEach(k=>aC.delete(k));}else{cats.forEach(k=>aC.add(k));}
      trackEvent('category_group_toggle',{group:grp.k,action:allIn?'clear':'select_all'});
      if(selPresets.size)presetsAdjusted=true;
      renderCats();renderThemes();apply();
    };
    label.querySelector('.grp-expand').onclick=(e)=>{
      const open=!expandedGroups.has(grp.k);
      if(open)expandedGroups.add(grp.k);else expandedGroups.delete(grp.k);
      e.currentTarget.setAttribute('aria-expanded',open?'true':'false');
      card.classList.toggle('open',open);};
    card.appendChild(label);
    const g=document.createElement('div');g.className='cat-grid';
    cats.forEach(k=>{const n=P.filter(p=>p.c===k&&aR.has(p.g)&&(aT.size===0||(p.t&&[...aT].every(t=>p.t.indexOf(t)>=0)))&&openNowOk(p)&&(!searchTerm||matchScore(p,searchTerm)>0)).length;
      const b=document.createElement('button');b.className='cat-btn'+(aC.has(k)?' active':'')+(aC.has(k)&&searchTerm?' paused':'')+(n===0?' zero':'');
      b.style.setProperty('--bc',CD[k]);
      if(n===0)b.title=UI[L_].catZeroHint;
      b.innerHTML='<span class="icon">'+IC[k]+'</span><span>'+CI[k][L_]+'</span><span class="cnt">('+n+')</span>';
      b.onclick=()=>{
        const action=aC.has(k)?'remove':'add';
        if(action==='add')_endSearchFor('category');
        if(aC.has(k))aC.delete(k);else aC.add(k);
        // a manual tweak no longer wipes the preset highlight; it marks it adjusted
        if(selPresets.size)presetsAdjusted=true;
        trackEvent('category_toggle',{id:k,action:action});
        renderCats();renderThemes();apply();};
      g.appendChild(b);});
    card.appendChild(g);
    root.appendChild(card);
  });
}
function regionLabel(){
  const u=UI[L_];
  if(aR.size===Object.keys(RI).length)return u.allReg;
  if(aR.size===1)return RI[[...aR][0]][L_];
  return u.areasN(aR.size);
}
// Search looks at everything a person might plausibly type: the name, the street
// address, the category label *in the language they are reading*, and the notes.
// Matching only name+address meant a Korean reader searching "은행" got nothing.
function noteText(d){
  const nt=d.note;
  if(!nt)return '';
  if(typeof nt==='string')return nt;
  return nt[L_]||nt.en||nt.zh||'';
}
