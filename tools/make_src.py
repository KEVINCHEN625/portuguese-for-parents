#!/usr/bin/env python3
"""Produce src/handbook.html: v5 body + new design system CSS + new header + final copy."""
import json
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
    '<p class="version">v7.1 · 2026-10-04</p>'
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

# 9) 新增第 14 章「工厂」（家人整理的工厂常用词），地名章顺延为 15
FACTORY = json.load(open(BASE / "tools" / "factory_entries.json", encoding="utf-8"))
if len(FACTORY) != 39:
    sys.exit(f"expected 39 factory entries, got {len(FACTORY)}")


def factory_card(e):
    phon_html = re.sub(r"【[^】]+】", lambda m: f"<strong>{m.group(0)}</strong>", e["phon"])
    search = " ".join([e["id"], e["zh"], e["pt"], e["phon"], e["note"]])
    return (
        f'<article class="entry" id="entry-{e["id"]}" data-id="{e["id"]}" data-section="s14" '
        f'data-group="" data-search="{search}">\n'
        f'<div class="badge">№ {e["id"]}</div><h4>{e["zh"]}</h4>\n'
        f'<p class="ptxt" lang="pt">{e["pt"]}</p>\n'
        f'<div class="phon"><span class="phon-label">中文辅助注音 · 近似</span>{phon_html}</div>\n'
        f'<div class="notes"><p>{e["note"]}</p></div>'
        f'<div class="actions"><button class="play-btn" data-play="{e["id"]}" data-rate="1" type="button" '
        f'aria-label="听读 {e["pt"]}">▶ 听读</button>'
        f'<button class="slow-btn" data-play="{e["id"]}" data-rate="0.5" type="button" '
        f'aria-label="慢读 {e["pt"]}">▷ 慢读</button></div></article>\n'
    )


# 9a) 既有地名章 s14 → s15（章号、卡片 data-section、下拉选项）
if html.count('data-section="s14"') != 40:
    sys.exit(f"expected 40 place cards in s14, got {html.count('data-section=\"s14\"')}")
for old, new, n_expect in [
    ('<section class="chapter" id="s14">', '<section class="chapter" id="s15">', 1),
    ('data-section="s14"', 'data-section="s15"', 40),
    ('<div class="chapter-number">14</div>', '<div class="chapter-number">15</div>', 1),
    ('<option value="s14">14｜地名注音示例（40条）</option>',
     '<option value="s14">14｜工厂（39条）</option><option value="s15">15｜地名注音示例（40条）</option>', 1),
    ('<option value="all">全部内容（203条）</option>', '<option value="all">全部内容（242条）</option>', 1),
]:
    n = html.count(old)
    if n != n_expect:
        sys.exit(f"renumber anchor {old[:40]!r} found {n} times (need {n_expect})")
    html = html.replace(old, new)

# 9b) 在（已改名为 s15 的）地名章之前插入工厂章
NEW_CH = (
    '<section class="chapter" id="s14"><div class="chapter-heading"><div class="chapter-number">14</div>'
    '<div><h2>工厂</h2><p class="subtitle" lang="pt">Palavras para o trabalho na fábrica</p></div></div>'
    '<p class="lead">按家人在饼干厂的实际场景整理：车间与设备、原料、包装与仓储、单据与客户。'
    '注音按拼写拟写，供起步练习，不等于当地录音。</p>\n'
    '<p class="chapter-note">本章来自家人提供的工厂常用词清单（v7.1 新增）；拼写按莫桑比克通用的葡葡习惯，'
    '如 factura、eléctrico、camião。</p>\n'
    '<div class="cards">' + "".join(factory_card(e) for e in FACTORY) + "</div></section>\n\n"
)
anchor = '<section class="chapter" id="s15">'
if html.count(anchor) != 1:
    sys.exit("s15 insertion anchor not unique")
html = html.replace(anchor, NEW_CH + anchor)

dst = BASE / "src" / "handbook.html"
dst.write_text(html, encoding="utf-8")
print(f"wrote {dst} ({dst.stat().st_size/1024:.0f} KB)")
