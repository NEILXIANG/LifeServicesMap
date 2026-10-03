// ---------------------------------------------------------------------------
// CITY — every fact that changes when this map is rebuilt for another city.
// Anything city-specific belongs here, never inline in the code or the prose.
// Text elsewhere uses {CITY} {PROV} {TRANSIT} {SD} {DATE} placeholders, expanded
// by tpl() at render time, so a new city means editing this block and the data —
// not hunting through five languages of copy.
// ---------------------------------------------------------------------------
const DATA_VERSION='2026.10.03a';
// city → country basics → province specifics → country reference
const GUIDE_ORDER=['guideCity','guideCA1','guideProv','guideCA2'];

// TASKS (the Life Guide's task cards) live in the city data file since
// 2026-09-11: every card names this city's offices, phone numbers and rules,
// so they are city facts, not engine. See data-<city>.js.
const TASK_BUCKETS=['first','ongoing','problem'];

// Stated once, rendered everywhere. Change this line to change the terms.
const LICENCE={id:'CC BY-NC 4.0', url:'https://creativecommons.org/licenses/by-nc/4.0/'};
// Single source of truth for the verification date. It used to be written out by
// hand in five different note strings, which is how they drift apart.
const VERIFIED='2026-09-11';
// Bus routes are not hand-collected: they come from the operator's GTFS feed, and
// every stop name and coordinate in BR was re-checked against this edition of it.
// Routes 8, 11, 12 and 15 are absent from the feed — Kamloops does not run them.
const BUS_SOURCE={feed:'BC Transit GTFS', edition:'2026-08-29', stopsChecked:475};
function verifiedDate(l){
  const [y,m,d]=VERIFIED.split('-').map(Number);
  const mn=UI[l].months[m-1];
  if(l==='zh')return y+'年'+m+'月'+d+'日';
  if(l==='ko')return y+'년 '+m+'월 '+d+'일';
  if(l==='ja')return y+'年'+m+'月'+d+'日';
  if(l==='en')return mn+' '+d+', '+y;
  if(l==='fr')return d+' '+mn+' '+y;
  return d+' de '+mn+' de '+y;
}
// Expands the {CITY}/{PROV}/{TRANSIT}/{SD}/{DATE} placeholders used throughout the
// translated copy. One function so a new city can never half-replace a name.
// The feedback address used to live in data-kamloops.js as a plain string,
// which meant every visitor downloaded a page carrying an unbroken, scrapable
// email address in the raw HTML -- exactly what address-harvesting bots regex
// for. CITY.contact_r stores it character-reversed instead, so no email-shaped
// substring exists anywhere in the page source; this reassembles the real
// address at runtime, the only place it is ever whole.
function contactEmail(){return (CITY.contact_r||"").split("").reverse().join("");}
function tpl(str,l){
  if(!str)return str;
  return str
    .replace(/\{CITY\}/g,CITY.name[l])
    .replace(/\{PROV\}/g,CITY.prov[l])
    .replace(/\{TRANSIT_URL\}/g,CITY.transit.url)
    .replace(/\{TRANSIT\}/g,CITY.transit.name)
    .replace(/\{SD_URL\}/g,CITY.schoolDistrict.url)
    .replace(/\{SD\}/g,CITY.schoolDistrict.name)
    .replace(/\{CONTACT\}/g,contactEmail())
    .replace(/\{LIC_URL\}/g,LICENCE.url)
    .replace(/\{LIC\}/g,LICENCE.id)
    .replace(/\{VER\}/g,DATA_VERSION)
    .replace(/\{DATE\}/g,verifiedDate(l));
}
// Builds the guide's index from whatever headings the four guide tiers happen to
// render. Nothing here knows what the sections are, so a city that rewrites
// guideCity, or a province that rewrites guideProv, gets a correct index for free
// and in its own language. Buttons rather than anchors: an <a href="#gs-3"> inside
// a modal makes the browser write to location.hash, which on a back-press closes
// something the reader did not ask to close.

// ---------------------------------------------------------------------------
// The task layer's UI. The guide used to open on twenty-six headings of prose,
// which answers "what exists here" but not "I have this problem, what do I do".
// It now opens on the problems themselves, in the reader's own words; choosing
// one replaces the list with that task's steps, documents, office, cost and
// wait, and a back link returns to the list. The long-form prose is untouched
// and still sits below — this is a way in, not a replacement.
// ---------------------------------------------------------------------------

// Which tasks the reader has ticked off. Kept in this browser only — never in
// the URL, never in an event, never on a server. Bandura's point about
// self-efficacy is the whole reason this exists: a list of eleven official
// errands is daunting, and the single cheapest way to make it feel finishable
// is to let someone see that three of them are already behind them.
const _TASK_DONE_KEY=SP+'TasksDone';
let taskDone=new Set();
try{const raw=JSON.parse(localStorage.getItem(_TASK_DONE_KEY)||'[]');
    if(Array.isArray(raw))taskDone=new Set(raw.filter(x=>typeof x==='string'));}catch(e){}
function saveTaskDone(){try{localStorage.setItem(_TASK_DONE_KEY,JSON.stringify([...taskDone]));}catch(e){}try{updateGuideProgress();}catch(e){}}
// 2026-09-13 (item 4): steps are ticked one at a time; ticking the last one
// marks the card done, un-ticking any step un-marks it. Same device-only rule.
const _STEP_KEY=SP+'Steps';
let stepDone={};
try{const raw=JSON.parse(localStorage.getItem(_STEP_KEY)||'{}');if(raw&&typeof raw==='object'&&!Array.isArray(raw))stepDone=raw;}catch(e){}
// the landing strip counts ticked steps as "started" (updateGuideProgress), so
// it has to be refreshed here too, not only when a whole card is marked done —
// 2026-09-13 audit: a first tick left the strip hidden until the next reload
function saveStepDone(){try{localStorage.setItem(_STEP_KEY,JSON.stringify(stepDone));}catch(e){}try{updateGuideProgress();}catch(e){}}
function stepsOf(t){return Array.isArray(t.steps)?t.steps.length:0;}
function stepsDoneN(t){const a=stepDone[t.id];return Array.isArray(a)?a.filter(i=>i>=0&&i<stepsOf(t)).length:0;}
function setStep(id,i,on){
  const t=TASKS.find(x=>x.id===id);if(!t)return false;
  const cur=new Set(Array.isArray(stepDone[id])?stepDone[id]:[]);
  if(on)cur.add(i);else cur.delete(i);
  stepDone[id]=[...cur].sort((a,b)=>a-b);
  saveStepDone();
  trackEvent('task_step',{action:on?'tick':'untick',n:cur.size,of:stepsOf(t)});
  const all=stepsOf(t)>0&&cur.size>=stepsOf(t);
  let changed=false;
  if(all&&!taskDone.has(id)){toggleTaskDone(id,true);changed=true;}
  else if(!all&&taskDone.has(id)){toggleTaskDone(id,true);changed=true;}
  return changed;
}
function toggleTaskDone(id,fromStep){
  const now=!taskDone.has(id);
  if(now)taskDone.add(id);else taskDone.delete(id);
  // the card's steps follow the card button: done = every step ticked, undone =
  // none. A change that came from a step keeps the other steps as they are.
  if(!fromStep)try{const t=TASKS.find(x=>x.id===id);if(t){stepDone[id]=now?t.steps.map((_,i)=>i):[];saveStepDone();}}catch(e){}
  saveTaskDone();
  // Which card, never sent: the privacy summary promises ticks stay on the
  // device, and the funnel question ("do people finish?") only needs the count.
  trackEvent('task_done',{action:now?'done':'undone',total:taskDone.size});
  return now;
}
let _taskOpen=null;
let _taskQ='';
// Search inside the guide: the question, the title, the steps, and the same
// aliases the map search uses — so 驾照 / SIN / 押金 land on their card.
function taskMatches(t,q){
  q=(q||'').trim().toLowerCase();if(!q)return true;
  // the reader's language plus English: a zh reader types "SIN", "ICBC",
  // "licence" — the words on the forms — as often as 驾照
  const tx=v=>v?((v[L_]||'')+' '+(v.en||'')):'';
  const bag=[tx(t.q),tx(t.t),tx(t.why),...(t.steps||[]).map(tx),
    ...(t.bring?[tx(t.bring)]:[]),...(t.alias||[])].join(' ').toLowerCase();
  if(bag.indexOf(q)>=0)return true;
  const pl=t.place?P.find(p=>p.id===t.place):null;
  return !!(pl&&(pl.n.toLowerCase().indexOf(q)>=0||(pl.alias||[]).some(a=>a.toLowerCase().indexOf(q)>=0)));
}
function taskText(v){return v&&(v[L_]||v.en)||'';}
// For the map search hand-off: the card's own question, title and aliases —
// not its steps, or "library" would point at the card that mentions one.
// Question words carry no information about *which* card: "how do I get a
// health card" and "医保怎么办" should both land on the MSP card.
const _Q_STOP=/\b(how|do|does|i|me|my|get|a|an|the|to|where|what|can|is|in|for|find|need|apply|comment|je|un|une|le|la|les|où|cómo|dónde|puedo|el|los|las|de|para|mi|obtener|obtengo|consigo|saco|quiero|hago|ma|mon|mes|avoir|faire)\b/g;
const _Q_STOP_CJK=/(怎么办|怎么|去哪里|去哪|在哪里|在哪|哪里|如何|办理|申请|需要|我要|我想|어떻게|어디서|어디|하나요|해요|받나요|신청|どうすれば|どこで|どこ|どう|ですか|申請|方法|は|を|の)/g;
function _wordStartIn(hay,q){
  let i=hay.indexOf(q);
  // a query of three letters or fewer ("er", "ei") must be a whole word, not a prefix
  const whole=q.length<=3,W=/[0-9a-z\u00c0-\u024f]/;
  while(i>=0){
    if((i===0||!W.test(hay[i-1]))&&(!whole||i+q.length>=hay.length||!W.test(hay[i+q.length])))return true;
    i=hay.indexOf(q,i+1);}
  return false;
}
function taskMatchesLoose(t,q,strict){
  q=(q||'').trim().toLowerCase();if(!q)return false;
  const tx=v=>v?((v[L_]||'')+' '+(v.en||'')):'';
  const bag=[tx(t.q),tx(t.t),...(t.alias||[])].join(' ').toLowerCase();
  const cjkQ=/[\u3400-\u9fff\uac00-\ud7af\u3040-\u30ff]/.test(q);
  // Latin text: the query has to start at a word boundary ("rent" is not in "parents")
  if(cjkQ?bag.indexOf(q)>=0:_wordStartIn(bag,q))return true;
  if(strict&&!cjkQ)return false;
  const cjk=/[\u3400-\u9fff\uac00-\ud7af\u3040-\u30ff]/.test(q);
  if(cjk){
    let core=q.replace(_Q_STOP_CJK,'').replace(/[\s？?！!。，、]/g,'');
    core=core.replace(/(는|은|이|가|을|를|에서|에|로|도)$/,'');   // a trailing Korean particle
    if(core.length<2)return false;
    if(bag.indexOf(core)>=0)return true;
    if(strict)return false;
    // "孩子上学": the card's own alias sits inside the reader's phrase
    return (t.alias||[]).some(a=>a.length>=2&&core.indexOf(String(a).toLowerCase())>=0);
  }
  const words=q.replace(_Q_STOP,' ').replace(/[?¿!¡.,]/g,' ').split(/\s+/).filter(w=>w.length>=2);
  return words.length>0&&words.every(w=>_wordStartIn(bag,w));   // "er" is not in "worker"
}
function esc(t){return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
