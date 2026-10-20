# Change log

<!-- 2026-09-07 起，页面本身不再展示更新记录，这个文件成为唯一的变更历史，手工维护。 -->

线上版本（Kamloops）：`2026.10.20a`（2026-10-20 从 `main` 部署，Worker 版本 `d2ab7872`；上一版 `40ed504d`）。`main` = 线上，只含 Kamloops；Kelowna 草稿只在 `multi-city`。

> 2026-10-04 补写：这份文件曾停在 `2026.09.08a`，之后的 70 次提交（包括 9 月 21–24 日的 p1–p34 修复轮次和整个多城市改造）
> 都没写进来。下面按版本补齐，内容取自提交说明（`git log`）和 `docs/archive/scripts/fixes-2026-09-21/README.md`。
> 从这次起只写中文，每个版本几行要点；细节以提交说明为准。`2026.09.08a` 及以前保留原来的中英双语全文。

## 未发布：2026.10.20b（main，未部署）

按上线标准逐个按钮实际操作检查（六种语言、手机和电脑）过程中的修复：
- **搜索结果列表**：搜索后列出"地点名 · 区域"，点一下地图滚过来并打开该地点卡片（手机 4 个，电脑两到三列 6 个，危机搜索不显示）。
- **危机搜索**：顶部改为"下面是 24 小时求助电话"；热线左对齐、宽度收窄。
- **冬季驾驶提示**：搜索时让开，不再盖住结果。
- **时间**：营业时间与时间段不断行；同一组星期的两段时间合并显示。
- **电脑版页头**：文字放大，"求助"改为醒目按钮；**分享面板**：电脑上不显示"短信"，说明按设备改写。
- **法文标点**：冒号、问号前用不换行空格。
- **办事卡**：重新核实过的卡显示自己的核对日期；"办成了"有自己的回复；从卡片去填到达日期后回到该卡。
- **分类面板**：说明缩成一句；全市没有地点的分类（咖啡店）不再出现。
- **其他**：关于窗口去掉无关的租金段；手机打开地点卡片时隐藏定位按钮；西、韩、日约 30 处用词。
- **TRU** 不再归在"中学"：新增"大学/学院"分类，搜"大学 / university"可直接找到。
- **Kindergarten**：中、韩、日不再译成"幼儿园/유치원/幼稚園"（那是自愿、常收费的学前班），改为"公立小学的第一年，免费"，免得家长错过 2 月登记。
- **法文**：四张办事卡的"官方页面"链到法文版；« » 内空格、"24 h sur 24""16 h 30" 不再断开。
- **短信识别**：中文"打或发短信 2-1-1"恢复为打电话。
- **母语审读**（法、韩、日）：法文 5 处、韩文约 20 处、日文约 30 处用词和标点；每一批修改都用六语文字快照核对过，其他语言没有变化。

## 2026.10.20a（2026-10-20 部署，当前线上版本）

在 `main` 的构建上再做一遍真人式走查（手机和电脑、六种语言，办事卡逐屏截到最后一行，4 份审阅）：上一版的改动全部生效，没有新的严重问题。补修：
- 指南"第一年先申请一次：RC66、RC151"一句原来只有英文，补齐另外五种语言；中文统一叫"食品与生活必需品补助"；法文"谁管什么"一栏改用新名称。
- 失业卡、住房卡"到了那里怎么说"改为对 WorkBC、法律诊所说的话（原来是该对前雇主、房东说的话）；法律卡加上 Legal Aid BC 全省电话（本地办公室周五到周日关门）。
- 指南和页脚里以文字写的电话号码也不再断行；"更多免费帮助"里的电话可以点；"关于"窗口标题与页脚按钮一致；中日文冒号后多出的空格去掉；韩文口译句补上动词；住房卡英文语法。

## 2026.10.19a（multi-city 与 main，未部署；内容并入 2026.10.20a）

上线后在线上版本上做了一次真人式走查（手机和电脑、六种语言、528 个画面 + 17 张办事卡逐张截图，9 份审阅），修了确认的问题：
- **危机搜索**：搜整句"I'm not safe at home"出来的是一家披萨店（只认关键词）。补上"不安全""害怕回家""威胁""跟踪"等六语说法；危机结果下面不再出现"请检查拼写"，按钮改为打开"立即求助"。
- **离线**：只访问过一次的人断网后打不开（页面要第二次访问才存进离线缓存）。现在安装时就预存页面；新增测试，去掉修复即失败。
- **过期内容**：市政选举"10 月 17 日"已过，改为每四年一次（上次 2026-10-17，下次 2030）。
- **事实与一致性**：指南说 KIS 口译"免费、问一下就行"，与 KIS 官网（收费服务）矛盾，已改；法律卡改为指向 Legal Aid BC；没有写诊所的两张卡不再说"上面列出的法律诊所"；解雇通知期一句英文重复。
- **六种语言**：口译预约电话不再被说成"紧急电话"（法、西、韩、日把它读成紧急号码）；韩、日"等待期从申请时算起"改正；日文前台用语保留英文原句；"newcomer"被全局替换成"居民/resident"留下的约 30 处错句改回"新移民/新来的人"（六语）；西语"破产"否定译反、法语难民用词、日语"保证人"、中文三处。
- **数据说明**：开头不再说"来源为 Google Places"（387 个地点里只有 19 个），中韩日"站点太多无法列出"的旧说法改正。页脚入口改名为"关于本指南 · 声明 · 隐私"（原来叫"看看记了什么"，找不到免责声明）。
- **排版与操作**：电话号码不再从中间断行（含"1-"前缀）；韩文不再在词中间断行；避难所的短信号码可以直接点（`sms:`）；办事卡步骤里的电话可以点。
- **对照官方核实后改正**：第一次报税也能网上申报（不必邮寄纸质表）；RC151 现在是 Canada Groceries and Essentials Benefit（原 GST/HST 抵免，指南六语统一）；MSP 的访客记录只在少数情况下可用；BC Housing 资格补上担保关系破裂的例外和 CUAET；开户时可以由社区中有信誉的人证明身份；长者照护的许可类型写准（TRP）。
- **搜索**：六种语言的"学英语"都能找到 KIS（原来中文、法文、西文找不到，英文排第一的是幼儿早教中心）。

## 2026.10.16a（2026-10-03 – 10-16，2026-10-19 部署，10-20 被 2026.10.20a 取代）

> 下面写"下次部署生效"的，都已随这次部署上线。Kelowna 的部分只在 `multi-city` 分支，不在 `main`、不上线。

**多城市引擎**（阶段 0–5，见 `docs/plans/2026-10-03-多城市工程化计划.md`）
- 引擎拆为 `app/engine/`（head、styles、body、19 个 JS 文件、tail）；城市数据移到 `cities/<id>/`（`city.json` + `data.js` + JSON 数据文件）；地点 schema 校验。
- 工具链按城市（`--city`）；测试城市 Testville（`cities/_fixture/`）与空城市测试；Kamloops 回归移到 `tests/kamloops/`。
- 部署按城市：每城一个 Worker，可切换为一站多路径或自有域名；Kamloops 网址永久不变；草稿城市不能部署；统计按城市区分（`blob5`）。
- 新城市骨架 `scripts/new-city.py`；运营资料移出仓库（决策 D4）。

**Kelowna（草稿）**
- 461 个地点，全部六语：省持牌托儿 133、学校 49、公园湖滩 70、BC Transit 29 条线路 / 955 个站点、官网调研 240 余条；17 张办事卡；6 个地标；"落地第一天"。
- 全部 243 条非政府数据记录经独立复核（55 条改正）；三条本地危机热线逐一核对；电话核实尚未开始（0/75）。
- 补上 Kamloops 已有的两条全国原住民 24 小时热线（Hope for Wellness、寄宿学校幸存者热线）。底图 key 对 Kelowna 网址返回 403，上线前要在 MapTiler 加域名。

**引擎改动（Kamloops 页面文字不变，下次部署生效）**
- 警察电话、本地法律援助、票价、数据来源说明、UPCC 由城市提供（原来写死在引擎里，Kelowna 会显示 Kamloops 的内容）。
- 搜"看病"的答案框按城市列出 UPCC（可多家，各自显示是否开着）；没有 UPCC 的城市也会显示 8-1-1、药剂师、911。
- 修复：连续搜索后点"在地图上看"，地点卡片闪一下就消失（Kamloops 同样受影响）。
- 没有公交数据的城市隐藏公交入口。

**Kamloops 页面会变的地方（下次部署生效）**
- BC 从 2026-11-01 起全年夏令时：时区数据过旧的设备上"现在营业"、季节提示、办事期限不再差一小时（**需在 11-01 前部署**）。
- 开放数据说明补上公交数据的出处与 BC Transit 使用条款（BC Transit 条款要求注明；原来只写了省政府数据），标题从"省政府开放数据"改为"开放数据"；BC 开放数据许可改用现行网址（旧网址会跳转）。
- MSP 办事卡的来源名从"HealthLink BC / MSP"改为"Government of BC — MSP"（链接本来就是省政府的 MSP 页面）。
- 80 家省数据托儿机构的备注补上"参加省托儿费减免计划（CCFRI）"，2 家补上年龄或语言（对照 2026-10-04 的省数据；id 不变）。

**2026-10-04 新手视角测试、两城数据严格校验、六语测试（下次部署生效）**
- **危机求助**：搜 "safe place""women shelter""he hit me""scared of my husband" 等现在先出 24 小时热线（原来出超市和酒吧）；"怎么办"卡片里的搜索遇到危机词也先出热线（原来叫人打只在白天工作日接听的 2-1-1）。
- **看病**：拼错（docter）、"找医生"不再走进死路；夜里没有开着的 UPCC 时说明医院急诊 24 小时开放。
- **搜索**：三个字母以内的英文词（SIN、ER、MSP）只按词首匹配（"SIN" 不再匹配 "Licensing"）；搜的正好是某张办事卡的关键词时，卡片放在结果上方；一个词找不到时提示最接近的词（foodbank → food bank）；补六语同义词（워크인 클리닉、託児所、seconde main 等）。
- **地点卡片**：上一个搜索的卡片不再在新搜索里反复出现（新增测试 `tests/engine/test_popup_lifecycle.py`，已确认它能抓到这个错误）。
- **MSP 办事卡**：改正"COPR 不被接受"——省 MSP 申请表明列永久居民确认书（COPR）；回归测试原来断言的就是这句错话，一并改正。地图点改为领照片卡的 ICBC。
- **Kamloops 数据**：307 条非政府记录第一次独立复核（212 确认、57 改正、35 待电话核实）；146 条备注按官网改正或删去主观评价（例：临终关怀"不收费"→ 有省定日费；StrongStart 要先登记；收容所规则）；3 处改名；药房记柜台时间。
- **Kelowna 数据**：113 个地点的搜索词被导入工具拆成单个字母，已修复并加校验；9 个政府服务点补六语搜索词；73 个缺营业时间的地点复核；重复的锡克庙、疑似关门的 Sabzi Mandi 移入隔离；报税诊所改到"政务移民"类；韩人天主教聚会时间改正。
- **办事卡与城市设置**：约 190 项事实对照官网，17 项改正（银行权利含联邦信用社、解雇补偿最多 8 周、ICBC 只认指定翻译、Kelowna 食物银行两处都要预约等）。
- **六种语言**：608 处译文修正（26 处改变原意的，如西语/日语押金卡把"房东付双倍"译成"你付双倍"；中文把 UPCC 叫"急诊中心"）；2-1-1 的语言数统一为 240 多种。
- **城市化**：最近一次全面核实日期、收藏代码前缀、导航地址里的市名（West Kelowna）改为城市设置。

**2026-10-16**
- 一直开着的标签页：开了 6 小时以上、回到前台时检查服务器上的页面有没有更新，有就提示刷新（访问日志发现一台手机三周都在跑旧版）。

**2026-10-05 继续**
- 省级包：BC 的时区和指南里的省级一章（健康卡、驾照、租房）从引擎移到 `provinces/bc/`，构建时注入；外省城市只需建自己的 `provinces/<省>/`（经验 L-040 由待落实改为自动检查）。
- 返回手势：办事卡"在地图上看"之后按返回，回到那张卡（原来直接离开网站）；新增测试。
- 每座城市一个界面测试 `tests/city_guitest.py --city <城市>`（城市的事实从数据取），Kamloops 也开始跑；Kelowna 的副本删除。
- Kelowna 营业时间：11 处按官网原文结构化，12 处标"不规律，请致电/看官网"，38 处记为"已核实官方未公布"；上线标准改为"每个地点都有时间，或已核实未公布"，对比口径只算官方来源。
- 六种语言第二轮：约 150 处人工修正（含今天改写的 130 条备注的译文复核）；MSP 等待期改正为"从成为居民时算起，但不申请就没有保障"。

**工具与检查**
- 导入工具（托儿、学校、ArcGIS 公园、GTFS、官网调研合并、营业时间、译文、办事卡）；BC 政府地址定位。
- 审核清单（上线差距、分类覆盖、独立复核覆盖、同口径营业时间）、电话核实表、跨语言一致性检查、城市严格界面测试（`tests/kelowna/guitest.py`）。
- 校验：引擎里出现本地电话或任何城市的地点编号即失败；有公交的城市必须有自己的票价；开放数据必须署名。
- 省级共用设置 `provinces/bc/province.json`（假日、热线、2-1-1、冬季与山火提示），同省城市不一致即失败；假日生成器 `scripts/holidays.py`。
- 分类分级 `schemas/category-tiers.json`（审核、核实、调研合并共用）；审核清单的地点目标和参照城市改为城市设置。
- 别城事实的禁用词由各城数据推导（`kamdata.fingerprint`），不再每城手写；新城市骨架同时生成 PROFILE.md。
- `deploy.sh` 的校验带上 `--city`（原来部署别的城市时用 Kamloops 的设置校验）；`audit6` 有 P0 发现即失败（原来永远显示通过）；check-all 每项显示耗时。
- 脚本共用的六语、当地日期、证书、导入路径、运营目录收进 `kamdata`；导入写入的核实月份改用城市当地日期。

**文档**
- 扩城方法论（1.2）、新城市操作手册、新移民画像、多方视角、城市差异建模分析、Kamloops 经验总结、Kelowna 迭代日志。
- 知识库 `docs/knowledge/`：经验登记表（由脚本对照代码核实）、资产清单、提示词模板、数据来源目录（107 个官方来源，网址由脚本核对）；文档结构整理与脚本索引 `scripts/README.md`（2026-10-04）。
- 目录整理：`data/` 改名 `records/`（运营台账）；对外材料的源文件和脚本（`docs/source/`、`flyers/`、`logo.svg`）合到 `outreach/`；BC 地址定位缓存移到 `provinces/bc/`。旧路径对照见 `docs/archive/README.md`。

## 2026.09.24b（2026-09-21 – 09-25）

按"全面检查报告"分 34 轮修复（p1–p34，脚本与说明在 `docs/archive/scripts/fixes-2026-09-21/`）：
- **安全与信任**（p1、p3、p7、p33）：六语危机词直达热线、页头求助按钮、立即离开与清除本机记录；法定假日、仅预约地点；"收录于 / 已核实"标注；原住民称谓与 Powwow 月份；"现在营业"不再挂热线。
- **数据**（p2、p4、p9、p11、p12、p14、p21、p24、p25）：47 条严重数据问题；18 处死链；公交末班、21 个坐标；删除 47 个无法核对的电话；补齐 15 所小学、80 家持牌托儿（省政府开放数据）；小学不再写推测的时间。
- **内容**（p5、p6、p8）：办事卡条件；法律援助、精神健康、女性安全等覆盖；新卡：家庭医生、安全找房、失业了；季节提醒。
- **搜索**（p16–p20、p22、p34）：六语同义词表；搜索时暂停分类筛选；没结果时显示最接近的结果、办事卡和看病答案框；约 2,400 个查询的误匹配回归。
- **界面**（p26–p29、p31、p32）：图标审查、气泡重构、设计令牌、扁平地图针；缩放动画期间不改动标记聚合；窄屏文字溢出。
- **多语言**（p30）：修掉 ES2018 正则（旧浏览器整页白屏），六语端到端检查。
- **统计**（p10、p13、p16）：补齐事件；办事卡电话点击；维护者设备标记 `?maintainer=1`。
- 9-25：面向定居团队的说明 PDF 修订；4 天访问分析；交接与发展方案。

## 2026.09.16b（2026-09-16）

- 线上安全头从未对首页生效（静态资源绕过了 Worker），改为 Worker 先处理；部署闸门从未跑通（指向旧路径）；月度巡检一直报假数（grep 计数错误）——三项都修好并加了检查。
- 链接巡检：HEAD 失败改用 GET 复核、按域名限速、证书包；3 条失效深链。文档与目录整理（`docs/` 统一收拢）。

## 2026.09.16（2026-09-16）

- 地点死链与错页修复；QA 脚本指向新的办事卡位置；去掉未用的传单版本。

## 2026.09.13a – 2026.09.13f（2026-09-13 – 09-14）

- 13a：上线前审计，31 个可复现缺陷（指南、地图、多语言、离线、无障碍）；桌面打印办事卡。
- 13b：搜索引导的首次使用、传单落地页、深链一次返回、步骤勾选与时间线、最近站点与距离、手机语言菜单、线条图标。
- 13c–13e：OpenStreetMap 瓦片服务器封禁本站 → 改用 MapTiler，失败自动回退 Esri；底图供应商成为城市数据；启动时探测 403。
- 13f：首次使用者视角的 25 个缺陷（手机、平板、桌面）。
- 9-14：外联 PDF 重建（`v2026.09.14`）。

## 2026.09.10b – 2026.09.11f（2026-09-10 – 09-13）

- 10b：指南为主、地图为辅；"现在营业"；19 个核实地点；标志。
- 10c：数据可信度（14 个坐标重新定位、7 个无法核实的地点隔离）、指南深度（指南内搜索、?task= 深链、到达日倒计时、长者照护卡、城市历史）、法律文字、Letter 尺寸传单。
- 10d：全新视角扫描：隔离 4 个已关闭或不存在的地点、补 12 个核实地点、9-8-8；法西语重音恢复；`?src=` 在改写地址栏前读取（此前从未被记录）。
- 10e – 11b：指南作为视觉主体；隐私说明逐项精确；Apple 风格的交互（底部面板、返回手势、撤销）。
- 11d：坐标双源互证；Worker 安全头与事件接口加固；"全城只有一家真正的 walk-in"如实写出。
- 11e：可查询的统计（Analytics Engine 各列）；办事卡移入数据层；校验禁止引擎含 TASKS、警告引擎里的本地电话。
- 11f：情境快捷选择（六个场景 + 更多）。

## 2026.09.08f – 2026.09.09a（2026-09-09 – 09-10）

- 08f：第二轮多学科审查（无障碍、指南）。
- 09a：地标重选（每区一个，外地人找得到、确实要去的地方）；隐私文字重写；传单世俗版，不再手写地点数量。


## 2026.09.08a

**中文**

- **修复了 `public/index.html`（Cloudflare Worker 实际提供服务的那份文件）长期没跟上根目录 `kamloops.html` 的问题。** 根因：`deploy.sh` 的 [1/5] 步骤会自己重跑一次 `build.py --city kamloops --out public/index.html`，但只有在真正执行 `./deploy.sh` 时才会发生；这次会话里根目录 `kamloops.html` 被反复重建了很多次（日语上线、居民改名……），却没有一次是通过 `deploy.sh` 触发的，`public/index.html` 就一直停在 9 月 7 日 04:56 那次，体积也比新版小了近 30%。修好的方式不是"记得多跑一步"，而是让它在结构上不可能再跑偏：`build.py` 现在只要是给 `kamloops` 城市构建（且没有显式 `--out` 到 `public/index.html` 本身），就会在写完主输出后自动把同一份 HTML 也写一份到 `public/index.html`，两份文件保证逐字节一致；新增 `--no-sync-public` 开关给一次性测试构建（比如 `--cdn`）留了跳出口。也就是说往后不管是本次会话里 `python3 build.py --city kamloops` 这种日常调试构建，还是别的场景下的重建，只要不是刻意关掉，`public/index.html` 都会跟着一起更新，不会再需要单独惦记它。当场把两份文件都同步成了最新版本（`DATA_VERSION=2026.09.08a`），设备上确认逐字节相同。
- **"附近"（Near Me）定位功能做了两处强化，让用户更容易点、点完就知道自己在哪。** 点击热区：这是地图上单次使用频率最高的控件，所以没有沿用全站共用的 44px 触控下限，而是在触屏设备上单独给到 48px（图标本身也从 18px 放大到 21px），移动端窄屏下的内边距也从 9px 加到 10px。定位反馈：原来定位成功后只是放一个纯色圆点，容易让人分不清"这是我的位置"还是"这是一个地点标记"；现在换成了一个会脉冲扩散的呼吸动画标记（外圈脉冲 + 内圈实心点，配色沿用站点强调色），旁边还常驻一个跟随语言切换的文字提示（"📍 你的位置" / "📍 Your location" / 其余四种语言同理），不需要额外点击或悬停就能一眼确认。已按 `prefers-reduced-motion` 关闭脉冲动画作为退化方案。
- **"数据说明"按钮按要求暂时隐藏，不是删除。** 头部的"数据说明"按钮现在带 `hidden` 属性，对用户不可见也不可点；对应的模态框、内容渲染逻辑原样保留，以后想恢复只需去掉这一个属性。隐藏的实现顺带补上了一个真实存在的陷阱：站内 `@media(pointer:coarse)` 下有一条作者样式统一把几个头部按钮设成 `display:inline-flex`，这条规则的优先级本来就会盖过浏览器对 `hidden` 属性的原生隐藏（作者样式永远赢过浏览器默认样式，跟选择器优先级无关）——如果不专门处理，这颗"暂时隐藏"的按钮会在所有触屏手机上原样露出来，而这在桌面浏览器里测试根本看不出来。已经用站内已有的同款防御写法（`#noteToggle[hidden]{display:none}`）堵上了。
- **回归测试新增 6 项，专门盯这三处改动，总数从 205 涨到 211，全部通过、0 个页面错误。** 覆盖：48px 触控热区在 pointer:coarse 下确实达标；定位成功后确实出现脉冲标记而不是纯色圆点；标记的提示文字确实带 `permanent` 属性、内容确实随语言切换而更新；细指针和粗指针（`pointer:coarse`）两种场景下 `#noteToggle` 的 `display` 计算值都确实是 `none`（专门覆盖上面那条 CSS 优先级陷阱，而不只是检查图标态）；旧的"其余三个头部链接维持纯图标"断言相应改成了"其余两个"（因为"数据说明"已经不是纯图标态而是彻底不渲染）。

**English**

- **Fixed `public/index.html` — the file Cloudflare Workers actually serves — falling behind the root `kamloops.html` build.** Root cause: `deploy.sh`'s own [1/5] step re-runs `build.py --city kamloops --out public/index.html`, but only when `./deploy.sh` itself actually runs; this session rebuilt root `kamloops.html` many times (the Japanese rollout, the resident-wording rename, ...) without a single one of those going through `deploy.sh`, so `public/index.html` sat frozen at its 2026-09-07 04:56 build, nearly 30% smaller than the current one. The fix isn't "remember one more step" — it's making the drift structurally impossible going forward: `build.py` now writes a byte-identical copy to `public/index.html` automatically any time it builds the `kamloops` city (unless `--out` already points there), with a `--no-sync-public` escape hatch for one-off test builds (e.g. `--cdn`) that shouldn't touch the real deploy artifact. So an ordinary debugging build like this session's `python3 build.py --city kamloops` — or any future rebuild — now keeps `public/index.html` current without anyone having to remember it separately. Both files were rebuilt to the latest version (`DATA_VERSION=2026.09.08a`) and confirmed byte-identical on the device.
- **Two Near Me (geolocation) upgrades, aimed at making the control easier to tap and its result unambiguous.** Tap target: since this is the single most-used control on the map, it now gets 48px on touch devices instead of the shared 44px floor (the icon itself grew from 18px to 21px, and mobile padding went from 9px to 10px). Location feedback: a successful fix used to drop a plain solid-color dot, easy to mistake for an ordinary place marker; it's now a pulsing "breathing" marker (an expanding pulse ring plus a solid center dot, in the site's accent color) with a permanent, language-aware tooltip label ("📍 Your location" / "📍 你的位置" / and so on for the other four languages) — no extra tap or hover needed to confirm it's you. The pulse animation is disabled under `prefers-reduced-motion`.
- **The "Data Notes" button is paused, not removed, per this round's request.** The header button now carries a `hidden` attribute and is neither visible nor clickable; the modal and its content-rendering logic are untouched, so re-enabling it later is a one-attribute change. Implementing the hide surfaced a real trap worth flagging: an author-origin `@media(pointer:coarse)` rule already sets several header buttons to `display:inline-flex`, and author styles always beat the browser's native `[hidden]` behavior regardless of selector specificity — so without a fix, this "hidden" button would have silently reappeared full-size on every touch phone, invisible in desktop testing where no such rule conflicts. Closed with the same defensive pattern already used elsewhere in the codebase (`#noteToggle[hidden]{display:none}`).
- **Regression suite grew by 6 checks specifically targeting these three changes, 205 → 211, all passing, 0 page errors.** New coverage: the 48px tap target actually measures ≥48px under pointer:coarse; a successful fix actually renders the pulsing marker (not the old plain dot); the marker's tooltip is actually `permanent` and its content actually updates on a language switch; `#noteToggle`'s computed `display` is actually `none` under both fine and coarse pointer types (directly guarding the CSS-cascade trap above, not just the icon-only state); the old "the other three header links stay icon-only" assertion was updated to "the other two" now that Data Notes is fully hidden rather than merely icon-only.

## 2026.09.08

**中文**

- **新增日语（日本語）作为第六种界面语言，位置排在韩语之后。** 覆盖全部内容：基础 UI 对象的 34 个键、192 个后置赋值键（含四段长文本的居民指南——加拿大通用篇、联系方式与心理健康篇、BC 省篇、Kamloops 本地篇）、49 个分类标签、10 个主题标签、11 个分组标签、7 个区域的地理提示、城市名称与省份、以及全部 235 条地点备注——一条不漏，遵循和法语/西班牙语/韩语相同的"要么全译、要么不译"契约。日语的标点没有照抄任何一种现有语言：括号沿用中文的全角（），列表分隔符沿用中文的顿号、，但日期/时间范围单独选了波浪线〜（既不同于中文的"至"，也不同于英韩的"–"），冒号则跟英韩一样用半角冒号加空格（不用中文的全角："）。
- **"新居民"改成了"居民"，五种既有语言同步。** 中文"新居民"→"居民"；英文 newcomer→resident；法文 nouvel(le)(s) arrivant(e)(s)→résident(s)；西班牙文 recién llegado(a)(s)→residente(s)；韩文 신규 정착민→주민；日文从一开始就按"居民"的语义书写。唯一保留的例外是"新移民"——这三个字在 engine.html 和 data-kamloops.js 里各出现一次，说的是 SWIS（校园定居支援员）项目真实的资格限定（新移民家庭），指的是一种移民身份，不是本站给读者的自称，所以没有动。同样没有动的还有代码内部标识符（DOM id、PRESETS 里的分类键、UI 对象里的 JSON 键）——它们仍然拼作 newcomer，改了会破坏分享链接和收藏夹的兼容性。
- **两处校验/回归随之更新。** `validate.py`：`LANGS` 加入 `ja`；地点备注的"要么全译、要么不译"契约从 fr/es/ko 三选一扩到 fr/es/ko/ja 四选一；房源用词检查现在同时禁止"新移民"（一直如此）和"新居民"（现已过时）。`regress.py`：所有遍历五种语言的循环扩到六种；语言按钮数量断言从 5 改成 6；新增两条检查，确认日语确实沿用了中文的顿号、也确实用了半角冒号（不是照抄中文的全角）。回归从 197 项增加到 205 项，全部通过，0 个页面错误。
- **本轮翻译先用三个独立子任务并行处理**（176 条界面短语、235 条地点备注分两批），每批完成后都做了结构校验（键集合、id 集合、JSON 合法性）而不是只信任任务报告；四段长文本的居民指南由本人直接撰写以保证语气和前几语言版本一致。

**English**

- **Added Japanese (日本語) as a sixth interface language, positioned after Korean.** Full coverage: all 34 base UI keys, all 192 post-assignment keys (including the four long-form resident-guide sections — national, contacts & wellbeing, BC-provincial, and Kamloops-specific), 49 category labels, 10 theme labels, 11 group labels, all 7 regions' geographic hints, the city name and province, and all 235 place notes — every one, following the same all-or-nothing translation contract already used for French/Spanish/Korean. Japanese punctuation wasn't copied wholesale from any existing language: parentheses and the list separator follow Chinese's full-width （）and 、, but date/time ranges got their own choice, a wave dash 〜 (distinct from Chinese's 至 and English/Korean's –), while the colon matches English/Korean's half-width "`: `" rather than Chinese's full-width "：".
- **Renamed the site's "newcomer" branding to plain "resident," synchronized across all five existing languages.** Chinese 新居民→居民; English newcomer→resident; French nouvel(le)(s) arrivant(e)(s)→résident(s); Spanish recién llegado(a)(s)→residente(s); Korean 신규 정착민→주민; the new Japanese copy was written in the resident framing from the start. The one deliberate exception is 新移民, which appears once each in engine.html and data-kamloops.js describing SWIS's actual eligibility (newcomer families) — a real immigration status, not the site's own term for its readers — and was left untouched, as were the internal code identifiers (DOM ids, the PRESETS category key, UI object JSON keys) still spelled "newcomer," which must not change without breaking shareable links and favourites.
- **Two supporting files updated to match.** `validate.py`: `LANGS` now includes `ja`; the note translation contract widened from fr/es/ko to fr/es/ko/ja, all-or-nothing; the house-wording check now forbids both 新移民 (always has) and 新居民 (now deprecated). `regress.py`: every five-language sweep now covers six; the language-button count assertion is 6 (was 5); two new checks confirm Japanese deliberately keeps the ideographic comma (、) like Chinese and a half-width colon (not Chinese's full-width one). Regression grew from 197 to 205 checks, all passing, 0 page errors.
- **Translation work was split into three parallel passes** (176 UI strings, 235 place notes in two batches), each independently verified afterward for key/id-set completeness and valid JSON rather than trusting the pass's own summary; the four long-form guide sections were written directly to keep their tone consistent with the existing four languages' versions.


## 2026.09.07g

**中文**

- **按《首次使用体验分析》实现了全部 P0(3)/P1(3)/P2(3) 共 9 项，P3 按计划暂缓。**
  - **新增"附近"定位入口。** 地图右下角一个圆形按钮，点击后**先解释、后请求**——先弹出一句话说明用途，用户确认了才真正调用浏览器定位；拒绝、超时、设备不支持都有对应文字说明，不会静默失败。定位成功后地图重新定位到当前位置，但返回的经纬度**不会出现在任何埋点事件里**——`geo_locate` 只记录"成功/失败/原因"，专门写了自动化测试逐字检查事件对象里没有 lat/lng/latitude/longitude/coords 任一字段。隐私说明五语言同步补了一句披露。
  - **首屏地图空间加大。** 首次提示语从一整句长解释缩短成一句问句式短提示；"重置"按钮在无筛选状态下从"变灰变淡"（一个 CSS 类）改成 DOM `hidden`——真正从页面消失，而不是继续占着位置。
  - **修了首次提示语在矮屏上直接消失的 bug。** 原逻辑拿"屏幕高度小于 680px"当"用户不需要提示"的代理指标，逻辑上并不成立；现在改成只看用户是否真的关闭过提示（沿用已有的 `hintDismissed` 标记），矮屏换一句更短的文案而不是隐藏成空白。
  - **头部📖新居民指南按钮加了可见文字标签**（五语言），另外三个纯图标按钮（🔗💬ℹ️）维持不变——它们不需要被主动发现，用到时找得到即可。
  - **7 个区域按钮名字后面都加了括号里的地理提示**（河的哪一岸、靠近哪所大学、方位），照顾完全不认识 Sahali、Brocklehurst 这类本地地名的新移民。
  - **地图默认视图新增 6 个地标常驻文字标签**，复用了公交站名早就有的防重叠算法，不再只有聚合数字撑场面。
  - **未筛选时的地点数量从"263/263"这种分数改成"263 处地点"**，一旦真的筛选了才恢复成比例形式——分数只在能传达"筛掉了多少"时才有意义。
  - **副标题不再预设"先选区域再选分类"的操作顺序**，同时从纯 `display:none` 改成视觉隐藏但留在无障碍树里，用 `aria-describedby` 关联主标题，从纯占位变成真正有用的说明。
  - **快捷选择行新增三个高价值主题按钮**：免费/低成本、亲子友好、室内/冬季。
- **过程中自查顺手修了几处**：新的定位按钮在手机宽度下只有 36px 高，补进了项目统一的 44px 触控热区规则；`validate.py` 的运行时符号检查此前只认函数的第一个参数，新写的 `computeLabelVisibility(items, forceFn)` 把 `forceFn` 当回调触发了误报，现在会识别具名函数的全部参数；两行代码注释里 `UI.hintShort` 这样的写法被死代码检测误判成 CSS 类选择器，改了措辞后消失；`data-kamloops.js` 新增 `LANDMARKS`（6 个地标 id），`validate.py` 相应新增一条校验，要求每个 id 都能解析到真实、不重复的地点。
- **3 条断言旧行为的回归测试按主动改变的新行为更新**（重置按钮的"变灰"→"真正消失"、地点数量的"永远是分数"→"未筛选时是总数"），不是被当成需要撤销的失败。
- **回归从 168 项增加到 197 项**，新增 22 条：定位功能的完整同意流程（含拒绝后能否重新弹出说明、二次点击是否跳过说明、事件里确认不含坐标）、地标标签渲染与平移后的稳定性、三个新主题按钮的实际筛选效果、矮屏提示语文案、副标题的无障碍属性、区域按钮的地理提示文本、筛选前后状态栏措辞、指南按钮的短标签。
- `DATA-SCHEMA.md` 新增 `LANDMARKS` 字段说明。

**English**

- **All 9 items from the first-use analysis — P0(3)/P1(3)/P2(3) — are implemented; P3 stays deferred as planned.**
  - **A "near me" entry point.** A round button at the bottom-right of the map explains itself **before** asking: a one-line explanation appears first, and the browser's location prompt only fires once the reader confirms. A denial, a timeout and an unsupported device each get their own message rather than failing silently. A successful fix recentres the map, but the resulting coordinates **never reach any telemetry event** — `geo_locate` records only success/failure/reason, and a test asserts, field by field, that the event object carries none of lat/lng/latitude/longitude/coords. The privacy note gained a matching disclosure in all five languages.
  - **More first-screen room for the map.** The first-run hint shrank from a full explanatory sentence to a short, question-shaped prompt; the Reset button, when there is nothing to reset, switched from a dimmed CSS state to the DOM `hidden` attribute — genuinely gone from the page rather than still occupying space.
  - **Fixed the hint vanishing entirely on short screens.** The old rule used screen height under 680px as a proxy for "this reader doesn't need the hint," which doesn't hold up; it now keys off whether the reader has actually dismissed the hint before (the existing `hintDismissed` flag), and short screens get a shorter variant of the text instead of nothing.
  - **The header's 📖 guide button gained a visible text label** in all five languages; the other three icon-only links (🔗💬ℹ️) stay as they were — they don't need to be discovered, only found when looked for.
  - **All 7 region buttons now carry a parenthetical geographic cue** (which riverbank, which university it's near, which direction), for a newcomer who has never heard of Sahali or Brocklehurst.
  - **Six persistent landmark labels now show on the map's opening view**, reusing the anti-overlap algorithm already built for bus-stop labels, so the first look shows named places rather than only cluster counts.
  - **The unfiltered place count reads as a plain total** ("263 places") instead of the "263/263" fraction; the ratio comes back once a filter actually narrows the results, which is the only time it says something useful.
  - **The subtitle no longer presumes "pick an area, then a category,"** and moved from plain `display:none` to visually hidden but present in the accessibility tree, tied to the heading via `aria-describedby` — from inert placeholder to an actual assistive description.
  - **Three high-value theme quick-picks were added**: Free/Low-cost, Kids & Family, Indoor/Winter.
- **Caught and fixed along the way**: the new locate button was only 36px tall at phone width, folded into the project's existing 44px touch-target rule; the runtime-symbol checker in `validate.py` only tracked a function's first parameter, so the new `computeLabelVisibility(items, forceFn)` calling `forceFn` as a callback was flagged as undefined — it now recognises every parameter of every named function; two code comments spelling out `UI.hintShort` were misread by the dead-CSS scanner as a class selector, fixed by rewording rather than suppressing; `data-kamloops.js` gained `LANDMARKS` (6 landmark ids), with a matching `validate.py` check that every id resolves to a real, distinct place.
- **Three assertions of the old behaviour were updated to match the new, intentional behaviour** (Reset going from dimmed to genuinely hidden; the place count going from always-a-fraction to a total when unfiltered) rather than treated as regressions to revert.
- **Regression grew from 168 checks to 197**, adding 22: the full geolocation consent flow (denial then re-prompt, a second tap skipping the explainer, confirming no coordinates in the event), landmark-label rendering and stability across a pan, the three new theme quick-picks actually filtering, the short-screen hint text, the subtitle's accessibility attributes, the region buttons' geographic cues, the status text's wording before and after filtering, and the guide button's short label.
- `DATA-SCHEMA.md` documents the new `LANDMARKS` field.

## 2026.09.07f

**中文**

- **埋点修了两个一直在错的地方。** 一是 `fav_toggle` 写的是 `P[idx].cat`，而字段其实叫 `c`——所以"大家收藏什么类型的地点"这一列**从上线起就一直是空的**，没人发现是因为空列不报错。二是搜索词的清洗函数按**事件名**挂钩（只处理 `search_run`），于是 `search_empty`——那个专门用来记录"用户打了什么却没找到"的事件——把原文连同电话号码、门牌号一起上传，和隐私说明写的内容直接冲突。现在改成按**字段名**清洗：任何带 `q` 的事件，无论现在有没有，都会先去掉连续数字再截断。
- **搜索词统计此前在统计一个错误的东西。** 上报挂在去抖后的每次按键上，慢速输入 "grocery" 会产生 gro/groc/groce/grocer/grocery 五行，"热门搜索词"排行榜实际上成了"真实搜索词的前缀"排行榜。现在等输入停稳（1.1 秒）再记一行，回车视为显式提交立即记录；同时 `search_run` 带上了结果数 `n`，一行就能判断这次搜索成没成。
- **补上了几个此前完全测不到的问题。** 新居民指南是全项目内容价值最高的部分，这一轮刚扩写六倍，而它**没有任何打开埋点**——"有没有人读指南"是查不出来的，不是查不准。现在有 `guide_open` 和带停留时长的 `guide_close`，能区分"点开看了一眼"和"真的读了"。同理补上 `note_open`；`marker_close` 带上停留时长；`session_start` 补上设备档位（手机/平板/电脑）、是否从桌面图标启动（manifest 从上线就带着 `?source=pwa`，但从来没人读它）、以及是否由带筛选的分享链接进入。
- **服务端不再无条件相信客户端时钟。** 时钟错乱的设备很常见——刚跨过几个时区的旧手机尤其如此——它写来的时间戳可能差几天甚至几年，而所有按时间分桶的报表会被静默污染，且没有任何迹象。现在 Worker 对偏离服务端时间超过 24 小时的时间戳用服务端时间兜底，并把校正过的行标记在 `double3`，于是"有多少设备时钟不准"本身也成了一个可以查询的指标。同时加了请求体大小上限和结构校验。
- **单个会话的事件数加了上限（250 条）。** 此前没有任何限制，一个反复点筛选的人可以耗掉免费额度，更麻烦的是能主导整份聚合。超限后发一条 `budget_reached` 说明被截断了——截断本身出现在数据里，好过悄悄消失。
- **隐私说明补上了两项一直在收集却从未披露的内容**：把访客带过来的那个网站的域名（`session_start.ref`，从一开始就在收，说明里没写），以及新增的屏幕档位与是否已安装到桌面。列出一部分而不列全部，比什么都不列更糟，因为它会让人以为那份清单是完整的。
- **多语言：三处一种语言的排版规则被套用到了全部五种。** 关门日列表的分隔符写死成顿号，所以英文读者看到的是 "Closed: Tue、Thu、Sun"，法文西文同理；公交提示条的站点数写死成全角括号，英文读者看到的是 "Route 1 Tranquille（31 stops）"；韩文的冒号用了中日文的全角 `：`，正确的韩文写法是半角冒号加空格。这三处的共同成因是中文文案先写、之后没人读过这几个分支的英文输出。现在分隔符和括号都成了每种语言自己的 UI 键，韩文按韩文排版。`validate.py` 加了一条检查：剥掉全部 UI 赋值之后，任何 CJK 标点出现在拼句子的代码里都会直接失败——这条检查在写完的当下就抓出了第二处（全角括号），我原本只找到第一处。
- **语言切换按钮统一了标准。** 五个按钮里有两个（中文、한국어）因为文字本身就是母语写法而"碰巧"自我说明，另外三个（EN/FR/ES）只是 ISO 代码，读屏软件会用当前页面的语言把它们读成字母。现在五个按钮一律带 `lang` 属性和该语言的母语全称作为无障碍名称与提示——同一条规则适用于全部五种，而不只是最需要的那几个。完整母语名称没有作为可见文字，是因为在 360px 宽的手机上五个全称放不下，而一个看不全的语言切换器比一个紧凑的更糟。
- **文档语言标记改为实际书写的地区变体**：`en-CA`、`fr-CA`（英文文案是加拿大拼法，法文用的是 courriel 这类加拿大用法）、`zh-CN`；西班牙文和韩文写的是中性语体，保持不带地区码。规则是"当文案确实是为某个变体写的时候，就把变体写出来"。
- **应用图标换成了原创的两河交汇图形。** 原来是蓝色方块里放一个 🗺️ emoji——既和这座城市无关，又取决于读者操作系统碰巧装了哪套 emoji 字体。新图标画的是 Kamloops 名字的来处：Secwepemc 语 "Tk'emlúps" 意为"两水交汇"，北汤普森河自北而来、南汤普森河自东而来，在干旱台地丘陵下汇合后向西流出。颜色取的是这条河谷夏天真实的样子。全部由几何图形从零绘制，不涉及任何徽标、字标、照片或其他受保护作品——河流交汇与山坡是地形事实，这几条曲线是原创的。同时补上了 iOS 需要的 180px PNG：Safari 从来不接受 SVG 作为 `apple-touch-icon`，所以此前那一行指向的是一个 iOS 会静默忽略的文件，加到桌面得到的是页面截图。
- **回归从 149 项增加到 168 项**，新增埋点与多语言两组浏览器实测（含"慢速输入只产生一行"和"每种语言用自己的标点"这类此前无人验证的行为）。

**English**

- **Two telemetry bugs that had been wrong the whole time.** `fav_toggle` wrote `P[idx].cat` when the field is `c`, so the column recording *what kind of place people save* has been **empty since it shipped** — nobody noticed because an empty column throws no error. And the search-term sanitiser was keyed on the **event name** (`search_run` only), so `search_empty` — the one event whose entire purpose is recording what someone typed and failed to find — uploaded the raw string, phone numbers and street numbers included, in direct contradiction of the privacy note. Sanitising is now keyed on the **field**: any event carrying `q`, including ones that do not exist yet, is cleaned first.
- **The search statistics were measuring the wrong thing.** Logging hung off every debounced keystroke, so "grocery" typed at phone speed produced gro/groc/groce/grocer/grocery and the top-searches ranking was really a ranking of prefixes of real queries. Logging now waits for the query to settle (1.1 s), with Enter treated as an explicit submit, and `search_run` carries the result count `n` so one row says whether the search worked.
- **Several questions were unanswerable rather than badly answered.** The newcomer guide is the most valuable content in the project and had just been expanded sixfold — and it had **no open event at all**. There are now `guide_open` and a `guide_close` carrying dwell, which separates a glance from a read; `note_open` likewise; `marker_close` carries dwell; and `session_start` gained the layout bucket (phone/tablet/desktop), whether the page was launched from an installed icon (the manifest has advertised `?source=pwa` since the PWA shipped and nothing ever read it), and whether the visit arrived on a shared link that already carried filters.
- **The server no longer trusts the client's clock unconditionally.** Devices with wrong clocks are common — near-certain on an old phone that has just crossed several time zones, which describes a fair share of this map's audience — and a timestamp days or years out silently corrupts every time-bucketed report with nothing to show for it. The Worker now substitutes server time for anything more than a day out and flags the corrected row in `double3`, so the rate of bad clocks becomes a measurable quantity instead of a hidden distortion. A request-size limit and a shape check were added at the same time.
- **A per-page-load event budget (250).** Nothing capped it before: a restless visitor could burn the free tier and, worse, dominate every aggregate. Crossing it emits one `budget_reached` so truncation appears in the data instead of looking like a session that simply stopped.
- **The privacy note now discloses two things that were being collected and never listed**: the domain of whatever site linked the reader here (`session_start.ref`, collected from the beginning, absent from the note), and the new screen bucket and installed-or-not flag. Listing some of what leaves the device and not the rest is worse than listing none, because it teaches the reader to trust the list.
- **Five languages were being shown one language's typography in three places.** The closed-day list separator was hard-coded as the ideographic comma, so English readers saw "Closed: Tue、Thu、Sun"; the bus indicator wrapped its stop count in full-width Chinese brackets, so they saw "Route 1 Tranquille（31 stops）"; and Korean used the Chinese full-width colon where Korean sets a normal colon and a space. All three have the same cause — the Chinese copy was drafted first and nobody read those branches' English output afterwards. Separator and brackets are now per-language UI keys and Korean is set in Korean conventions. `validate.py` gained a check that strips every UI assignment and fails on CJK punctuation left in the code that assembles a sentence — and it caught the second instance the moment it was written, which I had missed.
- **One standard for all five language buttons.** Two of the five were self-describing only because their scripts are distinctive; the other three were ISO codes a screen reader announces as letters in the current page's voice. All five now carry a `lang` attribute and the language's own name as the accessible name and tooltip. The full endonyms are not the visible labels because five of them do not fit a 360 px header, and a language switcher a reader cannot see in full is worse than a compact one they can.
- **The document now declares the locale actually written**: `en-CA` and `fr-CA` (the English is Canadian spelling, the French uses Canadian usage such as *courriel*), `zh-CN`; Spanish and Korean stay unqualified because that copy is written neutrally. The rule is to name the variant when the copy is written for one.
- **The app icon is now an original drawing of the confluence.** It was a 🗺️ emoji in a blue square — unrelated to this city, and rendered as whatever glyph the reader's OS happened to supply. The new one draws where the city's name comes from: Secwepemc *Tk'emlúps*, "the meeting of the waters" — the North Thompson down from the north, the South Thompson in from the east, joining below the dry benchlands and leaving west as one river, in the colours that valley actually is in summer. Drawn from scratch as plain geometry; no logo, wordmark, photograph or other protected work is involved — a river junction and a hillside are facts of the landscape and these curves are original. A 180 px PNG was added for iOS, which has never accepted an SVG `apple-touch-icon`: the previous line pointed at a file iOS silently ignored, so a home-screen tile came out as a screenshot of the page.
- **Regression went from 149 checks to 168**, adding browser coverage for telemetry and for per-language typography — including "slow typing produces one row" and "each language brackets and separates in its own punctuation", neither of which anything had ever verified.

## 2026.09.07e

**中文**

- **新居民指南大幅扩写**：从 4 个小节扩到 27 个小节，五种语言同步。新增的内容是按"新到一个国家的人真正会卡在哪里"来选的，而不是按行政流程罗列：从零开始建立信用记录（刚落地的人不是信用差，是系统里查不到，很多申请因此被直接拒）；**你有权免费要求传译**（本省公立医疗系统提供 200 多种语言、24 小时、患者不付费，8-1-1 提供 130 多种语言——这是新居民最被低估的一项权利，也是本次最想让人看到的一条）；哪怕收入为零也要报税（GST 退税、儿童福利金都是从报税记录里算出来的，不报就一分拿不到）；加拿大简历不放照片年龄性别、"本地经验"死循环的几种破法、受监管职业的执业认证；找不到家庭医生时的正规轮候登记与替代路径；租房法定底线（押金半月上限、涨租 12 个月一次、三个月书面通知、2026 年上限 2.3%）、看房防骗、没有本地信用记录怎么租；**遇到歧视、骚扰或不公平对待怎么办**（受保护的理由与领域、留证据、一年时效、免费投诉渠道，以及"这算不算歧视"的判断路径）；留学生的每周 24 小时打工上限、保险衔接空窗、毕业工签与学术诚信；钱不够用时的食物银行 / 2-1-1 / 租金周转 / 社会救助；**"不知道该问谁"的对号入座表**（把十几类常见问题一一对到具体机构和电话）；以及孤独、想家与融入——包括口音不是缺陷、本地人真正认识朋友的固定场合、以及"不必完全同化"。本地一层新增了落地第一站的定居机构、没有车怎么生活、TRU、夏天的山火烟霾与冬天的装备和季节性情绪低落、以及本地省钱与免费资源。
- **指南目录**：内容长了六倍，所以指南顶部会自动生成一份目录，点任意一条直接跳到该小节并高亮。目录是从标题实时生成的，任何一层新增小节都会自动出现在目录里，五种语言都一样。
- **新增"主题"筛选轴（打卡点分类）**：分类是单选的（它决定图钉的颜色和图标），但一个地点可以同时属于多个主题。十个主题：生活日常、亲子遛娃、娱乐休闲、风景打卡、历史古迹、文化艺术、免费低价、多元文化、学生常用、冬天室内。主题和分类、区域三者叠加生效，勾选多个主题表示"同时满足"。主题会显示在每个地点的弹窗里（不打开筛选面板也能看到这个维度存在）、可以直接搜索主题名、会写进分享链接、每个主题在筛选后有独立可移除的标签。主题的归属由 `tools/themes.py` 按规则生成，逐条例外都在脚本里写明依据来自该记录自己的备注——"风景"和"历史"绝不从分类推断。
- **新增两个分类**：食物银行、历史建筑。
- **数据准确性修复（这一轮最实质的部分）**：
  - `precision:'low'` 这个字段在数据里已经存在 22 条，但页面从来没有渲染过——也就是说一个偏差 100 米的图钉，看起来和实测到米的图钉一样自信。现在弹窗会直接说明"这是大致位置，地址才是准确的，导航用的也是地址"，五种语言都有。
  - `sameComplex` 同样是死字段（只有 Costco 两条在用），于是九组坐标完全重合的图钉看起来像重复数据。现在补齐到 11 组 23 条，弹窗会写明"同一地址还有：XX"——邮局柜台在药房里、戏水乐园在公园里，这样才读得懂。
  - **五条坐标被证明是错的并已修正**：Scotiabank(Victoria St) 偏 498 米、TD Canada Trust(Victoria St) 偏 411 米、Okanagan Thompson Legal Clinic 偏 389 米、Young Drivers of Canada 偏 260 米、City Centre Auto Service 偏 779 米。判定方法是：同一条直街上门牌号与坐标近似线性，用该街 13 条实测记录拟合直线（残差 21 米），偏离超过 200 米的即为坐标借用了别处。修正后的坐标标记为 `precision:'low'`（由本项目自己的实测记录推算，不是实地测量）。这些记录的地址一直是对的，导航按钮用的也是地址，所以导航从未出错——错的只是地图上的那个点。
  - Summit Medical Clinic 与相邻药房门牌相差 170 号却只有 3 米，坐标显然是借来的，同样降级标注。
- **三条新记录**（均来自官方/第一方页面，标记为待实地核实）：{CITY} Food Bank（171 Wilson St，凭家庭成员身份证件领取，不看移民身份）、St. Andrew's on the Square（1887 年，全市最古老的公共建筑）、The Old Courthouse（1909 年，现为艺术与社区活动场地）。Salvation Army 那条的备注补上了社区服务的实际内容（紧急食物包、衣物家具代金券、每周两次流动厨房）。
- **校验与回归同步加强**：`validate.py` 新增主题轴校验（键存在、五语言齐全、有图标、顺序正确、没有空主题）、`sameComplex` 对称性校验、以及两项坐标校验——同街不同门牌却相距 30 米内，和"用该街实测记录拟合直线后偏离超过 200 米"。第二项的第一版用普通最小二乘，被数据里的坏点自己把容差撑大到 590 米，反而放过了 231 米的错误；现在改成迭代剔除（拟合→剔除超过中位残差 3 倍的点→重新拟合），这才把剩下两条揪出来。`regress.py` 从 112 项增加到 149 项，新增主题轴、坐标诚实性、指南目录三组浏览器实测。

**English**

- **The newcomer guide is substantially expanded** — from 4 sections to 27, in all five languages. What went in was chosen by where people actually get stuck on arriving in a new country, not by administrative sequence: building credit from zero (a new arrival doesn't have *bad* credit, they have *no file*, and applications are declined regardless of what they owned back home); **your right to a free interpreter** (200+ languages, 24 hours, at no cost to the patient through the provincial health system; 130+ on 8-1-1 — the most under-used right newcomers have, and the single line this round most wanted to surface); filing a tax return even with zero income (the GST credit and the Canada Child Benefit are *calculated from* the return, so not filing means receiving none of it); a Canadian résumé carrying no photo, age or marital status, ways through the "Canadian experience" catch-22, and licensing for regulated professions; the proper waitlist and the alternatives when you cannot find a family doctor; the floor tenancy law gives you (half-month deposit cap, one increase per 12 months, three full months' written notice, a 2.3% cap for 2026), rental scams, and renting without local credit history; **what to do about discrimination, harassment or unfair treatment** (the protected grounds and areas, writing it down, the one-year limit, the free complaint route, and how to judge "is this even discrimination?"); international students' 24-hour weekly work limit, the insurance gap, post-graduation permits and academic integrity; food banks, 2-1-1, rent banks and income assistance when money runs short; **a match-the-problem-to-the-door table** for the commonest newcomer difficulty, which is not a lack of services but not knowing which body handles a given thing; and loneliness, homesickness and belonging — including that an accent is not a defect, the quite predictable settings where people here actually make friends, and permission not to fully assimilate. The city tier gained the local settlement agency, living here without a car, TRU, wildfire smoke in summer and what winter actually requires, and local ways to save money.
- **A guide index.** The content is six times longer, so an index is generated at the top from whatever headings the four tiers render; tapping one scrolls to that section and marks it. Because it is built from the headings, a new section in any tier appears in the index automatically, in every language.
- **A second, overlapping filter axis: themes.** A place has one category (it decides the pin's colour and icon, so it cannot be a list) and any number of themes: Daily Life, Kids & Family, Fun & Leisure, Scenic Spots, History, Arts & Culture, Free & Low-cost, Multicultural, Student Life, Indoor/Winter. Themes stack with categories and areas, and ticking two means both. They appear in each place's popup — so the axis is discoverable without opening the filter panel — are searchable by name in the reading language, ride in the shared URL, and each gets its own removable chip. Assignment is scripted in `tools/themes.py`; every per-record exception carries the evidence from that record's own verified note, and Scenic and History are never inferred from a category alone.
- **Two new categories:** Food Bank and Heritage Sites.
- **Data accuracy — the substantial part of this round:**
  - `precision:'low'` had been in the data on 22 records and was never rendered, so a pin 100 m off the door looked exactly as confident as one surveyed to the metre. The popup now says so in five languages, and says the address is the accurate part and what the Directions button uses.
  - `sameComplex` was dead too — only the two Costco rows used it — leaving nine pairs of markers stacked on one coordinate looking like duplicate data. It is now populated across 11 groups and 23 records, and the popup names the neighbour, so "the postal counter is inside that pharmacy" reads as what it is.
  - **Five coordinates were proved wrong and repaired:** Scotiabank (Victoria St) by 498 m, TD Canada Trust (Victoria St) by 411 m, Okanagan Thompson Legal Clinic by 389 m, Young Drivers of Canada by 260 m and City Centre Auto Service by 779 m. Method: on a straight street, position is very nearly linear in the civic number; a line fitted through 13 surveyed rows on Victoria St reproduces them to 21 m rms, and anything more than 200 m off that line has a coordinate borrowed from somewhere else. Repaired rows are marked `precision:'low'` because a fitted position is derived from this project's own surveyed rows, not surveyed itself. Their addresses were always right and Directions uses the address, so navigation was never wrong — only the picture was.
  - Summit Medical Clinic sat 3 m from a pharmacy 170 civic numbers away, which is impossible; its coordinate is demoted for the same reason.
- **Three new records**, all from an official or first-party page and marked pending an in-person check: the {CITY} Food Bank (171 Wilson St; ID for each household member, immigration status not screened), St. Andrew's on the Square (1887, the city's oldest public building) and The Old Courthouse (1909, now an arts and community venue). The Salvation Army note now states what its community services actually are.
- **Checks kept pace.** `validate.py` gained theme-axis invariants (keys exist, five languages, an icon each, correct order, no empty theme), `sameComplex` symmetry, and two coordinate checks: same street with different civic numbers within 30 m, and deviation from a street's own fitted geometry. The first version of that second check used plain least squares — the bad rows were inside the sample, dragged the line toward themselves and inflated the tolerance to 590 m, which let a 231 m error through. It now iterates (fit, drop residuals past 3× the median, refit), and that is what caught the last two. `regress.py` went from 112 checks to 149, adding browser coverage for the theme axis, coordinate honesty and the guide index.

## 2026.09.07d

**中文**

- 页面上的「更新记录」整体移除：指南底部的版本变更列表、指南按钮上的「有更新」红点、以及指南顶部的跳转链接都已删除，五种语言的相关文案、CHANGELOG 数据数组和渲染函数一并从代码里清掉，构建产物因此小了约 29 KB。变更历史继续保留在仓库的这个文件里，只是不再对访问者展示。
- 配套清理：回归测试里针对更新记录的 2 项断言同步删除（功能已不存在，留着只会让套件崩在找不到的元素上）；`tools/gen-changelog.py` 及 `deploy.sh` 里的漂移检查一并撤除，因为它们的数据来源已经不在了。

**English**

- The change log is gone from the page: the version list at the bottom of the newcomer guide, the "something is new" dot on the guide button and the jump link at the top of the guide have all been removed, along with the five-language strings, the CHANGELOG data array and its render function. The built file is about 29 KB smaller. The history itself stays in this file — it is simply no longer shown to readers.
- Follow-through: the two regression assertions covering the change log were deleted with it, since a test pointing at an element that no longer exists only crashes the suite; `tools/gen-changelog.py` and the drift check in `deploy.sh` were removed too, as the source they read no longer exists.

## 2026.09.07c

**中文**

- 新增分享面板：过去点「分享」只是把链接复制到剪贴板，现在会打开一个面板，可以直接发到 WhatsApp、Facebook、X、Telegram、LINE、邮件、短信，复制链接仍然排在第一个。手机上会多出「用系统分享」——调用手机自带的分享面板，里面列出的是你自己装了的 App，微信、KakaoTalk、TikTok 都能直接选到。分享出去的链接依然带着当前的语言、区域、分类和搜索词。
- 关于微信和 TikTok：它们没有提供「分享网页链接」的接口——微信在电脑上要扫码、在自家浏览器里要用需服务端签名的 JS-SDK，TikTok 的 Share Kit 是通过注册应用推送视频/图片而不是网址。所以面板里不做它们的按钮（做了也点不动），而是在说明里写清楚：手机用系统分享可直达微信，电脑上复制链接后粘贴。韩国的 KakaoTalk 同理。
- 分享埋点按平台细分：新增 share_open（打开面板，并记录该设备是否支持系统分享），share_click 沿用原有的 intent/result 两段式，但加上了 target 字段（copy / whatsapp / facebook / x / telegram / line / email / sms / native）。系统分享还会区分「分享成功」和「用户取消」——取消是正常结果而非失败，混在一起会让成功率失真。

**English**

- A share sheet. The Share button used to copy the link and stop there; it now opens a panel that sends straight to WhatsApp, Facebook, X, Telegram, LINE, email or Messages, with Copy link still first. On a phone there is also "Share via your device", which opens the OS share sheet — that lists the apps the reader actually has installed, so WeChat, KakaoTalk and TikTok are all reachable there. The shared link still carries the current language, area, category and search.
- On WeChat and TikTok: neither offers a share-a-link endpoint. WeChat expects a QR scan on desktop or a server-signed JS-SDK inside its own browser, and TikTok Share Kit pushes video or photos through a registered app rather than a URL. Rather than add buttons that could not work, the sheet says plainly what to do: use the device share sheet on a phone to reach WeChat directly, or copy the link and paste it on a computer. KakaoTalk is the same.
- Share telemetry is now per destination: share_open records opening the sheet and whether the device supports the native sheet; share_click keeps the existing intent/result staging and adds a target field (copy / whatsapp / facebook / x / telegram / line / email / sms / native). The native path also separates a completed share from a dismissed one — dismissing is a normal outcome, and folding it into failures would distort the success rate.

## 2026.09.07b

**中文**

- 公交站名标签重新按文字实际宽度做碰撞检测：此前退回成了「固定 58 像素距离」，长站名（如 Lansdowne Exch Bay I）需要的间距是短站名的三倍，一个固定值不可能同时正确，14 条线路实测有多处标签互相压字。同时修掉两个更隐蔽的问题——被隐藏的标签宽度读数为 0，会被误判成「放得下」而反复弹回来；以及同一条环线两次经过同一换乘站时，两个同名标签直接叠在一起。现在 14 条线路标签互压为 0，显示的站名反而更多
- 恢复「记住你选过的语言」：手动切换后会记在浏览器里，下次不带 ?lang= 参数打开仍是你选的语言。链接里明确带的 ?lang= 依然优先。此前这个功能在改版中丢失，每次重开都会退回浏览器语言
- 恢复「有更新」提示：更新记录其实一直在维护，但它排在新居民指南的最底部——实测要滚约 12 倍面板高度才看得到，回访的人根本无从知道改过什么。现在指南按钮上有红点（打开一次即消失，版本变化后再出现），指南顶部有一键跳转链接
- 分类配色修复：医院与亚洲超市此前图钉色和文字色完全相同，汽车维修与法律援助的文字色也相同——而分类面板本身是当作地图图例用的，颜色撞车会让图例失效。另外出租车/室内儿童乐园/租房中介三个颜色与白字对比度低于代码自己声明的 4.5:1，一并调深
- 「跳到主内容」快捷链接的高度从 39 像素提到 44 像素，这是全站最后一个未达触控标准的控件
- 隐私说明改写：此前把上传内容列成「事件类型＋时间戳＋会话 ID」三项，但实际上搜索框里输入的文字也会上传（去掉连续数字并截断后）；那个标识符也不是一次性的，它存在浏览器里、下次访问仍是同一个。现在如实说明，不再用封闭式列举

**English**

- Bus stop labels are measured by the width the text actually takes again. The check had been reduced to a fixed 58-pixel distance, but a long name like "Lansdowne Exch Bay I" needs roughly three times the clearance of a short one, and across the 14 routes labels were drawing over each other. Two subtler faults went with it: a label hidden by the previous pass reports a width of 0, so it looked like it fit anywhere and kept popping back; and a loop route that passes the same exchange bay twice stacked two identical names on the same spot. Overlaps across all 14 routes are now zero, and more stop names are visible than before
- The language you pick is remembered again — switch manually and the next visit without ?lang= opens in that language; an explicit ?lang= in a shared link still wins. This had been lost in a rewrite, so every reopen fell back to the browser language
- The "something changed" cue is back. The change log is maintained but sits at the very bottom of the newcomer guide — measured at about 12x the panel height of scrolling — so a returning reader had no way to discover it. The guide button now carries a dot (cleared once opened, back when the version changes) and the guide opens with a jump link to it
- Category colour repairs: Medical and Asian Market had identical pin and text colours, as did Auto Repair and Legal Aid — and the category panel is explicitly offered as the map legend, which collisions break. Taxi, Indoor Play and Rental agents also sat below the 4.5:1 on white that the colour table itself promises, and were darkened
- The skip-to-content link grew from 39 to 44 pixels tall — the last control on the page still under the touch-target minimum
- Privacy note rewritten. It listed what is uploaded as "event type + timestamp + session ID", but the text typed into the search box is also sent (digit runs stripped, truncated), and the identifier is not per-visit: it lives in your browser and stays the same next time. It now says so plainly instead of giving a closed list

## 2026.09.07

**中文**

- 修复整页文案空白：2026-09-05 新增的 4 条记录用了 CI 里不存在的分类 key（rec/community/cafe/liquor），popup() 取 CI[分类][语言] 抛异常，而所有弹窗是在启动时一次性构建的，于是这一条坏记录让初始化循环中途死掉——标题、按钮文字、快捷选择、地点计数全部没写进页面，只剩一个空壳。同一批改动里还有第二个被它掩盖的崩溃：面板焦点陷阱那行 backdrop.addEventListener 写在 const backdrop 声明之前，触发暂时性死区。两个都已修复
- 正式新增两个分类：☕咖啡店、🍷酒类专卖（五种语言标签、地图图钉色、文字安全色、归入购物餐饮组）。Westsyde Community Hall 按 DATA-SCHEMA 定义归入既有的「社区中心」；「Westsyde Pool & Fitness Centre」和一条重复的「Westsyde Centennial Park」是与既有记录同地址的重复条目，已删除
- 新增第四档来源标签「未核实（建议致电确认）」：补覆盖缺口时新增、尚未逐项电话核实的记录，此前带着 CI 不认识的 src 值，结果一个来源标签都不显示——最没核实的记录反而看起来最干净。现在会明确提示读者先打电话确认，且这些记录仍然不会进入对外开放的数据子集
- 删除深色模式：只给面板换肤、地图底图仍是亮的，深色边框里嵌一块白地图并不好看；同时页面显式声明为 light-only，微信等内置浏览器的自动深色转换不会再把文字变成看不见的浅色
- 修复源数据文件被自动编辑改坏的两处：地点数组丢了赋值前缀（const P 那一句）（任何重新构建都会得到空地图）、文件头注释被拼接成一行
- deploy.sh 增加静态校验闸门：validate.py 不通过就不部署。9-05 那次上线的 19 项校验失败，validate.py 本来全都能查出来，只是从来没被放进部署路径

**English**

- Fixed the blank-interface bug: four records added on 2026-09-05 used category keys absent from CI (rec/community/cafe/liquor). popup() reads CI[category][lang], every popup is built in one pass at start-up, and so a single bad row killed the init loop midway — title, button labels, Quick Picks and the place count were never written, leaving an empty shell. A second crash in the same batch was masked by the first: the panel focus-trap line called backdrop.addEventListener above the const backdrop declaration, a temporal-dead-zone ReferenceError. Both fixed
- Two categories added properly: ☕ Cafés and 🍷 Liquor Stores (labels in five languages, a map-pin colour, a text-safe colour meeting 4.5:1 on white, and membership of the Shopping & Dining group). Westsyde Community Hall moves into the existing Community Centre category, which is where DATA-SCHEMA already puts halls; "Westsyde Pool & Fitness Centre" and a second "Westsyde Centennial Park" duplicated existing records at the same address and were removed
- A fourth source tier — "Unverified — call ahead". Entries added to fill coverage gaps but not yet phone-checked were carrying a src value no tier recognised, so they rendered no provenance chip at all: the least-verified rows looked the cleanest. They now tell the reader to confirm first, and still stay out of the openly-licensed export
- Dark mode removed: it re-skinned only the chrome we own while the OSM basemap stayed bright, which put a white map inside a dark frame. The page now declares itself light-only, which also stops in-app browsers (WeChat especially) applying an automatic dark transform that turned text unreadable
- Repaired two corruptions a bad automated edit left in the data file: the places array had lost the assignment that names it (any rebuild would have produced an empty map) and the header comment had been joined into one line
- deploy.sh now runs validate.py as a hard gate. All 19 failures that shipped on 09-05 were things validate.py already catches — it simply was never part of the deploy path

## 2026.09.05b

**中文**

- 埋点可区分维护者流量与真实用户：以 ?debug=1 打开页面的所有事件，以及每次部署后的自动化冒烟测试，都会标记 env:dev 并写入独立的数据列。分析时用 double2=0 只看真实用户，避免测试用的假地点 ID 混进「最常查看的地点」排名。分享按钮的埋点拆成 stage:intent（点击意图）与 stage:result（复制结果）两次记录——此前只发一条 copied:false 表示点击，回溯数据时被误读成一半的复制失败率

**English**

- Analytics can now separate maintainer traffic from real usage: any event from a page opened with ?debug=1, plus the automated post-deploy smoke test, is tagged env:dev and written to its own numeric column. Filter on double2=0 to see real users only, so hand-rolled test place IDs stop polluting the "most viewed places" ranking. The share button now logs two distinct events — stage:intent (the click) and stage:result (the copy outcome) — where it previously emitted a bare copied:false for the click, which read back as a 50% failure rate even though every copy succeeded

## 2026.09.05

**中文**

- 埋点接入 Cloudflare Analytics Engine（Phase A 上线）：trackEvent() 内部从「仅写 localStorage」改为「同时通过 navigator.sendBeacon 把事件发到 /api/event，Worker 写入 Analytics Engine」；25 处调用点全部不动。新增匿名会话 ID（kamloopsSid，localStorage 持久化）让服务端能识别同一浏览器的多次会话。搜索词脱敏规则保持不变；footer 加了一行小字说明匿名统计

**English**

- Click tracking upgraded to Phase A: trackEvent() now both writes to localStorage AND fires navigator.sendBeacon("/api/event") on every call, where the Cloudflare Worker records the row in Analytics Engine. All 25 call sites stay unchanged. Added an anonymous session ID (kamloopsSid in localStorage) so server-side queries can stitch events from the same browser. Search-query sanitisation is unchanged; the footer now carries a one-line privacy note

## 2026.09.04c

**中文**

- 新增点击埋点（本地版）：18 类事件统一走 trackEvent(type, props) 抽象——搜索、搜索无结果、分类（含 × 清除）、区域、快捷选择（含全部清除）、语言、收藏、面板打开/关闭、地图标记查看/关闭、popup 内导航/电话/网站按钮、分享、重置；本机 localStorage，?debug=1 可查看计数与导出 JSON；Phase A 接入 Cloudflare Analytics Engine 时只改 trackEvent 内部实现，调用点不动
- 搜索词在埋点层做脱敏：去除连续 3 位以上数字串并截断到 24 字符（Phase A 上传时将不含人名/电话/地址）

**English**

- Click tracking added (Phase B / local-only): 19 event types now flow through one trackEvent(type, props) helper — search, search-empty, category (incl. × chip clear), region, preset (incl. clear all), language, favorite, panel open/close, marker view/close, in-popup nav/call/web buttons, share, reset. 25 call sites in total (share_click uses 4 branches to cover execCommand / clipboard / failure paths). Stored on this device only; open ?debug=1 to see counts and export JSON. Phase A replaces the helper's internals with a sendBeacon — all 25 call sites stay untouched.
- Search queries are sanitised before storage: digit runs ≥3 chars are stripped and the term is capped at 24 characters, so Phase A server-side payloads cannot carry phone numbers, addresses or names

## 2026.09.04b

**中文**

- 接入 Cloudflare Web Analytics：无 cookie、不追踪个体用户，统计浏览量 / 来源 / 设备 / 加载性能等维度（数据 24-48 小时后可看）

**English**

- Cloudflare Web Analytics integrated — cookie-free, no individual tracking; tracks page views, referrers, devices and load performance (data visible 24-48h after integration)

## 2026.09.04a

**中文**

- 界面语言默认值恢复为硬编码英文——只有 URL 显式带 ?lang= 时才会切到其他语言，不再读取浏览器的语言设置（避免"分享链接给不同语言用户"的不可预测行为）

**English**

- Interface language default is back to hard-coded English — only an explicit ?lang= in the URL switches to another language (no longer reads the browser's language, which made the result unpredictable when a link was shared across users)

## 2026.08.31e

**中文**

- 搜索原本会完全绕开已选的区域/分类筛选；现在会在筛选范围内缩小结果，筛选范围内搜不到时会明确说明原因，并提供一键清除筛选
- "快捷选择"里的🧳选项原叫"新居民必看"，和顶部📖"新居民指南"按钮撞名——已改名为"新居民必备"
- 区域内数量为0的分类原本会从分类面板直接消失，容易被误解成"这个工具根本不收录这类地点"——现在会保留在列表里，显示"(0)"并变灰，附悬停说明
- 首次使用的提示语补充说明了搜索、快捷选择（可多选、会自动帮你选分类）和区域/分类筛选之间的关系
- 界面语言默认值原本硬编码为英文——现在会先读取浏览器语言设置（链接里带的 ?lang= 仍然优先）
- 分类筛选面板的说明文字里加了一句：这份列表的颜色/图标和地图图钉一一对应，可以当图例用
- 弹窗信息顺序调整：地点名称排到最前面，分类/区域标签移到名称下方，不再抢在名字前面
- 收藏的"导出/导入"改名为"复制代码/导入代码"，并明确说明不会下载文件，只是一串可以复制粘贴的文字
- 公交面板新增一句说明：选中线路只是把它画在地图上，和当前显示的地点共存，不会筛选或隐藏它们
- "数据说明"从一整段文字拆成三个带标题的小节（数据来源与覆盖范围 / 实用提醒 / 核实日期与免责声明），文字内容本身一字未改
- 弹窗里地点自己的"信息核实于"日期新增悬停说明，指出它和"数据说明"里的整体核实日期是两回事
- 三色来源标签中"第三方地图数据"这一档，把"建议致电确认"直接写进标签本身，不用再悬停才能看到
- 地图上的聚合圆圈新增悬停提示，说明数字含义和点击可展开
- "快捷选择"支持多选这件事写进了提示语；手动调整过的芯片原本只有一个"·"符号加悬停提示，现在直接显示"(已调整)"文字
- 分类筛选面板说明补充：不勾选＝显示全部，勾选＝只看这些，没有单独隐藏某个分类的功能
- "重置"按钮加了悬停说明，指出它不仅重置筛选，也会清空搜索/公交线路选择并让地图回到初始视角
- 页脚里的 911/8-1-1/RCMP 紧急电话原本和普通的资料来源链接挤在一起——现在用醒目的浅红色单独标出
- 新增"🔗分享"按钮：一键复制当前链接（带着语言、筛选和搜索词）——这个能力其实一直都在，只是从没有入口
- 面板顶部的拖动手柄第一次打开时会轻轻晃动一下，提示它可以往下拖动关闭
- 自查时发现：新增的"分享"按钮让顶部四个链接在手机宽度下换行成两行，挤掉了地图的可视高度，在部分语言/尺寸组合下跌破了既定下限；同时变长的首次提示语在中等高度的手机上也多占了一行。已将四个链接在窄屏下收成纯图标（保留可点击区域与朗读文字），并收紧了提示语的行距——20 项手机宽高×语言组合全部恢复达标，触控热区也重新量过，全部不小于 44px

**English**

- Search used to bypass the active Area/Category filters entirely; it now narrows within them, and a search that finds nothing purely because of the filter says so, with a one-tap way to clear it
- The 🧳 Quick Pick was labelled "Newcomer Guide" — identical to the 📖 Newcomer Guide button in the header. Renamed to "Newcomer Essentials" so the two are no longer indistinguishable
- Categories with zero matches in the selected area(s) used to vanish from the Category panel, reading as "not tracked" rather than "none here" — they now stay listed, muted, with a (0) count and an explanatory tooltip
- The first-run hint now explains how Search, Quick Picks (multi-select, sets Category for you) and Area/Category relate to each other
- The interface language defaulted to English regardless of the browser’s own language — it now reads the browser’s language first (an explicit ?lang= link still wins)
- The Category panel’s hint now says its colours/icons double as the map’s legend
- Popup layout reordered: the place name now leads, with the category/region tags underneath it rather than above it
- Favourites "Export/Import" renamed to "Copy Code/Import Code", and the note now says explicitly that no file is downloaded — it’s text you paste back in
- The Bus Routes panel gained a line explaining that selecting a route only draws it alongside whatever places are showing — it doesn’t filter or hide them
- Data Notes split from one paragraph into three labelled sections — Source & Coverage / Practical Notes / Last Verified & Disclaimer — with the legal wording itself unchanged
- The popup’s per-place "Verified" date now carries a tooltip explaining it’s a different thing from the page-wide "Last verified" date in Data Notes
- The "Third-party map data" source tier now says "— call ahead" directly in the visible label, not only in a hover tooltip
- Map cluster bubbles gained a hover tooltip spelling out what the number means and that they’re clickable
- The Quick Picks hint now says you can combine any number of them; a manually-adjusted preset chip now shows "(edited)" as real text instead of only a "·" with a hover title
- The Category panel’s hint now states plainly that nothing checked shows everything, and checking narrows — there’s no way to hide a single category
- The Reset button gained a tooltip explaining it clears search and the bus route too, and returns the map view, not just the filters
- The footer’s 911/8-1-1/RCMP line used to look like just another source citation — it now sits in its own tinted line, visually separated from the routine links
- Added a 🔗 Share button that copies a link to exactly the current view (language, filters, search) — the URL already carried all of this, it just never had a visible way to use it
- The bottom sheet’s drag handle gives a brief one-time nudge the first time a panel opens on a phone, hinting that it can be dragged down to dismiss
- Caught in verification: the new Share button pushed the header’s four links onto two lines at phone widths, eating into the map’s share of the screen and dropping it below the tested floor for several language/size combinations; the lengthened first-run hint added a similar line at medium phone heights. Both four links now collapse to icon-only below 600px (full names remain for screen readers) and the hint’s line spacing was tightened — all 20 tested phone width/height/language combinations pass again, and every tap target was re-measured at 44px or larger

## 2026.08.31d

**中文**

- 首次使用测试发现的十一个问题，逐一修复：快捷选择行原本几乎看不出能左右滑，六个分类因此形同隐形——现在滑动条纹清晰可见，且只在真的还有内容时才显示
- 收藏一个地点原本只有一个 16px 图标变色作为反馈，容易误以为没点中而再点一次、白白取消收藏——现在会弹出一条简短提示
- "地图加载不出来"的提示条原本一直盖住地图最显眼的位置；6 秒后自动收成右下角一个小圆点，点一下可展开
- 搜索时快捷选择的按钮看起来还能点，其实早已被忽略——现在会同步变灰
- 所有弹出面板（新居民指南、数据说明、地区/分类/公交/收藏）原本背景页面会跟着一起滚动——现已锁定，这也让公交面板里"为何跳过 8/11/12 号线"的说明终于能被滚动到
- 公交路线选中后，多个站名标签会互相压字——现在会避开所有已显示的标签，而不仅仅是紧邻的前一个
- 分类筛选面板新增一行说明：点组名展开子分类，勾选组前的框可整组选中
- 数据说明页新增一处分段，把公交/票价信息和公寓/营业时间提醒分开成段
- 收藏为空时，"导入"区域原本没有任何说明——现在补充了一句解释它是给换设备的人用的
- 筛选提示语补上了对快捷选择行的提示
- 用回归测试自查时，发现这一轮改动本身弄坏了一处测试：离线提示条的测试原本直接改它的显示状态，绕过了新加的"自动收起"记录，导致测试踩到真实代码根本不会出现的状态而报错——已改为让测试调用和真实代码一样的函数，并单独为收起后的小圆点补了测试

**English**

- Eleven problems found in a first-time-user pass, fixed one by one: the Quick Picks row barely hinted it could scroll, so six of nine categories were effectively invisible — the fade and arrow are now genuinely visible, and only appear while there truly is more to scroll to
- Favouriting a place gave no feedback beyond a 16px icon changing colour, which invited a second tap that silently un-favourited it — a brief confirmation now appears
- The "map imagery can't load" banner used to sit over the busiest part of the map indefinitely; it now shrinks to a small corner badge after 6 seconds and expands again on tap
- Quick Picks chips still looked tappable during a search even though the results notice said filters were being ignored — they now grey out to match
- Every overlay (Newcomer Guide, Data Notes, and the Area/Category/Bus Routes/Favorites sheet) let the page underneath scroll along with it — now locked, which also finally makes the Bus Routes panel's existing "why 8/11/12 are missing" note reachable by scrolling
- Bus stop labels on a selected route could overlap each other; each label now keeps clear of every label already shown, not just the previous one in sequence
- The Category filter panel — the one overlay with real hidden structure — gained a one-line hint on the two gestures it needs (tap a group to expand, check its box to select it whole)
- Data Notes gained one more paragraph break, separating the transit/fare aside from the apartment-rent reminder
- The empty Favourites panel showed an Import box with no explanation of why — it now says plainly that it's for a code exported from another device
- The filter hint text now mentions the Quick Picks row, not just Area/Category
- Self-check via the regression suite caught one thing this round's own work broke: its test for the offline banner set the element's visibility directly, which skipped the new auto-compact bookkeeping and started failing on a stale state the real code never actually produces — fixed by having the test call the same function every real caller uses, and a dedicated check was added for the compact badge itself

## 2026.08.31c

**中文**

- 地点备注补齐法语、西班牙语和韩语——221 条全部翻译，法/西/韩读者不再看到英文
- 搜索现在也能搜到当前语言的备注（备注一翻译，搜索自动跟上）
- 物业管理公司从「公寓租房」拆出，独立成「租房中介」分类：公寓从 18 条变回 14 条真实楼盘
- North Shore Community Centre 从「政务移民」移到「社区中心」——它本来就是社区中心
- 备注很长的地点，弹窗不再高过地图；此前在 320px 屏幕上会自己关掉
- 新增外链失效检查脚本（需在能联网的机器上运行）

**English**

- Place notes now exist in French, Spanish and Korean — all 221 translated, so those readers no longer get the English text
- Search reaches the notes in whatever language is showing, which came free with the translation
- Property managers split out of Apartments into their own category: the apartment count is 14 real buildings again, not 18
- North Shore Community Centre moved from Government to Community Centres, which is what it is
- Popups with long notes no longer grow taller than the map; on a 320px screen they used to close themselves
- Added a link-checker script for the 150 external websites (run it on a networked machine)

## 2026.08.31b

**中文**

- 18 个公园、步道、狗公园和沙滩不再声称「24 小时营业」，改为「开放时间见现场告示」——市政公园几乎都有条例规定的关闭时段
- Kamloops Immigrant Services 原本重复成两条记录（分属两个分类，坐标相差 1.4 公里），已合并；旧收藏仍然有效
- 4 条记录的地址里混着中文括注，非中文读者看不懂，已移进双语备注
- 收藏可以导出成一串文字自己保存，换设备或清理浏览器后再导入——不上云，不建账号
- 弹窗在 320px 的老手机上不再超出屏幕
- 手机上的按钮加大到便于单手点按的尺寸
- Canada Games Aquatic Centre 等场馆从「请致电」改为「详见官网」，官网本来就有时刻表
- 三条备注里的「新移民」改为「新居民」

**English**

- 18 parks, trails, dog parks and beaches no longer claim to be open 24 hours; they now say hours are posted on site, since municipal parks almost always have a bylaw closing time
- Kamloops Immigrant Services had been listed twice, in two categories, with coordinates 1.4 km apart; the records are merged and existing favourites still resolve
- Four records carried Chinese parentheticals inside the address field, unreadable for four of the five audiences; moved into the bilingual note
- Favourites can be exported as a short line of text and imported on another device or after clearing the browser — no account, nothing uploaded
- Popups no longer run off the edge of a 320px phone
- Controls on phones are large enough to hit one-handed
- Venues like Canada Games Aquatic Centre now point at their published timetable instead of saying "phone to confirm"
- Three notes still said 新移民 (new immigrant); the house wording is 新居民 (new resident)

## 2026.08.31

**中文**

- 公交数据全量核对官方 GTFS：14 条线路、475 个站点全部一致；查明本市根本没有 8/11/12/15 号线，说明文字已改写
- 弹窗打开时不再被地图的缩放按钮和版权链接穿透（此前可以点到，会把背后的地图放大或直接跳走）
- 修正地址栏参数校验：像 ?lang=constructor 这样的链接不再让页面变成空白
- 地图归属改为「© OpenStreetMap contributors」并加上版权页链接
- 数据说明里新增隐私说明：本页不收集任何信息，唯一的对外请求是地图底图
- 改用系统字体，去掉最后一个第三方请求，离线时字体也不再变形
- 修正六处过小或过浅的文字，全部达到 WCAG AA 对比度
- 收藏星标现在会告诉读屏软件「已收藏 / 未收藏」
- 手机上底部面板可以向下拖动关闭了（顶部那条横杠一直在暗示这件事）
- 手机上改用 dvh 计算高度，页面不再多出一截无用的滚动

**English**

- Bus data re-checked against the operator’s official GTFS feed: 14 routes and all 475 stops matched, and routes 8, 11, 12 and 15 turn out not to exist here at all — the copy now says so instead of implying a gap
- Modal dialogs are no longer punched through by the map’s zoom control and attribution link — both used to stay clickable, zooming the map behind or navigating away
- Fixed URL parameter validation: a link like ?lang=constructor no longer blanks the page
- Map attribution now reads “© OpenStreetMap contributors” and links to the licence
- Added a privacy note: this page collects nothing, and the map imagery is its only outbound request
- Switched to system fonts, removing the last third-party request and the last offline gap
- Fixed six pieces of text that were too small or too faint to meet WCAG AA contrast
- The favourite star now tells a screen reader whether it is on or off
- The mobile sheet can be swiped down to dismiss — the handle at its top had been promising that all along
- Mobile heights use dvh, so the page no longer carries a strip of dead scroll

## 2026.08.30

**中文**

- 全部 250 处地点的营业时间改为结构化数据，五种语言分别渲染，并明确标出休息日
- 移除所有硬编码的评分数字，改用 ⭐ 推荐标记
- 新增韩语；222 条备注补齐英文，法/西/韩回退到英文
- 分类筛选逻辑改为「未筛选 / 只看选中项」，不再是反向的排除逻辑
- 「重置」按钮改为常驻显示，并可一并清除公交线路与搜索
- 纠错入口带上地点名称、编号、分类与数据版本
- 地址栏记录当前语言、区域、分类与搜索词，链接可直接分享
- 指南拆为城市 / 省 / 国家三层；新增授权与署名说明（{LIC}）
- 地图库改为内置，无网络时除底图外全部功能可用
- 每条记录标注数据出处：登记了机构官网的显示「机构官网」，其余显示「第三方地图数据」
- 弹窗可读性修复：法语/西语标签不再和内容挤在一起；弹窗不再被缩放按钮遮住店名

**English**

- All 250 records now carry structured opening hours, rendered per language, with closed days stated rather than implied
- Removed every hard-coded rating number in favour of a ⭐ recommended mark
- Added Korean; filled in English for 222 notes, with fr/es/ko falling back to English
- Category filtering is now "no filter / show only what is selected" instead of the inverted exclude logic
- Reset is always visible and now also clears the bus route and the search box
- Corrections now carry the place name, id, category and data version
- The address bar records language, area, category and search term, so a link can be shared as-is
- The guide is split into city / province / country tiers; added a licence and attribution notice ({LIC})
- The map library is bundled, so everything but the base map works with no network
- Every record now states where its details come from — the operator’s own site, or third-party map data
- Popup fixes: French and Spanish labels no longer run into their values, and the zoom control no longer covers the place name
