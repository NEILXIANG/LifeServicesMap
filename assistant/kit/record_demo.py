#!/usr/bin/env python3
"""assistant/kit/record_demo.py — 录一段英文界面的演示视频，像真人一样操作（可见鼠标、打字、边读边翻）。

    .venv/bin/python assistant/kit/record_demo.py [--site URL]     # → ../Guide to Life in Canada - ops/assistant-kit/<日期>/demo-en.mp4

重点放在 AI 回答（Neil 2026-10-24）：开头快速点一遍其他按钮（语言、隐私说明、常见问题、个人信息提醒），
然后危机演示（不经过 AI），再用 4 个问题真实调用 Claude，每个回答都慢慢往下翻着读，并展示来源、反馈、复制、地图链接、之前的回答。

4 个 AI 问题会真实调用 Claude（约 $0.20）。线上每个 IP 每天只有 10 题，录制可以用本机同一版本的服务（--site http://127.0.0.1:8788，
.claude/launch.json 的 assistant-demo：和线上一样每人每天 10 题，但每次启动从零计数），这样录坏了能重录。
字幕和鼠标只在录像时临时加在页面上，不改网站。
"""
import argparse, os, random, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import kamdata

W, H = 1280, 800
random.seed(7)

# 每次打开页面都加上字幕条和鼠标（隐私说明页、返回首页后也有）
INIT = r"""
(() => {
  const add = () => {
    if (document.getElementById('demo-cap')) return;
    const s = document.createElement('style');
    s.textContent = `#demo-cap{position:fixed;left:0;right:0;top:0;z-index:99998;background:rgba(10,95,201,.95);color:#fff;
      font:600 17px -apple-system,Helvetica,Arial,sans-serif;padding:10px 18px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.2)}
      body{padding-top:44px!important}
      #demo-cursor{position:fixed;z-index:99999;width:26px;height:26px;pointer-events:none;left:0;top:0;
        transition:left .6s cubic-bezier(.25,.8,.3,1),top .6s cubic-bezier(.25,.8,.3,1);filter:drop-shadow(0 1px 2px rgba(0,0,0,.45))}
      #demo-cursor.click::after{content:"";position:absolute;left:-14px;top:-14px;width:28px;height:28px;border-radius:50%;
        border:3px solid #ff9f0a;animation:demo-ring .45s ease-out forwards}
      @keyframes demo-ring{from{transform:scale(.3);opacity:1}to{transform:scale(1.4);opacity:0}}`;
    document.head.append(s);
    const c = document.createElement('div'); c.id = 'demo-cap'; c.textContent = sessionStorage.getItem('demo-cap') || '';
    document.body.append(c);
    const k = document.createElement('div'); k.id = 'demo-cursor';
    k.innerHTML = '<svg viewBox="0 0 24 24" width="26" height="26"><path d="M3 2l17 10-7 1.6L9.6 21z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    const p = JSON.parse(sessionStorage.getItem('demo-pos') || '[640,400]');
    k.style.left = p[0] + 'px'; k.style.top = p[1] + 'px';
    document.body.append(k);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', add); else add();
})();
"""


class Demo:
    def __init__(self, pg):
        self.pg = pg

    def caption(self, text):
        self.pg.evaluate('t => { sessionStorage.setItem("demo-cap", t); const c = document.getElementById("demo-cap"); if (c) c.textContent = t; }', text)

    def _cursor(self, x, y, dur=0.6):
        self.pg.evaluate('([x, y, d]) => { const k = document.getElementById("demo-cursor"); if (!k) return;'
                         ' k.style.transitionDuration = d + "s"; k.style.left = x + "px"; k.style.top = y + "px";'
                         ' sessionStorage.setItem("demo-pos", JSON.stringify([x, y])); }', [x, y, dur])
        self.pg.mouse.move(x, y, steps=8)
        time.sleep(dur + 0.08)

    def wheel(self, dy, ms=600):
        """像真人一样滚动：一串小的滚轮事件，前快后慢"""
        n = max(6, int(abs(dy) / 18))
        done = 0
        for i in range(n):
            part = round(dy * (1 - (1 - (i + 1) / n) ** 2)) - done
            done += part
            self.pg.mouse.wheel(0, part)
            time.sleep(ms / 1000 / n)

    def into_view(self, loc, top=150, bottom=H - 140):
        for _ in range(20):
            b = loc.bounding_box()
            if not b: return
            if b['y'] < top: self.wheel(b['y'] - top - 40, 450)
            elif b['y'] + b['height'] > bottom: self.wheel(min(b['y'] + b['height'] - bottom + 40, 420), 450)
            else: return
            time.sleep(0.25)

    def point(self, loc, dur=0.6, dx=0.5, dy=0.5):
        self.into_view(loc)
        b = loc.bounding_box()
        x, y = b['x'] + b['width'] * dx, b['y'] + b['height'] * dy
        self._cursor(x, y, dur)
        return x, y

    def click(self, loc, dur=0.6, after=0.6):
        x, y = self.point(loc, dur)
        self.pg.evaluate('() => { const k = document.getElementById("demo-cursor"); k.classList.remove("click"); void k.offsetWidth; k.classList.add("click"); }')
        time.sleep(0.12)
        self.pg.mouse.click(x, y)
        time.sleep(after)

    def type(self, text):
        for ch in text:
            self.pg.keyboard.type(ch)
            time.sleep(random.uniform(0.035, 0.11) + (0.18 if ch in ' ,.?' and random.random() < 0.35 else 0))

    def read(self, loc, chunk=260, pause=(2.2, 3.2)):
        """边读边往下翻：每次翻一小段，停下来读；鼠标跟着视线慢慢往下"""
        for _ in range(30):
            b = loc.bounding_box()
            if not b or b['y'] + b['height'] <= H - 60: break
            self._cursor(random.uniform(760, 900), random.uniform(320, 520), 0.9)
            time.sleep(random.uniform(*pause))
            self.wheel(chunk, 700)
        time.sleep(random.uniform(*pause))

    def ask(self, q):
        self.click(self.pg.locator('#q'), after=0.3)
        self.type(q)
        time.sleep(0.6)
        self.click(self.pg.locator('#go'), after=0.4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', default='https://kamloops-assistant.neilxiang.workers.dev/')
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    out_dir = os.path.join(kamdata.ops_dir(), 'assistant-kit', kamdata.today().isoformat())
    os.makedirs(out_dir, exist_ok=True)
    tmp = tempfile.mkdtemp()
    with sync_playwright() as pw:
        # 和项目里所有浏览器启动一样屏蔽地图瓦片服务（经验 L-145）
        b = pw.chromium.launch(args=['--host-resolver-rules=MAP api.maptiler.com 127.0.0.1, MAP tiles.stadiamaps.com 127.0.0.1'])
        ctx = b.new_context(viewport={'width': W, 'height': H}, record_video_dir=tmp, record_video_size={'width': W, 'height': H},
                            locale='en-CA', permissions=['clipboard-read', 'clipboard-write'])
        ctx.add_init_script(INIT)
        pg = ctx.new_page()
        d = Demo(pg)
        pg.goto(a.site, wait_until='networkidle')
        L = pg.locator

        # ---------- 开头：其他按钮快速点一遍 ----------
        d.caption('Kamloops Newcomer Assistant — answers come only from the verified Kamloops Life Guide (test version)')
        time.sleep(3)
        d.caption('A link back to the Life Guide, and six interface languages')
        d.point(L('.toguide'), dur=0.8); time.sleep(1.2)
        d.click(L('[data-lang=zh]'), after=1.6)
        d.click(L('[data-lang=fr]'), after=1.4)
        d.click(L('[data-lang=en]'), after=1.0)
        d.caption('A privacy note in every language — questions and answers are not stored')
        d.click(L('a[href^="privacy"]'), after=0.4)
        pg.wait_for_load_state('networkidle'); time.sleep(1.5)
        d.wheel(320, 800); time.sleep(2.2)
        pg.go_back(); pg.wait_for_load_state('networkidle'); time.sleep(1.2)
        d.caption('Common questions can be opened or folded away')
        d.click(L('#quick summary'), after=1.0)
        d.click(L('#quick summary'), after=1.0)

        d.caption('Personal details are flagged before anything is sent')
        d.ask('My phone number is 250-555-1234. How do I get a SIN?')
        time.sleep(2.6)
        d.click(L('#pii button.primary'), after=0.6)
        pg.keyboard.press('Meta+A' if sys.platform == 'darwin' else 'Control+A'); pg.keyboard.press('Backspace')
        time.sleep(1.0)

        # ---------- 危机：不经过 AI ----------
        d.caption('A safety question is never sent to the AI — 9-1-1 and 24-hour help lines appear at once')
        d.ask("My friend's husband hits her. Where can she get help?")
        pg.wait_for_selector('#out .crisis', timeout=20000); time.sleep(1.5)
        d.point(L('.call911'), dur=0.8); time.sleep(2.2)
        d.read(L('#out .crisis'), chunk=240, pause=(1.6, 2.2))
        d.click(L('#out .crisis button.secondary'), after=1.4)

        # ---------- 4 个真实调用 AI 的问题 ----------
        def answer(cap_ask, q, cap_read):
            d.caption(cap_ask)
            d.ask(q)
            pg.wait_for_selector('#out .answer, #out .error', timeout=90000)
            if L('#out .error').count():
                raise SystemExit('AI 没有回答：' + L('#out .error').inner_text())
            time.sleep(1.2)
            d.caption(cap_read)
            return L('#out .answer')

        card = answer('AI-assisted answer · a personal-eligibility question — the AI is now writing from the guide',
                      'Can a refugee claimant get MSP health coverage?',
                      'It does not decide anyone’s eligibility — it gives the general process and says who can help')
        d.point(card.locator('.summary'), dur=0.8, dx=0.2); time.sleep(3)
        d.caption('Every step names its source — tap [1] to see the guide card and the month it was checked')
        d.click(card.locator('.cite').first, after=3.2)
        d.read(card.locator('ol').first)
        d.caption('Phone numbers and web addresses are checked against the guide before the answer is shown')
        d.read(card.locator('.sources'), pause=(2.4, 3.0))
        d.point(card.get_by_role('link', name='Open in the guide').first, dur=0.7); time.sleep(1.8)
        d.caption('Feedback helps improve the answers')
        d.click(card.get_by_role('button', name='Useful'), after=2.0)

        d.click(card.get_by_role('button', name='Ask another question'), after=0.8)
        card = answer('AI-assisted answer · an everyday process',
                      'How do I enrol my 9-year-old in school in Kamloops?',
                      'Short, practical steps — each with its source')
        time.sleep(2.5)
        d.read(card.locator('ol').first)
        d.read(card.locator('.sources'), pause=(2.0, 2.6))
        d.caption('Copy (or Share on a phone) to pass the answer on, with its sources')
        d.click(card.get_by_role('button', name='Copy'), after=2.0)

        d.click(card.get_by_role('button', name='Ask another question'), after=0.8)
        card = answer('AI-assisted answer · basic needs',
                      "Where can I get food if I can't afford groceries?",
                      'Local places with addresses and phone numbers')
        time.sleep(2.5)
        d.read(card.locator('ol').first)
        d.read(card.locator('.sources'), pause=(2.0, 2.6))
        maplink = card.get_by_role('link', name='Find on the guide map').first
        if maplink.count():
            d.caption('Each place links to the Life Guide map, with the place already selected')
            d.point(maplink, dur=0.8); time.sleep(2.4)

        d.click(card.get_by_role('button', name='Ask another question'), after=0.8)
        card = answer('AI-assisted answer · free legal help',
                      'Where can I get free legal advice in Kamloops?',
                      'Free local services, each marked official, author-checked or third-party')
        time.sleep(2.5)
        d.read(card.locator('ol').first)
        d.read(card.locator('.sources'), pause=(2.0, 2.6))
        d.caption('Earlier answers stay on the page until it is closed — nothing is saved')
        d.click(L('#earlier > summary'), after=1.2)
        if not L('#earlier').evaluate('e => e.open'):
            d.click(L('#earlier > summary'), after=1.2)
        past = L('#earlierList > details > summary').first
        d.click(past, after=1.4)
        if not L('#earlierList > details').first.evaluate('e => e.open'):
            d.click(past, after=1.4)
        d.read(L('#earlierList > details').first, chunk=240, pause=(1.6, 2.2))

        d.caption('Independent pilot · not a service of KIS or the government · official sources take precedence')
        pg.evaluate('window.scrollTo({top: 0, behavior: "smooth"})')
        time.sleep(4)
        video = pg.video.path()
        ctx.close()
        b.close()
    mp4 = os.path.join(out_dir, 'demo-en.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', video, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '23',
                    '-movflags', '+faststart', mp4], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print('wrote', mp4)


if __name__ == '__main__':
    main()
