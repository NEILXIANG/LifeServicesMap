#!/usr/bin/env python3
"""2026-09-24 — the same kind of problem as "Open now" + crisis lines: help that
appears on its own and does not match what the reader asked for.

Two things appear without being asked for: the "Were you trying to do this?"
task card under a search, and the "Sick today?" answer box. 2,367 queries were
run through both (every place name, alias, category, theme, area and task title
in six languages, the synonym table, 450 everyday words, and a list of trap
words such as skill, parent, nursery, haircut). The crisis panel had no false
triggers. These did:

Task card
  food bank 食物银行 / 食品银行   → "Open a bank account"      ("银行" inside the word)
  restaurant 음식점              → "Not enough money for food" ("음식" inside the word)
  animal hospital 동물병원       → "Get care without a doctor" ("병원" inside)
  dentist 歯医者                 → the same                    ("医者" inside)
  driving school 自動車学校      → "Register a child for school"
  university 대학교              → the same                    ("학교" inside)
  rent                          → "Care for an older parent"   ("rent" inside "parents")
  ER                            → "Find settlement services"   ("er" inside a word)
  free                          → "Get legal help"             (one generic word)
  rent / 租房 / alquiler / 賃貸   → "Get your deposit back", not "Find housing safely"

"Sick today?" box
  Little Fawn Nursery (a daycare) — "nurse" inside "Nursery"
  수의사 (veterinarian)            — "의사" inside the word
  eye doctor, seguro médico (health insurance) — not someone who is sick today

Changes
  - The card is chosen in three passes, strongest first: a card with that exact
    alias; the query found in a card's own text, starting at a word boundary (so
    "rent" no longer matches "parents"); and only then the loose rule that finds
    an alias inside a longer phrase ("孩子上学"). The loose rule no longer fires
    when the query is itself a kind of place (it is in the synonym table) or a
    place's own alias — "食物银行" is a food bank, not a bank.
  - A lone generic word (free, help, gratuit, 免费, 무료, 無料 …) suggests no card.
  - The deposit card keeps its own words (deposit, landlord, tenant, 押金, 敷金,
    보증금 …); the general renting words move to "Find housing safely", which
    already carried most of them. Its Korean gains 임대. hardship gains 食品银行.
  - "rent" alone now suggests "Find housing safely" (it was an exact alias on the
    hardship card too, which comes first); hardship is still found by its own
    sentence about rent.
  - A Latin query of three letters or fewer must be a whole word ("ER" is not
    the start of every word that begins with "er").
  - Health box: "nurse" no longer matches nursery; vet, eye care and insurance
    words are excluded; and "ER" on its own now counts as a health query.
"""
import re, sys, json
E = 'src/engine.html'; D = 'src/data-kamloops.js'
s = open(E, encoding='utf-8').read(); d = open(D, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:100], n))
    return src.replace(old, new)

# ---- task card: three passes
s = rep(s, """function _taskForQuery(){
  const q=(searchRaw||searchTerm||'').trim();
  return q.length>=2?TASKS.find(t=>taskMatchesLoose(t,q)):null;
}""",
"""// 2026-09-24: strongest match first. (1) a card with this exact alias; (2) the
// query in a card's own text, starting at a word boundary; (3) only then the loose
// rule that finds an alias inside a longer phrase — and never for a query that is
// itself a kind of place or a place's own alias ("食物银行" is a food bank, not a
// bank; "동물병원" is a vet, not a clinic). A lone generic word suggests nothing.
const _TASK_GENERIC=new Set(['free','help','card','cheap','info','service','services','centre','center','office','support',
  'gratuit','gratuite','gratis','aide','ayuda','免费','免費','帮助','幫助','무료','도움','無料','助け']);
function _isPlaceWord(q){
  if(synCats(q).size)return true;
  const lq=q.toLowerCase();
  return P.some(p=>(p.alias||[]).some(a=>String(a).toLowerCase()===lq));
}
function _taskForQuery(){
  const q=(searchRaw||searchTerm||'').trim();
  if(q.length<2)return null;
  const lq=q.toLowerCase();
  if(_TASK_GENERIC.has(lq))return null;
  const exact=TASKS.find(t=>(t.alias||[]).some(a=>String(a).toLowerCase()===lq));
  if(exact)return exact;
  const strong=TASKS.find(t=>taskMatchesLoose(t,q,true));
  if(strong)return strong;
  return _isPlaceWord(q)?null:(TASKS.find(t=>taskMatchesLoose(t,q))||null);
}""")
s = rep(s, """function taskMatchesLoose(t,q){
  q=(q||'').trim().toLowerCase();if(!q)return false;
  const tx=v=>v?((v[L_]||'')+' '+(v.en||'')):'';
  const bag=[tx(t.q),tx(t.t),...(t.alias||[])].join(' ').toLowerCase();
  if(bag.indexOf(q)>=0)return true;""",
"""function taskMatchesLoose(t,q,strict){
  q=(q||'').trim().toLowerCase();if(!q)return false;
  const tx=v=>v?((v[L_]||'')+' '+(v.en||'')):'';
  const bag=[tx(t.q),tx(t.t),...(t.alias||[])].join(' ').toLowerCase();
  const cjkQ=/[\\u3400-\\u9fff\\uac00-\\ud7af\\u3040-\\u30ff]/.test(q);
  // Latin text: the query has to start at a word boundary ("rent" is not in "parents")
  if(cjkQ?bag.indexOf(q)>=0:_wordStartIn(bag,q))return true;
  if(strict&&!cjkQ)return false;""")
s = rep(s, """    // "孩子上学": the card's own alias sits inside the reader's phrase
    return (t.alias||[]).some(a=>a.length>=2&&core.indexOf(String(a).toLowerCase())>=0);""",
"""    if(strict)return false;
    // "孩子上学": the card's own alias sits inside the reader's phrase
    return (t.alias||[]).some(a=>a.length>=2&&core.indexOf(String(a).toLowerCase())>=0);""")
s = rep(s, """function taskMatchesLoose(t,q,strict){""",
"""function _wordStartIn(hay,q){
  let i=hay.indexOf(q);
  // a query of three letters or fewer ("er", "ei") must be a whole word, not a prefix
  const whole=q.length<=3,W=/[0-9a-z\\u00c0-\\u024f]/;
  while(i>=0){
    if((i===0||!W.test(hay[i-1]))&&(!whole||i+q.length>=hay.length||!W.test(hay[i+q.length])))return true;
    i=hay.indexOf(q,i+1);}
  return false;
}
function taskMatchesLoose(t,q,strict){""")

s = rep(s, """  return words.length>0&&words.every(w=>bag.indexOf(w)>=0);
}""", """  return words.length>0&&words.every(w=>_wordStartIn(bag,w));   // "er" is not in "worker"
}""")

# ---- the "Sick today?" box
s = rep(s, "const _HEALTH_RE=/doctor|clinic|walk.?in\\b|sick|urgent|nurse|\\bgp\\b|",
           "const _HEALTH_RE=/doctor|clinic|walk.?in\\b|sick|urgent|nurs[e](?!ry)|\\bgp\\b|\\ber\\b|")
s = rep(s, "const _NOT_HEALTH_RE=/\\bdent|\\bvet\\b|veterin|animal|\\bpets?\\b|legal|lawyer|\\blaw\\b|牙|兽医|獸醫|宠物|寵物|法律|치과|동물|歯|動物/i;",
           "const _NOT_HEALTH_RE=/\\bdent|\\bvet\\b|veterin|animal|\\bpets?\\b|legal|lawyer|\\blaw\\b|牙|兽医|獸醫|宠物|寵物|法律|치과|동물|수의|歯|動物|獣医"
           "|\\beyes?\\b|optom|glasses|lunettes|gafas|眼科|眼镜|眼鏡|안과|안경|目医者"
           "|insurance|seguro|assurance|保险|保險|보험|保険/i;")

# ---- task aliases
i = d.index('const TASKS='); e = d.index('\n', i)
arr = d[i + len('const TASKS='):e].rstrip()[:-1]
T = json.loads(arr); assert json.dumps(T, separators=(',', ':'), ensure_ascii=False) == arr
byid = {t['id']: t for t in T}
MOVE = ['rent', 'alquiler', 'loyer', '租房', '賃貸', '임대']
byid['deposit']['alias'] = [a for a in byid['deposit']['alias'] if a not in MOVE]
for a in ['rent', 'alquiler', 'loyer', '租房', '賃貸', '임대']:
    if a not in byid['housing']['alias']: byid['housing']['alias'].append(a)
if '食品银行' not in byid['hardship']['alias']: byid['hardship']['alias'].append('食品银行')
# "rent" alone is someone looking for a place to live; the hardship card is still
# found by its own words ("饭钱或房租不够了", "can't pay the rent")
byid['hardship']['alias'] = [a for a in byid['hardship']['alias'] if a != 'rent']
d = d[:i] + 'const TASKS=' + json.dumps(T, separators=(',', ':'), ensure_ascii=False) + ';' + d[e:]

open(E, 'w', encoding='utf-8').write(s); open(D, 'w', encoding='utf-8').write(d)
print('p34 applied')
