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
