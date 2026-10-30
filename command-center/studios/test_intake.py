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


if __name__ == "__main__":
    unittest.main()
