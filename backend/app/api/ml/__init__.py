"""ML prediction endpoints.

Provides slot congestion prediction for farmers.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.slot_service import get_slot_by_id
from ml.predict import get_model_info, predict_congestion

router = APIRouter(prefix="/api/ml", tags=["ml"])


class SlotPredictionResponse(BaseModel):
    """Response for slot congestion prediction."""
    centre_id: str
    slot_id: str | None = None
    slot_date: str
    slot_hour: int
    congestion_level: str
    predicted_wait_minutes: int
    current_bookings: int
    slot_capacity: int
    confidence: float | None = None
    confidence_available: bool = False
    model_available: bool = False
    message: str | None = None


class ModelInfoResponse(BaseModel):
    """Response for model information."""
    model_available: bool
    model_type: str | None = None
    evaluation: dict | None = None
    thresholds: dict | None = None
    training_rows: int | None = None
    total_bookings: int | None = None


@router.get("/slot-prediction", response_model=SlotPredictionResponse)
async def get_slot_prediction(
    centre_id: str,
    slot_date: str = Query(..., description="Slot date in YYYY-MM-DD format"),
    slot_hour: int = Query(..., description="Slot hour (e.g. 9, 10, 11, 14, 15)"),
    crop: str = Query("Unknown", description="Crop type"),
    slot_capacity: int = Query(10, description="Maximum farmers for this slot"),
    current_bookings: int = Query(0, description="Current number of bookings"),
    db: Session = Depends(get_db),
):
    """Predict congestion level and estimated wait time for a slot.

    This endpoint uses the trained ML model to predict how congested
    a particular procurement slot is likely to be.

    The prediction is advisory only — it does NOT override any
    booking rules, slot capacity checks, or transaction safety.
    """
    try:
        # Validate centre_id is not empty
        if not centre_id or not centre_id.strip():
            raise HTTPException(status_code=400, detail="centre_id is required")

        # Parse date
        try:
            parsed_date = date.fromisoformat(slot_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # Validate hour
        if not (0 <= slot_hour <= 23):
            raise HTTPException(status_code=400, detail="Invalid hour. Must be 0-23")

        # Run prediction
        prediction = predict_congestion(
            centre_id=centre_id,
            slot_date=parsed_date,
            slot_hour=slot_hour,
            crop=crop,
            slot_capacity=slot_capacity,
            current_bookings=current_bookings,
        )

        return SlotPredictionResponse(
            centre_id=prediction["centre_id"],
            slot_date=prediction["slot_date"],
            slot_hour=prediction["slot_hour"],
            congestion_level=prediction["congestion_level"],
            predicted_wait_minutes=prediction["predicted_wait_minutes"],
            current_bookings=prediction["current_bookings"],
            slot_capacity=prediction["slot_capacity"],
            confidence=prediction.get("confidence"),
            confidence_available=prediction.get("confidence_available", False),
            model_available=prediction.get("model_available", False),
            message=prediction.get("message"),
        )

    except HTTPException:
        raise
    except Exception as e:
        # Fallback: return a safe default that doesn't block the farmer
        return SlotPredictionResponse(
            centre_id=centre_id,
            slot_date=slot_date,
            slot_hour=slot_hour,
            congestion_level="UNKNOWN",
            predicted_wait_minutes=0,
            current_bookings=current_bookings,
            slot_capacity=slot_capacity,
            model_available=False,
            message="AI prediction temporarily unavailable.",
        )


@router.get("/model-info", response_model=ModelInfoResponse)
async def get_model_information():
    """Return information about the trained ML model.

    Useful for debugging and SIH presentation.
    """
    info = get_model_info()
    return ModelInfoResponse(**info)
