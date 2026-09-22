#!/usr/bin/env python3
"""
query-events.py — 在终端直接查 Cloudflare Analytics Engine 里的埋点数据。

配合 analyze-events.py 使用：
  - query-events.py  查**服务端**数据（所有用户 / 跨设备 / 可留存 90 天）  ← 主力
  - analyze-events.py 分析**本机**导出的 JSON（?debug=1 → Export JSON）   ← 调试

准备（只需做一次）
------------------
1. 创建 API Token（按 Cloudflare 官方文档的措辞）：
   https://dash.cloudflare.com/profile/api-tokens
     → Create Token → Create Custom Token
     Permissions:  Account | Account Analytics | Read
     Account Resources: Include | 你的账户（Neil Xiang's Account）
     TTL: 随便（建议 1 年）
   ⚠️ 注意：权限名是 "Account Analytics"，不是 "Analytics Engine"。
      列表里若看到 "Workers Analytics Engine Write" 那是给 Worker 写数据用的，
      查询要的是 "Account Analytics | Read"。
2. 保存 token（二选一）：
     export CF_API_TOKEN='xxxxx'                     # 当前 shell 有效
     echo 'xxxxx' > ~/.cf_token && chmod 600 ~/.cf_token   # 永久生效

用法
----
  ./query-events.py                     # 默认跑 health（数据体检）
  ./query-events.py types               # 事件类型分布
  ./query-events.py funnel              # 转化漏斗
  ./query-events.py gap                 # 搜索 0 结果 → 内容缺口清单
  ./query-events.py daily               # 每日趋势
  ./query-events.py lang                # 语言分布
  ./query-events.py places              # 被查看最多的地点
  ./query-events.py presets             # 预设标签热度
  ./query-events.py routes              # 公交线路需求
  ./query-events.py recent              # 最近 30 条原始事件
  ./query-events.py tasks               # 办事卡打开次数（按卡、按入口）
  ./query-events.py taskout             # 办事卡"有用 / 卡住了"反馈
  ./query-events.py links               # 用户点出去的外部网站（办事卡来源 / 卡内 / 指南）
  ./query-events.py feedback            # 点"报告错误 / 反馈"的次数
  ./query-events.py season              # 季节提醒：显示 / 点链接 / 关闭
  ./query-events.py help                # "求助"面板每日打开次数（不含拨了哪个号码）
  ./query-events.py session <sid>       # 单个会话的完整轨迹
  ./query-events.py --list              # 列出所有预设
  ./query-events.py "SELECT ..."        # 任意 SQL

真实用户 vs 维护者流量
--------------------
默认**只看真实用户**（自动追加 double2 != 1）。被排除的是：
  - 以 ?debug=1 打开的页面产生的所有事件
  - 每次 ./deploy.sh 部署后自动发的 deploy_smoke 冒烟事件
这些事件 props 里带 env:'dev'，Worker 会把它们写进 double2=1。
不加过滤的话，测试用的假地点 ID（如 p042）会混进「最常查看的地点」排名。
需要连维护者流量一起看时，在任意命令后加 --all：
  ./query-events.py recent --all

字段映射（worker.js 的 writeDataPoint 决定）
------------------------------------------
  blob1     = sid      匿名会话 ID（客户端生成，跨刷新复用）
  blob2     = t        事件类型（小写下划线）
  blob3     = props    JSON 字符串（≤2048 字符）
  blob4     = lang     界面语言          blob5 = city   城市 key
  blob6     = host     站点域名          blob7 = p.src  入口（task_open / guide_open 等）
  blob8     = p.id || p.task             地点 / 办事卡 / 季节提醒的 id
  blob9     = p.cat    分类
  blob10    = p.kind || p.target || p.to || p.mode   动作类型或外链域名
  blob11    = ver      数据版本
  double1   = d        客户端 Date.now()（毫秒，时钟可能不准）
  double2   = env      1 = 维护者流量（?debug=1 / 部署冒烟），0 = 真实用户
  index1    = t        同 blob2，用于加速过滤
  timestamp =          CF 服务端接收时间 ← **做时间过滤用这个，不要用 double1**
"""

import json

# macOS 上 python.org 版的 Python 不带系统钥匙串的根证书，不处理的话每次调用
# Cloudflare API 都会 CERTIFICATE_VERIFY_FAILED，得手动 export SSL_CERT_FILE。
# 有 certifi 就直接用，省掉那条要记的环境变量。
try:
    import certifi, ssl as _ssl, urllib.request as _ureq
    _ureq.install_opener(_ureq.build_opener(
        _ureq.HTTPSHandler(context=_ssl.create_default_context(cafile=certifi.where()))))
except Exception:
    pass
import os
import sys
import time
import urllib.error
import urllib.request

ACCOUNT_ID = "d25d00a8131224f4d2caf2165d134db0"
DATASET = "kamloops_events"
API = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/analytics_engine/sql"

# ---- 预设查询 ---------------------------------------------------------------
# ⚠ Analytics Engine SQL API 的限制（已在脚本里全部规避）：
#   ✗ 顶层无 success 字段，HTTP 200 即成功，错误靠 HTTP 状态码返回
#   ✗ 无 uniq() / groupUniqArray() —— 用 count(DISTINCT col)
#   ✗ 无 UNION ALL / 子查询 —— funnel 拆 5 查、types 去掉 pct
#   ✗ 无 JSONExtractString 等 JSON 函数 —— places/presets/routes 改 GROUP BY blob3，
#     由 render() 用 json.loads() 后处理
#   ⚠ formatDateTime 的 %M = 月份全名（POSIX 语义），分钟要用 %i
PRESETS = {
    "health": (
        "数据体检：数据进来了没、多少个会话、最后一条什么时候",
        f"""
SELECT count() AS events,
       count(DISTINCT blob1) AS sessions,
       count(DISTINCT blob2) AS event_types,
       formatDateTime(min(timestamp), '%Y-%m-%d %H:%i') AS first_seen,
       formatDateTime(max(timestamp), '%Y-%m-%d %H:%i') AS last_seen
FROM {DATASET}
WHERE timestamp > NOW() - INTERVAL '7' DAY AND double2 != 1
""",
    ),
    "types": (
        "事件类型分布（哪些操作最频繁，有多少人触发）",
        f"""
SELECT blob2 AS event_type,
       count() AS n,
       count(DISTINCT blob1) AS users
FROM {DATASET}
WHERE timestamp > NOW() - INTERVAL '7' DAY AND double2 != 1
GROUP BY blob2 ORDER BY n DESC
""",
    ),
    "funnel": (
        "转化漏斗：打开 → 浏览地点 → 查看 popup → 点 CTA（真的要联系了）",
        # 拆 5 查，由 main() 在结果前拼接
        f"""
SELECT count(DISTINCT blob1) AS users FROM {DATASET} WHERE blob2='panel_open' AND timestamp > NOW() - INTERVAL '7' DAY AND double2 != 1
""",
    ),
    "funnel_marker": (
        "funnel 第 3 步：marker_view",
        f"""
SELECT count(DISTINCT blob1) AS users FROM {DATASET} WHERE blob2='marker_view' AND timestamp > NOW() - INTERVAL '7' DAY AND double2 != 1
""",
    ),
    "funnel_cta": (
        "funnel 第 4 步：cta_click",
        f"""
SELECT count(DISTINCT blob1) AS users FROM {DATASET} WHERE blob2='cta_click' AND timestamp > NOW() - INTERVAL '7' DAY AND double2 != 1
""",
    ),
    "funnel_fav": (
        "funnel 第 5 步：fav_toggle",
        f"""
SELECT count(DISTINCT blob1) AS users FROM {DATASET} WHERE blob2='fav_toggle' AND timestamp > NOW() - INTERVAL '7' DAY AND double2 != 1
""",
    ),
    "funnel_category": (
        "funnel 第 2 步：category/preset toggle",
        f"""
SELECT count(DISTINCT blob1) AS users FROM {DATASET} WHERE blob2 IN ('category_toggle','preset_toggle') AND timestamp > NOW() - INTERVAL '7' DAY AND double2 != 1
""",
    ),
    "gap": (
        "内容缺口清单：搜了但 0 结果的词 → 这就是下一轮该补的数据",
        f"""
SELECT blob3 AS props, count() AS n, count(DISTINCT blob1) AS users
FROM {DATASET}
WHERE blob2 = 'search_empty' AND timestamp > NOW() - INTERVAL '30' DAY AND double2 != 1
GROUP BY blob3 ORDER BY n DESC LIMIT 50
""",
    ),
    "daily": (
        "每日趋势（判断推广/改版有没有带来真实变化）",
        f"""
SELECT toDate(timestamp) AS day,
       count() AS events,
       count(DISTINCT blob1) AS sessions,
       count(DISTINCT blob2) AS kinds
FROM {DATASET}
WHERE timestamp > NOW() - INTERVAL '30' DAY AND double2 != 1
GROUP BY day ORDER BY day
""",
    ),
    "lang": (
        "语言分布：用户最终停在哪种语言（判断默认英文是否合理）",
        f"""
SELECT blob3 AS props, count() AS switches, count(DISTINCT blob1) AS users
FROM {DATASET}
WHERE blob2 = 'lang_change' AND timestamp > NOW() - INTERVAL '30' DAY AND double2 != 1
GROUP BY blob3 ORDER BY switches DESC
""",
    ),
    "places": (
        "被查看最多的地点（marker_view）→ 数据质量/内容投入的优先级",
        # JSON 解析在 render() 里做（AE 无 JSON 函数）
        f"""
SELECT blob3 AS props, count() AS views, count(DISTINCT blob1) AS users
FROM {DATASET}
WHERE blob2 = 'marker_view' AND timestamp > NOW() - INTERVAL '30' DAY AND double2 != 1
GROUP BY blob3 ORDER BY views DESC LIMIT 200
""",
    ),
    "presets": (
        "快捷预设标签热度 → 哪类需求是主流画像",
        f"""
SELECT blob3 AS props, count() AS n, count(DISTINCT blob1) AS users
FROM {DATASET}
WHERE blob2 = 'preset_toggle' AND timestamp > NOW() - INTERVAL '30' DAY AND double2 != 1
GROUP BY blob3 ORDER BY n DESC LIMIT 200
""",
    ),
    "routes": (
        "公交线路需求排名 → 哪些线路要重点补全",
        f"""
SELECT blob3 AS props, count() AS selects, count(DISTINCT blob1) AS users
FROM {DATASET}
WHERE blob2 = 'route_select' AND timestamp > NOW() - INTERVAL '30' DAY AND double2 != 1
GROUP BY props ORDER BY selects DESC LIMIT 100
""",
    ),
    "tasks": (
        "办事卡打开次数：哪张卡最常被打开、从哪里打开",
        f"""
SELECT blob8 AS card, blob7 AS src, count() AS opens, count(DISTINCT blob1) AS users
FROM {DATASET}
WHERE blob2 = 'task_open' AND timestamp > NOW() - INTERVAL '30' DAY AND double2 != 1
GROUP BY card, src ORDER BY opens DESC LIMIT 100
""",
    ),
    "taskout": (
        "办事卡反馈：\"有用\" 还是 \"卡住了\"（卡住多的卡优先重写）",
        f"""
SELECT blob8 AS card, blob3 AS props, count() AS n
FROM {DATASET}
WHERE blob2 = 'task_outcome' AND timestamp > NOW() - INTERVAL '90' DAY AND double2 != 1
GROUP BY card, props ORDER BY n DESC LIMIT 100
""",
    ),
    "links": (
        "用户点出去的外部网站：task_src=卡片官方来源 / task_link=卡内其他链接 / guide_link=指南正文",
        f"""
SELECT blob2 AS kind, blob8 AS card, blob10 AS site, count() AS clicks, count(DISTINCT blob1) AS users
FROM {DATASET}
WHERE blob2 IN ('task_src','task_link','guide_link') AND timestamp > NOW() - INTERVAL '30' DAY AND double2 != 1
GROUP BY kind, card, site ORDER BY clicks DESC LIMIT 100
""",
    ),
    "feedback": (
        "点 \"报告错误 / 反馈\" 的次数（place=地点弹窗 · task=办事卡翻译纠错 · general=通用反馈链接）",
        f"""
SELECT blob10 AS kind, blob8 AS id, count() AS clicks
FROM {DATASET}
WHERE blob2 = 'feedback_click' AND timestamp > NOW() - INTERVAL '90' DAY AND double2 != 1
GROUP BY kind, id ORDER BY clicks DESC LIMIT 100
""",
    ),
    "season": (
        "季节提醒：显示了多少次、点了哪个链接、关掉多少次",
        f"""
SELECT blob8 AS season, blob2 AS event, blob10 AS site, count() AS n, count(DISTINCT blob1) AS users
FROM {DATASET}
WHERE blob2 IN ('season_shown','season_link','season_close') AND timestamp > NOW() - INTERVAL '90' DAY AND double2 != 1
GROUP BY season, event, site ORDER BY season, n DESC
""",
    ),
    "help": (
        "\"求助\" 面板每日打开次数（只有打开这一个动作；拨了哪个号码从不记录）",
        f"""
SELECT toDate(timestamp) AS day, count() AS opens, count(DISTINCT blob1) AS users
FROM {DATASET}
WHERE blob2 = 'help_open' AND timestamp > NOW() - INTERVAL '30' DAY AND double2 != 1
GROUP BY day ORDER BY day
""",
    ),
    "recent": (
        "最近 30 条原始事件（确认数据格式 / 排查故障）",
        f"""
SELECT timestamp, blob1 AS sid, blob2 AS type, blob3 AS props
FROM {DATASET}
WHERE double2 != 1
ORDER BY timestamp DESC LIMIT 30
""",
    ),
}


def get_token():
    tok = os.environ.get("CF_API_TOKEN", "").strip()
    if tok:
        return tok, "环境变量 CF_API_TOKEN"
    path = os.path.expanduser("~/.cf_token")
    if os.path.isfile(path):
        with open(path) as f:
            tok = f.read().strip()
        if tok:
            return tok, f"文件 {path}"
    return None, None


def run_sql(token, sql):
    # NOTE: this endpoint is NOT JSON — Cloudflare expects the raw SQL text as
    # the request body. Sending {"query": "..."} returns 422 "sql parser error:
    # Expected an SQL statement, found: {".
    body = sql.encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/plain",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read().decode()
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:600]
        print(f"✗ HTTP {e.code} 来自 Cloudflare API", file=sys.stderr)
        print(detail, file=sys.stderr)
        if e.code == 403:
            print(
                "\n提示：403 通常是 token 权限不足。重建 token 时权限选\n"
                "  Account | Account Analytics | Read\n"
                "（不是 'Analytics Engine | Read'），并把 Account Resources 选对你的账户。",
                file=sys.stderr,
            )
        sys.exit(1)
    except Exception as e:
        print(f"✗ 请求失败：{e}", file=sys.stderr)
        sys.exit(1)

    resp = json.loads(raw)
    # 注意：Analytics Engine SQL API 顶层无 success 字段（与 CF REST API 不同）。
    # HTTP 200 + 顶层包含 meta/data 即视为成功。
    if "meta" not in resp or "data" not in resp:
        print("✗ 响应结构异常：", file=sys.stderr)
        print(json.dumps(resp, ensure_ascii=False, indent=2)[:600], file=sys.stderr)
        sys.exit(1)
    return resp


def render(preset_name, result):
    data = result.get("data") or []
    meta = result.get("meta") or []
    rows = result.get("rows")

    # 特殊预设：places/presets/routes 解析 props JSON 按目标键聚合
    JSON_KEYS = {
        "places":  ["id", "cat"],
        "presets": ["id", "action"],
        "routes":  ["id"],
        "lang":    ["from", "to"],
    }
    if preset_name in JSON_KEYS and data and "props" in (data[0] if data else {}):
        keys = JSON_KEYS[preset_name]
        # views 列：places→views, presets→n, routes→selects, lang→switches
        views_field = {
            "places": "views", "presets": "n",
            "routes": "selects", "lang": "switches",
        }[preset_name]
        agg = {}
        for row in data:
            try:
                p = json.loads(row.get("props", "") or "{}")
            except Exception:
                continue
            kt = tuple(str(p.get(k, "?")) for k in keys)
            if kt not in agg:
                agg[kt] = 0
            agg[kt] += int(row.get(views_field) or 0)
        rows_out = sorted(
            [{"key": "/".join(kt), views_field: v} for kt, v in agg.items()],
            key=lambda x: -x[views_field],
        )
        if not rows_out:
            print("（无数据）")
            return
        col_key = "key"
        widths = [max(len(col_key), max(len(str(r[col_key])) for r in rows_out)),
                  max(len(views_field), max(len(str(r[views_field])) for r in rows_out))]
        print("+" + "+".join("-" * (w + 2) for w in widths) + "+")
        print("| " + col_key.ljust(widths[0]) + " | " + views_field.ljust(widths[1]) + " |")
        print("+" + "+".join("=" * (w + 2) for w in widths) + "+")
        for r in rows_out:
            print("| " + str(r[col_key]).ljust(widths[0])[:widths[0]] + " | " + str(r[views_field]).ljust(widths[1]) + " |")
        print("+" + "+".join("-" * (w + 2) for w in widths) + "+")
        print(f"\n{len(rows_out)} 行（按 props 解析后聚合；AE 无 JSON 函数 + GROUP BY blob3 时不能保留 distinct，"
              "users 列已弃）")
        return

    if not data:
        print("（查询成功，但没有数据）")
        if rows == 0:
            print("\n可能原因：Analytics Engine 有 5-10 分钟索引延迟；或这个时间窗内确实没有事件。")
        return

    cols = [m.get("name") for m in meta] or list(data[0].keys())
    widths = []
    for c in cols:
        w = max(len(str(c)), max(len(str(row.get(c, ""))) for row in data))
        widths.append(min(w, 60))

    def line(ch="-"):
        return "+" + "+".join(ch * (w + 2) for w in widths) + "+"

    print(line())
    print("| " + " | ".join(str(c).ljust(widths[i])[: widths[i]] for i, c in enumerate(cols)) + " |")
    print(line("="))
    for row in data:
        cells = []
        for i, c in enumerate(cols):
            v = str(row.get(c, ""))
            if len(v) > 60:
                v = v[:57] + "..."
            cells.append(v.ljust(widths[i]))
        print("| " + " | ".join(cells) + " |")
    print(line())
    print(f"\n{len(data)} 行（服务端返回 rows={rows}）")


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    # --all: 保留维护者流量（?debug=1 页面 + deploy.sh 冒烟测试）。
    # 默认排除，否则测试用的假地点 ID 会混进「最常查看的地点」排名。
    include_dev = False
    if "--all" in args:
        include_dev = True
        args = [a for a in args if a != "--all"]

    if args[0] == "--list":
        print("可用预设：\n")
        for k, (desc, _) in PRESETS.items():
            print(f"  {k:10s}  {desc}")
        print(f"\n  {'session':10s}  单个会话轨迹，用法：./query-events.py session <sid>")
        print(f"  {'<SQL>':10s}  任意 SQL，用引号包起来")
        print(f"\n  {'--all':10s}  加在任意命令后：连维护者流量（?debug=1 + 部署冒烟）一起算")
        print(f"{'':12s}  默认只看真实用户（double2 != 1）")
        sys.exit(0)

    token, src = get_token()
    if not token:
        print("✗ 没找到 Cloudflare API token。\n", file=sys.stderr)
        print("二选一：", file=sys.stderr)
        print("  export CF_API_TOKEN='你的token'", file=sys.stderr)
        print("  echo '你的token' > ~/.cf_token && chmod 600 ~/.cf_token\n", file=sys.stderr)
        print("创建 token：https://dash.cloudflare.com/profile/api-tokens", file=sys.stderr)
        print("  权限：Account | Account Analytics | Read", file=sys.stderr)
        sys.exit(1)

    if args[0] == "session":
        if len(args) < 2:
            print("用法：./query-events.py session <sid>", file=sys.stderr)
            print("（sid 可在浏览器 F12 Console 跑 localStorage.getItem('kamloopsSid') 拿到）", file=sys.stderr)
            sys.exit(1)
        sid = args[1].replace("'", "''")
        desc = f"会话 {args[1]} 的完整轨迹"
        sql = (
            f"SELECT timestamp, blob2 AS type, blob3 AS props "
            f"FROM {DATASET} WHERE blob1 = '{sid}' "
            f"AND timestamp > NOW() - INTERVAL '7' DAY AND double2 != 1 ORDER BY timestamp"
        )
        preset_name = None
    elif args[0] == "funnel":
        # 跑 5 个独立查询（AE 不支持 UNION ALL），合并展示
        print("▸ 转化漏斗：打开 → 浏览地点 → 查看 popup → 点 CTA（真的要联系了）")
        print(f"  token 来源：{src}\n")
        steps = [
            ("1 panel_open",      PRESETS["funnel"][1]),
            ("2 category/preset", PRESETS["funnel_category"][1]),
            ("3 marker_view",     PRESETS["funnel_marker"][1]),
            ("4 cta_click",       PRESETS["funnel_cta"][1]),
            ("5 fav_toggle",      PRESETS["funnel_fav"][1]),
        ]
        if include_dev:
            steps = [(l, s.replace(" AND double2 != 1", "")) for l, s in steps]
            print("（--all：含维护者流量）")
        width_step = max(len(s) for s, _ in steps)
        width_users = 8
        print("+" + "-" * (width_step + 2) + "+" + "-" * (width_users + 2) + "+")
        print("| " + "step".ljust(width_step) + " | " + "users".ljust(width_users) + " |")
        print("+" + "=" * (width_step + 2) + "+" + "=" * (width_users + 2) + "+")
        for label, sql in steps:
            r = run_sql(token, sql)
            d = (r.get("data") or [{}])[0]
            u = d.get("users", "?")
            print("| " + label.ljust(width_step) + " | " + str(u).ljust(width_users) + " |")
            time.sleep(0.3)
        print("+" + "-" * (width_step + 2) + "+" + "-" * (width_users + 2) + "+")
        sys.exit(0)
    elif args[0] in PRESETS:
        desc, sql = PRESETS[args[0]]
        preset_name = args[0]
    else:
        desc, sql = "自定义查询", " ".join(args)
        preset_name = None

    if include_dev:
        sql = sql.replace(" AND double2 != 1", "").replace("WHERE double2 != 1\n", "")
        desc += "（含维护者流量）"

    print(f"▸ {desc}")
    print(f"  token 来源：{src}\n")
    render(preset_name, run_sql(token, sql))


if __name__ == "__main__":
    main()
