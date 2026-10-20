# 文档地图

> 2026-10-04 整理。所有文档从这里进；项目本身（构建、测试、部署）先看根目录 `README.md`。
> 上一次整理是 2026-09-16（目录规则）；这次按"现行 / 证据 / 历史"重新分层，并对照代码改正了过时的内容。
> 这次整理的分析和改动清单：[`reports/2026-10-04-文档审计与整理.md`](reports/2026-10-04-文档审计与整理.md)。

## 一、按要做的事找

| 我要… | 先读 | 再读 |
|---|---|---|
| 了解这个项目 | 根目录 `README.md` | `CHANGELOG.md`（版本与改动） |
| 开一座新城市 | [`knowledge/README.md`](knowledge/README.md)（开工前必读 10 条） | [`guides/新城市操作手册.md`](guides/新城市操作手册.md)（每一步的命令）→ [`guides/新城市扩展方法论与标准.md`](guides/新城市扩展方法论与标准.md)（原则与上线标准） |
| 改城市数据 | [`guides/DATA-SCHEMA.md`](guides/DATA-SCHEMA.md)（字段、城市设置、省级设置、城市文字、校验规则） | 该城市的 `cities/<城市>/PROFILE.md` |
| 找官方数据来源 | [`knowledge/数据来源目录.md`](knowledge/数据来源目录.md)（按联邦 / 省 / 区域 / 市，网址、许可、导入工具、要注意的地方） | |
| 找某个脚本 | [`../scripts/README.md`](../scripts/README.md)（用途、`--city`、谁调用、输出到哪里） | |
| 改引擎 | 根目录 `CLAUDE.md`（规则） | [`../tests/README.md`](../tests/README.md)（测试）、[`knowledge/经验库.md`](knowledge/经验库.md)（为什么有这些检查） |
| 维护线上城市 | [`../records/README.md`](../records/README.md)（台账与每月巡检） | [`guides/埋点与日志查看分析手册.md`](guides/埋点与日志查看分析手册.md)（看统计） |
| 让代理去调研、翻译、复核 | [`knowledge/prompts/`](knowledge/prompts/) | |
| 想产品方向 | [`guides/新移民画像与需求.md`](guides/新移民画像与需求.md)、[`guides/多方视角与产品方向.md`](guides/多方视角与产品方向.md)（第八节是待办总表） | [`reports/2026-10-04-三方视角缺点与改进.md`](reports/2026-10-04-三方视角缺点与改进.md) |
| 知道某个决定为什么这样定 | [`plans/2026-10-03-多城市工程化计划.md`](plans/2026-10-03-多城市工程化计划.md)（文首状态核对 + 决策记录 D1–D5） | |
| 做对外材料（PDF、传单） | 本页第四节 | 运营资料目录 `../Guide to Life in Canada - ops/` |

## 二、目录

`docs/` 只放文档。对外材料的源文件和构建脚本在 `../outreach/`，运营台账在 `../records/`，脚本说明在 `../scripts/README.md`。

| 目录 | 放什么 | 性质 |
|---|---|---|
| `knowledge/` | 知识库：经验登记表 `lessons.json`（生成 `经验库.md`、`资产清单.md`）、来源登记表 `sources.json`（生成 `数据来源目录.md`），`prompts/` 提示词模板 | **现行**，由 `scripts/knowledge.py` 对照代码核对 |
| `guides/` | 长期手册：方法论与标准、新城市操作手册、DATA-SCHEMA、埋点与日志手册、新移民画像、多方视角 | **现行**，与代码不符就改 |
| `plans/` | 多城市工程化计划（含状态核对与决策记录）、城市差异建模分析 | **现行**（计划随进度更新） |
| `reports/` | 仍在使用的报告：Kamloops 经验总结、Kelowna 扩城迭代日志、三方视角分析、交接与发展方案、Kelowna 审核清单（生成的）、本次文档审计 | **证据**，不改正文，只追加 |
| `archive/` | 历史：上线前后的审计和方案、2026-09 的报告（`archive/reports/`）、跑过一次的脚本、旧传单 | **历史**，只读，见 [`archive/README.md`](archive/README.md) |

**reports/ 里的文件**

| 文件 | 是什么 |
|---|---|
| `2026-10-03-Kamloops经验总结.md` | Kamloops 一路的经验，每条附出处（经验库的证据） |
| `2026-10-03-Kelowna扩城迭代日志.md` | Kelowna 每一轮做了什么、发现什么、改了什么（每轮一节，持续追加） |
| `2026-10-04-三方视角缺点与改进.md` | 从新移民、移民服务中心、政府角度看工具的缺点与优先级 |
| `2026-09-25-交接与发展方案-中文审阅稿.md` | 交给机构运营的方案：预算、资金窗口、12 周交接、授权条款 |
| `Kelowna审核清单.md` | `scripts/review_checklist.py --city kelowna` 生成，每次数据变化后重跑（不要手改） |
| `2026-10-04-文档审计与整理.md` | 本次文档整理的分析与改动 |

## 三、文档的规则

1. **一个事实只写在一处**，别处引用。经验写在 `knowledge/lessons.json`；字段写在 DATA-SCHEMA；命令写在操作手册。
2. **数字从代码或数据现取**，不手写（地点数、办事卡数、版本号……）。手写的数字会过时——对外 PDF 就因此印过"14 张卡"。
3. **生成的文件不手改**：`knowledge/经验库.md`、`knowledge/资产清单.md`、`knowledge/数据来源目录.md`、`reports/<城市>审核清单.md`、`public/index.html`。
4. **现行文档与代码不符就改现行文档**；证据和历史文档不改正文——要更正，在现行文档里写，或在 `archive/README.md` 里加一行说明。
5. **归档时不改文件名**（经验总结用 R0910、CA 这类缩写引用它们）；归档前把文中仍有用的内容搬进现行文档，并在 `archive/README.md` 的"内容去了哪里"登记。
6. 台账（`records/`）只记真实发生的事，不放示例。
7. 每轮迭代结束：迭代日志加一轮 → 新经验进 `lessons.json` → `python3 scripts/knowledge.py` → `./scripts/check-all.sh --quick`。

## 四、对外材料（PDF）怎么做

正文写在 `../outreach/pdf/content/*.txt`（纯文本，一个文档一个文件），**不要直接改 PDF**。数字用占位符，构建时从城市数据和页面现取：
`{PLACES}` `{TASKS}` `{CATS}` `{AREAS}` `{ROUTES}` `{STOPS}` `{APPROX}` `{THEMES}` `{VERSION}` `{VERIFIED}` `{PREPARED}` `{PREPARED_ZH}` `{URL}` `{EMAIL}`。

```bash
python3 outreach/pdf/builddocs.py               # 全部重建 → ../Guide to Life in Canada - ops/public/<日期>/
python3 outreach/pdf/builddocs.py zh-complete   # 只建一份
python3 outreach/pdf/builddocs.py --html-only   # 只出 HTML（outreach/pdf/_build/），不需要 Playwright，也不查线上版本
```

- **只在部署之后建 PDF**：脚本会读线上版本号，与 `public/index.html` 不一致就拒绝（PDF 上印的版本必须是读者能打开的）；草稿可加 `--allow-undeployed`，但不要发出去。
- 改了功能，就检查对外文字（2026-10-04 发现已发出的 PDF 仍写着"人权投诉倒计时"和"红色热线条"，见本次文档审计）。
- 变更说明写在那一批的 `CHANGES.md` 里，不进 PDF。截图（`../outreach/pdf/assets/img_*.png`）跟随界面改版重拍。

## 五、写脚本时读写数据

一律经根目录的 `kamdata.py`（括号配平解析，不用正则）：

```python
import kamdata
kamdata.use('kelowna')               # 选城市（默认 kamloops）
P = kamdata.load('P')                # 也可以 'TASKS' / 'BR' / 'RI' / 'LANDMARKS'
CI = kamdata.load('CI', engine=True) # 引擎里的分类
kamdata.save('P', P)                 # 写回 cities/<城市>/places.json（缩进格式）
kamdata.today()                      # BC 当地日期（不看机器时区；已处理 2026-11-01 起的全年夏令时）
```
