# 访问分析周报

> 数据来源：Cloudflare Workers Metrics + Cloudflare Web Analytics
> 截图归档：本目录 `./screenshots/YYYY-MM-DD.png`

---

## 周报模板（每条周报复制一份）

### YYYY-Www（YYYY-MM-DD ~ YYYY-MM-DD）

**访问量**

| 指标 | 数值 | 同比上周 |
|---|---|---|
| 请求数 | — | — |
| 唯一访客（UV） | — | — |
| 浏览量（PV） | — | — |

**地理分布 Top 5**

| 国家 / 城市 | 请求占比 |
|---|---|
| — | — |
| — | — |

**使用时段**（哪几个小时最高）

| 时段 | 请求数 |
|---|---|
| 09-12 | — |
| 12-18 | — |
| 18-22 | — |
| 22-09 | — |

**错误率**

| 状态码 | 次数 |
|---|---|
| 2xx | — |
| 4xx | — |
| 5xx | — |

**设备 / 来源**

| 维度 | 占比 |
|---|---|
| 桌面 / 手机 / 平板 | — / — / — |
| 直链 / 搜索 / 社交 | — / — / — |

**本周发现**

- （从数据里读出的信号，不超过 3 条）

**本周动作 / 部署**

- `YYYY-MM-DD` 部署 `DATA_VERSION='2026.09.04a'`，变更内容：…
- 推广动作：[群/帖链接]，24h 后 UV 增量…

---

## 示例（仅供参考格式）

### 2026-W36（2026-09-04 ~ 2026-09-10）⚠️ 第一周，基线

**访问量**

| 指标 | 数值 | 同比上周 |
|---|---|---|
| 请求数 | 247 | —（首周） |
| 唯一访客（UV） | 89 | — |
| 浏览量（PV） | 312 | — |

**地理分布 Top 5**

| 国家 / 城市 | 请求占比 |
|---|---|
| Canada / Kamloops | 58% |
| Canada / Vancouver | 21% |
| Canada / Toronto | 9% |
| China / Beijing | 6% |
| China / Shanghai | 3% |

**使用时段**

| 时段 | 请求数 |
|---|---|
| 09-12 | 23 |
| 12-18 | 47 |
| 18-22 | 132 |
| 22-09 | 45 |

**错误率**

| 状态码 | 次数 |
|---|---|
| 2xx | 247 |
| 4xx | 0 |
| 5xx | 0 |

**设备 / 来源**

| 维度 | 占比 |
|---|---|
| 桌面 / 手机 / 平板 | 35% / 60% / 5% |
| 直链 / 搜索 / 社交 | 78% / 15% / 7% |

**本周发现**

1. **峰值在 18-22 点**：晚饭后是新移民最活跃的查找时间 → 推广动作放傍晚更高效
2. **手机占 60%**：移动端体验是优先级，已知问题（结果列表 / 面板 dialog）应优先修
3. **国内 UV 占 9%**：有真实跨境用户，**国内访问速度应作为长期关注项**

**本周动作 / 部署**

- 2026-09-04 部署 `DATA_VERSION='2026.09.04a'`，变更：默认语言改英文
- 推广动作：[温哥华华人微信群](wechat://...)，24h 后 UV 增量 42

---

## 接入动作日志（数据采集相关的事件）

> 每次接入 / 升级 / 关掉采集工具，在这里记一行。

### 2026-09-04 · 部署 v1

- **工具**：Cloudflare Workers（直接上传）
- **URL**：https://kamloops-lifemap.neilxiang.workers.dev/
- **版本**：`DATA_VERSION='2026.09.04a'`
- **变更**：默认语言改英文（浏览器语言不再自动覆盖）
- **采集**：仅 Workers Metrics（请求数 / 错误率 / 地理 / CPU 时间）
- **数据维度缺口**：PV / 来源 / 设备 / 加载性能 —— **待补 Cloudflare Web Analytics**

### 2026-09-04c · Phase B 点击埋点上线（本地版）

- **状态**：✅ 已构建 / 已复制 `index.html`（**663KB**, MD5 一致）
- **范围**：13 个事件类型（搜索/分类/区域/筛选/preset/语言/收藏/地图标记/面板打开/公交线路/重置），35 个交互入口中收敛到 **15 个** `trackEvent(...)` 调用点
- **数据去向**：仅本机 `localStorage["kamloopsEvents"]`，最近 1000 条环形队列，5s 自刷 + 关闭前 flush
- **查看**：浏览器打开应用后，访问 `?debug=1` 看到右下角浮窗（计数、Top 8 分类/区域/搜索、Export JSON、Clear）
- **验证**：python3 validate.py 通过（5 个 warning 全是原项目数据层提示，无新增）；Node --check 通过；MD5 一致

### 2026-09-04 · 准备接入 Cloudflare Web Analytics

- **状态**：token 待用户提供（已发《Web Analytics 接入操作清单》）
- **计划插入位置**：`src/engine.html` 第 2709 行（`</script>` 与 `</body>` 之间）
- **计划版本号**：升级到 `2026.09.04b`
- **预计完成**：用户贴 token 后 10 分钟内（接入 + build + 部署 + 验证）

### 2026-09-04 · Cloudflare Web Analytics 接入完成 ✅

- **token**：`dfb57b079102488baabcd4523f0fda75`
- **snippet 形式**：`<script type='module'>`（Cloudflare 新版写法，异步加载更快）
- **插入位置**：`src/engine.html` 第 2709 行后 + CHANGELOG 顶部插入新条目
- **版本**：`DATA_VERSION='2026.09.04a'` → **`'2026.09.04b'`**
- **部署 URL**：`https://kamloops-lifemap.neilxiang.workers.dev/`（URL 不变）
- **验证结果**：
  - HTTP 200
  - 线上 `DATA_VERSION='2026.09.04b'` ✅
  - 线上 `data-cf-beacon='{"token": "dfb57b..."}'` 完整 ✅
  - 线上 / 本地 MD5 完全一致 ✅（`6e7726dc92151aecc78349ecfaee23d0`）
  - validate.py 跑线上版：all invariants hold ✅

### 下次行动 checklist

- [x] 用户从 Cloudflare 控制台拿到 beacon token
- [x] 接入 snippet 到 src/engine.html
- [x] 重 build + 重部署
- [x] 抓线上版 grep `beacon.min.js` 验证
- [ ] 24-48 小时后回 Web Analytics 看首次数据
- [ ] 第一次填 `2026-W36` 的"访问量 / 地理分布 / 来源 / 设备"四张表