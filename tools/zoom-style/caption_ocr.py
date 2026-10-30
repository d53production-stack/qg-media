#!/usr/bin/env python3
"""Read the burned-in captions with tesseract, so each move can be tied to
the words on screen when it starts.

Samples the caption band halfway through every caption (between the change
times from caption_sync.py) and at the start of every move, and writes
`captions` ([{t, text}]) plus `caption_text` on each move into the JSON.

    python3 caption_ocr.py clip.mp4 analysis/clip.json
"""
import json
import os
import re
import subprocess
import sys
import tempfile

import cv2

os.environ.setdefault("OMP_THREAD_LIMIT", "1")

CAP_Y0, CAP_Y1 = 1395, 1535


def ocr(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    g = cv2.bitwise_not(g)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
        cv2.imwrite(tf.name, g)
        try:
            out = subprocess.run(["tesseract", tf.name, "-", "--psm", "6"], capture_output=True, text=True, timeout=120).stdout
        finally:
            os.unlink(tf.name)
    words = re.findall(r"[A-Za-z0-9'$%.,-]+", out)
    text = " ".join(words).strip()
    # tesseract noise on an empty band is short and mixed case
    letters = sum(ch.isalpha() for ch in text)
    return text if letters >= 3 else ""


def grab(cap, t):
    cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, t) * 1000)
    ok, fr = cap.read()
    if not ok:
        return None
    if fr.shape[0] == 1920:
        return fr[CAP_Y0:CAP_Y1, :]
    return None


def main():
    video, jpath = sys.argv[1], sys.argv[2]
    d = json.load(open(jpath))
    cap = cv2.VideoCapture(video)
    dur = d["duration"]
    changes = [0.0] + list(d.get("caption_changes") or []) + [dur]
    times = {}
    for a, b in zip(changes, changes[1:]):
        if b - a >= 0.4:
            times[round((a + b) / 2, 2)] = "mid"
    for mv in d["moves"]:
        times[round(min(mv["start"] + 0.15, dur - 0.1), 2)] = "move"
    caps = []
    cache = {}
    for t in sorted(times):
        fr = grab(cap, t)
        text = ocr(fr) if fr is not None else ""
        cache[t] = text
        if times[t] == "mid":
            caps.append({"t": t, "text": text})
    d["captions"] = caps
    for mv in d["moves"]:
        t = round(min(mv["start"] + 0.15, dur - 0.1), 2)
        mv["caption_text"] = cache.get(t, "")
    json.dump(d, open(jpath, "w"), indent=1)
    print(f"{d['clip']}: {sum(1 for c in caps if c['text'])}/{len(caps)} captions read")


if __name__ == "__main__":
    main()
