function dismissHint(){
  if(hintDismissed)return;
  hintDismissed=true;
  document.getElementById('fhint').textContent='';
  try{localStorage.setItem(SP+'HintDismissed','1');}catch(e){}
}
// P0-C: the only thing that ever clears the hint is hintDismissed — TIGHT only
// picks which of the two translations shows, never whether one does. Called from
// setLang() (language just changed) and from TIGHT's own change listener (screen
// crossed the breakpoint while the hint was still showing).
function refreshHint(){
  document.getElementById('fhint').innerHTML=hintDismissed?'':iconify(TIGHT.matches?UI[L_].hintShort:UI[L_].hint);
}
const FAV_CODE_PREFIX='KAM1:';
function favCode(){return FAV_CODE_PREFIX+[...favorites].join('.');}
function parseFavCode(txt){
  const t=(txt||'').trim();
  if(t.indexOf(FAV_CODE_PREFIX)!==0)return null;
  const live=new Set(P.map(p=>p.id));
  // Unknown ids are dropped rather than rejected: a code exported from an older
  // edition should still restore whatever it can instead of failing whole.
  const ids=t.slice(FAV_CODE_PREFIX.length).split('.')
    .map(v=>FAV_MIGRATE[v]||v).filter(v=>live.has(v));
  return ids;
}
function favMsg(t){const el=document.getElementById('favIOMsg');if(el)el.textContent=t||'';}
function wireFavIO(){
  const box=document.getElementById('favCode');
  document.getElementById('favExport').onclick=()=>{
    const u=UI[L_];
    // Export/import is the migration path between devices; whether anyone ever
    // completes it was not measurable, so a broken code format could have gone
    // unnoticed indefinitely. The count travels, never the ids.
    trackEvent('fav_export',{n:favorites.size});
    box.value=favCode();box.select();
    // execCommand still works on file:// where the async clipboard API often does not.
    let copied=false;
    try{copied=document.execCommand('copy');}catch(e){}
    if(copied){favMsg(u.favCopied);return;}
    if(navigator.clipboard&&navigator.clipboard.writeText){
      navigator.clipboard.writeText(box.value).then(()=>favMsg(u.favCopied),()=>favMsg(''));
      return;
    }
    favMsg('');   // the code is in the box either way; the reader can copy it by hand
  };
  document.getElementById('favImport').onclick=()=>{
    const u=UI[L_];
    if(!box.value.trim()){box.focus();favMsg(u.favPastePrompt);return;}
    const ids=parseFavCode(box.value);
    if(ids===null){trackEvent('fav_import',{ok:false,reason:'bad_code'});favMsg(u.favBadCode);return;}
    // count what is new to this browser, not what the code contained
    const fresh=ids.filter(id=>!favorites.has(id));
    trackEvent('fav_import',{ok:true,n:fresh.length});
    ids.forEach(id=>favorites.add(id));
    saveFavorites();
    const added=new Set(ids);
    updateFavBadge();
    M.forEach(m=>{if(added.has(m.data.id))m.setPopupContent(popup(m.data,m.i));});
    renderFavList();
    favMsg(fresh.length===0?u.favImportedNone:(fresh.length===1?u.favImportedOne:u.favImported.replace('{N}',fresh.length)));
  };
}
function resetFavIO(){
  const box=document.getElementById('favCode');
  if(box){box.value='';box.placeholder=UI[L_].favPastePrompt;}
  favMsg('');
}
// Export already hides itself when there is nothing yet to export (see below), but
// Import stayed visible either way with no explanation of why a brand-new visitor —
// who has never exported anything — would see a "paste your code" box. It's still
// the right control to keep showing (it's exactly what a resident switching from
// their old phone needs), so rather than hide it, the note next to it now says what
// it's for whenever the list is empty, and reverts once there is a favourite to
// export.
function updateFavIONote(){
  const el=document.getElementById('favIONote');
  if(!el)return;
  const u=UI[L_];
  el.textContent=u.favIONote+(favorites.size===0?u.favIONoteEmpty:'');
}
function renderFavList(){
  const root=document.getElementById('favList');root.innerHTML='';
  const u=UI[L_];
  document.getElementById('favExport').hidden=favorites.size===0;
  updateFavIONote();
  if(favorites.size===0){
    root.innerHTML='<div class="fav-empty">'+u.noFavorites+'</div>';
    return;
  }
  M.forEach(m=>{
    if(!favorites.has(m.data.id))return;
    const p=m.data;
    const item=document.createElement('div');item.className='bus-item fav-item';
    const tagTxt=(p.tag&&u[p.tag])?' <span class="fav-tag">'+u[p.tag]+'</span>':'';
    const fd=distFromUser(p);
    item.innerHTML='<span class="dot" style="background:'+catColour(p.c)+'"></span><button class="rt-name">'+p.n+tagTxt+(fd!==null?'<span class="rt-stop">📍 '+fmtDist(fd)+'</span>':'')+'</button><button class="rt-remove" aria-label="'+u.aClose+'">✕</button>';
    item.querySelector('.rt-name').onclick=()=>{
      // Re-opening a saved place is the clearest evidence that favourites are
      // being used as intended, and it was the one favourites action with no
      // event of its own (only the star toggle had one).
      trackEvent('fav_open',{cat:p.c,reg:p.g,total:favorites.size});
      // No setView here: focusMarker moves the map itself, and moving it first
      // makes the cluster plugin think the flight is already over and stop short
      // of expanding — the marker then stays hidden inside its cluster.
      focusMarker(m,16);closePanel();
    };
    item.querySelector('.rt-remove').onclick=(e)=>{
      e.stopPropagation();
      // Same action as un-starring in the popup, so it carries the same event
      // name and shape — otherwise removals done from this list looked, in the
      // data, like favourites that were never removed at all.
      trackEvent('fav_toggle',{action:'remove',cat:p.c,reg:p.g,src:'list'});
      favorites.delete(p.id);saveFavorites();renderFavList();updateFavBadge();
      m.setPopupContent(popup(m.data,m.i));
    };
    root.appendChild(item);
  });
}
function positionPanel(){
  if(window.innerWidth<=900){panel.style.left='';panel.style.top='';panel.style.maxHeight='';return;}
  const btn=panelMode==='area'?areaBtnEl:panelMode==='cat'?catBtnEl:panelMode==='bus'?busBtnEl:favBtnEl;
  const r=btn.getBoundingClientRect();const w=460;
  let left=Math.min(r.left,window.innerWidth-w-20);left=Math.max(left,20);
  const top=r.bottom+8;
  panel.style.left=left+'px';panel.style.top=top+'px';
  // 2026-09-13 audit: the CSS cap (72vh) ignores where the panel starts, so on
  // a short landscape tablet (1024x600) the Done bar sat 45px below the screen
  // and the last rows could never be scrolled to. Cap it to what is left.
  panel.style.maxHeight=Math.max(240,Math.min(640,window.innerHeight*0.72,window.innerHeight-top-12))+'px';
}
function openPanel(mode){
  // The four buttons at the top of the screen all funnel through here when the
  // panel is closed or showing a different section — tracking at this single
  // point captures "which filter do users open most" without instrumenting
  // each button or the close behavior separately.
  trackEvent('panel_open',{mode:mode,prev:panelMode});
  // 2026-09-13 audit: the four sections share one scrolling body, so a list
  // scrolled in Category opened Bus Routes 400px down with its search box off
  // screen. A different section starts at its top.
  const modeChanged=panelMode!==mode;
  panelMode=mode;
  panelAreaEl.hidden=(mode!=='area');
  panelCatEl.hidden=(mode!=='cat');
  panelBusEl.hidden=(mode!=='bus');
  panelFavEl.hidden=(mode!=='fav');
  document.getElementById('applyBar').style.display=(mode==='bus'||mode==='fav')?'none':'';
  [['area',areaBtnEl],['cat',catBtnEl],['bus',busBtnEl],['fav',favBtnEl]].forEach(([k,el])=>
    el.setAttribute('aria-expanded',mode===k?'true':'false'));
  areaBtnEl.classList.toggle('open',mode==='area');
  catBtnEl.classList.toggle('open',mode==='cat');
  busBtnEl.classList.toggle('open',mode==='bus');
  favBtnEl.classList.toggle('open',mode==='fav');
  if(mode==='bus')renderBusList();
  if(mode==='fav'){resetFavIO();renderFavList();}
  const wasOpen=backdrop.classList.contains('open');
  backdrop.classList.add('open');panel.classList.add('open');
  // (after the panel is displayed: a closed panel is display:none and keeps its
  // old offset internally — a scrollTop set while hidden does nothing)
  if(modeChanged){const pb=panel.querySelector('.panel-body');if(pb)pb.scrollTop=0;}
  if(!wasOpen){
    lockBodyScroll();
    pushSheetState('panel');
    // P0-E INT-01 — 对话框语义 + 焦点管理（WCAG 2.1.1 / 2.4.3）。
    // panel 是一个真正的模态：4 个筛选分类都在里面，键盘用户必须能 Tab 循环、
    // 读屏用户必须知道这是个对话框。仅在面板从关闭到打开的瞬间记录 lastFocused，
    // 后续在 area/cat/bus/fav 之间切换不重置。
    lastFocused=document.activeElement;
    backdrop.setAttribute('role','dialog');
    backdrop.setAttribute('aria-modal','true');
    backdrop.setAttribute('aria-labelledby','panelTitle');
    var firstFocus=panel.querySelector('button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])');
    (firstFocus||document.getElementById('panelClose')).focus();
  }
  updatePanelTitle();
  positionPanel();
  showDragHintOnce();
  dismissHint();
}
function closePanel(fromPop){
  // panel_open is logged on entry; closing here gives a clean open/close pair
  // for funnel reports ("how many people opened Category and never hit Apply").
  // The previous mode is captured so SQL can reconstruct sequences.
  if(panel.classList.contains('open'))trackEvent('panel_close',{mode:panelMode});
  [areaBtnEl,catBtnEl,busBtnEl,favBtnEl].forEach(el=>el.setAttribute('aria-expanded','false'));
  const wasOpen=backdrop.classList.contains('open');
  backdrop.classList.remove('open');panel.classList.remove('open');
  areaBtnEl.classList.remove('open');catBtnEl.classList.remove('open');busBtnEl.classList.remove('open');favBtnEl.classList.remove('open');
  if(wasOpen){unlockBodyScroll();if(fromPop!==true)popSheetState('panel');}
  // P0-E INT-01 — 关闭时清理对话框属性并把焦点还给触发的按钮。
  backdrop.removeAttribute('role');
  backdrop.removeAttribute('aria-modal');
  backdrop.removeAttribute('aria-labelledby');
  // 计算当前激活的面板模式，把焦点还给对应按钮
  // Only when a panel actually closed: Reset and the route ✕ call this too,
  // and stealing focus from them sent keyboard users to the Area button.
  if(!wasOpen)return;
  var triggerBtn=panelMode==='area'?areaBtnEl:panelMode==='cat'?catBtnEl:panelMode==='bus'?busBtnEl:panelMode==='fav'?favBtnEl:null;
  (triggerBtn||lastFocused||areaBtnEl).focus();
}
areaBtnEl.onclick=()=>{(panel.classList.contains('open')&&panelMode==='area')?closePanel():openPanel('area');};
catBtnEl.onclick=()=>{(panel.classList.contains('open')&&panelMode==='cat')?closePanel():openPanel('cat');};
busBtnEl.onclick=()=>{(panel.classList.contains('open')&&panelMode==='bus')?closePanel():openPanel('bus');};
favBtnEl.onclick=()=>{(panel.classList.contains('open')&&panelMode==='fav')?closePanel():openPanel('fav');};
document.getElementById('panelClose').onclick=closePanel;
document.getElementById('applyBtn').onclick=closePanel;
backdrop.onclick=(e)=>{if(e.target===backdrop)closePanel();};
// The drag gesture below works, but a plain static bar is an easy-to-miss
// affordance — this nudges it once, the first time any sheet opens on a
// touch-sized screen, so the handle's draggability registers without needing a
// caption that would cost space in an already tight panel head.
let dragHintShown=false;
function showDragHintOnce(){
  if(dragHintShown||window.innerWidth>900)return;
  dragHintShown=true;
  const grab=document.getElementById('panelGrab');
  if(!grab)return;
  grab.classList.add('hint');
  setTimeout(()=>grab.classList.remove('hint'),900);
}
// ---------------------------------------------------------------------------
// Swipe the bottom sheet down to dismiss it. The handle has been drawn at the top
// of this panel all along, which reads as a promise that it can be dragged; until
// now it could not be, which is worse than having no handle. Pointer events cover
// touch and mouse with one path.
// Desktop (>=901px) uses an anchored dropdown, not a sheet, so the grab area is
// hidden there and this never arms.
(function panelDrag(){
  const grab=document.getElementById('panelGrab');
  if(!grab||!window.PointerEvent)return;
  let startY=0,startT=0,dy=0,dragging=false;
  const CLOSE_PX=90, FLICK_VELOCITY=0.5;   // px, and px per ms
  function end(commit){
    if(!dragging)return;
    dragging=false;
    panel.classList.remove('dragging');
    panel.style.transform='';
    if(commit)closePanel();
  }
  grab.addEventListener('pointerdown',e=>{
    if(window.innerWidth>900)return;
    dragging=true;startY=e.clientY;startT=e.timeStamp;dy=0;
    panel.classList.add('dragging');
    try{grab.setPointerCapture(e.pointerId);}catch(err){/* capture is a nicety */}
  });
  grab.addEventListener('pointermove',e=>{
    if(!dragging)return;
    dy=Math.max(0,e.clientY-startY);          // downward only
    panel.style.transform='translateY('+dy+'px)';
  });
  grab.addEventListener('pointerup',e=>{
    const dt=Math.max(1,e.timeStamp-startT);
    end(dy>CLOSE_PX||(dy>24&&dy/dt>FLICK_VELOCITY));
  });
  // A cancelled pointer (an incoming call, the browser taking over the gesture)
  // must restore the panel, never close it — the user did not ask for that.
  grab.addEventListener('pointercancel',()=>end(false));
})();
// 2026-09-13 audit: a popup that was open when the phone turned sideways kept
// its portrait height, and its name/★/✕ ended up above the (now shorter) map.
// Leaflet only applies maxHeight when a popup opens, so re-lay the open one out.
let _popupResizeT=null;
function relayoutOpenPopup(){
  try{const pu=map._popup;if(pu&&pu.isOpen&&pu.isOpen()){pu.options.autoPanPaddingTopLeft=panPad();pu.options.maxHeight=popMaxH();pu.update();}}catch(e){}
}
window.addEventListener('resize',()=>{if(panel.classList.contains('open'))positionPanel();syncPanPad();placeMapNotes();
  clearTimeout(_popupResizeT);_popupResizeT=setTimeout(relayoutOpenPopup,150);});
if(TIGHT.addEventListener)TIGHT.addEventListener('change',()=>{refreshHint();apply();});
document.addEventListener('click',(e)=>{
  if(!panel.classList.contains('open')||window.innerWidth<=900)return;
  // A handler that re-renders its own container detaches the clicked element, so by
  // the time this runs `panel.contains(target)` is false and the panel would close
  // under the user. Anything no longer in the document was an inside click.
  if(!e.target.isConnected)return;
  if(panel.contains(e.target)||areaBtnEl.contains(e.target)||catBtnEl.contains(e.target)||busBtnEl.contains(e.target)||favBtnEl.contains(e.target))return;
  // the Quick Picks "More" chip opens this very panel; its click must not
  // also count as a click outside it
  if(e.target.closest&&(e.target.closest('#qpMore')||e.target.closest('#searchSuggest')))return;
  closePanel();
});
// Everything a user can put the page into, undone in one place. It used to leave
// the drawn bus route, the open popup and the map view untouched, and it was hidden
// whenever no filter was set — which is exactly when someone wants to start over.
function resetAll(){
  // "how many filters before someone gives up" needs the answer: was anything
  // actually set, or did they open the app and immediately scrub back to the
  // city-wide view?
  const wasDirty=!!(searchTerm||selectedRoute||presetsAdjusted||openNow||nearOnly||aC.size>0||aT.size>0||aR.size<Object.keys(RI).length);
  // "dirty: true" says something was on but not what, so it cannot tell a reader
  // clearing one stray area filter apart from one abandoning a search that went
  // nowhere. The dimensions are cheap and make the event diagnostic.
  trackEvent('reset_all',{dirty:wasDirty,search:!!searchTerm,route:!!selectedRoute,
    cats:aC.size,themes:aT.size,areas:aR.size<Object.keys(RI).length});
  const snap=wasDirty?filterSnapshot():null;
  aR=new Set(Object.keys(RI));
  aC.clear(); aT.clear(); selPresets.clear(); presetsAdjusted=false; openNow=false; updateOpenQuickpick(); nearOnly=false; updateNearQuickpick();
  searchInputEl.value=''; clearTimeout(searchTimer); searchTerm=''; searchRaw='';
  searchClearEl.hidden=true; preSearchView=null;
  if(selectedRoute)renderRoute(null,false);
  map.closePopup();
  closePanel();
  expandedGroups.clear(); DEFAULT_OPEN_GROUPS.forEach(g=>expandedGroups.add(g));
  map.setView(CITY.centre,CITY.zoom);
  renderRegs();renderCats();renderThemes();apply();
  if(snap)showToast(UI[L_].resetDone,{action:UI[L_].undo,onAction:()=>restoreSnapshot(snap)});
}
document.getElementById('resetBtn').onclick=resetAll;
updateFavBadge();
