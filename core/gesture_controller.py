"""
GestureControl AI - Core Controller Module
Coordinates webcam capture, hand landmark tracking, gesture state machine,
cursor smoothing, safety checks, HUD overlay, debug mode, and system action execution.
"""

import threading
import time
from typing import Dict, Optional, Tuple
import cv2
import numpy as np

from config import GESTURE_NAMES
from core.camera import Camera
from core.calibration import CalibrationManager
from core.evaluation import EvaluationEngine
from core.gesture_recognizer import GestureRecognizer, distance_3d
from core.hand_tracker import HandTracker, INDEX_FINGER_TIP, WRIST, THUMB_TIP
from core.metrics import MetricsCollector
from core.profiles import ProfileManager
from controls.keyboard_controller import KeyboardController
from controls.media_controller import MediaController
from controls.mouse_controller import MouseController
from utils.logger import setup_logger, log_ui
from utils.smoothing import ExponentialSmoother, map_camera_to_screen, apply_dead_zone

logger = setup_logger("GestureController")

# Human-readable action names per gesture
GESTURE_ACTION_NAMES = {
    "CURSOR": "Cursor Movement",
    "PINCH": "Left Mouse Click",
    "RIGHT_CLICK": "Right Mouse Click",
    "OPEN_PALM": "Scroll Up / Down",
    "DRAG": "Drag & Drop",
    "DOUBLE_PINCH": "Double Click",
    "THUMBS_UP": "Media Play / Pause",
    "SWIPE_LEFT": "Previous Track",
    "SWIPE_RIGHT": "Next Track",
    "FIST": "Gesture Control Disabled",
    "IDLE": "Waiting for hand...",
    "UNKNOWN": "Waiting for hand..."
}


class GestureController:
    """
    Main controller linking hardware feed, computer vision recognition, and system input actions.
    """

    def __init__(self, settings: dict, dry_run: bool = False):
        self.settings = settings
        self.dry_run = dry_run
        self.control_enabled = settings.get("control_enabled", False)

        # Core Modules
        self.camera = Camera(
            camera_index=settings.get("camera_index", 0),
            width=settings.get("camera_width", 640),
            height=settings.get("camera_height", 480),
            target_fps=settings.get("camera_fps", 30)
        )
        self.hand_tracker = HandTracker(
            max_num_hands=1,
            min_detection_confidence=settings.get("confidence_threshold", 0.7),
            min_tracking_confidence=settings.get("confidence_threshold", 0.7)
        )
        self.recognizer = GestureRecognizer(settings)

        # Performance Metrics, Calibration, Evaluation, and Profiles Engines
        self.metrics = MetricsCollector()
        self.calibration = CalibrationManager()
        self.evaluation = EvaluationEngine()
        self.profile_mgr = ProfileManager(active_profile=settings.get("active_profile", "Desktop"))

        # Controllers
        self.mouse = MouseController(dry_run=self.dry_run)
        self.keyboard = KeyboardController(dry_run=self.dry_run)
        self.media = MediaController(dry_run=self.dry_run)

        # Cursor Smoothing & Coordinate Mapping State
        self.smoother = ExponentialSmoother(factor=settings.get("smoothing", 0.75))
        self.prev_screen_x = None
        self.prev_screen_y = None
        self.prev_scroll_y = None

        # Threading & Status State
        self.running = False
        self.process_thread: Optional[threading.Thread] = None

        self.current_gesture = "IDLE"
        self.raw_gesture = "IDLE"
        self.current_confidence = 0.0
        self.hand_count = 0
        self.cooldown_active = False
        self.cooldown_remaining = 0.0
        self.latest_debug_info = {}

        self.processed_frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()

        self.active_profile = settings.get("active_profile", "Desktop")

    def update_settings(self, new_settings: dict):
        """Dynamic configuration update handler."""
        self.settings = new_settings
        self.active_profile = new_settings.get("active_profile", "Desktop")
        self.control_enabled = new_settings.get("control_enabled", self.control_enabled)
        self.recognizer.update_settings(new_settings)
        self.smoother.set_factor(new_settings.get("smoothing", 0.75))

    def enable_control(self):
        """Enables system action execution."""
        self.control_enabled = True
        self.settings["control_enabled"] = True
        log_ui("Gesture Control ACTIVE", "SUCCESS")
        logger.info("Gesture Control ENABLED by user.")

    def disable_control(self, reason: str = "User request"):
        """Disables system action execution while keeping video pipeline active."""
        self.control_enabled = False
        self.settings["control_enabled"] = False
        self.mouse.stop_drag()
        log_ui(f"Gesture Control PAUSED ({reason})", "WARN")
        logger.info(f"Gesture Control PAUSED: {reason}")

    def emergency_stop(self):
        """Instant emergency kill-switch for computer control."""
        self.disable_control("EMERGENCY STOP TRIGGERED")

    def start(self) -> bool:
        """Starts video capture and background processing thread."""
        if self.running:
            return True

        if not self.camera.start():
            logger.error("Failed to start camera feed.")
            return False

        self.running = True
        self.process_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.process_thread.start()
        logger.info("GestureController processing loop started.")
        return True

    def _processing_loop(self):
        """Primary pipeline execution loop: capture -> tracking -> recognition -> dispatch."""
        screen_w, screen_h = self.mouse.get_screen_size()

        while self.running:
            t_start = time.time()
            is_connected, frame = self.camera.get_frame()
            if not is_connected or frame is None:
                time.sleep(0.01)
                continue

            # Run MediaPipe hand tracking
            tracking = self.hand_tracker.process_frame(frame)
            self.hand_count = tracking.get("hand_count", 0)
            hand_detected = tracking.get("detected", False) and len(tracking.get("landmarks", [])) > 0

            annotated_frame = frame.copy()

            if hand_detected:
                landmarks = tracking["landmarks"][0]

                # Draw 21 landmark skeleton joints
                annotated_frame = self.hand_tracker.draw_landmarks(annotated_frame, tracking)

                # Recognize gesture with strict priority and scale invariance
                raw_gesture, confidence, debug_info = self.recognizer.detect_gesture(landmarks)
                action_gesture, trigger, cooldown_act, cooldown_rem = self.recognizer.process_state_machine(raw_gesture, confidence)

                self.raw_gesture = raw_gesture
                self.current_gesture = action_gesture
                self.current_confidence = confidence
                self.cooldown_active = cooldown_act
                self.cooldown_remaining = cooldown_rem
                self.latest_debug_info = debug_info

                # CALIBRATION MODE SAFETY OVERRIDE: process bounds, bypass real mouse control
                if self.calibration.is_active:
                    pinch_dist = distance_3d(landmarks[4], landmarks[8]) if len(landmarks) > 8 else 0.05
                    self.calibration.process_frame_landmarks(landmarks, pinch_dist)
                # EVALUATION MODE SAFETY OVERRIDE: record trial match, bypass real mouse control
                elif self.evaluation.is_active:
                    if trigger and action_gesture != "IDLE":
                        self.evaluation.record_trial(action_gesture, confidence)
                else:
                    # Record recognition metric
                    self.metrics.record_gesture(action_gesture, confirmed=trigger, confidence=confidence)

                    # Dispatch system control actions IF CONTROL ACTIVE
                    self._dispatch_action(
                        action_gesture=action_gesture,
                        trigger=trigger,
                        landmarks=landmarks,
                        screen_w=screen_w,
                        screen_h=screen_h,
                        frame_w=frame.shape[1],
                        frame_h=frame.shape[0]
                    )
            else:
                # No hand detected
                self.raw_gesture = "IDLE"
                self.current_gesture = "IDLE"
                self.current_confidence = 0.0
                self.cooldown_active = False
                self.cooldown_remaining = 0.0
                self.latest_debug_info = {}
                self.smoother.reset()
                self.prev_scroll_y = None
                if self.mouse.is_dragging:
                    self.mouse.stop_drag()

            proc_time_ms = (time.time() - t_start) * 1000.0
            self.metrics.record_frame(hand_detected, proc_time_ms)

            # Annotate HUD overlay on frame
            annotated_frame = self._draw_hud(annotated_frame)

            with self.frame_lock:
                self.processed_frame = annotated_frame

            time.sleep(0.005)

    def _dispatch_action(
        self,
        action_gesture: str,
        trigger: bool,
        landmarks: list,
        screen_w: int,
        screen_h: int,
        frame_w: int,
        frame_h: int
    ):
        """Executes computer interaction based on confirmed gesture and master control state."""
        # 1. EMERGENCY FIST GESTURE -> Disable gesture control immediately
        if action_gesture == "FIST":
            if self.control_enabled:
                self.disable_control("Fist Emergency Gesture Detected")
            return

        # Release drag state if gesture changed away from DRAG
        if action_gesture != "DRAG" and self.mouse.is_dragging:
            self.mouse.stop_drag()

        # If CONTROL IS PAUSED, bypass all mouse and keyboard actions
        if not self.control_enabled:
            return

        # 2. CURSOR MOVEMENT
        if action_gesture == "CURSOR":
            index_tip = landmarks[INDEX_FINGER_TIP]
            raw_screen_x, raw_screen_y = map_camera_to_screen(
                cam_x=index_tip["x"],
                cam_y=index_tip["y"],
                cam_w=frame_w,
                cam_h=frame_h,
                screen_w=screen_w,
                screen_h=screen_h,
                margin_x=self.settings.get("margin_x", 0.15),
                margin_y=self.settings.get("margin_y", 0.15),
                sensitivity=self.settings.get("sensitivity", 1.4)
            )

            # Apply EMA smoothing
            smooth_x, smooth_y = self.smoother.update(raw_screen_x, raw_screen_y)

            # Apply dead zone jitter filter
            final_x, final_y = apply_dead_zone(
                smooth_x, smooth_y,
                self.prev_screen_x, self.prev_screen_y,
                threshold=self.settings.get("dead_zone", 3.0)
            )

            self.mouse.move_to(final_x, final_y)
            self.prev_screen_x, self.prev_screen_y = final_x, final_y

        # 3. DRAG AND DROP
        elif action_gesture == "DRAG":
            index_tip = landmarks[INDEX_FINGER_TIP]
            raw_screen_x, raw_screen_y = map_camera_to_screen(
                cam_x=index_tip["x"],
                cam_y=index_tip["y"],
                cam_w=frame_w,
                cam_h=frame_h,
                screen_w=screen_w,
                screen_h=screen_h,
                margin_x=self.settings.get("margin_x", 0.15),
                margin_y=self.settings.get("margin_y", 0.15),
                sensitivity=self.settings.get("sensitivity", 1.4)
            )
            smooth_x, smooth_y = self.smoother.update(raw_screen_x, raw_screen_y)
            self.mouse.start_drag()
            self.mouse.move_to(smooth_x, smooth_y)
            self.prev_screen_x, self.prev_screen_y = smooth_x, smooth_y

        # 4. LEFT CLICK
        elif action_gesture == "PINCH" and trigger:
            self.mouse.left_click()

        # 5. DOUBLE CLICK
        elif action_gesture == "DOUBLE_PINCH" and trigger:
            self.mouse.double_click()

        # 6. RIGHT CLICK
        elif action_gesture == "RIGHT_CLICK" and trigger:
            self.mouse.right_click()

        # 7. PRESENTATION PROFILE SPECIAL ACTIONS
        if self.active_profile == "Presentation":
            if action_gesture == "OPEN_PALM" and trigger:
                # Presentation Profile: Open Palm -> Next Slide (Right Arrow key)
                self.keyboard.press_key("right")
                log_ui("Next Slide (Open Palm)", "PRESENTATION")
                return "Next Slide"
            elif action_gesture == "THREE_FINGERS" and trigger:
                # Presentation Profile: Three Fingers -> Previous Slide (Left Arrow key)
                self.keyboard.press_key("left")
                log_ui("Previous Slide (Three Fingers)", "PRESENTATION")
                return "Previous Slide"

        # 8. SCROLL (OPEN PALM in Desktop & Media Profiles)
        elif action_gesture == "OPEN_PALM":
            wrist_y = landmarks[WRIST]["y"]
            if self.prev_scroll_y is not None:
                dy = self.prev_scroll_y - wrist_y  # Moving hand UP (dy > 0) -> scroll UP
                deadzone = self.settings.get("scroll_deadzone", 0.02)
                if abs(dy) > deadzone:
                    scroll_speed = self.settings.get("scroll_sensitivity", 25.0)
                    clicks = int(dy * scroll_speed * 10)
                    self.mouse.scroll(clicks)
            self.prev_scroll_y = wrist_y

        if action_gesture != "OPEN_PALM":
            self.prev_scroll_y = None

        # 9. MEDIA CONTROLS
        if trigger:
            if action_gesture == "THUMBS_UP":
                self.media.play_pause()
            elif action_gesture == "SWIPE_RIGHT":
                self.media.next_track()
            elif action_gesture == "SWIPE_LEFT":
                self.media.previous_track()

    def _draw_hud(self, frame: np.ndarray) -> np.ndarray:
        """Overlays camera HUD status card, active gesture badge, FPS, and optional Debug panel."""
        h, w, _ = frame.shape

        # Top status bar background overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 45), (15, 15, 20), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Title Header & Control status
        ctrl_str = "CONTROL: ACTIVE" if self.control_enabled else "CONTROL: PAUSED"
        ctrl_color = (50, 225, 50) if self.control_enabled else (0, 140, 255)
        cv2.putText(frame, ctrl_str, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, ctrl_color, 2, cv2.LINE_AA)

        # FPS indicator
        fps_text = f"FPS: {self.camera.get_fps()}"
        cv2.putText(frame, fps_text, (w - 110, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 1, cv2.LINE_AA)

        # Bottom HUD Info Banner
        cv2.rectangle(frame, (0, h - 45), (w, h), (15, 15, 20), -1)

        if self.hand_count == 0:
            gesture_line = "Gesture: NONE"
            action_line = "Action: Waiting for hand..."
            conf_str = ""
            status_color = (160, 160, 160)
        else:
            g_name = self.current_gesture
            if not self.control_enabled and g_name == "FIST":
                action_line = "Action: Gesture control disabled"
            else:
                action_line = f"Action: {GESTURE_ACTION_NAMES.get(g_name, 'None')}"

            gesture_line = f"Gesture: {g_name}"
            conf_str = f"Confidence: {int(self.current_confidence * 100)}%" if self.current_confidence > 0 else ""
            status_color = (0, 215, 255) if self.control_enabled else (0, 140, 255)

        hud_str = f"{gesture_line}   |   {action_line}   {conf_str}".strip()
        cv2.putText(frame, hud_str, (12, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 1, cv2.LINE_AA)

        # OPTIONAL DEBUG MODE OVERLAY PANEL (Section 15)
        if self.settings.get("debug_mode", False) and self.latest_debug_info:
            self._draw_debug_overlay(frame)

        return frame

    def _draw_debug_overlay(self, frame: np.ndarray):
        """Renders technical diagnostic parameters overlay when debug_mode is enabled."""
        h, w, _ = frame.shape
        debug_bg = frame.copy()
        cv2.rectangle(debug_bg, (10, 50), (280, 200), (10, 10, 15), -1)
        cv2.addWeighted(debug_bg, 0.8, frame, 0.2, 0, frame)

        dbg = self.latest_debug_info
        fingers = dbg.get("fingers", {})
        f_str = f"T:{int(fingers.get('thumb',0))} I:{int(fingers.get('index',0))} M:{int(fingers.get('middle',0))} R:{int(fingers.get('ring',0))} P:{int(fingers.get('pinky',0))}"

        lines = [
            "--- DEBUG MODE ---",
            f"Raw Gest: {dbg.get('raw_gesture', 'IDLE')}",
            f"Pinch Ratio: {dbg.get('pinch_ratio', 0.0)}",
            f"Hand Scale: {dbg.get('hand_scale', 0.0)}",
            f"Fingers: {f_str}",
            f"Cooldown: {'ACTIVE (' + str(self.cooldown_remaining) + 's)' if self.cooldown_active else 'READY'}"
        ]

        y_offset = 70
        for line in lines:
            color = (0, 255, 255) if "DEBUG" in line else (200, 220, 200)
            cv2.putText(frame, line, (18, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
            y_offset += 20

    def get_processed_frame(self) -> Optional[np.ndarray]:
        """Returns the latest annotated video frame."""
        with self.frame_lock:
            if self.processed_frame is not None:
                return self.processed_frame.copy()
            return None

    def get_status_info(self) -> dict:
        """Returns snapshot dictionary of active controller states for Dashboard cards."""
        g_name = self.current_gesture
        action_name = GESTURE_ACTION_NAMES.get(g_name, "Waiting for hand...")
        if not self.control_enabled and g_name == "FIST":
            action_name = "Gesture control disabled"
        elif self.active_profile == "Presentation":
            if g_name == "OPEN_PALM":
                action_name = "Next Slide"
            elif g_name == "THREE_FINGERS":
                action_name = "Previous Slide"

        return {
            "connected": self.camera.is_connected,
            "control_enabled": self.control_enabled,
            "active_profile": self.active_profile,
            "current_gesture": g_name,
            "gesture_label": GESTURE_NAMES.get(g_name, g_name),
            "action_name": action_name,
            "confidence": self.current_confidence,
            "confidence_pct": f"{int(self.current_confidence * 100)}%" if self.current_confidence > 0 else "--",
            "hand_count": self.hand_count,
            "hand_status": "Hand Detected" if self.hand_count > 0 else "No hand detected",
            "fps": self.camera.get_fps(),
            "cooldown_active": self.cooldown_active,
            "session_stats": self.metrics.get_session_stats(),
            "calibration_active": self.calibration.is_active,
            "calibration_step": self.calibration.get_current_step(),
            "calibration_instruction": self.calibration.get_instruction(),
            "evaluation_active": self.evaluation.is_active,
            "evaluation_target": self.evaluation.get_target_label()
        }

    def stop(self):
        """Gracefully shuts down camera, threads, releases held mouse buttons, and cleans up."""
        self.running = False
        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=1.0)

        self.camera.stop()
        self.hand_tracker.close()
        self.mouse.stop_drag()
        logger.info("GestureController shut down.")
