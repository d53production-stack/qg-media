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
- [ ] run over all webinar clips, eyeball the shot sheets, fix thresholds
- [ ] write PROFILE.md (Matt's style)
- [ ] Claude's own zoom rules + side-by-side comparison
