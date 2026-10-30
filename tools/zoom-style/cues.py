#!/usr/bin/env python3
"""Attention cues inside each hold: Matt's live red-ink annotations.

During the webinar Matt draws red circles and arrows on the dashboard. They
are the strongest visible "look here" signal, so for every hold we measure
how much red ink is on screen and where it sits inside the window. That lets
the comparison ask: when Matt zooms, is the ink inside the zoom, and is it
centred? And in the wide holds, was there ink he chose not to zoom on?

    python3 cues.py clip.mp4 analysis/clip.json   (writes "ink" into each hold)
"""
import json
import os
import sys

import cv2
import numpy as np


def ink_mask(bgr):
    b, g, r = bgr[:, :, 0].astype(int), bgr[:, :, 1].astype(int), bgr[:, :, 2].astype(int)
    return (r > 170) & (g < 90) & (b < 90) & (r - np.maximum(g, b) > 100)


def measure(frame, y0, y1):
    win = frame[y0:y1]
    m = ink_mask(win)
    n = int(m.sum())
    h, w = m.shape
    if n < 40:
        return {"px": n, "share": 0.0, "center": None, "bbox": None}
    ys, xs = np.where(m)
    x0, x1 = np.percentile(xs, [2, 98])
    yy0, yy1 = np.percentile(ys, [2, 98])
    return {
        "px": n,
        "share": round(n / (h * w), 5),
        "center": [round(float(xs.mean() / w), 3), round(float(ys.mean() / h), 3)],
        "bbox": [round(float(x0 / w), 3), round(float(yy0 / h), 3), round(float(x1 / w), 3), round(float(yy1 / h), 3)],
    }


def run(clip, json_path):
    d = json.load(open(json_path))
    y0, y1 = d["window"]["y0"], d["window"]["y1"]
    cap = cv2.VideoCapture(clip)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    for h in d["holds"]:
        if h["kind"] != "video":
            h["ink"] = None
            continue
        # sample three frames across the hold, keep the strongest ink
        best = None
        for frac in (0.25, 0.5, 0.85):
            t = h["start"] + frac * h["dur"]
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
            ok, f = cap.read()
            if not ok:
                continue
            r = measure(f, y0, y1)
            if best is None or r["px"] > best["px"]:
                best = r
        h["ink"] = best
    cap.release()
    with open(json_path, "w") as fh:
        json.dump(d, fh, indent=1)
    return d


def main():
    clip, jp = sys.argv[1], sys.argv[2]
    d = run(clip, jp)
    print(d["clip"], [(h["index"], h["zoom"], None if not h["ink"] else h["ink"]["px"]) for h in d["holds"]])


if __name__ == "__main__":
    main()
