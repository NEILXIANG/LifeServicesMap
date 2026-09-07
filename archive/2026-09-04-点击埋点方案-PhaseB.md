# 点击埋点方案 — Phase B（本地，2026.09.04d）

## 一句话总结

App 内所有有价值的用户决策（**19 类事件、共 25 处埋点**）都走一个 `trackEvent(type, props)` 函数；当前**只在本机 localStorage** 累积，**Phase A** 把同一函数的内部从 localStorage 换成 `navigator.sendBeacon` 打到 Cloudflare Analytics Engine，所有调用点**一行不动**。

## 跟踪的事件类型（19 类）

| `t` 字段 | 何时触发 | `p` 字段 | 商业价值 |
|---|---|---|---|
| `search_run` | 搜索词长度 ≥ MIN_QUERY | `q`（已脱敏）, `len` | 知道用户在找什么 → 重点补充搜索空缺 |
| `search_empty` | 搜索后结果数 = 0 | `q`（已脱敏）, `len`, `filters{areas,cat,route}` | 内容空缺的直接证据；Phase A 后每周扫一次就是数据需求清单 |
| `category_toggle` | 点击分类 chip | `id`, `action`(add/remove) | 热门/冷门分类 → 决定资源投向 |
| `category_clear_chip` | 点击已选 chip 上的 × | `id` | 用户放弃某分类的信号 |
| `category_group_toggle` | 点击分组全选/全消 | `group`, `action` | 哪类组合被批量使用 |
| `region_toggle` | 点击区域 chip | `id`, `action`(add/remove) | 区域集中度 |
| `region_select_all` | 点击"all areas" | （空） | 反向信号（全选 = 用户想看全市） |
| `preset_toggle` | 点击快捷 preset chip | `id`, `action`, `active` | 哪个 preset 流行 |
| `preset_clear_all` | 点击 "× 全部清除" | （空） | 用户放弃 signal |
| `fav_toggle` | 点击 ☆ 收藏 | `id`, `action`, `cat` | 哪些地点被重点关注 |
| `lang_change` | 切换语言 | `from`, `to` | 各语言用户占比；默认英文是否被覆盖 |
| `panel_open` | 打开筛选面板 | `mode`(area/cat/bus/fav), `prev` | 哪个面板用得最多 |
| `panel_close` | 关闭筛选面板 | `mode` | 与 panel_open 配对 → 漏斗分析 |
| `route_select` | 选择公交线路 | `id`, `action` | 哪些线路有真实需求 |
| `marker_view` | 打开地图标记 popup | `id`, `cat`, `reg` | 哪些地点被点开看详情 |
| `marker_close` | 关闭地图标记 popup | `id`, `cat`, `reg` | 兴趣深度信号 |
| `cta_click` | popup 内点击导航/电话/网站按钮 | `kind`(nav/call/web), `id`, `cat` | **转化漏斗**——用户真的要联系这家店了 |
| `share_click` | 点击分享按钮 | `copied`, `method` | 病毒性指标 |
| `reset_all` | 按"重置"按钮 | `dirty`(是否已选筛) | 弃用信号 |

## 调用点详细分布（25 处）

| 事件 | 调用次数 | 备注 |
|---|---|---|
| `share_click` | **4** | 单一入口但 3 路分支：execCommand 成功 / clipboard API 成功 / clipboard 失败 / 兜底失败。**这是合理的多分枝，不是冗余** |
| `trackEvent(type, ...)` 其余 18 类 | 各 1 处（共 21 处） | 每类事件一个入口 |
| **合计** | **25** | — |

> 早期文档里写的 "22 处" 与 "30+" 都是估算误差。**实测调用点 = 25**，其中 `share_click` 一类独占 4 个分支。

## `data-track` 通用逃生通道

文档里写过 `*`（任意 `[data-track="..."]` 元素）—— 实际只在 **popup 容器内**做了一个事件代理：

```js
popupEl.addEventListener('click', e => {
  const tk = e.target.closest('[data-track]');
  if (!tk) return;
  try{ trackEvent(tk.dataset.track, JSON.parse(tk.dataset.trackProps||'{}')); }catch(e){}
});
```

工作机制：
- popup 内的任意 DOM 元素只要加 `data-track="event_name" data-track-props='{"k":"v"}'`
- 点击时自动捕获并调用 `trackEvent(...)`
- 当前 popup 内 CTA 按钮（导航/电话/网站）走的是另一种已特化的 `cta_click`，**没有走 data-track**
- 所以 data-track 目前**没有实际生产使用**，只是留作未来埋点的逃生通道（避免每次都要改全局 click 代理）

## `lang_change` vs `lang_switch`

代码里**只有 `lang_change` 一处**（line 2286）。文档早期提到的 `lang_switch` 是规划别名，**未实际启用**。如需新增同义事件，直接复用 `lang_change` 即可——`from`/`to` 字段已经包含完整切换路径。

## 数据存储

- **位置**：`localStorage["kamloopsEvents"]`（JSON 数组）
- **大小**：最近 1000 条事件（FIFO 环形队列）
- **写入策略**：累计 20 条后刷盘 + 切到隐藏标签页立即刷盘 + `beforeunload` 刷盘
- **降级**：若 localStorage 写入失败（极少），丢弃最老 20% 再重试一次
- **跨会话**：刷新或重启浏览器后会从 localStorage 恢复（取最后 1000 条）

## 隐私

- ✅ 仅本机存储，零上传
- ✅ 无 cookie
- ✅ 无 IP / 用户标识 / 设备指纹
- ✅ 无第三方脚本（仍只有 Cloudflare Web Analytics 一行）
- ✅ **搜索词在 trackEvent 内部脱敏**：连续 3 位以上数字串移除 + 截断到 24 字符
  - Phase A 上传时也不会包含人名/电话/地址
- ⚠️ `?debug=1` 是公开 URL，普通用户访问时浮窗无内容（因为他们 localStorage 里没事件）

## 管理员视角（仅限你本机）

打开 `https://kamloops-lifemap.neilxiang.workers.dev/?debug=1`，右下角浮窗显示：

- 顶部事件总数
- 按事件类型计数（最多的在前）
- 分类 Top 8、区域 Top 8、搜索 Top 8
- "Export JSON" 按钮 → 下载 JSON 文件（含全部事件，含原始 props）
- "Clear" 按钮 → 双击确认后清空本机记录

## 验证

- `python3 validate.py Kamloops生活服务地图.html` → `all invariants hold`（5 条 warning 全是历史数据问题，与埋点无关）
- 构建产物：669KB，MD5 `d15adbbfe577dd30f61b011633f7499f`
- 本地手动测试：在本地 `?debug=1` 反复点击 → Export JSON → 看到事件正常记录

## Phase A 接入步骤（待办）

1. **新建 wrangler 项目**：在项目根加 `wrangler.toml`，声明 Analytics Engine binding
2. **加 Worker fetch handler**：把 `/api/event` POST 转到 Analytics Engine `writeDataPoint`
3. **`trackEvent()` 内部替换**：
   ```js
   // 现在（Phase B）：
   _evBuf.push({t:type,p:safeProps||{},d:Date.now()});
   if(++_sinceFlush>=_flushThreshold){flushEvents();_sinceFlush=0;}
   // 改为（Phase A）：
   try{
     navigator.sendBeacon('/api/event',JSON.stringify({t:type,p:safeProps||{},d:Date.now(),sid:getSid()}));
   }catch(e){}
   ```
   其中 `getSid()` 用 `crypto.randomUUID()` 存 sessionStorage（同浏览器会话内稳定）。
4. **CF 那边**：去 dashboard 建 Analytics Engine 数据集，配 wrangler.toml 的 `[[analytics_engine_datasets]]`，SQL 查询消费
5. **不需要动**：所有 `trackEvent(...)` 调用点、CHANGELOG、`?debug=1` 面板（仍可作为本地调试保留）

预计工时：1 小时左右（不涉及界面改动）。

## Phase B → Phase A 兼容性

- **已有 25 个调用点 / 19 个事件类型**：全部由 `trackEvent(type, props)` 包装
- **新增的事件类型**（cta_click、marker_close、panel_close、search_empty、category_clear_chip、share_click）在 Phase A 同样只需 `trackEvent(...)` 即可工作
- **搜索词脱敏**已在 helper 内部完成，Phase A 切换不影响
- **唯一标识 sid** 在 Phase A 引入（`{sid, t, p, d}` 四个字段）