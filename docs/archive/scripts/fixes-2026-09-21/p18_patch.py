#!/usr/bin/env python3
"""2026-09-22 — one synonym table for search.

Before: a category was findable only by its label in the language on screen
("Groceries", "Dental"), so "grocery", "dentist", "supermarket", "mechanic",
"牙医", "歯医者", "dentiste" all found nothing, and a Chinese reader with the
English interface typing 超市 found nothing either. Per-place `alias` lists
had been patching this one place at a time.

Now:
- SYN (engine, city-independent) lists, per category, the words people type
  for it in six languages, singular and plural, formal and everyday.
- Every category's label in all six languages is indexed too, so a search works
  whatever language the interface is in.
- Accents are ignored on both sides (epicerie = épicerie).
- Match rule: the whole query equals a term, or is the start of one — from 4
  Latin letters or 2 CJK/Hangul characters, so "tax" never becomes "taxi".
- Score 58: below a name (100/80), an alias (70/65) and the on-screen category
  label (60); above themes, address, area and notes. Nothing that used to rank
  first is pushed down.
- Per-place `alias` stays for names (T&T, UPCC); SYN is for kinds of place.
- scripts/validate.py checks the table: real categories only, no crisis words,
  no stop words, no one-letter terms, no term in two categories unless listed.
"""
import sys
sys.path.insert(0, '.')
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:100], n))
    return src.replace(old, new)

SYN_JS = r"""
// ---- 2026-09-22: one synonym table for search --------------------------------
// The words people actually type for each kind of place, in all six languages.
// A category's own labels (all six) are added automatically below. Terms are
// matched whole or as a prefix of 4+ Latin letters / 2+ CJK characters, accents
// ignored. "Clinic" is left out on purpose: dental, vet and legal clinics are
// clinics too, and a bare "clinic" would also pull in the appointment-only
// UPCLC for "walk-in clinic" (its note says "not a walk-in").
// Place names belong in a place's `alias`, not here. scripts/validate.py
// checks this table (real categories, no crisis or stop words, no duplicates).
const SYN={
 school:['high school','high schools','secondary school','secondary','highschool','中学','中學','高中','初中','중학교','고등학교','高校','中学校','lycée','collège','école secondaire','escuela secundaria','preparatoria'],
 elem:['elementary school','elementary schools','primary school','grade school','小学','小學','초등학교','小学校','école primaire','escuela primaria','primaria'],
 hospital:['hospital','hospitals','doctor','doctors','family doctor','physician','medical','medical clinic','urgent care','emergency room','医院','醫院','医生','醫生','看病','急诊','急診','병원','의원','의사','응급실','病院','医者','診療所','hôpital','médecin','urgences','médico','urgencias'],
 dental:['dentist','dentists','dental clinic','teeth','tooth','牙医','牙醫','牙科','看牙','치과','치과의사','歯医者','歯科','dentiste','dentista'],
 vet:['vet','vets','veterinarian','veterinary','animal hospital','pet clinic','兽医','獸醫','宠物医院','寵物醫院','동물병원','수의사','動物病院','獣医','vétérinaire','veterinario'],
 pharmacy:['pharmacy','pharmacies','drugstore','drug store','chemist','药房','藥房','药店','藥局','약국','薬局','ドラッグストア','pharmacie','farmacia'],
 police:['police','police station','rcmp','警察','警察局','警局','경찰','경찰서','警察署','policía','comisaría','gendarmerie'],
 pool:['pool','pools','swimming','swimming pool','swim','aquatic centre','游泳','游泳池','수영','수영장','水泳','プール','piscine','natation','piscina','natación'],
 splash:['splash pad','spray park','spray pad','戏水','水上乐园','물놀이','水遊び','jeux d\'eau'],
 gym:['gym','gyms','fitness','健身','健身房','헬스','헬스장','ジム','フィットネス','salle de sport','gimnasio'],
 rink:['rink','ice rink','skating','arena','hockey','滑冰','溜冰','冰场','冰場','스케이트','아이스링크','スケート','patinoire','patinaje','pista de hielo'],
 park:['park','parks','playground','公园','公園','操场','游乐场','공원','놀이터','parc','parque','aire de jeux'],
 dogpark:['dog park','dog parks','off-leash','off leash','狗公园','遛狗','반려견','애견','ドッグラン','parc à chiens','parque para perros'],
 beach:['beach','beaches','lake','沙滩','海滩','湖泊','해변','호수','ビーチ','plage','lac','playa','lago'],
 trail:['trail','trails','hiking','hike','walking trail','步道','徒步','远足','爬山','등산','산책로','트레일','ハイキング','登山','sentier','randonnée','sendero','senderismo'],
 library:['library','libraries','books','图书馆','圖書館','도서관','図書館','bibliothèque','biblioteca'],
 museum:['museum','museums','博物馆','博物館','박물관','musée','museo'],
 cinema:['cinema','movie','movies','movie theatre','movie theater','电影','电影院','電影院','영화','영화관','映画','映画館','cinéma','cine'],
 grocery:['grocery','groceries','grocery store','supermarket','supermarkets','超市','超级市场','超級市場','买菜','買菜','마트','슈퍼','슈퍼마켓','장보기','スーパー','スーパーマーケット','épicerie','supermarché','supermercado','tienda de comestibles'],
 asian:['asian grocery','asian market','asian supermarket','chinese grocery','chinese supermarket','chinese market','korean grocery','korean market','japanese grocery','华人超市','中国超市','中國超市','亚洲超市','亞洲超市','韩国超市','日本超市','한인마트','한국마트','한국 마트','아시아 마트','アジア食材','中華食材','韓国食材','épicerie asiatique','supermercado asiático'],
 restaurant:['restaurant','restaurants','dining','餐馆','餐館','餐厅','餐廳','饭店','吃饭','식당','음식점','레스토랑','レストラン','食堂','飲食店','restaurante'],
 secondhand:['thrift','thrift store','thrift shop','second hand','second-hand','secondhand','used clothes','used furniture','二手','二手店','旧货','중고','중고매장','リサイクル','古着','friperie','segunda mano','ropa usada'],
 hardware:['hardware store','tools','五金','五金店','建材','철물점','공구','ホームセンター','金物','quincaillerie','ferretería'],
 mall:['mall','shopping centre','shopping center','shopping mall','商场','商場','购物中心','購物中心','쇼핑몰','ショッピングモール','centre commercial','centro comercial'],
 transit:['bus','buses','bus stop','bus exchange','transit','公交','公交车','公車','巴士','버스','대중교통','バス','autobus','autobús'],
 bank:['bank','banks','banking','atm','银行','銀行','은행','banque','banco'],
 post:['post office','mail','canada post','邮局','郵局','寄信','우체국','郵便局','bureau de poste','correos','oficina de correos'],
 conv:['convenience store','corner store','便利店','편의점','コンビニ','dépanneur','tienda de conveniencia'],
 liquor:['liquor','liquor store','alcohol','beer','wine','买酒','酒类','주류','酒屋','alcool','licorería'],
 gov:['government','government office','immigration','service canada','政府','移民','政务','정부','이민','役所','gouvernement','gobierno','inmigración'],
 laundry:['laundry','laundromat','coin laundry','洗衣','洗衣店','自助洗衣','빨래방','세탁소','コインランドリー','laverie','lavandería'],
 barber:['barber','barbers','hair','haircut','hair salon','hairdresser','理发','理髮','剪头发','美发','이발','미용실','헤어','美容院','床屋','散髪','coiffeur','peluquería','barbería'],
 gas:['gas','gas station','fuel','petrol','加油','加油站','주유소','ガソリン','essence','gasolinera'],
 apt:['apartment','apartments','rent','rental','rentals','housing','租房','公寓','아파트','원룸','월세','アパート','賃貸','appartement','logement','apartamento','alquiler'],
 schoolbus:['school bus','校车','校車','스쿨버스','通学バス','autobus scolaire','autobús escolar'],
 religious:['church','churches','mosque','temple','gurdwara','synagogue','worship','教会','教會','教堂','寺庙','清真寺','교회','성당','モスク','église','mosquée','iglesia','mezquita','templo'],
 commctr:['community centre','community center','rec centre','recreation centre','社区中心','社區中心','活动中心','커뮤니티센터','公民館','centre communautaire','centro comunitario'],
 taxi:['taxi','cab','uber','lyft','rideshare','出租车','計程車','的士','打车','택시','タクシー'],
 driving:['driving school','driving lessons','驾校','駕校','学车','운전학원','教習所','auto-école','autoescuela'],
 usedcar:['used car','used cars','car dealer','二手车','二手車','买车','중고차','中古車','voiture d\'occasion','auto usado','carro usado'],
 autorepair:['mechanic','auto repair','car repair','garage','oil change','tires','修车','修車','汽车维修','汽修','정비소','카센터','自動車修理','garagiste','mécanicien','mecánico','taller mecánico'],
 daycare:['daycare','day care','childcare','child care','托儿所','托兒所','日托','어린이집','保育園','garderie','crèche','guardería'],
 tutor:['tutor','tutoring','补习','補習','家教','补课','학원','과외','家庭教師','tutorat','tutoría','clases particulares'],
 playcenter:['indoor playground','play centre','play center','室内乐园','淘气堡','키즈카페','키즈 카페','室内遊び場','キッズパーク'],
 legal:['lawyer','lawyers','legal aid','legal help','law','律师','律師','法律','법률','변호사','弁護士','法律相談','avocat','abogado'],
 propmgmt:['property management','property manager','rental agency','rent','rental','rentals','housing','租房中介','物业','物業','부동산','不動産','agence immobilière','inmobiliaria'],
 foodbank:['food bank','free food','food hamper','食物银行','食物銀行','免费食物','免費食物','푸드뱅크','무료 음식','フードバンク','食料支援','banque alimentaire','banco de alimentos','comida gratis'],
 heritage:['heritage','historic','history','historic site','历史','歷史','古迹','역사','史跡','patrimoine','histórico'],
 indigenous:['indigenous','first nations','aboriginal','native','métis','原住民','원주민','先住民','autochtone','indígena'],
 support:['shelter','shelters','homeless','outreach','庇护所','庇護所','无家可归','無家可歸','쉼터','노숙','シェルター','refuge','refugio','albergue']
};
// Accents never decide a match: "epicerie" finds épicerie. NFC afterwards puts
// Hangul and kana back together, so only Latin diacritics are dropped.
function _fold(s){try{return String(s).normalize('NFD').replace(/[̀-ͯ]/g,'').normalize('NFC');}catch(e){return String(s);}}
const _SYN_IDX=(function(){
  const m=new Map();
  const add=(t,c)=>{t=_fold(String(t).toLowerCase().trim());if(t.length<2)return;if(!m.has(t))m.set(t,new Set());m.get(t).add(c);};
  Object.keys(CI).forEach(c=>Object.values(CI[c]).forEach(lab=>{add(lab,c);String(lab).split('/').forEach(x=>add(x,c));}));
  Object.keys(SYN).forEach(c=>{if(CI[c])SYN[c].forEach(t=>add(t,c));});
  return m;
})();
const _synCache=new Map();
function synCats(q){
  q=_fold(String(q||'').toLowerCase().trim());
  let r=_synCache.get(q);if(r)return r;
  r=new Set();
  const cjk=/[㐀-鿿가-힯぀-ヿ]/.test(q);
  const pre=q.length>=(cjk?2:4);
  if(q.length>=2)_SYN_IDX.forEach((cs,t)=>{if(t===q||(pre&&t.startsWith(q)))cs.forEach(c=>r.add(c));});
  if(_synCache.size>400)_synCache.clear();
  _synCache.set(q,r);return r;
}
"""

anchor = "function catLabel(c){const e=CI[c];return e&&e[L_]?e[L_]:String(c||'');}\n"
s = rep(s, anchor, anchor + SYN_JS.lstrip('\n'))

s = rep(s, "  if(cat.startsWith(q)||cat.includes(q))return 60;\n",
           "  if(cat.startsWith(q)||cat.includes(q))return 60;\n"
           "  // the synonym table: any word for this kind of place, in any of the six languages\n"
           "  if(synCats(q).has(d.c))return 58;\n")
# ---- 2. closest matches never hide better matches behind a filter ------------
# Found 2026-09-22 while analysing search + category filters: with "Parks"
# selected, "dog park open now" showed 22 ordinary parks as the closest matches
# while the city's 5 dog parks sat hidden by the filter. The fallback now scores
# every place, and shows in-filter matches only when nothing outside the filters
# matches more of the words. Otherwise the existing empty state says the filters
# are the reason and offers to clear them.
s = rep(s, """      const cand=[];
      M.forEach(m=>{
        if(!markerPasses(m,1))return;              // the active filters still apply
        let hit=0,sc=0;
        words.forEach(w=>{const x=matchScore1(m.data,w);if(x>=40){hit++;sc+=x;}});
        if(hit)cand.push({m,hit,sc});
      });
      const floor=Math.max(1,Math.ceil(words.length/2));
      for(let need=words.length;need>=floor&&!v;need--){""",
"""      const cand=[];let bestAll=0,bestIn=0;
      M.forEach(m=>{
        let hit=0,sc=0;
        words.forEach(w=>{const x=matchScore1(m.data,w);if(x>=40){hit++;sc+=x;}});
        if(!hit)return;
        if(hit>bestAll)bestAll=hit;
        if(!markerPasses(m,1))return;              // the active filters still apply
        if(hit>bestIn)bestIn=hit;
        cand.push({m,hit,sc});
      });
      const floor=Math.max(1,Math.ceil(words.length/2));
      // a closer match exists outside the filters: say so (empty state), don't guess inside them
      if(bestIn<bestAll)cand.length=0;
      for(let need=words.length;need>=floor&&!v;need--){""")
# ---- 3. a superseded focus gives up --------------------------------------------
# focusMarker's 1.6 s fallback opened its popup even when the reader had since
# asked for a different place: a one-result search (動物病院 → the vet) followed
# within 1.6 s by "Show it on the map" in the health box ended on the vet's card.
# Pre-existing; surfaced by the timing of the larger result sets. Each focus now
# takes a number, and a stale one opens nothing.
s = rep(s, "let _focusPending=null;\n", "let _focusPending=null,_focusGen=0;\n")
s = rep(s, """  if(cluster&&cluster.hasLayer(m)){
    _focusPending=m;
    let shown=false;""", """  const gen=++_focusGen;
  if(cluster&&cluster.hasLayer(m)){
    _focusPending=m;
    let shown=false;""")
s = rep(s, """    const show=()=>{
      if(shown)return;
      shown=true;""", """    const show=()=>{
      if(shown||gen!==_focusGen)return;   // the reader has asked for another place since
      shown=true;""")
# ---- 4. a full name typed is a name ---------------------------------------------
# With the table, "South Kamloops Secondary" also matched Kamloops School of the
# Arts word by word ("secondary" is now its category), so the one-result search
# no longer opened the school's card. When some place's name contains the whole
# multi-word query, the reader typed a name: word-by-word matching is skipped.
# Across 308 test queries this changes one: "community centre" drops two loose
# word matches (a food centre, the friendship society).
s = rep(s, """function matchScore(d,q){
  const whole=matchScore1(d,q);
  if(whole>0)return whole;
  const words=q.split(/\\s+/).filter(w=>w.length>=2);
  if(words.length<2)return 0;
""", """const _nameHitCache=new Map();
function _someNameHas(q){
  let r=_nameHitCache.get(q);
  if(r===undefined){r=P.some(p=>p.n.toLowerCase().includes(q));if(_nameHitCache.size>400)_nameHitCache.clear();_nameHitCache.set(q,r);}
  return r;
}
function matchScore(d,q){
  const whole=matchScore1(d,q);
  if(whole>0)return whole;
  const words=q.split(/\\s+/).filter(w=>w.length>=2);
  if(words.length<2)return 0;
  if(_someNameHas(q))return 0;           // a whole name was typed: only whole-query matches
""")
open(E, 'w', encoding='utf-8').write(s)
print('p18 applied')
