# Change log

<!-- 由 tools/gen-changelog.py 从 src/engine.html 生成，请勿手改。 -->
<!-- 改动写进 src/engine.html 的 CHANGELOG 数组，再跑一次这个脚本。 -->

当前版本：`2026.09.07c`

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
