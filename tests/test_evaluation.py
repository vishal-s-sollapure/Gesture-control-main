"""
GestureControl AI - Unit Tests for Evaluation Engine
"""

import unittest
from core.evaluation import EvaluationEngine


class TestEvaluation(unittest.TestCase):

    def setUp(self):
        self.ee = EvaluationEngine()

    def test_evaluation_initial_state(self):
        """Initial state should be inactive with no data available."""
        self.assertFalse(self.ee.is_active)
        report = self.ee.compute_report()
        self.assertEqual(report["overall_accuracy_pct"], "N/A")

    def test_evaluation_trial_recording(self):
        """Record trials and check accuracy calculation."""
        self.ee.start_evaluation()
        target = self.ee.get_current_target()
        self.assertEqual(target, "CURSOR")

        # Record matching trial for CURSOR
        trial1 = self.ee.record_trial("CURSOR", 0.95)
        self.assertTrue(trial1["match"])

        # Second target is PINCH
        self.assertEqual(self.ee.get_current_target(), "PINCH")

        # Record non-matching trial for PINCH
        trial2 = self.ee.record_trial("OPEN_PALM", 0.80)
        self.assertFalse(trial2["match"])

        report = self.ee.compute_report()
        self.assertEqual(report["total_trials"], 2)
        self.assertEqual(report["correct_trials"], 1)
        self.assertEqual(report["overall_accuracy_pct"], 50.0)


if __name__ == "__main__":
    unittest.main()
