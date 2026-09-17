# docs/archive/scripts/ — 跑过一次、已经生效的迁移脚本

这里放的是**一次性数据迁移**：它们的结果早已写进 `src/data-kamloops.js`，
留着是为了说明某个字段当初是怎么来的，不是为了再跑一遍。

多数已经**跑不动了**——它们按显示名索引记录（`'⭐⭐ Kamloops Immigrant Services'`、
`'BMO(North Shore)'`），而这些名字后来改过，所以断言会直接失败。
这是设计如此：宁可响亮地停下，也不要静默地改错记录。

| 文件 | 做过什么 | 生效于 | 现在再跑 |
|---|---|---|---|
| `addrecs-2026-09-07.py` | 新增 3 条记录，改写 Salvation Army 的备注 | 2026-09-07 | 断言失败（记录已存在），且 `src` 后来已从 stub 升为 official |
| `complex-2026-09-10.py` | 给同一楼址的记录互相打 `sameComplex`；降一个坐标精度 | 2026-09-10 | 断言失败（`BMO(North Shore)` 已改名） |
| `fixcoords-2026-09-10.py` | 按街道线性几何重拟坐标 | 2026-09-10 | **不要跑**：非幂等（第二遍锚点更少），且街道键截断到 14 字符会把 `Trans-Canada Hwy` 和 `Trans-Canada Hwy E` 合成一条街 |
| `themes-2026-09-10.py` | 从分类 + 一张 33 条的人工表推导 `t`（主题）字段 | 2026-09-10 | 断言失败（`YMCA-YWCA of Kamloops(Downtown Y)` 已改名）；要重推主题得先把表里的名字对齐 |
| `history-2026-09-10.py` | 早期数据沿革整理 | 2026-09-10 | — |
| `ingest-2026-09-10.py` | 早期批量导入 | 2026-09-10 | — |

要新写一个改数据的脚本，从 `kamdata.py` 起步：

```python
import os, sys
_r = os.path.dirname(os.path.abspath(__file__))
for _ in range(6):
    if os.path.exists(os.path.join(_r, 'kamdata.py')): break
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
import kamdata

P = kamdata.load('P')
...
kamdata.save('P', P)        # 只替换 P 那一段，排版保持一条记录一行
```

它负责定位项目根、括号配平地解析、原样写回。**不要**再写一遍
`re.search(r'const P=(\[.*?\]);')` —— 那个正则悄悄依赖"`];` 只在结尾出现"，
备注里多一个 `]` 就会静默截错。
