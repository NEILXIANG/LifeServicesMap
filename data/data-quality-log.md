# 数据质量审查日志

> 数据本身的问题清单——**准确、及时、覆盖**是产品信任的根本。
> 已知保留问题同步自《UX审计四》《UX审计五》。

---

## 待修复（具体地点 / 字段）

| ID | 分类 | 问题描述 | 来源 | 优先级 | 状态 | 修复日期 |
|---|---|---|---|---|---|---|
| `xxx01` | — | — | 自查 / 用户反馈 | P0/P1/P2 | 待修 / 已修 / 搁置 | — |

> ID 用地点前 5 字符或前 8 字符 ID 简称，例如 `rbc001` 指 `Royal Bank` 类条目第一项。

---

## 待补充（已知缺哪些地点 / 分类）

| 分类 / 区域 | 缺什么 | 优先级 | 状态 |
|---|---|---|---|
| 例：`apt` / 北Thompson | 缺 3 家公寓楼 | P2 | 待补 |

---

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

**执行**：`python3 check-links.py > data/check-links-2026-09-05.log`

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

**29 个 MOVED** 全部有 `→` 指向正确新 URL，可批量替换。已在 data/check-links-2026-09-05.log 完整保留。

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

## 示例（仅供参考）

#### 待修复

| ID | 分类 | 问题描述 | 来源 | 优先级 | 状态 |
|---|---|---|---|---|---|
| `rbc01` | bank | RBC 地址写的是旧址（已搬迁）| 用户反馈 | P0 | 待修 |
| `wal03` | supermarket | Walmart Westsyde 周日营业时间与官方不符 | 自查 | P1 | 待修 |
| `lib01` | library | Thompson-Nicola 区域图书馆无 phone 字段 | 自查 | P2 | 待补 |

#### 待补充

| 分类 / 区域 | 缺什么 | 优先级 | 状态 |
|---|---|---|---|
| `pharm` / 南Kamloops | 缺 Shoppers Drug Mart Aberdeen 分店 | P2 | 待补 |
| `vet` | 整个分类缺 | P1 | 待补 |

#### 自查记录

### 2026-09-04 · 首次代码层自查（`validate.py`）

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
- 完整 log: data/check-links-2026-09-05.log

### 2026-09-07 · 月度巡检

- stale: 0 POI over 180d. nothing to do this cycle.
- 深链: 0 OK, 0 MOVED, 0 DEAD, 1 BLOCKED
- 完整 log: data/check-links-2026-09-07.log

### 2026-09-16 · 月度巡检

- stale: 0 POI over 180d. nothing to do this cycle.
- 深链: 0 OK, 0 MOVED, 0 DEAD, 56 BLOCKED（共 56 条）
- 完整 log: data/check-links-2026-09-16.log（计数取自同名 .json）

### 2026-09-16 · 月度巡检

- stale: 0 POI over 180d. nothing to do this cycle.
- 深链: 46 OK, 2 MOVED, 2 DEAD, 6 BLOCKED（共 56 条）
- 完整 log: data/check-links-2026-09-16.log（计数取自同名 .json）

### 2026-09-16 · 月度巡检

- stale: 0 POI over 180d. nothing to do this cycle.
- 深链: 36 OK, 2 MOVED, 2 DEAD, 16 BLOCKED（共 56 条）
- 完整 log: data/check-links-2026-09-16.log（计数取自同名 .json）

### 2026-09-16 · 月度巡检

- stale: 0 POI over 180d. nothing to do this cycle.
- 深链: 46 OK, 2 MOVED, 2 DEAD, 6 BLOCKED（共 56 条）
- 完整 log: data/check-links-2026-09-16.log（计数取自同名 .json）

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

**本轮同时修掉的两个巡检自身的缺陷**（详见 `docs/reports/2026-09-16-脚本全面分析与优化.md`）

1. HEAD 请求失败时直接下结论 —— 对 HEAD 回 404 的站点（Wix/Shopify/部分 WordPress 常见）误判为 DEAD。已改为任何 HEAD 失败都用 GET 复核。
2. 没有按域名节流 —— 56 条深链集中在 27 个域名，其中 `kamloops.ca` 14 条、`kelsongroup.com` 11 条，6 个并发一起打过去把对方打到限流，报告里看起来像"这家网站挂了"。已改为同域名串行、间隔 1.5 秒，并发只跨域名。
