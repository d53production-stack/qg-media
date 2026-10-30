#!/usr/bin/env python3
"""Draw where Matt's zooms land, as boxes over one wide dashboard frame.

Every zoomed hold is a rectangle in the coordinates of its own clip's
widest frame (centre + 1/zoom of the width and height). The dashboards
differ a little from day to day, but the app layout is the same (ladder on
the left, SPX / SPY / QQQ charts across), so one background frame is a fair
map.

    python3 focus_map.py analysis/ background.jpg focus-map.jpg
"""
import glob
import json
import os
import sys

import cv2
import numpy as np


def main():
    analysis_dir, bg_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    bg = cv2.imread(bg_path)
    H, W = bg.shape[:2]
    heat = np.zeros((H, W), np.float32)
    canvas = bg.copy()
    n = 0
    for f in sorted(glob.glob(os.path.join(analysis_dir, "*.json"))):
        d = json.load(open(f))
        holds = [h for h in d["holds"] if h["kind"] == "video" and h["dur"] >= 1.0 and h["zoom"]]
        if not holds:
            continue
        base = min(h["zoom"] for h in holds)
        for h in holds:
            z = h["zoom"] / base
            if z < 1.15 or not h["center"]:
                continue
            cx, cy = h["center"]
            w, hh = W / z, H / z
            x0, y0 = int((cx * W) - w / 2), int((cy * H) - hh / 2)
            x1, y1 = int(x0 + w), int(y0 + hh)
            x0c, y0c, x1c, y1c = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
            if x1c > x0c and y1c > y0c:
                heat[y0c:y1c, x0c:x1c] += h["dur"]
            color = (0, 255, 0) if z < 1.7 else ((0, 200, 255) if z < 2.2 else (0, 0, 255))
            cv2.rectangle(canvas, (x0, y0), (x1, y1), color, 1)
            n += 1
    if heat.max() > 0:
        hm = (heat / heat.max() * 255).astype(np.uint8)
        hm = cv2.applyColorMap(hm, cv2.COLORMAP_JET)
        blend = cv2.addWeighted(bg, 0.45, hm, 0.55, 0)
    else:
        blend = bg
    sheet = np.concatenate([canvas, blend], axis=0)
    cv2.putText(sheet, f"{n} zoomed holds: green <1.7x, orange <2.2x, red tighter", (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(sheet, "time-weighted heat map of where the zoomed window sits", (8, H + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.imwrite(out, sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(f"{n} zoomed holds drawn -> {out}")


if __name__ == "__main__":
    main()
