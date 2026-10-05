# CLAUDE.md

Life Guide：面向新居民的多语言（六种）生活指南与地图。每座城市一个自包含 HTML，离线可用，部署在 Cloudflare Workers。
一套引擎 + 多个城市：Kamloops 已上线（线上版本 2026.09.24b），Kelowna 是草稿。文档入口：`docs/README.md`。

## 命令

```sh
python3 build.py                     # → build/kamloops.html，并同步 public/index.html（逐字节相同）
./scripts/check-all.sh --quick       # 构建并校验每座城市 + 经验库核对 + 跨语言一致性（无需 Playwright）
./scripts/check-all.sh               # 再加全部浏览器测试，约 25 分钟（需 .venv 里的 Playwright）
python3 scripts/consistency_check.py --city <id>   # 各语言备注的数字/电话一致、无别城名字（草稿城市在 check-all 里严格执行）
./deploy.sh                          # 构建 → 校验 → wrangler deploy → 线上探针（需 npm install）
./deploy.sh --verify-only            # 只跑线上探针
./deploy.sh --city <id> --dry-run    # 看某座城市的部署设置（网址、Worker、目录），不部署
python3 scripts/new-city.py <id> --name <Name> --centre <lat>,<lng>   # 新城市骨架（TODO 未清完 validate 不通过）
# city.json 里 "status": "draft" 的城市不能部署；Kelowna 目前是草稿，审核清单是 docs/reports/Kelowna审核清单.md
```

首次准备：`npm install`（锁定版本的 wrangler）；
`python3 -m venv .venv && .venv/bin/pip install playwright pypdf && .venv/bin/python -m playwright install chromium`。

## 结构

- `app/engine/` — 引擎，按 `parts.txt` 顺序拼成一个 HTML：`head.html`、`styles.css`、`body.html`、`js/*.js`（按功能分 19 个文件）、`tail.html`。`cities/<城市>/` — 城市数据：`city.json`（构建与部署配置）、`data.js`（手写部分，用 `/*@json*/` `/*@text*/` 引用其余文件）、`places.json` 等、`guide/<lang>.html`。字段说明见 `docs/guides/DATA-SCHEMA.md`，地点记录的结构由 `schemas/place.schema.json` 校验。
- `build.py` 把引擎、数据、`vendor/` 的 Leaflet 合成一个文件。**只改 `app/` 和 `cities/`，不要手改构建产物。** 脚本读写数据一律通过 `kamdata.py`。
- `scripts/` 校验、链接检查、开放数据导出、统计分析、导入（`importers/`）、审核与核实工具；索引见 `scripts/README.md`。只读的脚本 `--city` 默认 kamloops（build、validate、check-links、export-open），会写数据的必须写 `--city`；`check-all.sh` 遍历全部城市。
- 共用设置：`provinces/bc/province.json`（假日、热线、冬季提示，同省城市必须一致）；`schemas/category-tiers.json`（安全相关、可不收的商业类等）。脚本里的六语、当地日期、证书、导入路径一律从 `kamdata` 取。
- `tests/engine/` 引擎测试，用测试城市 `cities/_fixture/`（Testville，由 `tests/make-fixture-city.py` 生成，不要手改）；
  `tests/kamloops/` 线上城市的完整回归（索引见其 README）；`tests/<城市>/guitest.py` 每座城市的严格界面测试（check-all 自动跑）。
- `worker.js` 处理 `/api/event`（写 Analytics Engine）并给所有响应加安全头；城市无关，所有城市共用。
- 部署：每座城市一个 Worker（决策 D1），设置在 `city.json` 的 `deploy` 段；`app/pwa/` 是 sw.js / manifest / 图标模板，
  构建时按城市渲染到部署目录（Kamloops 是 `public/`，网址永久不变、不跳转）。统计按 `blob5` 区分城市，查询加 `--city`。
- `records/` 运营台账（访问、数据质量、反馈、商业假设；2026-10-04 前叫 `data/`）；`outreach/` 对外材料的源文件与构建脚本（PDF、传单、标志）；`docs/` 只放文档。
- 对外成品（外联邮件、PDF）不在仓库里，在同级目录 `../Guide to Life in Canada - ops/`。

## 知识库与工作循环（每次都要做，不是可选）

入口：`docs/knowledge/README.md`（扩城经验、规则、工具、官方来源目录、提示词）。目标是踩过的坑不再踩第二次：

1. **开工前**：`python3 scripts/knowledge.py --brief <阶段>`（立项 调研 画像 骨架 导入 核实 翻译 城市内容 引擎 上线 维护），
   先读"只有文档 / 待落实"的几条——没有检查兜底，只能靠这一步记住。新城市还要读 README 第三节"开工前必读"。
2. **发现问题时当场登记**：修完一个问题，问一句"别的城市会不会也这样"；会，就在 `docs/knowledge/lessons.json` 加一条
   （证据、规则、落在哪个文件的哪段标记、状态），能写成检查就写成检查（status auto），写不成就是 doc / todo。
3. **每轮结束**：迭代日志加一节"## 第 N 轮" → 本轮经验进 `lessons.json`（每一轮都必须至少有一条经验引用它，否则 check 失败；
   确实没有新经验就在标题写"（无新经验）"）→ `python3 scripts/knowledge.py` → `./scripts/check-all.sh --quick`。
4. **持续加固**：每轮从 `python3 scripts/knowledge.py --todo` 挑一两条"只靠人记"的经验，变成检查或工具。
5. 新的官方数据来源登记进 `docs/knowledge/sources.json`；新脚本按 `scripts/README.md` 的约定写并登记。

## 规则

- 页面内容一变，`app/engine/js/20-versions-templates-tasks.js` 里的 `DATA_VERSION` 必须改（`deploy.sh` 会拦）。
  缓存的静态资源有变化时，改该城市 `city.json` 的 `deploy.swCache`（模板在 `app/pwa/sw.js`；`public/sw.js` 是生成的）。
- 六种语言（zh/en/fr/es/ko/ja）"要么全译、要么不译"，`validate.py` 会检查。
- 数据记录要有来源分级 `src`（opendata / official / places / own）和核实月份 `v`，见 `docs/guides/DATA-SCHEMA.md`。
- 引擎里不放任何城市事实（电话、地址、地点编号、票价）；城市的事实写在 `cities/<城市>/data.js`（`validate.py` 会检查）。
- 改完至少跑 `./scripts/check-all.sh --quick`；改引擎行为要跑完整版。
- 部署、推送、对外发布、给合作方发邮件：先征得 Neil 同意。

## 当前计划

`docs/plans/2026-10-03-多城市工程化计划.md`（阶段 0–5 + 决策记录）。
待定事项由 Claude 按建议自主决定，并在该文件"决策记录"里标 **[自主决定]**；Neil 可追加推翻。
多城市改造期间：每一步都要和基线 `tests/baseline/` 对照，Kamloops 的行为和用户本地数据不能变。
