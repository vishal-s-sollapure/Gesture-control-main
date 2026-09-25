"""
GestureControl AI - Gesture Recognizer Module
Implements scale-invariant landmark geometry, finger state detection, priority-based
conflict elimination, dedicated swipe posture checking, decoupled double-click timing,
genuine confidence scoring, and debug state data.
"""

from collections import deque
import math
import time
from typing import Dict, List, Optional, Tuple

from core.hand_tracker import (
    WRIST, THUMB_TIP, THUMB_IP, THUMB_MCP,
    INDEX_FINGER_TIP, INDEX_FINGER_PIP, INDEX_FINGER_MCP,
    MIDDLE_FINGER_TIP, MIDDLE_FINGER_PIP, MIDDLE_FINGER_MCP,
    RING_FINGER_TIP, RING_FINGER_PIP, RING_FINGER_MCP,
    PINKY_TIP, PINKY_PIP, PINKY_MCP
)
from utils.logger import setup_logger

logger = setup_logger("GestureRecognizer")


def distance_3d(p1: dict, p2: dict) -> float:
    """Calculates 3D Euclidean distance between two normalized landmark points."""
    return math.sqrt(
        (p1["x"] - p2["x"]) ** 2 +
        (p1["y"] - p2["y"]) ** 2 +
        (p1["z"] - p2["z"]) ** 2
    )


def distance_2d(p1: dict, p2: dict) -> float:
    """Calculates 2D Euclidean distance between two normalized landmark points."""
    return math.hypot(p1["x"] - p2["x"], p1["y"] - p2["y"])


class GestureRecognizer:
    """
    Analyzes 21 3D hand landmark coordinates to infer hand gestures, eliminate gesture conflicts,
    compute scale-invariant metrics, genuine confidence scores, and enforce temporal stability.
    """

    def __init__(self, settings: dict):
        self.settings = settings

        # Timing Memory
        self.last_action_time = 0.0
        self.last_pinch_time = 0.0
        self.is_pinching = False

        # Swipe tracking history: deques storing (timestamp, normalized_wrist_x, normalized_wrist_y)
        self.position_history = deque(maxlen=settings.get("swipe_frames", 6))

        # Temporal stability frame consistency memory
        self.prev_raw_gesture = "IDLE"
        self.gesture_frame_count = 0
        self.required_confirm_frames = 3  # Must hold gesture for 3 frames before confirming

        # Debug & Diagnostic snapshot
        self.latest_debug_info = {}

    def update_settings(self, new_settings: dict):
        """Updates internal thresholds from configuration."""
        self.settings = new_settings

    def analyze_finger_states(self, landmarks: List[dict], hand_scale: float) -> Dict[str, bool]:
        """
        Determines extension state (True = Extended, False = Folded) for all 5 fingers
        using scale-invariant joint distances and vector positions.
        """
        if not landmarks or len(landmarks) < 21:
            return {"thumb": False, "index": False, "middle": False, "ring": False, "pinky": False}

        wrist = landmarks[WRIST]

        # Finger extension rule: Tip distance from wrist vs PIP distance from wrist
        def is_finger_extended(tip_idx: int, pip_idx: int, mcp_idx: int) -> bool:
            dist_tip = distance_3d(landmarks[tip_idx], wrist)
            dist_pip = distance_3d(landmarks[pip_idx], wrist)

            extended_dist = dist_tip > dist_pip * 1.12
            extended_mcp = distance_3d(landmarks[tip_idx], landmarks[mcp_idx]) > distance_3d(landmarks[pip_idx], landmarks[mcp_idx]) * 1.15
            return extended_dist and extended_mcp

        thumb_tip = landmarks[THUMB_TIP]
        thumb_mcp = landmarks[THUMB_MCP]
        pinky_mcp = landmarks[PINKY_MCP]

        thumb_extended = distance_3d(thumb_tip, pinky_mcp) > distance_3d(thumb_mcp, pinky_mcp) * 1.18

        index_extended = is_finger_extended(INDEX_FINGER_TIP, INDEX_FINGER_PIP, INDEX_FINGER_MCP)
        middle_extended = is_finger_extended(MIDDLE_FINGER_TIP, MIDDLE_FINGER_PIP, MIDDLE_FINGER_MCP)
        ring_extended = is_finger_extended(RING_FINGER_TIP, RING_FINGER_PIP, RING_FINGER_MCP)
        pinky_extended = is_finger_extended(PINKY_TIP, PINKY_PIP, PINKY_MCP)

        return {
            "thumb": thumb_extended,
            "index": index_extended,
            "middle": middle_extended,
            "ring": ring_extended,
            "pinky": pinky_extended
        }

    def detect_gesture(self, landmarks: List[dict]) -> Tuple[str, float, dict]:
        """
        Identifies active gesture using strict priority rules to prevent gesture conflicts.
        Computes scale-invariant metrics and genuine confidence scores.

        :param landmarks: List of 21 landmark dicts ({'x', 'y', 'z'})
        :return: Tuple of (gesture_name: str, confidence_score: float, debug_info: dict)
        """
        if not landmarks or len(landmarks) < 21:
            return "IDLE", 0.0, {}

        wrist = landmarks[WRIST]
        middle_mcp = landmarks[MIDDLE_FINGER_MCP]

        # Calculate scale-invariant hand size metric (wrist to middle finger MCP distance)
        hand_scale = distance_2d(wrist, middle_mcp)
        if hand_scale < 1e-4:
            hand_scale = 0.1  # Prevent divide by zero

        fingers = self.analyze_finger_states(landmarks, hand_scale)

        # Pinch distance relative to hand scale (scale-invariant)
        raw_pinch_dist = distance_2d(landmarks[THUMB_TIP], landmarks[INDEX_FINGER_TIP])
        pinch_ratio = raw_pinch_dist / hand_scale

        # Scale-relative pinch ratio threshold (~0.25 is pinch, >0.40 is open)
        pinch_thresh_ratio = self.settings.get("pinch_threshold", 0.045) / 0.18

        thumb_tip = landmarks[THUMB_TIP]
        thumb_ip = landmarks[THUMB_IP]

        # Index finger pointing posture evaluation
        pointing_index = (
            fingers["index"] and
            not fingers["middle"] and
            not fingers["ring"] and
            not fingers["pinky"]
        )

        # Track wrist position over time for dynamic swipe detection
        now = time.time()
        self.position_history.append((now, wrist["x"], wrist["y"]))

        enabled = self.settings.get("enabled_gestures", {})

        # -------------------------------------------------------------
        # STRICT PRIORITY CHAIN TO PREVENT GESTURE CONFLICTS
        # -------------------------------------------------------------

        # PRIORITY 1: CLOSED FIST (Emergency Pause Control)
        folded_count = sum(1 for f in ["index", "middle", "ring", "pinky"] if not fingers[f])
        fist_tip_dist = sum(distance_2d(landmarks[tip], wrist) for tip in [INDEX_FINGER_TIP, MIDDLE_FINGER_TIP, RING_FINGER_TIP, PINKY_TIP]) / 4.0
        fist_ratio = fist_tip_dist / hand_scale

        is_fist = (folded_count == 4) and (fist_ratio < 1.35)
        if is_fist and enabled.get("emergency_fist", True):
            conf = max(0.70, min(0.99, 1.0 - (fist_ratio / 1.35) * 0.3))
            debug_data = self._make_debug(landmarks, fingers, pinch_ratio, hand_scale, "FIST", conf)
            return "FIST", round(conf, 2), debug_data

        # PRIORITY 2: DEDICATED SWIPE DETECTION (Critical Fix #1)
        # CRITICAL SAFETY REQUIREMENT: Normal index-finger cursor movement MUST NEVER trigger swipe!
        # Swipe is ONLY evaluated if pointing_index is False and hand is in an open/flat posture!
        open_or_flat_posture = (fingers["index"] and fingers["middle"]) or (fingers["index"] and fingers["ring"])
        if not pointing_index and open_or_flat_posture:
            swipe_detected = self._detect_swipe()
            if swipe_detected == "SWIPE_LEFT" and enabled.get("prev_track", True):
                debug_data = self._make_debug(landmarks, fingers, pinch_ratio, hand_scale, "SWIPE_LEFT", 0.92)
                return "SWIPE_LEFT", 0.92, debug_data
            elif swipe_detected == "SWIPE_RIGHT" and enabled.get("next_track", True):
                debug_data = self._make_debug(landmarks, fingers, pinch_ratio, hand_scale, "SWIPE_RIGHT", 0.92)
                return "SWIPE_RIGHT", 0.92, debug_data

        # PRIORITY 3: PINCH / DRAG / DOUBLE PINCH
        if pinch_ratio < pinch_thresh_ratio:
            conf = max(0.75, min(0.99, 1.0 - (pinch_ratio / pinch_thresh_ratio) * 0.4))
            if enabled.get("drag_and_drop", True) and self.is_pinching:
                debug_data = self._make_debug(landmarks, fingers, pinch_ratio, hand_scale, "DRAG", conf)
                return "DRAG", round(conf, 2), debug_data
            elif enabled.get("left_click", True) or enabled.get("double_click", True):
                debug_data = self._make_debug(landmarks, fingers, pinch_ratio, hand_scale, "PINCH", conf)
                return "PINCH", round(conf, 2), debug_data

        # PRIORITY 4: THUMBS UP (Play/Pause Media)
        thumbs_up_orientation = (thumb_tip["y"] < thumb_ip["y"] - 0.03) and (thumb_tip["y"] < wrist["y"] - 0.1)
        is_thumbs_up = (
            fingers["thumb"] and
            thumbs_up_orientation and
            not fingers["index"] and
            not fingers["middle"] and
            not fingers["ring"] and
            not fingers["pinky"]
        )
        if is_thumbs_up and enabled.get("media_play_pause", True):
            conf = 0.94
            debug_data = self._make_debug(landmarks, fingers, pinch_ratio, hand_scale, "THUMBS_UP", conf)
            return "THUMBS_UP", conf, debug_data

        # PRIORITY 5: OPEN PALM (Scroll Gesture)
        all_extended = fingers["thumb"] and fingers["index"] and fingers["middle"] and fingers["ring"] and fingers["pinky"]
        if all_extended and pinch_ratio > pinch_thresh_ratio * 1.4 and enabled.get("scroll", True):
            conf = 0.91
            debug_data = self._make_debug(landmarks, fingers, pinch_ratio, hand_scale, "OPEN_PALM", conf)
            return "OPEN_PALM", conf, debug_data

        # PRIORITY 6: TWO FINGERS (Right Click)
        two_fingers = (
            fingers["index"] and
            fingers["middle"] and
            not fingers["ring"] and
            not fingers["pinky"] and
            pinch_ratio > pinch_thresh_ratio * 1.3
        )
        if two_fingers and enabled.get("right_click", True):
            conf = 0.92
            debug_data = self._make_debug(landmarks, fingers, pinch_ratio, hand_scale, "RIGHT_CLICK", conf)
            return "RIGHT_CLICK", conf, debug_data

        # PRIORITY 7: INDEX POINTING (Cursor Movement)
        if pointing_index and enabled.get("cursor_movement", True):
            index_dist = distance_3d(landmarks[INDEX_FINGER_TIP], wrist)
            middle_dist = distance_3d(landmarks[MIDDLE_FINGER_TIP], wrist)
            ratio = index_dist / (middle_dist + 1e-6)
            conf = max(0.70, min(0.98, (ratio - 1.0) * 0.8 + 0.70))
            debug_data = self._make_debug(landmarks, fingers, pinch_ratio, hand_scale, "CURSOR", conf)
            return "CURSOR", round(conf, 2), debug_data

        debug_data = self._make_debug(landmarks, fingers, pinch_ratio, hand_scale, "IDLE", 0.5)
        return "IDLE", 0.5, debug_data

    def _detect_swipe(self) -> Optional[str]:
        """
        Analyzes position history deque for rapid horizontal swipe movement.
        """
        if len(self.position_history) < self.position_history.maxlen:
            return None

        t_start, x_start, _ = self.position_history[0]
        t_end, x_end, _ = self.position_history[-1]

        dt = t_end - t_start
        dx = x_end - x_start

        if dt > 0.35 or dt <= 0.0:
            return None

        swipe_thresh = self.settings.get("swipe_threshold", 0.08)

        if dx > swipe_thresh:
            self.position_history.clear()
            return "SWIPE_RIGHT"
        elif dx < -swipe_thresh:
            self.position_history.clear()
            return "SWIPE_LEFT"

        return None

    def process_state_machine(self, raw_gesture: str, confidence: float) -> Tuple[str, bool, bool, float]:
        """
        Filters raw gestures through temporal state machine:
        - Consecutive frame consistency confirmation (3 frames required for discrete actions)
        - Decoupled double-click timing (Critical Fix #2)
        - Cooldown timer after actions

        :return: Tuple of (actionable_gesture: str, trigger_flag: bool, cooldown_active: bool, cooldown_remaining: float)
        """
        now = time.time()
        cooldown = self.settings.get("gesture_cooldown", 0.50)
        double_click_interval = self.settings.get("double_click_interval", 0.40)

        time_since_last = now - self.last_action_time
        cooldown_active = time_since_last < cooldown
        cooldown_remaining = max(0.0, cooldown - time_since_last) if cooldown_active else 0.0

        # Update pinch release memory IMMEDIATELY regardless of frame counter exit
        if raw_gesture != "PINCH" and raw_gesture != "DRAG":
            self.is_pinching = False

        # Frame consistency counter update
        if raw_gesture == self.prev_raw_gesture:
            self.gesture_frame_count += 1
        else:
            self.gesture_frame_count = 1
            self.prev_raw_gesture = raw_gesture

        is_continuous = raw_gesture in ["CURSOR", "DRAG", "OPEN_PALM"]
        required_frames = 1 if is_continuous else self.required_confirm_frames

        if self.gesture_frame_count < required_frames:
            return "IDLE", False, cooldown_active, round(cooldown_remaining, 2)

        confirmed_gesture = raw_gesture

        # Continuous actions bypass discrete action cooldown
        if is_continuous:
            return confirmed_gesture, True, False, 0.0

        # -------------------------------------------------------------
        # CRITICAL FIX #2 — DECOUPLED DOUBLE CLICK vs COOLDOWN TIMING
        # -------------------------------------------------------------
        if confirmed_gesture == "PINCH":
            if not self.is_pinching:
                self.is_pinching = True
                time_since_last_pinch = now - self.last_pinch_time

                if time_since_last_pinch < double_click_interval and self.last_pinch_time > 0:
                    # Second pinch within double-click window -> TRIGGER DOUBLE CLICK
                    self.last_action_time = now
                    self.last_pinch_time = 0.0
                    return "DOUBLE_PINCH", True, True, cooldown
                else:
                    # First pinch -> TRIGGER SINGLE LEFT CLICK
                    self.last_pinch_time = now
                    self.last_action_time = now
                    return "PINCH", True, True, cooldown
            return "PINCH", False, False, 0.0

        # Discrete actions (RIGHT_CLICK, THUMBS_UP, SWIPE_LEFT, SWIPE_RIGHT, FIST)
        if cooldown_active:
            return confirmed_gesture, False, True, round(cooldown_remaining, 2)

        if confirmed_gesture in ["RIGHT_CLICK", "THUMBS_UP", "SWIPE_LEFT", "SWIPE_RIGHT", "FIST"]:
            self.last_action_time = now
            return confirmed_gesture, True, True, cooldown

        return confirmed_gesture, False, False, 0.0

    def _make_debug(
        self,
        landmarks: list,
        fingers: dict,
        pinch_ratio: float,
        hand_scale: float,
        raw_gesture: str,
        confidence: float
    ) -> dict:
        """Constructs debug state snapshot dictionary."""
        return {
            "landmarks_count": len(landmarks),
            "fingers": fingers,
            "pinch_ratio": round(pinch_ratio, 3),
            "hand_scale": round(hand_scale, 3),
            "raw_gesture": raw_gesture,
            "confidence": round(confidence, 2)
        }
