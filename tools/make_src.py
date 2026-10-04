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
    '<ul class="facts">'
    '<li><b>203</b><span>学习卡</span></li>'
    '<li><b>14</b><span>章节</span></li>'
    '<li><b>11</b><span>省份地名</span></li>'
    '<li><b>2</b><span>内置声音</span></li>'
    '</ul></div></header>'
)
html = html[:header_marker.start()] + NEW_HEADER + html[header_marker.end():]

# 3) 最终文案（此前 build_html.py 中的替换，烘进源文件）
REPLACEMENTS = [
    ("<title>父母学葡语 · 地名分组与可选语音版</title>",
     "<title>父母学葡语 · 离线语音版</title>"),
    ('<p id="voiceInfo" role="status">本页使用系统葡语声音，没有内置录音。Reed / Rocko 如可用，会排在列表前部。</p>',
     '<p id="voiceInfo" role="status">已内置两套语音：声音一（pt-PT 女声，欧洲葡语口音）、声音二 Reed（苹果合成，与 iPhone 上的 Reed 同源），各 203 条，离线可播、无需系统语音包。也可切换为系统声音。</p>'),
    ("<p>本页只列设备提供的葡语声音，并显示完整名称和语言标签。你可以切换 Reed、Rocko 或其他葡语声音；同一浏览器允许本地保存时，会记住选择。不会使用英语版 Reed 代读葡语；上次所选声音消失时，会要求重新选择。</p>",
     "<p>两套内置语音都是机器合成音，不是莫桑比克当地人的真人录音。声音一为欧洲葡语口音，拼写与读音与莫桑比克官方用法一致；声音二 Reed 是苹果系统的葡语合成（巴西口音），与 iPhone 上的 Reed 声音同源，适合对照听读。仍可切换其他系统声音；选择会被记住。</p>"),
    ("<p>此交付是本地 HTML 文件，不是已发布的网站。iPhone 的“文件”或聊天预览器可能不运行脚本，不能保证直接点附件就可听读。通过网站在 Safari 打开后，才可按 Apple 的方法添加到主屏幕。本次没有发布网站，也没有在你的实际 iPhone 上完成测试。<a href=\"#sources\">资料见页末</a>。</p>",
     "<p>本页已发布为网站并支持离线使用：首次在有网络时用 Safari 完整打开一次，文字与内置语音即存入手机；之后即使无网络，也能从主屏幕图标打开点读。添加到主屏幕：Safari 底部“分享”→“添加到主屏幕”。若图标被误删，重新打开链接再添加一次即可。<a href=\"#sources\">资料见页末</a>。</p>"),
    ("<p>音色是否可用、是否需联网，由系统与所选声音决定。网页不能添加未提供给它的声音；切换声音会停止当前朗读并清空队列。点击另一条卡片则加入队列，不主动截断前一句。</p>",
     "<p>内置语音不联网、不需要系统下载任何语音包。切换声音会停止当前朗读并清空队列；点击另一条卡片则加入队列，不主动截断前一句。</p>"),
    ('<meta name="apple-mobile-web-app-capable" content="yes">',
     '<meta name="mobile-web-app-capable" content="yes">'
     '<meta name="apple-mobile-web-app-capable" content="yes">'),
    ('<meta name="apple-mobile-web-app-title" content="父母学葡语">',
     '<meta name="apple-mobile-web-app-title" content="父母学葡语">'
     '<link rel="manifest" href="manifest.webmanifest">'
     '<link rel="apple-touch-icon" href="icon-180.png">'
     '<link rel="icon" type="image/png" sizes="512x512" href="icon-512.png">'
     '<meta name="theme-color" content="#122e26">'),
    ('<p id="statusText" role="status">先选择声音，再点“听读”或“慢读”。</p>',
     '<p id="statusText" role="status">点“听读”或“慢读”即可播放；连点多条会依次排队。</p>'),
    ('<option value="">正在读取可用的葡语声音…</option>',
     '<option value="">读取中…</option>'),
    ("<p>2026-10-04 · v5 地名分组与可选语音版。PDF 为无音频文字版；HTML 调用设备提供的葡语声音，没有内置 Reed 或 Rocko 录音。</p>",
     "<p>2026-10-04 · v6.2 离线语音版。内置两套合成语音（声音一 · 欧洲葡语口音女声，在线翻译引擎合成；声音二 · Reed，苹果系统葡语合成（巴西口音）；均为机器合成音，非莫桑比克真人录音）；仍可切换设备系统声音。PDF 为无音频文字版。</p>"),
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
