"""
GestureControl AI - Performance & Metrics Collector Module
Tracks real-time system performance, frame statistics, gesture classification metrics,
latency, false trigger rates, and session durations without synthetic numbers.
"""

import time
from typing import Dict, Any


class MetricsCollector:
    """
    Thread-safe runtime metrics collector for system performance monitoring.
    Calculates empirical stats: FPS, hand detection rate, confirmed vs rejected gestures,
    and average gesture response latency.
    """

    def __init__(self):
        self.session_start_time = time.time()
        self.total_frames = 0
        self.frames_with_hand = 0
        self.confirmed_gestures = 0
        self.rejected_gestures = 0
        self.gesture_counts: Dict[str, int] = {}
        self.latencies_ms: list = []

        # Windowed FPS computation
        self.fps_frame_count = 0
        self.fps_last_time = time.time()
        self.current_fps = 0.0

    def record_frame(self, hand_detected: bool, processing_time_ms: float = 0.0):
        """
        Record frame processing result.
        """
        self.total_frames += 1
        if hand_detected:
            self.frames_with_hand += 1

        if processing_time_ms > 0:
            self.latencies_ms.append(processing_time_ms)
            if len(self.latencies_ms) > 100:
                self.latencies_ms.pop(0)

        # Update FPS window
        self.fps_frame_count += 1
        now = time.time()
        elapsed = now - self.fps_last_time
        if elapsed >= 1.0:
            self.current_fps = round(self.fps_frame_count / elapsed, 1)
            self.fps_frame_count = 0
            self.fps_last_time = now

    def record_gesture(self, gesture_name: str, confirmed: bool, confidence: float = 1.0):
        """
        Record classified gesture event.
        """
        if gesture_name in ("IDLE", "UNKNOWN"):
            return

        if confirmed:
            self.confirmed_gestures += 1
            self.gesture_counts[gesture_name] = self.gesture_counts.get(gesture_name, 0) + 1
        else:
            self.rejected_gestures += 1

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Returns snapshot dictionary of calculated empirical performance metrics.
        """
        now = time.time()
        session_duration = max(0.1, now - self.session_start_time)
        detection_rate = (self.frames_with_hand / max(1, self.total_frames)) * 100.0
        avg_fps = self.total_frames / session_duration

        total_trials = self.confirmed_gestures + self.rejected_gestures
        false_trigger_rate = (self.rejected_gestures / max(1, total_trials)) * 100.0

        avg_latency = (
            sum(self.latencies_ms) / len(self.latencies_ms) if self.latencies_ms else 0.0
        )

        return {
            "session_duration_sec": round(session_duration, 1),
            "total_frames": self.total_frames,
            "frames_with_hand": self.frames_with_hand,
            "detection_rate_pct": round(detection_rate, 1),
            "current_fps": self.current_fps,
            "average_fps": round(avg_fps, 1),
            "confirmed_gestures": self.confirmed_gestures,
            "rejected_gestures": self.rejected_gestures,
            "false_trigger_rate_pct": round(false_trigger_rate, 1),
            "avg_response_ms": round(avg_latency, 1),
            "gesture_counts": self.gesture_counts.copy()
        }

    def reset_session(self):
        """
        Resets all counters for a new benchmark session.
        """
        self.session_start_time = time.time()
        self.total_frames = 0
        self.frames_with_hand = 0
        self.confirmed_gestures = 0
        self.rejected_gestures = 0
        self.gesture_counts.clear()
        self.latencies_ms.clear()
        self.fps_frame_count = 0
        self.fps_last_time = time.time()
        self.current_fps = 0.0
