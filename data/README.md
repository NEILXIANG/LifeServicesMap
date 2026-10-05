# `data/` — 运营台账

这里是**运营记录**（访问数据、反馈、数据质量、商业假设），不是页面数据——页面数据在 `cities/<城市>/`。
2026-10-04 重写（原版写于 09-04，里面的 `src/data-kamloops.js`、"上手顺序（本周内）"已经过时）。

## 文件

| 文件 | 内容 | 谁写 | 多久看一次 |
|---|---|---|---|
| `analytics-log.md` | 访问数据记录：每一期导出的真实外部访客、维护者占比、渠道、搜索缺口；`?src=` 标记表 | 人（用 `scripts/analytics/` 导出、汇总后写一期） | 每次导出后（约每两周） |
| `data-quality-log.md` | **Kamloops** 数据本身的问题：待修复、待补充、自查和每月巡检结果 | 人 + `scripts/monthly-quality-check.sh`（追加巡检小结） | 每月巡检后 |
| `data-quality-log-<城市>.md` | 其他城市上线后的每月巡检（草稿城市的问题看 `docs/reports/<城市>审核清单.md`） | `monthly-quality-check.sh <城市>` | 每月 |
| `feedback-log.md` | 反馈（去标识化：只留地域、渠道、内容摘要） | 人 | 收到就写 |
| `business-hypothesis.md` | 商业化假设 H001–H005 与验证证据 | 人 | 每季度 |
| `stale-POIs-<YYYY-MM>.md` | 超过 180 天没核实的地点（其他城市文件名带城市） | `monthly-quality-check.sh` → `export-open.py` | 每月 |
| `check-links[-<城市>]-<日期>.log` / `.json` | 链接巡检结果 | `monthly-quality-check.sh` → `check-links.py` | 每月（不入库） |
| `geocode-cache.json` | BC 地址定位结果缓存 | `scripts/bc_geocode.py` | 不用看 |
| `exports/` | 统计原始导出（**不入库**） | `scripts/analytics/export-events.py` | — |

每月一次：`bash scripts/monthly-quality-check.sh [城市]`（默认 kamloops）。最近一次跑是 2026-09-16，10 月还没跑。

## 写记录的规则

- 日期一律 `YYYY-MM-DD`；时区写明（统计导出曾经混用 UTC 和当地时间，看起来像两批访客）。
- **只写真实发生的事**。模板和示例不放在台账里——示例数字曾被当成真实基线引用（经验库 L-003）。
- 反馈去标识化：不记姓名、头像、电话、邮箱；只留地域、渠道、内容摘要。
- 写结论时注明来源（哪次导出、哪份报告），让以后能核对。

## 隐私（与页面上的说明一致）

页面会发送**匿名使用事件**（点了什么、搜了什么），用于改进工具：不记 IP、不记设备 id、不用 cookie；会话 id 是随机的，
每 90 天换一次；搜索词上传前去掉数字、截到 24 个字符；危机类搜索只记 `[crisis]`；求助面板只记"打开过"（`help_open`，不带任何内容），里面拨了哪个号码、点了什么都不记。
细节见 `docs/guides/埋点与日志查看分析手册.md` 第 1.7 节。台账里引用统计时只写汇总数字。

## 不在这里的

- 外联邮件、对外 PDF、电话核实表：仓库外的 `../Guide to Life in Canada - ops/`（决策 D4）。
- 历史分析（如 2026-09-07 的全面分析）：`docs/archive/`。
