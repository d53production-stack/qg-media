#!/usr/bin/env python3
"""Measure the zoom/crop moves inside QuantGeeks webinar highlight clips.

The clips are rendered 1080x1920 verticals: title band, a video window with
a crop of the webinar screen share, captions, CTA. There are no edit files,
so the zoom is measured from the rendered frames themselves:

1. find the video window (rows beside the template's green left bar),
2. sample the window at SAMPLE_FPS, match ORB features between consecutive
   samples and fit a similarity transform (scale + translation),
3. split the timeline into holds (the window sits still) and moves (a cut,
   or an animated zoom/pan ramp between two holds),
4. match every hold against every other, walk the match graph, and express
   each hold's zoom relative to the widest hold in the clip, plus where the
   hold is looking inside that widest frame.

Output: one JSON per clip in --out, plus a contact sheet of hold keyframes.

    python3 analyze_zoom.py clip.mp4 [clip2.mp4 ...] --out analysis/
"""
import argparse
import json
import math
import os
import sys

import cv2
import numpy as np

SAMPLE_FPS = 10
WORK_W = 540           # window is downscaled to this width before matching
CUT_DIFF = 0.35        # mean abs diff (0-1) between samples that counts as a cut
MOVE_LOG = 0.03        # |log scale| per sample that counts as zoom motion
MOVE_PX = 8            # translation per sample (at WORK_W) that counts as pan motion
JUMP_LOG = 0.25        # one-sample change this big is a cut, not a ramp
JUMP_PX = 120
MIN_HOLD_S = 0.3


def find_window(cap, n_frames):
    """The video window: the rows beside the template's green left bar, or
    the template's known slot."""
    cap.set(cv2.CAP_PROP_POS_FRAMES, n_frames // 2)
    ok, f = cap.read()
    if not ok:
        return None
    strip = f[:, :6, :].astype(int)
    green = (strip[:, :, 1] > 150) & (strip[:, :, 2] < 120) & (strip[:, :, 0] < 120)
    rows = np.where(green.mean(axis=1) > 0.5)[0]
    rows = rows[rows > 300]          # the top band also has a green accent
    if len(rows) > 400 and rows.max() - rows.min() < len(rows) * 1.2:
        return int(rows.min()), int(rows.max())
    if f.shape[0] == 1920 and f.shape[1] == 1080:
        return 610, 1400
    return None


def similarity(prev_kp, prev_des, kp, des, matcher):
    """Scale and translation that maps prev onto cur, or None."""
    if prev_des is None or des is None or len(prev_kp) < 12 or len(kp) < 12:
        return None
    pairs = matcher.knnMatch(prev_des, des, k=2)
    good = [m for m, n in (p for p in pairs if len(p) == 2) if m.distance < 0.75 * n.distance]
    if len(good) < 12:
        return None
    src = np.float32([prev_kp[m.queryIdx].pt for m in good])
    dst = np.float32([kp[m.trainIdx].pt for m in good])
    M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=3.0)
    if M is None or inl is None or inl.sum() < 10:
        return None
    s = math.hypot(M[0, 0], M[0, 1])
    if not (0.2 < s < 5.0):
        return None
    return {"scale": float(s), "tx": float(M[0, 2]), "ty": float(M[1, 2]), "inliers": int(inl.sum()), "n": len(good)}


def read_samples(path, y0, y1):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, int(round(fps / SAMPLE_FPS)))
    orb = cv2.ORB_create(nfeatures=1500, fastThreshold=10)
    samples = []
    i = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i % step == 0:
            crop = f[y0:y1, :]
            scale = WORK_W / crop.shape[1]
            small = cv2.resize(crop, (WORK_W, int(crop.shape[0] * scale)), interpolation=cv2.INTER_AREA)
            g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            kp, des = orb.detectAndCompute(g, None)
            samples.append({"t": i / fps, "g": g, "kp": kp, "des": des, "bgr": small})
        i += 1
    cap.release()
    return samples, fps, n_frames


def segment(samples, matcher):
    """Holds and moves along the sample timeline."""
    moving = [False]
    motions = [None]
    diffs = [0.0]
    for a, b in zip(samples, samples[1:]):
        d = float(np.abs(a["g"].astype(np.int16) - b["g"].astype(np.int16)).mean()) / 255.0
        m = similarity(a["kp"], a["des"], b["kp"], b["des"], matcher)
        diffs.append(d)
        motions.append(m)
        if m is None:
            moving.append(d > 0.12)
        else:
            moving.append(d > CUT_DIFF or abs(math.log(m["scale"])) > MOVE_LOG
                          or abs(m["tx"]) > MOVE_PX or abs(m["ty"]) > MOVE_PX)
    # runs
    events = []   # ("hold"|"move", first_sample, last_sample_inclusive)
    k = 0
    n = len(samples)
    while k < n:
        j = k
        while j + 1 < n and moving[j + 1] == moving[k] and (j + 1 > 0):
            j += 1
        events.append(("move" if moving[k] else "hold", k, j))
        k = j + 1
    # sample 0 is never "moving"; a hold shorter than MIN_HOLD_S between two
    # moves is swallowed into one move
    merged = []
    for ev in events:
        kind, a, b = ev
        dur = (b - a + 1) / SAMPLE_FPS
        if kind == "hold" and dur < MIN_HOLD_S and merged and merged[-1][0] == "move":
            merged[-1] = ("move", merged[-1][1], b)
        elif kind == "move" and merged and merged[-1][0] == "move":
            merged[-1] = ("move", merged[-1][1], b)
        else:
            merged.append(ev)
    holds, moves = [], []
    for kind, a, b in merged:
        t0, t1 = samples[a]["t"], samples[b]["t"] + 1 / SAMPLE_FPS
        if kind == "hold":
            holds.append({"index": len(holds), "start": round(t0, 2), "end": round(t1, 2),
                          "dur": round(t1 - t0, 2), "s0": a, "s1": b})
        else:
            ms = [motions[k] for k in range(a, b + 1)]
            known = [m for m in ms if m is not None]
            log_sum = sum(math.log(m["scale"]) for m in known)
            px = sum(m["tx"] for m in known)
            py = sum(m["ty"] for m in known)
            one = (b - a + 1) == 1
            jump = any(m is None or abs(math.log(m["scale"])) > JUMP_LOG or abs(m["tx"]) > JUMP_PX or abs(m["ty"]) > JUMP_PX for m in ms)
            big_diff = max(diffs[a:b + 1]) > CUT_DIFF
            moves.append({"index": len(moves), "start": round(t0, 2), "end": round(t1, 2),
                          "dur": round(t1 - t0, 2),
                          "type": "cut" if (one and (jump or big_diff)) or (jump and not known) else ("ramp" if known else "cut"),
                          "log_scale": round(log_sum, 3), "pan_px": round(math.hypot(px, py), 1),
                          "after_hold": len(holds) - 1 if holds else None})
    return holds, moves


def resolve_zoom(holds, samples, matcher):
    """Zoom of each hold relative to the widest hold, via pairwise matching."""
    def key(h):
        return samples[(h["s0"] + h["s1"]) // 2]

    keys = [key(h) for h in holds]
    n = len(holds)
    for h, ks in zip(holds, keys):
        h["features"] = 0 if ks["des"] is None else len(ks["kp"])
    pair = {}
    for i in range(n):
        for j in range(i + 1, n):
            m = similarity(keys[i]["kp"], keys[i]["des"], keys[j]["kp"], keys[j]["des"], matcher)
            if m is not None:
                s, tx, ty = m["scale"], m["tx"], m["ty"]
                pair[(i, j)] = (s, tx, ty)
                pair[(j, i)] = (1 / s, -tx / s, -ty / s)
    degree = [sum(1 for (a, b) in pair if a == i) for i in range(n)]
    # rel[i] = (s, tx, ty) mapping hold i's window coordinates into the
    # start hold's coordinates, composed along the match graph
    rel = {}
    if n:
        start = max(range(n), key=lambda i: (degree[i], holds[i]["dur"]))
        rel[start] = (1.0, 0.0, 0.0)
        frontier = [start]
        while frontier:
            i = frontier.pop()
            for (a, b), (s, tx, ty) in pair.items():
                if a == i and b not in rel:
                    # b -> a is the inverse of a -> b, then a -> start
                    sb, txb, tyb = pair[(b, a)]
                    sa, txa, tya = rel[a]
                    rel[b] = (sa * sb, sa * txb + txa, sa * tyb + tya)
                    frontier.append(b)
    for h in holds:
        h["kind"] = "card" if (h["features"] < 80 or (degree[h["index"]] == 0 and n > 1)) else "video"
        h["zoom"] = None
        h["center"] = None
    resolved = [i for i in rel if holds[i]["kind"] == "video"]
    unresolved = [h["index"] for h in holds if h["kind"] == "video" and h["index"] not in rel]
    widest = None
    if resolved:
        # a zoomed-in hold maps into the start frame with scale < 1; the
        # widest hold is the one with the largest scale
        widest = max(resolved, key=lambda i: rel[i][0])
        sw, txw, tyw = rel[widest]
        wh, ww = keys[widest]["g"].shape
        wk = keys[widest]
        for i in resolved:
            si, txi, tyi = rel[i]
            # i -> start -> widest, unless a direct match is available
            s = si / sw
            tx = (txi - txw) / sw
            ty = (tyi - tyw) / sw
            if i != widest:
                m = similarity(keys[i]["kp"], keys[i]["des"], wk["kp"], wk["des"], matcher)
                if m is not None and m["inliers"] >= 30:
                    s, tx, ty = m["scale"], m["tx"], m["ty"]
                    holds[i]["direct"] = True
            holds[i]["zoom"] = round(1 / s, 3)
            cx = (s * ww / 2 + tx) / ww
            cy = (s * wh / 2 + ty) / wh
            holds[i]["center"] = [round(cx, 3), round(cy, 3)]
    return widest, unresolved, keys


def contact_sheet(holds, keys, path):
    tiles = []
    for h, ks in zip(holds, keys):
        tile = ks["bgr"].copy()
        z = "?" if h["zoom"] is None else f"{h['zoom']:.2f}x"
        label = f"#{h['index']} {h['start']:.1f}-{h['end']:.1f}s {z} {h['kind']}"
        cv2.rectangle(tile, (0, 0), (tile.shape[1], 22), (0, 0, 0), -1)
        cv2.putText(tile, label, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
        tiles.append(tile)
    if not tiles:
        return
    cols = 3
    th, tw = tiles[0].shape[:2]
    rows_n = math.ceil(len(tiles) / cols)
    sheet = np.zeros((rows_n * th, cols * tw, 3), np.uint8)
    for k, t in enumerate(tiles):
        r, c = divmod(k, cols)
        sheet[r * th:(r + 1) * th, c * tw:(c + 1) * tw] = t
    cv2.imwrite(path, sheet, [cv2.IMWRITE_JPEG_QUALITY, 80])


def analyze(path, out_dir):
    name = os.path.splitext(os.path.basename(path))[0]
    cap = cv2.VideoCapture(path)
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    win = find_window(cap, n_frames)
    cap.release()
    if win is None:
        print(f"{name}: no video window found", file=sys.stderr)
        return None
    y0, y1 = win
    samples, fps, n_frames = read_samples(path, y0, y1)
    if len(samples) < 3:
        return None
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    holds, moves = segment(samples, matcher)
    widest, unresolved, keys = resolve_zoom(holds, samples, matcher)
    # zoom change across each move, from the holds either side
    for mv in moves:
        a = mv["after_hold"]
        b = a + 1 if a is not None else 0
        za = holds[a]["zoom"] if a is not None and a < len(holds) else None
        zb = holds[b]["zoom"] if b < len(holds) else None
        mv["zoom_from"] = za
        mv["zoom_to"] = zb
        mv["zoom_ratio"] = round(zb / za, 3) if za and zb else None
    for h in holds:
        h.pop("s0", None)
        h.pop("s1", None)
    res = {
        "clip": name,
        "fps": fps,
        "frame": [W, H],
        "window": {"y0": y0, "y1": y1, "h": y1 - y0, "w": W},
        "duration": round(n_frames / fps, 2),
        "sample_fps": SAMPLE_FPS,
        "widest_hold": widest,
        "holds": holds,
        "moves": moves,
        "unresolved_holds": unresolved,
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, name + ".json"), "w") as fh:
        json.dump(res, fh, indent=1)
    contact_sheet(holds, keys, os.path.join(out_dir, name + "-holds.jpg"))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--out", default="analysis")
    args = ap.parse_args()
    for p in args.clips:
        r = analyze(p, args.out)
        if r:
            zs = [h["zoom"] for h in r["holds"]]
            mv = [(m["type"], m["zoom_ratio"]) for m in r["moves"]]
            print(f"{r['clip']}: {len(r['holds'])} holds {zs}; moves {mv}")


if __name__ == "__main__":
    main()
