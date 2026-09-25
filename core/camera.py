"""
GestureControl AI - Camera Module
Manages threaded OpenCV webcam video stream, FPS calculation, camera recovery, and frame capture.
"""

import threading
import time
from typing import Optional, Tuple
import cv2
import numpy as np

from utils.logger import setup_logger, log_ui

logger = setup_logger("Camera")


class Camera:
    """
    Threaded OpenCV VideoCapture manager for responsive, low-latency webcam processing.
    """

    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480, target_fps: int = 30):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.target_fps = target_fps

        self.cap: Optional[cv2.VideoCapture] = None
        self.is_connected = False
        self.running = False
        self.thread: Optional[threading.Thread] = None

        self.latest_frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()

        # FPS metrics
        self.fps = 0.0
        self._frame_count = 0
        self._fps_start_time = time.time()

    def start(self) -> bool:
        """Initializes the webcam device and launches the thread loop."""
        if self.running:
            return True

        self._init_camera()
        if not self.is_connected:
            # Attempt camera auto-discovery if specified index failed
            for fallback_idx in [0, 1, 2]:
                if fallback_idx != self.camera_index:
                    logger.info(f"Retrying camera discovery with index {fallback_idx}...")
                    self.camera_index = fallback_idx
                    self._init_camera()
                    if self.is_connected:
                        break

        if not self.is_connected:
            logger.error("Failed to connect to any camera device.")
            log_ui("Camera device unavailable or restricted!", "ERROR")
            return False

        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        logger.info(f"Camera thread started on index {self.camera_index} ({self.width}x{self.height})")
        log_ui(f"Camera connected (Index {self.camera_index})", "INFO")
        return True

    def _init_camera(self):
        """Attempts connection to OpenCV VideoCapture."""
        if self.cap is not None:
            self.cap.release()

        # On Windows, try CAP_DSHOW or default CAP_ANY
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)

        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)

            # Test frame read
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.is_connected = True
                with self.frame_lock:
                    self.latest_frame = frame
            else:
                self.is_connected = False
        else:
            self.is_connected = False

    def _update_loop(self):
        """Continuous frame grab thread loop."""
        self._fps_start_time = time.time()
        self._frame_count = 0

        while self.running:
            if self.cap is None or not self.cap.isOpened():
                self.is_connected = False
                time.sleep(0.5)
                continue

            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.is_connected = False
                time.sleep(0.1)
                continue

            self.is_connected = True

            with self.frame_lock:
                self.latest_frame = frame

            # FPS calculation
            self._frame_count += 1
            now = time.time()
            elapsed = now - self._fps_start_time
            if elapsed >= 1.0:
                self.fps = self._frame_count / elapsed
                self._frame_count = 0
                self._fps_start_time = now

            # Sleep slightly to prevent high CPU spinning if camera is fast
            time.sleep(0.005)

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Returns the most recent webcam BGR frame."""
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.is_connected, self.latest_frame.copy()
            return False, None

    def get_fps(self) -> float:
        """Returns calculated frames-per-second."""
        return round(self.fps, 1)

    def stop(self):
        """Stops the camera thread and releases hardware resources."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.is_connected = False
        logger.info("Camera device stopped.")
        log_ui("Camera disconnected", "WARN")
