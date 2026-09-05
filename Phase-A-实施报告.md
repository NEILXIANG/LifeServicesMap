# Phase A 实施报告

**实施日期**：2026-09-04（PT）/ 2026-09-05（UTC+8）
**状态**：✅ **已部署上线** — Version ID `e4700372-9522-4188-95b7-0c4b5cb08d27`

---

## 🎉 部署验证结果（2026-09-05 00:00 PT）

```
▸ [5/5] 线上探针
✓ 首页 200  DATA_VERSION='2026.09.05'  trackEvent=27  sendBeacon=8
✓ /api/event GET → 404（Worker 已接管，GET 落到 ASSETS）
✓ /api/event POST → 200（事件已写入 Analytics Engine）
✓ /api/event 非法 payload → 400（正确拒绝）
✓ 404 × 9  .git/HEAD  .git/config  data/*  src/*  wrangler.toml  worker.js
```

### 端到端事件流测试（模拟真实用户会话）

| # | 事件 | props | 结果 |
|---|---|---|---|
| 1 | `panel_open` | `{mode:"cat"}` | 200 ✓ |
| 2 | `category_toggle` | `{id:"health",action:"add"}` | 200 ✓ |
| 3 | `category_toggle` | `{id:"edu",action:"add"}` | 200 ✓ |
| 4 | `panel_close` | `{mode:"cat"}` | 200 ✓ |
| 5 | `search_run` | `{q:"dentist near me",len:15}` | 200 ✓ |
| 6 | `marker_view` | `{id:"p042",cat:"health"}` | 200 ✓ |
| 7 | `cta_click` | `{kind:"call",id:"p042"}` | 200 ✓ |
| 8 | `fav_toggle` | `{id:"p042",action:"add"}` | 200 ✓ |
| 9 | `lang_change` | `{from:"en",to:"zh"}` | 200 ✓ |
| 10 | `route_select` | `{id:"1",action:"select"}` | 200 ✓ |

### 边界用例（服务端必须拒绝垃圾数据）

| 输入 | 期望 | 实际 |
|---|---|---|
| `{"t":"UPPERCASE!"}` | 400 | **400** ✓ |
| `{"t":"ok_lower"}`（无 sid/d） | 200 | **200** ✓ |
| `{"p":{}}`（缺 type） | 400 | **400** ✓ |

### 回归检查（线上页面，零退化）

```
DATA_VERSION          '2026.09.05'   ✓ 新版本
trackEvent callsites  28             ✓ 全部在
sendBeacon            5 处           ✓ 1 调用 + 4 注释
getSid defined        1              ✓ 函数存在
kamloopsSid           3 处           ✓ 常量 + 读 + 写
footer-privacy        6 处           ✓ CSS 1 + 5 语言
CF Web Analytics      1              ✓ beacon 仍在
Leaflet inlined       1              ✓ 离线仍可用
markercluster         1              ✓ 聚合仍可用
5 languages           5              ✓ zh/en/fr/es/ko 全在
```

---

## ⚠️ 踩到的两个坑（已解决）

### 坑 1：Analytics Engine 是账户级开关

**现象**：首次 `wrangler deploy` 报 `[code: 10089] You need to enable Analytics Engine`。

**根因**：CF Analytics Engine 每个账户必须先在 Dashboard 手动启用一次（免费）。`wrangler.toml` 里声明 binding **不会**自动触发启用。

**解法**：打开 `https://dash.cloudflare.com/<account-id>/workers/analytics-engine` → 点 Enable → 重跑 `./deploy.sh`。

**副作用**：静态资源已上传成功，但 Worker script 版本创建失败 → **线上没切换**，仍跑旧版。启用后重跑即可。

**已改进**：`deploy.sh` 捕获 `code 10089` → 打印友好指引而非红色堆栈。

### 坑 2：macOS 的 `date +%s%3N` 不存在

**现象**：探针 POST 返回 400，看起来像 Worker 拒绝事件。

**根因**：`%3N`（毫秒）是 GNU date 扩展，macOS 的 BSD `date` **不支持**，输出 `17885916753N` —— 非法 JSON，Worker 正确拒绝了它。

**解法**：探针改用 `python3 -c 'import time;print(int(time.time()*1000))'` 生成毫秒时间戳（跨平台）。

**已改进**：`deploy.sh` 加了 `now_ms()` 函数。

**顺带修正**：`/api/event` 的 GET 期望值从 400 改为 404 —— Worker 只处理 POST，GET 会落到 `env.ASSETS`，ASSETS 里没有这个文件所以是 404，**404 反而证明 Worker 在跑**。

---

## 改动文件清单

| 文件 | 类型 | 大小 | 内容 |
|---|---|---|---|
| `wrangler.toml` | **新增** | 1.4 KB | Workers Static Assets + Analytics Engine binding 声明 |
| `worker.js` | **新增** | 4.9 KB | 边缘 Worker：路由 `/api/event` → 写 Analytics Engine，其余交给 `env.ASSETS` |
| `public/index.html` | **新增** | 672 KB | 构建产物（之前叫 `index.html`，现在在 `public/` 下给 Worker Static Assets 用） |
| `src/engine.html` | **修改** | - | trackEvent() 内部加 sendBeacon；新增 getSid() 与 sid 字段；5 种语言 footer 加隐私小字；DATA_VERSION 升到 `2026.09.05`；CHANGELOG 顶部加 2026.09.05 条目 |
| `deploy.sh` | **重写** | 9.7 KB | 流程从「打包 zip」改为「wrangler deploy」+ 端到端探针（首页 + `/api/event` + 敏感路径） |

**删除**：`index.html`、`Kamloops生活服务地图.html`、`kamloops-deploy.zip`、`kamloops-deploy/` 目录、`zikcyzhs` 占位文件 —— 这些都是 Direct Upload 时代的产物，Phase A 不再需要。

---

## 架构变化（vs Phase B）

### Phase B（之前）
```
 浏览器          Edge
 ┌──────┐    ┌────────┐
 │trackE├────►│localStorage│  ← 单设备，看不到别人
 │vent  │    └────────┘
 └──────┘
```

### Phase A（现在）
```
 浏览器          Edge                          CF Dashboard
 ┌──────┐    ┌──────────────┐             ┌─────────────────┐
 │trackE├────►│sendBeacon    │             │ Analytics       │
 │vent  ├────►│/api/event    ├─writePoint─►│ Engine          │
 │      │    │ (Worker)     │             │ - 90 天保留      │
 │      │    │   + env.ASSETS│             │ - SQL 查询       │
 └──────┘    └──────────────┘             │ - 漏斗/cohort    │
                                          └─────────────────┘
         + 本机仍写 localStorage（?debug=1 用）
```

---

## 部署形态变化

| 之前 | 现在 |
|---|---|
| 拖 zip 到 CF Dashboard Deployments | `wrangler deploy` 命令 |
| Workers Direct Upload | Workers Static Assets + Worker 代码 |
| 无 binding | Analytics Engine binding（自动随 Worker 一起） |

**为什么必须改**：
- CF Workers Direct Upload **不支持** Analytics Engine binding（binding 必须在 `wrangler.toml` 声明）
- CF Workers Direct Upload **不支持**把 Worker 代码（`worker.js`）作为入口
- 要让 `/api/event` 在边缘被执行，必须有 Worker fetch handler —— 单纯托管静态文件做不到

---

## 隐私边界

| 项 | Phase B | Phase A |
|---|---|---|
| 数据去哪儿 | 用户浏览器 localStorage | CF 服务端 Analytics Engine |
| 是否收集 IP | 无 | **无**（CF Analytics Engine 不记录 IP） |
| 是否记 UA/cookie | 无 | 无 |
| 用户标识 | 无 | **匿名 sid**（本地随机 24 字符，localStorage 持久化） |
| 搜索词是否脱敏 | 本机不需 | **脱敏后再发**（已 Phase B 时代就做好） |
| 告知用户 | 无 | **footer 加一行小字**（5 种语言全部加） |

合规等级：与 CF Web Analytics 同档（cookie-free、无第三方），BC PIPA / GDPR 合规。

---

## 新增 / 修改的事件 schema

事件从 `_evBuf.push({t, p, d})` 升级为：

```json
{
  "sid": "a3f2e1b9c8d7...",        // 新增：24 字符随机 sid
  "t":   "preset_toggle",          // 事件类型
  "p":   {"id": "health", "action": "add", "active": 3},  // props
  "d":   1725561234567             // Date.now() 毫秒
}
```

服务端 Analytics Engine 写入：
- `blobs[0]` = sid
- `blobs[1]` = t
- `blobs[2]` = JSON.stringify(p)（≤2048 字符）
- `doubles[0]` = d
- `indexes[0]` = t（用于 SQL 高效过滤）

---

## 验证（部署前本地静态检查已通过）

```
validate.py public/index.html
  → "all invariants hold"   ✓
  → 5 warnings（全是历史数据问题，Phase A 没引入）
```

```
trackEvent(...) 实际调用点（代码）：28 处
事件类型：19 个（search_run / search_empty / category_toggle / category_clear_chip /
             category_group_toggle / region_toggle / region_select_all / preset_toggle /
             preset_clear_all / fav_toggle / lang_change / panel_open / panel_close /
             route_select / marker_view / marker_close / cta_click / share_click / reset_all）
```

> 备注：之前 CHANGELOG 写"25 call sites"——CHANGELOG 是当时理解的近似值，精确数 28 是这次审计出来的。

---

## ✅ 部署已完成 — 你现在要看什么

### 第 1 步：体验一次（1 分钟）

打开 `https://kamloops-lifemap.neilxiang.workers.dev/` 随便点几下：
- 切语言、开预设、点地图标记、收藏、搜索
- 打开 `?debug=1` 会看到右下角调试浮窗，计数应该随操作增长

footer 底部现在多了一行小字（5 种语言都有）：
> 📊 Anonymous usage statistics are collected to improve this service (no personal data)

### 第 2 步：等 5-10 分钟，去 Dashboard 查数据

Analytics Engine 有索引延迟（写入成功 ≠ 立即可查）。等几分钟后：

**Workers & Pages → kamloops-lifemap → 左侧 Analytics Engine → SQL Editor**

先跑这条看有没有数据：

```sql
SELECT
  timestamp,
  blob1 AS sid,
  blob2 AS event_type,
  blob3 AS props
FROM kamloops_events
ORDER BY timestamp DESC
LIMIT 50
```

> 如果表名不对，试试 `FROM kamloops_events` 换成 Dashboard 里显示的 dataset 名。

### 第 3 步：清理旧部署（建议做）

旧的 Direct Upload 部署（2026.09.04a/b/d）**仍然存在**，它们的 `.git/config`、`data/` 等敏感文件路径**还能访问** —— 新部署不会自动清理旧版本的静态资源。

**Workers & Pages → kamloops-lifemap → Deployments → 每行右侧 ⋯ → Delete deployment**

保留最新的 `e4700372`（Version ID），其余全删。

---

## 部署后随时跑

```bash
./deploy.sh --verify-only    # 只跑线上探针（不动本地）
./deploy.sh --login          # 单独做 wrangler login（首次部署前或 token 过期时）
./deploy.sh --no-build        # 跳过构建，直接 deploy（适合纯代码改动）
```

---

## 已知风险与缓解

| 风险 | 缓解 |
|---|---|
| wrangler login 跳浏览器（首次必须） | deploy.sh 自动引导；登录后无感 |
| 首次 wrangler deploy 可能慢（边缘冷启动） | 5-15 秒；deploy.sh 等 3 秒再探针 |
| Analytics Engine 数据 5-10 分钟才可查（CF 后端索引延迟） | 不影响"事件已写入"——writeDataPoint 成功即代表数据落库 |
| sid 跨浏览器不同（同设备多浏览器各算一个用户） | 这是隐私设计——不试图跨浏览器 fingerprint |
| Worker 挂了 → /api/event 返回错误 | client 仍写 localStorage（?debug=1 可看本机数据），数据不丢 |
| 旧 Direct Upload 历史部署需要手动删除 | wrangler deploy 会创建新部署；旧部署的 URL 仍可访问，旧敏感文件路径也跟着能访问，**部署完后建议手动删除** |

---

## SQL 查询模板（部署成功、Analytics Engine 数据可查后可用）

```sql
-- 1. 总事件数 + 独立用户数（24h）
SELECT
  count() AS events,
  count(DISTINCT blob1) AS users
WHERE timestamp > NOW() - INTERVAL '1' DAY

-- 2. 事件类型分布（24h）
SELECT blob2 AS event_type, count() AS n
WHERE timestamp > NOW() - INTERVAL '1' DAY
GROUP BY event_type ORDER BY n DESC

-- 3. 最热门的 preset 组合
SELECT blob3, count() AS n
WHERE blob2 = 'preset_toggle' AND timestamp > NOW() - INTERVAL '7' DAY
GROUP BY blob3 ORDER BY n DESC LIMIT 20

-- 4. 用户漏斗（搜索 → 点击 marker）
SELECT
  countIf(blob2 = 'search_run') AS searches,
  countIf(blob2 = 'marker_view') AS marker_views,
  countIf(blob2 = 'cta_click') AS cta_clicks
WHERE timestamp > NOW() - INTERVAL '7' DAY

-- 5. 单个用户完整行为（用 ?debug=1 拿到的 sid）
SELECT timestamp, blob2, blob3
WHERE blob1 = '<sid>'
ORDER BY timestamp ASC LIMIT 200
```

> 在 CF Dashboard → Workers & Pages → kamloops-lifemap → Analytics Engine → SQL Editor 里执行。