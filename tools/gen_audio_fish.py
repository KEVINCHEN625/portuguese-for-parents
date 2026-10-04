#!/usr/bin/env python3
"""Generate pt TTS audio for all entries via Fish Audio S2.1-Pro API.

Usage:
  export FISH_API_KEY=...            # required
  export FISH_MODEL="s2.1-pro-free"  # optional, default s2.1-pro-free
  export FISH_VOICE_ID=...           # optional reference_id from fish.audio voice library
  python3 tools/gen_audio_fish.py            # generate all (incremental, skips existing)
  python3 tools/gen_audio_fish.py 001 005 011  # only these entry ids (for samples)

The API key is read from the environment only — it must never be committed
(this repo is public).
"""
import json
import os
import pathlib
import sys
import time
import urllib.request

BASE = pathlib.Path(__file__).resolve().parent.parent
ENTRIES = json.load(open(BASE / "entries.json", encoding="utf-8"))
OUT_DIR = BASE / "audio" / "fish"

API_KEY = os.environ.get("FISH_API_KEY", "")
MODEL = os.environ.get("FISH_MODEL", "s2.1-pro-free")
# 2026-10-04 家人试听选定：Valentino (Português)
VOICE_ID = os.environ.get("FISH_VOICE_ID", "a35003f7cc784a989bf2d54db0d93f8f").strip()
SPEED = 0.9          # 稍慢于常速，适合跟读
BITRATE = 64         # mono mp3 64kbps 足够且省体积
MIN_BYTES = 800
CONCURRENCY = 4      # 起档并发限制为 5

if not API_KEY:
    sys.exit("FISH_API_KEY not set")

ENDPOINT = "https://api.fish.audio/v1/tts"


def synth(eid: str, text: str, tries: int = 5) -> str | None:
    out = OUT_DIR / f"{eid}.mp3"
    if out.exists() and out.stat().st_size >= MIN_BYTES:
        return None
    body = {
        "text": text,
        "prosody": {"speed": SPEED},
        "format": "mp3",
        "mp3_bitrate": BITRATE,
        "latency": "normal",
        "normalize": True,
    }
    if VOICE_ID:
        body["reference_id"] = VOICE_ID
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "model": MODEL,
        },
        method="POST",
    )
    err = "unknown"
    for attempt in range(tries):
        try:
            data = urllib.request.urlopen(req, timeout=60).read()
            if len(data) >= MIN_BYTES:
                out.write_bytes(data)
                return None
            err = f"too small ({len(data)}B): {data[:120]!r}"
        except urllib.error.HTTPError as ex:
            detail = ex.read()[:200].decode("utf-8", "replace")
            err = f"HTTP {ex.code}: {detail}"
            if ex.code in (401, 402):  # key/quota problem: no point retrying
                return f"{eid}: {err}"
        except Exception as ex:  # noqa: BLE001
            err = f"{type(ex).__name__}: {str(ex)[:120]}"
        time.sleep(1.5 * (attempt + 1))
    return f"{eid}: {err}"


def main() -> None:
    wanted = set(sys.argv[1:])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jobs = [(e["id"], e["pt"]) for e in ENTRIES if not wanted or e["id"] in wanted]
    errors = []
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        for i, res in enumerate(ex.map(lambda j: synth(*j), jobs), 1):
            if res:
                errors.append(res)
                print("FAIL", res, flush=True)
            if i % 25 == 0:
                print(f"progress: {i}/{len(jobs)}", flush=True)
    ok = sum(1 for f in OUT_DIR.glob("*.mp3") if f.stat().st_size >= MIN_BYTES)
    total_kb = sum(f.stat().st_size for f in OUT_DIR.glob("*.mp3")) // 1024
    print(f"fish voice: {ok} clips on disk ({total_kb} KB), model={MODEL}, voice={VOICE_ID or 'default'}, speed={SPEED}")
    if errors:
        sys.exit(f"{len(errors)} errors")


if __name__ == "__main__":
    main()
