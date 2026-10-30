# Studio workers: report a job to the Command Center

Every QG studio worker (Highlight Studio render request, Video Factory page request and weekly batch,
the 3-hourly queue check, Style Studio requests, Publishing Desk Sunday run) follows a runbook in the
QG studios project. Each runbook's job section gets ONE line at the end, after the job's result is
written back to the studio's own doc, on success and on failure alike:

> Fire the Command Center report: `fire_trigger` (Claude Code Remote) with
> `trigger_id` `trig_0167LNuPWWRSGkPnAvEaAAih` and `text` `"<studio> <job id>"`, where `<studio>` is
> `highlight`, `factory`, `style` or `desk` and `<job id>` is the studio doc id
> (Highlight `jobs/<id>`, Factory `batches/<id>`, Style `requests/<id>`, Desk `proposals/<week>`
> or `videos/<id>`). If the tool is missing or the call fails, skip it: the Command Center's
> hourly sweep catches the job.

That is the whole change. No studio page, prompt or database is touched. The fired task
("Command Center: studio job done") reads that one job, runs `intake.py job`, and writes the
Command Center in one batch: the STUDIOS card row, the TODAY badge on failure, new videos as
Content items, the day's check-in, and the Automations "last check" row.

Runbooks to change (QG studios project, shared folder):

| Studio | Runbook | Section |
|---|---|---|
| Highlight Studio | `style/studio/RUNBOOK.md` | "When woken" (render, mute, rename; also the failure path) |
| Video Factory | `build/factory/RUNBOOK.md` | "Make a batch" end, and the failure path |
| Style Studio | `style/style-studio/RUNBOOK.md` | after a request is written back (done or failed) |
| Publishing Desk | `build/DESK-RUNBOOK.md` | "Weekly": after the proposal is applied/proposed, and after any video status change |

Rules the task enforces are in `README.md` and `intake.py` next to this file.
