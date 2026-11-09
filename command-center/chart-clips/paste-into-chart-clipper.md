Paste this into the "QG Auto Chart Clipper" project (or its scheduled job's prompt):

---

Add one reporting step to the evening clip job. Keep everything else as it is: what gets made, captions, and Buffer scheduling all stay the same. This step only reports.

Report target: the Clip Monitor artifact https://claude.ai/artifact/W6Tu8vrSJ5JD6SSa8bCfgd (load ArtifactData and Artifact with ToolSearch if needed).

1. When the job starts, use ArtifactData `set` on that url, collection `runs`, doc_id = today's date in America/New_York (YYYY-MM-DD). Write {status: "working", updatedAt: now ISO, message: "Reading Joule", clips: []}. Read the doc first and pass if_version if it already exists.
2. After each clip renders, upload the mp4 to the monitor with the Artifact tool: action publish, url = the monitor, file_path = the mp4, asset: true. Files must be 20 MB or less. Note the `id` the result returns.
3. After the clip is scheduled in Buffer, add it to `clips` in the runs doc using `update` with if_version:
   {id: short slug, ticker: "SPX"|"SPY"|"QQQ" (or a list), title: the clip's headline, caption: the first line of the caption, assetId: the id from step 2, seconds, createdAt: now ISO, posts: {tiktok: <Buffer post id>, instagram: <id>, youtube: <id>}}
   Leave out any channel that has no post.
4. At the end, set status "done" (or "failed" with a one-sentence `message`) and updatedAt.
5. Each time you write the runs doc (steps 1, 3 and 4), also write the same doc to the QG Command Center https://claude.ai/artifact/MC7jzykFQzwWp16rzA65QA, collection `clips`, with the same doc_id and with if_version. That fills the CREATED column on its Chart Clips card.
6. Once a day, delete monitor assets older than 5 days (Artifact action delete, url = the monitor, path = asset id). Only delete ones this job uploaded. This keeps the store under its quota.

Status words on the monitor and Command Center are confirmed, pending, failed and unknown. "Confirmed" needs a Buffer post id, so always include the ids.
