"""
GestureControl AI - Unit Tests for Coordinate Transformation & Smoothing
Tests camera-to-screen projection, corner grid mappings, boundary clamping,
EMA smoothing convergence, and dead zone jitter suppression.
"""

import unittest
from utils.smoothing import ExponentialSmoother, map_camera_to_screen, apply_dead_zone


class TestCoordinateMath(unittest.TestCase):

    def test_map_camera_to_screen_center(self):
        """Tests mapping center of camera frame (0.5, 0.5) to center of screen."""
        screen_x, screen_y = map_camera_to_screen(
            cam_x=0.5,
            cam_y=0.5,
            cam_w=640,
            cam_h=480,
            screen_w=1920,
            screen_h=1080,
            margin_x=0.15,
            margin_y=0.15,
            sensitivity=1.0,
            flip_h=True
        )

        # Center camera normalized (0.5, 0.5) flipped remains 0.5 -> mapped to screen center (~959.5, ~539.5)
        self.assertAlmostEqual(screen_x, 959.5, delta=5.0)
        self.assertAlmostEqual(screen_y, 539.5, delta=5.0)

    def test_map_camera_corners_grid(self):
        """
        Tests mapping all 4 corners and center: (0,0), (1,0), (0,1), (1,1), (0.5, 0.5).
        With flip_h=True (selfie mode mirroring):
        - Camera top-left (0,0) -> Screen top-right (1919, 0)
        - Camera top-right (1,0) -> Screen top-left (0, 0)
        - Camera bottom-left (0,1) -> Screen bottom-right (1919, 1079)
        - Camera bottom-right (1,1) -> Screen bottom-left (0, 1079)
        """
        w, h = 1920, 1080

        # Top-Right on screen (Camera X=0.0 -> flipped X=1.0)
        tr_x, tr_y = map_camera_to_screen(0.0, 0.0, 640, 480, w, h, 0.15, 0.15, 1.0, True)
        self.assertAlmostEqual(tr_x, 1919.0, delta=2.0)
        self.assertAlmostEqual(tr_y, 0.0, delta=2.0)

        # Top-Left on screen (Camera X=1.0 -> flipped X=0.0)
        tl_x, tl_y = map_camera_to_screen(1.0, 0.0, 640, 480, w, h, 0.15, 0.15, 1.0, True)
        self.assertAlmostEqual(tl_x, 0.0, delta=2.0)
        self.assertAlmostEqual(tl_y, 0.0, delta=2.0)

        # Bottom-Right on screen (Camera X=0.0, Y=1.0)
        br_x, br_y = map_camera_to_screen(0.0, 1.0, 640, 480, w, h, 0.15, 0.15, 1.0, True)
        self.assertAlmostEqual(br_x, 1919.0, delta=2.0)
        self.assertAlmostEqual(br_y, 1079.0, delta=2.0)

        # Bottom-Left on screen (Camera X=1.0, Y=1.0)
        bl_x, bl_y = map_camera_to_screen(1.0, 1.0, 640, 480, w, h, 0.15, 0.15, 1.0, True)
        self.assertAlmostEqual(bl_x, 0.0, delta=2.0)
        self.assertAlmostEqual(bl_y, 1079.0, delta=2.0)

    def test_map_camera_to_screen_clamping(self):
        """Tests that out-of-bounds coordinates clamp strictly inside screen boundaries [0, W-1] x [0, H-1]."""
        screen_x, screen_y = map_camera_to_screen(
            cam_x=1.5,   # Out of bounds right
            cam_y=-0.5,  # Out of bounds top
            cam_w=640,
            cam_h=480,
            screen_w=1920,
            screen_h=1080,
            margin_x=0.15,
            margin_y=0.15,
            sensitivity=1.0,
            flip_h=True
        )

        self.assertGreaterEqual(screen_x, 0.0)
        self.assertLessEqual(screen_x, 1919.0)
        self.assertGreaterEqual(screen_y, 0.0)
        self.assertLessEqual(screen_y, 1079.0)

    def test_exponential_smoother(self):
        """Tests EMA smoothing convergence over successive updates."""
        smoother = ExponentialSmoother(factor=0.5)

        # Initial point sets baseline
        p1_x, p1_y = smoother.update(100.0, 100.0)
        self.assertEqual((p1_x, p1_y), (100.0, 100.0))

        # Sudden jump to (200, 200) -> EMA should step halfway to 150
        p2_x, p2_y = smoother.update(200.0, 200.0)
        self.assertEqual((p2_x, p2_y), (150.0, 150.0))

        # Next update to (200, 200) -> EMA moves halfway again to 175
        p3_x, p3_y = smoother.update(200.0, 200.0)
        self.assertEqual((p3_x, p3_y), (175.0, 175.0))

    def test_dead_zone_filter(self):
        """Tests micro-movement dead zone filtering."""
        prev_x, prev_y = 500.0, 500.0

        # Small jitter (1.0 pixel move < 3.0 threshold) -> Should return previous position
        filtered_x, filtered_y = apply_dead_zone(501.0, 500.0, prev_x, prev_y, threshold=3.0)
        self.assertEqual((filtered_x, filtered_y), (prev_x, prev_y))

        # Significant move (10 pixels > 3.0 threshold) -> Should return new position
        moved_x, moved_y = apply_dead_zone(510.0, 500.0, prev_x, prev_y, threshold=3.0)
        self.assertEqual((moved_x, moved_y), (510.0, 500.0))


if __name__ == "__main__":
    unittest.main()
