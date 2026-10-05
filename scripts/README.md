# 脚本索引

> 2026-10-04 整理。每个脚本：做什么、怎么指定城市、谁调用、输出到哪里。测试见 [`../tests/README.md`](../tests/README.md)；
> 为什么有这些脚本、它们保证了哪条经验，见 [`../docs/knowledge/资产清单.md`](../docs/knowledge/资产清单.md) 和 [`经验库`](../docs/knowledge/经验库.md)。

## 按用途

### 构建与数据（根目录 + scripts/）

| 脚本 | 做什么 | 城市 | 谁调用 | 输出 |
|---|---|---|---|---|
| `build.py` | 引擎 + 城市数据 + Leaflet → 一个自包含页面；同步部署目录 | `--city`，默认 kamloops | check-all、deploy.sh、CI、测试 | `build/<城市>.html`、部署目录（Kamloops 是 `public/`） |
| `kamdata.py` | **所有脚本读写数据的唯一入口**，也放共用小工具（见下） | `use(城市)` 或环境变量 `LIFEGUIDE_CITY` | 约 30 个脚本 | — |
| `new-city.py` | 新城市骨架（city.json、data.js、PROFILE.md 等；城市事实都是 TODO，不带参照城市的事实） | 位置参数 `<id>` | 手动；`tests/engine/test_empty_city.py` | `cities/<id>/` |
| `holidays.py` | 按省规则生成法定假日 → `provinces/<省>/province.json`；`--apply` 写回同省各城市 | `--province`，默认 bc | 手动（validate 在假日表到期前 120 天提醒） | 省级文件、各城市 data.js |

### 校验与门禁

| 脚本 | 做什么 | 城市 | 谁调用 |
|---|---|---|---|
| `check-all.sh` | 构建 + 静态校验 + 经验库 + 一致性 + 全部浏览器测试；每项带耗时；`--quick` 不跑浏览器 | 遍历全部城市 | 手动（每次改完） |
| `validate.py` | 构建产物的约 140 条规则（语法、六语、来源分级、别城事实、省级设置一致、许可署名……） | `--city`，默认 kamloops | check-all、deploy.sh、CI |
| `consistency_check.py` | 各语言备注的数字和电话一致、区号、别城名字；`--strict` 用于草稿城市 | `--city` 必填 | check-all、CI |
| `knowledge.py` | 经验库、资产清单、数据来源目录：核对后生成页面；`--check` 只核对 | 不分城市 | check-all、CI |

### 导入（`importers/` + `bc_geocode.py`）

公共框架是 `importers/common.py`（出处、查重、锚点、译文与营业时间叠加）；每座城市的配置在 `cities/<城市>/import/config.json`。
全部 `--city` 必填，结果写回 `cities/<城市>/places.json`，出处写进 `import/provenance.json`。

| 脚本 | 来源 |
|---|---|
| `importers/bc_childcare.py` | 省持牌托儿（Child Care Map Data，OGL-BC） |
| `importers/bc_schools.py` | 省 K-12 学校 + 学区学校列表 |
| `importers/arcgis_parks.py` | 市政 ArcGIS 公园与设施 |
| `importers/gtfs_routes.py` | 公交运营方 GTFS |
| `importers/research_merge.py` | 官网调研结果（`import/research/*.json`） |
| `importers/apply_hours.py`、`importers/hours.py` | 营业时间原文 → 引擎格式 |
| `importers/apply_translations.py` | 套用 `import/translations.json` |
| `importers/tasks_from.py` | 从别的城市生成办事卡（`--from`）+ `import/task-overrides.json` |
| `bc_geocode.py` | BC 政府地址定位（带缓存 `data/geocode-cache.json`；得分 ≥ 95 才用） |

各来源的网址、许可、要注意的地方：[`docs/knowledge/数据来源目录.md`](../docs/knowledge/数据来源目录.md)。

### 审核与核实

| 脚本 | 做什么 | 城市 | 输出 |
|---|---|---|---|
| `review_checklist.py` | 上线差距表 + 按后果排序的核实清单（目标和参照城市在 city.json `review`） | `--city` 必填，`--ref` 可选 | `docs/reports/<城市>审核清单.md` |
| `verify_sheet.py` | 可打印的电话核实表（安全相关地点） | `--city` 必填 | 运营目录 `verification/` |

### 运维与巡检

| 脚本 | 做什么 | 城市 | 输出 |
|---|---|---|---|
| `monthly-quality-check.sh` | 每月：过期记录 + 链接检查 + 台账小结 | 位置参数 `[城市]`，默认 kamloops | `data/` 下的报告和台账 |
| `check-links.py` | 网址与深链检查 | `--city`，默认 kamloops | `data/check-links[-<城市>]-<日期>.log/.json` |
| `export-open.py` | 开放数据导出 + 超过 180 天未核实的记录 | `--city`，默认 kamloops | `build/`、`data/stale-POIs-*.md` |

### 统计（`analytics/`）

| 脚本 | 做什么 |
|---|---|
| `analytics/query-events.py` | 查询线上统计（预设：tasks、links、calls、help…）；`--city` 按城市筛 |
| `analytics/export-events.py` | 导出最近 N 天原始事件到 `data/exports/`（不入库） |
| `analytics/summarize-export.py` | 导出文件的一页摘要 |
| `analytics/analyze-events.py` | 分析浏览器 `?debug=1` 的本地导出（调试用） |

用法见 `docs/guides/埋点与日志查看分析手册.md`。

### 对外材料与部署（不在 scripts/ 里）

| 脚本 | 做什么 |
|---|---|
| `docs/source/builddocs.py` | 对外 PDF；只在部署后构建（对照线上版本号） |
| `flyers/buildflyer.py`、`flyers/mapart.py` | 传单、海报、地图插画（目前只做 Kamloops） |
| `deploy.sh` | 构建 → 校验（带 `--city`）→ wrangler → 线上探针；`--city`、`--dry-run`、`--verify-only` |
| `worker.js` | 线上：`/api/event` 写统计、给所有响应加安全头（所有城市共用） |

## 写脚本的约定

1. **读写城市数据一律经 `kamdata`**，不要自己用正则取 `const P=`。
2. **共用的东西从 `kamdata` 取**，不要再写一份：`kamdata.LANGS`（六种语言）、`kamdata.today(city)` / `month(city)`（城市当地日期，
   不用 `datetime.date.today()`——机器可能是 UTC，傍晚就跳到第二天）、`import_path` / `load_import`、`ops_dir()`、`ssl_context()`、
   `USER_AGENT`、`city_obj(city)`（CITY 设置）、`fingerprint` / `leak_markers`（别城事实）、`category_tiers()`（`schemas/category-tiers.json`）。
3. **城市**：新脚本用 `--city`（argparse）。会写数据的脚本 `--city` 必填；只读的可以默认 kamloops。
4. **不写死某座城市的值**（目标数、参照城市、区号、网址）：写进该城市的 `city.json`，或省级文件 `provinces/<省>/province.json`。
5. **会被 import 的文件名用下划线**（`bc_geocode.py`）；命令行脚本用连字符的老名字保留，**不为统一而改名**（外部定时任务、文档、经验库都引用了路径）。
6. **检查要会失败**：发现问题就以非 0 退出；只打印的报告在 check-all 里会显示成"通过"（`audit6.py` 曾经如此）。
7. 新脚本加进本页，并在 `docs/knowledge/lessons.json` 的 assets 里登记，然后 `python3 scripts/knowledge.py`。

## 有意不做的

- 统一文件名（连字符 / 下划线）、改统计数据集名 `kamloops_events`、改 Kamloops 不带城市后缀的输出文件名：破坏引用或丢历史数据，收益只有好看。
- 拆分 `tests/kamloops/regress.py`、合并 19 个 phase 测试：它们是 Kamloops 的基线依据；先看 check-all 的耗时，确有必要再改运行方式，不改断言。
- 旧的 11 份"找 kamdata 的路径循环"不逐个改：能用；新脚本照第 1–2 条写。
