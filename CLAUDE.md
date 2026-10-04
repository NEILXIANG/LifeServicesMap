# CLAUDE.md

Kamloops Life Guide：面向新居民的多语言（六种）生活服务地图。单个自包含 HTML，离线可用，
部署在 Cloudflare Workers。正在改造成"一套引擎 + 多个城市"（下一个：Kelowna）。

## 命令

```sh
python3 build.py                     # → build/kamloops.html，并同步 public/index.html（逐字节相同）
./scripts/check-all.sh --quick       # 构建 + validate.py（无需 Playwright）
./scripts/check-all.sh               # 再加全部浏览器测试（需 .venv 里的 Playwright）
./deploy.sh                          # 构建 → 校验 → wrangler deploy → 线上探针（需 npm install）
./deploy.sh --verify-only            # 只跑线上探针
```

首次准备：`npm install`（锁定版本的 wrangler）；
`python3 -m venv .venv && .venv/bin/pip install playwright pypdf && .venv/bin/python -m playwright install chromium`。

## 结构

- `app/engine/` — 引擎，按 `parts.txt` 顺序拼成一个 HTML：`head.html`、`styles.css`、`body.html`、`js/*.js`（按功能分 18 个文件）。`cities/kamloops/` — 城市数据：`city.json`（构建期配置）、`data.js`（手写部分，用 `/*@json*/` `/*@text*/` 引用其余文件）、`places.json` 等、`guide/<lang>.html`。字段说明见 `docs/guides/DATA-SCHEMA.md`，地点记录的结构由 `schemas/place.schema.json` 校验。
- `build.py` 把引擎、数据、`vendor/` 的 Leaflet 合成一个文件。**只改 `app/` 和 `cities/`，不要手改构建产物。** 脚本读写数据一律通过 `kamdata.py`。
- `scripts/` 校验、链接检查、开放数据导出、统计分析，都接受 `--city <id>`（默认 kamloops）。
- `tests/engine/` 引擎测试，用测试城市 `cities/_fixture/`（Testville，由 `tests/make-fixture-city.py` 生成，不要手改）；
  `tests/kamloops/` 线上城市的完整回归（索引见其 README）。
- `worker.js` 处理 `/api/event`（写 Analytics Engine）并给所有响应加安全头。
- 运营资料（外联邮件、对外 PDF）不在仓库里，在同级目录 `../Guide to Life in Canada - ops/`。

## 规则

- 页面内容一变，`app/engine/js/20-versions-templates-tasks.js` 里的 `DATA_VERSION` 必须改（`deploy.sh` 会拦）。
  `public/sw.js` 里 STATIC_ASSETS 有变化时要改 `CACHE`。
- 六种语言（zh/en/fr/es/ko/ja）"要么全译、要么不译"，`validate.py` 会检查。
- 数据记录要有来源分级 `src`（official/own/第三方）和核实月份 `v`，见 `docs/guides/DATA-SCHEMA.md`。
- 改完至少跑 `./scripts/check-all.sh --quick`；改引擎行为要跑完整版。
- 部署、推送、对外发布、给合作方发邮件：先征得 Neil 同意。

## 当前计划

`docs/plans/2026-10-03-多城市工程化计划.md`（阶段 0–5 + 决策记录）。
待定事项由 Claude 按建议自主决定，并在该文件"决策记录"里标 **[自主决定]**；Neil 可追加推翻。
多城市改造期间：每一步都要和基线 `tests/baseline/` 对照，Kamloops 的行为和用户本地数据不能变。
