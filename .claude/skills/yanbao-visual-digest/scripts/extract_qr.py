#!/usr/bin/env python3
"""Extract base64 image(s) — e.g. a QR the user pasted inline — from a Claude session JSONL.

When a user pastes a QR image into chat, it is NOT saved as a file; it lives as a
base64 image block inside the session transcript. This pulls it back out.

Usage:
    python extract_qr.py [session.jsonl] [out_dir]

With no jsonl, auto-picks the newest under ~/.claude/projects/**/*.jsonl.
Saves each image as qr_candidate_<i>.<ext> in out_dir (default: cwd) and prints sizes.
Then eyeball / decode them and pick the QR; clean it with crop_qr.py.
"""
import sys, os, json, base64, glob

def newest_jsonl():
    cands = glob.glob(os.path.expanduser("~/.claude/projects/**/*.jsonl"), recursive=True)
    if not cands:
        sys.exit("no session JSONL found under ~/.claude/projects/")
    return max(cands, key=os.path.getmtime)

jsonl = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else newest_jsonl()
out_dir = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else "."
os.makedirs(out_dir, exist_ok=True)
print("reading:", jsonl)

found = []
def walk(o):
    if isinstance(o, dict):
        if o.get("type") == "image" and isinstance(o.get("source"), dict):
            s = o["source"]
            if s.get("type") == "base64" and "data" in s:
                found.append((s.get("media_type", "image/png"), s["data"]))
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)

with open(jsonl, errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            walk(json.loads(line))
        except Exception:
            pass

ext = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
print("image blocks found:", len(found))
for i, (mt, data) in enumerate(found):
    raw = base64.b64decode(data)
    p = os.path.join(out_dir, f"qr_candidate_{i}.{ext.get(mt,'bin')}")
    with open(p, "wb") as g:
        g.write(raw)
    print(f"  [{i}] {mt} {len(raw)} bytes -> {p}")
