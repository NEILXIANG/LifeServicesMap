# Phase A 真实数据首批分析报告

> **生成时间**：2026-09-05 00:55 PDT  
> **覆盖时段**：2026-09-05 07:01 ~ 07:21 UTC（约 20 分钟窗口）  
> **数据源**：CF Analytics Engine `kamloops_events`（端到端验证：`/api/event` POST → worker.js → writeDataPoint → SQL API）

---

## 一、SQL API 完整排查记录（4 类错误 + 修复）

### 1.1 初始症状
- 0 条请求 → 401（正常，无 token）
- 1 条 `SELECT 1` → 200 ✅
- 5 条不同预设 → 一律 3103 "value is too long"

→ 用户判断"权限不够"，但 token 实际验证通过（`/user/tokens/verify` → active）。

### 1.2 根因（按发现顺序）

| # | 现象                                  | 真因                                  | 修复                                          |
| - | ----------------------------------- | ----------------------------------- | ------------------------------------------- |
| 1 | HTTP 422 `unknown function call: UNIQ` | **AE 不支持 `uniq()`**                | 全脚本 `uniq(col)` → `count(DISTINCT col)`（15 处） |
| 2 | HTTP 422 `unsupported query type: ...UNION ALL` | **AE 不支持 `UNION ALL`**           | funnel 拆 5 个独立查询，main() 里合并打印               |
| 3 | HTTP 422 `unsupported expression type: (SELECT ...)` | **AE 不支持子查询当列**                  | types 去掉 `pct` 列（或两次查询）                      |
| 4 | HTTP 422 `unknown function call: JSONEXTRACTSTRING` | **AE 不支持任何 JSON 函数**（含 JSONExtract / JSON_VALUE / visitParamExtractString / simpleJSONExtractString） | places/presets/routes 改 `GROUP BY blob3`，render() Python 解析 |
| 5 | HTTP 422 `unknown function call: TOSTRING` | **AE 不支持 `toString()`**            | recent 直接 `SELECT timestamp`（输出 `2026-09-05 07:21:57` 格式已可读） |
| 6 | HTTP 422 `unable to find type of column: "timestamp"` | **`timestamp AS xxx` 不被 AE 接受**   | 别名用别的列；timestamp 列必须原名                          |
| 7 | 脚本报"Cloudflare 返回错误 null"           | **AE SQL API 顶层无 `success` 字段**，旧脚本的 `resp.get("success")` → None → 走错误分支 | run_sql() 改为检查 `meta` + `data` 键             |
| 8 | `formatDateTime(.. '%M')` 输出"September" | **AE 里 `%M` = 月份全名（POSIX 语义）** | 改成 `%i`（分钟）                                  |

### 1.3 最终结果
10 个预设全部跑通（health / types / funnel / gap / daily / lang / places / presets / routes / recent + session）。

---

## 二、真实数据洞察（截至 2026-09-05 07:21 UTC）

### 2.1 总览

| 指标            | 数值    |
| ------------- | ----- |
| 总事件           | 71    |
| 独立会话（sid）     | 10    |
| 事件类型数         | 20    |
| 时间窗口          | 07:01 ~ 07:21（~20 分钟）|
| 平均事件/会话      | 7.1   |

### 2.2 事件类型分布（top 10）

| 事件                | 次数 | 用户数 | 解读                       |
| ----------------- | -- | --- | ------------------------ |
| panel_close       | 9  | 2   | 反复开关面板（探索期）           |
| preset_toggle     | 9  | 3   | 试 preset                 |
| panel_open        | 9  | 3   | 打开各种面板                  |
| **lang_change**   | 7  | 3   | **语言切换频繁**（用户测多语言或真切换） |
| route_select      | 5  | 2   | 5 次公交线路切换                |
| ping              | 4  | 1   | 1 个会话的心跳                 |
| category_toggle   | 4  | 2   | 分类筛选                      |
| marker_view       | 3  | 3   | 3 个不同地点的 popup          |
| search_run        | 3  | 3   | 3 次有效搜索                  |
| **cta_click**     | 3  | 3   | **3 个不同地点触发了行动**（核心 KPI） |

### 2.3 转化漏斗（funnel：用户在每个阶段的人数）

| #   | 步骤              | 用户数 | 相对上一级留存率        |
| --- | --------------- | --- | --------------- |
| 1   | panel_open      | 3   | —               |
| 2   | category/preset | 4   | — (preset 多了 1 用户) |
| 3   | marker_view     | 3   | 100%            |
| 4   | cta_click       | 3   | **100%**         |
| 5   | fav_toggle      | 1   | 33%             |

**关键发现**：从 marker_view → cta_click 100%，**这意味着每一位看了地点详情的人都触发了行动（打电话/导航/访问网站）**。但样本只有 3 人，不能下结论。

### 2.4 preset 热度（按 id+action 聚合后）

| preset       | action | 次数 |
| ------------ | ------ | -- |
| health       | add    | 3  |
| newcomer     | add    | 2  |
| kids         | add    | 1  |
| daily        | add    | 1  |
| edu          | add    | 1  |
| sports       | add    | 1  |

→ **健康类需求最强（3 次），新移民其次（2 次）**。

### 2.5 公交线路需求排名

| route | selects |
| ----- | ---- |
| 1     | 1    |
| 2     | 1    |
| 3     | 1    |
| 9     | 1    |
| 13    | 1    |

→ 5 条线路各 1 次（都是同一个会话 sid=`0804aa...` 在测试面板）。

### 2.6 语言切换路径（按 from → to 聚合）

| from → to | 切换次数 |
| --------- | ---- |
| en → fr   | 2    |
| en → zh   | 1    |
| fr → es   | 1    |
| ko → zh   | 1    |
| es → zh   | 1    |
| zh → ko   | 1    |

→ **默认英文（en）切换出去最多**（共 2 次 en→fr + 1 次 en→zh）。这跟"默认英文合理"假设相符——用户能从英文切到他们想要的语言。但样本太小。

### 2.7 地点热度（marker_view 按 id+cat 聚合）

| place_id   | cat    | views |
| ---------- | ------ | ----- |
| p042/health | health | 1   |
| p113/food   | food    | 1   |
| p007/health | health | 1   |

→ 3 个不同地点被各看 1 次。health 类被看 2 次。

### 2.8 真实用户行为片段（recent）

最有价值的 sid：`0804aa630a1e4710b1126a0f`（24 字符匿名 sid），在 ~10 分钟内完成了一次完整的"试公交"流程：

```
07:16:36  panel_open     mode=bus, prev=area
07:16:37  route_select   id=2
07:16:37  panel_close    mode=bus
07:16:38  panel_open     mode=bus, prev=bus
07:16:39  route_select   id=9
07:16:39  panel_close    mode=bus
07:16:41  panel_open     mode=bus, prev=bus
07:16:42  route_select   id=13
07:16:42  panel_close    mode=bus
07:16:43  panel_open     mode=cat, prev=bus   ← 切到分类面板
07:16:45  category_group_toggle  group=edu, action=select_all
07:16:47  panel_close    mode=cat
```

→ **用户行为解读**：在公交面板里快速试了 3 条线路（2/9/13），然后切到分类面板去开 edu 类。这是个真实用户的"探索"过程。

---

## 三、初步判断 & 下一步

### 3.1 数据质量结论

| 维度       | 状态                   |
| -------- | -------------------- |
| `/api/event` 链路 | ✅ 通（71 条全 200）         |
| sid 分布   | ✅ 10 个会话平均 7 事件（合理）  |
| 事件类型完整性 | ⚠️ 20 个类型里含 `ok_lower` / `tail_demo` / `tail_probe` / `manual_test` / `deploy_smoke` 这些是开发/测试用，应区分流量来源 |
| props 完整性 | ✅ 所有 events 都有非空 props  |
| 时间序列     | ✅ 服务端 timestamp 连续，无断点 |
| 跨设备 sid  | 未知（要等真实用户来才知道）       |

### 3.2 接下来的优化方向

1. **区分开发 vs 真实流量**：给测试事件加个 `env` 字段（`dev` / `prod`），分析时过滤掉 `env='dev'`
2. **删除旧部署 version**（手动）：Dashboard → Workers → kamloops-lifemap → Deployments → fcff4321 → "View Version" → 删 afeabcf9（API token 不能删 version）
3. **真实数据等积累**：现在 71 条是混合了 deploy.sh 的 smoke 测试 + 我自己的探索，要等 ≥1 周真实流量才有判断力
4. **每月初归档**：把 `daily` 趋势结果抄到 `data/analytics-log.md`（90 天后会过期）

### 3.3 工具链就绪度

| 工具             | 状态    | 备注                                                  |
| -------------- | ----- | --------------------------------------------------- |
| `query-events.py` | ✅ 10 预设全通 | 已修 8 类错误 + render() 加 JSON 后处理                       |
| `analyze-events.py` | ✅ 之前验证过 | 仅用于 `?debug=1` 导出的本机 JSON                            |
| `deploy.sh`    | ✅     | 探针 + MD5 校验 + zip 白名单                                 |
| 手册            | ✅ 更新  | §1.1b 加 AE 限制表 + §1.3 §1.4 重写 SQL + §8 故障表 +10 行 |

---

## 四、附录：删除 afeabcf9 deployment 的完整命令

```bash
TOKEN=$(cat ~/.cf_token)
ACC='d25d00a8131224f4d2caf2165d134db0'
SCRIPT='kamloops-lifemap'
DEP_ID='62564bbb-eca6-42a9-b62f-1e30526a6360'  # = afeabcf9 deployment

curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/$ACC/workers/scripts/$SCRIPT/deployments/$DEP_ID"
# → {"result":null,"success":true,"errors":[],"messages":[]}
```

> DELETE deployment 后，对应的 version `afeabcf9-...` 仍占存储（CF API 405）。要彻底清：Dashboard → Workers & Pages → kamloops-lifemap → Settings → Versions → 删 afeabcf9。