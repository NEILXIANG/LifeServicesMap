#!/usr/bin/env python3
"""Phase 1 — safety and trust. Every replacement asserts its exact count."""
import re, sys, json
sys.path.insert(0, '.')
import kamdata

E = 'src/engine.html'
D = 'src/data-kamloops.js'
s = open(E, encoding='utf-8').read()
d = open(D, encoding='utf-8').read()

def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count:
        sys.exit('expected %d of %r, found %d' % (count, old[:80], n))
    return src.replace(old, new)

# ---------------------------------------------------------------- (a) event log
s = rep(s, "function flushEvents(){\n  try{localStorage.setItem(_EV_KEY,JSON.stringify(_evBuf));}catch(e){",
        "function flushEvents(){\n"
        "  // 2026-09-21: the local copy exists only for the maintainer's ?debug=1\n"
        "  // panel. On an ordinary visit it was a readable history of every search\n"
        "  // and card, left on a device that may be shared — so it stays in memory.\n"
        "  if(!_IS_DEBUG)return;\n"
        "  try{localStorage.setItem(_EV_KEY,JSON.stringify(_evBuf));}catch(e){")
s = rep(s, "try{\n  const saved=localStorage.getItem(_EV_KEY);\n  if(saved){",
        "try{\n  if(!_IS_DEBUG)localStorage.removeItem(_EV_KEY);   // clears what older versions left behind\n"
        "  const saved=_IS_DEBUG?localStorage.getItem(_EV_KEY):null;\n  if(saved){")

# ---------------------------------------------------------------- (g) crisis regex
CRISIS = r"""// 2026-09-21: a search that says someone may be in danger gets the lines that
// answer, above any results, and the words themselves are never uploaded.
const _CRISIS_RE=/\b(suicid\w*|kill my ?self|kill me|want to die|self[- ]?harm\w*|overdos\w*|abus\w*|violen\w*|domestic|hits me|beats me|rape\w*|sexual assault|assault\w*|unsafe|in danger|crisis|crise|dv|me tuer|mourir|agress\w*|agresi\w*|matarme|morir|maltrato\w*)\b|自杀|想死|不想活|轻生|自残|家暴|暴力|被打|打我|虐待|性侵|强奸|危机|자살|죽고 싶|자해|폭력|학대|폭행|自殺|死にたい|自傷|性暴力/i;
function isCrisisQuery(q){return !!q&&_CRISIS_RE.test(String(q));}
const _evBuf=[];"""
s = rep(s, "const _evBuf=[];", CRISIS)
s = rep(s, "    if(props&&typeof props.q==='string'){\n      safeProps=Object.assign({},props,{q:_sanitiseQuery(props.q)});\n    }",
        "    if(props&&typeof props.q==='string'){\n      safeProps=Object.assign({},props,{q:isCrisisQuery(props.q)?'[crisis]':_sanitiseQuery(props.q)});\n    }")

# crisis block in the empty state (and above results when there are some)
s = rep(s, "function renderEmptyState(v,searching,filtered){\n  const el=document.getElementById('emptyState'),u=UI[L_];\n  if(v>0){el.hidden=true;el.innerHTML='';_lastEmptyKind=null;return;}",
        "function crisisHtml(){\n"
        "  const u=UI[L_];\n"
        "  return '<div class=\"crisis-block\"><p class=\"crisis-lead\">'+esc(u.crisisLead)+'</p>'+hotlineHtml(false)+localCrisisHtml()\n"
        "    +'<p class=\"crisis-more\">'+esc(u.crisisMore)+'</p></div>';\n"
        "}\n"
        "function renderEmptyState(v,searching,filtered){\n"
        "  const el=document.getElementById('emptyState'),u=UI[L_];\n"
        "  const crisis=searching&&isCrisisQuery(searchRaw||searchTerm);\n"
        "  if(v>0){\n"
        "    _lastEmptyKind=null;\n"
        "    if(crisis){el.hidden=false;el.dataset.kind='crisis';el.innerHTML=crisisHtml();}\n"
        "    else{el.hidden=true;el.innerHTML='';}\n"
        "    return;\n"
        "  }")
s = rep(s, "  el.innerHTML='<p>'+msg+'</p>'+(selectedRoute?'<p class=\"empty-route\">'+esc(u.emptyRouteNote)+'</p>':'')+(onlyOpen&&!searching?hotlineHtml(false):'');",
        "  el.innerHTML=(crisis?crisisHtml():'')+'<p>'+msg+'</p>'+(selectedRoute?'<p class=\"empty-route\">'+esc(u.emptyRouteNote)+'</p>':'')+(onlyOpen&&!searching?hotlineHtml(false):'');")

# local crisis line helper (city data, rendered by the engine)
s = rep(s, "function hotlineHtml(compact){",
        "function localCrisisHtml(){\n"
        "  const c=CITY.localCrisis;if(!c)return '';\n"
        "  return '<p class=\"help-local\">'+esc(c.note[L_]||c.note.en)+' <a href=\"tel:'+esc(c.n.replace(/[^\\d]/g,''))+'\"><b>'+esc(c.n)+'</b></a></p>';\n"
        "}\n"
        "function hotlineHtml(compact){")

# ---------------------------------------------------------------- (b) no search in the address bar
s = rep(s, "    if(searchTerm)q.set('q',searchInputEl.value.trim());\n",
        "    // 2026-09-21: the search box stays out of the address bar — it is what\n"
        "    // lands in browser history on a shared device. A share adds it on purpose.\n")
s = rep(s, "function copyShareLink(){\n  const u=UI[L_],href=location.href;",
        "// The link a reader chooses to send: the address bar plus the search, when\n"
        "// there is one and it is not a cry for help.\n"
        "function shareHref(){\n"
        "  try{\n"
        "    const raw=searchInputEl.value.trim();\n"
        "    if(!searchTerm||!raw||isCrisisQuery(raw))return location.href;\n"
        "    const x=new URL(location.href);x.searchParams.set('q',raw);return x.toString();\n"
        "  }catch(e){return location.href;}\n"
        "}\n"
        "function copyShareLink(){\n  const u=UI[L_],href=shareHref();")
s = rep(s, "    a.href=t.url(location.href,shareText());", "    a.href=t.url(shareHref(),shareText());")
s = rep(s, "  navigator.share({title:shareText(),url:location.href}).then(", "  navigator.share({title:shareText(),url:shareHref()}).then(")

# ---------------------------------------------------------------- (c) no card id on ticks
s = rep(s, "trackEvent('task_step',{id:id,action:on?'tick':'untick',n:cur.size,of:stepsOf(t)});",
        "trackEvent('task_step',{action:on?'tick':'untick',n:cur.size,of:stepsOf(t)});")

# ---------------------------------------------------------------- (d) truthful one-liners
s = rep(s, "UI.zh.taskLocalOnly='勾选只存在这台设备的浏览器里，不会上传。';UI.en.taskLocalOnly='Ticks stay in this browser on this device. Nothing is uploaded.';UI.fr.taskLocalOnly='Les coches restent dans ce navigateur, sur cet appareil. Rien n’est envoyé.';UI.es.taskLocalOnly='Las marcas se quedan en este navegador, en este dispositivo. No se envía nada.';UI.ko.taskLocalOnly='체크 표시는 이 기기의 브라우저에만 저장되며 전송되지 않습니다.';UI.ja.taskLocalOnly='チェックはこの端末のブラウザにのみ保存され、送信されません。';",
        "UI.zh.taskLocalOnly='勾选只存在这台设备的浏览器里；用同一台设备的人也能看到。';UI.en.taskLocalOnly='Ticks are saved only in this browser, on this device — anyone who uses this device can see them.';UI.fr.taskLocalOnly='Les coches sont enregistrées seulement dans ce navigateur, sur cet appareil — toute personne qui l’utilise peut les voir.';UI.es.taskLocalOnly='Las marcas se guardan solo en este navegador, en este dispositivo; quien use este dispositivo puede verlas.';UI.ko.taskLocalOnly='체크 표시는 이 기기의 브라우저에만 저장됩니다. 이 기기를 쓰는 다른 사람도 볼 수 있습니다.';UI.ja.taskLocalOnly='チェックはこの端末のブラウザにだけ保存されます。この端末を使う人は誰でも見られます。';")
s = rep(s, "UI.zh.fuSafe='免费 · 不用注册 · 不收集你的任何信息';UI.en.fuSafe='Free · no sign-up · nothing collected about you';UI.fr.fuSafe='Gratuit · sans inscription · rien de collecté sur vous';UI.es.fuSafe='Gratis · sin registro · no se recopila nada sobre usted';UI.ko.fuSafe='무료 · 가입 없음 · 개인정보 수집 없음';UI.ja.fuSafe='無料 · 登録不要 · あなたの情報は集めません';",
        "UI.zh.fuSafe='免费 · 不用注册 · 不要你的姓名和位置';UI.en.fuSafe='Free · no sign-up · never asks your name or sends your location';UI.fr.fuSafe='Gratuit · sans inscription · ni votre nom ni votre position ne sont envoyés';UI.es.fuSafe='Gratis · sin registro · no pide su nombre ni envía su ubicación';UI.ko.fuSafe='무료 · 가입 없음 · 이름을 묻지 않고 위치를 보내지 않음';UI.ja.fuSafe='無料 · 登録不要 · 名前を聞かず、位置情報も送りません';")

# ---------------------------------------------------------------- (f) footer numbers are links, plus 9-8-8
FOOT = {
 '🚨 <b>911</b>（报警 / 火警 / 救护）· <b>8-1-1</b>（非紧急健康咨询，有中文翻译）· <b>250-828-3000</b>（RCMP非紧急）':
 '🚨 <a href=\\"tel:911\\"><b>911</b></a>（报警 / 火警 / 救护）· <a href=\\"tel:988\\"><b>9-8-8</b></a>（自杀危机，24 小时）· <a href=\\"tel:811\\"><b>8-1-1</b></a>（非紧急健康咨询，有中文翻译）· <a href=\\"tel:2508283000\\"><b>250-828-3000</b></a>（RCMP非紧急）',
 '🚨 Emergency: <b>911</b> · <b>8-1-1</b> (non-emergency health advice) · <b>250-828-3000</b> (RCMP non-emergency)':
 '🚨 Emergency: <a href=\\"tel:911\\"><b>911</b></a> · <a href=\\"tel:988\\"><b>9-8-8</b></a> (suicide crisis, 24 h) · <a href=\\"tel:811\\"><b>8-1-1</b></a> (non-emergency health advice) · <a href=\\"tel:2508283000\\"><b>250-828-3000</b></a> (RCMP non-emergency)',
 '🚨 Urgence : <b>911</b> · <b>8-1-1</b> (conseils santé non urgents, interprète en français sur demande) · <b>250-828-3000</b> (GRC non urgent)':
 '🚨 Urgence : <a href=\\"tel:911\\"><b>911</b></a> · <a href=\\"tel:988\\"><b>9-8-8</b></a> (crise suicidaire, 24 h) · <a href=\\"tel:811\\"><b>8-1-1</b></a> (conseils santé non urgents, interprète en français sur demande) · <a href=\\"tel:2508283000\\"><b>250-828-3000</b></a> (GRC non urgent)',
 '🚨 Emergencias: <b>911</b> · <b>8-1-1</b> (asesoría de salud no urgente, intérprete en español a pedido) · <b>250-828-3000</b> (RCMP no urgente)':
 '🚨 Emergencias: <a href=\\"tel:911\\"><b>911</b></a> · <a href=\\"tel:988\\"><b>9-8-8</b></a> (crisis suicida, 24 h) · <a href=\\"tel:811\\"><b>8-1-1</b></a> (asesoría de salud no urgente, intérprete en español a pedido) · <a href=\\"tel:2508283000\\"><b>250-828-3000</b></a> (RCMP no urgente)',
 '🚨 긴급 전화: <b>911</b>(긴급상황) · <b>8-1-1</b>(비응급 건강 상담, 한국어 통역 요청 가능) · <b>250-828-3000</b>(RCMP 비응급)':
 '🚨 긴급 전화: <a href=\\"tel:911\\"><b>911</b></a>(긴급상황) · <a href=\\"tel:988\\"><b>9-8-8</b></a>(자살 위기, 24시간) · <a href=\\"tel:811\\"><b>8-1-1</b></a>(비응급 건강 상담, 한국어 통역 요청 가능) · <a href=\\"tel:2508283000\\"><b>250-828-3000</b></a>(RCMP 비응급)',
 '🚨 緊急電話: <b>911</b>（緊急時）· <b>8-1-1</b>（非緊急の健康相談、日本語通訳依頼可）· <b>250-828-3000</b>（RCMP非緊急）':
 '🚨 緊急電話: <a href=\\"tel:911\\"><b>911</b></a>（緊急時）· <a href=\\"tel:988\\"><b>9-8-8</b></a>（自殺の危機、24時間）· <a href=\\"tel:811\\"><b>8-1-1</b></a>（非緊急の健康相談、日本語通訳依頼可）· <a href=\\"tel:2508283000\\"><b>250-828-3000</b></a>（RCMP非緊急）',
}
for k, v in FOOT.items():
    s = rep(s, k, v)
s = rep(s, "  .footer-emergency b{color:inherit;}",
        "  .footer-emergency b{color:inherit;}\n  .footer-emergency a{color:inherit;text-decoration:none;}\n  .footer-emergency a:hover b{text-decoration:underline;}")

# ---------------------------------------------------------------- (e) hotlines data
OLD_HL = "  help:{settle:'778-470-6101', info:'211'},\n  hotlines:[{n:'911',t:'emergency'},{n:'310-6789',t:'mental'},{n:'1-800-784-2433',t:'suicide'},{n:'9-8-8',t:'suicide'},{n:'811',t:'health'},{n:'211',t:'info'}]\n};"
NEW_HL = """  help:{settle:'778-470-6101', info:'211'},
  // 2026-09-21: only lines that answer around the clock. 2-1-1 left this list —
  // bc211 answers 9am–9pm on weekdays (the hardship card says so) — and sits in
  // the Help sheet with its hours. VictimLink and KUU-US are 24/7, toll-free,
  // and were already named in the guide text.
  hotlines:[{n:'911',t:'emergency'},{n:'310-6789',t:'mental'},{n:'1-800-784-2433',t:'suicide'},{n:'9-8-8',t:'suicide'},{n:'811',t:'health'},{n:'1-800-563-0808',t:'victim'},{n:'1-800-588-8717',t:'indigenous'}],
  // A local, non-police crisis team (KAFS Community Response to Crisis Line,
  // kafs.ca/crcl-program, checked 2026-09-21). Not 24 hours, so not a hotline.
  localCrisis:{n:'778-470-2725',src:'https://kafs.ca/crcl-program',
    note:{en:'Kamloops crisis team (not police), daily 11am–11pm, call, text or WhatsApp, age 13+:',
          fr:'Équipe de crise de Kamloops (pas la police), tous les jours 11 h–23 h, appel, texto ou WhatsApp, dès 13 ans :',
          es:'Equipo de crisis de Kamloops (no es la policía), todos los días 11–23 h, llamada, texto o WhatsApp, desde 13 años:',
          zh:'Kamloops 危机小组（不是警察），每天 11:00–23:00，可打电话、发短信或 WhatsApp，13 岁以上：',
          ko:'Kamloops 위기 대응팀(경찰 아님), 매일 11:00–23:00, 전화·문자·WhatsApp, 13세 이상:',
          ja:'Kamloops の危機対応チーム（警察ではない）、毎日11:00–23:00、電話・SMS・WhatsApp、13歳以上：'}}
};"""
d = rep(d, OLD_HL, NEW_HL)

# ---------------------------------------------------------------- UI strings
NEWUI = {
 'hot_victim': dict(zh='犯罪 / 家暴受害者支援（VictimLink）', en='victims of crime or abuse (VictimLink)', fr='victimes de crime ou de violence (VictimLink)', es='víctimas de delito o violencia (VictimLink)', ko='범죄·폭력 피해자 지원(VictimLink)', ja='犯罪・暴力の被害者支援（VictimLink）'),
 'hot_indigenous': dict(zh='原住民危机热线（KUU-US）', en='Indigenous crisis line (KUU-US)', fr='ligne de crise autochtone (KUU-US)', es='línea de crisis indígena (KUU-US)', ko='원주민 위기 상담(KUU-US)', ja='先住民のための危機ライン（KUU-US）'),
 'helpBtnLabel': dict(zh='📞 求助', en='📞 Help now', fr='📞 Aide', es='📞 Ayuda', ko='📞 도움', ja='📞 相談'),
 'helpBtnShort': dict(zh='求助', en='Help', fr='Aide', es='Ayuda', ko='도움', ja='相談'),
 'helpTitle': dict(zh='📞 需要帮助', en='📞 Help now', fr='📞 Besoin d’aide', es='📞 Ayuda ahora', ko='📞 지금 도움받기', ja='📞 いま相談する'),
 'helpLead': dict(zh='现在有危险就打 911。其他情况，选一个合适的电话——都是免费的。', en='In danger right now? Call 911. Otherwise, pick the line that fits — they are free.', fr='En danger maintenant ? Composez le 911. Sinon, choisissez la ligne qui vous convient — elles sont gratuites.', es='¿En peligro ahora mismo? Llame al 911. Si no, elija la línea que le sirva: son gratuitas.', ko='지금 위험하다면 911에 전화하세요. 그 밖에는 맞는 전화를 고르세요 — 모두 무료입니다.', ja='いま危険なら911へ。それ以外は、合う窓口を選んでください。どれも無料です。'),
 'helpInfo': dict(zh='帮你找本地合适的机构，可用母语——工作日 9:00–21:00，不是 24 小时', en='finds the right local service, in your language — weekdays 9am–9pm, not 24 hours', fr='trouve le bon service local, dans votre langue — en semaine 9 h–21 h, pas 24 h sur 24', es='encuentra el servicio local adecuado, en su idioma — días laborables 9–21 h, no 24 horas', ko='맞는 지역 서비스를 모국어로 안내 — 평일 9:00–21:00, 24시간 아님', ja='地域の合う窓口を母語で案内 — 平日9:00–21:00、24時間ではありません'),
 'helpExit': dict(zh='立即离开这个页面', en='Leave this page now', fr='Quitter cette page maintenant', es='Salir de esta página ahora', ko='지금 이 페이지 나가기', ja='今すぐこのページを離れる'),
 'helpExitNote': dict(zh='会在这个标签页打开 Google。浏览记录里仍可能留有本站——和别人共用设备时，建议用浏览器的无痕模式。', en='Opens Google in this tab. This site may still show in your browser history — on a shared device, a private window is safer.', fr='Ouvre Google dans cet onglet. Ce site peut rester dans l’historique — sur un appareil partagé, une fenêtre privée est plus sûre.', es='Abre Google en esta pestaña. Este sitio puede seguir en el historial; en un dispositivo compartido, una ventana privada es más segura.', ko='이 탭에서 Google을 엽니다. 방문 기록에 이 사이트가 남을 수 있으니, 함께 쓰는 기기라면 시크릿 창이 더 안전합니다.', ja='このタブでGoogleを開きます。閲覧履歴にこのサイトが残ることがあるので、共用の端末ではプライベートウィンドウが安全です。'),
 'helpClear': dict(zh='清除这台设备上的记录', en='Clear what this site saved on this device', fr='Effacer ce que ce site a enregistré sur cet appareil', es='Borrar lo que este sitio guardó en este dispositivo', ko='이 사이트가 이 기기에 저장한 내용 지우기', ja='このサイトがこの端末に保存した内容を消す'),
 'helpClearConfirm': dict(zh='再点一次确认清除', en='Tap again to clear', fr='Touchez encore pour effacer', es='Toque otra vez para borrar', ko='한 번 더 누르면 지워집니다', ja='もう一度押すと消えます'),
 'helpClearNote': dict(zh='收藏、勾选、语言和到达日期都会删掉，页面会重新打开。', en='Favourites, ticks, language and arrival date are removed, and the page reopens.', fr='Favoris, coches, langue et date d’arrivée sont supprimés, puis la page se rouvre.', es='Se borran favoritos, marcas, idioma y fecha de llegada, y la página se vuelve a abrir.', ko='즐겨찾기, 체크, 언어, 도착일이 삭제되고 페이지가 다시 열립니다.', ja='お気に入り、チェック、言語、到着日が消え、ページが開き直されます。'),
 'crisisLead': dict(zh='你不必一个人扛。现在有危险就打 911。下面这些电话都能帮你，而且免费：', en='You don’t have to face this alone. In danger right now? Call 911. These lines are here for you, free:', fr='Vous n’avez pas à affronter cela seul·e. En danger maintenant ? Composez le 911. Ces lignes sont là pour vous, gratuitement :', es='No tiene que enfrentar esto solo/a. ¿En peligro ahora? Llame al 911. Estas líneas están para usted, gratis:', ko='혼자 감당하지 않아도 됩니다. 지금 위험하다면 911에 전화하세요. 아래 전화가 무료로 도와줍니다:', ja='ひとりで抱えなくて大丈夫です。いま危険なら911へ。次の窓口が無料で力になります：'),
 'crisisMore': dict(zh='你在这里输入的字不会发送到任何地方。', en='What you typed here is not sent anywhere.', fr='Ce que vous avez tapé ici n’est envoyé nulle part.', es='Lo que escribió aquí no se envía a ningún lugar.', ko='여기에 입력한 내용은 어디에도 전송되지 않습니다.', ja='ここに入力した言葉はどこにも送信されません。'),
}
def uiline(key, vals):
    parts = []
    for l in ('zh', 'en', 'fr', 'es', 'ko', 'ja'):
        v = vals[l].replace('\\', '\\\\').replace("'", "\\'")
        parts.append("UI.%s.%s='%s';" % (l, key, v))
    return ''.join(parts)
anchor = [ln for ln in s.split('\n') if ln.startswith("UI.zh.hot_info=")]
assert len(anchor) == 1
block = anchor[0] + '\n' + '\n'.join(uiline(k, v) for k, v in NEWUI.items())
s = rep(s, anchor[0] + '\n', block + '\n')

# ---------------------------------------------------------------- (h) Help button + sheet
s = rep(s, '    <button class="note-toggle" id="shareBtn">',
        '    <button class="note-toggle help-btn" id="helpBtn" type="button"><span class="hl-ic" aria-hidden="true"></span><span class="hl-tx"></span></button>\n    <button class="note-toggle" id="shareBtn">')
s = rep(s, '<div class="backdrop" id="shareBackdrop">',
        '<div class="backdrop" id="helpBackdrop">\n'
        '  <div class="guide-modal" id="helpModal">\n'
        '    <div class="sheet-grab" aria-hidden="true"><div class="panel-handle"></div></div>\n'
        '    <div class="guide-head">\n'
        '      <div class="panel-title" id="helpTitle"></div>\n'
        '      <button class="panel-close" id="helpClose">✕</button>\n'
        '    </div>\n'
        '    <div class="guide-body" id="helpBody"></div>\n'
        '  </div>\n'
        '</div>\n'
        '<div class="backdrop" id="shareBackdrop">')
for old in ("  #guideBackdrop.open,#noteBackdrop.open,#shareBackdrop.open{-webkit-backdrop-filter",
            "  #guideBackdrop,#noteBackdrop,#shareBackdrop{align-items:center!important",
            "  #guideBackdrop.open,#noteBackdrop.open,#shareBackdrop.open{pointer-events:auto;}",
            "    #guideBackdrop,#noteBackdrop,#shareBackdrop{align-items:flex-end!important",
            "    #guideBackdrop.open,#noteBackdrop.open,#shareBackdrop.open{animation:fadeIn"):
    new = old.replace('#shareBackdrop.open{', '#shareBackdrop.open,#helpBackdrop.open{').replace('#shareBackdrop{', '#shareBackdrop,#helpBackdrop{')
    assert new != old
    s = rep(s, old, new)
s = rep(s, "  .hotlines .hl-line b{color:#a11;}",
        "  .hotlines .hl-line b{color:#a11;}\n"
        "  .help-btn .hl-ic,.help-btn{color:#a11;}\n"
        "  .crisis-block{margin:0 0 8px;}\n"
        "  .crisis-lead{margin:0 0 4px;font-weight:700;color:#8a1c1c;line-height:1.5;}\n"
        "  .crisis-more,.help-note{margin:6px 0 0;font-size:11.5px;color:var(--sub-ink);line-height:1.6;}\n"
        "  .help-local,.help-info{margin:8px 0 0;font-size:13px;line-height:1.6;}\n"
        "  .help-local a,.help-info a{color:#a11;text-decoration:none;}\n"
        "  .help-lead{margin:0 0 6px;font-size:13.5px;line-height:1.6;font-weight:600;}\n"
        "  .help-actions{margin:16px 0 0;padding-top:12px;border-top:1px solid var(--line);display:flex;flex-direction:column;gap:6px;}\n"
        "  .help-exit,.help-clear{font:inherit;font-size:13.5px;font-weight:700;border-radius:10px;padding:10px 14px;min-height:44px;cursor:pointer;text-align:center;}\n"
        "  .help-exit{background:#8a1c1c;color:#fff;border:none;}\n"
        "  .help-clear{background:none;color:var(--ink);border:1px solid var(--line);margin-top:8px;}\n"
        "  .help-clear.armed{border-color:#a11;color:#a11;}")
# the phone header shows the word next to the icon, like the guide button does
s = rep(s, "    #guideToggle::after{content:attr(data-short);font-size:11px;font-weight:700;margin-left:3px;color:#fff;}",
        "    #guideToggle::after{content:attr(data-short);font-size:11px;font-weight:700;margin-left:3px;color:#fff;}\n"
        "    #helpBtn::after{content:attr(data-short);font-size:11px;font-weight:700;margin-left:3px;color:#a11;}")
s = rep(s, "  setHL('shareBtn',u.shareBtnLabel);\n",
        "  setHL('shareBtn',u.shareBtnLabel);\n  setHL('helpBtn',u.helpBtnLabel);\n  document.getElementById('helpBtn').dataset.short=u.helpBtnShort;\n"
        "  if(helpBackdropEl&&helpBackdropEl.classList.contains('open'))renderHelpSheet();\n")
HELPJS = r"""const helpBackdropEl=document.getElementById('helpBackdrop');
// 2026-09-21: one door that is always on screen, for the moment someone is not
// looking for a place but for a person to talk to.
let _clearArmed=false;
function renderHelpSheet(){
  const u=UI[L_],body=document.getElementById('helpBody');
  document.getElementById('helpTitle').innerHTML=iconify(u.helpTitle);
  _clearArmed=false;
  body.innerHTML='<p class="help-lead">'+esc(u.helpLead)+'</p>'+hotlineHtml(false)+localCrisisHtml()
    +'<p class="help-info"><a href="tel:'+esc(CITY.help.info)+'"><b>2-1-1</b></a> '+esc(u.helpInfo)+'</p>'
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
    try{Object.keys(localStorage).filter(k=>/^kamloops/.test(k)).forEach(k=>localStorage.removeItem(k));}catch(e){}
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
const noteBackdropEl=document.getElementById('noteBackdrop');"""
s = rep(s, "const noteBackdropEl=document.getElementById('noteBackdrop');", HELPJS)
s = rep(s, "  if(shareBackdropEl.classList.contains('open')){closeModal(shareBackdropEl);return;}",
        "  if(helpBackdropEl.classList.contains('open')){closeModal(helpBackdropEl);return;}\n  if(shareBackdropEl.classList.contains('open')){closeModal(shareBackdropEl);return;}")
s = rep(s, "[guideBackdropEl,noteBackdropEl,shareBackdropEl]", "[guideBackdropEl,noteBackdropEl,shareBackdropEl,helpBackdropEl]", 2)
s = rep(s, "  attachSheetDrag(shareBackdropEl,document.getElementById('shareModal'));",
        "  attachSheetDrag(shareBackdropEl,document.getElementById('shareModal'));\n  attachSheetDrag(helpBackdropEl,document.getElementById('helpModal'));")

open(E, 'w', encoding='utf-8').write(s)
open(D, 'w', encoding='utf-8').write(d)

# ---------------------------------------------------------------- (i) task wording
T = kamdata.load('TASKS')
by = {t['id']: t for t in T}
h = by['hardship']; st = by['settle']
h['why'] = {
 'en': 'Asking early costs nothing and keeps a hard month from becoming an eviction.',
 'fr': 'Demander tôt ne coûte rien et évite qu’un mois difficile devienne une expulsion.',
 'es': 'Pedir ayuda pronto no cuesta nada y evita que un mes difícil termine en desalojo.',
 'zh': '早开口不花一分钱，能把“难过的一个月”挡在“被赶出去”之前。',
 'ko': '일찍 요청하면 비용이 들지 않고, 힘든 한 달이 퇴거로 이어지는 것을 막습니다.',
 'ja': '早めに相談すれば費用はかからず、苦しい月が立ち退きに至るのを防げます。'}
assert h['steps'][1]['en'].startswith('Go to the food bank.')
h['steps'][1] = {
 'en': 'Go to the food bank. You do not need to be destitute. Bring ID for each person in your household and something that shows your address; if something is missing, call first and ask what they accept.',
 'fr': 'Allez à la banque alimentaire. Nul besoin d’être démuni. Apportez une pièce d’identité pour chaque membre du ménage et un document indiquant votre adresse ; s’il vous manque quelque chose, appelez d’abord pour savoir ce qui est accepté.',
 'es': 'Vaya al banco de alimentos. No hace falta estar en la miseria. Lleve identificación de cada persona del hogar y algo que muestre su dirección; si le falta algo, llame antes y pregunte qué aceptan.',
 'zh': '去食物银行。不需要“穷到极点”才能去。带上家里每个人的证件和一份能证明住址的东西；缺了什么，先打电话问他们接受什么。',
 'ko': '푸드뱅크에 가세요. 극빈 상태여야 하는 것은 아닙니다. 가구원 모두의 신분증과 주소를 보여 주는 서류를 가져가세요. 빠진 것이 있으면 먼저 전화해 무엇이 되는지 물어보세요.',
 'ja': 'フードバンクへ。困窮の極みである必要はありません。世帯全員の身分証と住所が分かる書類を持参してください。足りないものがあれば、先に電話して何が使えるか聞きましょう。'}
h['confid'] = {
 'en': 'These are community services, not immigration offices. If you were sponsored, or hold a work or study permit, and are thinking about government income assistance, ask a settlement worker or Legal Aid first — both are free.',
 'fr': 'Ce sont des services communautaires, pas des bureaux d’immigration. Si vous avez été parrainé·e, ou avez un permis de travail ou d’études, et envisagez l’aide sociale du gouvernement, consultez d’abord un intervenant en établissement ou l’aide juridique — tous deux gratuits.',
 'es': 'Son servicios comunitarios, no oficinas de inmigración. Si usted fue patrocinado/a, o tiene permiso de trabajo o de estudio, y piensa pedir asistencia social del gobierno, consulte antes a un trabajador de asentamiento o a Legal Aid; ambos son gratuitos.',
 'zh': '这些是社区服务，不是移民部门。如果你是被担保来的，或持工签 / 学签，又在考虑申请政府的社会救助（income assistance），先问定居服务专员或法律援助——都免费。',
 'ko': '이곳들은 지역사회 서비스이지 이민 기관이 아닙니다. 초청(스폰서)으로 왔거나 취업·학생 허가 소지자로서 정부 소득 지원을 생각한다면, 먼저 정착 지원 담당자나 법률 구조(Legal Aid)에 물어보세요. 둘 다 무료입니다.',
 'ja': 'これらは地域のサービスで、入国管理の窓口ではありません。スポンサー制度で来た方や、就労・学生許可をお持ちで政府の生活扶助を考えている方は、先に定住支援ワーカーか法律扶助（Legal Aid）に相談を。どちらも無料です。'}
st['confid'] = {
 'en': 'A settlement worker is not an immigration officer and does not decide anything about your case. Asking them a question is not an application.',
 'fr': 'Un intervenant en établissement n’est pas un agent d’immigration et ne décide rien sur votre dossier. Lui poser une question n’est pas une demande.',
 'es': 'Un trabajador de asentamiento no es un agente de inmigración y no decide nada sobre su caso. Hacerle una pregunta no es una solicitud.',
 'zh': '定居服务专员不是移民官，不决定你案子的任何事。向他们提问不等于提交申请。',
 'ko': '정착 지원 담당자는 이민 심사관이 아니며 사건에 대해 아무것도 결정하지 않습니다. 질문하는 것은 신청이 아닙니다.',
 'ja': '定住支援ワーカーは入国管理の職員ではなく、あなたの件について何も決めません。質問することは申請ではありません。'}
kamdata.save('TASKS', T)
print('phase 1 patch applied')
