#!/usr/bin/env python3
"""Do Matt's moves line up with what is being said?

There is no transcript in the repo, but the captions are burned in under the
video window and change phrase by phrase. This measures, per clip, when the
caption band changes and how far each zoom move sits from the nearest
caption change. A move that lands within about half a second of a new
phrase is a move made on the words.

    python3 caption_sync.py analysis/ clip.mp4 [clip2.mp4 ...]
    (writes "caption_changes" and per-move "caption_offset_s" into the JSON,
     prints a summary)
"""
import glob
import json
import os
import sys

import cv2
import numpy as np

SAMPLE_FPS = 10
CAP_Y0, CAP_Y1 = 1405, 1530       # caption band in the 1080x1920 template
CHANGE = 0.06                     # mean abs diff (0-1) that counts as a new phrase
MIN_GAP_S = 0.5


def caption_changes(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, int(round(fps / SAMPLE_FPS)))
    prev = None
    changes = []
    i = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i % step == 0:
            g = cv2.cvtColor(cv2.resize(f[CAP_Y0:CAP_Y1], (270, 32), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.int16)
            if prev is not None:
                d = float(np.abs(g - prev).mean()) / 255.0
                t = i / fps
                if d > CHANGE and (not changes or t - changes[-1] >= MIN_GAP_S):
                    changes.append(round(t, 2))
            prev = g
        i += 1
    cap.release()
    return changes


def main():
    analysis_dir = sys.argv[1]
    clips = sys.argv[2:]
    offsets, n_moves = [], 0
    baseline = []          # the same statistic for random times in the clip
    rng = np.random.default_rng(0)
    for clip in clips:
        name = os.path.splitext(os.path.basename(clip))[0]
        jp = os.path.join(analysis_dir, name + ".json")
        if not os.path.exists(jp):
            continue
        d = json.load(open(jp))
        ch = caption_changes(clip)
        d["caption_changes"] = ch
        for mv in d["moves"]:
            if mv.get("kind") == "template" or not ch:
                mv["caption_offset_s"] = None
                continue
            # signed: negative = move came before the nearest caption change
            near = min(ch, key=lambda c: abs(c - mv["start"]))
            mv["caption_offset_s"] = round(mv["start"] - near, 2)
            if 1.0 < mv["start"] < d["duration"] - 4.5:
                offsets.append(mv["start"] - near)
                n_moves += 1
                for _ in range(5):
                    r = rng.uniform(1.0, d["duration"] - 4.5)
                    baseline.append(abs(r - min(ch, key=lambda c: abs(c - r))))
        json.dump(d, open(jp, "w"), indent=1)
        print(f"{name}: {len(ch)} caption changes, {len(d['moves'])} moves")
    if offsets:
        a = np.abs(np.array(offsets))
        print(json.dumps({
            "moves": n_moves,
            "within_0.3s_of_a_caption_change": round(float((a <= 0.3).mean()), 2),
            "within_0.5s": round(float((a <= 0.5).mean()), 2),
            "within_1.0s": round(float((a <= 1.0).mean()), 2),
            "median_abs_offset_s": round(float(np.median(a)), 2),
            "median_signed_offset_s": round(float(np.median(offsets)), 2),
            "baseline_random_within_0.3s": round(float((np.array(baseline) <= 0.3).mean()), 2),
            "baseline_random_within_0.5s": round(float((np.array(baseline) <= 0.5).mean()), 2),
            "baseline_random_median_abs_s": round(float(np.median(baseline)), 2),
        }, indent=1))


if __name__ == "__main__":
    main()
