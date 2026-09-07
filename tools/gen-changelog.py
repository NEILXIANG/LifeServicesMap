#!/usr/bin/env python3
"""gen-changelog.py — 从 src/engine.html 生成根目录的 CHANGELOG.md

为什么需要它：更新记录此前有两份——页面里给用户看的 CHANGELOG 数组，和根目录的
CHANGELOG.md。两份各自手工维护，到 2026-09-07 已经漂移了两个版本（页面 2026.09.07b，
文件停在 2026.09.05c）。用户看到的是页面里那份，所以它是唯一事实来源，这个脚本把它
导出成 Markdown，CHANGELOG.md 不要再手改。

用法:
    python3 tools/gen-changelog.py          # 写入 CHANGELOG.md
    python3 tools/gen-changelog.py --check  # 只检查是否过期，过期则退出码 1
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENGINE = os.path.join(ROOT, 'src', 'engine.html')
OUT = os.path.join(ROOT, 'CHANGELOG.md')

# CHANGELOG 是 JS 对象字面量（键不带引号、字符串用单引号），json 解析不了，
# 交给 node 求值再转成 JSON。node 本来就是 validate.py 的依赖。
def read_changelog():
    src = open(ENGINE, encoding='utf-8').read()
    m = re.search(r'const DATA_VERSION=\'([^\']+)\'', src)
    version = m.group(1) if m else '(unknown)'
    i = src.index('const CHANGELOG=')
    j = src.index('\n];', i) + 3
    literal = src[i:j].replace('const CHANGELOG=', '', 1).rstrip().rstrip(';')
    js = 'process.stdout.write(JSON.stringify(%s))' % literal
    try:
        out = subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True)
    except FileNotFoundError:
        sys.exit('need node on PATH to parse the CHANGELOG literal')
    except subprocess.CalledProcessError as e:
        sys.exit('could not parse the CHANGELOG literal: %s' % e.stderr[:300])
    return version, json.loads(out.stdout)

def render(version, entries):
    lines = ['# Change log', '',
             '<!-- 由 tools/gen-changelog.py 从 src/engine.html 生成，请勿手改。 -->',
             '<!-- 改动写进 src/engine.html 的 CHANGELOG 数组，再跑一次这个脚本。 -->',
             '', '当前版本：`%s`' % version, '']
    for e in entries:
        lines.append('## %s' % e.get('v', '?'))
        lines.append('')
        for lang, label in (('zh', '中文'), ('en', 'English')):
            items = e.get(lang)
            if not items:
                continue
            lines.append('**%s**' % label)
            lines.append('')
            for it in items:
                lines.append('- %s' % it)
            lines.append('')
    return '\n'.join(lines).rstrip() + '\n'

def main():
    version, entries = read_changelog()
    text = render(version, entries)
    if '--check' in sys.argv:
        cur = open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
        if cur != text:
            print('CHANGELOG.md is out of date — run: python3 tools/gen-changelog.py')
            return 1
        print('CHANGELOG.md is up to date (%s)' % version)
        return 0
    open(OUT, 'w', encoding='utf-8').write(text)
    print('wrote CHANGELOG.md — %d entries, current version %s' % (len(entries), version))
    return 0

if __name__ == '__main__':
    sys.exit(main())
