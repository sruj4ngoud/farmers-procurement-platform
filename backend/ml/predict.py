"""Prediction module for ML congestion prediction.

Loads the trained model and metadata, then provides a predict() function
that the API endpoint calls.

The model predicts congestion level (LOW / MODERATE / HIGH) for a given
centre + slot combination. Estimated wait time is derived from the
predicted congestion level and slot capacity.
"""

import json
import logging
import pathlib
from datetime import date, datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

from ml.data_preparation import (
    classify_congestion,
    estimate_wait_minutes,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_MODULE_DIR = pathlib.Path(__file__).resolve().parent
_MODEL_DIR = _MODULE_DIR / "model"
_MODEL_PATH = _MODEL_DIR / "queue_congestion_model.joblib"
_METADATA_PATH = _MODEL_DIR / "model_metadata.json"


# ---------------------------------------------------------------------------
# Model loading (cached)
# ---------------------------------------------------------------------------

_model = None
_metadata = None
_label_encoders: dict[str, LabelEncoder] = {}


def _load_model():
    """Load the trained model and metadata from disk (cached)."""
    global _model, _metadata, _label_encoders

    if _model is not None:
        return True

    if not _MODEL_PATH.exists():
        logger.warning("[ML] Model file not found at %s", _MODEL_PATH)
        return False
    if not _METADATA_PATH.exists():
        logger.warning("[ML] Metadata file not found at %s", _METADATA_PATH)
        return False

    try:
        _model = joblib.load(_MODEL_PATH)
        with open(_METADATA_PATH) as f:
            _metadata = json.load(f)

        # Reconstruct LabelEncoders from saved classes
        encoder_data = _metadata.get("label_encoders", {})
        for col, classes in encoder_data.items():
            le = LabelEncoder()
            le.classes_ = np.array(classes)
            _label_encoders[col] = le

        logger.info("[ML] Model loaded successfully from %s", _MODEL_PATH)
        return True
    except Exception as e:
        logger.error("[ML] Failed to load model: %s", e)
        return False


def is_model_available() -> bool:
    """Check if the ML model is loaded and available."""
    return _load_model()


def reload_model() -> bool:
    """Force-reload the model (useful after retraining)."""
    global _model, _metadata, _label_encoders
    _model = None
    _metadata = None
    _label_encoders = {}
    return _load_model()


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

def predict_congestion(
    centre_id: str,
    slot_date: date | str,
    slot_hour: int,
    crop: str = "Unknown",
    avg_quantity: float = 5.0,
    slot_capacity: int = 10,
    current_bookings: int = 0,
) -> dict:
    """Predict congestion level and estimated wait time for a slot.

    Args:
        centre_id: The procurement centre identifier.
        slot_date: The date of the slot.
        slot_hour: The hour of the slot (e.g. 9, 10, 11, 14, 15, 16).
        crop: The crop type (for feature encoding).
        avg_quantity: Average quantity per booking (default 5.0).
        slot_capacity: Maximum farmers the slot can hold.
        current_bookings: How many farmers already booked this slot.

    Returns:
        dict with keys:
            centre_id, slot_date, slot_hour,
            congestion_level (LOW/MODERATE/HIGH),
            predicted_wait_minutes (int),
            current_bookings (int),
            slot_capacity (int),
            confidence_available (bool),
            model_available (bool),
            confidence (float | None),
            message (str | None)
    """
    result = {
        "centre_id": str(centre_id),
        "slot_date": str(slot_date),
        "slot_hour": slot_hour,
        "congestion_level": "UNKNOWN",
        "predicted_wait_minutes": 0,
        "current_bookings": current_bookings,
        "slot_capacity": slot_capacity,
        "confidence_available": False,
        "model_available": False,
        "confidence": None,
        "message": None,
    }

    if not _load_model():
        result["message"] = "AI prediction temporarily unavailable."
        # Fallback: use current_bookings directly
        low_t = 1
        high_t = 3
        if _metadata:
            low_t = _metadata.get("low_threshold", 1)
            high_t = _metadata.get("high_threshold", 3)
        effective = max(current_bookings, 1)  # at least 1 if booked
        result["congestion_level"] = classify_congestion(effective, low_t, high_t)
        result["predicted_wait_minutes"] = estimate_wait_minutes(effective, slot_capacity)
        return result

    result["model_available"] = True

    # Parse date
    if isinstance(slot_date, str):
        try:
            slot_date = datetime.strptime(slot_date, "%Y-%m-%d").date()
        except ValueError:
            slot_date = date.today()

    day_of_week = slot_date.weekday()  # 0=Mon .. 6=Sun
    month = slot_date.month

    # Season
    if month in (6, 7, 8, 9, 10):
        season = "Kharif"
    elif month in (11, 12, 1, 2, 3):
        season = "Rabi"
    else:
        season = "Zaid"

    # Build feature vector matching training order:
    # [centre_id, hour, day_of_week, month, dominant_crop, season, avg_quantity]
    try:
        features = pd.DataFrame(
            [{
                "centre_id": str(centre_id),
                "hour": slot_hour,
                "day_of_week": day_of_week,
                "month": month,
                "dominant_crop": crop,
                "season": season,
                "avg_quantity": avg_quantity,
            }]
        )

        # Encode categorical features
        for col in ["centre_id", "dominant_crop", "season"]:
            le = _label_encoders.get(col)
            if le is not None:
                known = set(le.classes_)
                val = str(features[col].iloc[0])
                if val in known:
                    features[col] = le.transform([val])[0]
                else:
                    features[col] = 0
            else:
                features[col] = 0

        # Predict class
        predicted_level = _model.predict(features.values)[0]
        result["congestion_level"] = str(predicted_level)

        # Get confidence (probability of predicted class)
        if hasattr(_model, "predict_proba"):
            proba = _model.predict_proba(features.values)[0]
            class_idx = list(_model.classes_).index(predicted_level)
            confidence = float(proba[class_idx])
            result["confidence"] = round(confidence, 4)
            result["confidence_available"] = True

        # Combine prediction with current bookings for wait time estimate
        # Use the higher of predicted and current bookings
        low_t = _metadata.get("low_threshold", 1) if _metadata else 1
        high_t = _metadata.get("high_threshold", 3) if _metadata else 3

        # If current bookings suggest higher congestion, override
        if current_bookings > 0:
            current_level = classify_congestion(current_bookings, low_t, high_t)
            level_order = {"LOW": 0, "MODERATE": 1, "HIGH": 2}
            if level_order.get(current_level, 0) > level_order.get(predicted_level, 0):
                result["congestion_level"] = current_level

        # Estimate wait based on effective congestion
        effective_congestion = result["congestion_level"]
        if effective_congestion == "HIGH":
            wait_estimate = estimate_wait_minutes(
                max(current_bookings, high_t + 1), slot_capacity
            )
        elif effective_congestion == "MODERATE":
            wait_estimate = estimate_wait_minutes(
                max(current_bookings, low_t + 1), slot_capacity
            )
        else:
            wait_estimate = estimate_wait_minutes(
                max(current_bookings, 1), slot_capacity
            )

        result["predicted_wait_minutes"] = wait_estimate
        return result

    except Exception as e:
        logger.error("[ML] Prediction failed: %s", e)
        result["message"] = "AI prediction temporarily unavailable."
        # Fallback
        low_t = _metadata.get("low_threshold", 1) if _metadata else 1
        high_t = _metadata.get("high_threshold", 3) if _metadata else 3
        effective = max(current_bookings, 1)
        result["congestion_level"] = classify_congestion(effective, low_t, high_t)
        result["predicted_wait_minutes"] = estimate_wait_minutes(effective, slot_capacity)
        return result


def get_model_info() -> dict:
    """Return metadata about the trained model."""
    if _metadata is None:
        return {"model_available": False}
    return {
        "model_available": True,
        "model_type": _metadata.get("model_type"),
        "evaluation": _metadata.get("evaluation"),
        "thresholds": {
            "low": _metadata.get("low_threshold"),
            "moderate": _metadata.get("high_threshold"),
        },
        "training_rows": _metadata.get("total_training_rows"),
        "total_bookings": _metadata.get("total_bookings"),
    }
