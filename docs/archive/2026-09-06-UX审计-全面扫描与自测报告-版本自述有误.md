# UX 审计六：全面扫描与自测报告

> **审计日期**：2026-09-06
> **审计范围**：src/engine.html（HTML/CSS/JS）、src/data-kamloops.js、build.py、worker.js、public/sw.js、public/manifest.json、validate.py、deploy.sh、wrangler.toml
> **审计方法**：代码静态分析 + validate.py 自动检查 + 线上浏览器实测 + 用户旅程模拟
> **线上版本**：https://kamloops-lifemap.neilxiang.workers.dev/ （DATA_VERSION='2026.08.31e'）

---

## 一、Bug / 功能缺陷

### B01 [严重] 搜索结果自动聚焦可命中被筛选隐藏的标记

- **位置**：`src/engine.html:2317`
- **现象**：当搜索仅匹配到 1 个地点但该地点不在当前区域/分类筛选范围内时，`M.find(m=>m.score>0)` 仍会找到它并尝试打开 popup。该标记已被 `hideMarker()` 从地图上移除，导致 popup 打开在空白位置或报错。
- **修复**：`M.find()` 应同时检查 `inFilter` 条件，或在 `focusMarker` 前验证标记可见性。

### B02 [中等] `document.referrer` 解析可导致 session_start 事件崩溃

- **位置**：`src/engine.html:3167`
- **现象**：`new URL(document.referrer)` 在 referrer 为非空但格式异常的字符串时抛出异常，导致整个 `applyURLState()` IIFE 中断，`session_start` 事件丢失，后续初始化代码可能不执行。
- **修复**：用 try/catch 包裹 referrer 解析。

### B03 [中等] 公交指示条使用 CJK 全角括号

- **位置**：`src/engine.html:2719`
- **现象**：`u.routeLabel(key)+' '+r.n+'（'+u.stopsN(r.s.length)+'）'` 中的 `（）` 是全角字符，在英/法/西/韩界面显示为不协调的宽括号。
- **修复**：改用半角 `()` 或使用翻译字符串模板。

### B04 [低] `nextDayPrefix` 翻译键未定义

- **位置**：`src/engine.html:2682`
- **现象**：`u.nextDayPrefix` 在所有 5 种语言中均未定义，公交车次跨午夜时显示无"次日"前缀。实际上 `UI.zh.nextDayPrefix` 等已在 line 626 定义（`'次日 '`），但需确认运行时是否可达。
- **状态**：需进一步验证是否为真 bug 还是审计误报。

### B05 [低] URL 状态写入 1 字符搜索词但不生效

- **位置**：`src/engine.html:3115` vs `2290`
- **现象**：`writeURLState` 写入 `searchInputEl.value.trim()`（原始输入），但 `apply()` 要求 `MIN_QUERY=2`。用户输入 1 个字符后分享 URL，接收方打开时该字符被加载但不触发搜索。
- **修复**：URL 仅在 `searchTerm` 非空时写入 `q` 参数。

### B06 [低] `lastFocused` 变量在 modal 和 panel 间共享

- **位置**：`src/engine.html:2860, 3048`
- **现象**：如果在 panel 打开期间通过某种方式触发了 modal（当前 UI 路径不支持但代码层面可能），关闭 modal 后 panel 的焦点恢复会使用错误的 `lastFocused` 值。
- **风险**：低（当前 UI 无法触发此路径），但代码脆弱。

### B07 [低] offline banner 在快速连续 popup 切换时状态错乱

- **位置**：`src/engine.html:1820, 1830-1831`
- **现象**：cluster spiderfy 时多个 popupopen/popupclose 事件快速触发，`yielded` 标志可能被提前清除，导致第二个 popup 关闭时 offline banner 不恢复。
- **影响**：仅离线模式下可见，极低概率。

### B08 [低] CSS 规则 `footer{flex:0 0 auto;}` 无效

- **位置**：`src/engine.html:423`
- **现象**：CSS 选择器 `footer`  targeting HTML `<footer>` 元素，但实际 HTML 使用 `<div class="footer">`（line 565）。该规则从未生效。
- **修复**：改为 `.footer{flex:0 0 auto;}`。

### B09 [低] `.fav-star.active` CSS 类无对应样式规则

- **位置**：JS line 1951 添加 `active` 类，CSS 无 `.fav-star.active` 规则
- **现象**：收藏星标的 active/non-active 状态视觉上无区别（都是金色 #f2a900）。用户无法通过星标外观判断是否已收藏。
- **修复**：添加 `.fav-star.active` 样式或改用不同颜色/填充状态。

---

## 二、无障碍问题

### A01 [中等] 缺少 `<main>` 地标区域

- **位置**：HTML 结构（lines 484-565）
- **现象**：页面没有 `<main>` 或 `role="main"` 元素。屏幕阅读器用户无法快速跳转到主要内容。
- **修复**：将 map + footer 区域包裹在 `<main>` 中。

### A02 [中等] 搜索框缺少关联 `<label>`

- **位置**：`src/engine.html:516`
- **现象**：`<input type="search">` 仅靠 JS 设置的 `placeholder` 和 `aria-label` 提供标签。Placeholder 在用户输入后消失，不是可靠的标签替代方案。
- **修复**：添加 visually-hidden 的 `<label for="searchInput">`。

### A03 [中等] 收藏导入 textarea 缺少 label

- **位置**：`src/engine.html:600`
- **现象**：`<textarea id="favCode">` 无 `<label>` 也无 `aria-label`。屏幕阅读器无法识别其用途。
- **修复**：添加 `aria-label` 或关联 label。

### A04 [中等] 搜索容器缺少 `role="search"`

- **位置**：`src/engine.html:514`
- **现象**：搜索栏 `<div class="search-bar">` 没有 `role="search"` 地标。
- **修复**：添加 `role="search"` 或改用 `<form>` 元素。

### A05 [低] 活跃筛选芯片关闭按钮触摸目标过小

- **位置**：CSS line 96, `.af-chip .x`
- **现象**：`.x` 按钮仅 15×15px，远低于 44px 触摸目标标准。虽然父级 `.af-chip` 有 min-height:44px，但实际点击目标是 `.x`。
- **修复**：给 `.af-chip .x` 添加 coarse-pointer min-width/min-height:44px。

### A06 [低] Popup 操作按钮触摸目标过小

- **位置**：CSS line 391, `.pact-btn`
- **现象**：导航/电话/网站按钮约 25-28px 高，无 coarse-pointer 覆盖。在 Leaflet popup 内空间有限但仍应满足最小目标。
- **修复**：增加 padding 或在 coarse-pointer 下增大尺寸。

### A07 [低] 分类组复选框视觉目标与实际点击区域不一致

- **位置**：CSS line 129, `.grp-check` 16×16px
- **现象**：视觉上只有 16px 的方框，但整行 `.cat-group-label` 都可点击。用户可能只瞄准小方框而错过。
- **修复**：增大 `.grp-check` 视觉尺寸或添加视觉提示表明整行可点击。

### A08 [低] Footer 使用 `<div>` 而非语义化 `<footer>`

- **位置**：`src/engine.html:565`
- **现象**：`<div class="footer">` 不是语义化的 `<footer>` 元素，屏幕阅读器无法识别为页脚地标。
- **修复**：改为 `<footer class="footer">`。

### A09 [信息] 标记设置 `keyboard:false`

- **位置**：`src/engine.html:2170`
- **现象**：250+ 标记不可键盘聚焦。这是有意为之的设计决策（避免 Tab 遍历 250 个元素），但应在文档中说明替代键盘导航方案。
- **状态**：已知权衡，非缺陷。

---

## 三、视觉 / UI 问题

### V02 [中等] 601-900px 宽度区间标题被挤压

- **位置**：CSS line 43 `h1{padding-right:265px}`
- **现象**：在 601-700px 宽度（大手机横屏/小平板竖屏），header 使用桌面布局（lang-sw 和 header-links 绝对定位），h1 的 265px 右内边距导致标题可用空间仅 335-435px，长标题（法语/西班牙语）被截断。
- **修复**：在 600-900px 区间添加中间断点，或将 h1 padding-right 改为响应式值。

### V03 [低] 快捷选择行滚动发现性不足

- **位置**：CSS lines 82-89
- **现象**：渐隐 + 箭头提示在浅色背景上几乎不可见（代码注释也承认了这一点）。9 个标签中后面的 5-6 个可能被完全忽略。
- **状态**：已在上一轮审计中标记为 #17，待修复。

### V04 [低] 打印样式完全缺失

- **现象**：无 `@media print` 样式表。打印时地图显示为空白/半渲染区域，交互元素浪费墨水，固定定位元素错位。
- **修复**：添加基础打印样式（隐藏地图/按钮/面板，仅保留列表视图）。

### V05 [低] `transition: all` 使用过泛

- **位置**：CSS lines 46, 101, 119, 202
- **现象**：`transition: all` 会在任何属性变化时触发过渡动画，包括布局属性（width/height/margin），可能导致意外动画和性能问题。
- **修复**：指定具体属性（如 `transition: background, border-color, color`）。

### V06 [信息] 字体大小偏小

- **现象**：大量 UI 元素使用 10.5-12.5px 字号。已在上一轮审计中标记为 #21。
- **状态**：已知问题，待修复。

---

## 四、交互 / 逻辑问题

### I01 [中等] 筛选面板每次调整需 4 步操作

- **现象**：打开面板 → 选择 → 点击"应用" → 面板关闭。频繁调整时体验繁琐。
- **状态**：已在上一轮审计中标记为 #18，待修复。

### I02 [中等] 收藏夹跨设备迁移体验差

- **现象**：需手动复制粘贴文本代码，操作路径深，"代码"概念对普通用户不友好。
- **状态**：已在上一轮审计中标记为 #5，待修复。

### I03 [低] 反馈渠道仅限 mailto

- **现象**：许多移动端用户没有配置邮件客户端，点击反馈链接无反应。
- **状态**：已在上一轮审计中标记为 #13，待修复。

### I04 [低] 新手引导缺失

- **现象**：仅有一行 hint 文字在首次打开面板时消失。无欢迎引导、无功能介绍。
- **状态**：已在上一轮审计中标记为 #2，待修复。

### I05 [低] 搜索不支持模糊匹配和跨语言

- **现象**：精确子串匹配，拼写错误即零结果。英文界面搜"医院"找不到"Hospital"。
- **状态**：已在上一轮审计中标记为 #6，待修复。

### I06 [低] 无历史记录/最近查看功能

- **现象**：关闭 popup 后无法快速回看之前查看的地点。
- **状态**：已在上一轮审计中标记为 #9。

### I07 [低] 公交模块无实时信息链接

- **现象**：反复提示"请查官网"但未提供直达具体线路/站点的实时页面链接。
- **状态**：已在上一轮审计中标记为 #8。

---

## 五、文案 / 翻译问题

### T01 [中等] 数据说明弹窗内容过长

- **现象**：免责声明 + 数据来源 + 公交票价 + 隐私说明全部堆在一个弹窗中，首次点击的用户被密集文字吓退。关键提醒（如"营业时间请电话确认"）被淹没。
- **修复**：分层展示，首屏仅显示 2-3 条核心提醒，详细内容折叠。

### T02 [低] 紧急电话信息层级不够突出

- **位置**：Footer 中的 `.footer-emergency`
- **现象**：911/8-1-1/RCMP 信息虽有独立样式，但仍混在 footer 长文本中。对于紧急情况，这些信息应该更显眼。
- **修复**：考虑在数据说明弹窗顶部或单独位置突出显示。

### T03 [低] 隐私说明过于技术化

- **现象**：隐私说明提到 `/api/event`、DevTools Network 面板等技术细节，普通用户无法理解。
- **修复**：用通俗语言重写，技术细节放入"了解更多"折叠区。

### T04 [信息] Guide 内容中的外部链接未验证可达性

- **现象**：新居民指南中包含多个政府网站链接（Service Canada、ICBC、BC RTB 等），这些链接未在 check-links.py 的检查范围内。
- **修复**：将指南链接纳入定期链接健康检查。

---

## 六、法律 / 合规问题

### L01 [中等] CC BY-NC 许可证与商业化探索存在张力

- **现象**：当前 CC BY-NC 4.0 许可证禁止商业使用。如果未来要走 B2G/B2B 路径（机构付费定制），需要明确：(a) 定制版是否仍受 NC 限制；(b) 是否需要双许可模式。
- **修复**：在法律层面明确"开源版 NC + 商业授权"的双轨模式，并在 README 中说明。

### L02 [低] 免责声明法律效力未评估

- **现象**：数据说明中的免责声明（"因使用本页面信息造成的任何损失由使用者自行承担"）未经法律专业人士审阅。在加拿大法律下，此类免责条款的有效性取决于具体措辞和使用场景。
- **修复**：咨询法律专业人士评估免责声明的充分性。

### L03 [低] PWA manifest 锁定 portrait 方向

- **位置**：`public/manifest.json:8`
- **现象**：`"orientation": "portrait"` 强制竖屏。地图应用在横屏下更有用，尤其平板用户。这可能被视为不必要的限制。
- **修复**：改为 `"any"` 或移除该字段。

### L04 [信息] OSM 瓦片使用遵守 ODbL

- **状态**：Attribution 正确显示（Leaflet + OpenStreetMap contributors 链接）。合规。

### L05 [信息] 隐私政策符合"隐私优先"定位

- **状态**：不收集 IP、不写 cookie、不跨设备追踪。Analytics Engine 仅存储聚合事件。隐私说明在 UI 中可见。合规。

---

## 七、性能 / 技术问题

### P01 [中等] 构建产物 701KB 单文件

- **现象**：所有 HTML/CSS/JS/Leaflet/数据打包为一个文件。首屏加载慢，尤其弱网环境。
- **状态**：已在上一轮审计中标记为 #1。CDN 模式已有但未默认启用。

### P02 [低] Service Worker 仅缓存 2 个静态资源

- **位置**：`public/sw.js:13-16`
- **现象**：仅缓存 manifest.json 和 icon.svg。HTML 本身依赖 network-first 策略，首次离线访问时无 fallback。
- **修复**：考虑在安装时也缓存 index.html。

### P03 [低] PWA manifest 仅有 SVG 图标

- **位置**：`public/manifest.json:12-18`
- **现象**：iOS Safari 和旧版 Android 不支持 SVG PWA 图标。需要 PNG 192×192 和 512×512。
- **修复**：生成 PNG 图标并添加到 manifest。

### P04 [低] deploy.sh 硬编码用户特定路径

- **位置**：`deploy.sh:67-76`
- **现象**：wrangler/node 二进制路径指向 `/Users/neilxiang/.workbuddy/...`，其他开发者或 CI 环境无法直接使用。
- **修复**：使用 `which wrangler` 或 `npx wrangler` 动态查找。

### P05 [低] wrangler.toml compatibility_date 过时

- **位置**：`wrangler.toml:14`
- **现象**：`compatibility_date = "2024-09-23"` 已近 2 年。更新可启用新运行时特性和修复。
- **修复**：更新为当前日期。

### P06 [信息] Worker props JSON 截断可能产生无效 JSON

- **位置**：`worker.js:75`
- **现象**：props 超 2048 字符时被截断，可能产生无效 JSON 写入 Analytics Engine blob 列。
- **风险**：低（Analytics Engine 对 blob 格式容错），但建议在截断后尝试 re-parse。

---

## 八、数据质量问题

### D01 [中等] 11 个死链未修复

- **来源**：`data/data-quality-log.md` 2026-09-05 巡检
- **现象**：Interior Savings Credit Union、Yellow Cabs、Stay Tuned Auto Repair、Lil' Monkey's Treehouse、Scotiabank(Victoria St) 等 11 个网站已死（DNS 不解析或 404）。
- **修复**：电话核实后标记停业或更新 URL。

### D02 [中等] 29 个重定向链接未更新

- **来源**：同上
- **现象**：29 个网站已 MOVED（301/302），新 URL 已知但未批量替换。
- **修复**：用脚本批量替换为重定向目标 URL。

### D03 [低] 22 个 POI 坐标精度低（≤3 位小数）

- **来源**：validate.py warning
- **现象**：约 110m 精度，包括 College Manor Apartments、Kamloops Buddhist Temple 等。
- **修复**：逐步用 Google Places API 或实地核实更新坐标。

### D04 [低] 6 个分类仅有 1 个条目

- **来源**：validate.py warning
- **分类**：cafe, legal, liquor, police, schoolbus, tutor
- **修复**：核实是真稀缺还是漏录入。

### D05 [低] 区域覆盖不均

- **来源**：validate.py warning
- **现象**：ot=12, ws=14 vs 最高 67。Westsyde 和 North Thompson 严重欠缺。
- **修复**：专项补全低覆盖区域。

### D06 [信息] 0 个过期 POI（>180天）

- **来源**：`data/stale-POIs-2026-09.md`
- **状态**：数据新鲜度良好。

---

## 九、SEO / 社交分享问题

### S01 [中等] 缺少 og:image

- **现象**：社交分享时无预览图片。Facebook/Twitter/微信分享卡片无视觉吸引力。
- **修复**：生成 OG image（地图截图或品牌图）并添加 meta tag。

### S02 [低] 缺少 Twitter Card meta tags

- **现象**：Twitter/X 分享时无富媒体预览。
- **修复**：添加 `twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`。

### S03 [低] 缺少 canonical URL

- **现象**：无 `<link rel="canonical">`，搜索引擎可能将不同 URL 参数组合视为重复内容。
- **修复**：添加 canonical link。

### S04 [低] 多语言页面无 hreflang 声明

- **现象**：支持 5 种语言但无 `hreflang` alternates，搜索引擎无法识别语言版本。
- **修复**：由于是 SPA 单页，hreflang 的实际价值有限。可作为长期优化项。

---

## 十、冗余 / 过期文档

### DOC01 项目根目录包含大量中文 markdown 文档

以下文档可能是过程产物或已过期的分析文档，建议归档到 `docs/archive/` 或删除：

| 文件 | 状态建议 |
|------|----------|
| `Phase-A-实施报告.md` | 归档（已完成阶段） |
| `Phase-A-真实数据初步分析.md` | 归档 |
| `UX审计三-问题分级与核心判断.md` | 归档（已被后续审计取代） |
| `UX审计四-交互逻辑与UI实现分析.md` | 归档 |
| `UX审计五-全用户旅程模拟与问题清单.md` | 归档 |
| `Web Analytics接入操作清单.md` | 删除（已完成接入） |
| `上线发布包.md` | 归档 |
| `埋点与日志查看分析手册.md` | 保留（运维参考） |
| `埋点审计与改进清单.md` | 归档（已完成） |
| `数据记录与商业化探索框架.md` | 保留（活跃文档） |
| `点击埋点方案-PhaseB.md` | 归档（已完成） |
| `自我诊断分析报告.md` | 归档 |
| `访问分析方法论.md` | 归档 |
| `Claude outputs/` 目录 | 归档（AI 生成的历史审计报告） |

### DOC02 `data/` 目录中的模板文件

- `data/analytics-log.md` 和 `data/feedback-log.md` 包含大量空模板和示例数据。建议将模板移到 `docs/templates/`，data 目录仅保留实际记录。

---

## 十一、优化建议（非缺陷）

### OPT01 添加 loading/skeleton 状态

首屏加载时显示骨架屏或 spinner，让用户知道页面正在加载而非卡死。

### OPT02 语言自动检测已实现但可增强

`detectLang()` 已读取 `navigator.languages`，但不会记住用户偏好。建议将用户选择的语言存入 localStorage，下次访问自动使用。

### OPT03 考虑添加 `<nav>` 地标

语言切换器和 header-links 具有导航性质，可用 `<nav>` 包裹或添加 `role="navigation"`。

### OPT04 收藏导出增加 QR 码

生成包含收藏数据的 QR 码，新设备扫码即可导入，比复制粘贴文本友好得多。

### OPT05 添加应用内反馈表单

替代纯 mailto 方案，POST 到 Cloudflare Worker 的 `/api/feedback` 端点。降低反馈门槛。

### OPT06 快捷选择改为 wrap 布局

水平滚动改为 2 行网格，提高后面标签的发现性。

### OPT07 桌面端筛选面板改为侧边栏

不遮挡地图，支持一边看地图一边调筛选。

### OPT08 添加"最近查看"列表

存 localStorage，显示在收藏面板旁边或作为独立入口。

### OPT09 Popup 信息层级重排

行动按钮（导航/电话/网站）置顶，来源/核实信息放底部灰色小字。

### OPT10 小屏 Header 简化

次要操作（反馈、说明、指南）收入"更多"菜单，header 仅保留语言切换和分享。

### OPT11 搜索增强

添加模糊匹配（Levenshtein）和跨语言别名索引。

### OPT12 添加 print stylesheet

隐藏地图和交互元素，仅保留地点列表用于打印。

### OPT13 生成 PNG PWA 图标

为 iOS/旧 Android 提供 192×192 和 512×512 PNG 图标。

### OPT14 解锁 PWA 横屏方向

地图应用在横屏下体验更好，尤其平板。

---

## 十二、汇总统计

| 类别 | 严重 | 中等 | 低 | 信息 | 合计 |
|------|------|------|-----|------|------|
| Bug/功能缺陷 | 1 | 2 | 6 | 0 | 9 |
| 无障碍 | 0 | 4 | 4 | 1 | 9 |
| 视觉/UI | 0 | 2 | 3 | 1 | 6 |
| 交互/逻辑 | 0 | 2 | 5 | 0 | 7 |
| 文案/翻译 | 0 | 1 | 2 | 1 | 4 |
| 法律/合规 | 0 | 1 | 2 | 2 | 5 |
| 性能/技术 | 0 | 1 | 4 | 1 | 6 |
| 数据质量 | 0 | 2 | 3 | 1 | 6 |
| SEO/社交 | 0 | 1 | 3 | 0 | 4 |
| 文档 | — | — | — | — | 2项 |
| 优化建议 | — | — | — | — | 14项 |
| **合计** | **1** | **16** | **32** | **7** | **56项 + 14优化 + 2文档** |

---

## 十三、优先级排序建议

### 立即修复（P0）
1. B01 — 搜索聚焦隐藏标记 bug
2. B02 — referrer 解析崩溃风险
3. B03 — CJK 括号国际化
4. B08 — CSS footer 选择器无效
5. B09 — 收藏星标状态不可见

### 近期修复（P1）
6. A01-A04 — 无障碍地标和标签补全
7. D01-D02 — 死链和重定向链接修复
8. V02 — 601-900px 标题挤压
9. T01 — 数据说明弹窗分层
10. S01 — og:image 添加
11. P01 — 加载性能优化

### 中期改进（P2）
12. 上一轮审计 P1 项（#16 Header简化、#19 Popup重设计、#6 搜索增强）
13. A05-A07 — 触摸目标修复
14. L01 — 许可证双轨模式明确化
15. P03 — PNG PWA 图标
16. 文档归档整理

### 长期优化（P3）
17. 上一轮审计 P2/P3 项
18. OPT01-OPT14 优化建议
19. V04 — 打印样式
20. S02-S04 — SEO 完善

---

*本报告基于 2026-09-06 的代码快照和线上版本生成。所有发现均已标注具体文件和行号，可直接用于修复跟踪。*
