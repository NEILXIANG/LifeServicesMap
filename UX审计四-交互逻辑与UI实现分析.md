# Kamloops 生活服务地图 · 第四份审查：交互逻辑与 UI 实现分析

> 审查对象：`Kamloops生活服务地图.html`（约 3440 行，单文件自包含）
> 审查视角：交互模型、状态管理、焦点/可访问性、UI 实现细节
> 说明：本报告只做分析，不做修改。与前两份审计（首次使用诊断、信息架构与信任模型）互补——那份看"用户怎么理解"，这份看"逻辑怎么运转"。

---

## 一、交互模型总览

整个页面本质上是一台**单向数据流状态机**，核心状态只有 8 个：

| 状态 | 载体 | 持久化 |
|---|---|---|
| 语言 `L_` | 内存 | URL `?lang=`（首次由 `navigator.languages` 探测） |
| 区域 `aR` | Set | URL `?r=` |
| 分类 `aC` | Set（空 = 全部） | URL `?c=` |
| 快捷预设 `selPresets` + `presetsAdjusted` | Set + bool | 不入 URL |
| 搜索词 `searchTerm` / `searchRaw` | 字符串 | URL `?q=`（260ms 防抖） |
| 公交线路 `selectedRoute` | 键 | URL `?route=` |
| 收藏 `favorites` | Set | localStorage（带 id 迁移表 + 载入时剪枝） |
| 分组展开 `expandedGroups` | Set | 不入 URL |

所有状态变化汇聚到一条渲染管线：**`renderRegs()/renderCats()` → `apply()` → 标记显隐 + 计数行 + 徽章 + 活动筛选 chips + 空状态 + `writeURLState()`**。URL 用 `replaceState` 同步（不污染后退按钮），启动时由 `readURLState()` 一次性还原。这个架构判断是对的：单一管线、状态即唯一事实源，任何一个入口（面板、chips、URL、重置）都收敛到同一处。

覆盖层系统有三类，各有独立开关逻辑：
1. **筛选面板**（Area / Category / Bus / Favorites 四模式复用一个容器）：≤900px 是可拖拽下滑关闭的 bottom sheet，>900px 是锚定在触发按钮下方的 dropdown（桌面另有 document 点击外部关闭）；
2. **两个居中模态**（Newcomer Guide / Data Notes）：有完整的焦点记忆、Tab 陷阱、Escape；
3. **Leaflet popup**：位置卡片，`maxHeight` 随地图实测高度计算（避免 autoPan 死循环，注释里记录了这个 bug 的成因）。

Escape 按明确优先级栈依次Dismiss（Guide → Note → Panel → Popup），`lockBodyScroll` 用引用计数防止两个覆盖层互相提前解锁——这些都是实现质量的体现。

---

## 二、先说做得好的（校准用）

这份代码的成熟度明显高于常见单文件项目，很多此前审计提出的问题**已经在代码里修复并有 rationale 注释**：

- **搜索在筛选内收窄**：搜索不再绕过 Area/Category，而是"在已过滤集合内再过滤"，空状态还区分了"搜索无结果"与"搜索×筛选无结果"两种诚实文案；
- **收藏反馈**：星标点击有 toast + `aria-pressed`，避免了"没看到变化再点一次反而取消"的经典坑；
- **空状态三分支**：无结果/被筛选清空/搜索太短，各配一个直接动作按钮；
- **触控目标**：coarse pointer 下全局 44px，短屏(≤680px 高)显式降级到 36px 并在注释里写明取舍理由（44px 挤掉地图 = 指南违背自身目的）；
- **溢出可发现性**：Quick Picks 行按真实 scrollWidth 切换 fade+chevron，而不是常驻装饰；
- **离线瓦片降级**：连续 tileerror → 展开提示 → 6 秒后收缩为角标 → 点击恢复，弹窗打开时让位；
- **收藏迁移**：从"按名字存"迁移到稳定 id，导入时丢弃未知 id 而非整体失败；
- **URL 注入防御**：`owns()` 检查 own property，挡掉 `?lang=constructor` 这类原型链攻击。

以下问题是在这个基础上提出的。

---

## 三、问题与建议

### 🔴 P0-1 键盘/读屏用户没有任何到达地点详情的路径

`M.forEach` 创建 250 个 marker 时统一 `keyboard:false`（注释说明是为了不让键盘用户 Tab 250 次）。出发点合理，但结果是：**键盘用户和读屏用户从头到尾无法打开任何一个地点的 popup**——页面上不存在任何替代性的文字浏览入口。搜索也只能把结果反映为地图上的 pin。

这直接触犯 WCAG 2.1.1（键盘）和 4.1.3（状态消息）。`:focus-visible` 样式写得再好，键盘用户能到达的只有筛选控件本身。

**建议**：增加一个**文字结果列表**（见 P0-3，同一方案可解两个问题）；`#map` 容器补 `role` 与 `aria-label`，把"这是交互地图、可筛选"告诉辅助技术。

### 🔴 P0-2 筛选面板没有对话框语义，焦点从不进入

对比很鲜明：两个居中模态有完整的 focus 管理（`openModal` 记住 `activeElement`、移焦到关闭按钮、关闭后还原），而使用频率更高的**筛选面板完全没有**：

- `openPanel()` 不移动焦点——用户点按钮后面板出现在别处，焦点还停在工具栏按钮上；
- 面板容器无 `role="dialog"` / `aria-modal"`，读屏不认为出现了对话框；
- 桌面上面板 DOM 位于页面底部（`#map`、footer 之后），Tab 要穿过整个地图和页脚才能到达面板内容。

**建议**：复用 `openModal/closeModal` 的焦点管理模式：打开时把焦点移入面板（标题或关闭按钮），关闭时还原到触发按钮；容器加 `role="dialog"` + `aria-modal="true"`（移动端 sheet）或 `aria-haspopup`/控制关系的 dropdown 语义（桌面）。

### 🔴 P0-3 搜索结果只能通过地图标记消费，没有文字列表

搜"bank"得到 N 个 pin，用户必须逐个点击标记才能知道是哪家、在哪个区。无法扫读、无法比较、无法用键盘遍历。对一个以"新居民找服务"为目标的产品，这是信息消费路径上的最大缺口——而且它同时是 P0-1 的解药。

**建议**：在状态行下方渲染可滚动的结果列表（名称 + 分类色点 + 区域），每项可点击 → `focusMarker()`。搜索时显示，平时隐藏或显示当前筛选的前 N 项。列表天然可键盘操作、可读屏，成本不高（`apply()` 里 score 和 bounds 都已经算好了）。

### 🟠 P1-4 重建式渲染导致每次点击丢焦点

`renderRegs()`、`renderCats()`、`renderBusList()`、`renderFavList()` 都用 `innerHTML=''` 整体重建。用户（尤其键盘用户）在分类 chip 上按一次 Space，按钮节点就被销毁重建，**焦点掉回 `<body>`**，必须重新 Tab 进面板。状态本来就存在 `aC`/`aR` 这些 Set 里，重建 DOM 没有必要。

**建议**：改为就地更新——toggle `active`/`zero` class、更新计数文本；或至少重建后按 `data-key` 找回焦点。这一条与 P0-2 叠加后，键盘操作面板的体验是"每按一次键就断一次"。

### 🟠 P1-5 搜索期间地图被连续"抢走"

防抖 260ms 解决了逐键抖动，但每次 `runSearch()` 若结果数在 1–40 之间仍会 `fitBounds`。逐字输入 "superstore" 的过程中，地图会连跳 4–5 次视野。审计一第十四条提过这个问题，防抖缓解了节奏但没改变本质。

**建议**：只在**进入搜索态的第一次** fit（`preSearchView` 已经在记录这个时刻）；或输入停止 800ms 后再 fit；结果数为 1 时现有 `focusMarker` 行为可以保留。

### 🟠 P1-6 状态变化对读屏静默

`#statusText`（"显示 X/Y · 区域"）和 `#searchNote` 都是普通 div，内容变化无 `aria-live`。筛选后地图上还剩几个结果、搜索命中多少，读屏用户一概听不到。Toast 有 `role="status"`，说明作者懂这个模式，只是没铺到状态行。

**建议**：两处加 `aria-live="polite"`；注意 `setLang` 会重写全文，切换语言时应避免逐条播报（可临时 `aria-live="off"` 再恢复）。

### 🟠 P1-7 分组三态复选框语义不完整

`.grp-check` 是 `button` + `aria-pressed="true|false"`，但视觉上有 **all / partial / none 三态**，`aria-pressed` 表达不了 partial。读屏用户听到的是"已按下/未按下"，而屏幕上明明还有个"—"。

**建议**：改用 `role="checkbox"` + `aria-checked="true|false|mixed"`，与视觉三态一一对应。

### 🟠 P1-8 语言切换器双重语义标注

`setLang` 同时给激活按钮设置 `aria-pressed="true"` 和 `aria-current="true"`。两个语义（开关组 vs 当前项）同时声明，读屏行为取决于实现，且它本质是单选组。

**建议**：改为 `role="radiogroup"` + `role="radio" aria-checked`，或只保留 `aria-current` 去掉 `aria-pressed`。

### 🟡 P2-9 收藏星标用 inline onclick + 数字索引

`onclick="toggleFav(this,event)"` + `data-i` 数组索引：索引会随数据增删漂移（虽然目前每次重建一致），且 inline handler 与严格 CSP 不兼容。事件里已处理了 `stopPropagation` 防止重写 popup 时冒泡关弹窗——说明这里踩过坑，用事件委托 + `data-id`（id 已存在且稳定）可以更干净。

### 🟡 P2-10 元数据字号过小

`tag`(9.5px)、`cnt`(10.5px)、`grp-count`(10.5px)、`stop-label`(9.5px)。WCAG 不设字号下限，但 9.5px 的彩色 tag 对中老年用户（新居民产品的典型人群之一）接近不可读。建议元数据下限提到 11px。

### 🟡 P2-11 其余小项

- `cat-btn.zero` 的提示只有 `title` + `cursor:help`，触屏不可达——好在 `(0)` 计数本身可见，影响有限；
- `h1 { padding-right:265px }` 为语言切换器让位的 magic number，换语言/字体缩放时脆弱；
- 无 `prefers-color-scheme` 深色模式（OSM 瓦片是浅色，成本确实高，仅记录）；
- 无 print 样式（生活指南类内容有被打印的现实需求）；
- `expandedGroups` 不入 URL，分享链接打开后分组展开状态与原作者视图不一致（轻微）。

---

## 四、与前几份审计的关系

- **已修复**（代码注释可证）：搜索绕过筛选、收藏无反馈、默认英文不探测语言、URL 分享能力隐藏、区域取消到零的死角、分类随区域消失、Quick Picks 溢出无提示、面板不可拖拽关闭。
- **仍在但已有缓解**：搜索时地图自动移动（P1-5）、三套筛选入口的概念重叠（信息架构层面，见审计二）、Quick Picks 多选可发现性。
- **本份新增视角**：焦点管理、对话框语义、结果列表缺失、重建式渲染的焦点副作用——前三份审计聚焦信息架构与信任模型，没有系统覆盖"键盘与读屏如何操作这个页面"这一层。

## 五、建议的优先顺序

1. **结果列表**（一次解决 P0-1 + P0-3，是收益最大的单项改动）；
2. **面板 dialog 语义 + 焦点进出管理**（P0-2）；
3. **就地更新渲染保焦点 + aria-live + 三态语义**（P1-4/6/7）；
4. 搜索 fit 策略、语言切换器语义、inline handler 清理；
5. P2 打磨项择机。

---

*审查方法：通读 `<style id="app-css">`（691–1103 行）、body 结构（1105–1231 行）与 `<script id="app">` 全部应用逻辑（1233–3439 行），含 popup/apply/setLang/panel/search/URL 状态/收藏/离线降级各模块；Leaflet 与 markercluster 内联库未逐行审查。*
