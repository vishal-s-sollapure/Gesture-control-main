"""
GestureControl AI - Interactive First-Run Calibration Module
Guides users through hand placement, boundary mapping, and pinch threshold calibration.
Saves customized ROI margins and gesture thresholds to settings without active mouse control.
"""

import time
from typing import Dict, Any, Tuple, Optional
from config import save_settings, load_settings
from utils.logger import setup_logger

logger = setup_logger("Calibration")


class CalibrationManager:
    """
    Manages step-by-step interactive hand calibration.
    Ensures computer control actions remain strictly PAUSED during calibration.
    """

    STEPS = [
        "CENTER",       # Step 1: Position hand in center
        "TOP_LEFT",     # Step 2: Move hand to top-left corner
        "BOTTOM_RIGHT", # Step 3: Move hand to bottom-right corner
        "PINCH",        # Step 4: Perform natural pinch
        "COMPLETE"      # Step 5: Calibration complete
    ]

    STEP_INSTRUCTIONS = {
        "CENTER": "1. Position your hand in the center of the webcam frame.",
        "TOP_LEFT": "2. Move your hand to the top-left corner of your comfortable reach area.",
        "BOTTOM_RIGHT": "3. Move your hand to the bottom-right corner of your comfortable reach area.",
        "PINCH": "4. Perform a natural thumb-index pinch gesture.",
        "COMPLETE": "5. Calibration complete! Settings updated successfully."
    }

    def __init__(self):
        self.is_active = False
        self.current_step_idx = 0

        # Sampled boundary landmarks
        self.top_left_sample: Optional[Tuple[float, float]] = None
        self.bottom_right_sample: Optional[Tuple[float, float]] = None
        self.pinch_samples: list = []
        self.step_start_time = 0.0

    def start_calibration(self):
        """
        Starts the calibration wizard loop.
        """
        self.is_active = True
        self.current_step_idx = 0
        self.top_left_sample = None
        self.bottom_right_sample = None
        self.pinch_samples.clear()
        self.step_start_time = time.time()
        logger.info("Started interactive calibration wizard.")

    def get_current_step(self) -> str:
        """Returns the active step name."""
        if not self.is_active or self.current_step_idx >= len(self.STEPS):
            return "IDLE"
        return self.STEPS[self.current_step_idx]

    def get_instruction(self) -> str:
        """Returns human-readable text instruction for active step."""
        step = self.get_current_step()
        return self.STEP_INSTRUCTIONS.get(step, "Calibration inactive.")

    def process_frame_landmarks(self, landmarks: list, pinch_distance: float) -> dict:
        """
        Process hand landmarks for active calibration step.
        Returns step progress dictionary.
        """
        if not self.is_active or not landmarks:
            return {"step": self.get_current_step(), "progress": 0.0, "ready": False}

        step = self.get_current_step()
        index_tip = landmarks[8]  # INDEX_FINGER_TIP
        now = time.time()
        step_elapsed = now - self.step_start_time

        if step == "CENTER":
            if step_elapsed >= 2.0:
                self.advance_step()

        elif step == "TOP_LEFT":
            if step_elapsed >= 2.0:
                self.top_left_sample = (index_tip["x"], index_tip["y"])
                self.advance_step()

        elif step == "BOTTOM_RIGHT":
            if step_elapsed >= 2.0:
                self.bottom_right_sample = (index_tip["x"], index_tip["y"])
                self.advance_step()

        elif step == "PINCH":
            self.pinch_samples.append(pinch_distance)
            if step_elapsed >= 2.0 and len(self.pinch_samples) > 5:
                self.advance_step()

        elif step == "COMPLETE":
            self.finalize_calibration()

        return {
            "step": step,
            "progress": min(1.0, step_elapsed / 2.0),
            "ready": step == "COMPLETE"
        }

    def advance_step(self):
        """Advances to the next calibration step."""
        self.current_step_idx += 1
        self.step_start_time = time.time()
        if self.get_current_step() == "COMPLETE":
            self.finalize_calibration()

    def finalize_calibration(self) -> dict:
        """
        Calculates calibrated parameters and saves them to settings.json.
        """
        settings = load_settings()

        margin_x = settings.get("margin_x", 0.15)
        margin_y = settings.get("margin_y", 0.15)
        pinch_thresh = settings.get("pinch_threshold", 0.045)

        if self.top_left_sample and self.bottom_right_sample:
            tl_x, tl_y = self.top_left_sample
            br_x, br_y = self.bottom_right_sample

            margin_x = max(0.05, min(0.35, round(min(tl_x, 1.0 - br_x), 3)))
            margin_y = max(0.05, min(0.35, round(min(tl_y, 1.0 - br_y), 3)))

        if self.pinch_samples:
            avg_pinch = sum(self.pinch_samples) / len(self.pinch_samples)
            pinch_thresh = max(0.025, min(0.08, round(avg_pinch * 1.25, 3)))

        settings.update({
            "calibrated": True,
            "calibrated_margin_x": margin_x,
            "calibrated_margin_y": margin_y,
            "calibrated_pinch_thresh": pinch_thresh,
            "margin_x": margin_x,
            "margin_y": margin_y,
            "pinch_threshold": pinch_thresh
        })

        save_settings(settings)
        self.is_active = False
        logger.info(f"Calibration completed: margin_x={margin_x}, margin_y={margin_y}, pinch_threshold={pinch_thresh}")
        return settings

    def cancel_calibration(self):
        """Cancels active calibration wizard without modifying settings."""
        self.is_active = False
        self.current_step_idx = 0
        logger.info("Calibration canceled by user.")
