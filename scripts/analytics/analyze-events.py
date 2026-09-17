#!/usr/bin/env python3
"""analyze-events.py — 分析 ?debug=1 导出的埋点 JSON

用法:
    python3 analyze-events.py /path/to/kamloops-events-XXXX.json
    python3 analyze-events.py /path/to/*.json   # 批量分析多个导出

输出:
    - 会话概况（事件数 / 时长 / 频率）
    - 事件类型分布 + 百分比
    - 操作时间线（按事件序号重建）
    - 关键洞察（语言路径、预设最终态、公交查询等）
    - 数据质量 8 项健康度检查
    - 可回答的业务问题清单
"""
import sys
import json
from collections import Counter
from pathlib import Path

# 字段含义速查表（供维护者参考）
EVENT_SCHEMAS = {
    'lang_change':    {'from': '原语言', 'to': '新语言'},
    'preset_toggle':  {'id': '预设 id', 'action': 'add/remove', 'active': '累计激活数'},
    'panel_open':     {'mode': '面板类型 area/cat/bus/fav', 'prev': '前一个面板'},
    'panel_close':    {'mode': '面板类型'},
    'route_select':   {'id': '公交线路 id', 'action': 'select/deselect'},
    'search_run':     {'q_len': '查询长度（不存原词，防 PII）', 'len': '冗余字段'},
    'search_empty':   {'q_len': '0 结果查询的长度', 'filters': '当时激活的筛选'},
    'marker_view':    {'id': '地点 id', 'cat': '分类', 'reg': '区域'},
    'marker_cta':     {'id': '地点 id', 'cta': 'nav/call/web/share'},
    'share_click':    {'method': 'clipboard/native'},
    'category_toggle':{'id': '分类 id', 'action': 'add/remove', 'active': '累计'},
    'region_toggle':  {'id': '区域 id', 'action': 'add/remove', 'active': '累计'},
    'fav_toggle':     {'id': '收藏 id', 'action': 'add/remove'},
    'reset_all':      {},
    'clear_filter':   {'target': 'search/area/cat/route/all'},
    'all_areas':      {},
    'lang_switch':    {'from': '原', 'to': '新'},  # 与 lang_change 同义，保留兼容
}


def load_events(path):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    events = data.get('events', [])
    if not events:
        sys.exit(f"  ⚠  {path} 没有 events 字段")
    return events, data.get('exported', '?')


def summarize(events):
    first, last = events[0]['d'], events[-1]['d']
    duration_s = (last - first) / 1000
    return {
        'count':    len(events),
        'first':    first,
        'last':     last,
        'duration': duration_s,
        'rate':     len(events) / max(duration_s, 0.001),
    }


def print_header(title):
    bar = '═' * 60
    print(f'\n{bar}\n {title}\n{bar}')


def print_section(title):
    # 注意运算次序：* 比 + 紧。原来等价于 ('\n─'*30) + ('\n {title}\n─'*30)，
    # 于是每个小节都先刷 30 行横线，再把标题印 30 遍。
    bar = '─' * 30
    print(f'\n{bar}\n {title}\n{bar}')


def quality_checks(events):
    # 这个函数的职责就是发现缺字段的导出，所以自己不能因为缺字段而 KeyError
    opens = sum(1 for e in events if e.get('t') == 'panel_open')
    closes = sum(1 for e in events if e.get('t') == 'panel_close')
    return [
        ('时间戳单调递增',
         all(events[i]['d'] <= events[i+1]['d'] for i in range(len(events)-1))),
        ('所有事件有 p 字段', all('p' in e for e in events)),
        ('所有事件有 t 字段', all('t' in e for e in events)),
        ('时间间隔 < 60s（人手操作）',
         all(0 < (events[i+1]['d']-events[i]['d']) < 60000 for i in range(len(events)-1))),
        ('lang_change 必有 from/to',
         all(set((e.get('p') or {}).keys()) >= {'from','to'} for e in events if e.get('t')=='lang_change')),
        ('preset_toggle 必有 id/action/active',
         all(set((e.get('p') or {}).keys()) >= {'id','action','active'} for e in events if e.get('t')=='preset_toggle')),
        # 原来断言"恰好剩一个没关"，用户把面板全关掉反而被判成"埋点系统有问题"
        ('panel open/close 配对（未关的不该多于 1 个）', 0 <= opens - closes <= 1),
        ('无搜索关键词（隐私保护）',
         not any('q' in e.get('p',{}) for e in events)),
    ]


def describe_event(e):
    """一行人话。字段缺了就退回原始字典——这个脚本是用来检查导出好不好的，
    不能被一条字段不全的事件整个打断（原来会在时间线中途抛 KeyError）。"""
    try:
        return _describe(e)
    except Exception:
        return '%s: %s' % (e.get('t', '?'), e.get('p'))


def _describe(e):
    t, p = e.get('t', '?'), e.get('p') or {}
    if t == 'lang_change':
        return f"语言: {p['from']} → {p['to']}"
    if t == 'preset_toggle':
        act = '启用' if p['action'] == 'add' else '关闭'
        return f"预设 {p['id']:10s} {act}（累计 {p['active']}）"
    if t == 'panel_open':
        return f"打开 {p['mode']} 面板（前: {p['prev']}）"
    if t == 'panel_close':
        return f"关闭 {p['mode']} 面板"
    if t == 'route_select':
        return f"公交线路: 选 {p['id']} 号"
    if t == 'search_run':
        return f"搜索（长度 {p.get('q_len','?')}）"
    if t == 'search_empty':
        return f"搜索 0 结果（长度 {p.get('q_len','?')}）"
    if t == 'marker_view':
        return f"查看标记 {p.get('id','?')} ({p.get('cat','?')})"
    if t == 'marker_cta':
        return f"点 CTA: {p.get('cta','?')} → {p.get('id','?')}"
    if t == 'category_toggle':
        return f"分类 {p['id']}: {'加' if p['action']=='add' else '去'}"
    if t == 'region_toggle':
        return f"区域 {p['id']}: {'加' if p['action']=='add' else '去'}"
    if t == 'fav_toggle':
        return f"收藏 {p['id']}: {'加' if p['action']=='add' else '去'}"
    if t == 'share_click':
        return f"分享（{p.get('method','?')}）"
    if t == 'reset_all':
        return "重置全部"
    if t == 'clear_filter':
        return f"清除筛选: {p.get('target','?')}"
    if t == 'all_areas':
        return "全选区域"
    return f"{t}: {p}"


def analyze_file(path):
    print_header(f"📄 {path}")
    events, exported = load_events(path)
    summary = summarize(events)
    print(f" 导出时间:  {exported}")
    print(f" 事件总数:  {summary['count']} 条")
    print(f" 会话时长:  {summary['duration']:.1f} 秒")
    print(f" 操作频率:  {summary['rate']:.2f} 事件/秒")

    # 分布
    print_section("事件类型分布")
    counts = Counter(e.get('t', '?') for e in events)
    total = len(events)
    for t, c in sorted(counts.items(), key=lambda x: -x[1]):
        bar = '█' * min(c * 3, 60)   # 封顶：一种事件 300 次会刷出 900 个方块
        pct = 100 * c / total
        print(f" {t:18s} {c:>3}  {pct:>5.1f}%  {bar}")

    # 时间线
    print_section("操作时间线")
    prev_t = events[0].get('d', 0)
    for i, e in enumerate(events, 1):
        dt_ms = e.get('d', prev_t) - prev_t
        rel = f"+{dt_ms/1000:.1f}s" if i > 1 else "+0.0s"
        prev_t = e.get('d', prev_t)
        print(f" {i:>2}. [{rel:>6}]  {describe_event(e)}")

    # 洞察
    print_section("关键洞察")
    lang_path = ['en']
    for e in events:
        if e.get('t') == 'lang_change':
            lang_path.append((e.get('p') or {}).get('to', '?'))
    print(f" • 语言切换路径: {' → '.join(lang_path)}（{len(lang_path)-1} 次）")

    presets_on = set()
    for e in events:
        if e.get('t') == 'preset_toggle':
            pp = e.get('p') or {}
            if pp.get('action') == 'add':
                presets_on.add(pp.get('id'))
            else:
                presets_on.discard(pp.get('id'))
    if presets_on:
        print(f" • 预设最终激活: {len(presets_on)} 个 — {sorted(presets_on)}")

    bus = [(e.get('p') or {}).get('id') for e in events if e.get('t') == 'route_select']
    if bus:
        print(f" • 公交线路查询: {bus}")

    panels = [(e.get('p') or {}).get('mode', '?') for e in events if e.get('t') == 'panel_open']
    if panels:
        print(f" • 面板切换路径: {' → '.join(panels)}")

    empty_q = [(e.get('p') or {}).get('q_len', '?') for e in events if e.get('t') == 'search_empty']
    if empty_q:
        print(f" • 搜索 0 结果: {len(empty_q)} 次（说明用户有未被满足的需求）")

    # 数据质量
    print_section("数据质量评估")
    all_ok = True
    for name, ok in quality_checks(events):
        print(f" {'✓' if ok else '✗'}  {name}")
        all_ok = all_ok and ok
    print(f"\n 整体结论: 埋点系统 {'完美运行' if all_ok else '有问题'}")


def main():
    if len(sys.argv) < 2:
        sys.exit("用法: python3 analyze-events.py <json文件> [<json文件> ...]")
    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.is_dir():
            for f in sorted(p.glob('*.json')):
                analyze_file(f)
        elif '*' in arg:
            # Path('.').glob('/abs/path/*.json') 会抛 NotImplementedError，
            # 而文档里写的正是这种用法；glob.glob 才能处理绝对路径。
            import glob as _glob
            for f in sorted(_glob.glob(arg)):
                analyze_file(f)
        else:
            analyze_file(arg)


if __name__ == '__main__':
    main()