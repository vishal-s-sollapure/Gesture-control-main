"""
GestureControl AI - Machine Learning Model Trainer & Evaluator
Loads 63-dimensional normalized landmark dataset, executes train/test split,
trains a Random Forest classifier, and evaluates Accuracy, Precision, Recall, F1, and Confusion Matrix.
"""

import csv
import json
import pickle
from pathlib import Path
import numpy as np

DATASET_PATH = Path(__file__).resolve().parent / "data" / "landmarks_dataset.csv"
MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"
REPORT_PATH = Path(__file__).resolve().parent / "evaluation_report.json"


def train_and_evaluate(
    dataset_path: Path = DATASET_PATH,
    model_path: Path = MODEL_PATH,
    report_path: Path = REPORT_PATH
) -> dict:
    """
    Executes ML training workflow: dataset loading -> train/test split -> RandomForest training
    -> metrics computation (Accuracy, Precision, Recall, F1, Confusion Matrix) -> model export.
    """
    if not dataset_path.exists():
        print(f"[ML Trainer] Dataset missing at: {dataset_path}")
        return {}

    labels = []
    features = []

    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if row:
                labels.append(row[0])
                features.append([float(x) for x in row[1:]])

    X = np.array(features)
    y = np.array(labels)

    try:
        from sklearn.model_selection import train_test_split
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
            confusion_matrix,
            classification_report
        )

        # 80% Train, 20% Test stratified split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        clf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
        clf.fit(X_train, y_train)

        # Evaluate on Test Set
        y_pred = clf.predict(X_test)
        classes = sorted(list(set(y)))

        acc = accuracy_score(y_test, y_pred)
        prec_weighted = precision_score(y_test, y_pred, average="weighted")
        rec_weighted = recall_score(y_test, y_pred, average="weighted")
        f1_weighted = f1_score(y_test, y_pred, average="weighted")

        prec_macro = precision_score(y_test, y_pred, average="macro")
        rec_macro = recall_score(y_test, y_pred, average="macro")
        f1_macro = f1_score(y_test, y_pred, average="macro")

        cm = confusion_matrix(y_test, y_pred, labels=classes)

        report_dict = {
            "dataset_total_samples": len(y),
            "train_samples": len(y_train),
            "test_samples": len(y_test),
            "classes": classes,
            "overall_accuracy_pct": round(acc * 100.0, 2),
            "precision_weighted": round(prec_weighted, 4),
            "recall_weighted": round(rec_weighted, 4),
            "f1_score_weighted": round(f1_weighted, 4),
            "precision_macro": round(prec_macro, 4),
            "recall_macro": round(rec_macro, 4),
            "f1_score_macro": round(f1_macro, 4),
            "confusion_matrix": cm.tolist()
        }

        # Save trained Random Forest model artifact
        model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(model_path, "wb") as f:
            pickle.dump(clf, f)

        # Save detailed evaluation metrics report
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=4)

        print("==================================================")
        print(" GESTURE RECOGNITION ML MODEL TRAINING COMPLETE ")
        print("==================================================")
        print(f" Train Samples:        {len(y_train)}")
        print(f" Test Samples:         {len(y_test)}")
        print(f" Test Accuracy:        {acc * 100.0:.2f}%")
        print(f" Weighted F1-Score:    {f1_weighted:.4f}")
        print(f" Weighted Precision:   {prec_weighted:.4f}")
        print(f" Weighted Recall:      {rec_weighted:.4f}")
        print(f" Model saved to:       {model_path}")
        print(f" Report saved to:      {report_path}")
        print("==================================================")

        return report_dict

    except ImportError:
        print("[ML Trainer] scikit-learn is missing. Fallback evaluation mode.")
        return {}


if __name__ == "__main__":
    train_and_evaluate()
