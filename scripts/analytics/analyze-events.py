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

# 字段含义速查表（供维护者参考）。2026-09-22 按 engine.html 里实际发出的事件重写：
# 原表里的 marker_cta / clear_filter / all_areas / lang_switch 从未被发出过，
# 而 cta_click、task_*、help_open、season_* 等真实事件都没有列出。
# 有意不记录：拨了哪个号码（办事卡里的电话只记是哪张卡，task_call）、"求助"面板里点了什么、
# 完成了哪张办事卡（只记总数）。
EVENT_SCHEMAS = {
    # 会话
    'session_start':  {'...': '页面打开'},
    'session_end':    {'dur': '停留秒数（离开页面时）'},
    'lang_menu':      {},
    'lang_change':    {'from': '原语言', 'to': '新语言'},
    'theme_toggle':   {'id': '主题', 'action': 'add/remove/remove_chip', 'active': '累计'},
    'firstuse_go':    {'to': '首屏引导去向'},
    'firstuse_dismiss': {'via': '关闭方式'},
    # 地图筛选
    'panel_open':     {'mode': 'area/cat/bus/fav', 'prev': '前一个面板'},
    'panel_close':    {'mode': '面板类型'},
    'preset_toggle':  {'id': '预设 id', 'action': 'add/remove', 'active': '累计激活数'},
    'preset_clear_all': {},
    'category_toggle':{'id': '分类 id', 'action': 'add/remove'},
    'category_group_toggle': {'group': '分组', 'action': 'clear/select_all'},
    'region_toggle':  {'id': '区域 id', 'action': 'add/remove'},
    'region_select_all': {},
    'filter_clear_chip': {'kind': '筛选类型', 'id': '被清掉的项'},
    'open_now_toggle':{'action': 'on/off'},
    'near_toggle':    {'action': 'on/off/no_location'},
    'geo_locate':     {'result': 'success/denied/unavailable/timeout/unsupported'},
    'reset_all':      {}, 'reset_undo': {},
    'empty_state_shown': {}, 'empty_state_recover': {'kind': '恢复方式'},
    # 搜索（q 已在客户端清洗：去掉 3 位以上数字、截到 24 字；危机类词一律替换成 [crisis]）
    'search_run':     {'q': '清洗后的搜索词', 'len': '原长度', 'n': '结果数', 'filtered': '是否有筛选'},
    'search_empty':   {'q': '清洗后的 0 结果搜索词'},
    'search_suggest': {'to': '建议去向（task:<id> / bus_tru / open_pharmacy）'},
    'search_clear':   {'had': '清掉前的长度', 'n': '结果数'},
    # 地点
    'marker_view':    {'id': '地点 id', 'cat': '分类', 'reg': '区域', 'src': 'clustered/hidden_by_filter'},
    'marker_close':   {},
    'cta_click':      {'kind': 'call/nav/web', 'id': '地点 id', 'cat': '分类'},
    'popup_route':    {'route': '弹窗里点的公交线路'},
    'route_select':   {'id': '线路', 'action': 'select/deselect', 'src': '入口'},
    'fav_toggle':     {'action': 'add/remove', 'cat': '分类', 'reg': '区域'},
    'fav_open':       {'cat': '分类', 'reg': '区域', 'total': '收藏数'},
    'fav_export':     {'n': '条数'}, 'fav_import': {'ok': '是否成功', 'n': '条数'},
    'feedback_click': {'kind': 'place/task/general', 'id': '地点或办事卡 id', 'cat': '分类'},
    # 办事卡与指南
    'guide_open':     {'src': '入口', 'task': '直达的办事卡'},
    'guide_close':    {'ms': '停留毫秒'},
    'guide_section_jump': {'id': '章节'},
    'guide_link':     {'to': '指南正文里点出去的网站域名'},
    'task_open':      {'id': '办事卡 id', 'src': '入口'},
    'task_back':      {'id': '办事卡 id'},
    'task_step':      {'action': 'tick/untick', 'n': '已勾步数', 'of': '总步数'},
    'task_done':      {'action': 'done/undone', 'total': '已完成张数（不记是哪张）'},
    'task_outcome':   {'id': '办事卡 id', 'result': 'worked/stuck'},
    'task_to_map':    {'id': '办事卡 id', 'place': '地点 id'},
    'task_src':       {'id': '办事卡 id', 'to': '官方来源域名'},
    'task_link':      {'id': '办事卡 id', 'to': '卡内其他外链域名'},
    'task_call':      {'id': '在哪张办事卡上点了电话（不记号码）'},
    'task_share':     {'id': '办事卡 id', 'native': '系统分享'},
    'task_print':     {'id': '办事卡 id'}, 'task_calendar': {'id': '办事卡 id'},
    # 求助 / 季节提醒
    'help_open':      {},
    'season_shown':   {'id': 'winter/wildfire（每次打开页面最多一次）'},
    'season_link':    {'id': '季节', 'to': '点出去的网站域名'},
    'season_close':   {'id': '季节'},
    # 分享 / 说明 / 技术
    'share_open':     {'native': '系统分享'},
    'share_click':    {'stage': 'intent/result', 'target': '渠道', 'method': '复制方式'},
    'note_open':      {'src': '入口'}, 'privacy_expand': {'action': 'open/close'},
    'mailto_fallback':{'kind': 'contact/share（应用内浏览器打不开邮件时改为复制）'},
    'offline_shown':  {'online': '浏览器是否认为在线'}, 'offline_note': {'action': 'dismiss'},
    'tile_probe':     {'status': '地图瓦片状态码'}, 'tile_fallback': {},
    'sw_register':    {'ok': '是否成功'}, 'pwa_install': {}, 'qp_more': {},
    'js_error':       {'...': '脚本错误摘要'},
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
        # 原来断言"没有 q"，而 search_run / search_empty 本来就会带清洗后的 q，
        # 每次导出都会被判"有问题"。现在检查的是 q 确实被清洗过。
        ('搜索词已清洗（无 3 位以上数字、≤24 字）',
         all(isinstance((e.get('p') or {}).get('q'), str)
             and (e['p']['q'] == '[crisis]'
                  or (len(e['p']['q']) <= 24 and not __import__('re').search(r'\d{3,}', e['p']['q'])))
             for e in events if 'q' in (e.get('p') or {}))),
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
        return f"搜索（原长度 {p.get('len','?')}，{p.get('n','?')} 个结果）"
    if t == 'search_empty':
        return f"搜索 0 结果：{p.get('q','?')}"
    if t == 'marker_view':
        return f"查看标记 {p.get('id','?')} ({p.get('cat','?')})"
    if t == 'cta_click':
        return f"点 CTA: {p.get('kind','?')} → {p.get('id','?')}"
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
    if t == 'filter_clear_chip':
        return f"清除筛选: {p.get('kind','?')} {p.get('id','')}"
    if t == 'region_select_all':
        return "全选区域"
    if t == 'task_open':
        return f"打开办事卡 {p.get('id','?')}（入口 {p.get('src','?')}）"
    if t == 'task_call':
        return f"在办事卡 {p.get('id','?')} 上点了电话"
    if t in ('task_src', 'task_link', 'guide_link', 'season_link'):
        return f"{t}: 点出去 → {p.get('to','?')}"
    if t == 'feedback_click':
        return f"点反馈（{p.get('kind','?')}）{p.get('id','') or ''}"
    if t == 'season_shown':
        return f"显示季节提醒 {p.get('id','?')}"
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

    empty_q = [(e.get('p') or {}).get('q', '?') for e in events if e.get('t') == 'search_empty']
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