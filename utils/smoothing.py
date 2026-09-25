"""
GestureControl AI - Smoothing Utility
Provides Exponential Moving Average (EMA) cursor smoothing, coordinate transformation,
dead-zone filtering, and boundary clamping.
"""

import math
from typing import Tuple


class ExponentialSmoother:
    """
    Exponential Moving Average (EMA) smoother for 2D points.
    smooth_pos = prev_pos * factor + current_pos * (1 - factor)
    """

    def __init__(self, factor: float = 0.75):
        """
        :param factor: Smoothing factor between 0.0 (no smoothing, raw) and 0.95 (heavy smoothing).
        """
        self.factor = max(0.0, min(0.95, factor))
        self.prev_x = None
        self.prev_y = None

    def set_factor(self, factor: float):
        """Updates the smoothing factor dynamically."""
        self.factor = max(0.0, min(0.95, factor))

    def reset(self):
        """Resets stored position memory."""
        self.prev_x = None
        self.prev_y = None

    def update(self, curr_x: float, curr_y: float) -> Tuple[float, float]:
        """
        Applies EMA smoothing to target coordinates (curr_x, curr_y).
        """
        if self.prev_x is None or self.prev_y is None:
            self.prev_x = curr_x
            self.prev_y = curr_y
            return curr_x, curr_y

        smooth_x = self.prev_x * self.factor + curr_x * (1.0 - self.factor)
        smooth_y = self.prev_y * self.factor + curr_y * (1.0 - self.factor)

        self.prev_x = smooth_x
        self.prev_y = smooth_y

        return smooth_x, smooth_y


def map_camera_to_screen(
    cam_x: float,
    cam_y: float,
    cam_w: int,
    cam_h: int,
    screen_w: int,
    screen_h: int,
    margin_x: float = 0.15,
    margin_y: float = 0.15,
    sensitivity: float = 1.0,
    flip_h: bool = True
) -> Tuple[float, float]:
    """
    Maps camera normalized or pixel coordinates to screen coordinates.

    :param cam_x: X coordinate in camera frame (0.0 to 1.0 or pixel value)
    :param cam_y: Y coordinate in camera frame (0.0 to 1.0 or pixel value)
    :param cam_w: Camera width in pixels
    :param cam_h: Camera height in pixels
    :param screen_w: Target screen width in pixels
    :param screen_h: Target screen height in pixels
    :param margin_x: Horizontal active box margin fraction (0.15 = 15% padding on left/right)
    :param margin_y: Vertical active box margin fraction (0.15 = 15% padding on top/bottom)
    :param sensitivity: Sensitivity multiplier (1.0 = normal, >1.0 = faster reach)
    :param flip_h: Flip horizontally for natural selfie webcam movement
    :return: Clamped target (screen_x, screen_y)
    """
    # Normalize inputs if given in pixels
    norm_x = cam_x / cam_w if cam_x > 1.0 else cam_x
    norm_y = cam_y / cam_h if cam_y > 1.0 else cam_y

    # Flip horizontally for selfie mirroring
    if flip_h:
        norm_x = 1.0 - norm_x

    # Apply ROI margin box scaling so full screen reach doesn't require extreme camera edges
    active_min_x = margin_x
    active_max_x = 1.0 - margin_x
    active_min_y = margin_y
    active_max_y = 1.0 - margin_y

    # Rescale coordinate within active range [0.0, 1.0]
    scaled_x = (norm_x - active_min_x) / (active_max_x - active_min_x + 1e-6)
    scaled_y = (norm_y - active_min_y) / (active_max_y - active_min_y + 1e-6)

    # Center-based sensitivity scaling
    if sensitivity != 1.0:
        scaled_x = 0.5 + (scaled_x - 0.5) * sensitivity
        scaled_y = 0.5 + (scaled_y - 0.5) * sensitivity

    # Clamp to valid screen range
    clamped_x = max(0.0, min(1.0, scaled_x))
    clamped_y = max(0.0, min(1.0, scaled_y))

    screen_x = clamped_x * (screen_w - 1)
    screen_y = clamped_y * (screen_h - 1)

    return screen_x, screen_y


def apply_dead_zone(
    curr_x: float,
    curr_y: float,
    prev_x: float,
    prev_y: float,
    threshold: float = 3.0
) -> Tuple[float, float]:
    """
    Ignores micro-movements smaller than `threshold` pixels to eliminate stationary hand jitter.
    """
    if prev_x is None or prev_y is None:
        return curr_x, curr_y

    dist = math.hypot(curr_x - prev_x, curr_y - prev_y)
    if dist < threshold:
        return prev_x, prev_y
    return curr_x, curr_y
