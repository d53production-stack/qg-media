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

from datetime import datetime, timedelta, timezone

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
    if studio == "highlight" and raw.get("task") == "clear":
        return None
    videos = len(_outputs_list(raw))
    word = raw.get("status")
    st = status(word, videos, raw.get("updatedAt"), now, studio)
    ended = None
    if _word(word) in DONE_RAW | FAILED_RAW:
        ended = raw.get("builtAt") if studio == "factory" and raw.get("builtAt") else raw.get("updatedAt")
    return _entry(
        raw.get("title") or raw.get("name") or job_id, st, word, raw.get("step"),
        raw.get("queuedAt") or raw.get("createdAt"), ended, raw.get("updatedAt"),
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
