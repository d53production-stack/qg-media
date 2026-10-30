# Prompt change: give intake.py the doc versions (2026-10-30)

ArtifactData `out_dir` files hold the bare doc data with no version, so intake.py could not pin its writes and every hourly studio sweep since 2026-10-30 03:07Z refused its own writes. intake.py now reads `./cc/versions.json` and exits 2 (`missing version for <doc>`) instead of printing unpinned writes. Both scheduled tasks need one added instruction. Apply only with Matt's OK.

## Hourly copy (trig_01NU7aWKpkA7LmF3mh6tbz9N), step 5b

Old:

```
list collection "content" with query {"limit": 1000} (only the file names are used). Then read each studio's changed docs
```

New:

```
list collection "content" with query {"limit": 1000} (only the file names are used). Each of those results prints a version per doc: with one python3 command write ./cc/versions.json mapping "studio/<name>" and "days/<date>" to the version printed for every studio and days doc you read, e.g. {"studio/highlight": 2, "days/2026-10-30": 5}. Then read each studio's changed docs
```

And old:

```
A studio whose read or script failed is skipped and its doc left alone.
```

New:

```
A studio whose read or script failed (exit 2 means a version is missing from versions.json) is skipped and its doc left alone.
```

And in the conflict retry, old:

```
re-read the named doc into ./cc, rerun the script for that studio only
```

New:

```
re-read the named doc into ./cc, put its new version in ./cc/versions.json, rerun the script for that studio only
```

## Studio job done (trig_0167LNuPWWRSGkPnAvEaAAih), step 2

Old:

```
list collection "content" with query {"limit": 1000} (only the file names are used).
3) Read the job
```

New:

```
list collection "content" with query {"limit": 1000} (only the file names are used). With one python3 command write ./cc/versions.json mapping "studio/<studio>" and "days/<TODAY>" to the version each result printed (leave out a doc that does not exist).
3) Read the job
```

And step 5, old:

```
re-read the named doc into ./cc, rerun step 4
```

New:

```
re-read the named doc into ./cc, put its new version in ./cc/versions.json, rerun step 4
```

## Dry run (2026-10-30 ~21:10Z, nothing written)

Real Command Center docs read with out_dir, versions.json written by hand from the printed versions, `intake.py sweep` run for all four studios: each produced one studio write pinned to its live version (highlight 2, factory 1, style 1, desk 1). Without versions.json the script exits 2 naming `studio/factory`.
