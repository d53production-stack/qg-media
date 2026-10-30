# Studio intake (`intake.py`)

The one place the mapping rules live for feeding the QG studios into the
Command Center. Pure Python 3, standard library only, no network. It reads
raw studio docs plus the current Command Center docs and prints a JSON list
of ArtifactData writes. Something else (a studio worker, or the hourly copy)
applies those writes with one `ArtifactData batch`.

Spec: `docs/superpowers/specs/2026-10-30-studio-intake-design.md`.
Plan: `docs/superpowers/plans/2026-10-30-studio-intake.md`.

## Commands

```bash
# a studio worker, at the end of one job run (success or failure)
python3 intake.py job factory path/to/job.json --id 2026-10-29-whats-new --cc ./cc > writes.json

# the hourly copy, over a directory of changed docs for one studio
python3 intake.py sweep highlight ./raw/highlight --cc ./cc > writes.json

python3 -m unittest test_intake   # 59 tests, fixtures cut from the live docs of 2026-10-30
```

Options: `--now <ISO>` fixes the clock (tests and dry runs), `--by` names
the writer (`worker` for `job`, `hourly` for `sweep`).

Studios: `highlight`, `factory`, `style`, `desk`.

## The `--cc` directory

Lay it out the way `ArtifactData ... out_dir` writes the Command Center docs
(`<out_dir>/<collection>/<doc_id>.json`, each file the wrapper
`{id, data, version}`; bare docs work too). Missing files mean "no doc yet".

| Path | Used for |
|---|---|
| `studio/<name>.json` | the current job map and its version |
| `settings/studios.json` | `since` (go-live time) and `taskMap` |
| `tasks/<id>.json` | only the mapped tasks; a `target` means a counter task |
| `days/<date>.json` | the day a check-in would land on |
| `content/*.json` | only the file names are read, to keep content add-only |

## Around the script (the writer's job)

1. Read the Command Center docs above into `./cc` with `out_dir`.
2. Read the studio's changed docs: `query` on its collection with
   `updatedAt > checkedAt` (Highlight `jobs`, Factory `batches`, Style
   `requests`), and for the Desk the `proposals` collection plus any
   `videos` with a platform outside SCHEDULED/READY. Use `out_dir` so the
   captions do not land in the context.
3. Run `intake.py`, then apply the output with one `ArtifactData batch`
   (the entries already carry `op`, `collection`, `doc_id`, `data` and
   `if_version`). On a version conflict: re-read the named doc once, rerun,
   and if it conflicts again skip until the next run. Never force.

If nothing changed, the output is one write: the studio doc with a fresh
`checkedAt`.

## Rules the script enforces

- Status words: `confirmed`, `pending`, `failed`, `unknown`, nothing else.
- `pending` older than 6 hours is `unknown`. Not applied to the Desk, where a
  PREVIEW proposal legitimately waits on Matt.
- A job entry is replaced only when its `updatedAt` is newer. Ten newest kept.
- Content is add-only. Only `confirmed` jobs that ended on or after
  `settings/studios.since` make items. No `since`, no items.
- Highlight clips with `short.date` before 2026-10-14 are never added.
- A check-in on `days/<PT date of endedAt>` is added once per mapped task and
  never changes an entry that is already there. Counter tasks get `count`.
- A malformed doc becomes one `unknown` job with `message: "unreadable job"`.

## Decisions the spec left open (made in the build, 2026-10-30)

- Highlight housekeeping jobs (`task: "clear"`) and jobs whose files were
  cleared (`cleared` / `clearRequestedAt`) are skipped, not shown as unknown.
  The Oct 29 clear had bumped `updatedAt` on eight old jobs, which would have
  pushed real ones out of the ten kept.
- Desk jobs are: every weekly proposal (`Week 2026-W44`), plus a video only
  once a platform leaves SCHEDULED/READY (PUBLISHING, PUBLISHED, FAILED).
  Scheduled-only videos are already content and stay out.
- Desk docs have no `updatedAt`; the script uses `applied_at` / `decided_at`
  / `created` for a proposal and the newest `schedule[].set` for a video.
- Content items carry both the spec's `type: "video"` and the page's existing
  fields (`kind`, `channels`, `media`, `createdAt`) so the Content tab renders
  them today. Both Factory orientations (`-v`, `-h`) become separate items.
- `studio/<name>` and `days/<date>` are written as full-document `set`s
  pinned with `if_version`, so the merge is tested here, not left to the
  server's merge depth.

## Rollout (each step waits for Matt's OK)

1. This script and its tests, in a PR. **(this PR)**
2. Command Center preview copy with the STUDIOS card and content chips.
3. Hourly copy prompt gains the sweep step. Live tool: ask first.
4. Publish the Command Center. Live tool: ask first.
5. Workers fire the "Command Center: studio job done" task at job end (see WORKER-STEPS.md); the runbook line needs Matt's OK per studio.
6. Mark `command-center.v3` (studio half) done once a real job has flowed through.
