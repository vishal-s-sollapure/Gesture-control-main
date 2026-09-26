"""
GestureControl AI - Dataset Collector & Synthetic Benchmark Generator
Generates realistic 21-point hand landmark samples across 8 gesture classes:
  1. INDEX (Cursor Pointing)
  2. PINCH (Thumb-Index Pinch)
  3. THREE_FINGERS (Index, Middle, Ring up)
  4. OPEN_PALM (Open Hand)
  5. FIST (Closed Hand)
  6. THUMBS_UP (Thumb Extended)
  7. SWIPE_LEFT (Palm Tilted Left)
  8. SWIPE_RIGHT (Palm Tilted Right)

Outputs normalized 63-dimensional feature vectors to ml/data/landmarks_dataset.csv.
"""

import csv
import math
import random
from pathlib import Path
from ml.preprocess import normalize_landmarks

DATASET_PATH = Path(__file__).resolve().parent / "data" / "landmarks_dataset.csv"

GESTURE_CLASSES = [
    "INDEX",
    "PINCH",
    "THREE_FINGERS",
    "OPEN_PALM",
    "FIST",
    "THUMBS_UP",
    "SWIPE_LEFT",
    "SWIPE_RIGHT"
]


def generate_synthetic_landmarks(gesture_label: str) -> list:
    """
    Generates realistic 21 3D hand landmarks ({'x', 'y', 'z'}) for target gesture pose,
    with physiological noise and joint angle variations.
    """
    lms = [{"x": 0.5, "y": 0.8, "z": 0.0} for _ in range(21)]

    # Base MCPs
    lms[1] = {"x": 0.42, "y": 0.72, "z": 0.0}  # THUMB_CMC
    lms[2] = {"x": 0.38, "y": 0.65, "z": 0.0}  # THUMB_MCP
    lms[3] = {"x": 0.35, "y": 0.58, "z": 0.0}  # THUMB_IP
    lms[4] = {"x": 0.32, "y": 0.52, "z": 0.0}  # THUMB_TIP

    lms[5] = {"x": 0.45, "y": 0.60, "z": 0.0}  # INDEX_MCP
    lms[6] = {"x": 0.45, "y": 0.50, "z": 0.0}  # INDEX_PIP
    lms[7] = {"x": 0.45, "y": 0.40, "z": 0.0}  # INDEX_DIP
    lms[8] = {"x": 0.45, "y": 0.30, "z": 0.0}  # INDEX_TIP

    lms[9] = {"x": 0.50, "y": 0.60, "z": 0.0}  # MIDDLE_MCP
    lms[10] = {"x": 0.50, "y": 0.50, "z": 0.0} # MIDDLE_PIP
    lms[11] = {"x": 0.50, "y": 0.40, "z": 0.0} # MIDDLE_DIP
    lms[12] = {"x": 0.50, "y": 0.30, "z": 0.0} # MIDDLE_TIP

    lms[13] = {"x": 0.55, "y": 0.60, "z": 0.0} # RING_MCP
    lms[14] = {"x": 0.55, "y": 0.50, "z": 0.0} # RING_PIP
    lms[15] = {"x": 0.55, "y": 0.40, "z": 0.0} # RING_DIP
    lms[16] = {"x": 0.55, "y": 0.30, "z": 0.0} # RING_TIP

    lms[17] = {"x": 0.60, "y": 0.60, "z": 0.0} # PINKY_MCP
    lms[18] = {"x": 0.60, "y": 0.52, "z": 0.0} # PINKY_PIP
    lms[19] = {"x": 0.60, "y": 0.44, "z": 0.0} # PINKY_DIP
    lms[20] = {"x": 0.60, "y": 0.36, "z": 0.0} # PINKY_TIP

    # Adjust tip y-coordinates based on extended vs folded posture
    if gesture_label == "INDEX":
        # Index extended, others folded
        lms[8]["y"] = 0.25
        lms[12]["y"] = 0.55
        lms[16]["y"] = 0.55
        lms[20]["y"] = 0.55

    elif gesture_label == "PINCH":
        # Thumb tip and Index tip touching
        lms[8]["x"] = 0.42
        lms[8]["y"] = 0.40
        lms[4]["x"] = 0.41
        lms[4]["y"] = 0.41

    elif gesture_label == "THREE_FINGERS":
        # Index, Middle, Ring up, Pinky folded
        lms[8]["y"] = 0.25
        lms[12]["y"] = 0.25
        lms[16]["y"] = 0.25
        lms[20]["y"] = 0.55

    elif gesture_label == "OPEN_PALM":
        # All 5 extended
        lms[4]["y"] = 0.45
        lms[8]["y"] = 0.25
        lms[12]["y"] = 0.23
        lms[16]["y"] = 0.25
        lms[20]["y"] = 0.28

    elif gesture_label == "FIST":
        # All 5 folded close to MCPs
        lms[4]["y"] = 0.60
        lms[8]["y"] = 0.58
        lms[12]["y"] = 0.58
        lms[16]["y"] = 0.58
        lms[20]["y"] = 0.58

    elif gesture_label == "THUMBS_UP":
        # Thumb tip extended upwards, others folded
        lms[4]["x"] = 0.30
        lms[4]["y"] = 0.35
        lms[8]["y"] = 0.58
        lms[12]["y"] = 0.58
        lms[16]["y"] = 0.58
        lms[20]["y"] = 0.58

    elif gesture_label == "SWIPE_LEFT":
        # Open hand tilted leftward (-25 degree roll angle)
        angle = math.radians(-25)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        for lm in lms:
            dx = lm["x"] - 0.5
            dy = lm["y"] - 0.8
            lm["x"] = 0.5 + (dx * cos_a - dy * sin_a)
            lm["y"] = 0.8 + (dx * sin_a + dy * cos_a)

    elif gesture_label == "SWIPE_RIGHT":
        # Open hand tilted rightward (+25 degree roll angle)
        angle = math.radians(25)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        for lm in lms:
            dx = lm["x"] - 0.5
            dy = lm["y"] - 0.8
            lm["x"] = 0.5 + (dx * cos_a - dy * sin_a)
            lm["y"] = 0.8 + (dx * sin_a + dy * cos_a)

    # Add subtle physiological noise to landmark positions
    for lm in lms:
        lm["x"] += random.gauss(0, 0.008)
        lm["y"] += random.gauss(0, 0.008)
        lm["z"] += random.gauss(0, 0.004)

    return lms


def build_dataset(samples_per_class: int = 150, dataset_path: Path = DATASET_PATH):
    """
    Builds CSV dataset containing normalized landmark feature vectors for all 8 gesture classes.
    """
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    total_samples = 0

    with open(dataset_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["label"] + [f"feat_{i}" for i in range(63)]
        writer.writerow(header)

        for gesture in GESTURE_CLASSES:
            for _ in range(samples_per_class):
                raw_lms = generate_synthetic_landmarks(gesture)
                features = normalize_landmarks(raw_lms)
                writer.writerow([gesture] + features)
                total_samples += 1

    print(f"[ML Dataset Generator] Generated {total_samples} samples across {len(GESTURE_CLASSES)} classes.")
    print(f"[ML Dataset Generator] Dataset saved to: {dataset_path}")


if __name__ == "__main__":
    build_dataset(samples_per_class=150)
