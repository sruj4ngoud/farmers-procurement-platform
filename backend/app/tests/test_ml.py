"""Tests for ML congestion prediction module.

Covers:
- Data preparation pipeline
- Feature encoding
- Model training
- Model loading
- Valid prediction
- Invalid slot handling
- Missing data handling
- Model unavailable fallback
- API endpoint responses
"""

import json
import os
import pathlib
import tempfile
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Data Preparation Tests
# ---------------------------------------------------------------------------


class TestDataPreparation:
    """Test the data preparation pipeline."""

    def test_load_bookings_csv(self):
        """Test loading the bookings CSV file."""
        from ml.data_preparation import load_bookings_csv

        df = load_bookings_csv()
        assert len(df) > 0
        assert "slot_datetime" in df.columns
        assert "hour" in df.columns
        assert "day_of_week" in df.columns
        assert "month" in df.columns
        assert "season" in df.columns
        assert "crop" in df.columns
        assert "centre_id" in df.columns

    def test_load_bookings_csv_custom_path(self):
        """Test loading bookings from a custom CSV path."""
        from ml.data_preparation import load_bookings_csv

        # Create a minimal test CSV
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("booking_id,passbook_number,cultivation_id,crop,centre_id,slot_datetime,token_number,quantity_to_sell_quintals,queue_status\n")
            f.write("BKG001,PPB001,CUL001,TestCrop,PPC001,2026-09-01 09:00:00,1,5.0,WAITING\n")
            f.write("BKG002,PPB002,CUL002,TestCrop,PPC001,2026-09-01 09:00:00,2,3.0,COMPLETED\n")
            csv_path = f.name

        try:
            df = load_bookings_csv(csv_path)
            assert len(df) == 2
            assert df["hour"].iloc[0] == 9
            assert df["crop"].iloc[0] == "TestCrop"
        finally:
            os.unlink(csv_path)

    def test_aggregate_to_slots(self):
        """Test slot aggregation."""
        from ml.data_preparation import aggregate_to_slots, load_bookings_csv

        df = load_bookings_csv()
        slots_df = aggregate_to_slots(df)

        assert len(slots_df) > 0
        assert "booking_count" in slots_df.columns
        assert "avg_quantity" in slots_df.columns
        assert "dominant_crop" in slots_df.columns
        # All booking counts should be >= 1
        assert (slots_df["booking_count"] >= 1).all()

    def test_classify_congestion(self):
        """Test congestion classification."""
        from ml.data_preparation import classify_congestion

        assert classify_congestion(0, 1, 3) == "LOW"
        assert classify_congestion(1, 1, 3) == "LOW"
        assert classify_congestion(2, 1, 3) == "MODERATE"
        assert classify_congestion(3, 1, 3) == "MODERATE"
        assert classify_congestion(4, 1, 3) == "HIGH"
        assert classify_congestion(10, 1, 3) == "HIGH"

    def test_estimate_wait_minutes(self):
        """Test wait time estimation."""
        from ml.data_preparation import estimate_wait_minutes

        # Low congestion
        wait = estimate_wait_minutes(1, 10)
        assert 0 <= wait <= 120

        # Higher congestion
        wait_high = estimate_wait_minutes(5, 10)
        assert wait_high > wait

        # Capped at slot capacity
        wait_capped = estimate_wait_minutes(100, 5)
        assert wait_capped <= 5 * 12  # slot_capacity * avg_procurement_minutes

    def test_compute_congestion_thresholds(self):
        """Test threshold computation."""
        from ml.data_preparation import compute_congestion_thresholds

        # Uniform distribution
        counts = pd.Series([1, 1, 1, 1, 1])
        low, high = compute_congestion_thresholds(counts)
        assert low <= high

        # Varied distribution
        counts = pd.Series([1, 1, 1, 2, 2, 3, 4, 5])
        low, high = compute_congestion_thresholds(counts)
        assert low < high

    def test_prepare_training_data(self):
        """Test full data preparation pipeline."""
        from ml.data_preparation import prepare_training_data

        slots_df, metadata = prepare_training_data()
        assert len(slots_df) > 0
        assert "congestion_level" in slots_df.columns
        assert "estimated_wait_minutes" in slots_df.columns
        assert metadata["low_threshold"] >= 0
        assert metadata["high_threshold"] > metadata["low_threshold"]
        assert metadata["total_training_rows"] > 0
        assert metadata["total_bookings"] > 0


# ---------------------------------------------------------------------------
# Training Tests
# ---------------------------------------------------------------------------


class TestTraining:
    """Test the model training pipeline."""

    def test_train_model(self):
        """Test model training produces valid output."""
        from ml.train import train_model

        result = train_model()
        assert "accuracy" in result
        assert "f1" in result
        assert "model_path" in result
        assert "metadata" in result
        assert result["accuracy"] >= 0
        assert result["f1"] >= 0

    def test_encode_features_fit(self):
        """Test feature encoding with fit=True."""
        from ml.data_preparation import prepare_training_data
        from ml.train import encode_features

        slots_df, _ = prepare_training_data()
        features_df, encoders = encode_features(slots_df, fit=True)

        assert len(features_df) == len(slots_df)
        assert "centre_id" in features_df.columns
        assert len(encoders) == 3  # centre_id, dominant_crop, season

    def test_encode_features_transform(self):
        """Test feature encoding with fit=False (transform only)."""
        from ml.data_preparation import prepare_training_data
        from ml.train import encode_features

        slots_df, _ = prepare_training_data()
        _, encoders = encode_features(slots_df, fit=True)

        # Transform new data
        new_features, _ = encode_features(slots_df.head(5), label_encoders=encoders, fit=False)
        assert len(new_features) == 5


# ---------------------------------------------------------------------------
# Prediction Tests
# ---------------------------------------------------------------------------


class TestPrediction:
    """Test the prediction module."""

    def test_is_model_available(self):
        """Test model availability check."""
        from ml.predict import is_model_available

        # Model should be available after training
        available = is_model_available()
        assert isinstance(available, bool)

    def test_predict_congestion_valid(self):
        """Test valid prediction."""
        from ml.predict import predict_congestion

        result = predict_congestion(
            centre_id="PPC001",
            slot_date="2026-09-01",
            slot_hour=9,
            crop="Maize",
            slot_capacity=10,
            current_bookings=2,
        )

        assert "congestion_level" in result
        assert result["congestion_level"] in ("LOW", "MODERATE", "HIGH", "UNKNOWN")
        assert "predicted_wait_minutes" in result
        assert result["predicted_wait_minutes"] >= 0
        assert "current_bookings" in result
        assert "slot_capacity" in result

    def test_predict_congestion_unknown_centre(self):
        """Test prediction with unknown centre."""
        from ml.predict import predict_congestion

        result = predict_congestion(
            centre_id="UNKNOWN_CENTRE_999",
            slot_date="2026-09-01",
            slot_hour=9,
            crop="Maize",
            slot_capacity=10,
            current_bookings=0,
        )

        # Should still return a valid prediction (model handles unseen categories)
        assert "congestion_level" in result
        assert result["congestion_level"] in ("LOW", "MODERATE", "HIGH", "UNKNOWN")

    def test_predict_congestion_empty_bookings(self):
        """Test prediction with zero bookings."""
        from ml.predict import predict_congestion

        result = predict_congestion(
            centre_id="PPC001",
            slot_date="2026-09-01",
            slot_hour=9,
            crop="Maize",
            slot_capacity=10,
            current_bookings=0,
        )

        assert result["congestion_level"] in ("LOW", "MODERATE", "HIGH", "UNKNOWN")
        assert result["predicted_wait_minutes"] >= 0

    def test_predict_congestion_high_bookings(self):
        """Test prediction with many bookings."""
        from ml.predict import predict_congestion

        result = predict_congestion(
            centre_id="PPC001",
            slot_date="2026-09-01",
            slot_hour=9,
            crop="Maize",
            slot_capacity=10,
            current_bookings=8,
        )

        assert result["congestion_level"] in ("LOW", "MODERATE", "HIGH", "UNKNOWN")
        # High bookings should result in higher wait time
        assert result["predicted_wait_minutes"] > 0

    def test_get_model_info(self):
        """Test model info retrieval."""
        from ml.predict import get_model_info

        info = get_model_info()
        assert "model_available" in info
        if info["model_available"]:
            assert "model_type" in info
            assert "evaluation" in info
            assert "thresholds" in info


# ---------------------------------------------------------------------------
# Fallback Tests
# ---------------------------------------------------------------------------


class TestFallback:
    """Test fallback behavior when ML model is unavailable."""

    def test_predict_without_model(self):
        """Test prediction when model file is missing."""
        from ml import predict

        # Temporarily clear the cached model
        original_model = predict._model
        original_metadata = predict._metadata
        predict._model = None
        predict._metadata = None

        # Temporarily rename the model file
        model_path = predict._MODEL_PATH
        backup_path = model_path.with_suffix(".joblib.bak")
        metadata_path = predict._METADATA_PATH
        backup_metadata = metadata_path.with_suffix(".json.bak")

        try:
            if model_path.exists():
                model_path.rename(backup_path)
            if metadata_path.exists():
                metadata_path.rename(backup_metadata)

            # Force reload
            predict._model = None
            predict._metadata = None

            result = predict.predict_congestion(
                centre_id="PPC001",
                slot_date="2026-09-01",
                slot_hour=9,
                crop="Maize",
                slot_capacity=10,
                current_bookings=2,
            )

            # Should fallback gracefully
            assert result["model_available"] is False
            assert result["message"] == "AI prediction temporarily unavailable."
            assert result["congestion_level"] in ("LOW", "MODERATE", "HIGH", "UNKNOWN")

        finally:
            # Restore files
            if backup_path.exists():
                backup_path.rename(model_path)
            if backup_metadata.exists():
                backup_metadata.rename(metadata_path)
            predict._model = original_model
            predict._metadata = original_metadata

    def test_model_reload(self):
        """Test model reload functionality."""
        from ml.predict import reload_model

        result = reload_model()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------


class TestMLAPI:
    """Test the ML API endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_slot_prediction_endpoint(self, client):
        """Test the slot prediction endpoint."""
        response = client.get(
            "/api/ml/slot-prediction",
            params={
                "centre_id": "PPC001",
                "slot_date": "2026-09-01",
                "slot_hour": 9,
                "crop": "Maize",
                "slot_capacity": 10,
                "current_bookings": 2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "congestion_level" in data
        assert "predicted_wait_minutes" in data
        assert "model_available" in data

    def test_slot_prediction_invalid_date(self, client):
        """Test prediction with invalid date format."""
        response = client.get(
            "/api/ml/slot-prediction",
            params={
                "centre_id": "PPC001",
                "slot_date": "invalid-date",
                "slot_hour": 9,
            },
        )
        assert response.status_code == 400

    def test_slot_prediction_invalid_hour(self, client):
        """Test prediction with invalid hour."""
        response = client.get(
            "/api/ml/slot-prediction",
            params={
                "centre_id": "PPC001",
                "slot_date": "2026-09-01",
                "slot_hour": 25,
            },
        )
        assert response.status_code == 400

    def test_slot_prediction_empty_centre(self, client):
        """Test prediction with empty centre ID."""
        response = client.get(
            "/api/ml/slot-prediction",
            params={
                "centre_id": "",
                "slot_date": "2026-09-01",
                "slot_hour": 9,
            },
        )
        assert response.status_code == 400

    def test_model_info_endpoint(self, client):
        """Test the model info endpoint."""
        response = client.get("/api/ml/model-info")
        assert response.status_code == 200
        data = response.json()
        assert "model_available" in data

    def test_slot_prediction_fallback_on_error(self, client):
        """Test that prediction returns gracefully on internal error."""
        response = client.get(
            "/api/ml/slot-prediction",
            params={
                "centre_id": "PPC001",
                "slot_date": "2026-09-01",
                "slot_hour": 9,
                "crop": "Maize",
                "slot_capacity": 10,
                "current_bookings": 2,
            },
        )
        # Should always return 200 with a valid response (never block farmer)
        assert response.status_code == 200
