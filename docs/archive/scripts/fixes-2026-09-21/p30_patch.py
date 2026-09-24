#!/usr/bin/env python3
"""2026-09-24 — multilingual audit before the public demo.

A full pass over every translatable string (6,747 of them across UI, categories,
areas, themes, 17 task cards, 360 place notes, seasons and hotlines) and a
runtime crawl of every surface in all six languages turned up four things.

1. A blank-page risk I introduced on 2026-09-24 (p22). The synonym index strips
   punctuation from each word with /[^\\p{L}\\p{N}]/u — a Unicode property escape,
   which is ES2018. The page's syntax floor is ES2017 (the comment above iconify
   says so, for exactly this reason): on a browser that predates property escapes
   the whole script fails to parse and the reader sees an empty page. It is now
   an explicit character range (Latin incl. accented, Hangul, kana, CJK) and the
   resulting index is byte-for-byte the same 1,046 terms — checked before/after.
   validate.py now refuses \\p{ in the app script so it cannot come back.

2. The screen-reader announcement ("Showing 387 of 387 places") stayed in the
   previous language after a language switch — it only refreshes when the count
   moves. setLang now clears it, so nothing stale is left for a screen reader to
   find. (It is .sr-only; nobody sighted ever saw it.)

3. Natural words that returned nothing. 180 everyday queries were typed in each
   language; these found zero places although the places exist:
     zh 洗衣房 食品银行 邮政 溜冰场 室内游乐场 佛寺
     fr barbier tuteur cours d'anglais
     ko 중고품 아시아마트 중국마트 애견공원 이민자 서비스 대학교 가정의
     ja お寺 韓国スーパー 移民支援 英語教室 車の修理 自動車学校
     en ESL english class
   Category words go into SYN (compounds only — a multi-word term is also
   indexed word by word, and "카 센터" would have sent every "센터" to car repair); words that point at one place (English classes
   and settlement → Kamloops Immigrant Services, whose note already describes its
   LINC classes; 대학교 → TRU) go into that place's alias, so they rank that place
   rather than a whole category. Queries with no real answer (咖啡/coffee — the
   one café was quarantined; T&T; currency exchange) are left returning nothing.

4. Spanish thousands separators were mixed inside one text ("98,000" beside
   "97.902"): the three comma forms now use the point like the other seven.
"""
import re, sys, json
E = 'src/engine.html'; D = 'src/data-kamloops.js'
s = open(E, encoding='utf-8').read(); d = open(D, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:100], n))
    return src.replace(old, new)

# ---- 1. ES2017: no Unicode property escapes
s = rep(s, "      w=w.replace(/^[^\\p{L}\\p{N}]+|[^\\p{L}\\p{N}]+$/gu,'');",
           "      // ES2017 floor: no \\p{…} property escapes (a parse error there is a blank\n"
           "      // page). Letters and digits in every script the table uses, spelled out.\n"
           "      w=w.replace(/^[^0-9A-Za-z\\u00C0-\\u024F\\u1100-\\u11FF\\u3041-\\u3096\\u30A1-\\u30FA\\u30FC\\u3131-\\u318E\\u3400-\\u9FFF\\uAC00-\\uD7AF\\uF900-\\uFAFF]+|[^0-9A-Za-z\\u00C0-\\u024F\\u1100-\\u11FF\\u3041-\\u3096\\u30A1-\\u30FA\\u30FC\\u3131-\\u318E\\u3400-\\u9FFF\\uAC00-\\uD7AF\\uF900-\\uFAFF]+$/g,'');")

# ---- 2. the live region is cleared on a language switch
s = rep(s, "  document.title=title;\n  document.getElementById('ogTitle')",
           "  document.title=title;\n"
           "  // the polite live region only refreshes when the count moves, so it kept the\n"
           "  // previous language's sentence; clearing it announces nothing and leaves nothing stale\n"
           "  {const ann=document.getElementById('a11yAnnounce');if(ann)ann.textContent='';}\n"
           "  document.getElementById('ogTitle')")

if len(sys.argv) > 1 and sys.argv[1] == 'regex-only':
    open(E, 'w', encoding='utf-8').write(s); print('p30 (regex + live region only)'); sys.exit(0)

# ---- 3a. category synonyms
ADD = {
 'laundry':   ['洗衣房','洗衣服','自助洗衣店','buanderie','세탁','コインランドリー店'],
 'foodbank':  ['食品银行','食品銀行','食物援助'],
 'post':      ['邮政','郵政','poste','postes canada','correo'],
 'rink':      ['溜冰场','溜冰場','滑冰场','滑冰場','스케이트장','アイスリンク'],
 'religious': ['佛寺','佛教','寺院','사찰','불교','お寺','仏教','temple bouddhiste','templo budista'],
 'playcenter':['室内游乐场','室內遊樂場','室内游乐园','실내놀이터'],
 'barber':    ['barbier','barbershop','coiffure'],
 'tutor':     ['tuteur','tutrice'],
 'secondhand':['중고품','중고가게'],
 'asian':     ['아시아마트','중국마트','韓国スーパー','中華スーパー','アジアスーパー','亚洲食品'],
 'dogpark':   ['애견공원','반려견공원','遛狗公园','ドッグパーク'],
 'autorepair':['車の修理','車修理','自動車整備','整備工場','자동차정비'],
 'driving':   ['自動車学校','自動車教習所','驾驶学校','駕駛學校'],
 'hospital':  ['가정의','가정의학과','주치의'],
}
i = s.index('const SYN={'); j = s.index('\n};', i)
block = s[i:j]
for cat, words in ADD.items():
    m = re.search(r'\n (%s):\[(.*?)\],?(?=\n)' % cat, block)
    if not m: sys.exit('SYN has no %s line' % cat)
    have = set(re.findall(r"'((?:[^'\\]|\\.)*)'", m.group(2)))
    new = [w for w in words if w not in have]
    if not new: continue
    add = ''.join(",'%s'" % w.replace("'", "\\'") for w in new)
    line = m.group(0)
    inner_end = line.rindex(']')
    block = block.replace(line, line[:inner_end] + add + line[inner_end:], 1)
s = s[:i] + block + s[j:]

# ---- 3b. place aliases: words that mean one specific place
def edit_place(d, name, extra):
    lines = d.split('\n'); hit = 0
    for k, line in enumerate(lines):
        if '"n":"%s"' % name not in line: continue
        m = re.match(r'^(\s*(?:const P=\[)?)(\{.*\})(,|\];)?\s*$', line)
        o = json.loads(m.group(2))
        assert json.dumps(o, separators=(',', ':'), ensure_ascii=False) == m.group(2), 'round-trip ' + name
        al = o.get('alias', [])
        o['alias'] = al + [a for a in extra if a not in al]
        lines[k] = m.group(1) + json.dumps(o, separators=(',', ':'), ensure_ascii=False) + (m.group(3) or '')
        hit += 1
    if hit != 1: sys.exit('%s matched %d lines' % (name, hit))
    return '\n'.join(lines)
d = edit_place(d, 'Kamloops Immigrant Services',
    ['immigrant services','newcomer services','settlement services','esl','linc','english class','english classes',
     'services aux immigrants',"cours d'anglais",'cours d’anglais','servicios para inmigrantes','clases de inglés',
     '英语课','英语班','이민자 서비스','이민자','정착 지원','영어 수업','移民支援','移民サービス','定住支援','英語教室'])
d = edit_place(d, 'Thompson Rivers University (TRU)', ['university','université','universidad','大学','大學','대학교','대학'])

# ---- 4. Spanish thousands separators, one convention per text
d = rep(d, 'aproximadamente 98,000 habitantes', 'aproximadamente 98.000 habitantes')
d = rep(d, 'y de unos 127,000 en', 'y de unos 127.000 en')
s = rep(s, '$5,000 y las', '$5.000 y las')

open(E, 'w', encoding='utf-8').write(s); open(D, 'w', encoding='utf-8').write(d)
print('p30 applied')
