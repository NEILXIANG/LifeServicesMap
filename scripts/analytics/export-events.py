#!/usr/bin/env python3
"""
export-events.py — 把最近 N 天的埋点原始数据导出成一个 JSON 文件，方便整体分析。

用法（在项目根目录）：
    python3 scripts/analytics/export-events.py            # 最近 5 天，只含真实用户
    python3 scripts/analytics/export-events.py --days 7
    python3 scripts/analytics/export-events.py --all      # 连维护者流量（?debug=1、部署冒烟）一起导出

输出：records/exports/events-<天数>d-<日期>.json（records/exports/ 已在 .gitignore 里，不会进仓库）

token 的读取方式与 query-events.py 完全相同（环境变量 CF_API_TOKEN 或 ~/.cf_token），
本脚本不打印、不保存 token。导出文件里只有埋点本身：匿名会话 id、事件类型、
props（搜索词已在客户端清洗过）、语言、版本等，没有 IP、没有姓名。
"""
import importlib.util
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
spec = importlib.util.spec_from_file_location("qe", os.path.join(HERE, "query-events.py"))
qe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qe)

COLS = ("blob1 AS sid, blob2 AS t, blob3 AS props, blob4 AS lang, blob5 AS city, blob6 AS host, "
        "blob7 AS src, blob8 AS id, blob9 AS cat, blob10 AS kind, blob11 AS ver, double1 AS client_ts, double2 AS dev")
PAGE = 5000   # rows per request; pages walk back by timestamp so nothing is dropped or doubled


def main():
    args = qe.take_city_arg(sys.argv[1:])
    days = 5
    if "--days" in args:
        days = int(args[args.index("--days") + 1])
    include_dev = "--all" in args
    token, src = qe.get_token()
    if not token:
        sys.exit("✗ 没找到 Cloudflare API token（与 query-events.py 相同：export CF_API_TOKEN=... 或 ~/.cf_token）")

    dev = "" if include_dev else " AND double2 != 1"
    rows, before = [], None
    while True:
        cond = "timestamp > NOW() - INTERVAL '%d' DAY%s" % (days, dev)
        if before:
            cond += " AND timestamp < toDateTime('%s')" % before
        sql = "SELECT timestamp, %s FROM %s WHERE %s ORDER BY timestamp DESC LIMIT %d" % (COLS, qe.DATASET, cond, PAGE)
        data = qe.run_sql(token, sql).get("data") or []
        if not data:
            break
        rows.extend(data)
        if len(data) < PAGE:
            break
        before = data[-1]["timestamp"]
        # rows sharing the boundary second would be skipped by '<'; fetch that second exactly
        same = qe.run_sql(token, "SELECT timestamp, %s FROM %s WHERE timestamp = toDateTime('%s')%s" % (COLS, qe.DATASET, before, dev)).get("data") or []
        seen = {json.dumps(r, sort_keys=True) for r in rows if r["timestamp"] == before}
        rows.extend(r for r in same if json.dumps(r, sort_keys=True) not in seen)
        time.sleep(0.3)

    rows.sort(key=lambda r: r["timestamp"])
    out_dir = os.path.join(ROOT, "records", "exports")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "events-%dd-%s.json" % (days, datetime.now().strftime("%Y%m%d-%H%M")))
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"exported": datetime.now().isoformat(timespec="seconds"), "days": days,
                   "include_dev": include_dev, "rows": rows}, f, ensure_ascii=False, indent=0)
    sessions = len({r.get("sid") for r in rows})
    print("✓ 导出 %d 条事件，%d 个会话 → %s" % (len(rows), sessions, os.path.relpath(out, ROOT)))


if __name__ == "__main__":
    main()
