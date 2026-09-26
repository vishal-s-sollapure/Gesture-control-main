"""
GestureControl AI - Safe Gesture Evaluation Module
Enables empirical testing and accuracy evaluation without performing computer control actions.
Exports evaluation results to local evaluation_results.json.
"""

import json
import time
from typing import Dict, Any, List, Optional
from config import EVALUATION_FILE, GESTURE_NAMES
from utils.logger import setup_logger

logger = setup_logger("Evaluation")


class EvaluationEngine:
    """
    Evaluation session manager. Records expected vs detected gestures, response time,
    and confidence scores for empirical accuracy benchmarks.
    """

    EVALUATION_TARGETS = [
        "CURSOR",
        "PINCH",
        "RIGHT_CLICK",
        "OPEN_PALM",
        "THREE_FINGERS",
        "DRAG",
        "DOUBLE_PINCH",
        "THUMBS_UP",
        "SWIPE_LEFT",
        "SWIPE_RIGHT",
        "FIST"
    ]

    def __init__(self):
        self.is_active = False
        self.current_target_idx = 0
        self.trials: List[dict] = []
        self.step_start_time = 0.0

    def start_evaluation(self):
        """Starts evaluation session."""
        self.is_active = True
        self.current_target_idx = 0
        self.trials.clear()
        self.step_start_time = time.time()
        logger.info("Evaluation session started.")

    def get_current_target(self) -> str:
        """Returns target gesture for active trial."""
        if not self.is_active or self.current_target_idx >= len(self.EVALUATION_TARGETS):
            return "IDLE"
        return self.EVALUATION_TARGETS[self.current_target_idx]

    def get_target_label(self) -> str:
        """Returns human-readable target label."""
        target = self.get_current_target()
        return GESTURE_NAMES.get(target, target)

    def record_trial(self, detected_gesture: str, confidence: float) -> dict:
        """
        Records trial result for current target gesture.
        """
        if not self.is_active:
            return {}

        expected = self.get_current_target()
        response_time = round((time.time() - self.step_start_time) * 1000.0, 1)
        is_match = (detected_gesture == expected)

        trial = {
            "expected_gesture": expected,
            "detected_gesture": detected_gesture,
            "match": is_match,
            "response_time_ms": response_time,
            "confidence": round(confidence, 3)
        }
        self.trials.append(trial)

        # Advance to next target gesture
        self.current_target_idx += 1
        self.step_start_time = time.time()

        if self.current_target_idx >= len(self.EVALUATION_TARGETS):
            self.finalize_evaluation()

        return trial

    def finalize_evaluation(self) -> dict:
        """
        Calculates final accuracy report and exports to evaluation_results.json.
        """
        report = self.compute_report()
        try:
            with open(EVALUATION_FILE, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4)
            logger.info("Evaluation report saved to evaluation_results.json")
        except Exception as e:
            logger.error(f"Error saving evaluation report: {e}")

        self.is_active = False
        return report

    def compute_report(self) -> dict:
        """
        Calculates overall and per-gesture accuracy statistics from empirical trials.
        """
        if not self.trials:
            return {
                "status": "No evaluation data available",
                "total_trials": 0,
                "overall_accuracy_pct": "N/A",
                "per_gesture_accuracy": {}
            }

        total_trials = len(self.trials)
        correct_trials = sum(1 for t in self.trials if t["match"])
        overall_acc = round((correct_trials / total_trials) * 100.0, 1)

        per_gesture: Dict[str, dict] = {}
        for target in self.EVALUATION_TARGETS:
            matching_trials = [t for t in self.trials if t["expected_gesture"] == target]
            if not matching_trials:
                continue
            matches = sum(1 for t in matching_trials if t["match"])
            acc = round((matches / len(matching_trials)) * 100.0, 1)
            per_gesture[target] = {
                "gesture_name": GESTURE_NAMES.get(target, target),
                "trials": len(matching_trials),
                "correct": matches,
                "accuracy_pct": acc
            }

        avg_latency = round(sum(t["response_time_ms"] for t in self.trials) / total_trials, 1)

        return {
            "status": "Completed",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_trials": total_trials,
            "correct_trials": correct_trials,
            "overall_accuracy_pct": overall_acc,
            "average_response_ms": avg_latency,
            "per_gesture_accuracy": per_gesture
        }

    def cancel_evaluation(self):
        """Cancels evaluation session."""
        self.is_active = False
        self.current_target_idx = 0
        logger.info("Evaluation session canceled.")
