#!/usr/bin/env python3
"""Build a single-file local audition page: 5 candidate voices x 4 entries."""
import base64
import json
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
ENTRIES = {e["id"]: e for e in json.load(open(BASE / "entries.json", encoding="utf-8"))}
ENTRY_IDS = ["004", "008", "021", "024"]

# 中文标题从 handbook.html 的卡片里取
import re
HANDBOOK = (BASE / "src" / "handbook.html").read_text(encoding="utf-8")
ZH = {}
for m in re.finditer(r'id="entry-(\d+)"[^>]*>.*?<h4>(.*?)</h4>', HANDBOOK, re.S):
    ZH[m.group(1)] = re.sub(r"<.*?>", "", m.group(2)).strip()

VOICE_META = {
    "A_default": ("A · 平台默认音色", "未选发音人，S2.1-Pro 自带音色"),
    "B_valentino": ("B · valentino portugues", "社区高热度专业声音（2 万+次使用）"),
    "C_valentino2": ("C · Valentino (Português)", "Valentino 系列另一版葡语声音"),
    "D_jarvis": ("D · Jarvis português", "Jarvis 系列葡语版（4 千+次使用）"),
    "E_narrador": ("E · Narrador de Historias e Ciências", "讲故事/科普解说风声音"),
}

rows = []
for vkey, (title, desc) in VOICE_META.items():
    cells = []
    for eid in ENTRY_IDS:
        p = BASE / "samples" / vkey / f"{eid}.mp3"
        b64 = base64.b64encode(p.read_bytes()).decode()
        e = ENTRIES[eid]
        cells.append(
            f'<div class="cell"><div class="pt">{e["pt"]}</div>'
            f'<div class="zh">{ZH.get(eid, eid)}</div>'
            f'<audio controls preload="none" src="data:audio/mpeg;base64,{b64}"></audio></div>'
        )
    rows.append(
        f'<section class="vrow"><h2>{title}</h2><p class="desc">{desc}</p>'
        f'<div class="grid">{"".join(cells)}</div></section>'
    )

html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>试听 · 选一个声音</title><style>
body{{font-family:-apple-system,"PingFang SC",sans-serif;background:#f5f1e8;color:#1b352c;margin:0;padding:30px 18px 80px;line-height:1.6}}
.wrap{{max-width:900px;margin:auto}}
h1{{font-size:26px;margin:0 0 6px}} .sub{{color:#6b7f74;font-size:15px;margin:0 0 30px}}
.vrow{{background:#fffdf7;border:1px solid #ddd5c3;border-radius:16px;padding:20px;margin-bottom:18px}}
.vrow h2{{font-size:19px;margin:0 0 2px}} .desc{{color:#8a9a8f;font-size:13px;margin:0 0 14px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}}
.cell{{background:#faf3e3;border-radius:12px;padding:12px}}
.pt{{font-size:18px;font-weight:700}} .zh{{font-size:13px;color:#8a5714;margin-bottom:8px}}
audio{{width:100%;height:36px}}
.note{{background:#fdf3e0;border:1px solid #e6c383;border-radius:12px;padding:14px 16px;font-size:14px;color:#745327}}
</style></head><body><div class="wrap">
<h1>Fish Audio S2.1-Pro · 葡语声音试听</h1>
<p class="sub">五个候选发音人 × 四条词条（语速 0.9，正式版与慢读按钮保持一致）。逐行听，选一个告诉我字母即可。</p>
{''.join(rows)}
<p class="note">提示：A 为平台默认音色；B–E 为声音库发音人。注意分辨哪个更像「葡萄牙/欧洲口音」而不是巴西腔——莫桑比克的官方用语更接近欧洲葡语。</p>
</div></body></html>"""

out = BASE / "samples.html"
out.write_text(html, encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size/1024:.0f} KB)")
