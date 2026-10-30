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


if __name__ == "__main__":
    unittest.main()
