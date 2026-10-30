#!/usr/bin/env python3
"""Studio intake for the QG Command Center.

Turns raw studio docs (Highlight Studio, Video Factory, Style Studio,
Publishing Desk) into ArtifactData writes for the Command Center database:
job status under studio/{name}, finished videos under content/{id}, and
task check-ins under days/{date}. Pure Python, standard library only, no
network. Every mapping rule lives here and is covered by test_intake.py.

Spec: docs/superpowers/specs/2026-10-30-studio-intake-design.md
"""
from __future__ import annotations

import json
import os
import sys

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

STATUS_WORDS = ("confirmed", "pending", "failed", "unknown")
STALE_PENDING = timedelta(hours=6)

PENDING_RAW = {"queued", "working", "running", "building"}
DONE_RAW = {"done", "ready"}
FAILED_RAW = {"failed", "error"}


def parse_time(value) -> datetime | None:
    """ISO 8601 to an aware datetime. 'Z' allowed; naive values are UTC."""
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _word(raw) -> str:
    return raw.strip().lower() if isinstance(raw, str) else ""


def status(raw, videos: int, updated_at, now: datetime, studio: str) -> str:
    """One of the four status words for a Highlight, Factory or Style job."""
    word = _word(raw)
    if word in FAILED_RAW:
        return "failed"
    if word in PENDING_RAW:
        seen = parse_time(updated_at)
        if seen is None or now - seen > STALE_PENDING:
            return "unknown"
        return "pending"
    if word in DONE_RAW:
        if studio == "style" or (videos or 0) >= 1:
            return "confirmed"
        return "unknown"
    return "unknown"


def desk_video_status(status_map) -> str:
    """Publishing Desk video: failed if any platform FAILED, confirmed once
    every scheduled platform is PUBLISHED, otherwise pending."""
    if not isinstance(status_map, dict):
        return "unknown"
    states = [_word(v).upper() for v in status_map.values()]
    states = [s for s in states if s != "CANCELLED"]
    if not states:
        return "unknown"
    if "FAILED" in states:
        return "failed"
    if all(s == "PUBLISHED" for s in states):
        return "confirmed"
    return "pending"


def desk_proposal_status(raw) -> str:
    word = _word(raw).upper()
    if word == "PREVIEW":
        return "pending"
    if word in ("APPROVED", "APPLIED"):
        return "confirmed"
    if word == "SENT BACK":
        return "failed"
    return "unknown"


# --- studios -----------------------------------------------------------------

STUDIOS = {
    "highlight": {"label": "Highlight Studio", "url": "https://claude.ai/artifact/9pKYhvbeaxpwwDyhQswHvi", "collection": "jobs", "prefix": "hs-"},
    "factory": {"label": "Video Factory", "url": "https://claude.ai/artifact/Q9r9A3GK8dhbKB5jKb2p2g", "collection": "batches", "prefix": "vf-"},
    "style": {"label": "Style Studio", "url": "https://claude.ai/artifact/AmAqmKFatXwLoTUiE29iTU", "collection": "requests", "prefix": None},
    "desk": {"label": "Publishing Desk", "url": "https://claude.ai/artifact/Y876Yu3rcP3g4hX6oSfcKz", "collection": "videos", "prefix": None},
}

DESK_QUIET = {"SCHEDULED", "READY", ""}


def _outputs_list(raw) -> list:
    outs = raw.get("outputs")
    if outs is None:
        return []
    if not isinstance(outs, list):
        raise ValueError("outputs is not a list")
    return [o for o in outs if isinstance(o, dict)]


def _entry(title, st, raw_word, step, started, ended, updated, videos, message=""):
    for t in (started, ended, updated):
        if t is not None and not isinstance(t, str):
            raise ValueError("time field is not a string")
    return {
        "title": str(title or ""),
        "status": st,
        "raw": str(raw_word or ""),
        "step": str(step or ""),
        "startedAt": started,
        "endedAt": ended,
        "updatedAt": updated,
        "videos": int(videos or 0),
        "message": str(message or ""),
    }


def normalize(studio: str, job_id: str, raw: dict, now: datetime) -> dict | None:
    """Spec job entry for one raw doc, or None when the doc is not a job the
    Command Center should show. Raises on malformed input; see safe_normalize."""
    if not isinstance(raw, dict):
        raise ValueError("job is not an object")
    if studio == "desk":
        return _normalize_desk(job_id, raw, now)
    if studio == "highlight" and (raw.get("task") == "clear" or raw.get("cleared") or raw.get("clearRequestedAt")):
        return None  # housekeeping, or a job whose files were cleared from disk
    videos = len(_outputs_list(raw))
    word = raw.get("status")
    updated = raw.get("updatedAt") or raw.get("builtAt") or raw.get("queuedAt") or raw.get("createdAt")
    st = status(word, videos, updated, now, studio)
    ended = None
    if _word(word) in DONE_RAW | FAILED_RAW:
        ended = raw.get("builtAt") if studio == "factory" and raw.get("builtAt") else updated
    return _entry(
        raw.get("title") or raw.get("name") or job_id, st, word, raw.get("step"),
        raw.get("queuedAt") or raw.get("createdAt"), ended, updated,
        videos, raw.get("message"),
    )


def _normalize_desk(job_id: str, raw: dict, now: datetime) -> dict | None:
    if "week" in raw or isinstance(raw.get("status"), str):
        word = raw.get("status")
        st = desk_proposal_status(word)
        updated = raw.get("applied_at") or raw.get("decided_at") or raw.get("created")
        ended = updated if st in ("confirmed", "failed") else None
        week = raw.get("week") or job_id
        return _entry(f"Week {week}", st, word, raw.get("status"), raw.get("created"), ended, updated, 0)
    smap = raw.get("status") if isinstance(raw.get("status"), dict) else {}
    if any(not isinstance(s, str) for s in smap.values()):
        raise ValueError("platform status is not a string")
    schedule = raw.get("schedule") or []
    if not isinstance(schedule, list):
        raise ValueError("schedule is not a list")
    loud = {p: s.upper() for p, s in smap.items() if s.upper() not in DESK_QUIET}
    if not loud:
        return None
    st = desk_video_status(smap)
    sets = [s.get("set") for s in schedule if isinstance(s, dict) and s.get("set")]
    updated = max(sets, key=lambda t: parse_time(t) or datetime.min.replace(tzinfo=timezone.utc)) if sets else now.isoformat()
    raw_word = " ".join(f"{p} {s}" for p, s in sorted(loud.items()))
    ended = updated if st in ("confirmed", "failed") else None
    return _entry(raw.get("title") or job_id, st, raw_word, raw.get("series"), None, ended, updated, 0)


def safe_normalize(studio: str, job_id: str, raw, now: datetime) -> dict | None:
    """normalize() that never raises: a malformed doc is an unknown job."""
    try:
        return normalize(studio, job_id, raw, now)
    except Exception:  # noqa: BLE001 - the sweep must never crash on one doc
        updated = raw.get("updatedAt") if isinstance(raw, dict) else None
        if not isinstance(updated, str) or not updated:
            updated = now.isoformat()
        return _entry(job_id, "unknown", "", "", None, None, updated, 0, "unreadable job")


def outputs(studio: str, job_id: str, raw) -> list[dict]:
    """Content candidates for a job's finished videos. Style and Desk give none."""
    prefix = STUDIOS.get(studio, {}).get("prefix")
    if not prefix or not isinstance(raw, dict):
        return []
    items = []
    for o in _outputs_list(raw):
        name = o.get("name")
        if not name:
            continue
        if studio == "factory":
            copy = o.get("copy") if isinstance(o.get("copy"), dict) else {}
            title = copy.get("title") or o.get("title") or name
            by_channel = {k: copy[src] for k, src in (("youtube", "description"), ("instagram", "instagram"), ("tiktok", "tiktok")) if copy.get(src)}
            text = copy.get("instagram") or copy.get("description") or ""
            orientation = o.get("o") or ("h" if name.endswith("-h") else "v")
            clip_date = None
        else:
            short = o.get("short") if isinstance(o.get("short"), dict) else {}
            title = short.get("title") or o.get("title") or name
            by_channel = {}
            text = title
            orientation = "v"
            clip_date = short.get("date") or raw.get("date")
        items.append({
            "id": prefix + name, "title": title, "path": o.get("path"), "poster": o.get("poster"),
            "seconds": o.get("seconds"), "orientation": orientation, "clipDate": clip_date,
            "text": text, "textByChannel": by_channel,
        })
    return items


# --- studio doc ----------------------------------------------------------------

KEEP_JOBS = 10


def _ts(value) -> datetime:
    return parse_time(value) or datetime.min.replace(tzinfo=timezone.utc)


def merge_jobs(current: dict | None, incoming: dict, by: str, now: datetime, studio: str | None = None) -> dict:
    """New studio/{name} data: incoming entries replace stored ones only when
    newer by updatedAt, the 10 newest jobs are kept, checkedAt is bumped."""
    studio = studio or (current or {}).get("studio")
    meta = STUDIOS.get(studio, {})
    jobs = dict((current or {}).get("jobs") or {})
    for job_id, entry in incoming.items():
        stored = jobs.get(job_id)
        if stored and _ts(stored.get("updatedAt")) >= _ts(entry.get("updatedAt")):
            continue
        jobs[job_id] = dict(entry, by=by)
    newest = sorted(jobs.items(), key=lambda kv: _ts(kv[1].get("updatedAt")), reverse=True)[:KEEP_JOBS]
    return {
        "studio": studio,
        "label": (current or {}).get("label") or meta.get("label", studio),
        "url": (current or {}).get("url") or meta.get("url", ""),
        "checkedAt": now.isoformat(),
        "checkedBy": by,
        "jobs": dict(newest),
    }


# --- content items -------------------------------------------------------------

MIN_CLIP_DATE = "2026-10-14"


def content_writes(studio: str, job_id: str, job: dict | None, candidates: list, existing_ids: set, since) -> list[dict]:
    """Add-only content/{id} writes for a confirmed job that ended on or after
    `since`. Highlight clips dated before MIN_CLIP_DATE are never added."""
    if not job or job.get("status") != "confirmed" or not since or not job.get("endedAt"):
        return []
    if _ts(job["endedAt"]) < _ts(since):
        return []
    meta = STUDIOS[studio]
    writes = []
    for c in candidates:
        if c["id"] in existing_ids:
            continue
        if studio == "highlight" and c.get("clipDate") and c["clipDate"] < MIN_CLIP_DATE:
            continue
        writes.append({"op": "set", "collection": "content", "doc_id": c["id"], "data": {
            "id": c["id"],
            "title": c["title"],
            "type": "video",
            "kind": "video",
            "status": "ready",
            "channels": [],
            "media": [{"file": c.get("path") or "", "alt": c["title"]}],
            "text": c.get("text") or "",
            "textByChannel": c.get("textByChannel") or {},
            "sourceArtifact": meta["url"],
            "studio": {
                "name": studio, "job": job_id, "path": c.get("path"), "poster": c.get("poster"),
                "seconds": c.get("seconds"), "orientation": c.get("orientation"), "clipDate": c.get("clipDate"),
            },
            "by": "studio",
            "at": job["endedAt"],
            "createdAt": job["endedAt"],
        }})
    return writes


# --- check-ins -----------------------------------------------------------------

PT = ZoneInfo("America/Los_Angeles")


def pt_date(iso: str) -> str:
    return parse_time(iso).astimezone(PT).strftime("%Y-%m-%d")


def checkin_write(studio: str, job: dict | None, task_map: dict, tasks: dict, day_doc: dict | None) -> dict | None:
    """A set on days/{PT date of endedAt} adding the mapped task's check-in,
    or None. An entry that is already there is never changed."""
    task_id = (task_map or {}).get(studio)
    if not task_id or not job or job.get("status") != "confirmed" or not job.get("endedAt"):
        return None
    done = dict((day_doc or {}).get("done") or {})
    if task_id in done:
        return None
    meta = STUDIOS[studio]
    entry = {"at": job["endedAt"], "by": "studio", "note": f"{meta['label']} · {job.get('title', '')}", "link": meta["url"]}
    task = (tasks or {}).get(task_id) or {}
    if task.get("target"):
        entry["count"] = int(job.get("videos") or 0)
    done[task_id] = entry
    date = pt_date(job["endedAt"])
    data = dict(day_doc or {}, date=date, done=done)
    return {"op": "set", "collection": "days", "doc_id": date, "data": data}


# --- a run ---------------------------------------------------------------------

class CCDocs:
    """The Command Center docs a run needs, as read before the run."""

    def __init__(self, studio=None, settings=None, tasks=None, days=None, content_ids=None, versions=None):
        self.studio = studio            # current studio/{name} data or None
        self.settings = settings or {}  # settings/studios data
        self.tasks = tasks or {}        # tasks/{id} data by id (only mapped ones needed)
        self.days = days or {}          # days/{date} data by date
        self.content_ids = set(content_ids or ())
        self.versions = versions or {}  # "collection/doc_id" -> version


def _pin(write: dict, cc: CCDocs) -> dict:
    v = cc.versions.get(f"{write['collection']}/{write['doc_id']}")
    if v is not None:
        write["if_version"] = v
    return write


def run(studio: str, raw_docs: dict, cc: CCDocs, now: datetime, by: str) -> list[dict]:
    """All writes for one studio: exactly one studio/{name} set, add-only
    content sets, and at most one days/{date} set per date."""
    if studio not in STUDIOS:
        raise SystemExit(f"unknown studio {studio!r}; one of {', '.join(STUDIOS)}")
    incoming, writes, days = {}, [], dict(cc.days)
    since = cc.settings.get("since")
    task_map = cc.settings.get("taskMap") or {}
    for job_id, raw in raw_docs.items():
        job = safe_normalize(studio, job_id, raw, now)
        if job is None:
            continue
        incoming[job_id] = job
        stored = (cc.studio or {}).get("jobs", {}).get(job_id) if cc.studio else None
        if stored and _ts(stored.get("updatedAt")) >= _ts(job.get("updatedAt")):
            continue  # nothing new for this job; no items or check-ins either
        writes.extend(content_writes(studio, job_id, job, outputs(studio, job_id, raw), cc.content_ids, since))
        if since and job.get("endedAt") and _ts(job["endedAt"]) >= _ts(since):
            ci = checkin_write(studio, job, task_map, cc.tasks, days.get(pt_date(job["endedAt"])))
            if ci:
                days[ci["doc_id"]] = ci["data"]
                writes = [w for w in writes if not (w["collection"] == "days" and w["doc_id"] == ci["doc_id"])]
                writes.append(_pin(ci, cc))
    doc = merge_jobs(cc.studio, incoming, by, now, studio=studio)
    return [_pin({"op": "set", "collection": "studio", "doc_id": studio, "data": doc}, cc)] + writes


# --- files and CLI -------------------------------------------------------------

def unwrap(obj, fallback_id: str):
    """(id, data, version) from an ArtifactData out_dir file or a bare doc."""
    if isinstance(obj, dict) and "data" in obj and isinstance(obj.get("id"), str):
        return obj["id"], obj["data"], obj.get("version")
    return fallback_id, obj, None


def _read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _json_files(root: str) -> list[str]:
    found = []
    for base, _dirs, files in os.walk(root):
        found.extend(os.path.join(base, f) for f in files if f.endswith(".json"))
    return sorted(found)


def load_cc(cc_dir: str, studio: str) -> CCDocs:
    """Read a Command Center out_dir: studio/<name>.json, settings/studios.json,
    tasks/*.json, days/*.json and the ids under content/. Missing files are fine."""
    cc = CCDocs()

    def one(rel):
        path = os.path.join(cc_dir, rel + ".json")
        if not os.path.exists(path):
            return None
        _id, data, version = unwrap(_read_json(path), os.path.basename(rel))
        if version is not None:
            cc.versions[rel] = version
        return data

    cc.studio = one(f"studio/{studio}")
    cc.settings = one("settings/studios") or {}
    for coll, target in (("tasks", cc.tasks), ("days", cc.days)):
        d = os.path.join(cc_dir, coll)
        if os.path.isdir(d):
            for path in _json_files(d):
                doc_id = os.path.splitext(os.path.basename(path))[0]
                target[doc_id] = one(f"{coll}/{doc_id}")
    d = os.path.join(cc_dir, "content")
    if os.path.isdir(d):
        cc.content_ids = {os.path.splitext(os.path.basename(p))[0] for p in _json_files(d)}
    # ArtifactData out_dir files hold bare doc data with no version, so the run
    # writes the versions its reads printed into versions.json.
    path = os.path.join(cc_dir, "versions.json")
    if os.path.exists(path):
        cc.versions.update({k: int(v) for k, v in _read_json(path).items()})
    return cc


def missing_pins(writes: list, cc_dir: str, cc: CCDocs) -> list[str]:
    """Writes to a doc that was read (its file is under cc_dir) but carry no
    version: the store refuses those, so the run must not send them."""
    return [f"{w['collection']}/{w['doc_id']}" for w in writes
            if "if_version" not in w and f"{w['collection']}/{w['doc_id']}" not in cc.versions
            and os.path.exists(os.path.join(cc_dir, w["collection"], w["doc_id"] + ".json"))]


def load_raw_dir(raw_dir: str) -> dict:
    """Every *.json under raw_dir (an ArtifactData out_dir may nest the
    collection folder) as {job_id: data}. An unreadable file is kept as a
    non-dict so the run records it as unreadable."""
    docs = {}
    for path in _json_files(raw_dir):
        fallback = os.path.splitext(os.path.basename(path))[0]
        try:
            doc_id, data, _v = unwrap(_read_json(path), fallback)
        except (OSError, ValueError):
            doc_id, data = fallback, None
        docs[doc_id] = data
    return docs


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, help_ in (("job", "one job file, reported by a studio worker"), ("sweep", "a directory of changed docs, swept by the hourly copy")):
        p = sub.add_parser(name, help=help_)
        p.add_argument("studio", choices=sorted(STUDIOS))
        p.add_argument("path")
        p.add_argument("--cc", required=True, help="directory of Command Center docs (ArtifactData out_dir layout)")
        p.add_argument("--now", help="ISO time to treat as now (default: current UTC time)")
        p.add_argument("--by", default="worker" if name == "job" else "hourly")
        if name == "job":
            p.add_argument("--id", dest="job_id", help="job id (default: the doc's id, or the file name)")
    a = ap.parse_args(argv)
    now = parse_time(a.now) if a.now else datetime.now(timezone.utc)
    if now is None:
        ap.error("--now is not an ISO time")
    cc = load_cc(a.cc, a.studio)
    if a.cmd == "job":
        fallback = os.path.splitext(os.path.basename(a.path))[0]
        job_id, data, _v = unwrap(_read_json(a.path), fallback)
        if isinstance(data, dict) and isinstance(data.get("id"), str):
            job_id = data["id"]
        raw = {a.job_id or job_id: data}
    else:
        raw = load_raw_dir(a.path)
    writes = run(a.studio, raw, cc, now, a.by)
    missing = missing_pins(writes, a.cc, cc)
    if missing:
        sys.stderr.write("".join(f"missing version for {m}: add it to {a.cc}/versions.json\n" for m in missing))
        return 2
    json.dump(writes, sys.stdout, indent=1, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
