#!/usr/bin/env python3
"""Produce src/handbook.html: v5 body + new design system CSS + new header + final copy."""
import pathlib
import re
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path("/Users/kevinchen/Downloads/Mozambique_Portuguese_v5_SelectableVoices.html")
CSS = (BASE / "tools" / "style.css").read_text(encoding="utf-8")

html = SRC.read_text(encoding="utf-8")

# 1) 换整套样式
style_marker = re.search(r"<style>.*?</style>", html, re.S)
if not style_marker:
    sys.exit("style block not found")
html = html[:style_marker.start()] + "<style>\n" + CSS + "\n</style>" + html[style_marker.end():]

# 2) 换页眉
header_marker = re.search(r"<header>.*?</header>", html, re.S)
if not header_marker:
    sys.exit("header not found")
NEW_HEADER = (
    '<header><div class="wrap">'
    '<p class="eyebrow">PORTUGUÊS PARA A VIDA EM MOÇAMBIQUE</p>'
    '<h1>莫桑比克生活葡语</h1>'
    '<p class="deck" lang="pt">Português para a vida em Mo&ccedil;ambique</p>'
    '<p class="version">v7.0 · 2026-10-04</p>'
    '</div></header>'
)
html = html[:header_marker.start()] + NEW_HEADER + html[header_marker.end():]

# 3) 删除页尾“资料与版本说明”区块（内部参考信息，家人不需要）
src_marker = re.search(r'<section class="sources".*?</section>\s*', html, re.S)
if not src_marker:
    sys.exit("sources section not found")
html = html[:src_marker.start()] + html[src_marker.end():]

# 4) footer 改为“播放中才出现”的停止钮；状态文字仅保留给读屏软件
footer_marker = re.search(r'<footer class="footer">.*?</footer>', html, re.S)
if not footer_marker:
    sys.exit("footer not found")
NEW_FOOTER = (
    '<footer class="footer" id="playbar" hidden>'
    '<p id="statusText" role="status" class="sr-only"></p>'
    '<span id="queueText" class="sr-only"></span>'
    '<button id="stop" type="button">■ 停止</button>'
    '</footer>'
)
html = html[:footer_marker.start()] + NEW_FOOTER + html[footer_marker.end():]

# 5) 删除快捷按钮行与连读/清除筛选行（家人反馈用处不大）
for pattern, name in [(r'<div class="quick">.*?</div>\s*', 'quick buttons'),
                      (r'<div class="list-tools">.*?</div>\s*', 'list tools')]:
    m = re.search(pattern, html, re.S)
    if not m:
        sys.exit(f"{name} block not found")
    html = html[:m.start()] + html[m.end():]

# 6) 删除语音提示条与折叠说明区（家人反馈用处不大）
for pattern, name in [(r'<p id="voiceInfo".*?</p>\s*', 'voiceInfo tip'),
                      (r'<details class="help">.*?</details>\s*', 'help details')]:
    m = re.search(pattern, html, re.S)
    if not m:
        sys.exit(f"{name} not found")
    html = html[:m.start()] + html[m.end():]

# 7) 慢读降为 0.5 倍速（家人反馈 0.78 仍偏快）
html, n_rate = re.subn(r'data-rate="0\.78"', 'data-rate="0.5"', html)
if n_rate != 203:
    sys.exit(f"expected 203 slow-rate buttons, rewrote {n_rate}")

# 8) 最终文案（此前 build_html.py 中的替换，烘进源文件）
REPLACEMENTS = [
    ("<title>父母学葡语 · 地名分组与可选语音版</title>",
     "<title>父母学葡语 · 离线语音版</title>"),
    ('<meta name="apple-mobile-web-app-capable" content="yes">',
     '<meta name="mobile-web-app-capable" content="yes">'
     '<meta name="apple-mobile-web-app-capable" content="yes">'),
    ('<meta name="apple-mobile-web-app-title" content="父母学葡语">',
     '<meta name="apple-mobile-web-app-title" content="父母学葡语">'
     '<link rel="manifest" href="manifest.webmanifest">'
     '<link rel="apple-touch-icon" href="icon-180.png">'
     '<link rel="icon" type="image/png" sizes="512x512" href="icon-512.png">'
     '<meta name="theme-color" content="#122e26">'),
    ('<option value="">正在读取可用的葡语声音…</option>',
     '<option value="">读取中…</option>'),
    ('<p id="empty" class="warning" hidden>没有找到匹配内容。可以缩短关键词，或清除筛选。</p>',
     '<p id="empty" class="warning" hidden>没有找到匹配内容。可以缩短关键词，或把章节选回“全部内容”。</p>'),
]
for old, new in REPLACEMENTS:
    n = html.count(old)
    if n != 1:
        sys.exit(f"replacement anchor found {n} times (need exactly 1):\n  {old[:70]}...")
    html = html.replace(old, new)

# 4) 徽标：CARD 001 → № 001（仅数字章；地名章为文字徽标，保持原样）
html, n_badge = re.subn(r'<div class="badge">CARD (\d+)</div>', r'<div class="badge">№ \1</div>', html)
print(f"badge rewritten: {n_badge}")

dst = BASE / "src" / "handbook.html"
dst.write_text(html, encoding="utf-8")
print(f"wrote {dst} ({dst.stat().st_size/1024:.0f} KB)")
