// === P0-D ERR-01 — global error trap =====================================
// Without this a Leaflet crash or a JSON.parse on bad data leaves the user
// staring at a half-broken map with no clue. Surface a non-blocking toast
// in the active language and ship the error to Analytics Engine as
// js_error so the failure pattern is visible from the dashboard too.
// The _reportError helper swallows its own failures so an error inside
// the error reporter cannot loop back into the error reporter.
(function installGlobalErrorTrap(){
  function _reportError(kind,payload){
    try{trackEvent('js_error',Object.assign({kind:kind},payload||{}));}catch(_){}
  }
  window.addEventListener('error',function(ev){
    var msg=(ev&&ev.message?String(ev.message):'(no message)').slice(0,160);
    var src=(ev&&ev.filename?String(ev.filename):'').split('/').slice(-2).join('/');
    var line=ev&&(ev.lineno||ev.lineNumber)||0;
    var col=ev&&(ev.colno||ev.columnNumber)||0;
    var stack=ev&&ev.error&&ev.error.stack?String(ev.error.stack).split('\n').slice(0,3).join(' | ').slice(0,300):'';
    _reportError('error',{msg:msg,src:src,line:line,col:col,stack:stack,ver:(typeof DATA_VERSION==='string'?DATA_VERSION:'')});
    try{if(typeof showToast==='function'&&UI&&UI[L_]&&UI[L_].errorHint)showToast(UI[L_].errorHint);}catch(_){}
  });
  window.addEventListener('unhandledrejection',function(ev){
    var r=ev&&ev.reason;
    var msg=r&&r.message?String(r.message):r?String(r):'(unknown)';
    _reportError('promise',{msg:String(msg).slice(0,160)});
    try{if(typeof showToast==='function'&&UI&&UI[L_]&&UI[L_].errorHint)showToast(UI[L_].errorHint);}catch(_){}
  });
})();
function toggleFav(el,ev){
  // Rewriting the popup detaches this very button, so the click would otherwise
  // finish bubbling to the map and Leaflet would close the popup under the user.
  if(ev&&ev.stopPropagation)ev.stopPropagation();
  const idx=+el.dataset.i,key=P[idx].id,u=UI[L_];
  const act=favorites.has(key)?'remove':'add';
  if(favorites.has(key)){favorites.delete(key);el.textContent='☆';el.classList.remove('active');}
  else{favorites.add(key);el.textContent='★';el.classList.add('active');}
  // category and area, not the place: a list of favourites is the reader's
  trackEvent('fav_toggle',{action:act,cat:P[idx].c,reg:P[idx].g});
  // The button survives this click, so its own state has to be updated in place —
  // the rewritten popup HTML below only takes effect on the next open.
  const now=favorites.has(key);
  el.setAttribute('aria-pressed',now);
  el.setAttribute('aria-label',now?u.favRemove:u.favAdd);
  // The star's own colour change was the only feedback a tap ever got — too subtle
  // to trust, which is what invited a second, undoing tap. This is deliberately the
  // only place in the app that raises a toast.
  showToast(now?u.favAddedMsg:u.favRemovedMsg);
  saveFavorites();
  // The marker's bound popup HTML is what Leaflet re-renders on every open, so it
  // has to be rewritten too — otherwise closing and reopening showed a stale ☆.
  const m=M[idx];
  if(m)m.setPopupContent(popup(m.data,idx));
  if(!panelFavEl.hidden)renderFavList();
  updateFavBadge();
}
function updateFavBadge(){
  const b=document.getElementById('favBadge');
  if(favorites.size>0){b.hidden=false;b.textContent=favorites.size;}else{b.hidden=true;}
}

// 2026-09-24 — the pin is a flat circle built from the same parts as a cluster
// bubble (see .kcluster): one ring width, one shadow, one shape language on the
// map. The category colour is the fill, the glyph sits on a white face so a
// colour emoji stays legible on every one of the 51 fills, and the anchor is the
// circle's centre — a place now sits on its coordinates rather than 21px above
// them, which is also how the cluster it collapses into behaves.
// (No CSS rotate on the shape: rotating a div was what made the original
// diamond markers look soft once dozens overlapped.)
function mkIcon(k){
  const html='<div class="kpin-dot" style="background:'+catColour(k)+'"><span>'+(IC[k]||'')+'</span></div>';
  // The class is what lets a selected bus route push these into the background
  // (see .route-focus below) and what lets a label know a pin is in its way.
  return L.divIcon({html:html,className:'kpin',iconSize:[30,30],iconAnchor:[15,15],popupAnchor:[0,-16]});
}
// Wraps just the phone-number-looking part of a string in a tel: link, leaving any
// trailing note (an email, an office name in brackets, etc.) as plain text.
// Second alternative: the short civic lines this app also quotes inline in a
// task's help text (2-1-1, 8-1-1, 9-1-1) — three single digits, hyphens
// required between each so it can never match a prefix of a longer, grouped
// number (validate.py's own phone-literal scan is why no example of one is
// spelled out here).
function phoneHtml(str){
  // 2026-09-15: was missing the g flag, so a string with more than one
  // phone-shaped substring (the hardship card's four-shelter note, added this
  // pass) only linkified the first and silently left the rest as plain,
  // unclickable text — every previous caller happened to pass a string with
  // exactly one number, which is why this went unnoticed until now.
  // 2026-10-19: a leading "1-" stayed outside the link and wrapped onto its own line ("1-" / "866-866-0800")
  return str.replace(/((?:\b1[-\s])?\d{3}[-\s]?\d{3}[-\s]?\d{4}|\b310-\d{4}\b|\b\d-\d-\d\b)/g, m=>'<a href="tel:'+m.replace(/[^\d]/g,'')+'">'+m+'</a>');
}
// ---- structured opening hours -> localised text -------------------------
// Hours are stored as data ({r:[[dayFrom,dayTo,openMin,closeMin,approx]], a:24h,
// s:service times, k:keyed message, q:qualifier, se:season) rather than as a
// pre-written Chinese string, so every language renders them from the same source.
function fmtClock(min,l){
  const wrapped=min%1440, h=Math.floor(wrapped/60), m=wrapped%60;
  if(l==='en'){const ap=h<12?'AM':'PM',hh=(h%12)||12;return hh+(m?':'+String(m).padStart(2,'0'):'')+' '+ap;}
  if(l==='fr')return h+' h'+(m?' '+String(m).padStart(2,'0'):'');
  return h+':'+String(m).padStart(2,'0');
}
function fmtDays(d1,d2,l){
  const u=UI[l];
  if(d1===1&&d2===7)return u.dAll;
  if(d1===6&&d2===7)return u.dWk;
  if(d1===d2)return u.d[d1-1];
  return u.d[d1-1]+u.dsep+u.d[d2-1];
}
function fmtHours(h,l){
  if(!h)return '';
  const u=UI[l];
  if(typeof h==='string')return h;
  const bits=[];
  if(h.a)bits.push(u.h24);
  if(h.k&&u[h.k])bits.push(u[h.k]);
  (h.r||[]).forEach(([d1,d2,o,c,ap])=>{
    const day=fmtDays(d1,d2,l);
    if(o===null)bits.push(day);
    else if(c===null)bits.push(day+' '+fmtClock(o,l)+' '+u.fromT);
    else bits.push(day+' '+fmtClock(o,l)+u.tsep+(ap?u.approx+' ':'')+fmtClock(c,l));
  });
  if(h.s&&h.s.length)bits.push(u.lSvc+u.colon+h.s.map(([d,t])=>u.d[d-1]+' '+fmtClock(t,l)).join(' / '));
  // Closed days are stated, not merely implied by their absence from the ranges.
  if((h.r||[]).length&&!h.a&&!h.k){
    const covered=new Set();
    h.r.forEach(([d1,d2])=>{for(let d=d1;d<=d2;d++)covered.add(d);});
    const shut=[1,2,3,4,5,6,7].filter(d=>!covered.has(d));
    if(shut.length&&shut.length<7){
      const weekendOnly=shut.length===2&&shut[0]===6&&shut[1]===7;
      bits.push(u.closedLabel+u.colon+(weekendOnly?u.dWk:shut.map(d=>u.d[d-1]).join(u.listSep)));
    }
  }
  let out=bits.join(' · ');
  if(h.se)out=u[h.se==='summer'?'seSummer':'seWinter']+' '+out;
  if(h.q&&u[h.q])out+=' ('+u[h.q]+')';
  return out;
}
// Entry stamps are stored as YYYY-MM and shown in the reader's own conventions,
// so they read consistently with the dated disclaimer rather than as raw data.
function fmtStamp(v,l){
  const [y,m]=v.split('-').map(Number);
  const mn=UI[l].months[m-1];
  if(l==='zh')return y+'年'+m+'月';
  if(l==='ko')return y+'년 '+m+'월';
  if(l==='ja')return y+'年'+m+'月';
  if(l==='en')return mn+' '+y;
  if(l==='fr')return mn+' '+y;
  return mn+' de '+y;
}
// A correction is only useful if it says WHICH record and WHICH version. The
// header link opens an empty mail; this one arrives pre-identified.
function reportHref(p){
  const u=UI[L_];
  const subj=u.fbSubject+': '+p.n;
  const body=[u.fbPlace+': '+p.n,
              u.fbId+': '+p.id,
              u.fbCategory+': '+catLabel(p.c),
              u.fbLang+': '+L_,
              u.fbVersion+': '+DATA_VERSION,
              (location.protocol.indexOf('http')===0?u.fbUrl+': '+location.href:''),
              '','---',u.fbPrompt,''].filter(Boolean).join('\n');
  return 'mailto:'+contactEmail()+'?subject='+encodeURIComponent(subj)+'&body='+encodeURIComponent(body);
}
// Where a record's factual fields come from. 'official' means the operator's own
// site is on file and the reader can check it; 'places' means they cannot, and
// should phone ahead; 'own' is a first-hand check by the compiler. Rendered as a
// small chip so credibility is visible per record rather than only in a blanket
// disclaimer at the bottom of the page.
UI.zh.shareTitle='🔗 分享这个视图';UI.zh.shareLead='分享出去的链接会带上你现在的语言、区域、分类和搜索词——对方打开看到的就是这一屏。';UI.zh.shareNative='📲 用系统分享…（微信、LINE、KakaoTalk、短信等）';UI.zh.shareCopy='复制链接';UI.zh.shareNote='说明：微信和 TikTok 没有提供“分享网页链接”的接口，所以这里没有它们的按钮。在手机上用上面的“系统分享”可以直接发到微信；在电脑上请复制链接后粘贴到微信。韩国的 KakaoTalk 同理。';UI.zh.shareEmail='邮件';UI.zh.shareSms='短信';
UI.en.shareTitle='🔗 Share this view';UI.en.shareLead='The link carries your current language, area, category and search — whoever opens it lands on this same screen.';UI.en.shareNative='📲 Share via your device… (WeChat, LINE, KakaoTalk, Messages…)';UI.en.shareCopy='Copy link';UI.en.shareNote='Note: WeChat and TikTok offer no share-a-link endpoint, so there are no buttons for them. On a phone, "Share via your device" reaches WeChat directly; on a computer, copy the link and paste it into WeChat. The same applies to KakaoTalk.';UI.en.shareEmail='Email';UI.en.shareSms='Messages';
UI.fr.shareTitle='🔗 Partager cette vue';UI.fr.shareLead='Le lien conserve votre langue, secteur, catégorie et recherche — la personne qui l’ouvre voit le même écran.';UI.fr.shareNative='📲 Partager via l’appareil… (WeChat, LINE, KakaoTalk, Messages…)';UI.fr.shareCopy='Copier le lien';UI.fr.shareNote='À noter : WeChat et TikTok n’offrent aucun point d’entrée pour partager un lien, d’où l’absence de boutons. Sur téléphone, « Partager via l’appareil » atteint WeChat directement; sur ordinateur, copiez le lien et collez-le dans WeChat. Idem pour KakaoTalk.';UI.fr.shareEmail='Courriel';UI.fr.shareSms='Messages';
UI.es.shareTitle='🔗 Compartir esta vista';UI.es.shareLead='El enlace conserva su idioma, zona, categoría y búsqueda — quien lo abra verá esta misma pantalla.';UI.es.shareNative='📲 Compartir desde el dispositivo… (WeChat, LINE, KakaoTalk, Mensajes…)';UI.es.shareCopy='Copiar enlace';UI.es.shareNote='Nota: WeChat y TikTok no ofrecen un punto de entrada para compartir enlaces, por eso no hay botones para ellos. En el celular, «Compartir desde el dispositivo» llega a WeChat directamente; en la computadora, copie el enlace y péguelo en WeChat. Lo mismo vale para KakaoTalk.';UI.es.shareEmail='Correo';UI.es.shareSms='Mensajes';
UI.ko.shareTitle='🔗 이 화면 공유';UI.ja.shareTitle='🔗 この画面を共有';UI.ko.shareLead='링크에는 현재 언어·지역·분류·검색어가 담겨 있어, 받는 사람도 같은 화면을 보게 됩니다.';UI.ja.shareLead='このリンクには現在の言語、エリア、カテゴリー、検索語が含まれており、開いた相手も同じ画面を見ることができます。';UI.ko.shareNative='📲 기기로 공유… (위챗, LINE, 카카오톡, 메시지 등)';UI.ja.shareNative='📲 端末で共有…（WeChat、LINE、KakaoTalk、メッセージなど）';UI.ko.shareCopy='링크 복사';UI.ja.shareCopy='リンクをコピー';UI.ko.shareNote='참고: 위챗과 TikTok은 링크 공유용 진입점을 제공하지 않아 별도 버튼이 없습니다. 휴대폰에서는 위의 “기기로 공유”로 위챗에 바로 보낼 수 있고, PC에서는 링크를 복사해 위챗에 붙여넣으세요. 카카오톡도 마찬가지입니다.';UI.ja.shareNote='ご注意: WeChatとTikTokはリンク共有用のエンドポイントを提供していないため、専用のボタンはありません。スマートフォンでは「端末で共有」からWeChatに直接送れますが、パソコンではリンクをコピーしてWeChatに貼り付けてください。KakaoTalkも同様です。';UI.ko.shareEmail='이메일';UI.ja.shareEmail='メール';UI.ko.shareSms='메시지';UI.ja.shareSms='メッセージ';
// A fourth, lowest tier (2026-09-07). Entries added to fill a coverage gap but
// not yet phone-verified were carrying src="stub-pending-verify", which no tier
// recognised — srcHTML() then rendered no chip at all, so the least-checked rows
// on the map were the only ones showing no provenance whatsoever. Making the
// tier explicit keeps the maintainer's own marker and, more importantly, tells
// the reader to call first. export-open.py still exports only official+own, so
// these stay out of the shareable subset until they are promoted.
const SRC_KINDS={official:['srcOfficial','srcOfficialTip'],
                 places:['srcPlaces','srcPlacesTip'],
                 // 2026-09-24: a government dataset is its own kind of source — more
                 // reliable than a third-party map, less than the organisation's own page
                 opendata:['srcOpenData','srcOpenDataTip'],
                 own:['srcOwn','srcOwnTip'],
                 'stub-pending-verify':['srcStub','srcStubTip']};
function srcHTML(p,u){
  const kind=SRC_KINDS[p.src];
  if(!kind)return '';
  return '<span class="pv-src src-'+String(p.src).split('-')[0]+'" title="'+u[kind[1]].replace(/"/g,'&quot;')+'">'
    +u.lSource+': '+u[kind[0]]+'</span> · ';
}
function popup(p,idx){
  const u=UI[L_];
  const starChar=ico('star'),starActive=favorites.has(p.id)?' active':'';
  // A screen reader could hear the star but not whether it was on. The label
  // states the action, aria-pressed states the current value.
  const faved=favorites.has(p.id);
  // The name is the one thing every reader opened the popup for, so it leads —
  // the category/region tags used to sit above it, which put metadata ahead of the
  // primary fact. They now sit as a supporting line right under the name instead.
  const pick=!!p.pick||/^⭐/.test(p.n), nm=p.n.replace(/^[⭐\s]+/,'');
  let b='<div class="pt">'+esc(nm)+'<button class="fav-star'+starActive+'" data-i="'+idx+'" onclick="toggleFav(this,event)" aria-pressed="'+faved+'" aria-label="'+(faved?u.favRemove:u.favAdd)+'">'+starChar+'</button></div>';
  b+='<div class="ptags"><span class="pchip pchip-id" style="--cc:'+catColour(p.c)+';--ci:'+catInk(p.c)+'">'
    +'<span class="pchip-ic" aria-hidden="true">'+IC[p.c]+'</span>'+catLabel(p.c)+'</span>'
    +'<span class="pchip pchip-meta pv-cut" title="'+esc(regLabel(p.g))+'"><span>'+esc(regShort(p.g))+'</span></span>';
  // A qualifier that used to sit inside the Chinese name ("（韩餐）") is data now,
  // so every language gets it instead of a parenthetical it cannot read.
  if(p.tag&&u[p.tag])b+='<span class="pchip pchip-meta">'+u[p.tag]+'</span>';
  // the ⭐ in a name is an editor's pick; said in words, and kept apart from
  // the reader's own ☆ favourite
  if(pick)b+='<span class="pchip pchip-pick">'+ico('star')+esc(u.recPick)+'</span>';
  b+='</div>';
  // The theme pills are the discovery surface for the second axis: someone who
  // never opens the filter panel still learns that this park counts as "free" and
  // "kids & family", and that those words are things the map can be filtered by.
  // 2026-09-10: the pills used to sit above the address, so a library showed
  // seven tags before its street. They now follow the hours, and beyond four
  // the rest fold behind a "+N" the reader can open.
  let themesHtml='';
  if(p.t&&p.t.length){
    const ks=TORDER.filter(k=>p.t.indexOf(k)>=0);
    const pill=k=>'<span class="pv-theme">'+emojiIcon(TIC[k])+themeLabel(k)+'</span>';
    themesHtml='<div class="pv-themes">'+ks.slice(0,4).map(pill).join('')
      +(ks.length>4?'<button type="button" class="pv-theme pv-more-t" onclick="this.parentNode.classList.add(\'all\')">+'+(ks.length-4)+'</button><span class="pv-rest">'+ks.slice(4).map(pill).join('')+'</span>':'')
      +'</div>';
  }
  b+='<div class="pr">'+p.a+'</div>';
  if(p.precision==='low')b+='<div class="pv-approx">'+u.lowPrecision+'</div>';
  if(p.sameComplex&&p.sameComplex.length){
    const sibs=p.sameComplex.map(id=>P.find(x=>x.id===id)).filter(Boolean);
    if(sibs.length)b+='<div class="pv-approx">'+u.sameComplexLabel
      +sibs.map(x=>x.n+' ('+catLabel(x.c)+')').join(' · ')+'</div>';
  }
  // Which task cards name this place as their "where do I go". Usually one;
  // Service BC carries two (MSP, and the health card that comes with it).
  const tks=(typeof TASKS!=='undefined')?TASKS.filter(t=>t.place===p.id):[];
  // 2026-09-24: phone, email and hours are one grid so their values share a
  // single left edge. The task card used to sit above them and pushed the core
  // facts down by about 90px; it now follows the hours.
  let kv='';
  if(p.p)kv+='<span class="pl">'+u.lPhone+'</span><span class="pval">'+phoneHtml(p.p)
    +(p.pq&&u[p.pq]?' <span class="pq">('+u[p.pq]+')</span>':'')+'</span>';
  if(p.e)kv+='<span class="pl">'+u.lEmail+'</span><span class="pval"><a href="mailto:'+p.e+'">'+p.e+'</a></span>';
  // Saying nothing about hours reads as "no hours"; say which it is instead.
  const hTxt=p.h?fmtHours(p.h,L_):(CITY.openAir.indexOf(p.c)>=0?u.hOnSite:u.hUnknown);
  const os=openState(p.h);
  const pill=os?('<span class="pv-open '+(os.open?'on':'off')+'">'+(os.open?u.openNowYes:u.openNowNo)
    +(os.open&&os.until!==null?' · '+u.openUntil+' '+fmtClock(os.until,L_):'')+'</span>')
    :(p.h&&!p.h.a&&isHolidayToday()?'<span class="pv-open hol">'+esc(u.holidayPill)+'</span>':'');
  kv+='<span class="pl">'+u.lHours+'</span><span class="pval">'+pill+hTxt+'</span>';
  b+='<div class="pkv">'+kv+'</div>';
  if(tks.length){
    b+='<div class="pv-task"><b>'+u.pvTaskLead+'</b>'
      +tks.map(t=>'<div>'+esc(taskText(t.t))+' <button type="button" class="pv-task-go" data-task="'+esc(t.id)+'">'+esc(u.pvTaskGo)+'</button></div>').join('')
      +'</div>';
  }
  b+=themesHtml;
  const nTxt=noteText(p);
  if(nTxt)b+='<div class="pn">'+nTxt+'</div>';
  // This per-place "checked on" date and the page-wide "Last verified" date in
  // Data Notes measure two different things (this one record vs. the whole
  // dataset) — a tooltip says so here rather than leaving the reader to notice
  // they don't always match.
  b+='<div class="pv">'+srcHTML(p,u)+(p.v?(p.src==='places'
      ?'<span class="pv-verified" title="'+u.lListedTip.replace(/"/g,'&quot;')+'">'+u.lListed+' '+fmtStamp(p.v,L_)+'</span> · '
      :'<span class="pv-verified" title="'+u.lVerifiedTip.replace(/"/g,'&quot;')+'">'+u.lVerified+' '+fmtStamp(p.v,L_)+'</span> · '):'')
    +'<a class="pv-report" href="'+reportHref(p)+'">'+u.reportIssue+'</a></div>';
  // Destination is the place name + address (not raw lat/lng) so the map app shows
  // a real, readable place to navigate to instead of a confusing pair of numbers.
  // A destination string with no civic number ("Cooney Bay") makes the maps app
  // guess; fall back to the exact coordinates in that case.
  const du=distFromUser(p);
  const ns=nearestStop(p);
  if(du!==null||ns){
    b+='<div class="pv-near">';
    if(du!==null)b+='<span class="pv-dist">'+ico('pin')+fmtDist(du)+' '+u.pvFromYou+' · '+u.walkMin(Math.max(1,Math.round(du/80)))+'</span>';
    if(ns)b+='<span class="pv-stop">'+ico('bus')+u.pvNearStop+u.colon+esc(ns.name)+' ('+fmtDist(ns.d)+') · '+u.pvRoutes+u.colon
      +ns.routes.map(k=>'<button type="button" class="pv-route" data-route="'+k+'" style="--rc:'+(BR[k].co||'#555')+'">'+k+'</button>').join(' ')+'</span>';
    b+='</div>';
  }
  const hasCivic=/\d/.test(p.a||'');
  // an area can name its own municipality (Kelowna: West Kelowna is a different city, 2026-10-04)
  const dest=hasCivic?encodeURIComponent(p.n+', '+p.a+((CITY.navSuffixArea||{})[p.g]||CITY.navSuffix))
                     :(p.lat+','+p.lng);
  const phoneDigits=p.p?(p.p.match(/\d{3}[-\s]?\d{3}[-\s]?\d{4}/)||[])[0]:null;
  b+='<div class="pact">';
  // data-cta lets the global click delegate below record the strongest possible
  // intent signal — a tap on the call/web/navigate button — without sprinkling
  // trackEvent calls into this render function (one of the popup's two phone
  // digits forms already runs through it).
  b+='<a class="pact-btn primary" data-cta="nav" data-pid="'+p.id+'" data-pcat="'+p.c+'" href="https://www.google.com/maps/dir/?api=1&destination='+dest+'" target="_blank" rel="noopener"><span class="pact-ic">'+ico('nav')+'</span>'+u.lNav+'</a>';
  if(phoneDigits)b+='<a class="pact-btn" data-cta="call" data-pid="'+p.id+'" data-pcat="'+p.c+'" href="tel:'+phoneDigits.replace(/[^\d]/g,'')+'"><span class="pact-ic">'+ico('phone')+'</span>'+u.lCall+'</a>';
  if(p.w)b+='<a class="pact-btn" data-cta="web" data-pid="'+p.id+'" data-pcat="'+p.c+'" href="'+p.w+'" target="_blank" rel="noopener"><span class="pact-ic">'+ico('globe')+'</span>'+u.lWeb2+'</a>';
  b+='</div>';
  return b;
}

