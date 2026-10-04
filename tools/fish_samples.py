#!/usr/bin/env python3
"""Generate audition samples: 5 candidate voices x entries 003/007/020/050."""
import json
import os
import pathlib
import urllib.request

BASE = pathlib.Path(__file__).resolve().parent.parent
KEY = os.environ["FISH_API_KEY"]
OUT = BASE / "samples"

VOICES = {
    "A_default": None,
    "B_valentino": "ba72c1300ed14630b21aa017e341fdd9",
    "C_valentino2": "a35003f7cc784a989bf2d54db0d93f8f",
    "D_jarvis": "ec426c7ea3554caba8a5b077a4c701aa",
    "E_narrador": "0ba1afd27db44eb2b4cb27fd331b93aa",
}
ENTRY_IDS = ["004", "008", "021", "024"]
ENTRIES = {e["id"]: e["pt"] for e in json.load(open(BASE / "entries.json", encoding="utf-8"))}


def synth(text, voice_id):
    body = {
        "text": text,
        "prosody": {"speed": 0.9},
        "format": "mp3",
        "mp3_bitrate": 64,
        "latency": "normal",
    }
    if voice_id:
        body["reference_id"] = voice_id
    req = urllib.request.Request(
        "https://api.fish.audio/v1/tts",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                 "model": "s2.1-pro-free"},
        method="POST",
    )
    return urllib.request.urlopen(req, timeout=60).read()


for vkey, vid in VOICES.items():
    d = OUT / vkey
    d.mkdir(parents=True, exist_ok=True)
    for eid in ENTRY_IDS:
        path = d / f"{eid}.mp3"
        if path.exists() and path.stat().st_size > 800:
            continue
        for attempt in range(4):
            try:
                data = synth(ENTRIES[eid], vid)
                if len(data) >= 800:
                    path.write_bytes(data)
                    print(f"{vkey}/{eid}.mp3  {len(data)}B", flush=True)
                    break
            except urllib.error.HTTPError as ex:
                print(f"{vkey}/{eid} HTTP {ex.code}: {ex.read()[:150]!r}", flush=True)
                if ex.code in (401, 402):
                    raise SystemExit(1)
            import time; time.sleep(2 * (attempt + 1))
print("DONE")
