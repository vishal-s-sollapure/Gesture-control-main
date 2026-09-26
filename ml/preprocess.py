"""
GestureControl AI - Landmark Normalization Preprocessor
Translates landmarks to wrist origin and scales vectors by maximum hand span
to generate scale and position-invariant 63-dimensional feature vectors.
"""

import math
from typing import List, Dict


def normalize_landmarks(landmarks: List[Dict[str, float]]) -> List[float]:
    """
    Normalizes 21 3D hand landmarks to produce position- and scale-invariant 63-element feature vector.

    Args:
        landmarks: List of 21 landmark dictionaries with 'x', 'y', 'z' keys.

    Returns:
        List of 63 float values: [x0', y0', z0', x1', y1', z1', ..., x20', y20', z20']
    """
    if not landmarks or len(landmarks) < 21:
        return [0.0] * 63

    wrist = landmarks[0]
    translated = []
    max_dist = 0.0001  # Prevent division by zero

    for lm in landmarks:
        dx = lm["x"] - wrist["x"]
        dy = lm["y"] - wrist["y"]
        dz = lm["z"] - wrist["z"]
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        if dist > max_dist:
            max_dist = dist
        translated.append((dx, dy, dz))

    # Scale normalize by max hand span
    feature_vector = []
    for dx, dy, dz in translated:
        feature_vector.extend([
            round(dx / max_dist, 5),
            round(dy / max_dist, 5),
            round(dz / max_dist, 5)
        ])

    return feature_vector
