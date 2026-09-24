#!/usr/bin/env python3
"""2026-09-24 — the marker cluster is never changed mid-animation.

Found by the multilingual test run, not caused by translation: 1,300 searches in
a row across six languages threw once, and with the CPU slowed to a mid-range
phone's (x4) two runs in four threw — with a realistic 300 ms between actions,
at Reset (resetAll → apply → showMarker):

    TypeError: Cannot read properties of undefined (reading '_zoom' / 'x')
      at markercluster _addLayer / DistanceGrid._sqDist  ← showMarker ← apply

markercluster keeps a spatial grid per zoom level and rewrites it while it
animates a zoom (a single-result search flies to the place; Reset flies home;
fitBounds). Adding or removing a marker inside that window leaves an entry in
the grid whose parent is gone, and every later add near it throws. apply() stops
at the first throw, so the count, the empty state and the address bar were left
describing the previous search.

Now, while the cluster (or the map) is animating a zoom, showMarker/hideMarker
record what the marker should be and change nothing; the recorded state is
applied as soon as the animation ends. The count apply() reports is unaffected —
it never depended on the cluster. Three safety valves:
  - "busy" expires after 1.5 s, so a counter markercluster fails to reset can
    never freeze the map;
  - focusMarker waits for the same window before it asks the cluster for a
    marker, so a single-result search during an animation still opens its card;
  - if the cluster still throws, the exception is caught, apply() finishes, and
    the cluster is rebuilt from scratch once nothing is animating or in flight.
"""
import sys
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:100], n))
    s = s.replace(old, new)

rep("""function showMarker(m){const h=markerHome();if(!h.hasLayer(m))h.addLayer(m);}
function hideMarker(m){
  // Removing the marker a cluster zoom is animating toward is what made
  // markercluster throw on arrival (see focusMarker). Hold it until the
  // animation lands; focusMarker's settle() hides it a moment later if the
  // filters still exclude it, so the filter stays honest either way.
  if(_focusPending===m)return;
  // From both homes, not just the current one: a marker that stayed in the
  // cluster while route focus moved the home to the map was left showing.
  if(map.hasLayer(m))map.removeLayer(m);
  if(cluster&&cluster.hasLayer(m))cluster.removeLayer(m);}""",
"""// 2026-09-24 — markercluster rewrites a spatial grid per zoom level while it
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
  if(cluster&&cluster.hasLayer(m))_clusterCall(()=>cluster.removeLayer(m));}""")

# focusMarker: never ask the cluster for a marker whose add is still queued
rep("""  const gen=++_focusGen;
  if(cluster&&cluster.hasLayer(m)){""",
"""  // A marker whose add is queued behind a cluster animation is not in the
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
  if(cluster&&cluster.hasLayer(m)){""")

# the queue is also flushed the moment an animation ends, not only on the timer
rep("""P.forEach((p,idx)=>{
  // keyboard:false keeps 250 markers out of the tab order""",
"""if(cluster){cluster.on('animationend',()=>setTimeout(_flushMarkers,0));}
map.on('zoomend',()=>setTimeout(_flushMarkers,0));
P.forEach((p,idx)=>{
  // keyboard:false keeps 250 markers out of the tab order""")

# the two places that read "which markers are on the map" straight after apply()
# ask for what apply() decided, not for what the cluster has caught up with yet
rep("""function showMarker(m){
  const h=markerHome();""","""// what apply() decided for this marker, even if the cluster has not caught up yet
function _isShown(m){return m._want!==undefined?m._want:markerHome().hasLayer(m);}
function showMarker(m){
  const h=markerHome();""")
rep("""      if(v===1){const only=M.find(m=>m.score>0&&markerHome().hasLayer(m));""",
    """      if(v===1){const only=M.find(m=>m.score>0&&_isShown(m));""")
rep("""    try{const b=M.filter(m=>markerHome().hasLayer(m)).map(m=>[m.data.lat,m.data.lng]);""",
    """    try{const b=M.filter(m=>_isShown(m)).map(m=>[m.data.lat,m.data.lng]);""")

open(E, 'w', encoding='utf-8').write(s)
print('p31 applied')
