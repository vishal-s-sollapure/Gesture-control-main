"""
GestureControl AI - Unit Tests for Gesture Recognition & State Machine
Uses synthetic hand landmark positions to test landmark geometry, finger states,
pinch detection, open palm, fist, swipe history, and cooldown logic without real hardware.
"""

import time
import unittest
from config import DEFAULT_SETTINGS
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

    def test_detect_swipe(self):
        """Tests dynamic horizontal swipe detection over position history buffer."""
        now = time.time()
        # Simulate moving hand rapidly rightward (dx > 0.08)
        self.recognizer.position_history.append((now - 0.20, 0.30, 0.5))
        self.recognizer.position_history.append((now - 0.15, 0.35, 0.5))
        self.recognizer.position_history.append((now - 0.10, 0.40, 0.5))
        self.recognizer.position_history.append((now - 0.05, 0.45, 0.5))
        self.recognizer.position_history.append((now - 0.02, 0.50, 0.5))
        self.recognizer.position_history.append((now, 0.55, 0.5))

        swipe = self.recognizer._detect_swipe()
        self.assertEqual(swipe, "SWIPE_RIGHT")

    def test_gesture_cooldown(self):
        """Tests that state machine respects frame confirmation and cooldown intervals."""
        # Frame 1: RIGHT_CLICK -> Requires 3 frames to confirm
        g1, trig1, cd_act1, cd_rem1 = self.recognizer.process_state_machine("RIGHT_CLICK", 0.9)
        self.assertFalse(trig1)

        # Frame 2: RIGHT_CLICK
        g2, trig2, cd_act2, cd_rem2 = self.recognizer.process_state_machine("RIGHT_CLICK", 0.9)
        self.assertFalse(trig2)

        # Frame 3: RIGHT_CLICK -> Confirmed and triggered!
        g3, trig3, cd_act3, cd_rem3 = self.recognizer.process_state_machine("RIGHT_CLICK", 0.9)
        self.assertTrue(trig3)

        # Instant frame 4: RIGHT_CLICK -> Ignored due to active cooldown
        g4, trig4, cd_act4, cd_rem4 = self.recognizer.process_state_machine("RIGHT_CLICK", 0.9)
        self.assertFalse(trig4)
        self.assertTrue(cd_act4)


if __name__ == "__main__":
    unittest.main()
