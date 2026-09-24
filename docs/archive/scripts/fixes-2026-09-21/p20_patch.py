#!/usr/bin/env python3
"""2026-09-24 — "kindergarten" and "preschool" found nothing.

In BC these are two different things, and the table covered neither:
- Kindergarten is the first year of public elementary school (age 5), so it
  belongs to the elementary schools, not to daycare.
- Preschool (age 3–4) runs at licensed childcare centres, so it belongs to
  daycare — together with the words other languages use for that age group
  (학원 is tutoring, but 유치원 / 幼稚園 / préscolaire / preescolar / 学前班 /
  早教 all mean the pre-school year) and with "child minding", the term
  settlement agencies use for on-site care during appointments.

Nothing is removed; both words simply stop returning an empty map.
"""
import sys
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:110], n))
    return src.replace(old, new)

# kindergarten -> elementary schools (BC: kindergarten is grade K at an elementary school)
s = rep(s, " elem:['elementary school','elementary schools','primary school','grade school',",
           " elem:['elementary school','elementary schools','primary school','grade school','kindergarten','kindergartens',")

# preschool and the childminding vocabulary -> licensed childcare
s = rep(s, " daycare:['daycare','day care','childcare','child care',",
           " daycare:['daycare','day care','childcare','child care','preschool','pre-school','child minding','childminding','学前班','早教','유치원','幼稚園','préscolaire','preescolar',")

open(E, 'w', encoding='utf-8').write(s)
print('p20 applied')
