# tests/ — 测试总览

全部运行：`./scripts/check-all.sh`（构建 + 静态校验 + 一致性 + 经验库 + 全部浏览器测试，本机约 25 分钟）；
只跑静态部分：`./scripts/check-all.sh --quick`。浏览器测试需要 `.venv` 里的 Playwright（安装步骤见根目录 `README.md`）。

| 目录 / 文件 | 测什么 | 用哪座城市 |
|---|---|---|
| `engine/test_fixture_city.py` | 引擎不依赖 Kamloops：第二座城市能加载、显示自己的名字、数据存在自己的存储前缀下 | 测试城市 Testville（`cities/_fixture/`） |
| `engine/test_empty_city.py` | 刚由 `new-city.py` 生成、什么数据都没有的城市也能加载；骨架有 TODO 时 validate 必须拒绝 | 临时生成，跑完删除 |
| `make-fixture-city.py` | 从 Kamloops 数据生成测试城市（去掉 Kamloops 的城市文字，显示引擎默认值）；**不要手改 `cities/_fixture/`** | — |
| `kamloops/` | 线上城市的完整回归：主回归约 365 项、19 个阶段测试、两份审计；索引见 [`kamloops/README.md`](kamloops/README.md) | Kamloops |
| `kelowna/guitest.py` | 草稿城市的严格界面测试（约 80 项，六语、别城事实、全部弹窗与办事卡、布局）；见 [`kelowna/README.md`](kelowna/README.md) | Kelowna |
| `baseline/` | 多城市改造开始前（2026-10-03）的 Kamloops 基线：构建产物、测试结果、本地存储键。改造期间每一步对照它 | Kamloops |

**每座新城市**：复制 `kelowna/guitest.py` 到 `tests/<城市>/`，改禁用词表（参照城市的地名、电话、票价）、UPCC 名字和"附近"的坐标；
`check-all.sh` 会自动运行所有 `tests/*/guitest.py`。

**持续集成**（`.github/workflows/check.yml`，每次推送）：构建 Kamloops、Kelowna、测试城市并校验，经验库核对，草稿城市的跨语言一致性，
`public/` 与构建结果一致。浏览器测试耗时长，只在本机用 `check-all.sh` 跑。

**原则**（经验库 L-041–L-047）：门禁本身要被测试；测试按真实用户的顺序做事；行为按设计改变时改断言并写理由，不放宽测试；不写死数量。
