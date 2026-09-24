#!/usr/bin/env python3
"""2026-09-24 — a search for "school" missed the elementary schools.

The synonym table matched a term whole or by its start, so "school" reached
"school bus" but not "elementary school" or "high school" — the word is in the
middle. A parent searching the most obvious word got the secondary schools and
only the handful of elementary schools whose notes happened to contain it.

Each word of a multi-word term is now indexed too, so a query can match a term
by any of its words:
  school  -> elementary school, high school, school bus, driving school
  centre  -> community centre, shopping centre, aquatic centre
  store   -> grocery store, liquor store, convenience store, thrift store
Only words of 4+ Latin letters or 2+ CJK characters are indexed, so the
connecting words in "tienda de comestibles" or "parc à chiens" never match.
"""
import sys
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:110], n))
    return src.replace(old, new)

s = rep(s, """const _SYN_IDX=(function(){
  const m=new Map();
  const add=(t,c)=>{t=_fold(String(t).toLowerCase().trim());if(t.length<2)return;if(!m.has(t))m.set(t,new Set());m.get(t).add(c);};""",
"""const _SYN_IDX=(function(){
  const m=new Map();
  const put=(t,c)=>{if(t.length<2)return;if(!m.has(t))m.set(t,new Set());m.get(t).add(c);};
  // 2026-09-24: index each word of a multi-word term as well, so "school" finds
  // "elementary school" and "centre" finds "community centre". Short connecting
  // words ("de", "à", "d'eau") are left out: only 4+ Latin letters or 2+ CJK.
  // "clinic" on its own is not indexed: dental, vet and legal clinics are clinics
  // too, and it would put the appointment-only UPCLC into "walk-in clinic" — whose
  // note says it is not a walk-in. The full terms ("dental clinic") still match.
  const _skip=new Set(['clinic','clinics']);
  const add=(t,c)=>{
    t=_fold(String(t).toLowerCase().trim());
    put(t,c);
    if(/\\s/.test(t))t.split(/[\\s/]+/).forEach(w=>{
      w=w.replace(/^[^\\p{L}\\p{N}]+|[^\\p{L}\\p{N}]+$/gu,'');
      if(_skip.has(w))return;
      if(w.length>=4||(w.length>=2&&/[\\u3400-\\u9fff\\uac00-\\ud7af\\u3040-\\u30ff]/.test(w)))put(w,c);
    });
  };""")
open(E, 'w', encoding='utf-8').write(s)
print('p22 applied')
