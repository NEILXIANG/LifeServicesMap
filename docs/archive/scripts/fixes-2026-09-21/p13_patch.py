#!/usr/bin/env python3
"""2026-09-22 — the maintainer's decision: count phone taps inside task cards.
task_call {id} records WHICH CARD a number was tapped on, never the number itself
(so a tap on a shelter, a crisis line or an employer cannot be told apart).
The Help sheet stays untracked, as before."""
import sys
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:100], n))
    return src.replace(old, new)
s = rep(s, "    if(!/^https?:/i.test(href))return;\n",
"""    // 2026-09-22 (maintainer's decision): a phone tap inside a task card is
    // counted as the card only — which number was dialled is never sent.
    if(/^tel:/i.test(href)){if(a.closest('#guideTasks'))trackEvent('task_call',{id:_taskOpen||undefined});return;}
    if(!/^https?:/i.test(href))return;
""")
open(E, 'w', encoding='utf-8').write(s)

A = 'scripts/analytics/analyze-events.py'
a = open(A, encoding='utf-8').read()
a = rep(a, "    'task_link':      {'id': '办事卡 id', 'to': '卡内其他外链域名'},\n",
"    'task_link':      {'id': '办事卡 id', 'to': '卡内其他外链域名'},\n"
"    'task_call':      {'id': '在哪张办事卡上点了电话（不记号码）'},\n")
a = rep(a, "# 有意不记录：拨打任何电话号码、\"求助\"面板里点了什么、完成了哪张办事卡（只记总数）。",
           "# 有意不记录：拨了哪个号码（办事卡里的电话只记是哪张卡，task_call）、\"求助\"面板里点了什么、\n# 完成了哪张办事卡（只记总数）。")
a = rep(a, "    if t in ('task_src', 'task_link', 'guide_link', 'season_link'):",
           "    if t == 'task_call':\n        return f\"在办事卡 {p.get('id','?')} 上点了电话\"\n    if t in ('task_src', 'task_link', 'guide_link', 'season_link'):")
open(A, 'w', encoding='utf-8').write(a)

Q = 'scripts/analytics/query-events.py'
q = open(Q, encoding='utf-8').read()
q = rep(q, "  ./query-events.py feedback            # 点\"报告错误 / 反馈\"的次数\n",
           "  ./query-events.py feedback            # 点\"报告错误 / 反馈\"的次数\n"
           "  ./query-events.py calls               # 办事卡里的电话被点了多少次（按卡；不含号码）\n")
q = rep(q, '    "feedback": (\n',
'''    "calls": (
        "办事卡里的电话点击（按卡统计；从不记录拨了哪个号码）",
        f"""
SELECT blob8 AS card, count() AS taps, count(DISTINCT blob1) AS users
FROM {DATASET}
WHERE blob2 = 'task_call' AND timestamp > NOW() - INTERVAL '30' DAY AND double2 != 1
GROUP BY card ORDER BY taps DESC
""",
    ),
    "feedback": (
''')
open(Q, 'w', encoding='utf-8').write(q)

T = 'tests/phase9test.py'
t = open(T, encoding='utf-8').read()
t = rep(t, "        check('tapping a phone number in a card sends nothing', tel['ev'] == [], tel)",
"""        check('tapping a phone number in a card is counted as that card only, never the number',
              tel['had'] and tel['ev'] == ['task_call'], tel)
        tc = await ev('task_call')
        check('task_call carries the card id and no digits', tc == [{'id': 'doctor'}], tc)""")
open(T, 'w', encoding='utf-8').write(t)
print('p13 applied')
