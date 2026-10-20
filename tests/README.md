# tests/ — 测试总览

全部运行：`./scripts/check-all.sh`（构建 + 静态校验 + 一致性 + 经验库 + 全部浏览器测试，本机约 25 分钟）；
只跑静态部分：`./scripts/check-all.sh --quick`。浏览器测试需要 `.venv` 里的 Playwright（安装步骤见根目录 `README.md`）。

| 目录 / 文件 | 测什么 | 用哪座城市 |
|---|---|---|
| `engine/test_fixture_city.py` | 引擎不依赖 Kamloops：第二座城市能加载、显示自己的名字、数据存在自己的存储前缀下 | 测试城市 Testville（`cities/_fixture/`） |
| `engine/test_popup_lifecycle.py` | 地点卡片该出现时出现、该消失时消失（新搜索不含它时关闭；读者关掉后不再回来） | 测试城市 |
| `engine/test_back_navigation.py` | 手机返回手势一层层退，"在地图上看"之后返回到原来的办事卡，不会意外离开网站 | 测试城市 |
| `engine/test_empty_city.py` | 刚由 `new-city.py` 生成、什么数据都没有的城市也能加载；骨架有 TODO 时 validate 必须拒绝 | 临时生成，跑完删除 |
| `make-fixture-city.py` | 从 Kamloops 数据生成测试城市（去掉 Kamloops 的城市文字，显示引擎默认值）；**不要手改 `cities/_fixture/`** | — |
| `kamloops/` | 线上城市的完整回归：主回归约 365 项、19 个阶段测试、两份审计；索引见 [`kamloops/README.md`](kamloops/README.md) | Kamloops |
| `city_guitest.py --city <城市>` | 每座城市的严格界面测试（81 项）：六种语言下页面、指南、帮助、分享、全部弹窗、公交面板里不出现**别的城市的事实**（`kamdata.leak_markers` 从各城数据推导，含 city.json `leakMarkers`）；没有未替换的占位符、`undefined`；电话链接能拨；常用搜索（含 city.json `review.guiQueries`）都有结果；看病列出全部 UPCC，"在地图上看"卡片保持打开；危机词直接给热线；每个分类和区域都有地点；办事卡六语可开；公交线路可选；收藏和语言刷新后保留；320–1280 像素无横向滚动；按钮有可读名称 | 每座城市（check-all 逐城运行） |
| `baseline/` | 多城市改造开始前（2026-10-03）的 Kamloops 基线：构建产物、测试结果、本地存储键。改造期间每一步对照它 | Kamloops |

**每座新城市**：不用复制测试。城市的标题、警察电话、UPCC、"附近"的起点、搜索示例都从城市数据取；只需在 city.json 写 `leakMarkers`（推导不出来的本城事实）和 `review.guiQueries`（本城特有的搜索词）。`check-all.sh` 会对每座城市运行。

**持续集成**（`.github/workflows/check.yml`，每次推送）：构建 Kamloops、Kelowna、测试城市并校验，经验库核对，草稿城市的跨语言一致性，
`public/` 与构建结果一致。浏览器测试耗时长，只在本机用 `check-all.sh` 跑。

**原则**（经验库 L-041–L-047）：门禁本身要被测试；测试按真实用户的顺序做事；行为按设计改变时改断言并写理由，不放宽测试；不写死数量。
