#!/usr/bin/env python3
"""2026-09-22 — link check fixes. Every replacement URL below was opened on
2026-09-22 (container fetch and/or the maintainer's Chrome) and returned the
right page:

  kamloopssalvationarmy.ca/programs/emergency-food-bank   "Emergency Food Bank", lists 344 Poplar St
  www.kafs.ca/program/mini-storage                         "Mini Storage | KAFS" (old URL redirected here)
  www.kamloops.ca/recreation-culture/aquatics/pool-facilities  lists Canada Games Aquatic Centre
  www.windsorplywood.com/pages/kamloops                   "Windsor Plywood Kamloops" (.ca redirected here)
  www.costco.ca/w/-/bc/kamloops/161                       "Kamloops, BC Warehouse" (already used by the gas bar)
  www.td.com/ca/en/personal-banking/branch-locator        TD Canada Trust locator (www.td.com went to the US site)
  journie.ca/chevron/bc-en/locations                      Chevron BC station finder, for the two Chevron entries with a site (www.chevron.ca timed out
                                                          in the maintainer's browser and resets from the container)
  www.facebook.com/staytunedautorepair/                   the shop's own page (staytunedauto.ca is NXDOMAIN)
  www.canadapost-postescanada.ca/cpc/en/tools/find-a-post-office.page   "Find a post office"
  www2.gov.bc.ca/…/eligibility-and-enrolment/apply-for-msp "Apply for MSP" (old /enrolment is 404)
  icbc.com/driver-licensing/moving-bc/moving-from-another-country  "Moving from outside Canada" (old is 404)
  canada.ca/fr/…/programme-communautaire-benevoles-matiere-impot.html  "Comptoirs d'impôts gratuits"
                                                          (the …-impots.html spelling is "Pas trouvé")
Only URLs change; no text, id, step or field is added or removed."""
import sys
E, D = 'src/engine.html', 'src/data-kamloops.js'
s = open(E, encoding='utf-8').read()
d = open(D, encoding='utf-8').read()
def rep(src, old, new, count):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:100], n))
    return src.replace(old, new)

W = lambda u: '"w":"%s"' % u
d = rep(d, W('https://www.kamloopssalvationarmy.ca/community-services/'),
           W('https://kamloopssalvationarmy.ca/programs/emergency-food-bank'), 1)
d = rep(d, W('https://kafs.ca/programs-services/mini-storage-units/'),
           W('https://www.kafs.ca/program/mini-storage'), 1)
d = rep(d, W('https://www.kamloops.ca/recreation-culture/aquatics'),
           W('https://www.kamloops.ca/recreation-culture/aquatics/pool-facilities'), 1)
d = rep(d, W('https://www.windsorplywood.ca/pages/kamloops'),
           W('https://www.windsorplywood.com/pages/kamloops'), 1)
d = rep(d, W('https://www.costco.ca'), W('https://www.costco.ca/w/-/bc/kamloops/161'), 1)
d = rep(d, W('https://www.td.com'), W('https://www.td.com/ca/en/personal-banking/branch-locator'), 3)
d = rep(d, W('https://www.chevron.ca'), W('https://journie.ca/chevron/bc-en/locations'), 2)
d = rep(d, W('https://www.staytunedauto.ca/'), W('https://www.facebook.com/staytunedautorepair/'), 1)
d = rep(d, W('https://www.canadapost-postescanada.ca'),
           W('https://www.canadapost-postescanada.ca/cpc/en/tools/find-a-post-office.page'), 7)

s = rep(s, 'https://www2.gov.bc.ca/gov/content/health/health-drug-coverage/msp/bc-residents/enrolment"',
           'https://www2.gov.bc.ca/gov/content/health/health-drug-coverage/msp/bc-residents/eligibility-and-enrolment/apply-for-msp"', 6)
s = rep(s, 'https://www.icbc.com/driver-licensing/new-to-bc"',
           'https://icbc.com/driver-licensing/moving-bc/moving-from-another-country"', 6)
s = rep(s, 'programme-communautaire-benevoles-matiere-impots.html',
           'programme-communautaire-benevoles-matiere-impot.html', 1)

# The Chevron stations' own names are unchanged; make sure none still points at the dead host.
for _bad, _src in (("chevron.ca\"", d), ("staytunedauto.ca", d), ("/new-to-bc", s)):
    assert _bad not in _src, _bad
open(D, 'w', encoding='utf-8').write(d)
open(E, 'w', encoding='utf-8').write(s)
print('p9 applied')
