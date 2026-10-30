#!/usr/bin/env python3
"""Boil the measured profile down to a style spec an auto-editor can follow.

    python3 make_spec.py profile.json > matt-zoom-style.json
"""
import json
import sys


def main():
    p = json.load(open(sys.argv[1]))
    z = p["zoom_level_when_zoomed"]
    spec = {
        "name": "matt-webinar-highlights",
        "measured_from": {"clips": p["clips"], "minutes": p["total_minutes"]},
        "frame": "1080x1920 vertical, video window y 610 to 1400, crop of the dashboard screen share",
        "open": {
            "wide_first_share": round(1 - (p["opens_zoomed_share"] or 0), 2),
            "first_zoom_after_s": p["first_zoom_s"]["median"],
        },
        "levels": {
            "wide": 1.0,
            "standard_zoom": z["median"],
            "standard_zoom_range": [z["p25"], z["p75"]],
            "tight_zoom_max": z["max"],
            "histogram": p["zoom_histogram"],
        },
        "holds_s": {
            "zoomed": p["zoomed_hold_dur_s"],
            "wide": p["wide_hold_dur_s"],
            "any_p90": p["hold_dur_s"]["p90"],
        },
        "moves": {
            "per_minute": p["moves_per_min"],
            "ramp_s": p["ramp_dur_s"],
            "kinds": p["move_kinds"],
            "zoom_in_step": p["zoom_in_ratio"],
            "zoom_out_step": p["zoom_out_ratio"],
            "common_sequences": p["move_sequences"],
        },
        "zoomed_share_of_time": p["zoomed_share_of_time"],
        "focus_cells": p["focus_cells_when_zoomed"],
    }
    print(json.dumps(spec, indent=1))


if __name__ == "__main__":
    main()
