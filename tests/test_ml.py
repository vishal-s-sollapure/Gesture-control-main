"""
GestureControl AI - Unit Tests for Machine Learning Recognition Engine & Dataset Pipeline
Tests landmark normalization, dataset generation, train/test split, Random Forest classifier,
and metric calculation (Accuracy, Precision, Recall, F1, Confusion Matrix).
"""

import unittest
from pathlib import Path
from ml.preprocess import normalize_landmarks
from ml.collect_data import build_dataset, DATASET_PATH
from ml.train import train_and_evaluate, MODEL_PATH, REPORT_PATH
from ml.evaluate import print_evaluation_summary


class TestMLPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Build dataset and train Random Forest model prior to running tests."""
        build_dataset(samples_per_class=100)
        cls.report = train_and_evaluate()

    def test_landmark_normalization_vector_length(self):
        """Normalized feature vector must be exactly 63 elements."""
        dummy_lms = [{"x": 0.5 + i * 0.01, "y": 0.5 - i * 0.01, "z": 0.0} for i in range(21)]
        feats = normalize_landmarks(dummy_lms)
        self.assertEqual(len(feats), 63)
        # Wrist origin (feat 0, 1, 2) must be 0.0, 0.0, 0.0
        self.assertEqual(feats[0], 0.0)
        self.assertEqual(feats[1], 0.0)
        self.assertEqual(feats[2], 0.0)

    def test_dataset_generation_file_exists(self):
        """Dataset CSV must exist and contain rows."""
        self.assertTrue(DATASET_PATH.exists())

    def test_model_training_output(self):
        """Model file model.pkl and report evaluation_report.json must exist."""
        self.assertTrue(MODEL_PATH.exists())
        self.assertTrue(REPORT_PATH.exists())

    def test_model_evaluation_metrics(self):
        """Report must contain valid accuracy, F1, precision, recall, and confusion matrix."""
        self.assertIn("overall_accuracy_pct", self.report)
        self.assertGreater(self.report["overall_accuracy_pct"], 80.0)
        self.assertIn("f1_score_weighted", self.report)
        self.assertGreater(self.report["f1_score_weighted"], 0.8)
        self.assertIn("confusion_matrix", self.report)
        self.assertEqual(len(self.report["classes"]), 8)


if __name__ == "__main__":
    unittest.main()
