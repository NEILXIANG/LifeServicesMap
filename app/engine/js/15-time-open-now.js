// Reading order for the chips and for the badges inside a popup.
const TORDER=["life","family","fun","scenic","history","culture","free","multi","student","indoor"];
// ---- "Open now" (2026-09-10) --------------------------------------------------
// Declared up here, ahead of the marker pass: every popup is rendered once at
// load (bindPopup), and a const declared further down is still in its temporal
// dead zone at that moment — the first build of this threw on load.
// Every place already carries structured hours, and the popup already renders
// them — but nothing ever answered the one question both a resident and a
// newcomer ask most: is it open right now? The clock is the city's, not the
// reader's device: someone planning from abroad, or a phone still on its old
// time zone, should see the same answer as someone standing outside the door.
const CITY_TZ=PROVINCE.timezone;   // provinces/<province>/province.json (2026-10-05; was written here)
// 2026-10-04: B.C. moved to permanent daylight time — on 2026-11-01 the clocks do not fall back (Province of
// B.C., news.gov.bc.ca 2026CITZ0009). A phone whose time-zone data predates that still turns America/Vancouver
// back to UTC-8 and would put every "open now" an hour wrong. From the moment the old rule would have fallen
// back (2026-11-01 09:00 UTC), when the device still reports UTC-8 the city clock is computed as UTC-7 instead.
// Devices with current data already report UTC-7 and are left alone.
const _BC_PERMANENT_DST_AT=Date.UTC(2026,10,1,9);
function _cityClockDate(){
  const now=new Date();
  if(CITY_TZ!=='America/Vancouver'||now.getTime()<_BC_PERMANENT_DST_AT)return {date:now,zone:CITY_TZ};
  try{
    const p=new Intl.DateTimeFormat('en-CA',{timeZone:CITY_TZ,hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(now);
    const h=parseInt((p.find(x=>x.type==='hour')||{}).value,10)%24,mi=parseInt((p.find(x=>x.type==='minute')||{}).value,10);
    const off=((h*60+mi)-(now.getUTCHours()*60+now.getUTCMinutes())+1440*2)%1440;   // the device's offset, in minutes mod a day
    if(off===16*60)return {date:new Date(now.getTime()-7*3600000),zone:'UTC'};      // still UTC-8 → read the clock as UTC-7
  }catch(e){}
  return {date:now,zone:CITY_TZ};
}
function cityNow(){
  // weekday 1..7 (Mon..Sun) and minutes since midnight, in the city's zone
  const c=_cityClockDate();
  const parts=new Intl.DateTimeFormat('en-CA',{timeZone:c.zone,weekday:'short',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(c.date);
  const g=k=>(parts.find(x=>x.type===k)||{}).value;
  const wd={Mon:1,Tue:2,Wed:3,Thu:4,Fri:5,Sat:6,Sun:7}[g('weekday')]||1;
  return {d:wd,m:(parseInt(g('hour'),10)%24)*60+parseInt(g('minute'),10)};
}
// Returns {open:true|false, until:minute|null} or null when the hours cannot
// say (no hours, a text-only entry, a schedule keyed to prayer times, a day
// listed with no times). "Unknown" is never reported as "closed": a wrong
// "closed" sends someone home from an open door.
// Month in the city's zone, for seasonal hours.
function cityMonth(){
  try{const c=_cityClockDate();return parseInt(new Intl.DateTimeFormat('en-CA',{timeZone:c.zone,month:'numeric'}).format(c.date),10);}catch(e){return new Date().getMonth()+1;}
}
// 2026-09-21: the city's own date, cached for a minute — openState runs for
// every place on every filter tap.
let _isoAt=0,_iso='';
function cityISODate(){
  const t=Date.now();
  if(t-_isoAt>60000){_isoAt=t;try{const c=_cityClockDate();_iso=new Intl.DateTimeFormat('en-CA',{timeZone:c.zone,year:'numeric',month:'2-digit',day:'2-digit'}).format(c.date);}catch(e){_iso='';}}
  return _iso;
}
function isHolidayToday(){return !!(CITY.holidays&&CITY.holidays.indexOf(cityISODate())>=0);}
function openState(h,now){
  if(!h||typeof h!=='object')return null;
  if(h.a)return {open:true,until:null};
  // A statutory holiday: the weekday hours on file are not today's hours.
  // "Unknown" is the honest answer (a clock passed in by a caller is a
  // question about an ordinary day, not today).
  if(!now&&isHolidayToday())return null;
  if(h.k)return null;
  // 2026-09-10: `q` marks hours that belong to an office, box office or parish
  // office rather than the place itself, and `se` marks a season. A spray park
  // "open now" in January, or a church "open" because its office is, is the
  // wrong kind of certain — outside the season, or with a qualifier, the
  // answer is "unknown", which the pill and the filter both leave alone.
  if(h.q)return null;
  if(h.se){
    const mo=(now&&now.mo)||cityMonth();
    const inSeason=h.se==='summer'?(mo>=5&&mo<=9):h.se==='winter'?(mo>=11||mo<=3):true;
    if(!inSeason)return null;
  }
  const r=h.r||[];
  if(!r.length)return null;
  now=now||cityNow();
  let known=false, best=null;
  for(const [d1,d2,o,c] of r){
    if(o===null||o===undefined)continue;           // day listed, times not
    known=true;
    const today=now.d>=d1&&now.d<=d2;
    // yesterday's range can still be running past midnight
    const yd=now.d===1?7:now.d-1, yesterday=yd>=d1&&yd<=d2;
    if(c===null||c===undefined){ if(today&&now.m>=o)return {open:true,until:null}; continue; }
    if(c>o){ if(today&&now.m>=o&&now.m<c)return {open:true,until:c}; }
    else{   // overnight, e.g. 20:00-02:00
      if(today&&now.m>=o)return {open:true,until:c};
      if(yesterday&&now.m<c)return {open:true,until:c};
    }
  }
  return known?{open:false,until:null}:null;
}
let openNow=false;
function openNowOk(d){ return !openNow || (openState(d.h)||{}).open===true; }
function themeLabel(k){const e=TI[k];return e&&e[L_]?e[L_]:String(k||'');}
const GRP=[
  {k:'edu',cats:['college','school','elem','schoolbus']},
  {k:'health',cats:['hospital','dental','vet','pharmacy']},
  {k:'housing',cats:['apt','propmgmt']},
  {k:'shop',cats:['grocery','asian','restaurant','cafe','secondhand','hardware','mall','conv','liquor']},
  // 'support' was first filed under Faith & Community because that is who runs
  // it. That is the provider's category, not the reader's: someone out of food
  // or out of housing does not go looking under a 🙏 heading, and putting it
  // there quietly says help here is a faith matter. It sits with the other
  // things-have-gone-wrong categories instead — food bank, legal, police.
  {k:'services',cats:['transit','bank','post','gov','laundry','barber','gas','police','legal','foodbank','support']},
  {k:'sports',cats:['pool','splash','gym','rink']},
  {k:'parks',cats:['park','dogpark','beach','trail']},
  {k:'culture',cats:['library','museum','cinema','heritage']},
  {k:'childcare',cats:['daycare','tutor','playcenter']},
  {k:'faith',cats:['religious','commctr','indigenous']},
  {k:'auto',cats:['taxi','driving','usedcar','autorepair']}
];
const GN={"edu":{"zh":"🎓教育","en":"🎓Education","fr":"🎓Éducation","es":"🎓Educación","ko":"🎓교육","ja":"🎓教育"},"health":{"zh":"⚕️医疗","en":"⚕️Health","fr":"⚕️Santé","es":"⚕️Salud","ko":"⚕️의료","ja":"⚕️医療"},"housing":{"zh":"🏢住房","en":"🏢Housing","fr":"🏢Logement","es":"🏢Vivienda","ko":"🏢주거","ja":"🏢住まい"},"shop":{"zh":"🛍️购物餐饮","en":"🛍️Shopping & Dining","fr":"🛍️Achats et repas","es":"🛍️Compras y restaurantes","ko":"🛍️쇼핑·외식","ja":"🛍️ショッピング・飲食"},"services":{"zh":"🧾生活服务","en":"🧾Services","fr":"🧾Services","es":"🧾Servicios","ko":"🧾생활 서비스","ja":"🧾生活サービス"},"sports":{"zh":"🏊运动健身","en":"🏊Sports & Fitness","fr":"🏊Sports et fitness","es":"🏊Deportes y fitness","ko":"🏊스포츠·피트니스","ja":"🏊スポーツ・フィットネス"},"parks":{"zh":"🌳公园户外","en":"🌳Parks & Outdoors","fr":"🌳Parcs et plein air","es":"🌳Parques y aire libre","ko":"🌳공원·야외","ja":"🌳公園・アウトドア"},"culture":{"zh":"🎭文化娱乐","en":"🎭Culture","fr":"🎭Culture","es":"🎭Cultura","ko":"🎭문화","ja":"🎭文化"},"childcare":{"zh":"👶育儿早教","en":"👶Childcare & Tutoring","fr":"👶Garde et tutorat","es":"👶Cuidado infantil y tutorías","ko":"👶육아·교육","ja":"👶育児・教育"},"faith":{"zh":"🙏信仰社区","en":"🙏Faith & Community","fr":"🙏Culte et communauté","es":"🙏Fe y comunidad","ko":"🙏신앙·커뮤니티","ja":"🙏信仰・コミュニティ"},"auto":{"zh":"🚗交通用车","en":"🚗Transportation & Auto","fr":"🚗Transport et auto","es":"🚗Transporte y autos","ko":"🚗교통·자동차","ja":"🚗交通・自動車"}};
