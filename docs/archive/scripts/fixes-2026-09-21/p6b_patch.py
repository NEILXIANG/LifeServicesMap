#!/usr/bin/env python3
"""Phase 6b — the Mustard Seed winter shelter (report §5 item 6, checked
2026-09-21: 1140 River St, 250-571-0469, seasonal). OSM matches the street
only, so the pin sits at the next civic number on River St and says so."""
import sys, hashlib
sys.path.insert(0, '.')
import kamdata
P = kamdata.load('P'); T = kamdata.load('TASKS')
n = 'The Mustard Seed Winter Shelter'
i = hashlib.sha1(n.encode()).hexdigest()[:8]
assert not any(p['id'] == i for p in P)
dog = next(p for p in P if p['id'] == '8b5beceb')           # 1110 River St
P.append({'n': n, 'c': 'support', 'g': 'sk', 'lat': dog['lat'], 'lng': dog['lng'], 'precision': 'low',
  'a': '1140 River St', 'p': '250-571-0469', 'h': {'k': 'hCallSeason'}, 'src': 'places', 'v': '2026-09', 't': ['free'],
  'alias': ['winter shelter', 'shelter', '庇护所', '冬季', '过夜', '쉼터', 'シェルター', 'refuge', 'albergue'],
  'note': {
   'zh': 'The Mustard Seed 的冬季庇护所，天冷的几个月开放。去之前打 250-571-0469，确认已开放、还有床位。',
   'en': 'The Mustard Seed’s seasonal winter shelter, open in the colder months. Call 250-571-0469 to check it is open and has space.',
   'fr': 'Le refuge d’hiver saisonnier de The Mustard Seed, ouvert pendant les mois froids. Appelez le 250-571-0469 pour vérifier qu’il est ouvert et qu’il reste de la place.',
   'es': 'El albergue de invierno de temporada de The Mustard Seed, abierto en los meses fríos. Llame al 250-571-0469 para confirmar que está abierto y tiene sitio.',
   'ko': 'The Mustard Seed의 계절 겨울 쉼터로, 추운 몇 달 동안 엽니다. 250-571-0469로 전화해 열었는지, 자리가 있는지 확인하세요.',
   'ja': 'The Mustard Seedの季節限定の冬季シェルターで、寒い時期に開きます。開いているか、空きがあるか 250-571-0469 に電話で確認を。'},
  'id': i})
kamdata.save('P', P)
h = next(t for t in T if t['id'] == 'hardship')
W = {'en': ' In the colder months The Mustard Seed also opens a winter shelter at 1140 River St — 250-571-0469.',
     'fr': ' Pendant les mois froids, The Mustard Seed ouvre aussi un refuge d’hiver au 1140 River St — 250-571-0469.',
     'es': ' En los meses fríos, The Mustard Seed abre además un albergue de invierno en 1140 River St: 250-571-0469.',
     'zh': '天冷的几个月，The Mustard Seed 还会在 1140 River St 开冬季庇护所——250-571-0469。',
     'ko': ' 추운 몇 달 동안 The Mustard Seed는 1140 River St에 겨울 쉼터도 엽니다 — 250-571-0469.',
     'ja': '寒い時期には、The Mustard Seedが1140 River Stで冬季シェルターも開きます — 250-571-0469。'}
for l, v in W.items():
    assert '571-0469' not in h['note'][l]
    h['note'][l] += v
kamdata.save('TASKS', T)
print('phase 6b applied')
