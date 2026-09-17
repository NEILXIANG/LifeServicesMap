# Cloudflare Web Analytics 接入操作清单

> **目的**：补全 Cloudflare Workers Metrics 看不出来的"页面加载性能 / 设备 / 来源"维度，零 cookie、不污染用户隐私。
>
> **为什么我帮你做不了拿 token 这一步**：Cloudflare 控制台需要你的浏览器登录会话，我没有 OAuth 权限。你只需把下面那一行 `data-cf-beacon='{"token": "abcdef..."}'` 复制粘贴给我，剩下的我全包。

---

## 你要做的（3 步，1 分钟）

### 1. 打开 Cloudflare Web Analytics

👉 https://www.cloudflare.com/web-analytics/

用你部署 `kamloops-lifemap` 时同一个 Cloudflare 账号登录。

### 2. 添加站点

1. 点 **Add a site**（或 **+ Add**）
2. 域名填：`kamloops-lifemap.neilxiang.workers.dev`
3. 点 **Install** / **Add site**

### 3. 复制 snippet

Cloudflare 会给你一段 HTML，你只需要把里面这一行**完整的字符串**贴给我：

```html
<script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{"token": "这里是你的token"}'></script>
```

**怎么复制**：
- 复制整段 HTML 也行
- 只复制 `data-cf-beacon='{"token": "abcdef..."}'` 的值也行
- 截图给我也行

---

## 我接手后做的事（你贴完 token 后给我）

1. 把 snippet 插入 `src/engine.html` 第 2709 行后（`</script>` 与 `</body>` 之间）
2. `DATA_VERSION` 升级到 `2026.09.04b`，`CHANGELOG` 加一条
3. 跑 `validate.py` 确认无副作用
4. `python3 build.py --out "Kamloops生活服务地图.html"`
5. 用 git show + cp 的方式重 build（避免 `.git/index.lock`，见你 user memory）
6. `curl` 抓线上版，grep snippet 验证已生效
7. 跑第二轮 validate.py 二次确认
8. 告诉你"接好了，等 24 小时看数据"

---

## 接入后能立刻看到什么

> 24-48 小时后回 https://www.cloudflare.com/web-analytics/ 看：

| 数据 | 用法 |
|---|---|
| **Visits（访问数）** | 比 Workers Metrics 的 Requests 更准（同一访客多次访问只算一次） |
| **Page views** | 总浏览量 |
| **Top countries / regions** | 用户地理分布（对判断"国内要不要加速"有直接依据）|
| **Top referrers** | 流量来源（微信群？Reddit？Google？）—— 帮你判断哪个推广渠道有效 |
| **Browsers / Devices** | 桌面 / 手机 / 平板占比；Safari / Chrome / 其他 |
| **Core Web Vitals**（LCP / FID / CLS） | 加载性能——用户体感是否流畅 |

---

## 隐私验证（重要）

Cloudflare Web Analytics 的 4 条核心隐私保证（https://www.cloudflare.com/privacypolicy/）：

1. **不用 cookie** —— 不需要 GDPR / 中国 PIPL 同意横幅
2. **不跨设备追踪** —— 不建用户画像
3. **不收集个人身份信息**（IP 只用于大致地理位置）
4. **数据所有权** —— 只有你看得到，Cloudflare 不外销

**与本项目"隐私优先"定位完全兼容**。无需在 README / 应用 UI 加任何隐私说明。

---

## 接入失败怎么办

| 现象 | 原因 / 解法 |
|---|---|
| Cloudflare 报"domain not found" | `kamloops-lifemap.neilxiang.workers.dev` 拼写错（少打 `lifemap`）；回 Workers 控制台复制一遍 |
| 看不到站点 | 等 1-2 分钟 Cloudflare 同步；刷新页面 |
| token 拿到但 snippet 没生效 | 贴给我时 token 字符串截断了——确保包含 `{}` 和引号 |
| 控制台报错 `beacon.min.js 404` | token 无效；让我帮你重新接入 |

---

## 备选：如果你不想接 Web Analytics

完全没问题 —— Workers Metrics 已经能覆盖 70% 的需求。剩下 30%（来源 / 设备 / 性能）可以在 `data/analytics-log.md` 里手动从其它来源收集。

但**强烈建议接入**——5 分钟拿到 token + 我 10 分钟接入 + 重部署，总成本 15 分钟，换来完整维度数据。