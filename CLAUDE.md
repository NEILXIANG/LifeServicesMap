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
`python3 -m venv .venv && .venv/bin/pip install playwright && .venv/bin/python -m playwright install chromium`。

## 结构

- `src/engine.html` — 引擎（HTML+CSS+JS 单文件，约 7400 行）。`src/data-kamloops.js` — 城市数据。
- `build.py` 把引擎、数据、`vendor/` 的 Leaflet 合成一个文件。**只改 `src/`，不要手改构建产物。**
- `scripts/` 校验、链接检查、开放数据导出、统计分析；`tests/` 浏览器测试（Playwright）。
- `worker.js` 处理 `/api/event`（写 Analytics Engine）并给所有响应加安全头。
- 运营资料（外联邮件、对外 PDF）不在仓库里，在同级目录 `../Guide to Life in Canada - ops/`。

## 规则

- 页面内容一变，`src/engine.html` 里的 `DATA_VERSION` 必须改（`deploy.sh` 会拦）。
  `public/sw.js` 里 STATIC_ASSETS 有变化时要改 `CACHE`。
- 六种语言（zh/en/fr/es/ko/ja）"要么全译、要么不译"，`validate.py` 会检查。
- 数据记录要有来源分级 `src`（official/own/第三方）和核实月份 `v`，见 `docs/guides/DATA-SCHEMA.md`。
- 改完至少跑 `./scripts/check-all.sh --quick`；改引擎行为要跑完整版。
- 部署、推送、对外发布、给合作方发邮件：先征得 Neil 同意。

## 当前计划

`docs/plans/2026-10-03-多城市工程化计划.md`（阶段 0–5 + 决策记录）。
待定事项由 Claude 按建议自主决定，并在该文件"决策记录"里标 **[自主决定]**；Neil 可追加推翻。
多城市改造期间：每一步都要和基线 `tests/baseline/` 对照，Kamloops 的行为和用户本地数据不能变。
