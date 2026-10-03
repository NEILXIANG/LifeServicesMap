# 文档总索引

> **2026-10-03 起（决策 D4）：** `public/`（对外成品 PDF）和 `outreach/`（外联名单、邮件、素材），
> 以及根目录的 `outreach-emails-docx/`，已移到仓库外的同级目录 `../Guide to Life in Canada - ops/`。
> 下文提到的 `public/`、`outreach/` 都指那个目录。`builddocs.py` 默认输出到那里，
> 也可用环境变量 `LIFEGUIDE_OPS` 指定别的位置。见 `docs/plans/2026-10-03-多城市工程化计划.md`。

这个项目的文档过去散在六个地方（根目录、archive/、data/、Claude outputs/、docs/、facebook-推广/），
共 50 多份，找一份要翻半天。2026-09-16 统一收拢到 `docs/` 下，规则如下。

## 目录怎么分

| 目录 | 放什么 | 会不会给外人看 |
|---|---|---|
| `public/<日期>/` | **对外材料成品**（介绍、使用说明、传单的 PDF），每次更新建一个新日期目录，旧的原样保留 | 会 |
| `source/` | 对外材料的**正文源文件**、图片和构建脚本 `builddocs.py` | 不会 |
| `guides/` | 长期有效的操作手册（数据结构说明、埋点与日志查看分析手册） | 不会 |
| `reports/` | 一次性的审查／自查报告，按日期命名 | 不会 |
| `outreach/` | 机构外联与 Facebook 推广的名单、分析、附件、素材 | 部分 |
| `archive/` | 已完成、已废弃、被后来版本取代的历史文档，只留档不维护 | 不会 |

两个例外，**刻意没有搬进来**：

- `data/` —— 运营日志（周报、反馈、数据质量、商业假设）。`tools/monthly-quality-check.sh`
  会往里写文件，`deploy.sh` 也拿 `data/business-hypothesis.md` 当敏感路径探针，搬走会同时弄坏两个脚本。
- 根目录的 `README.md` 和 `CHANGELOG.md` —— 仓库惯例，放根目录才找得到。

## 对外材料：每次更新怎么做

正文写在 `source/content/*.txt` 里（纯文本，一个文档一个文件）。**不要直接改 PDF**——
2026-09-16 之前那批 PDF 没有源文件，改一句话要动 PDF 内部，这就是这套源文件存在的原因。

```bash
cd "<项目根目录>"
python3 docs/source/builddocs.py            # 全部重建
python3 docs/source/builddocs.py zh-complete # 只建一份
python3 docs/source/builddocs.py --html-only # 没装 playwright 时，只出 HTML 自己在浏览器里打印
```

脚本会按**当天日期**在 `public/` 下建目录，PDF 写进去；HTML 中间产物放 `source/_build/`（不入库）。
旧目录一律不动，所以任何时候都能对比两批材料的差别。

数字不要手写。地点数、办事卡数、分类数、区域数、公交线数、站点数、"大致位置"条数、主题数、
版本号、核实日期，全部由脚本在构建时从 `cities/kamloops/`（经 kamdata）和 `public/index.html` 现取
（占位符 `{PLACES}` `{TASKS}` `{CATS}` `{AREAS}` `{ROUTES}` `{STOPS}` `{APPROX}` `{THEMES}`
`{VERSION}` `{VERIFIED}`）。曾经因为手写数字出过错，别再手写。

**变更说明写在 `public/<日期>/CHANGES.md` 里，不进对外 PDF。** 对外材料本身不谈自己改过什么。

## 现在有哪些批次

- `public/2026-09-16/` —— **当前版本**。九份材料，第一次由 `source/` 生成。
- `public/2026-09-14/` —— 上一版，手工排版、无源文件。留档备查，不要再改。

## 长期手册在哪

- `guides/DATA-SCHEMA.md` —— 数据结构与"引擎不含城市事实"的约束。
- `guides/埋点与日志查看分析手册.md` —— 怎么查真实用户数据（`query-events.py`、Analytics Engine、
  Web Analytics、`?debug=1`）。**注意**：这份手册写于 2026-09-05，后来新增的事件
  （`open_now_toggle`、`guide_open.src`、`privacy_expand` 等）还没补进去，用之前先对一眼事件表。

## 工程目录（2026-09-16 整理后）

```
项目根/
  README.md  CHANGELOG.md  .gitignore
  wrangler.toml  worker.js        部署约定，必须在根
  build.py  deploy.sh             最常用的两条命令
  src/                            引擎 + 每城一份数据（不要往里塞城市无关的东西）
  public/                         唯一会上云的目录——放进去的东西会原样公开
  build/                          全部构建产物（gitignore）
  scripts/                        长期脚本：validate / check-links / export-open
    analytics/                    query-events / analyze-events
    data/                         addrecs / complex / fixcoords / themes
    monthly-quality-check.sh
  tests/                          regress / tasktest / audit6 / soci2
  flyers/                         传单源码 buildflyer.py + mapart.py
  data/                           运营日志（被两个脚本引用，不要移动）
  docs/                           见上文
```

**路径约定**：所有脚本都用 `_project_root()` 向上查找 `app/engine/parts.txt` 来定位项目根，
因此整个项目可以移动到任何目录（含中文和空格的路径已实测），脚本也可以从任意工作目录调用。
唯一的例外是 `deploy.sh` 里指向本机 wrangler/npx 的绝对路径，找不到时会自动回退到 PATH。

**搬迁时记得带上 `node_modules`**（或先 `npm install`）：`build.py` 会把 Leaflet 内联进单文件，
缺了它会退回 CDN 引用、离线能力失效——脚本会打印 `! ... not found locally` 警告，别忽略。

---

## 脚本共用的数据入口：根目录 `kamdata.py`

任何要读写城市数据（`cities/<city>/`）或引擎源码的脚本都从它取，不要再各写一遍正则：

```python
import os, sys
_r = os.path.dirname(os.path.abspath(__file__))
for _ in range(6):
    if os.path.exists(os.path.join(_r, 'kamdata.py')): break
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
import kamdata

P = kamdata.load('P')                  # 也可以 'TASKS' / 'BR' / 'RI'
CI = kamdata.load('CI', engine=True)   # CI 在 app/engine/ 里
kamdata.save('P', P)                   # 写回 cities/kamloops/places.json（缩进格式）
kamdata.data_text()                    # 展开后的完整城市数据 JS（与页面里的一致）
kamdata.today()                        # Kamloops 当地日期（不看构建机器时区）
```

它同时负责向上找项目根，所以脚本在哪个目录下跑都一样。
跑过一次的迁移脚本收在 `docs/archive/scripts/`，见那里的 README。
