# -*- coding: utf-8 -*-
"""Three records the audit showed were missing, all verified against an official
or first-party source today. Every one is src='stub-pending-verify' and
precision='low' because the *address, phone and hours* come from the operator's
own page but the *coordinate* does not: no geocoder was reachable, so each pin
was interpolated from the transit feed's own surveyed stops on the same street.
The popup now says so. Promote to src='official' after standing at the door."""
import json, re, hashlib

NEW = [
 {"n":"Kamloops Food Bank","c":"foodbank","g":"ns",
  "lat":50.685,"lng":-120.352,"a":"171 Wilson St",
  "w":"https://kamloopsfoodbank.org/clients/","p":"250-376-2252",
  "note":{
   "zh":"⭐ 面向有需要的家庭发放食物，凭家中每位成员的身份证件即可，不看移民身份。家庭/单亲与单身/夫妇分在不同日子领取，60岁以上长者有更早的时段；中午有休息时间。领取频率与当期时段请以官网或电话为准。",
   "en":"⭐ Food for households in need, on presentation of ID for each household member; immigration status is not screened. Families/single parents and singles/couples attend on different days, with an earlier slot for seniors 60+ and a break over midday. Confirm current times and how often you can attend on the website or by phone.",
   "fr":"⭐ Nourriture pour les ménages dans le besoin, sur présentation d'une pièce d'identité par membre du ménage; le statut d'immigration n'est pas vérifié. Familles et parents seuls d'un côté, personnes seules et couples de l'autre, à des jours différents, avec une plage plus tôt pour les 60 ans et plus et une pause le midi. Confirmez les heures et la fréquence sur le site ou par téléphone.",
   "es":"⭐ Alimentos para hogares que lo necesitan, presentando una identificación por cada miembro del hogar; no se revisa la situación migratoria. Familias y padres solos por un lado, personas solas y parejas por otro, en días distintos, con un horario más temprano para mayores de 60 años y una pausa al mediodía. Confirme horarios y frecuencia en el sitio web o por teléfono.",
   "ko":"⭐ 도움이 필요한 가구에 식품을 제공하며, 가구 구성원 각자의 신분증을 제시하면 됩니다. 이민 신분은 확인하지 않습니다. 가족·한부모 가구와 1인·부부 가구가 서로 다른 요일에 방문하고, 60세 이상 노인은 더 이른 시간대가 있으며 점심 무렵 휴식 시간이 있습니다. 정확한 시간과 이용 횟수는 홈페이지나 전화로 확인하세요."},
  "src":"stub-pending-verify","precision":"low"},

 {"n":"St. Andrew's on the Square","c":"heritage","g":"sk",
  "lat":50.675,"lng":-120.338,"a":"159 Seymour St",
  "w":"https://www.kamloops.ca/recreation-culture/culture-heritage/heritage-buildings/st-andrews-square",
  "note":{
   "zh":"建于1887年，是全市最古老的公共建筑，晚期维多利亚哥特复兴风格。1991年险被拆除，1996年由市政府买下修复并连同旁边的广场重新向公众开放；2026年完成又一轮大修后重开，现作为活动与文化场地使用。开放时间随活动安排变动，前往前请查官网。",
   "en":"Built in 1887 and the city's oldest public building, in late Victorian Gothic Revival style. Saved from demolition in 1991, bought and restored by the City in 1996 and reopened to the public along with the square beside it; it reopened again in 2026 after a further major restoration, and is used as an events and cultural venue. Opening depends on what is booked, so check the website before going.",
   "fr":"Construit en 1887, c'est le plus ancien bâtiment public de la ville, de style néogothique victorien tardif. Sauvé de la démolition en 1991, acheté et restauré par la Ville en 1996 puis rouvert au public avec la place attenante; il a rouvert de nouveau en 2026 après une autre restauration majeure et sert de lieu d'événements et de culture. L'ouverture dépend des réservations : vérifiez le site avant de vous déplacer.",
   "es":"Construido en 1887, es el edificio público más antiguo de la ciudad, de estilo neogótico victoriano tardío. Se salvó de la demolición en 1991, la Ciudad lo compró y restauró en 1996 y lo reabrió al público junto con la plaza contigua; volvió a reabrir en 2026 tras otra restauración importante y se usa como sede de eventos y actividades culturales. La apertura depende de lo que esté reservado: consulte el sitio web antes de ir.",
   "ko":"1887년에 지어진 이 도시에서 가장 오래된 공공 건축물로, 후기 빅토리아 고딕 리바이벌 양식입니다. 1991년 철거 위기를 넘긴 뒤 1996년 시가 매입·복원해 옆 광장과 함께 다시 공개했고, 2026년 대규모 보수를 마치고 재개관해 행사·문화 공간으로 쓰입니다. 개방 여부는 예약 일정에 따라 달라지므로 방문 전 홈페이지를 확인하세요."},
  "src":"stub-pending-verify","precision":"low"},

 {"n":"The Old Courthouse","c":"heritage","g":"sk",
  "lat":50.675,"lng":-120.339,"a":"7 Seymour St W",
  "w":"https://www.kamloops.ca/recreation-culture/culture-heritage/heritage-buildings/old-courthouse",
  "note":{
   "zh":"1909年落成的三层法院旧址，现归市政府所有，作为艺术、文化与社区活动的场地使用，本地艺术组织在此办展览与演出。是否开放取决于当期活动，前往前请查官网。",
   "en":"A three-storey courthouse completed in 1909, now owned by the City and used as a hub for arts, culture and community events, with local arts organisations running exhibitions and performances here. Whether it is open depends on what is on, so check the website before going.",
   "fr":"Un palais de justice de trois étages achevé en 1909, aujourd'hui propriété de la Ville et utilisé comme pôle des arts, de la culture et des activités communautaires; des organismes artistiques locaux y présentent expositions et spectacles. L'ouverture dépend de la programmation : vérifiez le site avant de vous déplacer.",
   "es":"Un juzgado de tres plantas terminado en 1909, hoy propiedad de la Ciudad y usado como centro de arte, cultura y actividades comunitarias, donde organizaciones artísticas locales realizan exposiciones y funciones. Que esté abierto depende de la programación: consulte el sitio web antes de ir.",
   "ko":"1909년에 완공된 3층짜리 옛 법원 건물로, 현재는 시 소유이며 예술·문화·지역 행사 공간으로 쓰입니다. 지역 예술 단체가 이곳에서 전시와 공연을 엽니다. 개방 여부는 그때의 프로그램에 따라 달라지므로 방문 전 홈페이지를 확인하세요."},
  "src":"stub-pending-verify","precision":"low"},
]

path='src/data-kamloops.js'
s=open(path,encoding='utf-8').read()
m=re.search(r"const P=(\[.*?\]);\n", s, re.S)
P=json.loads(m.group(1))
have={p['n'] for p in P}
ids={p['id'] for p in P}
today='2026-09-07'
for r in NEW:
    assert r['n'] not in have, r['n']
    r['v']=today
    r['id']=hashlib.sha1(r['n'].encode()).hexdigest()[:8]
    assert r['id'] not in ids, r['id']
    ids.add(r['id'])
    P.append(r)

# The thrift store at 344 Poplar St already carried a half-sentence about food
# assistance; the audit showed the operator publishes real hours for it, and a
# reader who needs food should not have to guess whether "also provides food"
# means a hamper programme or a shelf by the till.
EXTRA={
 "zh":"价格最低的二手店；同一机构还在此提供社区服务：紧急食物包（需带当期收入证明，申请在中午前截止）、衣物与家具代金券，另有每周两次的流动厨房。前往前请致电或查官网确认时段。",
 "en":"The lowest prices among the thrift stores; the same organisation also runs community services here — emergency food hampers (bring proof of current income; applications close before midday), vouchers for clothing and furniture, and a mobile kitchen twice a week. Phone or check the website for current times before going.",
 "fr":"Les prix les plus bas parmi les magasins d'occasion; le même organisme y offre aussi des services communautaires — paniers alimentaires d'urgence (apportez une preuve de revenu courant; les demandes ferment avant midi), bons pour vêtements et meubles, et une cuisine mobile deux fois par semaine. Téléphonez ou consultez le site pour les heures avant de vous déplacer.",
 "es":"Los precios más bajos entre las tiendas de segunda mano; la misma organización ofrece aquí además servicios comunitarios — despensas de emergencia (lleve comprobante de ingresos actuales; las solicitudes cierran antes del mediodía), vales para ropa y muebles, y una cocina móvil dos veces por semana. Llame o consulte el sitio web para los horarios antes de ir.",
 "ko":"중고매장 중 가격이 가장 저렴합니다. 같은 단체가 이곳에서 지역사회 서비스도 운영합니다 — 긴급 식품 꾸러미(현재 소득 증빙 지참, 신청은 정오 전 마감), 의류·가구 바우처, 그리고 주 2회 이동식 급식입니다. 방문 전 전화하거나 홈페이지에서 시간을 확인하세요."}
for p in P:
    if p['n']=='The Salvation Army':
        p['note']=EXTRA; p['v']=today; break
else:
    raise SystemExit('Salvation Army record not found')

body=json.dumps(P,ensure_ascii=False,separators=(',',':'))
open(path,'w',encoding='utf-8').write(s[:m.start(1)]+body+s[m.end(1):])
print('now %d places' % len(P))
