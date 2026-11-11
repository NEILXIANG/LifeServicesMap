#!/usr/bin/env python3
"""assistant/kit/intro.py — 给演示视频加一段开场字幕卡（这个工具是什么、为什么存在），不调用 AI。

    .venv/bin/python assistant/kit/intro.py <演示视频.mp4> [输出.mp4]

开场卡逐帧生成（每秒 30 帧、1280×800，和 record_short.py 一致）：几行字依次淡入，停留，再淡出，接上演示视频。
"""
import os, shutil, subprocess, sys, tempfile

W, H, FPS = 1280, 800, 30

HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><style>
html,body{margin:0;width:%dpx;height:%dpx;background:#0a3d7a;color:#fff;font-family:-apple-system,"Helvetica Neue",Arial,sans-serif}
.wrap{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;padding:0 110px}
h1{font-size:46px;margin:0 0 10px;font-weight:700;letter-spacing:.2px}
.sub{font-size:24px;color:#cfe3ff;margin:0 0 38px}
h2{font-size:22px;text-transform:uppercase;letter-spacing:2px;color:#9cc4ff;margin:0 0 14px;font-weight:700}
ul{margin:0;padding:0;list-style:none}
li{font-size:24px;line-height:1.45;margin:0 0 14px;padding-left:30px;position:relative}
li::before{content:"";position:absolute;left:0;top:13px;width:12px;height:12px;border-radius:50%%;background:#ffb340}
.foot{font-size:19px;color:#cfe3ff;border-top:1px solid rgba(255,255,255,.25);padding-top:18px}
[data-i]{opacity:0}
</style></head><body><div class="wrap">
<h1 data-i="0">Kamloops Newcomer Assistant</h1>
<p class="sub" data-i="0">Ask everyday settling-in questions in your own words — in any language.</p>
<h2 data-i="1">Why it exists</h2>
<ul>
<li data-i="2">New arrivals have urgent, practical questions — often in a second language, often after office hours.</li>
<li data-i="3">Every answer comes only from the verified Kamloops Life Guide, with its sources and the month it was checked.</li>
<li data-i="4">It points people to real help — KIS settlement workers, 8-1-1, 2-1-1 — and never sends a safety question to AI.</li>
</ul>
</div></body></html>""" % (W, H)

# 每一组字的淡入开始时间（秒）；淡入用 0.6 秒；全部出现后停 3.2 秒，最后 0.5 秒淡出到黑
STARTS = [0.2, 1.0, 1.5, 2.5, 3.5]   # 2026-11-11 Neil：删掉底部"Independent pilot · free · not a service of KIS or the government"
FADE, HOLD, OUT = 0.6, 3.2, 0.5


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src.replace('.mp4', '-with-intro.mp4')
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp()
    total = STARTS[-1] + FADE + HOLD + OUT
    n = int(round(total * FPS))
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': W, 'height': H})
        pg.set_content(HTML)
        for f in range(n):
            t = f / FPS
            fade_out = max(0.0, min(1.0, (total - t) / OUT))
            ops = [max(0.0, min(1.0, (t - s) / FADE)) * fade_out for s in STARTS]
            pg.evaluate('ops => document.querySelectorAll("[data-i]").forEach(e => { e.style.opacity = ops[+e.dataset.i]; })', ops)
            pg.screenshot(path=os.path.join(tmp, '%05d.png' % f))
        b.close()
    intro = os.path.join(tmp, 'intro.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(tmp, '%05d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-r', str(FPS), intro], check=True)
    lst = os.path.join(tmp, 'list.txt')
    with open(lst, 'w') as f:
        f.write("file '%s'\nfile '%s'\n" % (intro, os.path.abspath(src)))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-r', str(FPS), '-movflags', '+faststart', dst], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print('intro %.1f s →' % total, dst)


if __name__ == '__main__':
    main()
