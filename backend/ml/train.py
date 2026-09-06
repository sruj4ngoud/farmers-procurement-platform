"""Train the ML congestion prediction model.

Trains a RandomForestClassifier on historical booking data to predict
congestion level (LOW / MODERATE / HIGH) for a given centre + slot combination.

The model is saved to backend/ml/model/queue_congestion_model.joblib

Usage:
    cd backend
    python -m ml.train
"""

import json
import pathlib
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from ml.data_preparation import prepare_training_data

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_MODULE_DIR = pathlib.Path(__file__).resolve().parent
_MODEL_DIR = _MODULE_DIR / "model"
_MODEL_PATH = _MODEL_DIR / "queue_congestion_model.joblib"
_METADATA_PATH = _MODEL_DIR / "model_metadata.json"


# ---------------------------------------------------------------------------
# Feature encoding
# ---------------------------------------------------------------------------

def encode_features(
    df: pd.DataFrame,
    label_encoders: dict[str, LabelEncoder] | None = None,
    fit: bool = False,
) -> tuple[pd.DataFrame, dict[str, LabelEncoder]]:
    """Encode categorical features into numeric values.

    Features used:
        - centre_id (encoded)
        - hour (as-is)
        - day_of_week (as-is)
        - month (as-is)
        - dominant_crop (encoded)
        - season (encoded)
        - avg_quantity (as-is)
    """
    feature_cols = [
        "centre_id",
        "hour",
        "day_of_week",
        "month",
        "dominant_crop",
        "season",
        "avg_quantity",
    ]

    result = df[feature_cols].copy()

    categorical_cols = ["centre_id", "dominant_crop", "season"]

    if label_encoders is None:
        label_encoders = {}

    for col in categorical_cols:
        if fit:
            le = LabelEncoder()
            result[col] = le.fit_transform(result[col].astype(str))
            label_encoders[col] = le
        else:
            le = label_encoders.get(col)
            if le is None:
                le = LabelEncoder()
                le.fit(result[col].astype(str))
                label_encoders[col] = le
            known = set(le.classes_)
            result[col] = result[col].astype(str).apply(
                lambda x: le.transform([x])[0] if x in known else -1
            )

    return result, label_encoders


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_model(
    csv_path: str | pathlib.Path | None = None,
    random_state: int = 42,
    test_size: float = 0.2,
) -> dict:
    """Train the congestion prediction model.

    Returns a dict with evaluation metrics and metadata.
    """
    # 1. Prepare data
    slots_df, metadata = prepare_training_data(csv_path)

    print(f"[ML] Training data: {metadata['total_training_rows']} slot rows")
    print(f"[ML] Congestion thresholds: LOW<={metadata['low_threshold']}, "
          f"MODERATE<={metadata['high_threshold']}, HIGH>{metadata['high_threshold']}")
    print(f"[ML] Congestion level distribution:")
    dist = slots_df["congestion_level"].value_counts()
    for level in ["LOW", "MODERATE", "HIGH"]:
        count = dist.get(level, 0)
        print(f"    {level:10s}: {count} ({count/len(slots_df)*100:.1f}%)")

    # 2. Encode features
    features_df, label_encoders = encode_features(slots_df, fit=True)
    target = slots_df["congestion_level"].values

    # 3. Train/test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        features_df.values,
        target,
        test_size=test_size,
        random_state=random_state,
        stratify=target,
    )

    print(f"\n[ML] Train: {len(X_train)} rows, Test: {len(X_test)} rows")

    # 4. Train RandomForestClassifier
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=random_state,
        n_jobs=-1,
        class_weight="balanced",  # Handle class imbalance
    )
    model.fit(X_train, y_train)

    # 5. Evaluate
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    precision_weighted = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    recall_weighted = recall_score(y_test, y_pred, average="weighted", zero_division=0)

    print(f"\n[ML] === Evaluation Metrics ===")
    print(f"    Accuracy:  {accuracy:.4f}")
    print(f"    Precision: {precision_weighted:.4f} (weighted)")
    print(f"    Recall:    {recall_weighted:.4f} (weighted)")
    print(f"    F1 Score:  {f1_weighted:.4f} (weighted)")

    print(f"\n[ML] Classification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # 6. Feature importance
    importances = model.feature_importances_
    feature_names = list(features_df.columns)
    print(f"[ML] Feature Importances:")
    for name, imp in sorted(
        zip(feature_names, importances), key=lambda x: -x[1]
    ):
        print(f"    {name:20s}: {imp:.4f}")

    # 7. Save model
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, _MODEL_PATH)
    print(f"\n[ML] Model saved to {_MODEL_PATH}")

    # 8. Save metadata + label encoders + thresholds
    encoder_data = {}
    for col, le in label_encoders.items():
        encoder_data[col] = le.classes_.tolist()

    save_meta = {
        **metadata,
        "feature_columns": feature_names,
        "label_encoders": encoder_data,
        "model_type": "RandomForestClassifier",
        "n_estimators": 100,
        "max_depth": 10,
        "random_state": random_state,
        "test_size": test_size,
        "evaluation": {
            "accuracy": float(accuracy),
            "precision_weighted": float(precision_weighted),
            "recall_weighted": float(recall_weighted),
            "f1_weighted": float(f1_weighted),
            "test_rows": len(X_test),
            "train_rows": len(X_train),
        },
    }

    with open(_METADATA_PATH, "w") as f:
        json.dump(save_meta, f, indent=2)
    print(f"[ML] Metadata saved to {_METADATA_PATH}")

    return {
        "accuracy": float(accuracy),
        "precision": float(precision_weighted),
        "recall": float(recall_weighted),
        "f1": float(f1_weighted),
        "model_path": str(_MODEL_PATH),
        "metadata_path": str(_METADATA_PATH),
        "metadata": save_meta,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    result = train_model(csv_path)
    print(f"\n[ML] Training complete. Accuracy={result['accuracy']:.4f}, F1={result['f1']:.4f}")
