# Studio Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One tested Python script turns raw studio docs into Command Center batch writes (job status, finished videos, task check-ins), so the four studios report in without Matt relaying anything.

**Architecture:** `intake.py` is a pure function from (raw studio docs, current Command Center docs, now) to a list of ArtifactData writes. `job` mode handles one job at the end of a worker run; `sweep` mode handles a directory of changed docs for the hourly copy. Both share one status function and one merge rule. The page changes (STUDIOS card, chips, Automations rows) come in step 2 as a preview copy and are not in this plan's tasks.

**Tech Stack:** Python 3.13 standard library only (`json`, `datetime`, `zoneinfo`, `unittest`). No network.

**Spec:** `docs/superpowers/specs/2026-10-30-studio-intake-design.md`

## Global Constraints

- Status words are only `confirmed`, `pending`, `failed`, `unknown`.
- The script never calls the network and never writes to a database. It prints a JSON list of writes.
- Writes are add-only for `content/{id}` and never change an existing `days/{date}.done[task]` entry.
- A job entry is replaced only when its `updatedAt` is newer than the stored one. Keep the 10 newest jobs by `updatedAt`.
- Highlight outputs with `short.date` before `2026-10-14` are never added as content.
- Only jobs with `endedAt >= settings/studios.since` make content items and check-ins.
- Every write to an existing doc carries `if_version` from the doc as read.

## Decisions the spec left open (made here, flagged to Matt in the PR)

- Highlight jobs with `task: "clear"` (housekeeping, no videos) are skipped entirely, not shown as `unknown`.
- Publishing Desk "jobs" are: every weekly proposal (id `week-<week>`), plus every video with at least one platform status outside SCHEDULED/READY (id = video id). Videos that are only scheduled stay out, because the Desk has hundreds of them and they are already content.
- Desk docs carry no `updatedAt`; the script uses the proposal's `applied_at` / `decided_at` / `created`, and for a video the newest `schedule[].set`, falling back to `now`. The 6-hour stale rule does not apply to Desk `pending` (a PREVIEW proposal legitimately waits on Matt for days).
- `endedAt`: Factory `builtAt`; Highlight and Style `updatedAt` when status is done or failed. `startedAt`: `queuedAt`, else `createdAt`.
- Content items carry both the spec's `type: "video"` and the page's existing fields (`kind: "video"`, `channels: []`, `media: [{file: path, alt: title}]`, `createdAt`), so the Content tab renders them today.
- Write shapes: `studio/{name}` and `days/{date}` are emitted as full-document `set` writes (the script holds the merged result), so the merge rule is tested in Python rather than relying on server merge depth. `content/{id}` is a `set` with no `if_version` (create only). `checkedAt` is bumped on the studio doc in the same write.

## Review Focus

1. A raw doc that is not a dict, or has `outputs` as a non-list, must become one `unknown` job with `message: "unreadable job"` and never raise. (Task 3)
2. A `since` that is missing or empty must mean "no content items and no check-ins", never a crash or a flood. (Task 4)
3. A check-in date must use the PT calendar day of `endedAt`, including a UTC time after 4 PM PT that falls on the next UTC day. (Task 5)
4. A job whose stored `updatedAt` equals the incoming one must not be rewritten (so a worker and the hourly copy do not flip-flop `by`). (Task 3)
5. A sweep directory with zero files must still produce a `checkedAt` bump and nothing else. (Task 6)

---

### Task 1: status() and the Desk rules

**Files:**
- Create: `command-center/studios/intake.py`
- Test: `command-center/studios/test_intake.py`

**Interfaces:**
- Produces: `status(raw: str|None, videos: int, updated_at: str|None, now: datetime, studio: str) -> str`; `desk_video_status(status_map: dict) -> str`; `desk_proposal_status(raw: str|None) -> str`; `STALE_PENDING = timedelta(hours=6)`.

- [ ] **Step 1: Write failing tests** `TestStatus` with one test per row: queued/working/running/building → pending; done with 1 video → confirmed; done with 0 videos and studio factory → unknown; done with 0 videos and studio style → confirmed; ready → confirmed; failed and error → failed; None and "weird" → unknown; pending with updatedAt 7h before now → unknown, 5h → pending. `TestDesk`: {ig: FAILED, shorts: PUBLISHED} → failed; all PUBLISHED → confirmed; mix of SCHEDULED/PUBLISHED → pending; empty map → unknown; PREVIEW → pending; APPROVED and APPLIED → confirmed; "SENT BACK" → failed; None → unknown.
- [ ] **Step 2: Run** `python3 -m unittest command-center/studios/test_intake.py -v` → ImportError / AttributeError.
- [ ] **Step 3: Implement** the three functions in `intake.py`. Raw values compare case-insensitively after strip. `updated_at` parsing: ISO 8601, `Z` allowed, naive treated as UTC.
- [ ] **Step 4: Run tests** → all pass.
- [ ] **Step 5: Commit** `feat(studios): status rules for intake`.

### Task 2: normalize one raw job per studio

**Files:** `intake.py`, `test_intake.py`, fixtures in `command-center/studios/fixtures/` (cut from the docs read 2026-10-30: `highlight-2026-10-29-0ww4.json` trimmed to 2 outputs, `highlight-clear.json`, `factory-2026-10-29-redo-howlive.json`, `style-rmvoi1xo6.json`, `desk-video-cc-04a.json`, `desk-proposal-2026-W44.json` trimmed).

**Interfaces:**
- Produces: `normalize(studio: str, job_id: str, raw: dict, now: datetime) -> dict|None` returning the spec's job entry (`title, status, raw, step, startedAt, endedAt, updatedAt, videos, message`) without `by`; `None` means skip (Highlight clear jobs; Desk videos that are only scheduled). `outputs(studio, job_id, raw) -> list[dict]` returning content candidates: `{id, title, path, poster, seconds, orientation, clipDate, text, textByChannel}`.
- `STUDIOS = {"highlight": {...label, url, collection}, "factory": ..., "style": ..., "desk": ...}`.

- [ ] **Step 1: Tests** per fixture: Highlight → status confirmed, videos 11, endedAt == updatedAt, startedAt == queuedAt; clear fixture → None; Factory → videos 2, endedAt == builtAt, title "Redo: How Live Is the Console? (overnight)"; Style → confirmed, videos 0, step "Saved as v006"; Desk video all SCHEDULED → None, same video with ig FAILED → failed, updatedAt == newest `schedule[].set`; proposal APPROVED → confirmed, title "Week 2026-W44", updatedAt == applied_at. `outputs`: Factory gives ids `vf-cc-how-live-v` and `vf-cc-how-live-h` with orientation from `o`, text = copy.instagram, textByChannel {youtube: copy.description, instagram: copy.instagram, tiktok: copy.tiktok}; Highlight gives `hs-2026-10-29-webinar-part1`, text = short.title, clipDate "2026-10-29"; Style and Desk give [].
- [ ] **Step 2: Run** → fail.
- [ ] **Step 3: Implement** `normalize` and `outputs`.
- [ ] **Step 4: Run** → pass. **Step 5: Commit** `feat(studios): normalize raw studio jobs`.

### Task 3: merge jobs into the studio doc

**Interfaces:**
- Produces: `merge_jobs(current: dict|None, incoming: dict[str, dict], by: str, now: datetime) -> dict` returning the new `studio/{name}` data (`studio, label, url, checkedAt, checkedBy, jobs`). `KEEP_JOBS = 10`.

- [ ] **Step 1: Tests**: newer `updatedAt` replaces and sets `by`; equal `updatedAt` leaves the stored entry untouched (Review Focus 4); older is ignored; 12 jobs → the 10 newest remain; `None` current builds the doc from `STUDIOS`; `checkedAt == now`, `checkedBy == by`; a malformed raw (a string, or `outputs: 5`) passed through `normalize` gives `{status: "unknown", message: "unreadable job"}` (Review Focus 1, implemented as `safe_normalize`).
- [ ] **Step 2–5:** run, implement, run, commit `feat(studios): merge job entries`.

### Task 4: content items (add-only, since, Oct 14 skip)

**Interfaces:**
- Produces: `content_writes(studio: str, job_id: str, job: dict, candidates: list, existing_ids: set[str], since: str|None) -> list[dict]` → `[{op: "set", collection: "content", doc_id, data}]`. `MIN_CLIP_DATE = "2026-10-14"`.

- [ ] **Step 1: Tests**: confirmed Factory job after `since` → 2 writes with spec fields plus `kind "video"`, `channels []`, `media [{file, alt}]`, `status "ready"`, `by "studio"`, `at == endedAt`; id already in `existing_ids` → skipped; job pending → []; job `endedAt` before `since` → []; `since` None or "" → [] (Review Focus 2); Highlight output clipDate "2026-10-12" → skipped, "2026-10-14" → kept.
- [ ] **Step 2–5:** run, implement, run, commit `feat(studios): add-only content items`.

### Task 5: task-map check-ins

**Interfaces:**
- Produces: `checkin_write(studio, job, task_map: dict, tasks: dict[str, dict], day_doc: dict|None, videos: int) -> dict|None` → a `set` on `days/{YYYY-MM-DD}` (PT date of `endedAt`) with the merged `done`, or None. `pt_date(iso: str) -> str`.

- [ ] **Step 1: Tests**: `pt_date("2026-10-30T02:00:00Z") == "2026-10-29"` (Review Focus 3); confirmed factory job with map `{factory: "content.evergreen"}` and task doc carrying `target` → entry `{at: endedAt, by: "studio", note: "Video Factory · <title>", link: url, count: videos}`; task without `target` → no `count`; existing `done[task]` → None; studio not in map → None; pending job → None; `day_doc` None → data has `date` and only this entry.
- [ ] **Step 2–5:** run, implement, run, commit `feat(studios): task-map check-ins`.

### Task 6: CLI (`job` and `sweep`) and the writes list

**Interfaces:**
- `python3 intake.py job <studio> <job.json> --cc <cc_dir> [--now ISO] [--by worker]`
- `python3 intake.py sweep <studio> <raw_dir> --cc <cc_dir> [--now ISO]` (`by` = hourly)
- `<cc_dir>` holds the Command Center docs as ArtifactData `out_dir` writes them: `studio/<name>.json`, `settings/studios.json`, `tasks/<id>.json`, `days/<date>.json`, `content/<id>.json` (only ids are read). Missing files mean "no doc".
- Each raw file may be the ArtifactData wrapper `{id, data, version}` or the bare data; `unwrap(obj, fallback_id) -> (id, data, version)`.
- Output: JSON list of writes to stdout, each `{op, collection, doc_id, data, if_version?}`; `if_version` only when the read doc carried a version. Exactly one `studio/<name>` write per run (Review Focus 5: empty dir → that one write only).
- Produces: `run(studio, raw_docs: dict[str, dict], cc: CCDocs, now, by) -> list[dict]`.

- [ ] **Step 1: Tests**: `run` with the Factory fixture, empty cc → writes for studio/factory (no if_version), 2 content, 1 days; with cc carrying `studio/factory` version 7 → that write has `if_version 7`; with existing content ids → no content writes; empty raw_docs → exactly one write. CLI smoke test via `subprocess` on the fixtures: exit 0 and valid JSON.
- [ ] **Step 2–5:** run, implement (`argparse`, `main()`), run, commit `feat(studios): intake CLI`.

### Task 7: README and runbook paragraph

- [ ] Write `command-center/studios/README.md`: what the script is, the two commands, the cc_dir layout, the ArtifactData calls around it (query with `out_dir`, then one `batch` from the output file), the open decisions above, and the rollout order with "ask Matt first" on steps 3-5.
- [ ] Commit `docs(studios): intake README`, run the whole suite once more, push, open the PR.
