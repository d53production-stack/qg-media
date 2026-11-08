# Chart Clips: monitor + Command Center section

Date: 2026-11-08. Asked by Matt. Status: monitor BUILT (new artifact); Command Center section PLANNED, preview only, waiting for Matt's OK.

## What Matt asked for
1. A place to watch and check the evening highlight clips from QG Auto Chart Clipper (SPX, SPY and QQQ), like the studios. Creation and scheduling stay fully automatic; the page only observes.
2. A Command Center section showing clip creation progress and Buffer status, filterable by ticker.

Status words everywhere: confirmed, pending, failed, unknown. Confirmed needs evidence.

## 1. Clip Monitor (built)
Artifact: https://claude.ai/artifact/W6Tu8vrSJ5JD6SSa8bCfgd (source `command-center/chart-clips/`, `./build.sh` inlines `clipstatus.js` into `clip-monitor.html`).

- Reads Buffer live, read-only (`Buffer.list_posts`, re-read every 15 min or on REFRESH). A clip = any Buffer post due 6:00-9:30 PM ET on a weekday; the regular top-up never schedules there (pacing blackout), so the window belongs to the clipper.
- Groups one clip's TikTok / Instagram / YouTube posts by caption (or by Buffer post id when the clipper reports them).
- Day strip (today + 5 weekdays back), ticker filter ALL / SPX / SPY / QQQ.
- Summary band: CREATED, then TIKTOK / INSTAGRAM / YOUTUBE as n of 5 with one pip per clip.
- Per clip: time, tickers, caption, each channel's word + Buffer post id + WATCH link (opens the video Buffer holds; the page can't play outside video inline).
- Player (added 2026-11-08 08:3xZ, Matt: human quality control of each render): 9:16 player above the list, PREV/NEXT, "play the next clip when one ends", GOOD/FLAG beside it. Each row has PLAY + VIDEO / NO VIDEO tag. The page can only play videos from its own asset store (artifact CSP blocks outside video), so a render plays when `runs/<day>.clips[].assetId` is set (clipper uploads it: Artifact publish `asset: true` to the monitor URL, verified 2026-11-08, then writes the id). Without it: WATCH IN NEW TAB (Buffer's copy) or ADD THE VIDEO FILE (editor upload, stored as `reviews/<key>.assetId`). Asset limit 20 MB per file; delete renders older than ~5 days to stay under the quota.
- Check per clip: GOOD or FLAG + note, saved in the monitor's db `reviews/<day>_<clipId>` {verdict, note, at, by, posts}. Checks never touch Buffer or the clipper.

### Status rules (`clipstatus.js`, 14 tests in `clipstatus.test.js`)
| Thing | confirmed | pending | failed | unknown |
|---|---|---|---|---|
| Channel post | Buffer says sent (has post id) | scheduled / sending | Buffer error, or a made clip never reached Buffer by 9:30 PM ET | Buffer not read, no post id, odd status |
| Channel summary | all its clips sent | any queued, or window still open | any failed | Buffer not read; nothing at all after the window |
| Created | run doc `done` with clips | run doc `queued`/`working`, updated in last 3 h | run doc `failed`, or `done` with 0 clips | no run doc, or stale |

### Report contract for the clipper (open question)
CREATED stays unknown until the clipper reports. Proposed: after each step the Chart Clipper job writes the monitor's db `runs/<YYYY-MM-DD>` (ET day):
```
{status: "queued"|"working"|"done"|"failed", updatedAt, message,
 clips: [{id, ticker, title, caption, assetId (render uploaded to the monitor), url?, seconds?, createdAt, posts: {tiktok, instagram, youtube: <Buffer post id>}}]}
```
Needs: where the clipper runs and saves its clips (unknown tonight), and a one-step change to its job. That job is in a separate project, so it is a "live tool" change and needs Matt's OK.

## 2. Command Center section (plan, preview only)
Modeled on the Studios / Recap Mac cards (I could not find a "Chart Map X posting" section in the live Command Center; Matt to point me to it if it's elsewhere).

**CHART CLIPS card on Today**, under Studios:
- Header: "Chart clips · tonight" (or the last weekday), "· needs a look" in rose when anything failed. Ticker filter ALL/SPX/SPY/QQQ (remembered per device).
- Four cells: CREATED (count + word + clipper message), TIKTOK / INSTAGRAM / YOUTUBE (n/5, 5 pips, word, "3 posted · 1 queued").
- Footer: "WATCH & CHECK" link to the monitor.
- Left stripe: green normal, rose on any failed, grey when everything is unknown.

**Data, no new permissions:**
- Buffer part reuses the Buffer posts the Command Center already loads (`LIVE.buffer.posts`, 2-week window). No extra connector call.
- Creation part reads Command Center db `clips/<day>` (same shape as the monitor's `runs/<day>`). Writer: the hourly copy (or the clipper's job directly) copies the monitor's run doc across, like `studio/*` today.
- Same `clipstatus.js` rules, so the card and the monitor always agree.

**Steps once Matt OKs:**
1. Merge the card into the live page source (read live first, patch, republish) — `cc-preview/patch.py` does it on a copy.
2. Add the `clips/<day>` copy to the hourly copy prompt (or have the clipper write both pages).
3. Optional: a "Chart clips" row in Automations with a daily dot (confirmed when all 3 channels got their clips).

Preview: `command-center/chart-clips/cc-preview/qg-command-center-clips.html` + `shots/` (ok, failed, Buffer-down; desktop + phone).
