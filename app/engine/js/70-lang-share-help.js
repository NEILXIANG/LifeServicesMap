function setLang(l){
  // Defence in depth: readURLState already filters, but a future caller might not.
  if(!owns(UI,l))l='en';
  // the first call is the page settling on its language, not a reader switching
  const prevL=L_,changed=L_!==l&&window._langInit;
  window._langInit=true;
  L_=l;const u=UI[l];
  // recorded after L_ moves so the envelope's language column is the new one
  if(changed)trackEvent('lang_change',{from:prevL,to:l});
  document.documentElement.lang=({zh:'zh-CN',en:'en-CA',fr:'fr-CA'})[l]||l;
  const title=tpl(u.title,l);
  document.getElementById('h1').textContent=title;
  document.title=title;
  // the polite live region only refreshes when the count moves, so it kept the
  // previous language's sentence; clearing it announces nothing and leaves nothing stale
  {const ann=document.getElementById('a11yAnnounce');if(ann)ann.textContent='';}
  document.getElementById('ogTitle').setAttribute('content',title);
  document.getElementById('metaDesc').setAttribute('content',tpl(u.metaDesc,l));
  document.getElementById('ogDesc').setAttribute('content',tpl(u.metaDesc,l));
  document.getElementById('sub').textContent=u.sub;
  // Three lines a reader will actually read, then the full statement behind one
  // tap. The full text is the same words as before — the change is that the
  // summary is what a passing reader now takes away, instead of nothing.
  let pv='<div class="privacy-note"><div class="pv-h">'+iconify(u.legalTitle)+'</div><ul class="pv-sum">';
  u.legalSum.forEach(x=>{pv+='<li><b>'+esc(x[0])+'</b> '+esc(x[1])+'</li>';});
  pv+='</ul></div>';
  pv+='<div class="privacy-note"><div class="pv-h">'+iconify(u.privacyTitle)+'</div><ul class="pv-sum">';
  u.privacySum.forEach(x=>{pv+='<li><b>'+esc(x[0])+'</b> '+esc(x[1])+'</li>';});
  pv+='</ul><button type="button" class="pv-more" id="pvMore" aria-expanded="false" aria-controls="pvFull">'
     +esc(u.privacyExpand)+'</button>'
     +'<div class="pv-full" id="pvFull" hidden>'+tpl(u.privacyNote,l)+'</div></div>';
  document.getElementById('noteBody').innerHTML=tpl(u.note,l)+pv;
  const pvBtn=document.getElementById('pvMore');
  if(pvBtn)pvBtn.onclick=()=>{
    const full=document.getElementById('pvFull');
    const opening=full.hidden;
    full.hidden=!opening;
    pvBtn.setAttribute('aria-expanded',opening?'true':'false');
    pvBtn.textContent=opening?u.privacyCollapse:u.privacyExpand;
    // Whether anyone goes past the summary is the one thing that says if the
    // summary is doing its job or hiding the detail.
    trackEvent('privacy_expand',{action:opening?'open':'close'});
  };
  setHL('noteToggle',u.noteToggleLabel);
  renderFirstUse();
  try{renderSeason();}catch(e){}
  // Landmark labels: sign name, and under it the same thing in the reader's
  // language when the data has one. Re-set on every language change.
  landmarkMarkers.forEach(it=>{
    const g=(typeof LANDMARK_GLOSS!=='undefined'&&LANDMARK_GLOSS[it.id]||{})[l];
    const tt=it.marker.getTooltip();
    if(tt)tt.setContent(esc(it.name)+(g?'<span class="lm-g">'+esc(g)+'</span>':''));
  });
  setTimeout(updateLandmarkLabelVisibility,60);
  document.getElementById('noteTitle').innerHTML=iconify(u.noteToggleLabel);
  setHL('guideToggle',u.guideToggleLabel);
  document.getElementById('guideToggle').dataset.short=u.guideToggleShort;
  setHL('shareBtn',u.shareBtnLabel);
  setHL('helpBtn',u.helpBtnLabel);
  document.getElementById('helpBtn').dataset.short=u.helpBtnShort;
  if(helpBackdropEl&&helpBackdropEl.classList.contains('open'))renderHelpSheet();
  document.getElementById('shareBtn').title=u.shareBtnTip;
  const si=document.getElementById('searchInput');
  si.placeholder=u.searchPlaceholder;si.setAttribute('aria-label',u.aSearch);
  try{startPlaceholderRotation();hideSearchSuggest();}catch(e){}
  document.getElementById('searchClear').setAttribute('aria-label',u.aClearSearch);
  document.getElementById('noteClose').setAttribute('aria-label',u.aClose);
  document.getElementById('guideClose').setAttribute('aria-label',u.aClose);
  document.getElementById('shareClose').setAttribute('aria-label',u.aClose);
  document.getElementById('panelClose').setAttribute('aria-label',u.aClose);
  document.getElementById('busCoverage').textContent=u.busCoverage;
  const onl=document.getElementById('offlineNote');
  if(onl&&!onl.hidden)document.getElementById('offlineText').innerHTML=iconify(u.offlineTiles);
  document.getElementById('offlineClose').setAttribute('aria-label',u.aClose);
  document.getElementById('favBtnLabel').textContent=u.favBtnLabel;
  updateFavIONote();
  favMsg('');   // 2026-09-13 audit: an import/export result stayed in the old language
  document.getElementById('favExport').textContent=u.favExport;
  document.getElementById('favImport').textContent=u.favImport;
  document.getElementById('favCode').placeholder=u.favPastePrompt;
  document.getElementById('guideTitle').innerHTML=iconify(u.guideToggleLabel);
  const qg=document.getElementById('qpGuide');
  if(qg){qg.innerHTML=iconify(u.guideToggleLabel);qg.setAttribute('aria-label',stripEmoji(u.guideToggleLabel));
    qg.onclick=()=>openGuide('quickpick');}
  // The guide is stored in tiers so another city reuses everything but guideCity,
  // and another province swaps only guideProv. GUIDE_ORDER keeps the reading order
  // sensible while the tiers stay separable.
  document.getElementById('guideBody').innerHTML=keepPhonesWhole(
    GUIDE_ORDER.map(k=>tpl(u[k],l)||'').join('')+tpl(u.licenceNote,l)+(tpl(u.licenceData,l)||''));
  buildGuideToc();
  // Keep the task layer in the reader's language too — and keep them on the
  // task they were reading rather than bouncing them back to the list.
  if(_taskOpen)openTask(_taskOpen,'lang'); else renderTaskList();try{updateGuideProgress();}catch(e){}
  document.getElementById('quickLabel').innerHTML=iconify(u.quickLabel);
  document.querySelectorAll('[data-ic]').forEach(el=>{el.innerHTML=ico(el.dataset.ic);});
  document.getElementById('clearCat').textContent=u.clearCatFilter;
  document.getElementById('themeLabel').innerHTML=iconify(u.themeLabel);
  document.getElementById('themeHint').textContent=u.themeHint;
  document.getElementById('themeRow').setAttribute('aria-label',u.themeLabel);
  document.getElementById('catPanelHint').textContent=u.catPanelHint;
  document.getElementById('busPanelHint').textContent=u.busPanelHint;
  Object.keys(PRESETS).forEach(key=>{const el=document.getElementById(key);if(el)el.innerHTML=iconify(u[key]);});
  const qm=document.getElementById('qpMore');
  if(qm){qm.innerHTML=ico('more')+esc(u.qpMore);qm.title=stripEmoji(u.catLabel);}
  document.getElementById('presetSecLabel').innerHTML=iconify(u.presetSecLabel);
  document.getElementById('presetSecHint').textContent=u.presetSecHint;
  // Chip width changes per language (French/Spanish labels run longer than English),
  // which changes whether the row overflows at all.
  requestAnimationFrame(updateQpFade);
  // WCAG 2.1 §2.4.1: keyboard bypass + landmark labels so screen readers can
  // jump between the language switcher / page actions / filter toolbar by role.
  const skipEl=document.getElementById('skipLink');
  if(skipEl)skipEl.textContent=u.aSkip;
  const langSwEl=document.getElementById('langSw');
  if(langSwEl)langSwEl.setAttribute('aria-label',u.aNavLang);
  const headerLinksEl=document.getElementById('headerLinksGroup');
  if(headerLinksEl)headerLinksEl.setAttribute('aria-label',u.aNavHeader);
  const ftoolbarEl=document.getElementById('ftoolbar');
  if(ftoolbarEl)ftoolbarEl.setAttribute('aria-label',u.aNavFilters);
  // qpRow already uses aria-labelledby="quickLabel" so AT reads u.quickLabel.
  document.getElementById('footer').innerHTML=keepPhonesWhole(tpl(u.footer,l))
    +'<br><span class="licence-line">'+tpl(u.licenceShort,l)+' · <span class="ver-line" title="'+esc(u.verTip)+'">v'+esc(DATA_VERSION)+'</span></span>';
  // See .footer-note-btn in the stylesheet: with the header's Data Notes button
  // hidden, this is the only remaining way for a reader to reach the privacy
  // disclosure and the disclaimer. Attached after every footer render because
  // setLang() rewrites that innerHTML wholesale.
  const fpv=document.getElementById('footer').querySelector('.footer-privacy');
  if(fpv){
    const nb=document.createElement('button');
    nb.type='button';nb.className='footer-note-btn';nb.id='footerNoteBtn';
    nb.textContent=u.privacyMore;
    nb.onclick=()=>{trackEvent('note_open',{src:'footer'});
                    openModal(document.getElementById('noteBackdrop'));};
    fpv.insertAdjacentElement('afterend',nb);
  }
  setHL('feedbackLink',u.feedbackLink);
  const fl=document.getElementById('feedbackLink');
  fl.href='mailto:'+contactEmail()+'?subject='+encodeURIComponent(u.fbSubjectGeneral)
    +'&body='+encodeURIComponent(u.fbLang+': '+l+'\n'+u.fbVersion+': '+DATA_VERSION+'\n\n---\n');
  document.getElementById('areaBtnLabel').textContent=u.areaBtnLabel;
  document.getElementById('catBtnLabel').textContent=u.catBtnLabel;
  document.getElementById('busBtnLabel').textContent=u.busBtnLabel;
  document.getElementById('resetLabel').textContent=u.resetBtn;
  document.getElementById('resetBtn').title=u.resetBtnTip;
  updatePanelTitle();
  if(!panelBusEl.hidden)renderBusList();
  if(!panelFavEl.hidden)renderFavList();
  if(selectedRoute)renderRoute(selectedRoute,false);
  refreshHint();
  if(geoControl&&geoControl._btn){
    geoControl._btn.setAttribute('aria-label',u.geoBtnTip);
    geoControl._btn.title=u.geoBtnTip;
    const tx=geoControl._btn.querySelector('.geo-btn-tx');
    if(tx)tx.textContent=u.geoBtnLabel;
  }
  if(geoMarker&&geoMarker.getTooltip())geoMarker.setTooltipContent(u.geoHereLabel);
  // the location note (permission denied / explain) keeps its language too
  try{if(geoNoteEl&&!geoNoteEl.hidden&&_geoNoteKey){
    if(_geoNoteKey==='explain')showGeoExplain();else geoMessage(u[_geoNoteKey],_geoNoteKey);}}catch(e){}
  updateThemeQuickpicks();
  updateQpFade();
  document.querySelectorAll('.lang-btn').forEach(b=>{
    const on=b.dataset.lang===l;
    b.classList.toggle('active',on);
    b.setAttribute('aria-pressed',on?'true':'false');
    if(on)b.setAttribute('aria-current','true');else b.removeAttribute('aria-current');});
  try{renderLangMenu();}catch(e){}
  M.forEach(m=>m.setPopupContent(popup(m.data,m.i)));
  // a standalone popup (favourite / guide hand-off for a filtered-out place)
  // is not bound to a marker; it carries its place and is re-rendered here
  try{const op=map._popup;if(op&&op._kplace&&map.hasLayer(op))op.setContent(popup(op._kplace,op._kidx||0));}catch(e){}
  // Leaflet's own controls speak English unless told otherwise
  try{const u2=UI[l];document.querySelectorAll('.leaflet-control-zoom-in').forEach(b=>{b.title=u2.aZoomIn;b.setAttribute('aria-label',u2.aZoomIn);});
    document.querySelectorAll('.leaflet-control-zoom-out').forEach(b=>{b.title=u2.aZoomOut;b.setAttribute('aria-label',u2.aZoomOut);});
    document.querySelectorAll('.leaflet-popup-close-button').forEach(b=>{b.title=u2.aClosePopup;b.setAttribute('aria-label',u2.aClosePopup);});
    const mapEl=document.getElementById('map');if(mapEl){mapEl.setAttribute('role','region');mapEl.setAttribute('aria-label',tpl(u2.aMap,l));}}catch(e){}
  // cluster bubbles carry a translated aria-label, so they have to be redrawn too
  if(cluster&&cluster.refreshClusters)cluster.refreshClusters();
  updateFavBadge();
  renderRegs();renderCats();renderThemes();apply();
  // 2026-09-13: the map was created before the header and toolbar had their
  // text, and longer labels (fr/es) wrap and push it down; Leaflet kept the
  // pre-text size all session, so every fit centred ~40px low on a phone.
  requestAnimationFrame(()=>{try{map.invalidateSize(false);}catch(e){}});
  // French spacing before : ; ? ! and inside « » (2026-10-20): what is on screen now, and whatever appears later
  if(l==='fr'){frSpaces(document.body);watchFrSpaces();}
}

document.querySelectorAll('.lang-btn').forEach(b=>{b.onclick=()=>{setStoredLang(b.dataset.lang);setLang(b.dataset.lang);closeLangMenu();};});
// item 13: the phone's single language button and its list
const LANG_NAMES={en:'English',fr:'Français',es:'Español',zh:'中文',ko:'한국어',ja:'日本語'};
function renderLangMenu(){
  const cur=document.getElementById('langMenuCur');if(cur)cur.textContent=LANG_NAMES[L_]||L_.toUpperCase();
  const menu=document.getElementById('langMenu');if(!menu)return;
  // only the phone's list is reordered; the desktop segmented control keeps a
  // stable order so a hand that knows where 中文 sits still finds it there
  let phone=false;try{phone=window.matchMedia('(max-width:600px)').matches||window.matchMedia('(max-height:500px) and (orientation:landscape) and (max-width:900px)').matches;}catch(e){}
  const tiny=phone&&window.innerWidth<=360;
  if(cur&&tiny)cur.textContent=({en:'EN',fr:'FR',es:'ES',zh:'中文',ko:'한국어',ja:'日本語'})[L_]||L_;
  // the list reads as names on a phone ("Français"), as codes in the desktop strip
  menu.querySelectorAll('.lang-btn').forEach(b=>{if(!b.dataset.code)b.dataset.code=b.textContent;b.textContent=phone?(LANG_NAMES[b.dataset.lang]||b.dataset.code):b.dataset.code;});
  if(!phone)return;
  // current language first, then the one the phone itself speaks, then the rest
  let guess=null;try{guess=detectLang();}catch(e){}
  const order=[L_].concat(guess&&guess!==L_?[guess]:[]);
  const rest=[...menu.querySelectorAll('.lang-btn')].filter(b=>order.indexOf(b.dataset.lang)<0);
  order.map(k=>menu.querySelector('.lang-btn[data-lang="'+k+'"]')).filter(Boolean).concat(rest).forEach(b=>menu.appendChild(b));
}
function openLangMenu(){const sw=document.getElementById('langSw');sw.classList.add('open');document.getElementById('langMenuBtn').setAttribute('aria-expanded','true');
  const a=sw.querySelector('.lang-btn.active');if(a)a.focus();}
function closeLangMenu(){const sw=document.getElementById('langSw');if(!sw.classList.contains('open'))return;sw.classList.remove('open');document.getElementById('langMenuBtn').setAttribute('aria-expanded','false');}
document.getElementById('langMenuBtn').onclick=()=>{const sw=document.getElementById('langSw');if(sw.classList.contains('open'))closeLangMenu();else{trackEvent('lang_menu',{});openLangMenu();}};
document.addEventListener('click',e=>{const sw=document.getElementById('langSw');if(sw.classList.contains('open')&&!sw.contains(e.target))closeLangMenu();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeLangMenu();});
let _lmResizeT=null;window.addEventListener('resize',()=>{clearTimeout(_lmResizeT);_lmResizeT=setTimeout(()=>{try{closeLangMenu();renderLangMenu();}catch(e){}},120);});
// The URL has quietly carried the current language/area/category/search/route for
// several rounds now (writeURLState), but nothing ever told a reader that copying
// the address bar sends someone else straight to this same view — a "here are the
// banks on the North Shore, in Korean" link was possible but undiscoverable. This
// button makes the existing feature visible instead of adding a new one.
// ---------------------------------------------------------------------------
// Sharing. The button used to copy the link outright; it now opens a sheet,
// because "share" means WhatsApp to a reader from Delhi, LINE in Osaka,
// KakaoTalk in Seoul and WeChat in Chinese-speaking households — and the copy
// is still the first thing in the sheet, so the old one-click habit costs one
// extra tap rather than breaking.
//
// Only platforms with a real, documented share-a-link endpoint get a button.
// WeChat, TikTok and KakaoTalk have none: WeChat expects a QR scan on desktop
// or a server-signed JS-SDK inside its own browser, TikTok's Share Kit takes
// video/photo through a registered app rather than a URL, and KakaoTalk needs
// its SDK and an app key. navigator.share covers all three on a phone, because
// the OS sheet lists whatever the reader has installed, so that is offered
// first and the sheet says plainly what to do on a desktop.
// ---------------------------------------------------------------------------
const SHARE_TARGETS=[
  {k:'whatsapp', ic:'💬', name:'WhatsApp', url:(u,t)=>'https://wa.me/?text='+encodeURIComponent(t+' '+u)},
  {k:'facebook', ic:'📘', name:'Facebook', url:(u)=>'https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(u)},
  {k:'x',        ic:'✖️', name:'X',        url:(u,t)=>'https://twitter.com/intent/tweet?url='+encodeURIComponent(u)+'&text='+encodeURIComponent(t)},
  {k:'telegram', ic:'✈️', name:'Telegram', url:(u,t)=>'https://t.me/share/url?url='+encodeURIComponent(u)+'&text='+encodeURIComponent(t)},
  {k:'line',     ic:'🟢', name:'LINE',     url:(u)=>'https://social-plugins.line.me/lineit/share?url='+encodeURIComponent(u)},
  {k:'email',    ic:'✉️', name:null, label:'shareEmail', url:(u,t)=>'mailto:?subject='+encodeURIComponent(t)+'&body='+encodeURIComponent(u)},
  {k:'sms',      ic:'📱', name:null, label:'shareSms',   url:(u,t)=>'sms:?&body='+encodeURIComponent(t+' '+u)}
];
const shareBackdropEl=document.getElementById('shareBackdrop');
function shareText(){
  // The page title already carries the city name through {CITY}; reuse it so the
  // shared message reads as something rather than a bare URL.
  return (document.getElementById('h1').textContent||document.title||'').trim();
}
// The link a reader chooses to send: the address bar plus the search, when
// there is one and it is not a cry for help.
function shareHref(){
  try{
    const x=new URL(location.href);
    x.searchParams.delete('tiles');   // a tester's map switch is not part of what is shared (2026-10-22)
    const raw=searchInputEl.value.trim();
    if(searchTerm&&raw&&!isCrisisQuery(raw))x.searchParams.set('q',raw);
    return x.toString();
  }catch(e){return location.href;}
}
function copyShareLink(){
  const u=UI[L_],href=shareHref();
  trackEvent('share_click',{stage:'intent',target:'copy'});
  let copied=false;
  try{
    const ta=document.createElement('textarea');
    ta.value=href;ta.style.position='fixed';ta.style.opacity='0';
    document.body.appendChild(ta);ta.select();
    copied=document.execCommand('copy');
    document.body.removeChild(ta);
  }catch(e){}
  if(copied){trackEvent('share_click',{stage:'result',target:'copy',copied:true,method:'execCommand'});showToast(u.linkCopied);return;}
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(href).then(
      ()=>{trackEvent('share_click',{stage:'result',target:'copy',copied:true,method:'clipboard'});showToast(u.linkCopied);},
      ()=>{trackEvent('share_click',{stage:'result',target:'copy',copied:false,method:'clipboard'});});
  }else{
    // Both paths unavailable — the click produced nothing, so record it rather
    // than let the failure rate look like zero.
    trackEvent('share_click',{stage:'result',target:'copy',copied:false,method:'none'});
  }
}
function renderShareSheet(){
  const u=UI[L_],grid=document.getElementById('shareGrid');
  document.getElementById('shareTitle').innerHTML=iconify(u.shareTitle);
  document.getElementById('shareLead').textContent=u.shareLead;
  document.getElementById('shareNote').textContent=navigator.share?u.shareNoteNative:u.shareNote;
  const nat=document.getElementById('shareNative');
  nat.textContent=u.shareNative;
  nat.hidden=!(navigator.share);
  grid.innerHTML='';
  // Copy comes first: it is the one that always works, including offline and
  // inside in-app browsers that block window.open.
  const copyBtn=document.createElement('button');
  copyBtn.className='share-item';copyBtn.type='button';
  copyBtn.innerHTML='<span class="si" aria-hidden="true">🔗</span><span></span>';
  copyBtn.lastChild.textContent=u.shareCopy;
  copyBtn.onclick=copyShareLink;
  grid.appendChild(copyBtn);
  // a text message needs a phone: on a computer (no touch) the button did nothing (2026-10-20)
  const touch=!!(window.matchMedia&&window.matchMedia('(pointer:coarse)').matches);
  SHARE_TARGETS.filter(t=>t.k!=='sms'||touch).forEach(t=>{
    const a=document.createElement('a');
    a.className='share-item';a.target='_blank';a.rel='noopener';
    a.href=t.url(shareHref(),shareText());
    a.innerHTML='<span class="si" aria-hidden="true">'+t.ic+'</span><span></span>';
    a.lastChild.textContent=t.name||u[t.label];
    a.onclick=()=>{trackEvent('share_click',{stage:'intent',target:t.k});
                   trackEvent('share_click',{stage:'result',target:t.k,opened:true});};
    grid.appendChild(a);
  });
}
document.getElementById('shareBtn').onclick=()=>{
  trackEvent('share_open',{native:!!navigator.share});
  renderShareSheet();
  openModal(shareBackdropEl);
};
document.getElementById('shareClose').onclick=()=>closeModal(shareBackdropEl);
shareBackdropEl.onclick=(e)=>{if(e.target===shareBackdropEl&&!justOpened(shareBackdropEl))closeModal(shareBackdropEl);};
shareBackdropEl.addEventListener('keydown',e=>trapTab(e,shareBackdropEl));
document.getElementById('shareNative').onclick=()=>{
  if(!navigator.share)return;
  trackEvent('share_click',{stage:'intent',target:'native'});
  navigator.share({title:shareText(),url:shareHref()}).then(
    // A dismissed sheet rejects with AbortError, which is a normal outcome and
    // not a failure — telling them apart is the whole point of logging it.
    ()=>{trackEvent('share_click',{stage:'result',target:'native',shared:true});closeModal(shareBackdropEl);},
    (err)=>{const aborted=err&&err.name==='AbortError';
            trackEvent('share_click',{stage:'result',target:'native',shared:false,aborted:!!aborted});});
};
const helpBackdropEl=document.getElementById('helpBackdrop');
// 2026-09-21: one door that is always on screen, for the moment someone is not
// looking for a place but for a person to talk to.
let _clearArmed=false;
function renderHelpSheet(){
  const u=UI[L_],body=document.getElementById('helpBody');
  document.getElementById('helpTitle').innerHTML=iconify(u.helpTitle);
  _clearArmed=false;
  body.innerHTML='<p class="help-lead">'+esc(u.helpLead)+'</p>'+hotlineHtml(false)+localCrisisHtml()
    +'<p class="help-info"><a href="tel:'+esc(CITY.help.info)+'"><b>2-1-1</b></a> '+glueTimes(esc(u.helpInfo))+'</p>'
    +'<div class="help-actions"><button type="button" class="help-exit" id="helpExit"></button><p class="help-note" id="helpExitNote"></p>'
    +'<button type="button" class="help-clear" id="helpClear"></button><p class="help-note" id="helpClearNote"></p></div>';
  document.getElementById('helpExit').textContent=u.helpExit;
  document.getElementById('helpExitNote').textContent=u.helpExitNote;
  const cl=document.getElementById('helpClear');cl.textContent=u.helpClear;
  document.getElementById('helpClearNote').textContent=u.helpClearNote;
  document.getElementById('helpExit').onclick=()=>{
    try{sessionStorage.clear();}catch(e){}
    location.replace('https://www.google.com/');
  };
  cl.onclick=()=>{
    if(!_clearArmed){_clearArmed=true;cl.classList.add('armed');cl.textContent=u.helpClearConfirm;return;}
    try{Object.keys(localStorage).filter(k=>k.startsWith(SP)).forEach(k=>localStorage.removeItem(k));}catch(e){}
    try{sessionStorage.clear();}catch(e){}
    location.replace(location.pathname);
  };
}
document.getElementById('helpBtn').onclick=()=>{
  trackEvent('help_open',{});
  renderHelpSheet();
  openModal(helpBackdropEl);
};
document.getElementById('helpClose').onclick=()=>closeModal(helpBackdropEl);
helpBackdropEl.onclick=(e)=>{if(e.target===helpBackdropEl&&!justOpened(helpBackdropEl))closeModal(helpBackdropEl);};
helpBackdropEl.addEventListener('keydown',e=>trapTab(e,helpBackdropEl));
const noteBackdropEl=document.getElementById('noteBackdrop');
document.getElementById('noteToggle').onclick=()=>{trackEvent('note_open',{});openModal(noteBackdropEl);};
document.getElementById('noteClose').onclick=()=>closeModal(noteBackdropEl);
noteBackdropEl.onclick=(e)=>{if(e.target===noteBackdropEl&&!justOpened(noteBackdropEl))closeModal(noteBackdropEl);};
noteBackdropEl.addEventListener('keydown',e=>trapTab(e,noteBackdropEl));
// Escape always dismisses the topmost thing that is open
document.addEventListener('keydown',(e)=>{
  if(e.key!=='Escape')return;
  if(helpBackdropEl.classList.contains('open')){closeModal(helpBackdropEl);return;}
  if(shareBackdropEl.classList.contains('open')){closeModal(shareBackdropEl);return;}
  if(guideBackdropEl.classList.contains('open')){closeModal(guideBackdropEl);return;}
  if(noteBackdropEl.classList.contains('open')){closeModal(noteBackdropEl);return;}
  if(panel.classList.contains('open')){closePanel();return;}
  if(document.querySelector('.leaflet-popup')){map.closePopup();}
});
// One control, and its name matches what it does: remove the category filter.
// Turning a category, a group or a Quick Pick on is a new "what"; during a search
// it would otherwise do nothing visible (search pauses categories), so it ends
// the search. Turning one off leaves the search alone.
function _endSearchFor(by){
  if(!searchTerm)return;
  trackEvent('search_clear',{had:searchRaw.length,n:lastVisible,by:by});
  searchInputEl.value='';clearTimeout(searchTimer);runSearch();
}
function clearCatFilter(){aC.clear();selPresets.clear();presetsAdjusted=false;renderCats();renderThemes();apply();}

document.getElementById('clearCat').onclick=()=>{trackEvent('preset_clear_all',{});clearCatFilter();};
Object.keys(PRESETS).forEach(key=>{
  const el=document.getElementById(key);
  if(el)el.onclick=()=>{
    const had=selPresets.has(key);
    if(!had)_endSearchFor('preset');
    if(had){selPresets.delete(key);}else{selPresets.add(key);}
    trackEvent('preset_toggle',{id:key,action:had?'remove':'add',active:selPresets.size});
    presetsAdjusted=false;
    if(selPresets.size===0){aC.clear();}
    else{const s2=new Set();selPresets.forEach(k=>PRESETS[k].forEach(c=>s2.add(c)));aC=s2;}
    renderCats();renderThemes();apply();
  };
});

const backdrop=document.getElementById('backdrop'),panel=document.getElementById('panel'),
  areaBtnEl=document.getElementById('areaBtn'),catBtnEl=document.getElementById('catBtn'),busBtnEl=document.getElementById('busBtn'),favBtnEl=document.getElementById('favBtn'),
  panelAreaEl=document.getElementById('panelArea'),panelCatEl=document.getElementById('panelCat'),panelBusEl=document.getElementById('panelBus'),panelFavEl=document.getElementById('panelFav');
// 2026-10-03: a city with no transit data has no bus entry at all, rather than a
// button that opens an empty list.
if(!Object.keys(BR).length&&busBtnEl)busBtnEl.hidden=true;
// P0-E INT-01 — Tab 焦点圈在面板内（与 note/guide 同套机制）。
// 2026-09-07：这一行原本写在上面约 18 行处，在 `const backdrop` 声明之前就引用了它，
// 触发暂时性死区（Cannot access 'backdrop' before initialization），整段初始化直接中断。
// 之前没暴露出来，是因为更早的分类 key 崩溃就已经让代码走不到这里。必须留在声明之后。
backdrop.addEventListener('keydown',e=>trapTab(e,backdrop));
// P1-A INT-04/06 — hintDismissed 持久化到 localStorage，刷新页面后不再
// 重新弹一次说明。键名带 'kamloops' 前缀以防和其他站点冲突，try/catch 包裹
// 是因为有些隐身模式/隐私浏览器会拒绝写入（同一规则也用在 favorites 上）。
let hintDismissed=false;
try{hintDismissed=localStorage.getItem(SP+'HintDismissed')==='1';}catch(e){}
