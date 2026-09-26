"""
GestureControl AI - Unit Tests for Performance Metrics Collector
"""

import unittest
from core.metrics import MetricsCollector


class TestMetrics(unittest.TestCase):

    def setUp(self):
        self.mc = MetricsCollector()

    def test_record_frames(self):
        """Record 10 frames with 8 hand detections."""
        for i in range(10):
            hand_found = (i < 8)
            self.mc.record_frame(hand_detected=hand_found, processing_time_ms=10.0)

        stats = self.mc.get_session_stats()
        self.assertEqual(stats["total_frames"], 10)
        self.assertEqual(stats["frames_with_hand"], 8)
        self.assertEqual(stats["detection_rate_pct"], 80.0)

    def test_gesture_confirmation_and_rejection(self):
        """Test confirmed vs rejected gesture metrics."""
        self.mc.record_gesture("PINCH", confirmed=True)
        self.mc.record_gesture("PINCH", confirmed=True)
        self.mc.record_gesture("SWIPE_LEFT", confirmed=False)

        stats = self.mc.get_session_stats()
        self.assertEqual(stats["confirmed_gestures"], 2)
        self.assertEqual(stats["rejected_gestures"], 1)

    def test_reset_session(self):
        """Resetting clears all counters."""
        self.mc.record_frame(True, 15.0)
        self.mc.record_gesture("PINCH", True)

        self.mc.reset_session()
        stats = self.mc.get_session_stats()
        self.assertEqual(stats["total_frames"], 0)
        self.assertEqual(stats["confirmed_gestures"], 0)


if __name__ == "__main__":
    unittest.main()
