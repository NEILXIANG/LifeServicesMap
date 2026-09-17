# Kamloops 生活服务地图 · 首次使用 UX 审计

> 一份以「完全不知道项目背景的新用户」视角，对 Kamloops Living Services Map 的首次使用体验、信息架构、交互模型与信任模型所做的全面诊断。
>
> 范围：从打开首页到完成一次搜索 / 筛选 / 收藏 / 切换语言的全路径。共六十节，未拆分。

---

## 一、总体结论

如果我是一个完全不知道这个项目背景的新用户：

第一次打开后，我大概能看懂"这是一个 Kamloops 地图"，但不一定马上理解"我应该从哪里开始"。

目前最大的问题不是功能不足，而是：

功能已经很多，但产品的"使用心智模型"还没有完全建立起来。

尤其是第一次使用时，会出现几个核心疑问：

- 我现在看到的到底是什么？
- 地图上的 250 个地点是不是全部？
- Area、Category、Quick Picks 三套筛选到底是什么关系？
- 搜索和筛选为什么不是同时工作？
- 点击地图 Marker 和点击 Cluster 后应该做什么？
- 公交到底是"地点"还是独立功能？
- Favorites 为什么不是账号同步？
- Newcomer Guide 与地图上的地点是什么关系？
- Data Notes 为什么有这么长的免责声明？
- 五种语言是不是所有内容都完整翻译？
- "View X places"到底是确认按钮还是应用筛选？
- 我怎么知道某条数据是否可信？
- 为什么有些地点有官网，有些没有？
- 为什么搜索后 Area/Category 看起来还在那里，但实际上失效？
- 在手机上，地图、列表、筛选面板之间的关系是什么？

因此目前属于：

功能比较丰富，但首次使用的"引导性"和"信息架构解释"仍有明显提升空间。

---

## 二、第一次打开：第一印象问题

当前首页结构大致是：

Header → Search → Area / Category / Bus / Favorites → 状态 → Quick Picks → Hint → Map → Footer。

**问题 1 🔴：第一视觉重点不够明确**

用户看到的是：

- 标题
- 语言
- 搜索
- Area / Category / Bus / Favorites
- Quick Picks
- 地图

功能很多。

但是新用户不知道："我第一步应该做什么？"

虽然有："Filter by area, then category · Click markers for details"

但这句话把用户引导到：Area → Category

实际上页面还有：Search、Quick Picks、Bus、Favorites、Newcomer Guide

所以产品实际存在多个入口，却只告诉用户一种操作方式。

---

## 三、标题和产品定位仍然存在理解成本

当前标题：

- Kamloops Living Services Map
- 中文：Kamloops 生活服务全景地图

用户仍然可能不知道："这是什么地图？"

例如新移民可能理解成：

- 普通 Google Maps？
- 还是 Kamloops 官方地图？
- 还是华人地图？
- 还是生活服务目录？

虽然 Data Notes 后面明确解释这是个人整理资料，但第一次进入时没有立刻建立"这是一个精选城市生活信息工具"的认知。

当前说明里明确写了这是个人整理、不是官方发布。

**问题**：免责声明承担了太多"产品定位解释"的任务。

---

## 四、最明显的首次使用问题：Area / Category / Quick Picks 三套入口

这是目前我认为最值得优先解决的交互问题之一。

页面同时存在：

① Area —— Filter by Area

② Category —— Filter by Category

③ Quick Picks —— 例如：

- Daily Essentials
- Newcomer Guide
- Family & Kids
- Sports
- Education
- Health
- Outdoors
- Shopping
- Transport

代码中 Quick Picks 实际上会映射到多个 category。

对于新用户："Quick Pick 是不是另一种 Category？" 这是非常自然的疑问。

---

## 五、Quick Picks 的逻辑不够直观

比如用户点击：🧳 Newcomer Guide

系统实际上选中了：

- Government
- Bank
- Post
- Secondhand
- Apartment
- Property Management
- Hardware
- Transit
- School Bus
- Hospital
- Asian
- Driving
- Religious
- Community Centre
- Legal

用户却看不到这个关系。

所以第一次点击 Newcomer Guide，用户可能以为：打开"新居民指南"。

实际上它是：一个预设筛选器。

而真正的 Newcomer Guide 又是顶部另外一个按钮。

于是出现：两个"Newcomer Guide"

- 一个是 Quick Pick
- 另一个是 📖 Newcomer Guide

这是典型的命名冲突 / 心智模型冲突。

---

## 六、Quick Picks 可以多选，这一点新用户很难发现

代码允许：`selPresets.add()` 也就是说 Daily + Kids 可以同时选择。

但是 UI 并没有明显告诉用户："可以选择多个快捷组合，结果会合并。"

这属于：隐藏交互能力。

用户很容易把它理解成：单选菜单。

---

## 七、Quick Pick 被手工修改后的状态非常难理解

当前有：`active`、`adjusted`

也就是说：先点击 Newcomer Guide，再手工修改 Category，系统知道 preset 被调整了。

但是普通用户很难理解："为什么这个 Quick Pick 现在不是原来的状态？"

这是产品内部状态暴露给用户的问题。

---

## 八、Area 筛选的"全选 / 部分选择"逻辑容易产生疑惑

Area 里面：All Areas，以及 Aberdeen、Brocklehurst、Downtown、Sahali……

用户选择一个区域以后：All Areas 状态改变。

如果把最后一个区域取消：代码会自动恢复 All Areas。

技术逻辑合理。

但是 UX 上："我明明把最后一个选项取消了，为什么地图又显示全部？"

用户很可能认为：操作失败。

这是一个典型的：业务逻辑正确，但用户心智模型不正确。

---

## 九、Category 筛选的复杂程度偏高

Category 使用：Group → 子 Category

例如：

- Education
  - School
  - Elementary
  - Tutor
  - Library

并且 Group 自身还有：全选 / 部分选择 / 未选择 三个状态：✓、–、空

代码中确实实现了这三个状态。

对于高级用户很好。

对于第一次用户：三个状态是什么意思？尤其 "–" 没有解释。

---

## 十、Category 的"清空"与"全部分类"概念容易混淆

目前：All Categories 和 Clear All 并不是完全相同的概念。

实际上：`aC.size === 0` 意味着：不限制分类；而不是：不显示任何分类。

这对于程序来说合理。

但普通用户可能理解：清空分类 = 不显示任何地点。

实际上：清空 Category = 显示所有 Category。

虽然页面文字可能有所解释，但这个概念非常反直觉。

---

## 十一、Search 与 Filter 的关系是一个重要 UX 问题 🔴

当前代码明确规定：搜索时 Area / Category 被忽略。

页面也会显示：Searching · area and category filters ignored

这是已经修复过的问题。

但从新用户角度：用户很自然会这样做

- Area = Sahali
- Category = Grocery
- Search = Walmart

他期望：在 Sahali 搜索 Walmart。

实际结果却是：搜索整个城市。

这可能是整个产品目前最重要的交互逻辑问题之一。

---

## 十二、搜索框没有充分解释"搜索范围"

Placeholder：Search name, address, category or notes…

这个已经很好。

但用户不知道：搜索是不是全城市？也不知道：搜索会不会受 Area / Category 影响？

当前 UI 是通过：Searching · area and category filters ignored 来告诉用户。

但这是：事后解释。而不是：事前预期管理。

---

## 十三、搜索至少两个字符，会让部分用户困惑

代码：`MIN_QUERY = 2`

所以输入 A 不会正式搜索。

系统会提示：Type at least 2 characters

逻辑合理。

但新用户可能会想："为什么我输入 A 没反应？" 尤其英文用户。

---

## 十四、搜索结果自动移动地图，存在"地图被抢走"的感觉

搜索结果 1–40 会自动：`fitBounds`

如果只有一个：自动定位并打开 Marker。

功能上合理。

但用户如果正在浏览地图：搜索一次，地图可能突然移动。

虽然代码已经保存原始地图位置，清空搜索时恢复。

但：第一次搜索时突然改变地图视角，仍可能造成"地图怎么自己动了"的感觉。

---

## 十五、地图 Marker 对新用户来说信息密度仍然很高

现在有 250 个地点。

代码已经增加 clustering：低缩放聚合、高缩放 spiderfy。

这已经解决了严重的 Marker 堆叠问题。

但第一次打开地图：用户仍然不知道这些点分别代表什么。

如果没有点击：他无法快速建立颜色 / 图标 / 分类的对应关系。

目前缺少明显的：Map Legend / 图例。

这是一个比较明显的问题。

---

## 十六、Marker 图标的语义可能不够自解释

用户看到：彩色 Marker，可能不知道

- 红色是什么？
- 蓝色是什么？
- 图标代表什么？

尤其地图本身不是用户熟悉的 Google Maps 标准符号。

因此：没有 Legend 是明显的信息缺口。

---

## 十七、Cluster 点击后的心理预期可能不一致

Cluster 显示："12 places, click to expand"

用户点击以后：地图可能放大 / 展开。

但没有明确告诉："这个数字是地点数量，不是搜索结果数量。"

容易理解成：12 家同类商家？

实际上可能是：不同 Category 的 12 个地点。

---

## 十八、点击 Marker 后 Popup 信息很多

Popup 包括：

- Category
- Area
- Tag
- Name
- Address
- Phone
- Email
- Hours
- Notes
- Source
- Verified
- Report
- Directions
- Call
- Website

从信息完整性来说很好。

但从第一次使用来说：一个地点详情页面承担的信息太多。

用户真正第一眼需要的通常只有：

- Name
- What is it?
- Where?
- Open?
- Phone?
- Website?
- Directions?

而：Source / Verified / Notes / Data status 属于第二层信息。

目前层级还不够明显。

---

## 十九、⭐ 收藏按钮仍然可能让第一次用户不知道"星星是什么"

虽然代码已经增加：`aria-label` 以及 `aria-pressed`（对无障碍是正确的）。

但视觉用户看到 ☆ 可能理解成：Rating，而不是 Favorite。

尤其你已经明确取消了硬编码评分数字，改成：Recommended。

那么 ⭐ 同时承担：Favorite 和 Recommended 两个视觉语义的风险仍然存在。

---

## 二十、Favorites 是当前最容易让用户困惑的功能之一

用户点击 ⭐ 收藏。

然后进入 Favorites，发现：这些收藏只存在这个浏览器。

代码已经非常诚实地说明了这一点，并提供 Export / Import。

但第一次用户仍然会问：

- "为什么没有登录？"
- "换手机以后还有吗？"
- "这个收藏是不是永久的？"
- "Export 是什么？"

---

## 二十一、Favorites Export / Import 的 UX 偏技术化

当前机制是：

Export → 一串文字 → 复制 → 换设备 → 粘贴 → Import

这是一个非常聪明的零服务器方案。

但：普通用户很难理解为什么要复制一串代码。尤其手机用户。

他们可能认为：导出 = 下载文件。

实际上：导出 = 生成字符串。

这是一个明显的 UX 心智模型问题。

---

## 二十二、Favorites 空状态说明位置合理，但教育性不够

当前：No favorites yet — tap ☆ in any place popup...

这已经很好。

但是第一次用户可能还没看到 Popup。

所以：用户必须先理解"地点 → Popup → ☆ → Favorite"这条链路。

---

## 二十三、Bus 功能的定位不够清晰

顶部：🚌 Bus Routes

但页面主体是：Map + Route + Stops + Service Hours + Fare

用户可能会问：这是公交地图吗？还是：普通地点地图里的一种 Category？

实际上它是：独立图层。这一点应该更明确。

---

## 二十四、Bus 与普通地点 Marker 的视觉关系可能造成混淆

用户选择公交线路后：路线、Stops 会出现在地图上。

但用户可能不知道：普通地点还在不在？还是：现在只看公交？

从代码来看公交 layer 是独立的，并不一定意味着地点过滤被清除。

这可能产生："我现在看到的到底是哪一层？" 的问题。

---

## 二十五、公交路线的颜色语义缺少解释

不同线路有不同颜色。

但用户不知道：颜色是官方颜色？还是：网站自己分配？是否代表：不同方向？不同路线？还是不同类别？

这需要更明确的视觉语义。

---

## 二十六、公交信息非常完整，但"实时公交"能力不存在

页面已经明确说：Live arrivals 请去官方 Transit。

这在法律和数据准确性上是正确的。

但是新用户可能看到 Bus Routes 以为可以：查实时公交。

点击后才发现：只能看静态线路。

因此：功能名称与用户预期存在潜在落差。

---

## 二十七、Newcomer Guide 的结构对新用户仍然不够明显

Guide 被拆成：City / Province / Country

代码中明确设计了：GUIDE_ORDER、guideCity、guideCA1、guideProv、guideCA2

架构是正确的。

但用户第一次看到 📖 Newcomer Guide，不知道里面到底有什么。

更重要的是：Guide 与地图之间缺少明显的双向连接。

例如："办理驾照" → 点击 → 显示附近 Driving / ICBC？

如果只是阅读文字：用户需要再次回地图搜索。

---

## 二十八、Data Notes 过长

这是一个非常明显的问题。

目前 Data Notes 同时包含：

- 数据来源
- 覆盖范围
- 非穷尽声明
- 公交说明
- 房租说明
- 营业时间说明
- 日期
- 非官方声明
- 准确性免责声明
- 责任限制
- 隐私说明

从法律角度可能有价值。

但从 UX：这是"数据说明"还是"免责声明"还是"隐私政策"？用户很难区分。

---

## 二十九、免责声明的"法律语气"会降低产品亲和力

例如："任何损失……由使用者自行承担……"

这对风险控制有价值。

但是第一次使用的普通用户可能感受到：这个网站是不是风险很高？

尤其：免费个人工具。

如果第一屏就强调：

- 不保证准确性
- 不承担责任
- 可能错过班车
- 可能多付费用

会削弱：Trust 和 Friendly。

---

## 三十、数据来源设计是优点，但用户不一定理解

当前有：

- Official site
- Third-party map data
- Checked in person

这是非常好的设计。

但：用户未必知道这三个等级意味着什么。

尤其："Third-party map data" 不是 "错误"，也不是 "不可靠"。

但普通用户容易把它理解成："这个数据可能不可信。"

需要更明确的视觉等级和解释。

---

## 三十一、Verified 日期存在，但用户不知道"验证什么"

Popup 显示：Verified

但这个 Verified 到底是：

- 地址？
- 电话？
- 营业时间？
- 所有信息？
- 官网？
- 仅仅某一次检查？

目前语义仍偏模糊。

---

## 三十二、最后核实日期是"全局日期"，容易被误解

页面有：Last verified: 2026-08-29

但用户可能理解：所有 250 个地点都是 8 月 29 日检查的吗？

实际很可能不是。

因此：全局 Data Version 和 单条 Place Verification 必须在 UX 上明确区分。

---

## 三十三、多语言：表面上已经很好，但还有"完整性认知"问题

目前支持：EN / FR / ES / 中文 / 한국어

代码中 UI 确实已经扩展到五种语言，而且大量 UI 已经翻译。

但是：数据内容并不是五种语言全部独立维护。

例如备注：`noteText(d)` 返回 `nt[L_]||nt.en||nt.zh||''`

意味着：法语 / 西班牙语 / 韩语缺失时回退到英文。

这对工程是合理的。

但用户可能不知道：为什么我切换成韩语，有些内容还是英文？

因此：语言切换成功 ≠ 内容完整本地化。

---

## 三十四、语言切换默认 EN 是非常值得注意的问题 🔴

当前 HTML 初始：

```html
<button class="lang-btn active" data-lang="en">EN</button>
```

并且初始化：`setLang(st&&st.lang?st.lang:'en');`

也就是说：默认语言是 English。

对于：中文用户，第一次打开：会看到英文。

对于：韩国用户，也是英文。

这对国际化产品是一个明显的 First-run UX 问题。

---

## 三十五、URL 语言逻辑虽然很好，但首次用户看不到它的价值

当前 URL 可以保存：lang、region、category、search、route

而且使用 `replaceState`，避免浏览器 Back 被大量筛选操作污染。

这是一个非常好的工程设计。

但是：用户不知道筛选后的页面可以直接分享。

因此这个能力目前是：Hidden Power Feature。

---

## 三十六、URL 分享还有一个用户心智问题

例如用户分享："这是我筛选出来的银行。"

朋友打开 URL 后：可以恢复筛选。很好。

但是：Favorites 不在 URL。这也是正确的隐私设计。

然而用户可能误以为："为什么我分享链接以后我的收藏没有过去？"

所以未来需要明确：Shared view ≠ Personal favorites

---

## 三十七、Reset 是正确的，但位置和意义仍需要教育

当前 Reset 会：

- 清 Area
- 清 Category
- 清 Search
- 清 Bus
- 关闭 Popup
- 关闭 Panel
- 恢复地图中心
- 恢复 Category 展开状态

这是一个很好的：Global Reset。

但是：它实际上比普通"Reset filters"更强。

用户可能以为：只重置筛选。实际：地图视角也重置。

所以名称 Reset 语义过于宽泛。

---

## 三十八、Footer 承担了过多功能

Footer 现在包含：

- 数据来源
- 学区工具
- Transit
- RTB
- 紧急电话
- 健康咨询
- RCMP
- Feedback
- License

从信息完整性很好。

从产品设计：Footer 已经变成一个"第二导航栏"。移动端尤其容易造成：页面很长。

---

## 三十九、紧急信息与普通生活信息混在一起

例如：911、8-1-1、RCMP

这些属于：Emergency / Safety

应该与：Data source / Feedback 形成更明显的层级。

否则用户真正遇到紧急情况时：不一定能第一时间找到。

---

## 四十、手机端：已经做了大量优化，但仍然存在信息密度问题

当前针对 320×568 等短屏幕已经做了专门处理。代码甚至在短屏幕下隐藏 hint、压缩顶部空间，并调整 touch targets。

这是很好的工程意识。

但是从第一次使用：顶部仍然有太多控制。

手机屏幕可能出现：

- Header
- Search
- Area Category Bus Favorites
- Status
- Quick Picks
- Map

结果：地图反而不是第一屏的主体。

这与："Map tool" 的核心价值存在冲突。

---

## 四十一、手机上的 Quick Picks 横向滚动不是所有用户都知道

代码明确做成：横向滚动。这是合理的。

但：没有足够明显的"还有更多"的视觉提示。

用户可能只看到前几个：Daily、Newcomer、Kids

然后以为：就只有这几个。

---

## 四十二、手机 Bottom Sheet 的"拖动关闭"虽然实现了，但发现性仍不足

代码已经实现：向下拖动关闭。

但这是典型：Discoverability 问题。

用户第一次看到：一个横杠，未必知道：可以拖。

---

## 四十三、手机上的 Popup 与 Bottom Sheet 存在两个"层级系统"

用户可能经历：

地图 Marker → Popup → Filter Sheet → Guide Modal

这些都是不同的交互层。

如果用户不知道当前打开的是：Popup / Sheet / Modal，就可能产生："为什么点一下没有反应？" 尤其：Map Popup + Sheet 同时存在时。

---

## 四十四、关闭行为不够统一

现在存在：

- X
- 点击背景
- Escape
- 下拉 Sheet
- 点击地图
- 点击其他按钮

多种关闭方式。

代码对 Escape 和 Modal 已经做得很好。

但从普通用户角度：每种弹层是否都能通过同样方式关闭？需要统一。

---

## 四十五、桌面端和手机端的交互模型差异比较大

Desktop：Panel

Mobile：Bottom Sheet

这本身是正确的 Responsive Design。

但意味着：同一个功能在两个设备上行为不同。

例如：点击地图之外关闭，Desktop 有明确逻辑；手机则更多依赖 Sheet / Backdrop。

第一次使用时可能有学习成本。

---

## 四十六、Accessibility 已经做得不错，但还有语义层问题

当前已经有：

- aria-label
- aria-pressed
- aria-expanded
- screen reader
- keyboard
- focus trap
- Escape
- touch targets

这些都是明显优点。

但问题是：Accessibility 不只是代码层面的 ARIA。还包括：用户是否理解控件的意义。

例如 "–" 即使有 aria-pressed：视觉用户仍然不理解。

---

## 四十七、数据准确性方面，最大的风险不是"明显错误"，而是"覆盖范围误解"

页面已经明确写：curated selection, not exhaustive 这是正确的。

但页面标题：Living Services Map 和 250 places，容易让用户产生："这是 Kamloops 全部服务吗？"

尤其：餐馆、加油站等只精选部分。

所以："250 places" 与 "全景地图" 的关系需要更清楚。

---

## 四十八、用户可能误解"所有区域都有数据"

页面写：covering all neighbourhoods

但：covering all neighbourhoods 不等于：每个 neighbourhood 每一种 Category 都有完整数据。

代码也确实会根据 Area 动态隐藏没有地点的 Category。

这可能让用户产生："为什么 Downtown 有这个分类，Sahali 没有？"

实际上可能只是：数据未收录 / 没有精选地点。

需要区分：No service 和 No data collected。这是数据产品非常重要的区别。

---

## 四十九、这是一个非常重要的数据语义问题 🔴

目前："没有地点" 可能有三种情况：

- A：确实不存在。
- B：存在，但没有收录。
- C：存在，但当前筛选范围没有匹配。

如果 UI 都表现成：0 places，用户会把 B 误认为 A。

这可能影响用户做真实生活决策。

---

## 五十、法律责任方面，目前不是"不够"，而是"结构需要更清晰"

目前已经有：

- 非官方声明
- 不保证准确性
- 使用风险
- 数据来源
- 最后核实日期
- License
- Privacy
- 外部请求说明

这已经比普通个人网站完整很多。

但是目前：Legal / Privacy / Data Methodology / Disclaimer 混在 Data Notes / Footer 中。

以后如果真的公开给几百 / 几千用户：需要拆成独立的内容结构。

---

## 五十一、第三方数据授权风险仍然需要进一步核查 🔴

页面当前说明：Google Places 以及 OpenStreetMap

同时代码设置：CC BY-NC 4.0

这里存在一个需要重点关注的问题：你自己的整理内容采用 CC BY-NC，并不自动意味着第三方来源数据也可以按这个 License 重新授权。

这不是 UI 问题，而是未来公开传播、商业化时非常重要的：Data provenance / licensing boundary 问题。

目前我建议把它列为：🔴 必须在正式公开前进一步核查。

---

## 五十二、Google Places 数据来源的用户表述需要非常谨慎

如果实际数据来自：Google Places，需要确认：

- 哪些字段来自 Google？
- 哪些字段来自官方网站？
- 哪些是你自己整理？

因为："数据来源：Google Places及官方网站" 容易被理解为：整个数据库都是可以自由再发布的公共数据。这是不准确的风险。

---

## 五十三、隐私说明很好，但"没有任何信息收集"需要保持严格一致

当前说明：本页不收集、不上传任何个人信息。

同时：OpenStreetMap tile server 会看到 IP。这个已经诚实说明。

未来如果加入：analytics、feedback form、error reporting、external fonts、CDN、API，就必须同步更新。

这意味着：隐私声明未来必须成为动态治理项目，而不是一次性文案。

---

## 五十四、语言切换之后 URL 会改变，但用户不一定知道

当前：language 会进入 URL。这非常适合分享。

但第一次用户可能看到：`?lang=ko` 不理解。

不是问题本身，而是：高级功能缺少产品说明。

---

## 五十五、浏览器返回键的体验值得重点测试

代码明确避免：每次筛选 push 一个 history entry。这是正确的。

但：用户改变语言 → 搜索 → 筛选 → 公交，这些变化是否完全符合 "Back 应该返回上一页，而不是撤销刚才的筛选" 这个产品哲学需要明确。

当前实现倾向：Back = 页面导航，而不是 Back = 撤销筛选。

我认为方向正确，但必须进行实际用户测试。

---

## 五十六、SEO 与分享虽然已经做了，但产品名称仍然不够有品牌感

现在：Kamloops Living Services Map 比较像：项目名称 / 技术工具名称。

如果未来复制：Kelowna、Vancouver、Calgary，需要考虑：用户为什么记住它？

目前更像：一个工具。而不是：一个产品品牌。

---

## 五十七、首次用户真正需要的是"任务入口"，目前仍然偏"工具入口"

当前：Search、Area、Category、Bus、Favorites 这是典型：Database UI。

但普通用户真实需求往往是：

- "我刚搬到 Kamloops，怎么办？"
- "孩子上学怎么办？"
- "我需要买菜。"
- "我没有车。"
- "我要找医生。"

所以目前：用户必须先知道分类，才能使用产品。

这与未来你希望它成为：City Living Intelligence 的方向还有差距。

---

## 五十八、我认为最核心的 UX 问题可以归纳成 8 个

如果不考虑技术，只看用户：

🔴 P0

1. 第一次打开不知道从哪里开始

🔴 P0

2. Search 与 Filter 是互斥关系，但用户天然认为它们可以组合

🔴 P0

3. Quick Picks、Category、Newcomer Guide 三者概念重叠

🔴 P0

4. "没有数据"和"确实没有这个服务"没有充分区分

🔴 P1

5. 地图缺少明显 Legend

🔴 P1

6. Popup 信息层级太平，重要信息与验证 / 法律信息混在一起

🔴 P1

7. Favorites 的本地存储 / Export / Import 对普通用户过于技术化

🔴 P1

8. 手机端功能很多，但地图核心区域仍被顶部控制区压缩

---

## 五十九、如果让我模拟一个新用户的完整使用过程

我认为最有价值的是看这条路径：

```
打开 URL
 ↓
"这是什么？"
 ↓
看地图
 ↓
"这些点是什么？"
 ↓
点击一个点
 ↓
"这个星星是什么？"
 ↓
看到详情
 ↓
"Source 是什么意思？"
 ↓
想找超市
 ↓
看到 Search
 ↓
输入 Walmart
 ↓
地图自动移动
 ↓
"为什么 Area/Category 不管用了？"
 ↓
想找 Sahali 的 Walmart
 ↓
发现搜索和筛选不能组合
 ↓
返回
 ↓
点击 Category
 ↓
"为什么有这么多分类？"
 ↓
点击 Quick Pick Shopping
 ↓
"这个是不是 Category？"
 ↓
再点 Newcomer Guide
 ↓
"为什么又是另一个 Newcomer Guide？"
 ↓
打开 Favorites
 ↓
"为什么不能同步？"
 ↓
看到 Export
 ↓
"为什么让我复制一串文字？"
```

这条路径说明：不是功能缺失，而是功能之间的关系没有被用户自然理解。

---

## 六十、最终问题分级

我建议后续修改时按照下面的优先级，而不是按"哪里不好看"来改。

| 等级 | 问题 | 影响 |
|---|---|---|
| 🔴 P0 | 首次使用没有明确起点 | 极高 |
| 🔴 P0 | Search 与 Filter 互斥 | 极高 |
| 🔴 P0 | Quick Picks / Category / Guide 概念重叠 | 极高 |
| 🔴 P0 | No Data ≠ No Service 没有区分 | 极高 |
| 🔴 P0 | 默认语言 EN | 高 |
| 🔴 P1 | 地图缺少 Legend | 高 |
| 🔴 P1 | Popup 信息层级 | 高 |
| 🔴 P1 | Mobile 顶部信息密度 | 高 |
| 🔴 P1 | Favorites Export/Import 心智模型 | 高 |
| 🟠 P1 | Bus 独立层概念不明显 | 中高 |
| 🟠 P1 | Guide 与地图缺乏连接 | 中高 |
| 🟠 P1 | Data Notes 信息过载 | 中高 |
| 🟠 P1 | 全局 Verified Date 语义 | 中高 |
| 🟠 P1 | Source 等级解释 | 中高 |
| 🟠 P2 | Cluster 语义 | 中 |
| 🟠 P2 | Reset 行为过强 | 中 |
| 🟠 P2 | Quick Pick 多选不明显 | 中 |
| 🟠 P2 | Category 三态不易理解 | 中 |
| 🟡 P2 | Footer 信息过载 | 中 |
| 🟡 P2 | URL 分享能力不易发现 | 中 |
| 🟡 P2 | 语言 fallback 不明显 | 中 |
| 🟡 P3 | 品牌定位 | 长期 |
| 🟡 P3 | 高级 AI / Recommendation | 长期 |

---

## 最后一个非常重要的判断

目前这个版本已经不是"做得不好"，恰恰相反：工程层面已经考虑了很多一般个人项目不会考虑的事情。

例如：

- URL 状态恢复
- 多语言 fallback
- 五语言
- 无网络功能降级
- 数据来源
- Verification
- Favorites export/import
- Cluster
- Screen reader
- Focus trap
- Escape
- 手机 Sheet
- dvh
- 搜索结果排序
- 数据版本
- GTFS 核验

这些从代码中都能直接看到。

所以下一阶段不应该继续无止境地增加功能。

现在最需要做的是：把"功能型地图"变成"用户一看就知道怎么用的城市生活工具"。

也就是说，下一轮重点应该从：

Feature completeness

转向：

Information Architecture → First-run UX → Interaction model → Visual hierarchy → Trust model。

这也是我认为目前最值得进行的一轮优化。
