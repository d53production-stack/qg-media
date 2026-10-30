# Studio intake for the QG Command Center (v3, studio half)

Date: 2026-10-30. Task: `command-center.v3`, studio intake. Design approved by Matt in the project thread on 2026-10-30.

## Goal

The QG studios report into the Command Center without Matt relaying anything. Two kinds of report:

1. **Job status**: each studio job shows as pending, confirmed, failed or unknown. A confirmed job can check off a mapped task, with evidence.
2. **Finished videos**: each video a job produces becomes a Command Center content item with status `ready`, so it can be scheduled.

Success means that when a studio finishes, fails or stalls, the Command Center shows it within an hour or less, using only the four status words. Matt gets a nudge only when a job has failed.

## Decisions already made (Matt, 2026-10-30)

- The studios send **both** job status and finished videos.
- **Both writers**: each studio's worker reports when a job ends, and the hourly copy fills in anything the workers missed.
- In scope: Highlight Studio, Video Factory, Style Studio and Publishing Desk. Copy Studio and Promo Studio come in a second pass, using the same shape.
- Out of scope: Calendar import, the month view and the brief gap line.

## Constraints

- Never overwrite Matt's artifacts. The studios keep their own databases and pages. Only their workers' prompts gain one extra step.
- Ask before changing any studio or live tool. That means each of the four worker prompts, the hourly copy and the live Command Center, each with its own OK.
- Data feeds are plain data with fixed rules. The only Claude that moves data is the hourly copy, plus the step added to each studio's own worker, which is a Claude run that already exists. Every mapping rule lives in one tested script, not in a prompt.
- The status words are only `confirmed`, `pending`, `failed` and `unknown`.
- Each artifact has its own database, and the Command Center page cannot read a studio's database. Data crosses only through a writer.

## Sources (read 2026-10-30)

| Studio | Artifact | Collection | Raw status values |
|---|---|---|---|
| Highlight Studio | 9pKYhvbeaxpwwDyhQswHvi | `jobs/{id}` | status, step, outputs[] (part and full clips: path, poster, seconds, short.title, short.date) |
| Video Factory | Q9r9A3GK8dhbKB5jKb2p2g | `batches/{id}` | status, step, queuedAt, builtAt, outputs[] (o v or h, path, poster, seconds, copy.title, description, instagram, tags) |
| Style Studio | AmAqmKFatXwLoTUiE29iTU | `requests/{id}` | status queued, working, done or failed, step, message. It makes styles, not videos, so it gives status only. |
| Publishing Desk | Y876Yu3rcP3g4hX6oSfcKz | `videos/{id}`, `proposals/{week}` | per platform: SCHEDULED, READY, PUBLISHING, PUBLISHED, FAILED or CANCELLED. Weekly proposal: PREVIEW, APPROVED, SENT BACK or APPLIED. It gives status only, because its videos are already scheduled content. |

## Data in the Command Center database

### `studio/{name}`: one doc per studio (`highlight`, `factory`, `style`, `desk`)

```json
{
  "studio": "factory",
  "label": "Video Factory",
  "url": "https://claude.ai/artifact/Q9r9A3GK8dhbKB5jKb2p2g",
  "checkedAt": "2026-10-30T15:58:00Z",
  "checkedBy": "hourly",
  "jobs": {
    "2026-10-17-gabj": {
      "title": "Batch of Oct 17",
      "status": "confirmed",
      "raw": "done",
      "step": "Ready",
      "startedAt": "2026-10-19T04:50:49Z",
      "endedAt": "2026-10-19T05:12:31Z",
      "updatedAt": "2026-10-19T05:12:59Z",
      "videos": 10,
      "message": "",
      "by": "worker"
    }
  }
}
```

- `jobs` is a map keyed by job id, so both writers merge by id. A writer replaces a job entry only when its `updatedAt` is newer than the stored one.
- A writer keeps only the 10 newest jobs by `updatedAt` and drops older entries.
- `checkedAt` is the last time any writer looked at this studio, whether or not anything changed.

### `content/{id}`: one item per finished video

The item uses the Content tab's existing fields, plus a `studio` block:

```json
{
  "id": "vf-rtb-s1-positive-v",
  "title": "The Positive Node | Reading the Board",
  "type": "video",
  "status": "ready",
  "text": "<instagram caption>",
  "textByChannel": { "youtube": "<description>", "instagram": "<instagram>" },
  "sourceArtifact": "https://claude.ai/artifact/Q9r9A3GK8dhbKB5jKb2p2g",
  "studio": {
    "name": "factory",
    "job": "2026-10-17-gabj",
    "path": "build/factory/out/2026-10-17-gabj/The Positive Node | Reading the Board.mp4",
    "poster": "...jpg",
    "seconds": 31.6,
    "orientation": "v",
    "clipDate": null
  },
  "by": "studio",
  "at": "2026-10-19T05:12:31Z"
}
```

- Ids: Video Factory is `vf-<output name>` (for example `vf-rtb-s1-positive-v`). Highlight Studio is `hs-<output name>` (for example `hs-2026-10-12-webinar-part1`).
- **Add only**: an item is written only if `content/{id}` does not exist yet. A writer never changes an item that is already there, because Matt or Buffer may have moved it on.
- **Skip old clips**: a Highlight output whose `short.date` is before 2026-10-14 is never added. This follows Matt's rule from 2026-10-26.
- Only videos from a job whose status is `confirmed` become items.
- **No backfill**: only jobs that end on or after `settings/studios.since` make items. `since` is set to the go-live time, so the first sweep doesn't flood the Content tab with batches that are already in Buffer or Meta. Older jobs still show in the job status.
- Highlight items have no captions yet: `text` is the clip's short title, and the Copy Studio pass can fill it in later.
- The Publishing Desk and Style Studio make no content items.

### `settings/studios`: the task map

```json
{ "since": "<go-live ISO time>", "taskMap": { "highlight": "shorts.daily.clips", "factory": "content.evergreen" } }
```

When a job turns `confirmed`, the writer adds a check-in to `days/{endedAt date in PT}` for the mapped task: `{at: endedAt, by: "studio", note: "<studio> · <job title>", link: <studio url>}`. Counter tasks get `count` equal to the number of videos. The existing check-in rule applies: never change an entry that is already there. Matt edits this map in the database. It starts with the two entries above.

## Status rules (one function, tested first)

`status(raw, videos, updatedAt, now)` returns one of the four words:

| Raw | Result |
|---|---|
| queued, working, running, building, any step in progress | `pending` |
| done or ready, with at least 1 video (Style Studio: done) | `confirmed` |
| done or ready, with no videos (not Style Studio) | `unknown` |
| failed or error | `failed` |
| anything else, or missing | `unknown` |
| `pending`, but `updatedAt` is more than 6 hours old | `unknown` |

Publishing Desk:
- A video's status is `failed` if any platform is FAILED, `confirmed` once every scheduled platform is PUBLISHED, and otherwise `pending`.
- A weekly proposal in PREVIEW is `pending`, which means it needs Matt. It is `confirmed` once APPROVED or APPLIED, and `failed` if SENT BACK.

The page applies one more rule when it reads the doc: if a studio's `checkedAt` is more than 2 hours old during copy hours (4 AM to 4 PM PT), every job on its card shows `unknown`, with the line "no check since <time PT>". Outside copy hours, the limit is 14 hours.

## Writers

### 1. Worker step (each studio's existing worker)

At the end of every job run, success or failure, the worker:
- builds one JSON file with the script (`intake.py job <studio> <job.json>`);
- writes it to the Command Center with one ArtifactData batch: an update to `studio/{name}` that merges into `jobs`, sets for any new content items, and the check-in.

This adds one short paragraph to each worker prompt. It needs Matt's OK for each of the four workers. If a worker crashes before it reports, the hourly copy catches the job.

### 2. Hourly copy step (trig_01NU7aWKpkA7LmF3mh6tbz9N)

For each studio:
- ArtifactData query where `updatedAt` is greater than the studio doc's `checkedAt`, with `out_dir`, so captions don't flood the context;
- `intake.py sweep <studio> <dir> <current studio doc>` outputs a batch file;
- one ArtifactData batch for all studios, plus a `checkedAt` bump.

If nothing changed, only `checkedAt` is written. The step adds about one Bash call and one batch to each run.

### The script: `command-center/studios/intake.py`

- It is pure Python with the standard library only, and it lives in qg-media next to the Buffer pipeline. It is the only place mapping rules live.
- Inputs: raw studio docs, plus the current Command Center docs (to check that items don't already exist and for the job versions).
- Output: a list of batch writes. It never calls the network.

## Screen (preview first; the Impeccable pass proposes the layout before anything is applied)

- **Today, STUDIOS card**: built like the Air card. It has one row per studio: name, latest job title, status word, and age. Clicking a row opens that studio. A failed job turns the card's border and the row rose. Unknown rows are grey.
- **Badges**: the TODAY tab badge counts studio jobs that are `failed`, plus Publishing Desk weeks waiting on approval. Nothing else nudges.
- **Content tab**: new items show a studio chip ("FACTORY", "HIGHLIGHT") and the video's length. They are otherwise normal `ready` cards.
- **Automations tab**: one row per studio, showing `checkedAt` and its source (worker or hourly).

## Errors

- Unreadable studio: that studio's doc is left alone, so its `checkedAt` ages and the page shows `unknown`.
- A version conflict on a batch write: re-read once, then skip until the next run. This never forces a write.
- A malformed job doc: the script records it as `unknown` with `message: "unreadable job"` and never crashes the sweep.

## Testing

- `test_intake.py` (unittest) covers every row of the status table, both Publishing Desk rules, merging by newer `updatedAt`, keeping 10 jobs, add-only content, the Oct 14 skip, the task-map check-in, and `count` on counter tasks. It uses fixtures cut from the real docs read on 2026-10-30.
- The page's staleness rule and card rendering are checked in a preview copy with seeded docs (fresh, stale, failed and empty), with screenshots at phone and desktop width.
- Before calling it done, run the hourly step once by hand against the live studios. Confirm that at least one real `confirmed` job and its content items land in the database. Then verify the page shows them.

## Rollout order (each step waits for Matt's OK)

1. Script and tests, in a PR.
2. Command Center preview copy with the STUDIOS card and chips, shown to Matt.
3. Hourly copy prompt change. Live tool: ask first.
4. Publish the Command Center. Live tool: ask first.
5. The worker steps for the four studios, one at a time. Live tools: ask first.
6. Once evidence shows a real job flowed through, mark `command-center.v3` (studio half) done.
