#!/usr/bin/env python3
"""Side by side: Matt's measured zoom style against Claude's default rules.

    python3 compare.py profile.json analysis/ > COMPARISON.md

Claude's defaults are the numbers in CLAUDE-DEFAULT-STYLE.md, copied here
so the table is generated from one place. The ink section reads the "ink"
field that cues.py adds to each hold.
"""
import glob
import json
import os
import sys

CLAUDE = {
    "moves_per_min": (8, 12),
    "hold_dur_s": (4, 6),
    "zoomed_share": (0.5, 0.6),
    "zoom_level": (1.5, 1.5),
    "tight_zoom": (2.0, 2.5),
    "ramp_dur_s": (0.4, 0.6),
    "opens_zoomed": (0.0, 0.0),
    "first_zoom_s": (1.5, 3.0),
    "max_hold_s": (10, 10),
}


def rng(lo, hi, unit=""):
    return f"{lo}{unit}" if lo == hi else f"{lo} to {hi}{unit}"


def row(label, matt, claude, note):
    return f"| {label} | {matt} | {claude} | {note} |"


def verdict(matt_med, lo, hi, lower_is="less"):
    if matt_med is None:
        return "no data"
    if matt_med < lo:
        return f"Matt {lower_is}"
    if matt_med > hi:
        return f"Matt {'more' if lower_is == 'less' else 'less'}"
    return "same"


def ink_stats(analysis_dir):
    """How Matt's zooms relate to his own red ink."""
    zoomed_with_ink = zoomed_total = 0
    wide_with_ink = wide_total = 0
    centred = []
    for f in glob.glob(os.path.join(analysis_dir, "*.json")):
        d = json.load(open(f))
        holds = [h for h in d["holds"] if h["kind"] == "video" and h["dur"] >= 1.0 and h.get("ink") is not None]
        if not holds:
            continue
        base = min((h["zoom"] for h in holds if h["zoom"]), default=1.0) or 1.0
        for h in holds:
            z = (h["zoom"] or 0) / base
            has = h["ink"]["px"] >= 150
            if z >= 1.15:
                zoomed_total += 1
                zoomed_with_ink += has
                if has:
                    cx, cy = h["ink"]["center"]
                    centred.append(max(abs(cx - 0.5), abs(cy - 0.5)))
            else:
                wide_total += 1
                wide_with_ink += has
    return {
        "zoomed_holds": zoomed_total,
        "zoomed_with_ink": zoomed_with_ink,
        "wide_holds": wide_total,
        "wide_with_ink": wide_with_ink,
        "ink_offcentre_median": round(sorted(centred)[len(centred) // 2], 3) if centred else None,
    }


def main():
    prof = json.load(open(sys.argv[1]))
    analysis_dir = sys.argv[2] if len(sys.argv) > 2 else None
    L = ["# Matt's zoom style vs Claude's default\n",
         f"Matt's numbers are medians over {prof['clips']} highlight clips ({prof['total_minutes']} min). Claude's are the defaults in CLAUDE-DEFAULT-STYLE.md.\n",
         "| what | Matt (measured) | Claude (default) | read |",
         "|---|---|---|---|"]
    m = prof["moves_per_min"]["median"]
    L.append(row("moves per minute", m, rng(*CLAUDE["moves_per_min"]), verdict(m, *CLAUDE["moves_per_min"])))
    h = prof["hold_dur_s"]["median"]
    L.append(row("hold length (s)", f"{h} (p90 {prof['hold_dur_s']['p90']})", rng(*CLAUDE["hold_dur_s"], "s"), verdict(h, *CLAUDE["hold_dur_s"], lower_is="shorter")))
    zs = prof["zoomed_share_of_time"]["median"]
    L.append(row("share of time zoomed in", zs, rng(*CLAUDE["zoomed_share"]), verdict(zs, *CLAUDE["zoomed_share"])))
    zl = prof["zoom_level_when_zoomed"]["median"]
    L.append(row("zoom level when zoomed", f"{zl}x (middle half {prof['zoom_level_when_zoomed']['p25']} to {prof['zoom_level_when_zoomed']['p75']}x)", rng(*CLAUDE["zoom_level"], "x"), verdict(zl, *CLAUDE["zoom_level"], lower_is="looser")))
    L.append(row("tightest zoom used", f"{prof['zoom_level_when_zoomed']['max']}x", rng(*CLAUDE["tight_zoom"], "x"), ""))
    hist = prof["zoom_histogram"]
    L.append(row("zoom histogram", str(hist), "mostly 1.5x, some 2 to 2.5x", ""))
    rd = prof["ramp_dur_s"]["median"]
    L.append(row("animated move length (s)", rd, rng(*CLAUDE["ramp_dur_s"], "s"), verdict(rd, *CLAUDE["ramp_dur_s"], lower_is="faster")))
    oz = prof["opens_zoomed_share"]
    L.append(row("clips that open already zoomed", oz, "0 (always open wide)", verdict(oz, *CLAUDE["opens_zoomed"])))
    fz = prof["first_zoom_s"]["median"]
    L.append(row("first zoom at (s)", fz, rng(*CLAUDE["first_zoom_s"], "s"), verdict(fz, *CLAUDE["first_zoom_s"], lower_is="earlier")))
    L.append(row("move kinds", str(prof["move_kinds"]), "zoom-in / zoom-out / pan, no cuts", ""))
    L.append(row("zoom-in step", f"{prof['zoom_in_ratio']['median']}x", "1.5x from wide, 1.3 to 1.7x again for tight", ""))
    L.append(row("zoom-out step", f"{prof['zoom_out_ratio']['median']}x", "back to wide (0.67x from 1.5x)", ""))
    L.append(row("common sequences", str(prof["move_sequences"]), "in > out > in", ""))
    L.append(row("where the zoom lands", str(prof["focus_cells_when_zoomed"]), "wherever the named thing is", ""))
    L.append("")
    if analysis_dir:
        s = ink_stats(analysis_dir)
        L.append("## Does the zoom follow the red ink?\n")
        if s["zoomed_holds"]:
            L.append(f"- Zoomed holds with Matt's red ink inside the window: {s['zoomed_with_ink']} of {s['zoomed_holds']} ({round(s['zoomed_with_ink'] / s['zoomed_holds'], 2)})")
        if s["wide_holds"]:
            L.append(f"- Wide holds with red ink on screen (Claude's rules would zoom on these): {s['wide_with_ink']} of {s['wide_holds']} ({round(s['wide_with_ink'] / s['wide_holds'], 2)})")
        L.append(f"- When ink is inside a zoomed hold, its centre sits a median {s['ink_offcentre_median']} of the window away from centre (0 = dead centre, 0.5 = at the edge)")
        L.append("")
    print("\n".join(L))


if __name__ == "__main__":
    main()
