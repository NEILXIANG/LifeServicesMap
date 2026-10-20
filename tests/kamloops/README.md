# tests/kamloops/ — Kamloops 回归测试

针对线上城市 Kamloops 的完整回归：断言里用到 Kamloops 的真实地点、地址、任务卡，所以只对 `build/kamloops.html` 有意义。
按"第几轮修复"命名是历史原因；每个文件覆盖什么见下表（取自各文件开头的说明）。
城市无关的引擎测试在 `tests/engine/`，用测试城市 `cities/_fixture/` 跑。

全部运行：`./scripts/check-all.sh`

| 文件 | 覆盖内容 |
|---|---|
| `soci2.py` | 社会服务卡片（connect、hardship）：六种语言、分组、搜索命中 |
| `audit6.py` | Audit pass 6 (2026-09-10): the data layer, mechanically.  |
| `audit7.py` | 2026-09-22 — independent functional audit (written from scratch, not derived from the earlier suites). Every check recomputes the expected answer from the raw |
| `regress.py` | **主回归套件**，约 365 项：搜索、筛选、弹窗、地图、公交、收藏、多语言、打印、统计、无障碍…… 按修复轮次编号（"72 …" 即第 72 轮） |
| `tasktest.py` | 办事指南面板：打开、任务列表、任务卡 |
| `phase1test.py` | Phase 1 (2026-09-21) — safety and trust. Checks the built page. |
| `phase2test.py` | Phase 2 (2026-09-21) — the serious data fixes, checked in the built page. |
| `phase3test.py` | Phase 3 (2026-09-21) — holidays, appointment-only places, freshness label. |
| `phase4test.py` | Phase 4 (2026-09-21) — systemic cleanup, checked in the built page. |
| `phase5test.py` | Phase 5 (2026-09-21) — task-card conditions; step counts unchanged. |
| `phase6test.py` | Phase 6 (2026-09-21) — coverage additions. |
| `phase7test.py` | Phase 7 (2026-09-21) — residents, and the Nation's own names. |
| `phase8test.py` | 2026-09-22 — three new cards and the seasonal reminder. |
| `phase9test.py` | 2026-09-22 — link fixes (p9) and the new tracking events (p10). |
| `phase10test.py` | 2026-09-22 — follow-ups from the 5-day analytics review: version bump, walk-in-clinic search, maintainer-device flag. |
| `phase11test.py` | 2026-09-22 — search dead ends (suggestions 1, 4, 5 from the analytics review): closest matches when nothing matches every word, the task card leading the |
| `phase12test.py` | 2026-09-22 — the search synonym table (SYN), and the closest-match fallback never hiding better matches behind a category/area filter. |
| `phase13test.py` | 2026-09-22 — plan B: a search pauses the category filter; areas, themes, open now and near me still apply; turning a category on ends a search. |
| `phase14test.py` | 2026-09-24 — the 15 elementary schools added from the province's K-12 dataset (p21): every record complete, findable in six languages, and claiming nothing |
| `phase15test.py` | 2026-09-24 — licensed child care imported from the province's Child Care Map (p25), the provincial source label and its attribution (p23), and school hours |
| `phase16test.py` | 2026-09-24 — the icon audit (p26): the "free" theme is no longer a dollar sign, parks use an emoji old phones can draw, the suitcase and the briefcase are |
| `phase17test.py` | 2026-09-24 — the popup rebuild (p27), the token convergence (p28) and the flat map pin (p29): one chip vocabulary, one type scale, one radius set, one shape |
| `phase18test.py` | 2026-09-24 — before the public demo: six languages end to end (p30), and the marker cluster is never changed while it animates (p31). |
| `phase19test.py` | 2026-09-24 (p33) — "Open now" is an errand filter: it no longer puts the crisis lines under the filter row. The lines stay wherever they answer a real need. |
