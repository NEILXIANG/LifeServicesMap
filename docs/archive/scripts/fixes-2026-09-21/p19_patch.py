#!/usr/bin/env python3
"""2026-09-22 — search pauses the category filter (the maintainer chose plan B).

Why: a category and a search both answer "what am I looking for"; the newer one
is the reader's current intent. Areas ("where"), themes (qualities such as free
or indoor), "open now" and "near me" still narrow a search, as before — the
2026-09 complaint that led to "search narrows within filters" was about an
area being ignored, and that stays fixed.

What changes:
1. While a search is active, markers are not filtered by category. Clearing
   the search brings the categories back unchanged.
2. The latest input wins in both directions: turning a category, a category
   group or a Quick Pick ON during a search ends the search (otherwise the tap
   would visibly do nothing). Turning one off leaves the search alone.
3. It is said wherever it matters, in six languages: the note under the search
   box, a line at the top of the category panel, the category chip and the
   paused category buttons. The theme help text and the two
   "narrowed by area/category filters" messages no longer claim categories
   narrow a search.
4. Counts, empty state, "open now" handling, map fitting and search logging
   read the effective filters (categories excluded while searching).
   search_run.filtered no longer counts categories; catsPaused:true says they
   were set. search_clear gains by:'category'/'preset' when a tap ends a search.
"""
import sys
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:120], n))
    return src.replace(old, new)

# ---- strings -----------------------------------------------------------------
S = {
 'searchActive': {
  'zh': ("搜索结果已按当前的区域/分类筛选缩小范围", "搜索结果已按当前的区域等筛选缩小范围"),
  'en': ("Results narrowed by your current area/category filters", "Results narrowed by your current area and other filters"),
  'fr': ("Résultats restreints par vos filtres de secteur/catégorie actuels", "Résultats restreints par votre secteur et vos autres filtres actuels"),
  'es': ("Resultados limitados por sus filtros de zona/categoría actuales", "Resultados limitados por su zona y sus otros filtros actuales"),
  'ko': ("현재 지역/분류 필터에 맞춰 결과가 좁혀졌습니다", "현재 지역 등 필터에 맞춰 결과가 좁혀졌습니다"),
  'ja': ("現在のエリア／カテゴリーフィルターで結果が絞り込まれています", "現在のエリアなどのフィルターで結果が絞り込まれています"),
 },
 'noResultFiltered': {
  'zh': ("在当前的区域/分类筛选范围内，没有匹配这次搜索的地点。", "在当前的筛选条件（区域、主题、现在营业等）下，没有匹配这次搜索的地点。"),
  'en': ("No places match this search within your current area/category filters.", "No places match this search with your current filters (area, theme, open now…)."),
  'fr': ("Aucun lieu ne correspond à cette recherche dans vos filtres de secteur/catégorie actuels.", "Aucun lieu ne correspond à cette recherche avec vos filtres actuels (secteur, thème, ouvert maintenant…)."),
  'es': ("Ningún lugar coincide con esta búsqueda dentro de sus filtros de zona/categoría actuales.", "Ningún lugar coincide con esta búsqueda con sus filtros actuales (zona, tema, abierto ahora…)."),
  'ko': ("현재 지역/분류 필터 범위 내에서는 이 검색과 일치하는 장소가 없습니다.", "현재 필터(지역, 테마, 지금 영업 중 등)로는 이 검색과 일치하는 장소가 없습니다."),
  'ja': ("現在のエリア／カテゴリーフィルター内では、この検索に一致する場所がありません。", "現在のフィルター（エリア、テーマ、営業中など）では、この検索に一致する場所がありません。"),
 },
}
for key, per in S.items():
    for l, (old, new) in per.items():
        s = rep(s, "UI.%s.%s='%s'" % (l, key, old), "UI.%s.%s='%s'" % (l, key, new))

HINT_ADD = {
 'zh': '搜索时分类筛选会暂停，只按区域、主题等筛选；清空搜索后恢复。',
 'en': ' While you search, categories are paused and only areas, themes and the other filters apply; clearing the search brings them back.',
 'fr': ' Pendant une recherche, les catégories sont mises en pause : seuls les secteurs, les thèmes et les autres filtres s’appliquent ; effacer la recherche les rétablit.',
 'es': ' Mientras busca, las categorías quedan en pausa y solo se aplican las zonas, los temas y los demás filtros; al borrar la búsqueda vuelven a aplicarse.',
 'ko': ' 검색하는 동안에는 분류 필터가 잠시 꺼지고 지역·테마 등 나머지 필터만 적용됩니다. 검색어를 지우면 다시 적용됩니다.',
 'ja': '検索中はカテゴリーの絞り込みが一時停止し、エリアやテーマなどのフィルターだけが適用されます。検索を消すと元に戻ります。',
}
import re
for l, add in HINT_ADD.items():
    m = re.search(r"UI\.%s\.themeHint='([^']*)'" % l, s)
    assert m and s.count(m.group(0)) == 1, l
    s = s.replace(m.group(0), "UI.%s.themeHint='%s%s'" % (l, m.group(1), add))

NEW_STR = (
 "UI.zh.catsPausedNote='搜索时暂停分类筛选，清空搜索后恢复';"
 "UI.en.catsPausedNote='Categories are paused while you search — clear the search to bring them back';"
 "UI.fr.catsPausedNote='Catégories en pause pendant la recherche — effacez la recherche pour les rétablir';"
 "UI.es.catsPausedNote='Categorías en pausa mientras busca: borre la búsqueda para volver a aplicarlas';"
 "UI.ko.catsPausedNote='검색하는 동안 분류 필터는 잠시 꺼집니다 — 검색어를 지우면 다시 적용됩니다';"
 "UI.ja.catsPausedNote='検索中はカテゴリーの絞り込みを一時停止しています — 検索を消すと元に戻ります';\n"
 "UI.zh.catsPausedShort='搜索时暂停';UI.en.catsPausedShort='paused while searching';"
 "UI.fr.catsPausedShort='en pause pendant la recherche';UI.es.catsPausedShort='en pausa durante la búsqueda';"
 "UI.ko.catsPausedShort='검색 중 일시 중지';UI.ja.catsPausedShort='検索中は一時停止';\n")
m = re.search(r"UI\.zh\.searchClosestN=[^\n]*\n", s)
assert m and s.count(m.group(0)) == 1
s = s.replace(m.group(0), m.group(0) + NEW_STR)

# ---- CSS -----------------------------------------------------------------------
s = rep(s, "  .cat-btn.zero .icon{filter:grayscale(1);}\n",
"""  .cat-btn.zero .icon{filter:grayscale(1);}
  /* 2026-09-22: a selected category while a search runs — kept, but visibly on hold */
  .cat-btn.active.paused{opacity:.55;}
  .cat-paused-note{margin:0 0 10px;font-size:12px;font-weight:600;color:var(--accent-text);}
  .af-chip.af-paused{opacity:.72;border-style:dashed;}
""")

# ---- the filter itself ---------------------------------------------------------
s = rep(s, "  const inFilter=(aC.size===0||aC.has(m.ck))&&aR.has(m.gk)&&themeOk(m.data)&&openNowOk(m.data)&&nearOk(m.data);",
"""  // 2026-09-22: a search pauses the category filter (it says "what", like the
  // category did — the newer one wins). Areas, themes, open now, near me still apply.
  const inFilter=(aC.size===0||!!searchTerm||aC.has(m.ck))&&aR.has(m.gk)&&themeOk(m.data)&&openNowOk(m.data)&&nearOk(m.data);""")
s = rep(s, "  return P.filter(p=>p.t&&aR.has(p.g)&&(aC.size===0||aC.has(p.c))\n",
           "  return P.filter(p=>p.t&&aR.has(p.g)&&(aC.size===0||!!searchTerm||aC.has(p.c))\n")
s = rep(s, "  const filtered=aR.size<totalR||aC.size>0||aT.size>0||openNow||nearOnly;\n  const bounds=[];",
           "  // categories do not narrow a search (see markerPasses)\n"
           "  const filtered=aR.size<totalR||(aC.size>0&&!searching)||aT.size>0||openNow||nearOnly;\n  const bounds=[];")
s = rep(s, "    const fitKey=searchTerm+'|'+[...aR].sort().join(',')+'|'+[...aC].sort().join(',')+'|'+",
           "    const fitKey=searchTerm+'|'+[...aR].sort().join(',')+'||'+")   # categories no longer change a search's result
s = rep(s, "    searching?(filtered?u.searchActive:''):(searchRaw?u.searchTooShort:'');",
           "    searching?[filtered?u.searchActive:'',aC.size?u.catsPausedNote:''].filter(Boolean).join(' · '):(searchRaw?u.searchTooShort:'');")
s = rep(s, "  const onlyOpen=openNow&&aC.size===0&&aT.size===0&&aR.size===Object.keys(RI).length;",
           "  const onlyOpen=openNow&&(aC.size===0||searching)&&aT.size===0&&aR.size===Object.keys(RI).length;")

# ---- chips and the category panel say so -------------------------------------------
s = rep(s, """  if(aC.size>0){
    const chip=document.createElement('div');chip.className='af-chip';
    chip.innerHTML='<span>🏷️ '+u.catsSelected(aC.size)+'</span><button""",
"""  if(aC.size>0){
    const chip=document.createElement('div');chip.className='af-chip'+(searchTerm?' af-paused':'');
    chip.innerHTML='<span>🏷️ '+u.catsSelected(aC.size)+(searchTerm?' · '+esc(u.catsPausedShort):'')+'</span><button""")
s = rep(s, """function renderCats(){
  const root=document.getElementById('catGrid');root.innerHTML='';
""", """function renderCats(){
  const root=document.getElementById('catGrid');root.innerHTML='';
  if(searchTerm&&aC.size){const n=document.createElement('p');n.className='cat-paused-note';n.textContent=UI[L_].catsPausedNote;root.appendChild(n);}
""")
s = rep(s, "      const b=document.createElement('button');b.className='cat-btn'+(aC.has(k)?' active':'')+(n===0?' zero':'');",
           "      const b=document.createElement('button');b.className='cat-btn'+(aC.has(k)?' active':'')+(aC.has(k)&&searchTerm?' paused':'')+(n===0?' zero':'');")

# ---- the latest input wins: choosing a category ends a search ------------------------
s = rep(s, "function clearCatFilter(){",
"""// Turning a category, a group or a Quick Pick on is a new "what"; during a search
// it would otherwise do nothing visible (search pauses categories), so it ends
// the search. Turning one off leaves the search alone.
function _endSearchFor(by){
  if(!searchTerm)return;
  trackEvent('search_clear',{had:searchRaw.length,n:lastVisible,by:by});
  searchInputEl.value='';clearTimeout(searchTimer);runSearch();
}
function clearCatFilter(){""")
s = rep(s, "        const action=aC.has(k)?'remove':'add';\n        if(aC.has(k))aC.delete(k);else aC.add(k);",
           "        const action=aC.has(k)?'remove':'add';\n        if(action==='add')_endSearchFor('category');\n        if(aC.has(k))aC.delete(k);else aC.add(k);")
s = rep(s, "      const allIn=cats.length>0&&cats.every(k=>aC.has(k));\n",
           "      const allIn=cats.length>0&&cats.every(k=>aC.has(k));\n      if(!allIn)_endSearchFor('category');\n")
s = rep(s, "    const had=selPresets.has(key);\n    if(had){selPresets.delete(key);}else{selPresets.add(key);}",
           "    const had=selPresets.has(key);\n    if(!had)_endSearchFor('preset');\n    if(had){selPresets.delete(key);}else{selPresets.add(key);}")

# ---- logging reads the effective filters -----------------------------------------------
s = rep(s, "  const filtered=aR.size<totalR||aC.size>0||aT.size>0;\n  trackEvent('search_run',{q:raw,len:raw.length,n:lastVisible,filtered:filtered,closest:_closest||undefined});",
           "  const filtered=aR.size<totalR||aT.size>0;   // categories pause during a search\n"
           "  trackEvent('search_run',{q:raw,len:raw.length,n:lastVisible,filtered:filtered,closest:_closest||undefined,catsPaused:aC.size>0||undefined});")
s = rep(s, "      filters:{areas:aR.size<totalR,cat:aC.size>0,theme:aT.size>0,route:!!selectedRoute}});",
           "      filters:{areas:aR.size<totalR,catsPaused:aC.size>0,theme:aT.size>0,route:!!selectedRoute}});")

open(E, 'w', encoding='utf-8').write(s)
print('p19 applied')
