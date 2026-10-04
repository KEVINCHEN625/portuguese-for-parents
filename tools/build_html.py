#!/usr/bin/env python3
"""Assemble the final single-file index.html: src/handbook.html + embedded font + audio bank + app.js + SW.

Set BANK_PARTIAL=1 to build a preview even if some audio clips are still missing.
"""
import base64
import datetime
import json
import os
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
SRC = BASE / "src" / "handbook.html"
APP_JS = (BASE / "tools" / "app.js").read_text(encoding="utf-8")
ENTRIES = json.load(open(BASE / "entries.json", encoding="utf-8"))
PARTIAL = os.environ.get("BANK_PARTIAL") == "1"

if "</script>" in APP_JS:
    sys.exit("app.js must not contain </script>")

html = SRC.read_text(encoding="utf-8")

# ---------- 嵌入字体 ----------
font_css = []
for style, fname in (("normal", "fraunces-latin-normal.woff2"), ("italic", "fraunces-latin-italic.woff2")):
    data = (BASE / "src" / "fonts" / fname).read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    font_css.append(
        "@font-face{font-family:'Fraunces';font-style:%s;font-weight:400 700;font-display:swap;"
        "src:url(data:font/woff2;base64,%s) format('woff2');"
        "unicode-range:U+0000-00FF,U+2000-206F,U+20AC;}" % (style, b64)
    )
font_block = "\n".join(font_css)
if html.count("/*FONTFACE*/") != 1:
    sys.exit("FONTFACE marker missing")
html = html.replace("/*FONTFACE*/", font_block)

# ---------- 音频库 ----------
voices = {}
missing = []
for comm in ("main",):
    items = {}
    for e in ENTRIES:
        m4a = BASE / "audio" / comm / f"{e['id']}.m4a"
        mp3 = BASE / "audio" / comm / f"{e['id']}.mp3"
        path = m4a if m4a.exists() else mp3 if mp3.exists() else None
        if path is None or path.stat().st_size < 200:
            missing.append(f"{comm}/{e['id']}")
            continue
        mime = "audio/mp4" if path.suffix == ".m4a" else "audio/mpeg"
        items[e["id"]] = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")
    voices[comm] = items
    raw = sum(p.stat().st_size for p in (BASE / "audio" / comm).glob("*") if p.suffix in (".mp3", ".m4a"))
    print(f"{comm}: {len(items)} clips, raw {raw/1024:.0f} KB, embedded {sum(len(v) for v in items.values())/1024:.0f} KB")

if missing and not PARTIAL:
    print(f"missing audio ({len(missing)}), e.g. {missing[:5]}")
    sys.exit("run tools/gen_audio.py first, or set BANK_PARTIAL=1 for a preview build")

bank = {
    "meta": {
        "generated": datetime.date.today().isoformat(),
        "engine": "Google Translate TTS (tl=pt-PT)",
        "voices": {"main": "pt-PT female"},
        "rate": "default (约0.78x慢读由播放器变速)",
        "partial": bool(missing),
        "note": "机器合成音（欧洲葡语），非莫桑比克真人录音；慢读为同一音频 0.78 倍速重放。"
    },
    "voices": voices,
}
bank_json = json.dumps(bank, ensure_ascii=False, separators=(",", ":"))
if "</script>" in bank_json:
    sys.exit("bank json contains </script>")

# ---------- 换主脚本 ----------
marker = "</main><script>"
idx = html.find(marker)
if idx < 0:
    sys.exit("main script marker not found")
head = html[:idx]
rest = html[idx + len(marker):]
tail_idx = rest.rfind("</script>")
if tail_idx < 0:
    sys.exit("closing script tag not found")
tail = rest[tail_idx + len("</script>"):]

sw_reg = ("if('serviceWorker' in navigator){window.addEventListener('load',function(){"
          "navigator.serviceWorker.register('sw.js').catch(function(){});});}")

out = (head + "</main>\n"
       + '<script id="audio-bank" type="application/json">' + bank_json + "</script>\n"
       + "<script>\n" + APP_JS + "\n</script>\n"
       + "<script>" + sw_reg + "</script>"
       + tail)

dst = BASE / "index.html"
dst.write_text(out, encoding="utf-8")
print(f"wrote {dst} ({dst.stat().st_size/1024/1024:.2f} MB), partial={bool(missing)}")
