#!/usr/bin/env python3
"""B.C.'s permanent daylight time (2026-11-01: the clocks do not fall back) — the city clock must stay right
whether or not the phone's time-zone data knows about it.

The engine reads the city's clock through Intl with America/Vancouver. A device with time-zone data from
before the change still falls back to UTC-8 on 2026-11-01, which would put every "open now", every
"closes at" and every holiday check an hour wrong. The engine corrects that case (15-time-open-now.js).

Here the device's time-zone data is simulated by redirecting America/Vancouver inside Intl.DateTimeFormat
to a fixed offset: Etc/GMT+8 (old data, still falling back) or Etc/GMT+7 (current data). The page clock
is fixed with Playwright's clock API. Fixture city, so no Kamloops data is needed.

    .venv/bin/python tests/engine/test_bc_permanent_dst.py
"""
import asyncio, datetime, os, subprocess, sys
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)

SIMULATE = """zone => {
  const Real = Intl.DateTimeFormat;
  function Fake(loc, opt) {
    opt = Object.assign({}, opt || {});
    if (opt.timeZone === 'America/Vancouver') opt.timeZone = zone;
    return new Real(loc, opt);
  }
  Fake.prototype = Real.prototype; Fake.supportedLocalesOf = Real.supportedLocalesOf;
  Intl.DateTimeFormat = Fake;
}"""

CASES = [
    # (label, UTC instant, simulated device zone for America/Vancouver (None = the browser's own data),
    #  expected city weekday, minutes since midnight, ISO date)
    ('before the change, the browser\'s own data: PDT', datetime.datetime(2026, 10, 15, 20, 0, tzinfo=datetime.timezone.utc), None, 4, 13 * 60, '2026-10-15'),
    ('after 2026-11-01, old time-zone data (UTC-8) is corrected to UTC-7', datetime.datetime(2026, 11, 15, 20, 0, tzinfo=datetime.timezone.utc), 'Etc/GMT+8', 7, 13 * 60, '2026-11-15'),
    ('after 2026-11-01, current time-zone data (UTC-7) is left alone', datetime.datetime(2026, 11, 15, 20, 0, tzinfo=datetime.timezone.utc), 'Etc/GMT+7', 7, 13 * 60, '2026-11-15'),
    ('just after midnight, old data: the date must be the new day', datetime.datetime(2026, 12, 1, 7, 30, tzinfo=datetime.timezone.utc), 'Etc/GMT+8', 2, 30, '2026-12-01'),
]

async def main():
    subprocess.run([sys.executable, os.path.join(ROOT, 'build.py'), '--city', '_fixture', '--no-sync-public'],
                   check=True, capture_output=True)
    url = 'file://' + os.path.join(ROOT, 'build', '_fixture.html') + '?lang=en'
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        for label, when, zone, wd, mins, iso in CASES:
            ctx = await b.new_context(timezone_id='America/Vancouver')
            pg = await ctx.new_page(); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
            await pg.clock.set_fixed_time(when)
            # the simulated device data must be in place before the engine runs
            if zone:
                await pg.add_init_script('(%s)(%r)' % (SIMULATE, zone))
            await pg.goto(url); await pg.wait_for_timeout(800)
            got = await pg.evaluate("()=>({now:cityNow(),iso:cityISODate(),month:cityMonth()})")
            check(label, got['now'] == {'d': wd, 'm': mins} and got['iso'] == iso and got['month'] == when.month and not errs,
                  {'got': got, 'want': {'d': wd, 'm': mins, 'iso': iso}, 'errors': errs})
            await ctx.close()
        await b.close()
    print('\n%d passed, %d failed' % (P, F))
    sys.exit(1 if F else 0)

if __name__ == '__main__':
    asyncio.run(main())
