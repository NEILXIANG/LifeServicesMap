# -*- coding: utf-8 -*-
"""Populates sameComplex, and demotes one coordinate the audit proved wrong.

sameComplex has been in the schema since Costco was split into a warehouse and a
gas bar, but nothing ever rendered it and only those two rows used it — so nine
other pairs of markers sat on top of each other with no explanation, which reads
as duplicate data rather than as "the post outlet is the counter at the back of
that pharmacy". It becomes an array here because one group has three members.
"""
import json, re, math
import os, sys
_r = os.path.dirname(os.path.abspath(__file__))
for _ in range(6):
    if os.path.exists(os.path.join(_r, 'kamdata.py')): break
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
import kamdata


GROUPS = [
  # a park and the water play inside it — the note already said so in prose
  ['McDonald Park', 'McDonald Park Spray Park'],
  ['Westsyde Centennial Park', 'Westsyde Centennial Water Park'],
  # one strip unit, two businesses
  ['Anytime Fitness', "Lil' Monkey's Treehouse"],
  ['K-SPOON', 'The Manila Social by Romeo'],
  # one address on Fortune Dr holding a bank branch, a building and its manager
  ['BMO(North Shore)', 'Ashview Apartments', 'Sunden Management'],
  # postal counters live inside the pharmacy; the gas bar shares the forecourt
  ['Shoppers Drug Mart(Summit)', 'Canada Post(Summit Dr/Shoppers)'],
  ['Shoppers Drug Mart(Valleyview)', 'Canada Post(Valleyview)'],
  ['Chevron(8th St)', 'On The Run(Chevron)'],
  ['Esso(8th St)', 'Hasty Mart'],
  ['Costco Wholesale', 'Costco Gas Station'],
  # both at 301 Victoria St, in different units — surfaced only once the
  # street-geometry repair moved them onto the same block
  ['TD Canada Trust(Victoria St)', 'Okanagan Thompson Legal Clinic'],
]

# 1210 Summit Dr and 1380 Summit Dr cannot be three metres apart. The two records
# at 1210 agree with each other, so it is 1380 that carries a coordinate borrowed
# from the neighbouring plaza. The address is right and Directions uses the
# address, so the honest repair — short of standing there — is to stop the pin
# claiming a precision it does not have.
DEMOTE = ['Summit Medical Clinic']

P = kamdata.load('P')
by = {p['n']: p for p in P}

for p in P:
    p.pop('sameComplex', None)
for g in GROUPS:
    for n in g:
        assert n in by, 'unknown place in a sameComplex group: %r' % n
    for n in g:
        by[n]['sameComplex'] = [by[o]['id'] for o in g if o != n]

for n in DEMOTE:
    assert n in by, n
    by[n]['precision'] = 'low'

kamdata.save('P', P)
print('sameComplex on %d records in %d groups; %d coordinate(s) demoted'
      % (sum(1 for p in P if p.get('sameComplex')), len(GROUPS), len(DEMOTE)))
