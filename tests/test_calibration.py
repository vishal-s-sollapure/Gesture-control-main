"""
GestureControl AI - Unit Tests for Calibration System
"""

import unittest
from core.calibration import CalibrationManager


class TestCalibration(unittest.TestCase):

    def setUp(self):
        self.calib = CalibrationManager()

    def test_calibration_initial_state(self):
        """Initial state should be inactive."""
        self.assertFalse(self.calib.is_active)
        self.assertEqual(self.calib.get_current_step(), "IDLE")

    def test_calibration_workflow_progression(self):
        """Tests advancing step sequence from CENTER -> TOP_LEFT -> BOTTOM_RIGHT -> PINCH -> COMPLETE."""
        self.calib.start_calibration()
        self.assertTrue(self.calib.is_active)
        self.assertEqual(self.calib.get_current_step(), "CENTER")

        self.calib.advance_step()
        self.assertEqual(self.calib.get_current_step(), "TOP_LEFT")

        self.calib.advance_step()
        self.assertEqual(self.calib.get_current_step(), "BOTTOM_RIGHT")

        self.calib.advance_step()
        self.assertEqual(self.calib.get_current_step(), "PINCH")

    def test_cancel_calibration(self):
        """Canceling resets active state without applying changes."""
        self.calib.start_calibration()
        self.calib.cancel_calibration()
        self.assertFalse(self.calib.is_active)
        self.assertEqual(self.calib.get_current_step(), "IDLE")


if __name__ == "__main__":
    unittest.main()
