#!/usr/bin/env python3
"""Generate pt-PT Azure neural audio (edge-tts) for both voices, with retries.

edge-tts connectivity from this network is flaky (all requests were rejected
earlier the same day), so every clip gets up to 6 attempts with backoff and
integrity checks; a final summary reports anything still missing.
"""
import asyncio
import json
import pathlib
import sys

import edge_tts

BASE = pathlib.Path(__file__).resolve().parent.parent
ENTRIES = json.load(open(BASE / "entries.json", encoding="utf-8"))
VOICES = {"fernanda": "pt-PT-FernandaNeural", "duarte": "pt-PT-DuarteNeural"}
RATE = "-10%"
CONCURRENCY = 4
MIN_BYTES = 500

sem = asyncio.Semaphore(CONCURRENCY)
done = 0
failures = []


async def gen_one(comm: str, voice_name: str, eid: str, text: str):
    global done
    out = BASE / "audio" / comm / f"{eid}.mp3"
    if out.exists() and out.stat().st_size >= MIN_BYTES:
        done += 1
        return
    err = "unknown"
    async with sem:
        for attempt in range(6):
            try:
                tts = edge_tts.Communicate(text, voice_name, rate=RATE)
                await tts.save(str(out))
                if out.stat().st_size >= MIN_BYTES:
                    done += 1
                    if done % 25 == 0:
                        print(f"progress: {done} files", flush=True)
                    return
                err = f"too small ({out.stat().st_size}B)"
            except Exception as e:  # noqa: BLE001
                err = f"{type(e).__name__}: {str(e)[:100]}"
                out.unlink(missing_ok=True)
            await asyncio.sleep(1.2 * (attempt + 1))
    failures.append({"voice": comm, "id": eid, "error": err})


async def main():
    tasks = []
    for comm, voice_name in VOICES.items():
        (BASE / "audio" / comm).mkdir(parents=True, exist_ok=True)
        for e in ENTRIES:
            tasks.append(gen_one(comm, voice_name, e["id"], e["pt"]))
    await asyncio.gather(*tasks)
    for comm in VOICES:
        n = sum(1 for f in (BASE / "audio" / comm).glob("*.mp3") if f.stat().st_size >= MIN_BYTES)
        print(f"{comm}: {n} / {len(ENTRIES)}")
    if failures:
        print(json.dumps(failures[:20], ensure_ascii=False))
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    asyncio.run(main())
