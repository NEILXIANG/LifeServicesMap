#!/usr/bin/env python3
"""assistant/kit/watch.py — 看助手的健康状况和用户反馈（不调用 AI，不花钱）。

    python3 assistant/kit/watch.py            # 健康检查 + 近 30 天反馈 + AI 故障
    python3 assistant/kit/watch.py health     # 只做健康检查（适合每天定时跑；有问题时退出码为 1）
    python3 assistant/kit/watch.py feedback [天数]

健康检查：页面能打开、危机提问直接给热线、AI 密钥仍然有效（/api/health?deep=1 用 Anthropic 不收费的接口核对）。
2026-11-11 密钥失效后，AI 回答停了一段时间才被发现——这个检查就是为了下次第一时间知道。
反馈和故障来自 Analytics Engine 数据集 kamloops_assistant_events（和指南的 kamloops_events 分开）；
查询用 ~/.cf_token（Account Analytics | Read），和 scripts/analytics/query-events.py 一样。只有"有用/有错/没回答"和一句去掉数字邮箱的说明，没有提问原文。
"""
import json, os, sys, urllib.error, urllib.request

try:   # macOS 上 python.org 版 Python 没有系统根证书（同 query-events.py）
    import certifi, ssl
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where()))))
except Exception:
    pass

SITE = os.environ.get('ASSISTANT_URL', 'https://kamloops-assistant.neilxiang.workers.dev')
ACCOUNT_ID = 'd25d00a8131224f4d2caf2165d134db0'
DATASET = 'kamloops_assistant_events'
API = f'https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/analytics_engine/sql'


def http(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode()


def health():
    problems = []
    try:
        code, _ = http(SITE + '/')
        if code != 200: problems.append('首页 HTTP %s' % code)
    except Exception as e:
        problems.append('首页打不开：%s' % e)
    try:
        _, body = http(SITE + '/api/health?deep=1')
        h = json.loads(body)
        if not h.get('ai'): problems.append('Worker 里没有 AI 密钥')
        if h.get('key_ok') is False: problems.append('AI 密钥无效（过期或被删除）——到 Console 新建，存 ~/.anthropic_key，再 wrangler secret put')
        if h.get('key_ok') is None: problems.append('暂时核对不了密钥（网络或限流），稍后再查')
    except urllib.error.HTTPError as e:
        problems.append('健康检查 HTTP %s' % e.code)
    except Exception as e:
        problems.append('健康检查失败：%s' % e)
    try:
        _, body = http(SITE + '/api/ask', data=json.dumps({'q': 'My husband hits me', 'uiLang': 'en'}).encode(),
                       headers={'Content-Type': 'application/json', 'Origin': SITE}, method='POST')
        if json.loads(body).get('status') != 'crisis': problems.append('危机提问没有直接给出热线')
    except Exception as e:
        problems.append('危机检查失败：%s' % e)
    print('健康检查：' + ('全部正常' if not problems else '有问题'))
    for p in problems: print('  ✗ ' + p)
    return not problems


def sql(q):
    tok = os.environ.get('CF_API_TOKEN', '').strip()
    path = os.path.expanduser('~/.cf_token')
    if not tok and os.path.isfile(path): tok = open(path).read().strip()
    if not tok: sys.exit('没有 Cloudflare token（~/.cf_token），见 scripts/analytics/query-events.py 顶部说明')
    try:
        _, body = http(API, data=q.encode(), headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'text/plain'}, method='POST')
    except urllib.error.HTTPError as e:
        sys.exit('Cloudflare API HTTP %s：%s' % (e.code, e.read().decode()[:300]))
    return json.loads(body).get('data', [])


def feedback(days=30):
    w = f"timestamp > NOW() - INTERVAL '{int(days)}' DAY"
    print(f'\n近 {days} 天的反馈（有用 / 有错 / 没回答我的问题）：')
    rows = sql(f"SELECT blob2 AS verdict, blob3 AS status, SUM(_sample_interval) AS n FROM {DATASET} "
               f"WHERE blob1 = 'feedback' AND {w} GROUP BY verdict, status ORDER BY n DESC")
    if not rows: print('  （还没有）')
    for r in rows: print('  %-9s 回答类型 %-16s %s 次' % (r['verdict'], r['status'], r['n']))
    notes = sql(f"SELECT timestamp, blob2 AS verdict, blob4 AS lang, blob5 AS note FROM {DATASET} "
                f"WHERE blob1 = 'feedback' AND blob5 != '' AND {w} ORDER BY timestamp DESC LIMIT 30")
    if notes:
        print('\n附带的说明（数字和邮箱已被去掉）：')
        for r in notes: print('  %s  %-8s %-4s %s' % (str(r['timestamp'])[:16], r['verdict'], r['lang'], r['note']))
    errs = sql(f"SELECT blob2 AS reason, SUM(_sample_interval) AS n, max(timestamp) AS last FROM {DATASET} "
               f"WHERE blob1 = 'ai_error' AND {w} GROUP BY reason ORDER BY n DESC")
    print(f'\n近 {days} 天 AI 没能回答的次数：' + ('无' if not errs else ''))
    for r in errs: print('  %-18s %s 次，最近一次 %s' % (r['reason'], r['n'], str(r['last'])[:16]))


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['health']:
        sys.exit(0 if health() else 1)
    if a[:1] == ['feedback']:
        feedback(int(a[1]) if len(a) > 1 else 30); sys.exit(0)
    ok = health()
    feedback()
    sys.exit(0 if ok else 1)
