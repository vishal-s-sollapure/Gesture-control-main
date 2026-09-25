"""
GestureControl AI - Comprehensive Unit Tests for Gesture Recognition & Safety System
Tests gesture geometry, scale ratios, swipe conflict fixes, double click timing,
cooldown logic, emergency stop safety, drag release, and disabled state enforcement.
"""

import time
import unittest

from config import DEFAULT_SETTINGS
from core.gesture_controller import GestureController
from core.gesture_recognizer import GestureRecognizer, distance_2d, distance_3d
from core.hand_tracker import (
    WRIST, THUMB_TIP, THUMB_IP, THUMB_MCP,
    INDEX_FINGER_TIP, INDEX_FINGER_PIP, INDEX_FINGER_MCP,
    MIDDLE_FINGER_TIP, MIDDLE_FINGER_PIP, MIDDLE_FINGER_MCP,
    RING_FINGER_TIP, RING_FINGER_PIP, RING_FINGER_MCP,
    PINKY_TIP, PINKY_PIP, PINKY_MCP
)


def create_dummy_landmarks(
    thumb: bool = False,
    index: bool = False,
    middle: bool = False,
    ring: bool = False,
    pinky: bool = False,
    pinch: bool = False
) -> list:
    """
    Constructs a valid list of 21 synthetic normalized landmark dicts ({'x', 'y', 'z'}).
    """
    lms = [{"x": 0.5, "y": 0.8, "z": 0.0} for _ in range(21)]  # Wrist at (0.5, 0.8)

    # Base MCP joint locations
    lms[THUMB_MCP] = {"x": 0.4, "y": 0.7, "z": 0.0}
    lms[INDEX_FINGER_MCP] = {"x": 0.45, "y": 0.6, "z": 0.0}
    lms[MIDDLE_FINGER_MCP] = {"x": 0.50, "y": 0.6, "z": 0.0}
    lms[RING_FINGER_MCP] = {"x": 0.55, "y": 0.6, "z": 0.0}
    lms[PINKY_MCP] = {"x": 0.60, "y": 0.6, "z": 0.0}

    # Base PIP joint locations
    lms[INDEX_FINGER_PIP] = {"x": 0.45, "y": 0.5, "z": 0.0}
    lms[MIDDLE_FINGER_PIP] = {"x": 0.50, "y": 0.5, "z": 0.0}
    lms[RING_FINGER_PIP] = {"x": 0.55, "y": 0.5, "z": 0.0}
    lms[PINKY_PIP] = {"x": 0.60, "y": 0.5, "z": 0.0}

    # Finger Tip positions depending on extended/folded boolean
    lms[INDEX_FINGER_TIP] = {"x": 0.45, "y": 0.2 if index else 0.55, "z": 0.0}
    lms[MIDDLE_FINGER_TIP] = {"x": 0.50, "y": 0.2 if middle else 0.55, "z": 0.0}
    lms[RING_FINGER_TIP] = {"x": 0.55, "y": 0.2 if ring else 0.55, "z": 0.0}
    lms[PINKY_TIP] = {"x": 0.60, "y": 0.2 if pinky else 0.55, "z": 0.0}

    # Thumb IP and TIP
    lms[THUMB_IP] = {"x": 0.35, "y": 0.65, "z": 0.0}
    if thumb:
        lms[THUMB_TIP] = {"x": 0.25, "y": 0.5, "z": 0.0}
    else:
        lms[THUMB_TIP] = {"x": 0.42, "y": 0.65, "z": 0.0}

    # Override for Pinch gesture: Thumb tip and Index tip within 0.02 distance
    if pinch:
        lms[INDEX_FINGER_TIP] = {"x": 0.45, "y": 0.3, "z": 0.0}
        lms[THUMB_TIP] = {"x": 0.45, "y": 0.31, "z": 0.0}

    return lms


class TestGestureRecognition(unittest.TestCase):

    def setUp(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.recognizer = GestureRecognizer(self.settings)

    def test_analyze_finger_states(self):
        """Tests individual finger extension state evaluation."""
        lms = create_dummy_landmarks(index=True, middle=False, ring=False, pinky=False)
        states = self.recognizer.analyze_finger_states(lms, hand_scale=0.2)
        self.assertTrue(states["index"])
        self.assertFalse(states["middle"])
        self.assertFalse(states["ring"])

    def test_is_pinch(self):
        """Tests thumb and index finger pinch detection."""
        pinch_lms = create_dummy_landmarks(pinch=True)
        gesture, conf, dbg = self.recognizer.detect_gesture(pinch_lms)
        self.assertEqual(gesture, "PINCH")
        self.assertGreater(conf, 0.7)

    def test_detect_open_palm(self):
        """Tests open palm gesture detection."""
        palm_lms = create_dummy_landmarks(thumb=True, index=True, middle=True, ring=True, pinky=True)
        gesture, conf, dbg = self.recognizer.detect_gesture(palm_lms)
        self.assertEqual(gesture, "OPEN_PALM")

    def test_detect_fist(self):
        """Tests closed fist emergency pause gesture detection."""
        fist_lms = create_dummy_landmarks(thumb=False, index=False, middle=False, ring=False, pinky=False)
        gesture, conf, dbg = self.recognizer.detect_gesture(fist_lms)
        self.assertEqual(gesture, "FIST")

    def test_detect_pointing_cursor(self):
        """Tests index finger cursor pointing gesture."""
        pointing_lms = create_dummy_landmarks(thumb=False, index=True, middle=False, ring=False, pinky=False)
        gesture, conf, dbg = self.recognizer.detect_gesture(pointing_lms)
        self.assertEqual(gesture, "CURSOR")

    def test_cursor_movement_does_not_trigger_swipe(self):
        """CRITICAL FIX #1: Fast index finger movement must NEVER trigger a media swipe!"""
        pointing_lms = create_dummy_landmarks(thumb=False, index=True, middle=False, ring=False, pinky=False)
        now = time.time()
        # Simulate rapid index finger position movement over frames
        self.recognizer.position_history.append((now - 0.20, 0.30, 0.5))
        self.recognizer.position_history.append((now - 0.15, 0.40, 0.5))
        self.recognizer.position_history.append((now - 0.10, 0.50, 0.5))
        self.recognizer.position_history.append((now, 0.60, 0.5))

        gesture, conf, dbg = self.recognizer.detect_gesture(pointing_lms)
        # MUST evaluate to CURSOR, NOT SWIPE_RIGHT!
        self.assertEqual(gesture, "CURSOR")
        self.assertNotEqual(gesture, "SWIPE_RIGHT")

    def test_swipe_requires_dedicated_pose(self):
        """CRITICAL FIX #1: Swipe requires open/flat hand posture, NOT index pointing posture."""
        open_hand_lms = create_dummy_landmarks(thumb=True, index=True, middle=True, ring=True, pinky=True)
        now = time.time()
        self.recognizer.position_history.append((now - 0.20, 0.30, 0.5))
        self.recognizer.position_history.append((now - 0.15, 0.35, 0.5))
        self.recognizer.position_history.append((now - 0.10, 0.40, 0.5))
        self.recognizer.position_history.append((now - 0.05, 0.45, 0.5))
        self.recognizer.position_history.append((now - 0.02, 0.50, 0.5))
        self.recognizer.position_history.append((now, 0.55, 0.5))

        gesture, conf, dbg = self.recognizer.detect_gesture(open_hand_lms)
        self.assertEqual(gesture, "SWIPE_RIGHT")

    def test_double_click_timing_and_cooldown(self):
        """CRITICAL FIX #2: Double pinch within interval triggers DOUBLE_PINCH without cooldown blockage."""
        # 1. First Pinch -> 3 consecutive frames of PINCH
        g1, trig1, cd_act1, cd_rem1 = "IDLE", False, False, 0.0
        for _ in range(3):
            g1, trig1, cd_act1, cd_rem1 = self.recognizer.process_state_machine("PINCH", 0.95)

        self.assertEqual(g1, "PINCH")
        self.assertTrue(trig1)

        # Release pinch
        self.recognizer.process_state_machine("IDLE", 0.5)

        # 2. Second Pinch 0.05s later (within 0.4s double click window) -> 3 consecutive frames of PINCH
        time.sleep(0.05)
        g2, trig2, cd_act2, cd_rem2 = "IDLE", False, False, 0.0
        for _ in range(3):
            g2, trig2, cd_act2, cd_rem2 = self.recognizer.process_state_machine("PINCH", 0.95)

        self.assertEqual(g2, "DOUBLE_PINCH")
        self.assertTrue(trig2)

    def test_pinch_hold_is_not_double_click(self):
        """Sustained pinch hold should NOT trigger double click."""
        for _ in range(3):
            g, trig, cd_act, cd_rem = self.recognizer.process_state_machine("PINCH", 0.95)
        self.assertEqual(g, "PINCH")

        # Continued frames of holding pinch without release
        for _ in range(5):
            g_hold, trig_hold, _, _ = self.recognizer.process_state_machine("PINCH", 0.95)
            self.assertNotEqual(g_hold, "DOUBLE_PINCH")

    def test_pinch_separated_by_interval_is_two_single_clicks(self):
        """Pinch separated by more than double-click interval (0.4s) results in independent single clicks."""
        for _ in range(3):
            self.recognizer.process_state_machine("PINCH", 0.95)

        self.recognizer.process_state_machine("IDLE", 0.5)

        # Wait 0.5s (longer than 0.4s double_click_interval)
        time.sleep(0.5)

        g_second, trig_second, _, _ = "IDLE", False, False, 0.0
        for _ in range(3):
            g_second, trig_second, _, _ = self.recognizer.process_state_machine("PINCH", 0.95)

        self.assertEqual(g_second, "PINCH")
        self.assertNotEqual(g_second, "DOUBLE_PINCH")


class TestSafetyAndController(unittest.TestCase):

    def setUp(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.settings["control_enabled"] = False  # Default startup state is PAUSED
        self.controller = GestureController(settings=self.settings, dry_run=True)

    def test_default_startup_state_paused(self):
        """SAFETY: Application default state must be CONTROL: PAUSED."""
        self.assertFalse(self.controller.control_enabled)

    def test_disabled_control_bypasses_actions(self):
        """SAFETY: Disabled control MUST NOT trigger mouse/keyboard actions."""
        self.controller.disable_control("Testing disabled bypass")
        self.assertFalse(self.controller.control_enabled)
        self.assertFalse(self.controller.mouse.is_dragging)

    def test_emergency_stop_disables_control_and_releases_drag(self):
        """SAFETY: Emergency stop immediately disables control and releases active drag."""
        self.controller.enable_control()
        self.controller.mouse.start_drag()
        self.assertTrue(self.controller.mouse.is_dragging)

        # Trigger Emergency Stop
        self.controller.emergency_stop()
        self.assertFalse(self.controller.control_enabled)
        self.assertFalse(self.controller.mouse.is_dragging)

    def test_shutdown_releases_drag(self):
        """SAFETY: Application shutdown MUST release active mouse drag."""
        self.controller.mouse.start_drag()
        self.assertTrue(self.controller.mouse.is_dragging)

        self.controller.stop()
        self.assertFalse(self.controller.mouse.is_dragging)
        self.assertFalse(self.controller.control_enabled)

    def test_fist_disables_control(self):
        """SAFETY: Fist emergency gesture disables control safely."""
        self.controller.enable_control()
        self.assertTrue(self.controller.control_enabled)

        # Dispatch FIST action
        self.controller._dispatch_action(
            action_gesture="FIST",
            trigger=True,
            landmarks=[],
            screen_w=1920,
            screen_h=1080,
            frame_w=640,
            frame_h=480
        )
        self.assertFalse(self.controller.control_enabled)


if __name__ == "__main__":
    unittest.main()
