"""Tests for intake.py. Fixtures are cut from the real studio docs read on 2026-10-30."""
import json
import os
import unittest
from datetime import datetime, timedelta, timezone

import intake

HERE = os.path.dirname(os.path.abspath(__file__))
NOW = datetime(2026, 10, 30, 3, 0, tzinfo=timezone.utc)


def fixture(name):
    with open(os.path.join(HERE, "fixtures", name), encoding="utf-8") as f:
        return json.load(f)


class TestStatus(unittest.TestCase):
    def s(self, raw, videos=0, updated=None, studio="factory"):
        return intake.status(raw, videos, updated or "2026-10-30T02:30:00Z", NOW, studio)

    def test_in_progress_words_are_pending(self):
        for raw in ("queued", "working", "running", "building", "Queued"):
            self.assertEqual(self.s(raw), "pending", raw)

    def test_done_with_videos_is_confirmed(self):
        self.assertEqual(self.s("done", 1), "confirmed")
        self.assertEqual(self.s("ready", 10), "confirmed")

    def test_done_without_videos_is_unknown(self):
        self.assertEqual(self.s("done", 0), "unknown")
        self.assertEqual(self.s("done", 0, studio="highlight"), "unknown")

    def test_style_done_without_videos_is_confirmed(self):
        self.assertEqual(self.s("done", 0, studio="style"), "confirmed")

    def test_failed_and_error_are_failed(self):
        self.assertEqual(self.s("failed"), "failed")
        self.assertEqual(self.s("error", 3), "failed")

    def test_anything_else_is_unknown(self):
        self.assertEqual(self.s(None), "unknown")
        self.assertEqual(self.s("weird"), "unknown")
        self.assertEqual(self.s(""), "unknown")

    def test_stale_pending_is_unknown(self):
        old = (NOW - timedelta(hours=7)).isoformat()
        fresh = (NOW - timedelta(hours=5)).isoformat()
        self.assertEqual(self.s("working", updated=old), "unknown")
        self.assertEqual(self.s("working", updated=fresh), "pending")

    def test_pending_without_updated_at_is_unknown(self):
        self.assertEqual(intake.status("working", 0, None, NOW, "factory"), "unknown")


class TestDesk(unittest.TestCase):
    def test_any_failed_platform_is_failed(self):
        self.assertEqual(intake.desk_video_status({"ig": "FAILED", "shorts": "PUBLISHED"}), "failed")

    def test_all_published_is_confirmed(self):
        self.assertEqual(intake.desk_video_status({"ig": "PUBLISHED", "tiktok": "PUBLISHED"}), "confirmed")

    def test_mixed_is_pending(self):
        self.assertEqual(intake.desk_video_status({"ig": "SCHEDULED", "tiktok": "PUBLISHED"}), "pending")
        self.assertEqual(intake.desk_video_status({"ig": "PUBLISHING"}), "pending")

    def test_cancelled_platforms_do_not_block_confirmed(self):
        self.assertEqual(intake.desk_video_status({"ig": "CANCELLED", "tiktok": "PUBLISHED"}), "confirmed")

    def test_empty_map_is_unknown(self):
        self.assertEqual(intake.desk_video_status({}), "unknown")
        self.assertEqual(intake.desk_video_status(None), "unknown")

    def test_proposal_states(self):
        self.assertEqual(intake.desk_proposal_status("PREVIEW"), "pending")
        self.assertEqual(intake.desk_proposal_status("APPROVED"), "confirmed")
        self.assertEqual(intake.desk_proposal_status("APPLIED"), "confirmed")
        self.assertEqual(intake.desk_proposal_status("SENT BACK"), "failed")
        self.assertEqual(intake.desk_proposal_status(None), "unknown")


class TestNormalize(unittest.TestCase):
    def test_highlight_done_job(self):
        raw = fixture("highlight-2026-10-29-0ww4.json")
        job = intake.normalize("highlight", "2026-10-29-0ww4", raw, NOW)
        self.assertEqual(job["status"], "confirmed")
        self.assertEqual(job["raw"], "done")
        self.assertEqual(job["videos"], 2)
        self.assertEqual(job["title"], "Oct 29 webinar")
        self.assertEqual(job["step"], "Done")
        self.assertEqual(job["startedAt"], raw["queuedAt"])
        self.assertEqual(job["endedAt"], raw["updatedAt"])
        self.assertEqual(job["updatedAt"], raw["updatedAt"])
        self.assertEqual(job["message"], "")
        self.assertNotIn("by", job)

    def test_highlight_clear_job_is_skipped(self):
        self.assertIsNone(intake.normalize("highlight", "2026-10-29-clear-ad4", fixture("highlight-clear.json"), NOW))

    def test_factory_done_batch(self):
        raw = fixture("factory-2026-10-29-redo-howlive.json")
        job = intake.normalize("factory", "2026-10-29-redo-howlive", raw, NOW)
        self.assertEqual(job["status"], "confirmed")
        self.assertEqual(job["videos"], 2)
        self.assertEqual(job["endedAt"], raw["builtAt"])
        self.assertEqual(job["title"], "Redo: How Live Is the Console? (overnight)")

    def test_factory_pending_has_no_ended_at(self):
        raw = dict(fixture("factory-2026-10-29-redo-howlive.json"), status="working", step="Rendering", outputs=[], updatedAt=NOW.isoformat())
        raw.pop("builtAt")
        job = intake.normalize("factory", "x", raw, NOW)
        self.assertEqual(job["status"], "pending")
        self.assertIsNone(job["endedAt"])
        self.assertEqual(job["videos"], 0)

    def test_style_request(self):
        raw = fixture("style-rmvoi1xo6.json")
        job = intake.normalize("style", "rmvoi1xo6", raw, NOW)
        self.assertEqual(job["status"], "confirmed")
        self.assertEqual(job["videos"], 0)
        self.assertEqual(job["step"], "Saved as v006")
        self.assertEqual(job["title"], "Halloween 2")
        self.assertEqual(job["endedAt"], raw["updatedAt"])

    def test_desk_video_only_scheduled_is_skipped(self):
        self.assertIsNone(intake.normalize("desk", "cc-04a-primary-and-majors", fixture("desk-video-cc-04a.json"), NOW))

    def test_desk_video_with_failure(self):
        raw = fixture("desk-video-cc-04a.json")
        raw["status"]["ig"] = "FAILED"
        job = intake.normalize("desk", "cc-04a-primary-and-majors", raw, NOW)
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["title"], "Primary and Majors")
        self.assertEqual(job["raw"], "ig FAILED")
        self.assertEqual(job["updatedAt"], "2026-10-29T15:17:33-07:00")
        self.assertEqual(job["videos"], 0)

    def test_desk_video_without_set_times_uses_now(self):
        raw = fixture("desk-video-cc-04a.json")
        raw["status"] = {"youtube": "PUBLISHED"}
        raw["schedule"] = [{"at": "2026-10-31T09:00:00-07:00", "platform": "youtube"}]
        job = intake.normalize("desk", "v", raw, NOW)
        self.assertEqual(job["status"], "confirmed")
        self.assertEqual(job["updatedAt"], NOW.isoformat())

    def test_desk_proposal(self):
        raw = fixture("desk-proposal-2026-W44.json")
        job = intake.normalize("desk", "2026-W44", raw, NOW)
        self.assertEqual(job["status"], "confirmed")
        self.assertEqual(job["title"], "Week 2026-W44")
        self.assertEqual(job["raw"], "APPROVED")
        self.assertEqual(job["updatedAt"], raw["applied_at"])
        self.assertEqual(job["endedAt"], raw["applied_at"])

    def test_desk_proposal_preview_is_pending_however_old(self):
        raw = {"week": "2026-W45", "status": "PREVIEW", "created": "2026-10-20T00:00:00Z"}
        job = intake.normalize("desk", "2026-W45", raw, NOW)
        self.assertEqual(job["status"], "pending")
        self.assertEqual(job["updatedAt"], raw["created"])
        self.assertIsNone(job["endedAt"])


class TestOutputs(unittest.TestCase):
    def test_factory_outputs(self):
        raw = fixture("factory-2026-10-29-redo-howlive.json")
        outs = intake.outputs("factory", "2026-10-29-redo-howlive", raw)
        self.assertEqual([o["id"] for o in outs], ["vf-cc-how-live-v", "vf-cc-how-live-h"])
        v = outs[0]
        self.assertEqual(v["orientation"], "v")
        self.assertEqual(v["title"], "How Live Is the Console? | QuantGeeks Console")
        self.assertEqual(v["path"], raw["outputs"][0]["path"])
        self.assertEqual(v["poster"], raw["outputs"][0]["poster"])
        self.assertEqual(v["seconds"], raw["outputs"][0]["seconds"])
        self.assertIsNone(v["clipDate"])
        self.assertEqual(v["text"], raw["outputs"][0]["copy"]["instagram"])
        self.assertEqual(v["textByChannel"], {
            "youtube": raw["outputs"][0]["copy"]["description"],
            "instagram": raw["outputs"][0]["copy"]["instagram"],
            "tiktok": raw["outputs"][0]["copy"]["tiktok"],
        })

    def test_highlight_outputs(self):
        raw = fixture("highlight-2026-10-29-0ww4.json")
        outs = intake.outputs("highlight", "2026-10-29-0ww4", raw)
        self.assertEqual(outs[0]["id"], "hs-2026-10-29-webinar-part1")
        self.assertEqual(outs[0]["title"], "QQQ Resists at 717 in a Trap Door | October 29")
        self.assertEqual(outs[0]["text"], "QQQ Resists at 717 in a Trap Door | October 29")
        self.assertEqual(outs[0]["textByChannel"], {})
        self.assertEqual(outs[0]["clipDate"], "2026-10-29")
        self.assertEqual(outs[0]["orientation"], "v")
        self.assertEqual(outs[0]["seconds"], 56.5)

    def test_style_and_desk_make_no_outputs(self):
        self.assertEqual(intake.outputs("style", "r", fixture("style-rmvoi1xo6.json")), [])
        self.assertEqual(intake.outputs("desk", "w", fixture("desk-proposal-2026-W44.json")), [])

    def test_output_without_name_is_skipped(self):
        raw = fixture("factory-2026-10-29-redo-howlive.json")
        raw["outputs"].append({"path": "x.mp4"})
        self.assertEqual(len(intake.outputs("factory", "j", raw)), 2)


def job_entry(updated, status="confirmed", by=None, title="t"):
    e = {"title": title, "status": status, "raw": "done", "step": "", "startedAt": None,
         "endedAt": updated, "updatedAt": updated, "videos": 1, "message": ""}
    if by:
        e["by"] = by
    return e


class TestMergeJobs(unittest.TestCase):
    def current(self, **jobs):
        return {"studio": "factory", "label": "Video Factory", "url": intake.STUDIOS["factory"]["url"],
                "checkedAt": "2026-10-29T00:00:00Z", "checkedBy": "hourly", "jobs": jobs}

    def test_newer_replaces_and_sets_by(self):
        cur = self.current(a=job_entry("2026-10-29T01:00:00Z", "pending", by="hourly"))
        doc = intake.merge_jobs(cur, {"a": job_entry("2026-10-29T02:00:00Z")}, "worker", NOW)
        self.assertEqual(doc["jobs"]["a"]["status"], "confirmed")
        self.assertEqual(doc["jobs"]["a"]["by"], "worker")

    def test_equal_updated_at_leaves_stored_entry(self):
        stored = job_entry("2026-10-29T02:00:00Z", by="worker", title="stored")
        doc = intake.merge_jobs(self.current(a=stored), {"a": job_entry("2026-10-29T02:00:00Z", title="again")}, "hourly", NOW)
        self.assertEqual(doc["jobs"]["a"], stored)

    def test_older_is_ignored(self):
        stored = job_entry("2026-10-29T02:00:00Z", by="worker")
        doc = intake.merge_jobs(self.current(a=stored), {"a": job_entry("2026-10-29T01:00:00Z")}, "hourly", NOW)
        self.assertEqual(doc["jobs"]["a"], stored)

    def test_keeps_ten_newest(self):
        cur = self.current(**{f"j{i:02d}": job_entry(f"2026-10-{i+1:02d}T00:00:00Z", by="hourly") for i in range(8)})
        incoming = {f"n{i}": job_entry(f"2026-10-2{i}T00:00:00Z") for i in range(4)}
        doc = intake.merge_jobs(cur, incoming, "hourly", NOW)
        self.assertEqual(len(doc["jobs"]), intake.KEEP_JOBS)
        self.assertNotIn("j00", doc["jobs"])
        self.assertNotIn("j01", doc["jobs"])
        self.assertIn("n3", doc["jobs"])

    def test_none_current_builds_doc(self):
        doc = intake.merge_jobs(None, {"a": job_entry("2026-10-29T02:00:00Z")}, "worker", NOW, studio="highlight")
        self.assertEqual(doc["studio"], "highlight")
        self.assertEqual(doc["label"], "Highlight Studio")
        self.assertEqual(doc["url"], intake.STUDIOS["highlight"]["url"])
        self.assertEqual(doc["checkedAt"], NOW.isoformat())
        self.assertEqual(doc["checkedBy"], "worker")

    def test_checked_at_bumps_even_with_nothing_new(self):
        doc = intake.merge_jobs(self.current(), {}, "hourly", NOW)
        self.assertEqual(doc["checkedAt"], NOW.isoformat())
        self.assertEqual(doc["jobs"], {})

    def test_malformed_raw_is_unknown_unreadable(self):
        for bad in ("just a string", {"status": "done", "outputs": 5, "updatedAt": 3}, {"status": {"ig": 1}, "schedule": "x"}):
            job = intake.safe_normalize("factory" if "ig" not in str(bad) else "desk", "bad", bad, NOW)
            self.assertEqual(job["status"], "unknown", bad)
            self.assertEqual(job["message"], "unreadable job", bad)


class TestContentWrites(unittest.TestCase):
    RAW = "factory-2026-10-29-redo-howlive.json"
    SINCE = "2026-10-29T00:00:00Z"

    def run_it(self, existing=(), since=SINCE, raw=None, studio="factory", job_id="2026-10-29-redo-howlive"):
        raw = raw or fixture(self.RAW)
        job = intake.normalize(studio, job_id, raw, NOW)
        cands = intake.outputs(studio, job_id, raw)
        return intake.content_writes(studio, job_id, job, cands, set(existing), since)

    def test_confirmed_job_after_since_makes_items(self):
        writes = self.run_it()
        self.assertEqual(len(writes), 2)
        w = writes[0]
        self.assertEqual((w["op"], w["collection"], w["doc_id"]), ("set", "content", "vf-cc-how-live-v"))
        self.assertNotIn("if_version", w)
        d = w["data"]
        self.assertEqual(d["id"], "vf-cc-how-live-v")
        self.assertEqual(d["type"], "video")
        self.assertEqual(d["kind"], "video")
        self.assertEqual(d["status"], "ready")
        self.assertEqual(d["channels"], [])
        self.assertEqual(d["media"], [{"file": d["studio"]["path"], "alt": d["title"]}])
        self.assertEqual(d["sourceArtifact"], intake.STUDIOS["factory"]["url"])
        self.assertEqual(d["studio"]["name"], "factory")
        self.assertEqual(d["studio"]["job"], "2026-10-29-redo-howlive")
        self.assertEqual(d["studio"]["orientation"], "v")
        self.assertEqual(d["studio"]["seconds"], fixture(self.RAW)["outputs"][0]["seconds"])
        self.assertIsNone(d["studio"]["clipDate"])
        self.assertEqual(d["by"], "studio")
        self.assertEqual(d["at"], "2026-10-29T22:10:54Z")
        self.assertEqual(d["createdAt"], "2026-10-29T22:10:54Z")
        self.assertIn("youtube", d["textByChannel"])
        self.assertTrue(d["text"])

    def test_existing_id_is_skipped(self):
        writes = self.run_it(existing=["vf-cc-how-live-v"])
        self.assertEqual([w["doc_id"] for w in writes], ["vf-cc-how-live-h"])

    def test_pending_job_makes_nothing(self):
        raw = dict(fixture(self.RAW), status="working", updatedAt=NOW.isoformat())
        self.assertEqual(self.run_it(raw=raw), [])

    def test_job_before_since_makes_nothing(self):
        self.assertEqual(self.run_it(since="2026-10-30T00:00:00Z"), [])

    def test_missing_since_makes_nothing(self):
        self.assertEqual(self.run_it(since=None), [])
        self.assertEqual(self.run_it(since=""), [])

    def test_highlight_old_clip_is_skipped(self):
        raw = fixture("highlight-2026-10-29-0ww4.json")
        raw["outputs"][0]["short"]["date"] = "2026-10-12"
        raw["outputs"][1]["short"]["date"] = "2026-10-14"
        writes = self.run_it(raw=raw, studio="highlight", job_id="2026-10-29-0ww4")
        self.assertEqual([w["doc_id"] for w in writes], ["hs-2026-10-29-webinar-part2"])
        self.assertEqual(writes[0]["data"]["studio"]["clipDate"], "2026-10-14")
        self.assertEqual(writes[0]["data"]["text"], writes[0]["data"]["title"])


class TestCheckin(unittest.TestCase):
    TASKS = {
        "content.evergreen": {"id": "content.evergreen", "kind": "recurring", "target": {"min": 4, "max": 6, "unit": "posts"}},
        "shorts.daily.clips": {"id": "shorts.daily.clips", "kind": "recurring"},
    }
    MAP = {"highlight": "shorts.daily.clips", "factory": "content.evergreen"}

    def job(self, studio="factory", status="confirmed", ended="2026-10-30T02:00:00Z", videos=2):
        return {"title": "Batch of Oct 29", "status": status, "endedAt": ended, "updatedAt": ended, "videos": videos}

    def test_pt_date_rolls_back_after_utc_midnight(self):
        self.assertEqual(intake.pt_date("2026-10-30T02:00:00Z"), "2026-10-29")
        self.assertEqual(intake.pt_date("2026-10-30T15:00:00Z"), "2026-10-30")

    def test_counter_task_gets_count(self):
        w = intake.checkin_write("factory", self.job(), self.MAP, self.TASKS, None)
        self.assertEqual((w["op"], w["collection"], w["doc_id"]), ("set", "days", "2026-10-29"))
        self.assertNotIn("if_version", w)
        self.assertEqual(w["data"]["date"], "2026-10-29")
        entry = w["data"]["done"]["content.evergreen"]
        self.assertEqual(entry, {"at": "2026-10-30T02:00:00Z", "by": "studio", "note": "Video Factory \u00b7 Batch of Oct 29",
                                 "link": intake.STUDIOS["factory"]["url"], "count": 2})
        self.assertEqual(list(w["data"]["done"]), ["content.evergreen"])

    def test_plain_task_has_no_count(self):
        w = intake.checkin_write("highlight", self.job("highlight"), self.MAP, self.TASKS, None)
        self.assertNotIn("count", w["data"]["done"]["shorts.daily.clips"])
        self.assertTrue(w["data"]["done"]["shorts.daily.clips"]["note"].startswith("Highlight Studio"))

    def test_existing_entry_is_never_changed(self):
        day = {"date": "2026-10-29", "done": {"content.evergreen": {"at": "x", "by": "matt", "count": 4}}}
        self.assertIsNone(intake.checkin_write("factory", self.job(), self.MAP, self.TASKS, day))

    def test_merges_into_existing_day(self):
        day = {"date": "2026-10-29", "done": {"platforms.check": {"at": "x", "by": "matt"}}}
        w = intake.checkin_write("factory", self.job(), self.MAP, self.TASKS, day)
        self.assertEqual(set(w["data"]["done"]), {"platforms.check", "content.evergreen"})
        self.assertEqual(w["data"]["done"]["platforms.check"], {"at": "x", "by": "matt"})

    def test_unmapped_studio_or_pending_job_gives_none(self):
        self.assertIsNone(intake.checkin_write("style", self.job("style"), self.MAP, self.TASKS, None))
        self.assertIsNone(intake.checkin_write("factory", self.job(status="pending", ended=None), self.MAP, self.TASKS, None))
        self.assertIsNone(intake.checkin_write("factory", self.job(status="failed"), self.MAP, self.TASKS, None))


if __name__ == "__main__":
    unittest.main()
