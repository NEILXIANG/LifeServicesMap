#!/usr/bin/env python3
"""
summarize-export.py — 读 export-events.py 导出的 JSON，给出一页"真实用户"摘要。

用法（项目根目录）：
    python3 scripts/analytics/summarize-export.py                  # 读 data/exports/ 里最新的导出
    python3 scripts/analytics/summarize-export.py path/to/file.json
    python3 scripts/analytics/summarize-export.py --keep-bots      # 不过滤扫描器 / 链接预览

默认过滤（2026-09-22 起，依据最近 5 天数据的观察）：
  - 维护者流量：double2=1（?debug=1、?maintainer=1 标记过的设备、部署冒烟）——导出时已排除；
  - 扫描器 / 链接预览：会话 id 为 "invalid"（浏览器禁用了存储，邮件安全扫描的典型特征），
    或整个会话除了打开 / 关闭 / service worker 之外没有任何操作、且停留不到 5 秒。
被过滤的会话数会单独列出，不会悄悄消失。
"""
import glob
import json
import os
import statistics
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PASSIVE = {'session_start', 'session_end', 'sw_register', 'tile_probe', 'tile_fallback', 'offline_shown'}


def load(path):
    rows = json.load(open(path, encoding='utf-8'))['rows']
    for r in rows:
        try:
            r['p'] = json.loads(r.get('props') or '{}')
        except Exception:
            r['p'] = {}
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    keep_bots = '--keep-bots' in sys.argv
    path = args[0] if args else (sorted(glob.glob(os.path.join(ROOT, 'data', 'exports', 'events-*.json'))) or [None])[-1]
    if not path:
        sys.exit('✗ data/exports/ 里没有导出文件，先跑 scripts/analytics/export-events.py')
    rows = load(path)
    S = defaultdict(list)
    for r in rows:
        S[r['sid']].append(r)

    def dur(ev):
        d = [e['p'].get('dur', 0) for e in ev if e['t'] == 'session_end']
        return max(d) if d else 0

    bots = {sid for sid, ev in S.items()
            if sid == 'invalid' or (all(e['t'] in PASSIVE for e in ev) and dur(ev) < 5)}
    real = {sid: ev for sid, ev in S.items() if keep_bots or sid not in bots}
    R = [r for ev in real.values() for r in ev]

    print('📄 %s' % os.path.relpath(path, ROOT))
    print('时间范围  %s → %s' % (rows[0]['timestamp'][:16], rows[-1]['timestamp'][:16]) if rows else '（空）')
    print('会话      %d 个真实会话（另过滤扫描器 / 链接预览 %d 个）' % (len(real), 0 if keep_bots else len(bots)))
    print('事件      %d 条' % len(R))
    starts = [e for e in R if e['t'] == 'session_start']
    c = lambda k: Counter(e['p'].get(k) for e in starts).most_common()
    print('版本      %s' % Counter(e['ver'] for e in R).most_common())
    print('语言      %s' % Counter(e['lang'] for e in starts).most_common())
    print('设备      %s' % c('dev'))
    print('来源      ref=%s  src=%s' % (c('ref'), c('src')))
    print('回访      %s' % Counter('首次' if (e['p'].get('visits') or 1) <= 1 else '回访' for e in starts).most_common())
    ds = [dur(ev) for ev in real.values() if dur(ev) > 0]
    if ds:
        print('停留      中位数 %ds（开着不关的标签页会拉高平均值，所以只看中位数）' % statistics.median(ds))
    acted = sum(1 for ev in real.values() if any(e['t'] not in PASSIVE for e in ev))
    print('有操作的会话  %d / %d' % (acted, len(real)))

    print('\n—— 做了什么 ——')
    for t, n in Counter(e['t'] for e in R if e['t'] not in PASSIVE).most_common(20):
        print('  %-20s %d' % (t, n))
    q = Counter((e['p'].get('q') or '') for e in R if e['t'] == 'search_run')
    if q:
        print('\n搜索词    %s' % q.most_common(15))
    qe = Counter((e['p'].get('q') or '') for e in R if e['t'] == 'search_empty')
    if qe:
        print('0 结果     %s   ← 下一批该补的内容' % qe.most_common(15))
    qc = Counter((e['p'].get('q') or '') for e in R if e['t'] == 'search_empty' and e['p'].get('closest'))
    if qc:
        print('  其中改显示了最接近结果的  %s' % qc.most_common(15))
    gs = Counter(e['p'].get('src') for e in R if e['t'] == 'guide_open' and str(e['p'].get('src', '')).startswith('search'))
    if gs:
        print('从搜索打开的办事卡  %s' % gs.most_common())
    for t, label in (('marker_view', '看过的地点'), ('task_open', '打开的办事卡'), ('cta_click', '联系动作'),
                     ('task_call', '办事卡里点电话'), ('task_src', '办事卡官方来源'), ('feedback_click', '反馈'),
                     ('search_help_click', '看病答案框')):
        v = Counter((e.get('id') or e['p'].get('id') or '') + ('/' + e['p'].get('kind') if e['p'].get('kind') else '')
                    for e in R if e['t'] == t)
        if v:
            print('%s  %s' % (label, v.most_common(10)))


if __name__ == '__main__':
    main()
