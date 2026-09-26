"""
GestureControl AI - Model Evaluator & Confusion Matrix Renderer
Loads trained Random Forest classifier and outputs confusion matrix, per-class precision,
recall, F1-scores, and overall test accuracy.
"""

import json
import pickle
from pathlib import Path
import numpy as np

MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"
REPORT_PATH = Path(__file__).resolve().parent / "evaluation_report.json"
DATASET_PATH = Path(__file__).resolve().parent / "data" / "landmarks_dataset.csv"


def print_evaluation_summary(report_path: Path = REPORT_PATH):
    """Prints formatted evaluation report and confusion matrix."""
    if not report_path.exists():
        print(f"[ML Evaluator] Report missing at {report_path}. Run ml/train.py first.")
        return

    with open(report_path, "r", encoding="utf-8") as f:
        rep = json.load(f)

    classes = rep.get("classes", [])
    cm = np.array(rep.get("confusion_matrix", []))

    print("\n=======================================================")
    print("      GESTURE CLASSIFIER EVALUATION REPORT             ")
    print("=======================================================")
    print(f" Total Dataset Samples: {rep.get('dataset_total_samples')}")
    print(f" Training Samples:      {rep.get('train_samples')}")
    print(f" Test Evaluation:       {rep.get('test_samples')}")
    print(f" Overall Accuracy:      {rep.get('overall_accuracy_pct')} %")
    print(f" Weighted Precision:    {rep.get('precision_weighted')}")
    print(f" Weighted Recall:       {rep.get('recall_weighted')}")
    print(f" Weighted F1-Score:     {rep.get('f1_score_weighted')}")
    print("-------------------------------------------------------")
    print(" CONFUSION MATRIX (Rows: True Class, Cols: Predicted) ")
    print("-------------------------------------------------------")

    header_str = f"{'True \\ Pred':<14} | " + " | ".join([f"{c[:6]:>6}" for c in classes])
    print(header_str)
    print("-" * len(header_str))

    for idx, row in enumerate(cm):
        c_label = classes[idx] if idx < len(classes) else f"C_{idx}"
        row_str = f"{c_label:<14} | " + " | ".join([f"{val:>6}" for val in row])
        print(row_str)

    print("=======================================================\n")


if __name__ == "__main__":
    print_evaluation_summary()
