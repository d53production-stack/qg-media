# zoom-style: learn Matt's zoom moves from the highlight clips

There are no edit files for the webinar highlights, only the rendered
1080x1920 verticals. These scripts read the zoom back out of the frames.

```bash
pip install opencv-python-headless numpy

# 1. per clip: holds, moves, zoom level, position (JSON + a contact sheet)
python3 analyze_zoom.py 2026-10-28-webinar-part*.mp4 --out results/analysis

# 2. red-ink cue per hold (Matt's live annotations)
for j in results/analysis/*.json; do python3 cues.py "$(basename "$j" .json).mp4" "$j"; done

# 3. aggregate
python3 profile.py results/analysis > results/profile.json
python3 profile.py results/analysis --md > results/PROFILE.md
python3 compare.py results/profile.json results/analysis > results/COMPARISON.md
python3 make_spec.py results/profile.json > results/matt-zoom-style.json
python3 focus_map.py results/analysis wide-frame.jpg results/focus-map.jpg
```

Terms: a **hold** is a stretch where the video window sits still. A
**move** is what happens between two holds: a hard **cut**, or a short
animated **ramp** (zoom-in, zoom-out, pan). **Zoom** is relative to the
widest hold of the same clip (1.0x = the widest view that clip shows), so
it does not need the raw webinar recording. The template's 0.5 s logo
slide-in, the 3.6 s pull-back and the end card are detected and excluded.

Limits: zoom is relative, not absolute, until a raw recording is available
to match against. Positions are in the coordinates of each clip's widest
frame, and the dashboards differ a little day to day. Holds shorter than
0.3 s are folded into the move around them.

`CLAUDE-DEFAULT-STYLE.md` holds the rules Claude would use on its own;
`compare.py` lays the two side by side. `NOTES.md` is the working log.
