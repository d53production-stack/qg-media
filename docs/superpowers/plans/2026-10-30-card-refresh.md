# Card Refresh Buttons + Studio Version Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A REFRESH button on the Recap Mac and Studios cards of the live QG Command Center that starts the hourly copy run on demand, plus the intake fix that lets the studio sweep write at all.

**Architecture:** The page already fires scheduled tasks through the `Claude Code Remote` connector (`fire_trigger` is in its stored mcp manifest; BRIEF NOW and the week planner use it). REFRESH fires the hourly copy task `trig_01NU7aWKpkA7LmF3mh6tbz9N` bare (it starts a fresh thread per run, and those refuse added text). The card watches its own evidence field and only shows the refresh as done when that field moves. Separately, `intake.py` stops depending on a version field that ArtifactData `out_dir` files never contain.

**Tech Stack:** Single-file HTML page (vanilla JS), Node for page-logic tests, Python 3 stdlib + unittest for intake.py, Playwright for screenshots.

**Spec:** the design Matt approved in the thread "Add refresh buttons to Command Center cards" on 2026-10-30 (option "Both: refresh + Studios fix").

## Global Constraints

- Status words are only confirmed, pending, failed, unknown. A refresh that brings no new evidence must never show anything as confirmed.
- The live page (https://claude.ai/artifact/MC7jzykFQzwWp16rzA65QA) and the two scheduled tasks change only after Matt says go. Build the page as a preview copy; snapshot the live version before publishing.
- Brand: dark only, square corners, Bebas Neue + JetBrains Mono, no emoji, existing `.btn` look.
- Never touch the MacBook Air.

## Review Focus

- Pressing REFRESH while the :58 cron run is already going: both runs write with if_version, one may conflict; the card still confirms when the field moves.
- The Air is asleep or offline: lastSeen never moves, so after 5 min the card says NO NEW REPORT (failed), never CHECKED.
- The connector is not approved or not available in this view: the press shows the reason and the card returns to idle; no pending state lingers.
- Tapping twice quickly: the second tap does nothing while a refresh is pending.
- One run refreshes both cards, so pressing either card's button puts both into CHECKING.

---

### Task 1: intake.py reads versions from `cc/versions.json` and refuses unpinned writes

**Root cause:** ArtifactData `out_dir` files hold the bare document data, with no `id` or `version`. `unwrap()` returns version None, so writes to existing docs carry no `if_version` and the hourly run refuses them (run of 2026-10-30 19:58Z: "writes came back without the version pins"). The tests used a wrapped fixture format that the tool never produces.

**Files:**
- Modify: `command-center/studios/intake.py` (`load_cc`, `main`)
- Test: `command-center/studios/test_intake.py`

**Interfaces:**
- Produces: `load_cc(cc_dir, studio)` merges `<cc_dir>/versions.json` (`{"studio/highlight": 2, "days/2026-10-30": 5, ...}`) into `cc.versions`, overriding versions found in files. `main()` exits 2 with `missing version for <collection>/<doc_id>` on stderr when a write targets a doc whose file exists under `cc_dir` but has no known version.

- [ ] Step 1: Tests (fail first): `test_versions_file_pins_bare_docs` (bare studio/factory.json + versions.json `{"studio/factory": 7}` → studio write has `if_version` 7); `test_versions_file_pins_days` (bare days/2026-10-29.json + versions.json → days write pinned); `test_bare_doc_without_version_fails_loudly` (bare studio file, no versions.json → exit 2, stderr names `studio/factory`); `test_new_doc_needs_no_version` (no studio file at all → exit 0, write has no if_version).
- [ ] Step 2: Run `python3 -m unittest test_intake` → the four new tests fail.
- [ ] Step 3: Implement in `load_cc` and a `_check_pins(writes, cc_dir, cc)` called from `main`.
- [ ] Step 4: Run `python3 -m unittest test_intake` → all pass.
- [ ] Step 5: Commit.

### Task 2: Draft the prompt lines for the two scheduled tasks (not applied)

**Files:**
- Create: `command-center/studios/versions-prompt-change.md` (exact old/new text for the hourly copy step 5b and the job-done task step 2)

New instruction for both: after the Command Center reads, write `./cc/versions.json` with one python3 command mapping `"<collection>/<doc_id>"` to the `version` each ArtifactData result printed, for the studio doc(s) and the days doc(s) read; then run the script as before. If the script exits 2, skip that studio and say so in the one-line reply.

- [ ] Step 1: Write the file with verbatim old and new prompt fragments.
- [ ] Step 2: Dry-run: read the real CC docs with out_dir, write versions.json by hand, run `intake.py sweep` for all four studios; every studio write must carry if_version. Do not apply the writes.
- [ ] Step 3: Commit.

### Task 3: Page refresh logic (pure, tested)

**Files:**
- Test: `command-center/refresh/refresh.test.js` (runs the page's `/* refresh-logic:start */ … /* refresh-logic:end */` block, like `studios.test.js`)

**Interfaces:**
- Produces: `REFRESH_WAIT_MS = 5*60e3`; `refreshState(req, mark, nowMs)` → `"idle" | "pending" | "confirmed" | "failed"`, where `req` is `null` or `{at: ms, mark: iso|null, err: string|null}` and `mark` is the card's evidence now (Air: `status/air.lastSeen`; Studios: newest `studio/*.checkedAt`). `airMark(doc)` and `studioMark(docsMap)` return those isos.

Rules: null req → idle; req.err → failed; `Date.parse(mark) > Date.parse(req.mark||0)` → confirmed; else `nowMs - req.at < REFRESH_WAIT_MS` → pending; else failed.

- [ ] Step 1: Tests: idle with no request; pending right after press; confirmed only when the mark moves past the pre-press mark; same mark after 5 min → failed (never confirmed); fire error → failed; missing doc before press then doc appears → confirmed; studioMark picks the newest checkedAt and ignores missing docs.
- [ ] Step 2: Run `node refresh.test.js <page>` → fails (block missing).
- [ ] Step 3: Add the block to the preview page (Task 4's patch).
- [ ] Step 4: Run → all pass.

### Task 4: Preview page with REFRESH buttons

**Files:**
- Create: `command-center/refresh/patch.py` (exact-match edits over the live source, fails if the live page changed), output `qg-command-center-refresh.html`
- Create: `command-center/refresh/shoot.js` (screenshots: idle, checking, checked, no new report; desktop and phone)

Behavior: `COPY_TRIGGER = "trig_01NU7aWKpkA7LmF3mh6tbz9N"`. One shared request `S.refresh = {at, air: {mark}, studios: {mark}, err}` (memory only). Pressing either button: if pending, ignore; else record marks, `LIVE.mcp.callTool("Claude Code Remote","fire_trigger",{trigger_id: COPY_TRIGGER})`; on reject set `err` to the WEEK_WHY reason and toast it. A 15 s timer re-renders while pending. Header button text: REFRESH / CHECKING (disabled) ; header "when" text on failed: `NO NEW REPORT · TAP TO TRY AGAIN` in rose; confirmed clears that card's part of the request and toasts "Recap Mac updated" / "Studios updated". Hidden when `LIVE.mcp` is null.

- [ ] Step 1: Write patch.py; build the preview from the live source.
- [ ] Step 2: Run refresh.test.js and the existing studios.test.js against the preview → pass.
- [ ] Step 3: shoot.js with a window.claude shim that resolves fire_trigger and later updates the doc; capture the four states on desktop (1280) and phone (390); check no console errors.
- [ ] Step 4: Commit; copy preview + screenshots to /mnt/project-files/command-center/refresh/.

### Task 5: Go-live (only after Matt says go)

- [ ] Merge the PR (intake.py on main, which both tasks curl).
- [ ] update_trigger the hourly copy prompt and the job-done prompt with Task 2's text.
- [ ] Save the live page to `/mnt/project-files/command-center/refresh/before-<version>.html`, re-run patch.py on the then-current live source, publish.
- [ ] Verify: press REFRESH once on the live page (or fire the task), confirm studio/* checkedAt and status/air move and the cards read CHECKED.
