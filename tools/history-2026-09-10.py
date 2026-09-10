#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add the immigration-history section to guideCity in all six languages.

Sourced 2026-09-10 from the Canadian Register of Historic Places, the Province
of BC's Chinese Legacy BC and Japanese-internment sign series, the Canadian
Encyclopedia, the National Association of Japanese Canadians, and Kamloops
Immigrant Services' own history page.

Deliberately left out, because the research could not stand them up:
  · "nearly 1,700 Japanese Canadians in Kamloops" — the community's own figure,
    no independent corroboration, and implausible against the city's mid-century
    size. A number the community would spot as wrong is worse than no number.
  · "approximately 8,500 Ukrainian residents" — almost certainly an ancestry
    count reported as nationals.
  · "over 17,000 Chinese workers on the Yale-Kamloops line" — a government
    heritage register says it, but it exceeds the Canadian Encyclopedia's figure
    for the whole CPR. The national figure is used instead.
  · Any founding date for the Sikh community here. The one local source that
    documents it says plainly that it does not know.
  · The 1970s removal of grave markers by city workers — Wikipedia only, and too
    serious a claim about a public body to run on one source.

Wage figures are given as ratios rather than dollar amounts: the ratio is the
fact that matters and it does not go stale.
"""
import io, re

SRC = 'src/data-kamloops.js'
s = io.open(SRC, encoding='utf-8').read()

SEC = {}

SEC['zh'] = """<h3>🧳 你不是第一个到这里的人</h3>
<p>这座城市的移民史比它的市容要长。知道这一点，不是为了怀旧——而是因为你正在做的事，很多人已经做过，而且他们留下的东西今天还在。</p>
<p><b>1881–1885 年，一万五千多名华工来到加拿大修建太平洋铁路。</b>1882 年底，卑诗省境内九千名铁路工人里有六千五百人是华人；他们拿到的日薪只有白人工人的三分之一到一半，而且要从中自付伙食和工具，同时被派去做最危险的活——包括搬运硝化甘油。他们修的那条线，就从你脚下这条河谷穿过。</p>
<p>铁路完工后人留了下来。到 <b>1890 年</b>，本市华人已超过四百人，在第一大道以西形成了自己的街区。<b>Lombard 街的华人公墓</b>至迟在 1887 年已经启用，1979 年停止安葬，是加拿大现存最大、最古老的华人公墓之一，约一百二十五处墓穴，其中五十多处曾被起出——按广东的二次葬习俗，人下葬七到十年后由专人拾骨，运回原乡的家族墓地。<b>直到 1927 年，这里才第一次立起永久的墓碑。</b>那一年是一个分界：从"总有一天要回去"，变成"这里就是家"。</p>
<p>与此同时，国家层面的法律并不欢迎他们：1885 年开征人头税，1902 与 1903 年两度提高；1923 年 7 月 1 日起《华人移民法》几乎完全禁止华人入境，直到 1947 年才废止。2006 年 6 月 22 日，加拿大总理在国会为人头税正式道歉。这些是全国性的法律，不是本市的规定。</p>
<p><b>1942 年，约两万两千名日裔被强制迁离卑诗海岸</b>（各方统计在两万一千到两万三千之间，取决于统计口径），其中四分之三以上是加拿大公民。男性被送去修路：沿黄头公路至 Blue River 一线共设了十七处筑路营，最南的 Blue River 就在本市以北的北汤普森河谷。第一批人于 1942 年 2 月抵达，工程 1946 年 5 月结束。他们的时薪只有标准工资的四成多，还要扣除食宿，每个营地驻有四名持枪的骑警，未经许可不得离开。限制直到 1949 年 4 月 1 日才解除。1988 年 9 月 22 日，联邦政府签署赔偿协议。</p>
<p>这件事在本市留下了一个你今天可以走进去的地方：<b>Vernon 街 160 号的日裔加拿大文化中心，1994 年建成，建设资金的一部分正是来自 1988 年那笔赔偿。</b>它由 1970 年代中期成立的本地日裔协会运营，馆内的博物馆在 2026 年 2 月重新开放。</p>
<p>旁遮普与锡克家庭随林业进入卑诗内陆，尤其在 1950 年代之后；本市今天有锡克教谒师所和活跃的锡克文化协会。</p>
<p><b>还有一件事，值得每一个刚到的人知道。</b>1979 至 1982 年，大批东南亚难民（"船民"）抵达加拿大。1980 年 3 月，本市成立了越南与移民社区中心；当时由本地的<b>华人社团</b>承接了为期两年的接待工作。1982 年 1 月 20 日，机构正式注册，1985 年更名为今天的 <b>{CITY} Immigrant Services</b>。也就是说——<b>今天接待你的那个机构，是四十多年前为越南难民而建的，而帮忙把它建起来的，是一个世纪前修铁路的那批人的后代。</b></p>
<p>这条线没有断过。2015 至 2016 年，本市接待了七个叙利亚家庭，到 2016 年 6 月已有四十多人在此定居。2022 年俄乌战争爆发后，乌克兰人陆续到来——他们持联邦紧急通道入境，法律身份并非难民。</p>
<p>你在这份名单上。总有一天，也会轮到你去帮下一个刚到的人。</p>"""

SEC['en'] = """<h3>🧳 You are not the first to arrive here</h3>
<p>This city's immigration history is longer than its streetscape suggests. Knowing it is not nostalgia — what you are doing now, many people have already done, and what they left behind is still here.</p>
<p><b>Between 1881 and 1885, more than 15,000 Chinese labourers came to Canada to build the Canadian Pacific Railway.</b> By the end of 1882, of the 9,000 railway workers in British Columbia, 6,500 were Chinese. They were paid between a third and a half of what white workers earned, and out of that paid for their own food and gear, while being given the most dangerous work — including handling nitroglycerin. The line they built runs through this valley.</p>
<p>When the railway was finished, people stayed. By <b>1890</b> the Chinese population here was over 400, with its own quarter west of First Avenue. The <b>Chinese Cemetery on Lombard Street</b> was in use by 1887 and closed to burials in 1979; it is one of the largest and oldest intact Chinese cemeteries in Canada, with about 125 plots, over fifty of which were disinterred — Guangdong practice was secondary burial, the bones collected after seven to ten years and shipped home to the family plot. <b>Permanent headstones were first set here in 1927.</b> That year is a turning point you can read in stone: from "one day I will go back" to "this is where I live."</p>
<p>Meanwhile the country's laws said otherwise. A head tax on Chinese immigrants was imposed in 1885 and raised twice, in 1902 and 1903. From 1 July 1923 the Chinese Immigration Act barred Chinese immigration almost entirely, and was not repealed until 1947. On 22 June 2006 the Prime Minister apologised in Parliament for the head tax. These were national laws, not local ones.</p>
<p><b>In 1942 about 22,000 people of Japanese descent were forcibly uprooted from the BC coast</b> (published figures range from 21,000 to 23,000 depending on what is counted); more than three quarters of them were Canadian citizens. Men were sent to build roads: seventeen camps ran along the Yellowhead highway up to Blue River, the southernmost of them in the North Thompson valley north of this city. The first group arrived in February 1942 and the project closed in May 1946. They were paid a little over 40 per cent of the standard wage, with room and board deducted, four armed RCMP officers were posted at each camp, and no one could leave without permission. The restrictions were not lifted until 1 April 1949. On 22 September 1988 the federal government signed the redress agreement.</p>
<p>That history left something here you can walk into today: <b>the Japanese Canadian cultural centre at 160 Vernon Avenue was built in 1994, funded in part by the money from that 1988 redress.</b> It is run by the local association formed in the mid-1970s, and its museum reopened in February 2026.</p>
<p>Punjabi and Sikh families settled across the BC interior with the forest industry, particularly after the 1950s; the city has a gurdwara and an active Sikh cultural society today.</p>
<p><b>And one more thing worth knowing on your first week.</b> Between 1979 and 1982 large numbers of Southeast Asian refugees — the "boat people" — arrived in Canada. In March 1980 a Vietnamese and Immigrants' Community Centre opened here, and the local <b>Chinese associations</b> carried the reception work under a two-year mandate. On 20 January 1982 the organisation was incorporated, and in 1985 it took the name it still has: <b>{CITY} Immigrant Services</b>. Which means the agency that will help you today was founded for Vietnamese refugees over forty years ago — and the people who helped build it were the descendants of the men who built the railway a century before that.</p>
<p>The thread has never broken. Seven Syrian families were resettled here in 2015 and 2016, more than forty people by that June. Ukrainians began arriving after 2022, under a federal emergency travel programme rather than as refugees.</p>
<p>You are on this list. One day it will be your turn to help whoever arrives next.</p>"""

SEC['fr'] = """<h3>🧳 Vous n'etes pas la premiere personne a arriver ici</h3>
<p>L'histoire de l'immigration de cette ville est plus longue que ne le laisse croire son paysage urbain. La connaitre n'est pas de la nostalgie : ce que vous faites en ce moment, beaucoup l'ont deja fait, et ce qu'ils ont laisse est toujours la.</p>
<p><b>Entre 1881 et 1885, plus de 15 000 travailleurs chinois sont venus au Canada construire le chemin de fer Canadien Pacifique.</b> A la fin de 1882, sur les 9 000 ouvriers du rail en Colombie-Britannique, 6 500 etaient chinois. Ils recevaient entre le tiers et la moitie du salaire des ouvriers blancs, devaient payer la-dessus leur nourriture et leur equipement, et se voyaient confier les taches les plus dangereuses, dont la manipulation de la nitroglycerine. La voie qu'ils ont batie traverse cette vallee.</p>
<p>Le chemin de fer acheve, des gens sont restes. Des <b>1890</b>, la population chinoise depassait ici 400 personnes, avec son propre quartier a l'ouest de la Premiere Avenue. Le <b>cimetiere chinois de la rue Lombard</b> etait en usage des 1887 et a ferme aux inhumations en 1979; c'est l'un des plus grands et des plus anciens cimetieres chinois intacts au Canada, avec environ 125 emplacements, dont plus de cinquante ont ete exhumes — la coutume cantonaise voulait une seconde sepulture, les ossements recueillis apres sept a dix ans et renvoyes au caveau familial. <b>Les premieres pierres tombales permanentes y ont ete posees en 1927.</b> Cette annee-la marque un basculement lisible dans la pierre : de « un jour je rentrerai » a « c'est ici que je vis ».</p>
<p>Pendant ce temps, les lois du pays disaient le contraire. Une taxe d'entree fut imposee aux immigrants chinois en 1885, puis relevee deux fois, en 1902 et en 1903. A partir du 1er juillet 1923, la Loi de l'immigration chinoise a interdit presque toute immigration chinoise, et ne fut abrogee qu'en 1947. Le 22 juin 2006, le premier ministre a presente des excuses au Parlement pour cette taxe. Ce sont des lois nationales, non des reglements locaux.</p>
<p><b>En 1942, environ 22 000 personnes d'origine japonaise ont ete deracinees de force de la cote de la Colombie-Britannique</b> (les chiffres publies vont de 21 000 a 23 000 selon ce que l'on compte); plus des trois quarts etaient citoyens canadiens. Les hommes ont ete envoyes construire des routes : dix-sept camps s'echelonnaient le long de la route Yellowhead jusqu'a Blue River, le plus au sud dans la vallee de la Thompson Nord, au nord de cette ville. Le premier groupe est arrive en fevrier 1942 et le chantier a ferme en mai 1946. Ils touchaient un peu plus de 40 pour cent du salaire courant, gite et couvert deduits, quatre agents de la GRC armes etaient postes a chaque camp, et nul ne pouvait partir sans autorisation. Les restrictions n'ont ete levees que le 1er avril 1949. Le 22 septembre 1988, le gouvernement federal a signe l'entente de reparation.</p>
<p>Cette histoire a laisse ici un lieu ou vous pouvez entrer aujourd'hui : <b>le centre culturel nippo-canadien du 160, avenue Vernon a ete construit en 1994, finance en partie par l'argent de cette reparation de 1988.</b> Il est gere par l'association locale formee au milieu des annees 1970, et son musee a rouvert en fevrier 2026.</p>
<p>Des familles pendjabies et sikhes se sont etablies dans tout l'interieur de la province avec l'industrie forestiere, surtout apres les annees 1950; la ville compte aujourd'hui un gurdwara et une societe culturelle sikhe active.</p>
<p><b>Et une derniere chose, a savoir des votre premiere semaine.</b> Entre 1979 et 1982, un grand nombre de refugies d'Asie du Sud-Est — les « boat people » — sont arrives au Canada. En mars 1980, un centre communautaire vietnamien et pour immigrants a ouvert ici, et ce sont les <b>associations chinoises</b> locales qui ont porte le travail d'accueil, sous un mandat de deux ans. Le 20 janvier 1982, l'organisme a ete constitue, et en 1985 il a pris le nom qu'il porte encore : <b>{CITY} Immigrant Services</b>. Autrement dit, l'organisme qui vous aidera aujourd'hui a ete fonde il y a plus de quarante ans pour des refugies vietnamiens — et ceux qui ont aide a le batir etaient les descendants des hommes qui avaient bati le chemin de fer un siecle plus tot.</p>
<p>Le fil ne s'est jamais rompu. Sept familles syriennes ont ete reinstallees ici en 2015 et 2016, plus de quarante personnes des le mois de juin. Des Ukrainiens arrivent depuis 2022, par un programme federal de voyage d'urgence et non comme refugies.</p>
<p>Vous etes sur cette liste. Un jour, ce sera votre tour d'aider la prochaine personne qui arrive.</p>"""

SEC['es'] = """<h3>🧳 Usted no es la primera persona en llegar aqui</h3>
<p>La historia migratoria de esta ciudad es mas larga de lo que sugiere su aspecto. Conocerla no es nostalgia: lo que usted esta haciendo ahora ya lo hicieron muchos, y lo que dejaron sigue aqui.</p>
<p><b>Entre 1881 y 1885, mas de 15.000 trabajadores chinos llegaron a Canada para construir el ferrocarril Canadian Pacific.</b> A finales de 1882, de los 9.000 obreros del ferrocarril en Columbia Britanica, 6.500 eran chinos. Cobraban entre un tercio y la mitad de lo que ganaban los obreros blancos, y de ahi debian pagar su propia comida y herramientas, mientras se les asignaban las tareas mas peligrosas, incluida la manipulacion de nitroglicerina. La via que construyeron atraviesa este valle.</p>
<p>Terminado el ferrocarril, hubo quien se quedo. Hacia <b>1890</b> la poblacion china aqui superaba las 400 personas, con su propio barrio al oeste de la Primera Avenida. El <b>cementerio chino de la calle Lombard</b> ya estaba en uso en 1887 y cerro a los entierros en 1979; es uno de los cementerios chinos intactos mas grandes y antiguos de Canada, con unas 125 sepulturas, mas de cincuenta de ellas exhumadas — la costumbre cantonesa era el entierro secundario: los huesos se recogian a los siete o diez anos y se enviaban al panteon familiar. <b>Las primeras lapidas permanentes se colocaron aqui en 1927.</b> Ese ano marca un cambio que se puede leer en la piedra: de "algun dia volvere" a "aqui es donde vivo".</p>
<p>Mientras tanto, las leyes del pais decian lo contrario. En 1885 se impuso un impuesto de entrada a los inmigrantes chinos, elevado dos veces, en 1902 y 1903. Desde el 1 de julio de 1923 la Ley de Inmigracion China prohibio casi por completo la inmigracion china, y no se derogo hasta 1947. El 22 de junio de 2006 el primer ministro pidio perdon en el Parlamento por ese impuesto. Fueron leyes nacionales, no normas locales.</p>
<p><b>En 1942 unas 22.000 personas de origen japones fueron desarraigadas por la fuerza de la costa de Columbia Britanica</b> (las cifras publicadas van de 21.000 a 23.000 segun lo que se cuente); mas de tres cuartas partes eran ciudadanos canadienses. A los hombres se los envio a construir carreteras: diecisiete campamentos se extendian por la carretera Yellowhead hasta Blue River, el mas meridional en el valle del Thompson Norte, al norte de esta ciudad. El primer grupo llego en febrero de 1942 y el proyecto cerro en mayo de 1946. Cobraban algo mas del 40 por ciento del salario habitual, con alojamiento y comida descontados, cuatro agentes armados de la RCMP estaban destinados en cada campamento, y nadie podia irse sin permiso. Las restricciones no se levantaron hasta el 1 de abril de 1949. El 22 de septiembre de 1988 el gobierno federal firmo el acuerdo de reparacion.</p>
<p>Esa historia dejo aqui un lugar al que usted puede entrar hoy: <b>el centro cultural japones-canadiense del 160 de la avenida Vernon se construyo en 1994, financiado en parte con el dinero de aquella reparacion de 1988.</b> Lo gestiona la asociacion local formada a mediados de los anos setenta, y su museo reabrio en febrero de 2026.</p>
<p>Familias punyabies y sijs se establecieron por todo el interior de la provincia con la industria forestal, sobre todo despues de los anos cincuenta; la ciudad tiene hoy un gurdwara y una sociedad cultural sij activa.</p>
<p><b>Y una cosa mas, que conviene saber en su primera semana.</b> Entre 1979 y 1982 llegaron a Canada numerosos refugiados del sudeste asiatico, la gente de los barcos. En marzo de 1980 abrio aqui un centro comunitario vietnamita y de inmigrantes, y fueron las <b>asociaciones chinas</b> locales las que sostuvieron el trabajo de acogida, con un mandato de dos anos. El 20 de enero de 1982 la organizacion se constituyo formalmente, y en 1985 tomo el nombre que todavia lleva: <b>{CITY} Immigrant Services</b>. Es decir: la agencia que hoy le ayudara se fundo hace mas de cuarenta anos para refugiados vietnamitas, y quienes ayudaron a levantarla eran los descendientes de los hombres que habian levantado el ferrocarril un siglo antes.</p>
<p>El hilo nunca se ha roto. Siete familias sirias fueron reasentadas aqui en 2015 y 2016, mas de cuarenta personas para junio de ese ano. Los ucranianos empezaron a llegar despues de 2022, por un programa federal de viaje de emergencia y no como refugiados.</p>
<p>Usted esta en esta lista. Algun dia le tocara ayudar a quien llegue despues.</p>"""

SEC['ko'] = """<h3>🧳 당신이 여기 처음 도착한 사람은 아닙니다</h3>
<p>이 도시의 이민 역사는 거리 풍경이 보여주는 것보다 깁니다. 이것을 아는 일은 향수가 아닙니다. 지금 당신이 하고 있는 일을 이미 많은 사람이 했고, 그들이 남긴 것이 지금도 여기 있습니다.</p>
<p><b>1881년부터 1885년까지 1만 5천 명이 넘는 중국인 노동자가 캐나다 태평양 철도를 놓기 위해 왔습니다.</b> 1882년 말 브리티시컬럼비아의 철도 노동자 9천 명 중 6천 5백 명이 중국인이었습니다. 이들은 백인 노동자가 받던 임금의 3분의 1에서 절반을 받았고, 그 돈에서 식비와 장비값을 스스로 냈으며, 니트로글리세린을 다루는 일을 포함해 가장 위험한 작업에 배치되었습니다. 그들이 놓은 선로가 이 계곡을 지나갑니다.</p>
<p>철도가 끝나자 사람들은 남았습니다. <b>1890년</b>에 이곳 중국인 인구는 400명이 넘었고 퍼스트 애비뉴 서쪽에 자기들의 구역이 있었습니다. <b>롬바드 스트리트의 중국인 묘지</b>는 늦어도 1887년에 사용되고 있었고 1979년에 매장이 끝났습니다. 캐나다에 온전히 남은 가장 크고 오래된 중국인 묘지 중 하나로 약 125기의 묘가 있고 그중 쉰 곳 넘게 이장되었습니다 — 광둥의 관습은 이차장이어서, 7년에서 10년 뒤 유골을 수습해 고향의 가족 묘로 보냈습니다. <b>영구적인 비석이 이곳에 처음 세워진 것은 1927년입니다.</b> 그해는 돌에 새겨진 전환점입니다. "언젠가 돌아간다"에서 "여기가 사는 곳이다"로 바뀐 것입니다.</p>
<p>한편 국가의 법은 반대로 말하고 있었습니다. 1885년 중국인 이민자에게 인두세가 부과되었고 1902년과 1903년 두 차례 인상되었습니다. 1923년 7월 1일부터 중국인 이민법이 중국인 이민을 사실상 전면 금지했고, 1947년에야 폐지되었습니다. 2006년 6월 22일 총리가 의회에서 인두세에 대해 사과했습니다. 이는 전국적인 법률이지 이 도시의 규정이 아니었습니다.</p>
<p><b>1942년 약 2만 2천 명의 일본계 사람들이 BC 해안에서 강제로 쫓겨났습니다</b>(공개된 수치는 무엇을 세느냐에 따라 2만 1천에서 2만 3천 사이입니다). 그중 4분의 3 이상이 캐나다 시민이었습니다. 남성들은 도로 건설에 보내졌습니다. 옐로헤드 고속도로를 따라 블루리버까지 열일곱 개의 캠프가 있었고, 그중 가장 남쪽이 이 도시 북쪽 노스톰프슨 계곡에 있었습니다. 첫 무리가 1942년 2월에 도착했고 공사는 1946년 5월에 끝났습니다. 이들은 표준 임금의 40퍼센트 남짓을 받았고 거기서 숙식비가 공제되었으며, 각 캠프에는 무장한 기마경찰 네 명이 배치되어 허가 없이는 떠날 수 없었습니다. 제한은 1949년 4월 1일에야 풀렸습니다. 1988년 9월 22일 연방정부가 배상 협정에 서명했습니다.</p>
<p>그 역사는 오늘 당신이 걸어 들어갈 수 있는 장소를 이곳에 남겼습니다. <b>버논 애비뉴 160번지의 일본계 캐나다인 문화센터는 1994년에 지어졌고, 건축비의 일부가 바로 1988년 그 배상금에서 나왔습니다.</b> 1970년대 중반에 만들어진 지역 협회가 운영하며, 안의 박물관은 2026년 2월에 다시 열었습니다.</p>
<p>펀자브와 시크 가정들은 임업을 따라 특히 1950년대 이후 BC 내륙 전역에 정착했습니다. 이 도시에는 오늘날 구르드와라와 활발한 시크 문화협회가 있습니다.</p>
<p><b>그리고 첫 주에 알아둘 만한 것이 하나 더 있습니다.</b> 1979년부터 1982년까지 많은 동남아시아 난민, 이른바 보트피플이 캐나다에 도착했습니다. 1980년 3월 이곳에 베트남·이민자 커뮤니티 센터가 문을 열었고, 2년 임기로 그 환대 업무를 감당한 것은 지역의 <b>중국인 단체들</b>이었습니다. 1982년 1월 20일 이 단체가 정식 등록되었고, 1985년에 지금의 이름 <b>{CITY} Immigrant Services</b>가 되었습니다. 다시 말해, 오늘 당신을 돕게 될 그 기관은 사십여 년 전 베트남 난민을 위해 세워졌고, 그것을 세우는 데 힘을 보탠 사람들은 그보다 한 세기 전에 철도를 놓은 이들의 후손이었습니다.</p>
<p>이 실은 한 번도 끊긴 적이 없습니다. 2015년과 2016년에 시리아 가족 일곱 가구가 이곳에 정착했고, 그해 6월까지 마흔 명이 넘었습니다. 우크라이나 사람들은 2022년 이후 도착하기 시작했는데, 난민이 아니라 연방 긴급 입국 프로그램을 통해서였습니다.</p>
<p>당신도 이 명단에 있습니다. 언젠가는 다음에 도착하는 사람을 도울 차례가 올 것입니다.</p>"""

SEC['ja'] = """<h3>🧳 ここに着いたのは、あなたが最初ではありません</h3>
<p>この街の移民の歴史は、街並みが思わせるよりずっと長いものです。それを知るのは懐古のためではありません。いまあなたがしていることを、すでに多くの人がしてきて、その人たちが残したものが今も here にあるからです。</p>
<p><b>1881年から1885年にかけて、1万5千人を超える中国人労働者がカナダ太平洋鉄道の建設のために渡ってきました。</b>1882年末、ブリティッシュコロンビア州の鉄道労働者9千人のうち6千5百人が中国人でした。彼らの賃金は白人労働者の3分の1から半分で、そこから食費と道具代を自分で払い、ニトログリセリンの取り扱いを含む最も危険な作業に回されました。彼らが敷いた線路が、この谷を通っています。</p>
<p>鉄道が完成しても、人は残りました。<b>1890年</b>にはこの街の中国人は400人を超え、ファースト・アベニューの西に自分たちの街区を持っていました。<b>ロンバード通りの中国人墓地</b>は遅くとも1887年には使われており、1979年に埋葬を終えました。カナダに完全な形で残る中国人墓地としては最大級かつ最古級で、約125の墓所があり、そのうち50以上が改葬されています — 広東の習慣は二次葬で、7年から10年の後に遺骨を集め、故郷の一族の墓へ送り返しました。<b>ここに恒久的な墓石が初めて立てられたのは1927年です。</b>その年は、石に刻まれた転換点です。「いつか帰る」から「ここが住む場所だ」へ。</p>
<p>その間、国の法律は逆のことを言っていました。1885年に中国人移民への人頭税が課され、1902年と1903年の二度引き上げられました。1923年7月1日からは中国人移民法が中国人の入国をほぼ全面的に禁じ、廃止は1947年でした。2006年6月22日、首相が議会で人頭税について謝罪しました。これらは国の法律であって、この街の規則ではありません。</p>
<p><b>1942年、約2万2千人の日系の人々がBC沿岸から強制的に立ち退かされました</b>（公表されている数字は、何を数えるかによって2万1千から2万3千の間です）。その4分の3以上がカナダ市民でした。男性は道路建設に送られました。イエローヘッド街道沿いにブルーリバーまで17の作業キャンプが並び、その最も南のものはこの街の北、ノース・トンプソン渓谷にありました。第一陣は1942年2月に到着し、工事は1946年5月に終わりました。賃金は標準の4割強で、そこから食住費が差し引かれ、各キャンプには武装した騎馬警察官が4名配置され、許可なく離れることはできませんでした。制限が解かれたのは1949年4月1日です。1988年9月22日、連邦政府が補償の協定に署名しました。</p>
<p>その歴史は、今日あなたが入っていける場所をこの街に残しました。<b>バーノン通り160番地の日系カナダ人文化センターは1994年に建てられ、その建設費の一部は1988年のあの補償から出ています。</b>1970年代半ばにできた地元の協会が運営しており、館内の博物館は2026年2月に再開しました。</p>
<p>パンジャブとシークの家族は林業とともに、とくに1950年代以降にBC内陸各地に定着しました。この街には今日、グルドワラと活動的なシーク文化協会があります。</p>
<p><b>そしてもう一つ、最初の一週間に知っておく価値のあることがあります。</b>1979年から1982年にかけて、多数の東南アジア難民、いわゆるボートピープルがカナダに到着しました。1980年3月、この街にベトナム人・移民のためのコミュニティセンターが開き、その受け入れの仕事を2年間の委託で担ったのは、地元の<b>華人団体</b>でした。1982年1月20日にこの団体は正式に法人化され、1985年に今の名前 <b>{CITY} Immigrant Services</b> になりました。つまり、今日あなたを助けるその機関は、40年余り前にベトナム難民のために作られたものであり、それを作るのを手伝ったのは、その一世紀前に鉄道を敷いた人々の子孫だったのです。</p>
<p>この糸は一度も切れていません。2015年から2016年にシリアの7家族がここに定住し、その年の6月までに40人を超えました。ウクライナの人々は2022年以降に到着しはじめましたが、難民としてではなく連邦の緊急渡航プログラムを通じてでした。</p>
<p>あなたもこの名簿に載っています。いつか、次に着いた人を助ける番が回ってきます。</p>"""

# One typo guard: an English word slipped into the Japanese draft above.
SEC['ja'] = SEC['ja'].replace('今も here にある', '今もここにある')

count = 0
for lang, block in SEC.items():
    # anchor: the 🧡 land-and-history heading in this language's guideCity,
    # then the next <h3> after it — the immigration history belongs directly
    # after the history of the land, before the practical sections resume.
    key = 'UI.%s.guideCity=`' % lang
    start = s.index(key)
    # the Japanese block closes with `; on the same line as its last tag,
    # the other five with a blank line before it — find the terminator
    # rather than assuming either shape
    end = s.index('`;', start)
    body = s[start:end]
    h = body.index('<h3>🧡')
    nxt = body.index('<h3>', h + 4)
    body = body[:nxt] + block + '\n' + body[nxt:]
    s = s[:start] + body + s[end:]
    count += 1

io.open(SRC, 'w', encoding='utf-8').write(s)
print('inserted the immigration-history section into %d languages' % count)
