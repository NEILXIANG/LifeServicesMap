// 2026-09-13 (item 15): one monochrome line-icon set for the chrome — SF Symbols
// in spirit: 24-grid, 1.8 stroke, round caps, currentColor. The emoji stay in
// the six-language strings as the source of truth (and as the fallback when a
// string reaches a place that renders plain text); ico()/iconify() swap a
// leading emoji for its drawing wherever HTML is rendered. Category pins keep
// their emoji: fifty-one coloured pictograms are a different job.
const ICONS={
  guide:'<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2.2 5.3-5.3 2.2 2.2-5.3z"/>',
  home:'<path d="M4 11l8-7 8 7"/><path d="M6 10v9h12v-9"/><path d="M10 19v-5h4v5"/>',
  suitcase:'<rect x="5" y="7.5" width="14" height="11" rx="2"/><path d="M10 7.5V5.6a1.6 1.6 0 011.6-1.6h.8A1.6 1.6 0 0114 5.6v1.9"/><path d="M8.5 18.5v1.6M15.5 18.5v1.6"/><path d="M8.5 21.4h.01M15.5 21.4h.01"/>',
  free:'<path d="M12 5v14"/><path d="M15.5 8.5a3 3 0 00-3-1.5h-1a2.5 2.5 0 000 5h1a2.5 2.5 0 010 5h-1a3 3 0 01-3-1.5"/><path d="M5 19.5L19 4.5"/>',
  child:'<circle cx="12" cy="7" r="3"/><path d="M6 20v-3a4 4 0 014-4h4a4 4 0 014 4v3"/>',
  snowflake:'<path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9"/><path d="M12 3l-2 2M12 3l2 2M12 21l-2-2M12 21l2-2M4.2 7.5l2.7.7M4.2 7.5l.7-2.7M19.8 16.5l-2.7-.7M19.8 16.5l-.7 2.7M4.2 16.5l2.7-.7M4.2 16.5l.7 2.7M19.8 7.5l-2.7.7M19.8 7.5l-.7-2.7"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
  walk:'<circle cx="13" cy="4.5" r="1.6"/><path d="M10 21l2-6 3 2v4"/><path d="M8 13l2-5 3 1 2.5 3.5H18"/><path d="M12 8l-1.5 6"/>',
  bulb:'<path d="M9 18h6"/><path d="M10 21h4"/><path d="M8.5 14.5A6 6 0 1115.5 14.5c-.7.6-1.5 1.8-1.5 3.5h-4c0-1.7-.8-2.9-1.5-3.5z"/>',
  pin:'<path d="M12 21s-6-5.5-6-11a6 6 0 0112 0c0 5.5-6 11-6 11z"/><circle cx="12" cy="10" r="2.2"/>',
  tag:'<path d="M3.5 12.5V4.5a1 1 0 011-1h8l8 8-8 8z"/><circle cx="8" cy="8" r="1.3"/>',
  bus:'<rect x="4" y="4" width="16" height="14" rx="3"/><path d="M4 12h16"/><path d="M7 21v-3M17 21v-3"/><path d="M8 15.5h.01M16 15.5h.01"/>',
  star:'<path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1.1 5.9-5.3-2.9-5.3 2.9 1.1-5.9-4.3-4.1 5.9-.8z"/>',
  share:'<path d="M12 4v12"/><path d="M8 8l4-4 4 4"/><path d="M5 13v6h14v-6"/>',
  chat:'<path d="M4 6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2h-7l-5 4v-4H6a2 2 0 01-2-2z"/>',
  info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/>',
  search:'<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.3-4.3"/>',
  phone:'<path d="M6 3h3l2 5-2.5 1.5a11 11 0 006 6L16 13l5 2v3a2 2 0 01-2 2A16 16 0 014 5a2 2 0 012-2z"/>',
  globe:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 010 18M12 3a14 14 0 000 18"/>',
  nav:'<path d="M12 3l8 18-8-4-8 4z"/>',
  alert:'<path d="M12 4l9 16H3z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
  basket:'<path d="M4 10h16l-1.5 9h-13z"/><path d="M8 10l3-6M16 10l-3-6"/><path d="M9 14v2M15 14v2"/>',
  sparkles:'<path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
  camera:'<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7l1.5-3h5L16 7"/><circle cx="12" cy="13.5" r="3.5"/>',
  history:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5h4"/><path d="M5 12a7 7 0 011.5-4.3"/>',
  palette:'<path d="M12 3a9 9 0 100 18h1.5a2 2 0 001.4-3.4 2 2 0 011.4-3.4H19a3 3 0 003-3 8.5 8.5 0 00-10-8.2z"/><circle cx="7.5" cy="12" r="1"/><circle cx="9.5" cy="7.5" r="1"/><circle cx="14.5" cy="6.5" r="1"/>',
  world:'<circle cx="12" cy="12" r="9"/><path d="M4 9.5c2 .5 3.5 2 3.5 4 0 1.5 1 2.5 2.5 2.5 1 0 1.5 1.5 1.5 3"/><path d="M20.5 10c-2-.5-3.5 1-4.5 2s-3 .5-3-1.5S15 7 17 7c1 0 2 .5 3.5 3z"/>',
  backpack:'<path d="M7 9a5 5 0 0110 0v11H7z"/><path d="M9 9V6a3 3 0 016 0v3"/><path d="M7 14h10"/><path d="M10 20v-4h4v4"/>',
  target:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>',
  idcard:'<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="11" r="2"/><path d="M5.5 16c.5-1.5 1.6-2.3 3-2.3s2.5.8 3 2.3"/><path d="M14 10h4M14 13.5h4"/>',
  health:'<path d="M12 20.5s-7.5-4.6-7.5-10A4.2 4.2 0 0112 8a4.2 4.2 0 017.5 2.5c0 5.4-7.5 10-7.5 10z"/><path d="M8.5 13h2l1-2 1.5 4 1-2h1.5"/>',
  car:'<path d="M5 13l1.5-5a2 2 0 011.9-1.4h7.2a2 2 0 011.9 1.4L19 13"/><rect x="3.5" y="13" width="17" height="5" rx="1.5"/><path d="M6 18v2M18 18v2"/><path d="M7 15.5h.01M17 15.5h.01"/>',
  bank:'<path d="M3 9l9-5 9 5"/><path d="M5 9v8M9.5 9v8M14.5 9v8M19 9v8"/><path d="M3 20h18"/><path d="M3 17h18"/>',
  school:'<path d="M4 5h6a2 2 0 012 2v13a2 2 0 00-2-2H4z"/><path d="M20 5h-6a2 2 0 00-2 2v13a2 2 0 012-2h6z"/>',
  receipt:'<path d="M6 3h12v18l-2-1.5-2 1.5-2-1.5-2 1.5-2-1.5L6 21z"/><path d="M9 8h6M9 12h6M9 16h3"/>',
  briefcase:'<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 012-2h2a2 2 0 012 2v2"/><path d="M3 12h18"/>',
  flame:'<path d="M12 3c1 3 5 5.5 5 10a5 5 0 01-10 0c0-2.2 1.2-3.8 2.5-5 .3 1.6 1.2 2.6 2.2 3C11.5 8.5 11 5.5 12 3z"/>',
  clipboard:'<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1"/><path d="M9 10h6M9 14h6M9 18h3"/>',
  people:'<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.3"/><path d="M3 20v-2a4 4 0 014-4h4a4 4 0 014 4v2"/><path d="M16 14.5a3.5 3.5 0 015 3.5v2"/>',
  elder:'<circle cx="11" cy="5.5" r="2.3"/><path d="M8 21v-6l-1-5a2 2 0 012-2h4a2 2 0 012 2v3"/><path d="M12 21v-5"/><path d="M17 12v9"/>',
  sick:'<path d="M6 4v6a6 6 0 0012 0V4"/><path d="M5 4h2M17 4h2"/><path d="M12 16v2a3 3 0 003 3h1a3 3 0 003-3v-1"/><circle cx="19" cy="14" r="1.8"/>',
  lock:'<rect x="5" y="10.5" width="14" height="9.5" rx="2"/><path d="M8.5 10.5V8a3.5 3.5 0 017 0v2.5"/>',
  key:'<circle cx="8" cy="14" r="4"/><path d="M11 11l9-9"/><path d="M16 6l2.5 2.5M19 3l2 2"/>',
  hands:'<path d="M12 21s-7-4-7-9V6l3-1v6"/><path d="M12 21s7-4 7-9V6l-3-1v6"/><path d="M8 11c0-2 2-3 4-1 2-2 4-1 4 1"/>',
  shield:'<path d="M12 3l8 3v6c0 4.5-3.5 7.5-8 9-4.5-1.5-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
  scale:'<path d="M12 3v18"/><path d="M5 7h14"/><path d="M8 21h8"/><path d="M3 14l3-7 3 7a3 3 0 01-6 0z"/><path d="M15 14l3-7 3 7a3 3 0 01-6 0z"/>',
  more:'<circle cx="12" cy="12" r="9"/><path d="M8 12h.01M12 12h.01M16 12h.01"/>',
  reset:'<path d="M4 12a8 8 0 1 0 2.3-5.7"/><path d="M4 4v5h5"/>',
  doc:'<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/><path d="M9.5 13h5M9.5 16.5h5"/>',
  calendar:'<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16"/><path d="M8 3v4M16 3v4"/>',
  print:'<path d="M7 9V4h10v5"/><rect x="4" y="9" width="16" height="8" rx="2"/><path d="M7 14h10v6H7z"/>',
  check:'<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  gradcap:'<path d="M3 9l9-4 9 4-9 4z"/><path d="M7 11v4c0 1.5 2.2 3 5 3s5-1.5 5-3v-4"/><path d="M21 9v5"/>',
  dumbbell:'<path d="M7 8v8M17 8v8"/><path d="M4 10v4M20 10v4"/><path d="M7 12h10"/>',
  tree:'<path d="M12 3l5 6h-3l4 5h-4l3 4H7l3-4H6l4-5H7z"/><path d="M12 18v3"/>',
  bag:'<path d="M5 8h14l-1 12H6z"/><path d="M9 8V6a3 3 0 016 0v2"/>',
  family:'<circle cx="8" cy="7" r="2.5"/><circle cx="16" cy="7" r="2.5"/><circle cx="12" cy="13" r="2"/><path d="M3 19v-1a3.5 3.5 0 013.5-3.5h1M21 19v-1a3.5 3.5 0 00-3.5-3.5h-1"/><path d="M9 21v-1a3 3 0 016 0v1"/>',
  pill:'<rect x="2.5" y="8.5" width="19" height="7" rx="3.5" transform="rotate(-45 12 12)"/><path d="M9.5 9.5l5 5"/>',
  layers:'<path d="M12 4l8 4.5-8 4.5-8-4.5z"/><path d="M4 13l8 4.5 8-4.5"/><path d="M4 16.5L12 21l8-4.5"/>',
  wifi_off:'<path d="M3 3l18 18"/><path d="M5 10a12 12 0 016-3.5M9 13.5a7 7 0 013-1.5M16.5 12.8A7 7 0 0119 13.5M13 7a12 12 0 016 3"/><path d="M12 18h.01"/>'
};
// which drawing stands in for which emoji when a string is rendered as HTML
const EMOJI_ICON={'🧭':'guide','🏠':'home','🧳':'suitcase','🆓':'free','🧒':'child','❄️':'snowflake','🕒':'clock','🚶':'walk','💡':'bulb','📍':'pin','🏷️':'tag','🚌':'bus','⭐':'star','🔗':'share','💬':'chat','ℹ️':'info','🔍':'search','📞':'phone','☎️':'phone','🌐':'globe','🚨':'alert','🧺':'basket','🎉':'sparkles','📷':'camera','🕰️':'history','🎨':'palette','🌏':'world','🎒':'backpack','🎯':'target','🪪':'idcard','⚕️':'health','🚗':'car','🏦':'bank','🏫':'school','🧾':'receipt','🤝':'people','🧓':'elder','🩺':'sick','🔑':'key','📜':'doc','🔒':'lock','🤲':'hands','🛡️':'shield','⚖️':'scale','📄':'doc','📅':'calendar','🖨️':'print','↺':'reset','📴':'wifi_off','💊':'pill','🗂️':'layers','🎓':'gradcap','💪':'dumbbell','🌳':'tree','🛍️':'bag','👨‍👩‍👧':'family','💼':'briefcase','🔥':'flame','📋':'clipboard'};
function ico(name,cls){
  const d=ICONS[name];if(!d)return '';
  return '<svg class="ic'+(cls?' '+cls:'')+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'+d+'</svg>';
}
// "🧭 How do I…?" → <svg …/> How do I…?   (text is escaped; the emoji is the key)
// (no \p{…} regex: the syntax floor is ES2017 and a parse error there is a blank page)
const _EMOJI_KEYS=Object.keys(EMOJI_ICON).sort((a,b)=>b.length-a.length);
function iconify(str,cls){
  if(typeof str!=='string')return '';
  for(let i=0;i<_EMOJI_KEYS.length;i++){const k=_EMOJI_KEYS[i];
    if(str.indexOf(k)===0)return ico(EMOJI_ICON[k],cls)+esc(str.slice(k.length).replace(/^\s+/,''));}
  return esc(str);
}
function emojiIcon(em,cls){return (em&&EMOJI_ICON[em])?ico(EMOJI_ICON[em],cls):esc(em||'');}
function localISODate(d){
  d=d||new Date();
  return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
}
function renderTaskList(){
  const host=document.getElementById('guideTasks');
  if(!host)return;
  const u=UI[L_];
  _taskOpen=null;
  try{writeURLState();}catch(e){}
  let h='<p class="task-lead">'+esc(u.taskLead)+'</p>';
  h+='<input type="search" class="task-search" id="taskSearch" placeholder="'+esc(u.taskSearchPh)+'" value="'+esc(_taskQ)+'" autocomplete="off">';
  const arr=arrivalDate();
  h+='<div class="task-arrive"><label for="arriveDate">'+esc(u.arriveLabel)+'</label>'
    +'<input type="date" id="arriveDate" value="'+esc(arr||'')+'" max="'+localISODate()+'">'
    +(arr?'<button type="button" class="task-tool" id="arriveClear">'+esc(u.arriveClear)+'</button>':'')
    +'<span class="task-arrive-h">'+esc(u.arriveHint)+'</span></div>';
  h+='<div id="taskBuckets"></div>';
  host.innerHTML=h;
  renderTaskBuckets();
  // 2026-09-10: the whole block, search box included, used to be rebuilt on
  // every keystroke. Replacing the focused <input> mid-composition aborts an
  // IME session, so 驾照 / 免許 / 운전면허 lost every syllable after the first.
  // The box now stays put and only the list below it re-renders — and not
  // while a composition is in progress.
  const ts=host.querySelector('#taskSearch');
  if(ts){
    ts.addEventListener('compositionend',()=>{_taskQ=ts.value;renderTaskBuckets();});
    ts.oninput=e=>{if(e&&e.isComposing)return;_taskQ=ts.value;renderTaskBuckets();};
    // 2026-09-13: Chromium's native Escape on <input type=search> empties the
    // box with a 'search' event and no 'input' event, so the list stayed
    // filtered by a query nobody could see. Escape with text = clear the box
    // and stop there; the second Escape closes the guide, as before.
    ts.addEventListener('search',()=>{if(ts.value!==_taskQ){_taskQ=ts.value;renderTaskBuckets();}});
    ts.addEventListener('keydown',e=>{if(e.key==='Escape'&&ts.value){e.preventDefault();e.stopPropagation();ts.value='';_taskQ='';renderTaskBuckets();}});
  }
  const ad=host.querySelector('#arriveDate');
  if(ad){
    ad.onchange=()=>{const v=ad.value;if(!setArrival(v))return;trackEvent('arrival_set',{set:!!v});renderTaskList();};
    // a value the field ends up with that was never accepted (a future date,
    // a half-typed year) is shown as what is actually stored once the reader
    // leaves the field — touching the value mid-edit would fight the browser
    ad.onblur=()=>{const cur=arrivalDate()||'';if(ad.value!==cur)ad.value=cur;};
  }
  const ac=host.querySelector('#arriveClear');
  if(ac)ac.onclick=()=>{setArrival(null);renderTaskList();};
}
function renderTaskBuckets(){
  const host=document.getElementById('taskBuckets');
  if(!host)return;
  const u=UI[L_];
  let h='';
  // Progress before the list: seeing "3 of 11 done" reframes the same eleven
  // errands from a wall into a sequence someone is already partway through.
  const doneN=TASKS.filter(t=>taskDone.has(t.id)).length;
  const stepsAll=TASKS.reduce((a,t)=>a+stepsOf(t),0),stepsN=TASKS.reduce((a,t)=>a+stepsDoneN(t),0);
  if(doneN>0||stepsN>0){
    h+='<div class="task-progress"><div class="task-bar"><span style="width:'
      +Math.round(stepsN/Math.max(stepsAll,1)*100)+'%"></span></div><span class="task-pc">'
      +esc(u.taskProgress(doneN,TASKS.length))+' · '+esc(u.stepProgress(stepsN,stepsAll))+'</span></div>';
  }
  // 2026-10-04 (newcomer test): "abuse" or "shelter" typed here used to end in "call 2-1-1" — a weekday
  // daytime line. A crisis word gets the 24-hour lines first, whatever the cards match.
  if(_taskQ&&isCrisisQuery(_taskQ))h+=crisisHtml();
  let any=0;
  TASK_BUCKETS.forEach(b=>{
    let items=TASKS.filter(t=>t.when===b&&taskMatches(t,_taskQ));
    if(!items.length)return;
    any+=items.length;
    // timeline order: week 1 → 90 days → tax season → any time; a real
    // deadline (arrival date set) breaks ties inside a rank
    // a real date (arrival date set) outranks everything: it is the one fact
    // that stops being useful the day after; undated cards then follow the rank
    const rank={week1:0,month3:1,season:2,any:3,need:4};
    const key=t=>{const d=deadlineDate(t);return d?Math.max(daysLeft(d),0):1e6+(rank[t.due]||0)*1e3;};
    items=items.slice().sort((x,y)=>key(x)-key(y));
    h+='<div class="task-bucket">'+esc(b==='first'?u.taskFirst:b==='ongoing'?u.taskOngoing:u.taskProblem)+'</div>';
    // A person in crisis should not have to open a card to find a phone number.
    if(b==='problem')h+=hotlineHtml(true);
    h+='<div class="task-grid">';
    items.forEach(t=>{
      const done=taskDone.has(t.id);
      // A deadline is the one fact on a card that stops being useful the day
      // after it passes, so it is the one fact promoted to the list.
      let dl='';
      if(t.deadline){
        const dd=deadlineDate(t);
        if(dd){const n=daysLeft(dd);
          dl='<span class="task-dl'+(n<0?' past':n<=14?' soon':'')+'">'+esc(n<0?u.dlPast:u.dlBy(fmtDate(dd,L_),n))+'</span>';}
        else dl='<span class="task-dl">'+esc(taskText(t.deadline))+'</span>';
      }
      const dueL=t.due&&u['due'+t.due.charAt(0).toUpperCase()+t.due.slice(1)];
      const sn=stepsDoneN(t),st=stepsOf(t);
      const stepChip=(!done&&sn>0&&st>0)?'<span class="task-stepc">'+esc(u.stepProgress(sn,st))+'</span>':'';
      h+='<button type="button" class="task-card'+(done?' is-done':'')+'" data-task="'+esc(t.id)+'">'
        +'<span class="task-top"><span class="task-ic" aria-hidden="true">'+emojiIcon(t.icon)+'</span>'
        +(dueL&&!dl&&!done?'<span class="task-due">'+esc(dueL)+'</span>':'')
        +dl+stepChip+(done?'<span class="task-done-b">✓ '+esc(u.taskDoneBadge)+'</span>':'')+'</span>'
        +'<span class="task-q">'+esc(taskText(t.q))+'</span>'
        +'<span class="task-t">'+esc(taskText(t.t))+'</span></button>';
    });
    h+='</div>';
  });
  if(!any&&_taskQ&&!isCrisisQuery(_taskQ))h+='<p class="task-none">'+esc(u.taskSearchNone)+'</p>';
  if(doneN===TASKS.length){
    // The last tick used to be the end of the road. It is the start of the
    // part the app cannot do for you.
    h+='<div class="task-alldone">'+esc(u.taskAllDone)+' <button type="button" class="task-tool" data-open="connect">'+esc(u.taskAllDoneGo)+'</button></div>';
  }
  h+='<p class="task-more">'+esc(u.taskReadMore)+'</p>';
  host.innerHTML=h;
  const go=host.querySelector('[data-open=connect]');
  if(go)go.onclick=()=>openTask('connect','alldone');
  host.querySelectorAll('.task-card').forEach(b=>{
    b.onclick=()=>openTask(b.dataset.task,'list');
  });
}

// A translation error in a medical or legal card is not a typo, it is a wrong
// turn taken by someone who trusted us. This is the cheapest way for the only
// people who can spot it — native readers — to report it.
function transFixHref(t){
  const u=UI[L_];
  const subj=u.fbSubject+': '+taskText(t.t)+' ['+L_+']';
  const body=[u.fbLang+': '+L_,u.fbVersion+': '+DATA_VERSION,'task: '+t.id,
              '','---',u.taskTransFix,''].join('\n');
  return 'mailto:'+contactEmail()+'?subject='+encodeURIComponent(subj)+'&body='+encodeURIComponent(body);
}
function openTask(id,src){
  const t=TASKS.find(x=>x.id===id);
  const host=document.getElementById('guideTasks');
  if(!t||!host)return;
  // one event per card opened, whichever door it came through (a language
  // switch re-renders the open card; that is not an open)
  if(src!=='lang')trackEvent('task_open',{id:id,src:src||'other'});
  // A card is one level deeper than the list: Back returns to the list,
  // not out of the guide (a navigation stack, the way a phone user expects).
  // 2026-09-13: only ever on top of the guide's own entry — a guide opened
  // from a link has none, and a card entry with nothing under it made ✕ step
  // the browser off the page (popSheetState assumes two entries)
  let underGuide=false;try{underGuide=!!(history.state&&history.state[_SHEET_KEY]==='guideBackdrop');}catch(e){}
  if(guideBackdropEl.classList.contains('open')&&!_taskOpen&&underGuide)pushSheetState('guideTask');
  _taskOpen=id;
  try{writeURLState();}catch(e){}
  const u=UI[L_];
  const row=(label,body,cls)=>body?'<div class="task-row'+(cls?' '+cls:'')+'"><div class="task-lb">'
      +esc(label)+'</div><div class="task-bd">'+body+'</div></div>':'';
  let h='<button type="button" class="task-back" id="taskBack">'+esc(u.taskBack)+'</button>'
       +'<div class="task-head"><span class="task-ic-lg" aria-hidden="true">'+emojiIcon(t.icon)+'</span>'
       +'<div><h4>'+esc(taskText(t.t))+'</h4><p>'+esc(taskText(t.why))+'</p></div></div>';
  const sd=new Set(Array.isArray(stepDone[t.id])?stepDone[t.id]:[]);
  h+=row(u.taskSteps,'<ol class="task-steps">'
      +t.steps.map((x,i)=>'<li class="task-step'+(sd.has(i)?' on':'')+'"><label><input type="checkbox" data-step="'+i+'"'+(sd.has(i)?' checked':'')+'><span>'+phoneHtml(esc(taskText(x)))+'</span></label></li>').join('')+'</ol>');
  h+=row(u.taskBring,t.bring?esc(taskText(t.bring)):'');
  // "Where do I go" is the question the rest of this app can already answer, so
  // it hands off to the map rather than repeating an address that could drift.
  const pl=t.place?P.find(p=>p.id===t.place):null;
  if(pl){
    let w='<div class="task-place"><b>'+esc(pl.n)+'</b><br>'+esc(pl.a||'');
    if(pl.p)w+='<br><a href="tel:'+esc(String(pl.p).replace(/[^\d]/g,''))+'">'+esc(pl.p)+'</a>';
    const hrs=pl.h?fmtHours(pl.h,L_):'';
    if(hrs)w+='<br><span class="task-hrs">'+esc(hrs)+'</span>';
    w+='<br><button type="button" class="task-map" data-pid="'+esc(pl.id)+'">'+esc(u.taskOpenMap)+'</button></div>';
    h+=row(u.taskWhere,w);
  }
  // A sentence to read aloud. "Walk in and ask" assumes a directness and a
  // phone-English confidence that are cultural, not universal; handing someone
  // the exact words removes a real barrier at the counter.
  if(t.say)h+=row(u.taskSay,'<div class="task-say">“'+esc(t.say)+'”</div>'
      +(t.sayGloss&&L_!=='en'?'<div class="task-say-g">'+esc(taskText(t.sayGloss))+'</div>':'')
      +'<div class="task-say-h">'+esc(u.taskSayHint)+'</div>');
  h+=row(u.taskCost,t.cost?esc(taskText(t.cost)):'');
  h+=row(u.taskWait,t.wait?esc(taskText(t.wait)):'');
  // The computed date lived only on the list card; inside the card the reader
  // saw "90 days from arrival" and no way to learn what unlocks the calendar.
  if(t.deadline){
    const dd=deadlineDate(t);
    if(dd){const n=daysLeft(dd);
      h+=row(u.taskDeadline,'<b>'+esc(n<0?u.dlPast:u.dlBy(fmtDate(dd,L_),n))+'</b>');}
    // rights can never resolve to a computed date (see deadlineDate) — offering
    // "enter your arrival date" there would promise an exact date that never comes.
    else h+=row(u.taskDeadline,esc(taskText(t.deadline))+(t.id==='rights'?'':' <button type="button" class="task-tool task-dl-set" id="taskDlSet">'+esc(u.dlSetArrival)+'</button>'));
  }
  // For a reader from a country where dealing with officials carries risk,
  // "go to a government office" is not neutral advice. Saying plainly who does
  // and does not see the information removes a barrier nothing else addresses.
  h+=row(u.taskConfid,t.confid?esc(taskText(t.confid)):'');
  // The reminder that belongs to this card and no other: not legal advice on a
  // legal card, 911 on a health card, CRA is the authority on the tax card.
  // Put where the risk is, so the front page does not have to frighten everyone.
  const cav={legal:'cavLegal',rights:'cavLegal',deposit:'cavLegal',sick:'cavHealth',msp:'cavHealth',eldercare:'cavHealth',tax:'cavTax'}[t.id];
  // 2026-10-19 (walkthrough): "ask the legal clinic named above" on cards that name no clinic (rights, deposit)
  const cavKey=cav==='cavLegal'&&!pl?'cavLegalNoPlace':cav;
  if(cavKey&&u[cavKey])h+='<div class="task-caveat">'+esc(u[cavKey])+'</div>';
  // 2026-09-15 institution-outreach review: note can hold a phone-number-bearing
  // block (see hardship's shelter list) the same way help already does — route
  // both through the same linkifier rather than inventing a second one.
  h+=row(u.taskNote,t.note?phoneHtml(esc(taskText(t.note))):'');
  h+=row(u.taskHelp,t.help?phoneHtml(esc(taskText(t.help))):'');
  h+=row(u.taskAlso,t.also?esc(taskText(t.also)):'');
  // Finish the card with the two things that close a loop: the reader's own
  // "I have done this", and the only signal that can tell the maintainer a card
  // is wrong — that somebody followed it and it did not work.
  const isDone=taskDone.has(t.id);
  // The three things a person does with a card besides read it: send it to
  // someone, take it to the counter on paper, and put its deadline somewhere it
  // will resurface. All three are local; none records anything about the reader.
  h+='<div class="task-tools">'
    +'<button type="button" class="task-tool" id="taskShare">'+esc(u.taskShare)+'</button>'
    +'<button type="button" class="task-tool" id="taskPrint">'+esc(u.taskPrint)+'</button>'
    +(t.deadline&&deadlineDate(t)?'<button type="button" class="task-tool" id="taskCal">'+esc(u.taskCal)+'</button>':'')
    +'</div>';
  h+='<div class="task-close">'
    +'<button type="button" class="task-tick'+(isDone?' on':'')+'" id="taskTick">'
    +(isDone?'✓ '+esc(u.taskUndone):esc(u.taskMarkDone))+'</button>'
    +'<div class="task-fb" id="taskFb"><span>'+esc(u.taskFeedbackQ)+'</span>'
    +'<button type="button" class="task-fb-b" data-r="worked">'+esc(u.taskWorked)+'</button>'
    +'<button type="button" class="task-fb-b" data-r="stuck">'+esc(u.taskStuck)+'</button></div>'
    +'<p class="task-local">'+esc(u.taskLocalOnly)+'</p></div>';
  if(t.src)h+='<p class="task-src"><a href="'+esc(t.src)+'" target="_blank" rel="noopener">'
      +esc(u.taskSource)+': '+esc(t.srcName)+' ↗</a></p>';
  h+='<p class="task-src task-checked">'+esc(u.taskVerified.replace('{TD}',CITY.tasksChecked||VERIFIED))
    +' · <a href="'+esc(transFixHref(t))+'">'+esc(u.taskTransFix)+'</a></p>';
  host.innerHTML=h;
  host.scrollIntoView({block:'start'});
  document.getElementById('taskBack').onclick=()=>{
    trackEvent('task_back',{id:id});renderTaskList();
    // 2026-09-13 audit: a guide opened from a link has no entry of its own, so
    // once the reader steps "← back to list" they have navigated *inside* the
    // page — from here the list is a level above the map, and the next card
    // needs an entry to sit on (openTask only pushes one over a guide entry;
    // without it Back from that card left the site). Give the guide its entry
    // now; on the normal stack the card entry is popped as before.
    let under=false;try{under=!!(history.state&&history.state[_SHEET_KEY]);}catch(e){}
    if(!under&&guideBackdropEl.classList.contains('open'))pushSheetState('guideBackdrop');
    else popSheetState('guideTask');
  };
  const tick=document.getElementById('taskTick');
  const syncTick=()=>{const on=taskDone.has(id);if(!tick)return;tick.classList.toggle('on',on);tick.textContent=on?('✓ '+u.taskUndone):u.taskMarkDone;};
  if(tick)tick.onclick=()=>{
    toggleTaskDone(id);syncTick();
    host.querySelectorAll('.task-step input').forEach(cb=>{cb.checked=taskDone.has(id);cb.closest('.task-step').classList.toggle('on',cb.checked);});
  };
  host.querySelectorAll('.task-step input').forEach(cb=>{
    cb.onchange=()=>{
      cb.closest('.task-step').classList.toggle('on',cb.checked);
      const changed=setStep(id,parseInt(cb.dataset.step,10),cb.checked);
      syncTick();
      if(changed&&taskDone.has(id))showToast(u.stepsAllDone,{ms:3000});
    };
  });
  const fb=document.getElementById('taskFb');
  if(fb)fb.querySelectorAll('.task-fb-b').forEach(b=>{
    b.onclick=()=>{
      trackEvent('task_outcome',{id:id,result:b.dataset.r});
      // "Stuck" used to end with a thank-you and nothing else — a signal for the
      // maintainer, no exit for the person. Now it hands over the two doors that
      // exist for exactly this: a settlement worker, and 2-1-1 in your language.
      fb.innerHTML='<span class="task-thanks">'+esc(u.taskThanks)+'</span>'
        +(b.dataset.r==='stuck'?'<div class="task-stuck-exit">'+esc(u.taskStuckExit)
          +' <a href="tel:'+esc(CITY.help.settle.replace(/[^\d]/g,''))+'">'+esc(CITY.help.settle)+'</a> · <a href="tel:'+esc(CITY.help.info)+'">2-1-1</a></div>':'');
    };
  });
  const sh=host.querySelector('#taskShare');
  if(sh)sh.onclick=()=>shareTask(t);
  const pr=host.querySelector('#taskPrint');
  if(pr)pr.onclick=()=>{trackEvent('task_print',{id:id});document.body.classList.add('print-task');window.print();
    // afterprint is the real end of printing (a preview can stay open far longer
    // than 1.5 s); the timer remains as the fallback for engines without it
    setTimeout(()=>document.body.classList.remove('print-task'),1500);};
  const cal=host.querySelector('#taskCal');
  if(cal)cal.onclick=()=>{trackEvent('task_calendar',{id:id});if(downloadIcs(t)===false)return;
    const dd=deadlineDate(t);if(dd)showToast(u.calAdded.replace('{D}',fmtDate(dd,L_)));};
  const dls=host.querySelector('#taskDlSet');
  if(dls)dls.onclick=()=>{renderTaskList();popSheetState('guideTask');const ad=document.getElementById('arriveDate');if(ad){ad.focus();try{ad.showPicker&&ad.showPicker();}catch(e){}}};
  const mb=host.querySelector('.task-map');
  if(mb)mb.onclick=()=>{
    const m=M.find(x=>x.data.id===mb.dataset.pid);
    trackEvent('task_to_map',{id:id,place:mb.dataset.pid});
    closeModal(guideBackdropEl);
    leaveTaskForMap(id);   // Back returns to this card (85-search-box-sheets.js)
    if(m)focusMarker(m,16);   // focusMarker moves the map; see the note there
  };
}
function buildGuideToc(){
  const body=document.getElementById('guideBody');
  if(!body)return;
  const hs=[...body.querySelectorAll('h3')];
  if(hs.length<4)return;              // short guide: an index would be noise
  const nav=document.createElement('nav');
  nav.className='guide-toc';
  nav.setAttribute('aria-label',UI[L_].guideTocLabel);
  const h=document.createElement('div');
  h.className='guide-toc-h';h.textContent=UI[L_].guideTocLabel;
  nav.appendChild(h);
  const list=document.createElement('div');list.className='guide-toc-list';
  hs.forEach((el,i)=>{
    el.id='gs-'+i;
    const b=document.createElement('button');
    b.className='guide-toc-btn';b.type='button';
    b.textContent=el.textContent;
    b.onclick=()=>{
      el.scrollIntoView({block:'start',behavior:'smooth'});
      // A colour flash is the only thing that says "this is the line you asked
      // for" once smooth-scrolling has stopped; :target can't be used without
      // touching the URL, so the class does the same job locally.
      hs.forEach(x=>x.classList.remove('gs-flash'));
      el.classList.add('gs-flash');
      trackEvent('guide_section_jump',{id:'gs-'+i});
    };
    list.appendChild(b);
  });
  nav.appendChild(list);
  body.insertBefore(nav,body.firstChild);
}
