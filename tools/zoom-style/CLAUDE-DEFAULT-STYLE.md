# The zoom style Claude would use on its own

These are the rules Claude would apply if handed a raw webinar highlight
and asked to cut a vertical with zooms, with no examples of Matt's edits
to copy. Written down on 2026-10-30 while the full measurement was still
running; a first partial read of 22 clips had been seen, so treat the
numbers here as Claude's defaults, not a blind guess.

## Triggers (when to move)

1. Open wide for the first sentence, so the viewer sees the whole dashboard
   once (1.5 to 3 s), then zoom to the first thing the speaker names.
2. Zoom in when the speech names a specific thing that is on screen: a
   ticker (SPY, QQQ, SPX), a level ("7,700", "717"), a label ("M2", "flip",
   "primary", "trap door"), or when the cursor parks or the presenter draws
   on the screen.
3. Zoom out (to wide) when the speaker generalises ("so overall", "the
   point is"), changes ticker, or when nothing on screen is being referred
   to for more than ~4 s.
4. Pan rather than zoom out and in again when the next target is adjacent
   and at the same scale (for example SPX chart to SPY chart).

## Levels (how tight)

- Wide = the full dashboard crop that fills the window.
- Standard zoom = 1.5x: one chart panel (or the ladder) fills the window.
- Tight zoom = 2.0 to 2.5x: one price level, one circle of ink, one label.
- Never tighter than 2.5x on a dashboard; text aliasing gets ugly.

## Holds (how long)

- Minimum hold 2 s, target 4 to 6 s, never more than 10 s at the same zoom
  unless the speaker is still on the same point.
- Return to wide at least once every 15 s.

## Moves (how)

- Animated ease-in-out zoom, 0.4 to 0.6 s. Hard cuts only when the source
  itself cuts.
- Centre the target in the window; leave 10 % padding around a circle of
  ink or a label.

## Pace

- About 8 to 12 moves per minute on a talking-head-over-dashboard clip.
- Roughly 50 to 60 % of the running time zoomed in.
