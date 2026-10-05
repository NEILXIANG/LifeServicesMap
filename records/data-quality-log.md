# 数据质量审查日志

> 数据本身的问题清单——**准确、及时、覆盖**是产品信任的根本。**只记 Kamloops**（线上城市）；草稿城市的问题在
> `docs/reports/<城市>审核清单.md`（由 `scripts/review_checklist.py` 生成）。
> 2026-10-04 整理：删除了"示例"一节（虚构的记录不放在真实日志里，L-003）；待补充改为真实缺口；
> 9 月 16 日以前月度巡检的"0 OK / 0 DEAD"是计数错误（grep 匹配不到带缩进的行），**不是真实结果**，已于 09-16 修复。

---

## 待修复（具体地点 / 字段）

| ID | 分类 | 问题描述 | 来源 | 优先级 | 状态 | 修复日期 |
|---|---|---|---|---|---|---|
| `success-formula` | tutor | Success Formula 的地址待核实 | 2026-09-24 学校与托儿补全 | P2 | 待修 | — |
| 救世军食物银行 | foodbank | 营业时间待按官网核实 | 2026-09-24 学校与托儿补全 | P1 | 待修 | — |

> ID 用地点前 5 字符或前 8 字符 ID 简称，例如 `rbc001` 指 `Royal Bank` 类条目第一项。

---

## 待补充（已知缺哪些地点 / 分类）

| 分类 / 区域 | 缺什么 | 优先级 | 状态 |
|---|---|---|---|
| `school` | 5 所私立学校（省 K-12 数据里有、地图上没有） | P2 | 待补 |
| `daycare` | 搜 `montessori school` 只出 1 家，实有 11 家（整名匹配问题，搜索层修复） | P1 | 待修 |
| 2SLGBTQ+ | 本地支持资源（2026-09-21 全面检查列为缺口） | P1 | 待补 |
| Brocklehurst | 没有超市、药房、医疗点（区域覆盖偏少） | P2 | 待补 |
| `religious` | 缺印度教、东正教、非英语教会（2026-09-10 从零自查） | P2 | 待补 |
| 办事卡 rights | 歧视理由列表漏了性别认同、家庭状况、原住民身份（2026-09-21） | P1 | 待核实 |
| `daycare`（80 条，省数据导入） | ~~缺网址和语言、年龄、减费信息~~ **2026-10-04 已处理**：用 `bc_childcare.py --city kamloops --enrich` 对照当天的省数据，80 条全部匹配，id 和本地那句转介不变；备注补上"参加托儿费减免计划（CCFRI）"（90 家全部参加），2 家补上年龄或语言（省数据里这两项对大多数机构是空的）。**网址那条是误报**：省数据里 Kamloops 90 家的 WEBSITE 全是空的，09-24 的导入说得对 | P1 | 已完成 2026-10-04 |
| 公交 | 仓库里只记了 BC Transit 的运营方编号（`operatorIds=46`，`p11_patch.py` 说明里），没有完整的 GTFS 下载地址；下次重导前写进 `cities/kamloops/import/config.json` | P2 | 待补 |
| 办事卡 eldercare | 来源指向非政府机构 Interior Community Services；Kelowna 用的是 Interior Health 的 Home and Community Care 页面，两城都适用——下次核实办事卡时考虑统一 | P2 | 待核实 |

---

## 2026-10-04 独立复核（官网对照）之后：要打电话或开浏览器核实的

Kamloops 全部 307 条非政府数据记录第一次做了独立复核（Kelowna 的做法；结果在 `cities/kamloops/import/verification.json`）：
212 条确认、57 条改正、35 条官网无法读取（多为商家网站拦截自动读取，或根本没有官网）。安全相关的已用浏览器补核。
下面这些仍需一个人打电话或用浏览器确认（地址、电话、营业时间）：

| 分类 | 地点 |
|---|---|
| apt | The View Apartments |
| asian | Cheng Kwong 長江超市 |
| asian | Day to Day Grocery |
| asian | FraserCart Indian Store |
| autorepair | Stay Tuned Auto Repair |
| bank | Beem Credit Union (Valleyview) |
| bank | TD Bank (North Shore) |
| bank | TD Bank (Notre Dame Dr) |
| bank | TD Canada Trust (Victoria St) |
| conv | 7-Eleven (Tranquille Rd) |
| conv | Tranquille Market |
| gas | Co-op Valleyview Gas Bar |
| gas | Petro-Canada (10th Ave) |
| gas | Petro-Canada (Powwow Trail) |
| gas | Petro-Canada (Sydney Ave) |
| grocery | FreshCo (Columbia) |
| grocery | Safeway (Fortune Dr) |
| gym | Anytime Fitness |
| gym | Planet Fitness |
| hardware | Canadian Tire |
| hardware | Kamloops Home Hardware |
| hardware | RONA Kamloops |
| mall | Columbia Place |
| mall | Columbia Square |
| post | Canada Post |
| post | Canada Post (Dalhousie Dr) |
| post | Canada Post (North Shore) |
| religious | Gurdwara Sahib Society |
| religious | Kamloops Sikh Cultural Society |
| restaurant | Oriental Express |
| restaurant | Victoria Oriental |
| secondhand | Lys's Thrift and Vintage |
| taxi | Yellow Cabs Kamloops |
| trail | Airport Trail |
| tutor | The Success Formula Tutoring |

## 待核实（`v` 字段超 6 个月）

`export-open.py` 可生成过期待核实清单。每月跑一次：

```bash
python3 export-open.py --stale-threshold 180 > data/stale-2026-09.md
```

| ID | 名称 | 上次核实 | 优先级 |
|---|---|---|---|
| — | — | — | — |

---

## 注释更新（`note` 字段误导或过时）

| ID | 问题 | 建议改法 | 状态 |
|---|---|---|---|
| — | — | — | 待改 / 已改 |

---

### 2026-09-05 · 深链巡检（`check-links.py`）

**执行**：`python3 check-links.py > records/check-links-2026-09-05.log`

**结果**：BLOCKED 24 · DEAD 11 · MOVED 29 · OK 86
（BLOCKED = 网络层超时/CAPTCHA，非真死链；MOVED = 301/302 重定向到新 URL；
DEAD = host 不解析或 HTTP 404 — 真正需要 follow-up）

**11 个 DEAD**（按原报告顺序）：

| 名称 | URL | 状态 |
|---|---|---|
| Interior Savings Credit Union | https://www.interiorsavings.com | DEAD |
| Yellow Cabs Kamloops | yellowcabskamloops.com | DEAD (DNS) |
| Stay Tuned Auto Repair | https://www.staytunedauto.ca/ | DEAD (DNS) |
| Lil' Monkey's Treehouse | https://www.lilmonkeystreehouse.com/ | DEAD (DNS) |
| Scotiabank(Victoria St) | https://www.scotiabank.com/ca/en/... | DEAD (404) |

**29 个 MOVED** 全部有 `→` 指向正确新 URL，可批量替换。已在 records/check-links-2026-09-05.log 完整保留。

**下一步**：
1. 把 11 个 DEAD 中能电话核实"真的关门了"的改成 `null` 或加 `note: "已停业"` 标记
2. 29 个 MOVED 用脚本批量替换 URL
3. 下次跑：2026-10-05（每月一次）

## 自查清单（每两周走一遍）

> 把所有筛选组合走一遍，记下"看着别扭"的地方。

- [ ] 全部分类（共 7 组 × 若干子项）每个至少打开看 3 个 marker
- [ ] 全部区域（RI）每个至少切一次
- [ ] 全部 5 种语言分别打开，对比「同一记录的标题 / 描述」是否一致
- [ ] 搜索 10 个高频关键词（walmart / bank / clinic / 学校 / …）看搜索是否合理
- [ ] 公交面板：所有路线至少看 2 个 stop 的 popup
- [ ] 收藏功能：加 5 个 → 删 2 个 → 重新打开页面看是否还在
- [ ] URL 分享：选好筛选 → 复制 URL → 隐身窗口打开看是否还原

---

## 自查记录

### 2026-09-04 · 首次代码层自查（`validate.py`；历史记录，当时的文件名和路径已变）

**执行**：本地 `python3 validate.py Kamloops生活服务地图.html`

**结果**：

```
places=249 categories=45 regions=7 routes=14  size=654KB
5 warning(s):
  ~ 'Costco Wholesale' 和 '⭐ Costco Gas Station' 同地址同网址 — 是否真的两个地点？
  ~ 14 个地点坐标只到 3 位小数（~110m 误差）：College Manor Apartments / Stetson Place / Bonnie Lee / Kamloops Buddhist Temple / Ayesha Mosque / Kami Cabs …
  ~ 5 个分类只有 1 个条目：legal / police / schoolbus / tutor / vet — 真的稀缺还是没补全？
  ~ 区域覆盖不均：ws=7, ot=12 vs 最高 66（北 Thompson 区域严重欠缺）
  ~ 150 个网站中有 33 个是深链（最容易腐烂）
all invariants hold
```

**评估**：5 条 warning 全部是**数据/补全类**，不是新引入问题（之前审计中已识别）。但**"区域覆盖不均"是结构性短板**——可以放入待优化清单。

**已转化为行动**：

| warning | 优先级 | 行动 |
|---|---|---|
| ws / ot 区域覆盖严重欠缺 | P1 | 抽一天专门补全这 2 个区域（北 Thompson 区域 12 条 vs 南 Kamloops 66 条）|
| 5 个单条目分类 | P2 | 核实是"真稀缺"还是"漏录入"——打电话 / 搜本地服务清单 |
| 33 个深链 | P1 | 月底跑一次 `check-links.py`（联网机器），把死链更新或删除 |
| 14 个低精度坐标 | P2 | 用户体感差异不大；除非有人反馈"位置偏差"，暂缓 |
| Costco 同地址 | P3 | 实地确认两个场所（是否真有 gas station 单独位置）|

- 2026-09-04 第一次走完，发现 3 处：
  1. 公交 Route 7 显示有问题（停站文字过大）
  2. 中文版「超市」分类标题被截断
  3. 收藏导出 import 的提示文字英文版有 typo

---

## 来源记录（用户报错用）

每次用户报错，按以下格式记一行（去标识化）：

```
YYYY-MM-DD | 渠道 | 地域 | 反馈内容摘要 | 已处理？
例：2026-09-04 | 微信群 | Kamloops | "RBC 那个地址不对，搬了" | 是，已修正
```
### 2026-09-05 · 月度巡检

- stale: 0 POI over 180d. nothing to do this cycle.
- 深链: 0 OK, 0 MOVED, 0 DEAD, 1 BLOCKED
- 完整 log: records/check-links-2026-09-05.log

### 2026-09-07 · 月度巡检

- stale: 0 POI over 180d. nothing to do this cycle.
- 深链: 0 OK, 0 MOVED, 0 DEAD, 1 BLOCKED
- 完整 log: records/check-links-2026-09-07.log

### 2026-09-16 · 月度巡检

- stale: 0 POI over 180d. nothing to do this cycle.
- 深链: 0 OK, 0 MOVED, 0 DEAD, 56 BLOCKED（共 56 条）
- 完整 log: records/check-links-2026-09-16.log（计数取自同名 .json）

### 2026-09-16 · 月度巡检

- stale: 0 POI over 180d. nothing to do this cycle.
- 深链: 46 OK, 2 MOVED, 2 DEAD, 6 BLOCKED（共 56 条）
- 完整 log: records/check-links-2026-09-16.log（计数取自同名 .json）

### 2026-09-16 · 月度巡检

- stale: 0 POI over 180d. nothing to do this cycle.
- 深链: 36 OK, 2 MOVED, 2 DEAD, 16 BLOCKED（共 56 条）
- 完整 log: records/check-links-2026-09-16.log（计数取自同名 .json）

### 2026-09-16 · 月度巡检

- stale: 0 POI over 180d. nothing to do this cycle.
- 深链: 46 OK, 2 MOVED, 2 DEAD, 6 BLOCKED（共 56 条）
- 完整 log: records/check-links-2026-09-16.log（计数取自同名 .json）

### 2026-09-16 · 深链巡检结果处理

月度巡检修好后第一次拿到真实数据（46 OK / 2 MOVED / 2 DEAD / 6 BLOCKED，共 56 条深链）。

**已改（3 条）**

| 地点 | 原因 | 新地址 |
|---|---|---|
| Scotiabank (Victoria St) | 原通用定位器页 404 | `https://locator.scotiabank.com/`（官网现行定位器，同类替换） |
| Windsor Plywood | `.com` 永久跳转到 `.ca` | `https://www.windsorplywood.ca/pages/kamloops`（跳转带的 `?shpxid=` 跟踪参数未写入） |
| KAFS Mini Storage | 官网改版，服务器自身跳转 | `https://www.kafs.ca/program/mini-storage` |

三条都只改了 `w`，**`v` 保持原值**——本次只核了链接可达性，没有重新核实地址、电话、营业时间，改 `v` 等于虚报核实范围。

**查证后确认不用改（1 条）**

- **The Salvation Army Community Services** — 报 HTTP 404，但实际抓取该页面内容完整（344 Poplar Street，周二至周五 10:00–13:00，急难食物包、食物券、公交票、眼镜转介等）。这是**软 404**：服务器返回 404 状态码却照常渲染页面。对真人完全可用，不动。下次巡检它还会报 DEAD，属已知情况。

**已知的反爬拦截，非故障（6 条，不需处理）**

`theseed.ca`（2 条）、`www.londondrugs.com`、`www.saveonfoods.com` 返回 403；
`www.canada.ca`（Service Canada）读超时。
这些站点对非浏览器请求设了拦截，真人访问正常。**每月巡检会重复报出，不是待办。**

**`www.kelsongroup.com` 的 11 条：已确认全部正常，之前是我们自己造成的。**
同一家公司有 11 个公寓地点，早期无节流的版本把它们并发打过去，还在二十分钟内
连跑四轮，被 IP 级临时限流，11 条全报 429——报告里看起来像"这家网站挂了"。
加上按域名串行 + 3 秒间隔、并等限流窗口过去后单独复查（`--host kelsongroup`），
结果 10 OK / 1 BLOCKED，那 1 条还是本轮第一个请求撞上残留窗口，随后即恢复。
**结论：11 条链接全部有效，无需改动。** 教训是巡检本身必须对小站有礼貌。

**本轮同时修掉的两个巡检自身的缺陷**（详见 `docs/archive/reports/2026-09-16-脚本全面分析与优化.md`）

1. HEAD 请求失败时直接下结论 —— 对 HEAD 回 404 的站点（Wix/Shopify/部分 WordPress 常见）误判为 DEAD。已改为任何 HEAD 失败都用 GET 复核。
2. 没有按域名节流 —— 56 条深链集中在 27 个域名，其中 `kamloops.ca` 14 条、`kelsongroup.com` 11 条，6 个并发一起打过去把对方打到限流，报告里看起来像"这家网站挂了"。已改为同域名串行、间隔 1.5 秒，并发只跨域名。

### 2026-09-21 · 按 TNRL 回复核实补充，并顺查同类遗漏

起因：TNRL 回信指出漏了 Aberdeen Mall 分馆，且各分馆在官网有独立页面。
范围：先落实她说的，再用同样的眼光查"这次写过信的 30 家机构"——他们正在看这份指南。

**图书馆（她指出的）**
- **新增 Aberdeen Tiny Library**（1320 Trans-Canada Hwy，商场内；778-471-2100）。2023 年开馆，TNRL 最小的分馆（352 平方英尺），也是 Kamloops 自 1974 年以来第一家新增图书馆。周一闭馆，周二三 12–4，周四五 10–5，周六 10–4，周日 12–4。预约的书在商场营业时间内可从门口取书柜自取。坐标用商场本身坐标（同一栋楼），与 Aberdeen Mall 互标 `sameComplex`。
- Kamloops Library、North Kamloops Library：地址、电话、**7 天营业时间逐天对照官网，完全一致**。只把 `w` 从 `tnrl.ca` 首页改为各自分馆页。因为这次确实全项核过，`v` 如实更新为 2026-09。
- TNRL 其余 10 个分馆都在 Kamloops 城区以外（Ashcroft、Barriere、Chase、Clearwater、Logan Lake、Merritt、Savona 等），不在本图范围。

**学校（同样的问题，而且更严重）**
- 10 所小学原来全部链到学区首页 `www.sd73.bc.ca`——正是她说的"每个地点有自己的页面"。
- SD73 已把所有学校迁到主站路径：旧子域名 `<代号>.sd73.bc.ca` 一律 **302 跳转**到 `www.sd73.bc.ca/<代号>`。15 所学校全部改为现行地址，每个代号都有服务器跳转或学区官网搜索结果为证，没有按校名推测。
- **其中 3 所中学原来的子域名本身就是错的**：NorKam 写成 `norkam.`（实为 `nkss`）、Westsyde 写成 `westsyde.`（实为 `wss`）、Valleyview 写成 `valleyview.`（实为 `vss`）。当初是按校名"合理地"拼出来的。它们是根路径，月度巡检只查深链，所以一直没被发现。
- **新增 Brocklehurst Secondary**（985 Windbreak St，250-376-1232）和 **Kamloops School of the Arts**（1390 9th Ave，250-374-3200）。Kamloops 城区 7 所中学原来只收了 5 所。KSA 是 **K-12 艺术类 School of Choice**，需家庭自主选择报读、不按住址分配——这一点写进了备注，对新移民家庭入学决策很重要。坐标均取自 OSM 上该地址的学校建筑本身。两所官网都没写办公时间，**未填，不照别校编**。

**其他机构**
- **Merit Place Shelter**：搜索时看到"延长至 2025 年 3 月"的旧新闻，担心已关闭仍挂在图上。经 CMHA 现行官网与 bc211 现行条目双重确认**仍在运营**，地址、电话、49 个床位与数据逐项一致。只把 `w` 从 CMHA 首页改为其收容所页面。
- **新增 Moira House**（600 Kingston Ave，250-312-2954）。CMHA 的第三家收容所，原来不在图上。CMHA 官网页面显示的 651 Victoria St / 250-374-0440 是**机构办公室**，不是收容所；地址以省政府开张新闻稿与 bc211 两处一致为准。它是**康复型、给从低门槛收容所过渡出来的人**的住所，不是第一晚的急难床位——备注里加粗写明"第一晚请先去 Emerald Centre 或 Merit Place"，避免危机中的人走错地方。
- **The Salvation Army**（旧货店那条）仍链到全国总会 `salvationarmy.ca`，偏泛；但救世军旧货店在加拿大部分是全国统一运营，未确认本地站上有该店页面前**暂不改**。

**结果**：地点 287 → 291；改链接 18 条（图书馆 2、学校 15、收容所 1）。

**本轮自己犯的一个错，已修并加了防呆**：`validate.py` 默认校验的是构建产物 `build/kamloops.html`。加数据后没先重建就校验，连续三次显示"all invariants hold"，其实校验的是加之前的旧产物；重建后才报出 Aberdeen Tiny Library 的主题顺序错误（`TORDER`）。已修正，并在 `validate.py` 加了检查：数据源比构建产物新时直接报错并提示先 `build.py`。`deploy.sh` 显式传入文件的调用方式不受影响。

## 2026-09-22 按 9-21 全面检查结论修复（7 个阶段）

依据：`docs/archive/reports/2026-09-21-全面检查报告-功能与数据.md`，以及当时 6 批逐条核对与办事卡核对的原始结论（运营方官网 / 市政府 / 省政府页面）。每个阶段都跑了 `build.py`、`validate.py`、`tests/kamloops/regress.py`、`soci2`、`tasktest`、`audit6`，并新增了该阶段自己的测试 `tests/kamloops/phaseNtest.py`。所有补丁脚本保存在 `docs/archive/scripts/fixes-2026-09-21/`，每条改动都在脚本注释里写了出处。

1. **安全与信任**
   - 搜索危机词（6 种语言）时，结果上方显示热线，统计里只记为 `[crisis]`。
   - 页头加常驻"📞 求助"按钮：24 小时热线、KAFS 危机小组、211（注明时段）、立即离开此页、清除本机记录。
   - 事件日志只在 `?debug=1` 时写入本机存储。
   - 搜索词不再写进地址栏，只在主动分享时带上。
   - 勾选步骤时不再上报卡片 ID。
   - 隐私短句改成实话。
   - 页脚紧急电话可以直接点拨，并加上 9-8-8。
   - 211 移出"24 小时热线"；加入 VictimLink 和 KUU-US。
   - 移民身份相关的绝对承诺改为审慎说法。
2. **严重数据**
   - 核对出的 47 条严重问题全部处理，其中 5 条下架进 QUARANTINE：两处已关闭的室内游乐场、9 月 30 日关门的二手店、被误标为二手店的救世军教会，以及位置矛盾的 Dallas 狗公园。
   - 税务卡改为：新移民到达即可用 RC66 / RC151 申请。
3. **"现在营业"如实显示**
   - 法定假日（BC 11 个，已列到 2028 年底；`validate.py` 会在清单快用完前提醒）不再相信平日营业时间。
   - 5 处只接受预约的地点不再显示"营业中"。
   - 第三方地图来源的条目显示"收录于"，不再显示"已核实"。
4. **系统性清理**
   - 名称里的 ⭐ 移到 `pick` 字段。
   - 34 个市政公园按公园条例 35-104 统一为 05:00–23:00。
   - 4 个戏水池按市政季节通知处理。
   - 75 个链接改为门店或机构自己的页面。
   - 银行补上晚关时间。
   - Pioneer Park Beach 注明禁止游泳。
   - 修正公交站路线。
5. **办事卡条件**：deposit、eldercare、msp、licence、sin、hardship、school、connect、settle、rights、bank、legal，以及 6 所小学的入学材料说明。所有步骤只改文字、不增不减，读者已勾选的步骤不会错位。
6. **覆盖补充**
   - 新增地点：Legal Aid BC 办公室、Interior Health 精神健康入口、性侵害辅导中心、第二座锡克庙、印度杂货店。
   - 4 所小学标注 StrongStart。
   - 两家牙科注明接受 CDCP。
   - 求助面板加入 Y 女性紧急庇护所和 Interior 危机热线。
7. **常住居民与原住民称谓**
   - 副标题改为同时面向长期居民；预设名改为"刚搬来"。
   - 指南新增"住了很多年的人"一节：ARCH、KamPASS、图书馆社区通行证、Snow Angels、10 月 17 日市政选举。
   - Kamloopa Powwow 改为 6 月。
   - 统一写作 Tk̓emlúps（旧写法作为搜索别名保留）。
   - 加入 Le Estcwicwéy̓ 的称呼，以及两条原住民 24 小时热线。

**测试改动（1 处）**：regress 第 44 轮原本用 Riverside Park 检查"开放场地无营业时间时显示'现场张贴'"。市政公园现在有条例规定的时间，所以改用 Cooney Bay 检查同一行为。

**未做、需要你决定或需要打电话确认的**
- 救世军食物银行的两套营业时间：需打 250-554-1611 确认。
- The Success Formula Tutoring 的地址。
- Mustard Seed 冬季庇护所（1140 River St）已加上，但 OSM 只能匹配到街道，图钉用了同街相邻门牌的坐标，并标为近似位置；是否已开放需打电话确认。
- 市政府开放数据许可：未替你接受。
- 进度条把"没钱吃饭 / 被歧视"算作待办：涉及交互改动，另议。

## 2026-09-24 学校与托儿数据补全、同义词与图标（p20–p26）

依据：省 K-12 学校开放数据、省 Child Care Map（OGL-BC）、BC Address Geocoder、SD73 各校官网。每个阶段都跑了 `build.py`、`validate.py`、`tests/kamloops/regress.py`、`soci2`、`tasktest`、`audit6`、`audit7`，并新增了该阶段自己的测试。补丁脚本在 `docs/archive/scripts/fixes-2026-09-21/`。

1. **搜不到幼儿园 / 托儿（p20、p22）**
   - kindergarten 指向小学（BC 的 K 年级在小学里），preschool、child minding、유치원、幼稚園、学前班、préscolaire、preescolar 指向托儿。
   - 同义词改为按词匹配：搜 school 能同时命中 elementary school、high school、school bus；`clinic`/`clinics` 列入跳过词，避免"走进式诊所"被只接受预约的 UPCLC 抢答。
2. **补齐 25 所小学（p21）**
   - 省 K-12 开放数据比对后补进缺的 15 所，电话与网址逐校对着 SD73 官网核实，来源标 `official`。
3. **持牌托儿中心 84 家（p25）**
   - 来自省 Child Care Map 的 80 家团体托儿中心；地址逐个过 BC Address Geocoder 重新定位，得分 ≥95 且与原坐标相差 150 m 以内才采用官方点位，否则标为近似位置。
   - 去重（同名 / 40 m 内）、同楼多张牌照合并、同一运营方的分店按街道改名。
   - **有意不收**：38 家持牌"家庭式"托儿（地址是私人住宅）。
4. **新来源标签（p23）**
   - 新增"省政府开放数据"来源类型（6 语）与 Open Government Licence – BC 署名，写进数据说明。
5. **小学时间不再瞎写（p24）**
   - 删掉未经核实的 8:30–15:30；25 所小学统一在备注里说明"各校时间不同、每年变动，去之前打电话或看学校页面"。
6. **图标审查（p26）**
   - 见 `docs/archive/scripts/fixes-2026-09-21/README.md` 的 p26 一行；配套测试 `tests/kamloops/phase16test.py`。

**数据规模**：292 → 387 个地点；来源分布 official 251 / opendata 80 / places 56；22 个近似位置。

**未做、需要你决定的**
- 38 家家庭式托儿（私人住宅地址）是否收录。
- 5 所独立/私立学校（Kamloops Christian、Our Lady of Perpetual Help、Sk'elep、St. Ann's Academy、First Baptist Classical）是否加入。
- `scripts/export-open.py` 目前只导出 `official` + `own`，未包含 80 条 opendata 记录。
- 市政府开放数据许可：仍未替你接受。
