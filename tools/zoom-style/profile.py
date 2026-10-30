#!/usr/bin/env python3
"""Turn the per-clip JSON from analyze_zoom.py into a zoom style profile.

    python3 profile.py analysis/ > profile.json
    python3 profile.py analysis/ --md > PROFILE.md
"""
import argparse
import glob
import json
import os
from collections import Counter

ZOOMED = 1.15        # a hold this far above the clip's widest hold counts as zoomed in
TIGHT = 1.6
PAN_PX = 60          # net translation (at 540 px wide) for a same-zoom move to count as a pan


def pct(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    k = (len(xs) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (k - lo), 2)


def spread(xs):
    return {"median": pct(xs, 0.5), "p25": pct(xs, 0.25), "p75": pct(xs, 0.75), "n": len([x for x in xs if x is not None])}


def grid_cell(center):
    cx, cy = center
    col = "left" if cx < 0.36 else ("right" if cx > 0.64 else "center")
    row = "top" if cy < 0.4 else ("bottom" if cy > 0.6 else "middle")
    return f"{row}-{col}"


def classify_move(mv, holds, clip_end):
    """cut / zoom-in / zoom-out / pan / template (slide in or out) / unknown."""
    a = mv["after_hold"]
    nxt = a + 1 if a is not None else 0
    before = holds[a] if a is not None and a < len(holds) else None
    after = holds[nxt] if nxt < len(holds) else None
    if mv["start"] < 1.0 and (before is None or before["dur"] <= 0.3):
        return "template"
    if after is None or after["kind"] in ("card", "template") or (before and before["kind"] in ("card", "template")):
        return "template"
    r = mv["zoom_ratio"]
    if mv["type"] == "cut":
        return "cut"
    if r is None:
        return "unknown"
    if r >= 1.1:
        return "zoom-in"
    if r <= 0.9:
        return "zoom-out"
    if mv["pan_px"] >= PAN_PX:
        return "pan"
    return "nudge"


def summarize(files):
    per_clip = []
    hold_durs, zoomed_durs, wide_durs, zoom_levels = [], [], [], []
    first_zoom, zoomed_share, moves_per_min = [], [], []
    cells, move_kinds = Counter(), Counter()
    ramp_durs, zoom_in_ratio, zoom_out_ratio = [], [], []
    opens_zoomed = 0
    clips_with_video = 0
    sequences = Counter()
    for f in files:
        d = json.load(open(f))
        holds = [h for h in d["holds"] if h["kind"] == "video" and h["dur"] >= 0.3]
        # the template ends every clip with a 3.6 s pull-back hold before the
        # end card; it is not one of Matt's moves
        if holds and holds[-1] is d["holds"][-1] and holds[-1]["dur"] <= 3.7:
            holds[-1]["kind"] = "template"
            holds = holds[:-1]
        if not holds:
            continue
        # re-base: the widest real hold (held at least 1 s) is 1.0x
        base = min((h["zoom"] for h in holds if h["zoom"] and h["dur"] >= 1.0), default=None)
        if base:
            for h in d["holds"]:
                if h["zoom"]:
                    h["zoom"] = round(h["zoom"] / base, 3)
            for mv in d["moves"]:
                for k in ("zoom_from", "zoom_to"):
                    if mv.get(k):
                        mv[k] = round(mv[k] / base, 3)
        clips_with_video += 1
        video_end = max(h["end"] for h in holds)
        video_len = video_end - min(h["start"] for h in holds)
        kinds = []
        for mv in d["moves"]:
            k = classify_move(mv, d["holds"], d["duration"])
            mv["kind"] = k
            if k == "template":
                continue
            move_kinds[k] += 1
            kinds.append(k)
            if k in ("zoom-in", "zoom-out", "pan"):
                ramp_durs.append(mv["dur"])
            if k == "zoom-in":
                zoom_in_ratio.append(mv["zoom_ratio"])
            if k == "zoom-out":
                zoom_out_ratio.append(mv["zoom_ratio"])
        for x, y in zip(kinds, kinds[1:]):
            sequences[f"{x} > {y}"] += 1
        real_moves = len(kinds)
        moves_per_min.append(real_moves / video_len * 60 if video_len else None)
        z_time = 0.0
        fz = None
        first = holds[0]
        if first["zoom"] and first["zoom"] >= ZOOMED:
            opens_zoomed += 1
        for h in holds:
            hold_durs.append(h["dur"])
            if h["zoom"] is None:
                continue
            zoom_levels.append(h["zoom"])
            if h["zoom"] >= ZOOMED:
                zoomed_durs.append(h["dur"])
                z_time += h["dur"]
                if fz is None:
                    fz = h["start"]
                if h["center"]:
                    cells[grid_cell(h["center"])] += 1
            else:
                wide_durs.append(h["dur"])
        zoomed_share.append(z_time / video_len if video_len else None)
        if fz is not None:
            first_zoom.append(fz)
        per_clip.append({
            "clip": d["clip"],
            "duration": d["duration"],
            "holds": len(holds),
            "moves": real_moves,
            "moves_per_min": round(real_moves / video_len * 60, 1) if video_len else None,
            "zoomed_share": round(z_time / video_len, 2) if video_len else None,
            "max_zoom": max((h["zoom"] for h in holds if h["zoom"]), default=None),
            "opens_zoomed": bool(first["zoom"] and first["zoom"] >= ZOOMED),
            "first_zoom_s": fz,
            "move_kinds": dict(Counter(kinds)),
            "unresolved": len(d.get("unresolved_holds", [])),
        })
    prof = {
        "clips": clips_with_video,
        "total_minutes": round(sum(r["duration"] for r in per_clip) / 60, 1),
        "holds_total": len(hold_durs),
        "moves_per_min": spread(moves_per_min),
        "hold_dur_s": {**spread(hold_durs), "p90": pct(hold_durs, 0.9)},
        "zoomed_hold_dur_s": spread(zoomed_durs),
        "wide_hold_dur_s": spread(wide_durs),
        "zoomed_share_of_time": spread(zoomed_share),
        "opens_zoomed_share": round(opens_zoomed / clips_with_video, 2) if clips_with_video else None,
        "first_zoom_s": {**spread(first_zoom), "clips_with_no_zoom": sum(1 for r in per_clip if r["first_zoom_s"] is None)},
        "zoom_level_when_zoomed": {**spread([z for z in zoom_levels if z >= ZOOMED]), "max": max(zoom_levels) if zoom_levels else None},
        "zoom_histogram": dict(sorted(Counter(
            ("1.0-1.15" if z < 1.15 else "1.15-1.4" if z < 1.4 else "1.4-1.6" if z < 1.6 else "1.6-1.9" if z < 1.9 else "1.9-2.5" if z < 2.5 else "2.5+")
            for z in zoom_levels).items())),
        "move_kinds": dict(move_kinds.most_common()),
        "ramp_dur_s": spread(ramp_durs),
        "zoom_in_ratio": spread(zoom_in_ratio),
        "zoom_out_ratio": spread(zoom_out_ratio),
        "move_sequences": dict(sequences.most_common(8)),
        "focus_cells_when_zoomed": dict(cells.most_common()),
        "per_clip": per_clip,
    }
    return prof


def fmt(s, unit=""):
    if not s or s.get("median") is None:
        return "n/a"
    return f"median {s['median']}{unit} (middle half {s['p25']} to {s['p75']}{unit}, n={s['n']})"


def to_md(p):
    L = []
    L.append("# Matt's zoom style, measured from the highlight clips\n")
    L.append(f"{p['clips']} clips, {p['total_minutes']} minutes, {p['holds_total']} holds. A hold is a stretch where the video window sits still; a move is the cut or the short animated ramp between two holds. Zoom is relative to the widest hold in the same clip (1.0x = the widest view that clip ever shows). Template slide-ins and the end card are excluded.\n")
    L.append("## Pace\n")
    L.append(f"- Moves per minute of video: {fmt(p['moves_per_min'])}")
    L.append(f"- Hold length: {fmt(p['hold_dur_s'], 's')}, one in ten over {p['hold_dur_s']['p90']}s")
    L.append(f"- Zoomed holds (>= {ZOOMED}x): {fmt(p['zoomed_hold_dur_s'], 's')}")
    L.append(f"- Wide holds: {fmt(p['wide_hold_dur_s'], 's')}\n")
    L.append("## How much and how tight\n")
    L.append(f"- Share of the clip spent zoomed in: {fmt(p['zoomed_share_of_time'])}")
    L.append(f"- Clips that open already zoomed in: {p['opens_zoomed_share']}")
    L.append(f"- First zoom arrives at {fmt(p['first_zoom_s'], 's')}; {p['first_zoom_s']['clips_with_no_zoom']} clips never zoom")
    z = p["zoom_level_when_zoomed"]
    L.append(f"- Zoom level when zoomed: {fmt(z, 'x')}, tightest {z['max']}x")
    L.append(f"- Zoom level histogram over all holds: {p['zoom_histogram']}\n")
    L.append("## How the moves are made\n")
    L.append(f"- Move kinds: {p['move_kinds']}")
    L.append(f"- Animated moves last {fmt(p['ramp_dur_s'], 's')}")
    L.append(f"- Zoom-in step: {fmt(p['zoom_in_ratio'], 'x')}; zoom-out step: {fmt(p['zoom_out_ratio'], 'x')}")
    L.append(f"- Most common move sequences: {p['move_sequences']}\n")
    L.append("## Where the zoom lands (position of the zoomed view inside the clip's widest frame)\n")
    for k, v in p["focus_cells_when_zoomed"].items():
        L.append(f"- {k}: {v}")
    L.append("")
    L.append("## Per clip\n")
    L.append("| clip | s | holds | moves/min | zoomed share | max zoom | opens zoomed | first zoom s | moves | unresolved |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in p["per_clip"]:
        L.append(f"| {r['clip']} | {r['duration']} | {r['holds']} | {r['moves_per_min']} | {r['zoomed_share']} | {r['max_zoom']} | {'yes' if r['opens_zoomed'] else 'no'} | {r['first_zoom_s']} | {r['move_kinds']} | {r['unresolved']} |")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("analysis_dir")
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--glob", default="*.json")
    args = ap.parse_args()
    files = sorted(glob.glob(os.path.join(args.analysis_dir, args.glob)))
    p = summarize(files)
    print(to_md(p) if args.md else json.dumps(p, indent=1))


if __name__ == "__main__":
    main()
