#!/usr/bin/env python3
"""Extract entry id + Portuguese text from the v5 handbook HTML."""
import html
import json
import re
import sys

SRC = "/Users/kevinchen/Downloads/Mozambique_Portuguese_v5_SelectableVoices.html"
OUT = "/Users/kevinchen/ZCodeProject/parents-pt-app/entries.json"

text = open(SRC, encoding="utf-8").read()
chunks = re.split(r"<article\b", text)[1:]
entries = []
seen = set()
for chunk in chunks:
    m_id = re.search(r'data-id="(\d+)"', chunk)
    m_sec = re.search(r'data-section="([^"]*)"', chunk)
    m_pt = re.search(r'<p class="ptxt"[^>]*>(.*?)</p>', chunk, re.S)
    if not (m_id and m_pt):
        continue
    eid = m_id.group(1)
    if eid in seen:
        continue
    seen.add(eid)
    pt = html.unescape(m_pt.group(1)).strip()
    pt = re.sub(r"\s+", " ", pt)
    entries.append({"id": eid, "section": m_sec.group(1) if m_sec else "", "pt": pt})

entries.sort(key=lambda e: e["id"])
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=1)

lengths = [len(e["pt"]) for e in entries]
print(f"entries: {len(entries)}")
print(f"pt chars total: {sum(lengths)} (min {min(lengths)}, max {max(lengths)})")
for e in entries[:3] + entries[-3:]:
    print(f"  {e['id']} [{e['section']}] {e['pt']}")
ids = [e["id"] for e in entries]
expected = [f"{i:03d}" for i in range(1, len(entries) + 1)]
if ids != expected:
    missing = set(expected) - set(ids)
    print(f"WARNING: non-contiguous ids, missing: {sorted(missing)}", file=sys.stderr)
    sys.exit(1)
empty = [e["id"] for e in entries if not e["pt"]]
if empty:
    print(f"WARNING: empty pt text: {empty}", file=sys.stderr)
    sys.exit(1)
print("OK: contiguous ids, no empty text")
