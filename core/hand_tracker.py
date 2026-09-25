"""
GestureControl AI - Hand Tracking Module
Wrapper around MediaPipe Hands for real-time 3D hand landmark detection, drawing,
and metric extraction.
"""

from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np

from utils.logger import setup_logger

MEDIAPIPE_IMPORT_ERROR = None

try:
    import mediapipe as mp
    try:
        mp_hands = mp.solutions.hands
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
    except AttributeError:
        from mediapipe.python.solutions import hands as mp_hands
        from mediapipe.python.solutions import drawing_utils as mp_drawing
        from mediapipe.python.solutions import drawing_styles as mp_drawing_styles
    HAS_MEDIAPIPE = True
except Exception as e:
    mp = None
    mp_hands = None
    mp_drawing = None
    mp_drawing_styles = None
    HAS_MEDIAPIPE = False
    MEDIAPIPE_IMPORT_ERROR = str(e)

logger = setup_logger("HandTracker")


# Standard MediaPipe Landmark Index Constants
WRIST = 0
THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP = 3
THUMB_TIP = 4
INDEX_FINGER_MCP = 5
INDEX_FINGER_PIP = 6
INDEX_FINGER_DIP = 7
INDEX_FINGER_TIP = 8
MIDDLE_FINGER_MCP = 9
MIDDLE_FINGER_PIP = 10
MIDDLE_FINGER_DIP = 11
MIDDLE_FINGER_TIP = 12
RING_FINGER_MCP = 13
RING_FINGER_PIP = 14
RING_FINGER_DIP = 15
RING_FINGER_TIP = 16
PINKY_MCP = 17
PINKY_PIP = 18
PINKY_DIP = 19
PINKY_TIP = 20


class HandTracker:
    """
    Tracks hand landmarks using MediaPipe Hands pipeline.
    """

    def __init__(
        self,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.7
    ):
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self.hands_solution = None
        if HAS_MEDIAPIPE and mp_hands is not None:
            try:
                self.hands_solution = mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=self.max_num_hands,
                    min_detection_confidence=self.min_detection_confidence,
                    min_tracking_confidence=self.min_tracking_confidence
                )
                logger.info("MediaPipe Hands pipeline initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing MediaPipe Hands: {e}")
        else:
            err_details = f" ({MEDIAPIPE_IMPORT_ERROR})" if MEDIAPIPE_IMPORT_ERROR else ""
            logger.warning(f"MediaPipe library unavailable{err_details}. Running in mock tracking mode.")

    def process_frame(self, frame_bgr: np.ndarray) -> dict:
        """
        Processes a BGR image frame and extracts hand landmark data.

        :param frame_bgr: Input BGR OpenCV image numpy array
        :return: Dictionary containing tracking status, count, landmarks list, and raw solution output.
        """
        result_data = {
            "detected": False,
            "hand_count": 0,
            "landmarks": [],  # List of normalized dicts per hand [{'x':.., 'y':.., 'z':..}, ...]
            "pixel_landmarks": [],  # List of pixel (x, y) per hand
            "handedness": [],  # 'Left' or 'Right'
            "raw_landmarks": []
        }

        if frame_bgr is None or self.hands_solution is None:
            return result_data

        h, w, _ = frame_bgr.shape
        # Convert BGR frame to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self.hands_solution.process(frame_rgb)

        if results.multi_hand_landmarks:
            result_data["detected"] = True
            result_data["hand_count"] = len(results.multi_hand_landmarks)

            # Store handedness label if available
            if results.multi_handedness:
                for classification in results.multi_handedness:
                    label = classification.classification[0].label
                    result_data["handedness"].append(label)

            for hand_landmarks in results.multi_hand_landmarks:
                result_data["raw_landmarks"].append(hand_landmarks)
                norm_pts = []
                pixel_pts = []
                for lm in hand_landmarks.landmark:
                    norm_pts.append({
                        "x": lm.x,
                        "y": lm.y,
                        "z": lm.z
                    })
                    pixel_pts.append((int(lm.x * w), int(lm.y * h)))

                result_data["landmarks"].append(norm_pts)
                result_data["pixel_landmarks"].append(pixel_pts)

        return result_data

    def draw_landmarks(self, frame_bgr: np.ndarray, tracking_results: dict) -> np.ndarray:
        """
        Annotates OpenCV frame with hand skeleton, joints, and visual landmark styles.
        """
        if frame_bgr is None or not tracking_results.get("detected", False):
            return frame_bgr

        annotated_frame = frame_bgr.copy()
        raw_lms = tracking_results.get("raw_landmarks", [])

        if HAS_MEDIAPIPE and mp_drawing is not None and mp_hands is not None:
            for hand_landmarks in raw_lms:
                mp_drawing.draw_landmarks(
                    annotated_frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style()
                )

        return annotated_frame

    def close(self):
        """Releases MediaPipe resources."""
        if self.hands_solution:
            self.hands_solution.close()
            self.hands_solution = None
