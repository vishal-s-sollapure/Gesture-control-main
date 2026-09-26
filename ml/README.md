# GestureControl AI — Machine Learning Pipeline

This module provides an optional Machine Learning gesture recognition pipeline that operates on MediaPipe 21-point hand landmarks.

## Architecture

```
Webcam Frame → MediaPipe Hand Tracker → 21 Hand Landmarks (x, y, z)
  → Landmark Normalization (Wrist Origin + Span Scale)
  → 63-Dimensional Feature Vector
  → ML Classifier (RandomForest / SVM) → Gesture State Machine → System Action
```

## Landmark Feature Normalization

Raw MediaPipe coordinates $(x, y, z)$ are normalized to ensure scale and position invariance:
1. **Translation Invariance**: Subtract Wrist Landmark $L_0(x, y, z)$ from all 21 points.
2. **Scale Invariance**: Divide all coordinate vectors by the maximum Euclidean distance between the wrist and finger tips (Hand Span $S$).

$$\mathbf{v}_{\text{normalized}} = \frac{\mathbf{p}_i - \mathbf{p}_{\text{wrist}}}{\max_{j} \|\mathbf{p}_j - \mathbf{p}_{\text{wrist}}\|}$$

This yields a 63-element normalized feature vector:
$$\mathbf{X} = [x_0', y_0', z_0', x_1', y_1', z_1', \dots, x_{20}', y_{20}', z_{20}']$$

## Usage Instructions

### 1. Collect Landmark Data
Run the dataset collector CLI to record labeled gesture training samples:
```bash
python ml/collect_data.py --gesture PINCH --samples 100
```

### 2. Train Gesture Classifier
Train a Random Forest classifier on collected landmark samples:
```bash
python ml/train.py --dataset ml/data/landmarks_dataset.csv --output ml/model.pkl
```

### 3. Evaluate Classifier Performance
Compute confusion matrix, per-gesture accuracy, precision, and recall:
```bash
python ml/evaluate.py --model ml/model.pkl --dataset ml/data/landmarks_dataset.csv
```
