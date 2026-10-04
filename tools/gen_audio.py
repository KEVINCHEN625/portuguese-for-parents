#!/usr/bin/env python3
"""Generate pt-PT TTS audio for all entries via Google translate_tts endpoint.

edge-tts (Azure) is blocked from this network (NoAudioReceived), so we use
Google's endpoint with tl=pt-PT (European Portuguese, female voice).
Max 100 chars per request; longest entry is 32 chars, so one request per entry.
"""
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

BASE = pathlib.Path(__file__).resolve().parent.parent
ENTRIES = json.load(open(BASE / "entries.json", encoding="utf-8"))
OUT_DIR = BASE / "audio" / "main"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
MIN_BYTES = 1000
failures = []

for e in ENTRIES:
    out = OUT_DIR / f"{e['id']}.mp3"
    if out.exists() and out.stat().st_size >= MIN_BYTES:
        continue
    if len(e["pt"]) > 100:
        failures.append({"id": e["id"], "error": "text too long"})
        continue
    url = ("https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=pt-PT&q="
           + urllib.parse.quote(e["pt"]))
    err = "unknown"
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            data = urllib.request.urlopen(req, timeout=20).read()
            if len(data) >= MIN_BYTES:
                out.write_bytes(data)
                n = sum(1 for f in OUT_DIR.glob("*.mp3") if f.stat().st_size >= MIN_BYTES)
                if n % 25 == 0:
                    print(f"progress: {n} / {len(ENTRIES)}", flush=True)
                time.sleep(0.2)
                break
            err = f"too small ({len(data)}B)"
        except Exception as ex:  # noqa: BLE001
            err = f"{type(ex).__name__}: {str(ex)[:120]}"
        time.sleep(1.2 * (attempt + 1))
    else:
        failures.append({"id": e["id"], "error": err})

total = sum(1 for f in OUT_DIR.glob("*.mp3") if f.stat().st_size >= MIN_BYTES)
print(f"generated files: {total} / {len(ENTRIES)}")
if failures:
    print(json.dumps(failures[:20], ensure_ascii=False))
    sys.exit(1)
print("OK")
