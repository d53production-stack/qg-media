# Zoom style notes (working log)

Goal: learn where Matt zooms in his webinar highlight edits and how (level,
timing, hold, cut vs ramp), then compare with the zoom plan Claude would make
on its own for the same material.

## What we have to work with (2026-10-30)

- No edit files in the repo (no Premiere/Resolve XML, EDL or keyframes), only
  the rendered 1080x1920 verticals that Buffer fetches.
- 96 `YYYY-MM-DD-webinar-partN.mp4` clips from 11 webinars (Oct 7 to Oct 28)
  plus the `2026-10-2x-halloween-*.mp4` clips, 30 fps, 27 to 60 s each.
- Layout of every clip: title band, a video window (about y 605 to 1385) that
  carries a crop of the webinar screen share, burned-in captions, CTA. The
  zoom and pan live inside the window only.
- Source webinar recordings are not in the repo. The Highlight Studio fixture
  names the upload `10-29-26 Webinar Highlights DRY.mp4`, so the raw cut
  exists on Matt's side.

## Method

`analyze_zoom.py` works from the rendered frames:

1. video window = the band of rows whose pixels change over the clip;
2. sample the window at 10 fps, ORB features, similarity transform between
   consecutive samples (scale + translation);
3. cut = big pixel jump or a transform jump; ramp = log-scale drift inside a
   shot;
4. zoom of each shot = 1 / scale of its keyframe matched into the clip's
   widest shot (most features = smallest text = widest view), and the
   position of the shot inside that wide frame.

`profile.py` aggregates the per-clip JSON into a style profile.

## Status

- [x] survey
- [x] analyzer and profile scripts written
- [x] run over all webinar clips (97 after dropping the pt1-3 aliases), eyeball sheets, fix thresholds
- [x] results/PROFILE.md (Matt's style), results/profile.json, results/matt-zoom-style.json
- [x] CLAUDE-DEFAULT-STYLE.md + results/COMPARISON.md
- [x] results/focus-map.jpg (heat map: SPX and SPY chart panels)
- [ ] absolute zoom against a raw recording (needs a DRY file from Matt)
- [ ] transcript timing: what word triggers each zoom (needs captions or audio)

## Findings (2026-10-30)

- Pace: 9.4 moves/min, holds 3.8 s median (zoomed 3.4 s, wide 4.7 s), 46 % of time zoomed.
- Level: 1.55x median when zoomed (middle half 1.44 to 1.66), tightest 2.3x; almost never 2x+.
- Moves: 0.2 to 0.3 s ramps since Oct 8 (Oct 7 used 0.55 s); cuts are rare (15 of 620).
- Pattern: in > out > in; pans at the same zoom (119) are common, stacked zoom-ins (20) are not.
- 33 % of clips open already zoomed; first zoom at 3.0 s median otherwise.
- Where: SPX and SPY chart panels in the middle of the dashboard; the ladder and QQQ rarely.
- Ink: 88 % of zoomed holds have Matt's red ink inside, a median 0.14 off centre; 44 % of wide holds also show ink he did not zoom on.
