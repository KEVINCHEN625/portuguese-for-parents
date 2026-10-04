#!/usr/bin/env python3
"""Generate a second pt-PT voice locally with macOS `say` (Joana) as a reliable fallback."""
import json
import pathlib
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

BASE = pathlib.Path(__file__).resolve().parent.parent
ENTRIES = json.load(open(BASE / "entries.json", encoding="utf-8"))
OUT = BASE / "audio" / "joana"
TMP = pathlib.Path("/tmp/joana_aiff")
MIN_BYTES = 1500


def gen(e):
    eid, text = e["id"], e["pt"]
    m4a = OUT / f"{eid}.m4a"
    if m4a.exists() and m4a.stat().st_size >= MIN_BYTES:
        return None
    aiff = TMP / f"{eid}.aiff"
    r = subprocess.run(["say", "-v", "Joana", "-o", str(aiff), text], capture_output=True, timeout=30)
    if r.returncode != 0 or not aiff.exists():
        return f"{eid}: say failed"
    r2 = subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", "32000", str(aiff), str(m4a)],
                        capture_output=True, timeout=30)
    aiff.unlink(missing_ok=True)
    if r2.returncode != 0 or m4a.stat().st_size < MIN_BYTES:
        return f"{eid}: afconvert failed"
    return None


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=8) as ex:
        errors = [e for e in ex.map(gen, ENTRIES) if e]
    n = sum(1 for f in OUT.glob("*.m4a") if f.stat().st_size >= MIN_BYTES)
    print(f"joana: {n} / {len(ENTRIES)}")
    if errors:
        print(errors[:10])
        sys.exit(1)
    print("OK")
