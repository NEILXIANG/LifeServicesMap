#!/usr/bin/env python3
"""assistant/kit/record_short.py — 约 75 秒的演示短片，逐帧生成，画面流畅不抖（Neil 2026-11-11）。

    .venv/bin/python assistant/kit/record_short.py [--site http://127.0.0.1:8788/]   # → ops/assistant-kit/<日期>/demo-short-en.mp4

为什么逐帧：第一版用 Playwright 自带录像 + 鼠标滚轮，滚动是一格一格跳的、帧率忽快忽慢，看起来抖。
这里每一帧由脚本决定：滚动和鼠标都按缓入缓出的曲线一帧一帧算出来、截一张图，最后按每秒 30 帧合成。
等 AI 回答的十来秒压缩成约 2 秒（字幕标明已缩短）。

5 个口语化的问题（全程英文界面）：刚到先做什么、免费学英语（之后跳到生活指南地图看 KIS 再返回）、孩子上学、MSP 还没生效孩子发烧、家暴（不经过 AI）。
前 4 个真实调用 Claude（约 $0.20）。打开线上指南时屏蔽它的访问统计（/api/event），地图瓦片按经验 L-145 屏蔽 MapTiler 和 Stadia。
"""
import argparse, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import kamdata

W, H, FPS = 1280, 800, 30

QUESTIONS = [
    ('ai', "I just moved to Kamloops last week. What should I do first?",
     'Everyday questions, answered only from the verified Kamloops Life Guide', 'It starts by pointing newcomers to a KIS settlement worker'),
    ('ai', "Is there anywhere I can learn English for free? I've got a 3-year-old too.",
     'Any wording works — no keywords needed', 'Free LINC English classes and free childminding at KIS — with sources'),
    ('ai', "My daughter's 9 and doesn't speak much English yet. How do we get her into school here?",
     'School for a child who is still learning English', 'Find the catchment school, what to bring, and English-language support — each step with its source'),
    ('ai', "We just got here and our MSP hasn't kicked in yet. My son's got a high fever — where can we take him, and how much will it cost?",
     'A worried parent, before health coverage starts', 'Costs during the MSP wait, 8-1-1 with interpreters, where to go — and when to go to emergency'),
    ('crisis', "My friend's husband keeps hitting her and she's scared to go home. Where can she go tonight?",
     'A safety question is never sent to the AI', '9-1-1 and 24-hour help lines appear at once — the shelter address is never shown'),
]

# 只在助手页面上：关掉页面自己的滚动（由脚本逐帧控制），聚焦时不跳屏；所有页面：字幕条和鼠标
INIT = r"""
(() => {
  const isAssistant = location.port === '8788' || location.hostname.startsWith('kamloops-assistant');
  if (isAssistant) {
    Element.prototype.scrollIntoView = function () {};
    window.scrollTo = function () {};
    const f = HTMLElement.prototype.focus;
    HTMLElement.prototype.focus = function (o) { return f.call(this, Object.assign({}, o || {}, { preventScroll: true })); };
  }
  const add = () => {
    if (document.getElementById('demo-cap')) return;
    const s = document.createElement('style');
    s.textContent = `#demo-cap{position:fixed;left:0;right:0;bottom:0;z-index:2147483646;background:rgba(10,95,201,.95);color:#fff;
      font:600 18px -apple-system,Helvetica,Arial,sans-serif;padding:11px 18px;text-align:center}
      #demo-cap:empty{display:none}
      #demo-cursor{position:fixed;left:0;top:0;z-index:2147483647;width:26px;height:26px;pointer-events:none;will-change:transform;
        filter:drop-shadow(0 1px 2px rgba(0,0,0,.45))}
      #demo-ring{position:fixed;left:0;top:0;z-index:2147483647;width:30px;height:30px;margin:-15px 0 0 -15px;border-radius:50%;
        border:3px solid #ff9f0a;pointer-events:none;opacity:0}`;
    document.head.append(s);
    const c = document.createElement('div'); c.id = 'demo-cap'; document.body.append(c);
    const r = document.createElement('div'); r.id = 'demo-ring'; document.body.append(r);
    const k = document.createElement('div'); k.id = 'demo-cursor';
    k.innerHTML = '<svg viewBox="0 0 24 24" width="26" height="26"><path d="M3 2l17 10-7 1.6L9.6 21z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    k.style.transform = 'translate(640px,420px)';
    document.body.append(k);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', add); else add();
})();
"""

ease = lambda t: 0.5 - 0.5 * __import__('math').cos(__import__('math').pi * t)   # 缓入缓出


class Rec:
    def __init__(self, out):
        self.out, self.n, self.pg, self.last = out, 0, None, None
        self.cur = (640, 420)

    def use(self, pg):
        self.pg = pg

    def shot(self, k=1):
        data = self.pg.screenshot(type='jpeg', quality=90)
        for _ in range(k):
            self.n += 1
            with open(os.path.join(self.out, '%06d.jpg' % self.n), 'wb') as f:
                f.write(data)

    def hold(self, secs):
        self.shot(max(1, round(secs * FPS)))

    def caption(self, text):
        self.pg.evaluate('t => { const c = document.getElementById("demo-cap"); if (c) c.textContent = t; }', text)

    def _set_cursor(self, x, y):
        self.pg.evaluate('([x, y]) => { const k = document.getElementById("demo-cursor"); if (k) k.style.transform = `translate(${x}px,${y}px)`; }', [x, y])
        self.cur = (x, y)

    def move(self, x, y, secs=0.6):
        (x0, y0), n = self.cur, max(1, round(secs * FPS))
        for i in range(1, n + 1):
            e = ease(i / n)
            self._set_cursor(x0 + (x - x0) * e, y0 + (y - y0) * e)
            self.shot()

    def scroll_y(self):
        return self.pg.evaluate('document.scrollingElement.scrollTop')

    def scroll_to(self, y, secs=0.9):
        y = max(0, min(y, self.pg.evaluate('document.scrollingElement.scrollHeight - innerHeight')))
        y0, n = self.scroll_y(), max(1, round(secs * FPS))
        if abs(y - y0) < 2: return
        for i in range(1, n + 1):
            self.pg.evaluate('v => { document.scrollingElement.scrollTop = v; }', y0 + (y - y0) * ease(i / n))
            self.shot()

    def box(self, loc):
        b = loc.bounding_box()
        return b['x'] + b['width'] / 2, b['y'] + b['height'] / 2, b

    def bring(self, loc, top=110, bottom=H - 120, secs=0.8):
        """一次滚到位（先算好位置），不来回修正"""
        _, _, b = self.box(loc)
        if b['y'] < top or b['y'] + b['height'] > bottom:
            self.scroll_to(self.scroll_y() + b['y'] - (H * 0.35), secs)

    def click(self, loc, secs=0.55, settle=0.15):
        self.bring(loc)
        x, y, _ = self.box(loc)
        self.move(x, y, secs)
        # 点击的圆圈：逐帧放大、变淡
        for i in range(8):
            t = i / 7
            self.pg.evaluate('([x, y, s, o]) => { const r = document.getElementById("demo-ring"); r.style.left = x + "px"; r.style.top = y + "px";'
                             ' r.style.transform = `scale(${s})`; r.style.opacity = o; }', [x, y, 0.4 + t, 1 - t])
            if i == 2: self.pg.mouse.click(x, y)
            self.shot()
        self.pg.evaluate('() => { document.getElementById("demo-ring").style.opacity = 0; }')
        self.hold(settle)

    def type(self, text, cps=26):
        per = FPS / cps
        acc = 0.0
        for ch in text:
            self.pg.keyboard.type(ch)
            acc += per * (1.8 if ch in ',.?' else 1.0)
            k = int(acc); acc -= k
            if k: self.shot(k)

    def read(self, loc, secs, margin=150):
        """把一张卡片从上到下慢慢翻完（匀速缓动），用时 secs"""
        _, _, b = self.box(loc)
        top = self.scroll_y() + b['y'] - 90
        end = top + max(0, b['height'] - (H - margin - 90))
        self.scroll_to(top, 0.8)
        if end > top + 5:
            self.hold(0.6)
            self.scroll_to(end, max(1.0, secs - 1.4))
        else:
            self.hold(max(0.6, secs - 0.8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', default='http://127.0.0.1:8788/')
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    out_dir = os.path.join(kamdata.ops_dir(), 'assistant-kit', kamdata.today().isoformat())
    os.makedirs(out_dir, exist_ok=True)
    frames = tempfile.mkdtemp()
    rec = Rec(frames)
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=['--host-resolver-rules=MAP api.maptiler.com 127.0.0.1, MAP tiles.stadiamaps.com 127.0.0.1'])
        ctx = b.new_context(viewport={'width': W, 'height': H}, locale='en-CA', device_scale_factor=1)
        ctx.add_init_script(INIT)
        ctx.route('**/api/event', lambda r: r.abort())          # 不把录制算进指南的访问统计
        pg = ctx.new_page()
        rec.use(pg)
        pg.goto(a.site, wait_until='networkidle')
        pg.evaluate('() => { try { localStorage.setItem("kia-lang", "en"); } catch (e) {} }')
        pg.reload(wait_until='networkidle')
        L = pg.locator

        rec.caption('Kamloops Newcomer Assistant — ask in your own words')
        rec.hold(1.6)

        for i, (kind, q, cap_ask, cap_read) in enumerate(QUESTIONS):
            rec.caption(cap_ask)
            if i:
                rec.scroll_to(0, 0.9)
            rec.click(L('#q'), secs=0.5)
            rec.type(q)
            rec.hold(0.25)
            rec.click(L('#go'), secs=0.4, settle=0.05)
            if kind == 'ai':
                rec.caption('The AI is writing the answer from the guide (waiting time shortened)')
                t0 = time.time()
                while not L('#out .answer, #out .error').count():
                    if time.time() - t0 > 90: raise SystemExit('AI 没有在 90 秒内回答')
                    rec.shot(4)                       # 快进：真实约 0.5 秒 → 视频 0.13 秒
                    time.sleep(0.35)
                if L('#out .error').count():
                    raise SystemExit('AI 没有回答：' + L('#out .error').inner_text())
                card = L('#out .answer')
            else:
                pg.wait_for_selector('#out .crisis', timeout=15000)
                card = L('#out .crisis')
            rec.caption(cap_read)
            rec.scroll_to(rec.scroll_y() + rec.box(card)[2]['y'] - 90, 0.8)
            rec.hold(0.8)
            if kind == 'ai':
                cite = card.locator('.cite').first
                if cite.count():
                    rec.click(cite, secs=0.5, settle=1.0)
                rec.read(card.locator('ol').first, 4.0)
            else:
                x, y, _ = rec.box(card.locator('.call911'))
                rec.move(x, y, 0.6)
                rec.hold(1.4)
                rec.read(card, 3.2)

            # 第 2 题之后：跳到生活指南的地图看 KIS，再回到助手
            if i == 1:
                link = card.locator('.sources li', has_text='Immigrant Services').get_by_role('link', name='Find on the guide map')
                if not link.count():
                    link = card.get_by_role('link', name='Find on the guide map')
                if not link.count():
                    link = L('.toguide')
                rec.caption('Each place links to the Kamloops Life Guide map')
                rec.bring(link.first)
                with ctx.expect_page() as info:
                    rec.click(link.first, secs=0.6, settle=0.1)
                guide = info.value
                guide.set_viewport_size({'width': W, 'height': H})
                guide.wait_for_load_state('load')
                time.sleep(2.5)                        # 等地图和地点卡片出来（不录这段等待）
                rec.use(guide)
                rec.caption('The Life Guide opens with the place already selected')
                rec._set_cursor(*rec.cur)
                rec.hold(1.0)
                rec.move(W * 0.62, H * 0.45, 0.9)
                rec.hold(2.2)
                guide.close()
                rec.use(pg)
                rec.caption('Back to the assistant — the answer is still here')
                rec.hold(1.6)

        rec.caption('Independent pilot · answers only from the verified Life Guide · not a service of KIS or the government')
        rec.scroll_to(0, 1.0)
        rec.hold(2.2)
        ctx.close(); b.close()

    mp4 = os.path.join(out_dir, 'demo-short-en.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(frames, '%06d.jpg'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', mp4], check=True)
    print('frames', rec.n, '→', round(rec.n / FPS, 1), 's')
    shutil.rmtree(frames, ignore_errors=True)
    print('wrote', mp4)


if __name__ == '__main__':
    main()
