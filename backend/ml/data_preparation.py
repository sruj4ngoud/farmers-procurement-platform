"""Data preparation for ML congestion prediction.

Loads historical booking data, engineers features, and prepares
training data for the congestion prediction model.

Target: booking_count per (centre_id, date, hour) slot.
    - LOW: booking_count <= low_threshold (default: 1)
    - MODERATE: low_threshold < booking_count <= high_threshold (default: 3)
    - HIGH: booking_count > high_threshold (default: 3)

The thresholds are computed from the training data distribution.
"""

import os
import pathlib
from datetime import datetime

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_MODULE_DIR = pathlib.Path(__file__).resolve().parent
_PROJECT_ROOT = _MODULE_DIR.parent.parent  # farmer-procurement-platform-main/
_DATA_DIR = _PROJECT_ROOT / "data"
_BOOKINGS_CSV = _DATA_DIR / "bookings_queue.csv"


# ---------------------------------------------------------------------------
# Load raw booking data
# ---------------------------------------------------------------------------

def load_bookings_csv(csv_path: str | pathlib.Path | None = None) -> pd.DataFrame:
    """Load the bookings_queue.csv and return a cleaned DataFrame.

    Columns returned:
        booking_id, passbook_number, cultivation_id, crop, centre_id,
        slot_datetime (datetime), hour, day_of_week, month, season,
        token_number, quantity_to_sell, queue_status
    """
    path = csv_path or _BOOKINGS_CSV
    df = pd.read_csv(path)

    # Parse slot_datetime
    df["slot_datetime"] = pd.to_datetime(df["slot_datetime"])
    df["date"] = df["slot_datetime"].dt.date
    df["hour"] = df["slot_datetime"].dt.hour
    df["day_of_week"] = df["slot_datetime"].dt.dayofweek  # 0=Mon .. 6=Sun
    df["month"] = df["slot_datetime"].dt.month

    # Season heuristic: Kharif=Jun-Oct, Rabi=Nov-Mar, Zaid=Apr-May
    def _season(m: int) -> str:
        if m in (6, 7, 8, 9, 10):
            return "Kharif"
        elif m in (11, 12, 1, 2, 3):
            return "Rabi"
        else:
            return "Zaid"

    df["season"] = df["month"].apply(_season)
    df["quantity_to_sell"] = pd.to_numeric(
        df["quantity_to_sell_quintals"], errors="coerce"
    ).fillna(0.0)

    return df


# ---------------------------------------------------------------------------
# Feature engineering: aggregate to slot level
# ---------------------------------------------------------------------------

def aggregate_to_slots(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate individual bookings to one row per (centre_id, date, hour).

    Returns DataFrame with columns:
        centre_id, date, hour, day_of_week, month, season,
        booking_count, avg_quantity, dominant_crop
    """
    slot_agg = (
        df.groupby(["centre_id", "date", "hour"])
        .agg(
            booking_count=("booking_id", "count"),
            avg_quantity=("quantity_to_sell", "mean"),
            dominant_crop=("crop", lambda x: x.mode().iloc[0] if len(x) > 0 else "Unknown"),
            day_of_week=("day_of_week", "first"),
            month=("month", "first"),
            season=("season", "first"),
        )
        .reset_index()
    )
    return slot_agg


# ---------------------------------------------------------------------------
# Classify congestion level
# ---------------------------------------------------------------------------

def classify_congestion(booking_count: int, low_thresh: int, high_thresh: int) -> str:
    """Map booking_count to LOW / MODERATE / HIGH."""
    if booking_count <= low_thresh:
        return "LOW"
    elif booking_count <= high_thresh:
        return "MODERATE"
    else:
        return "HIGH"


def compute_congestion_thresholds(
    booking_counts: pd.Series,
    low_pct: float = 0.33,
    high_pct: float = 0.67,
) -> tuple[int, int]:
    """Compute thresholds from the booking_count distribution.

    Returns (low_threshold, high_threshold).
    """
    low_thresh = int(np.percentile(booking_counts, low_pct * 100))
    high_thresh = int(np.percentile(booking_counts, high_pct * 100))
    # Ensure at least 1 apart
    if high_thresh <= low_thresh:
        high_thresh = low_thresh + 1
    return low_thresh, high_thresh


# ---------------------------------------------------------------------------
# Estimate wait time from congestion
# ---------------------------------------------------------------------------

def estimate_wait_minutes(
    booking_count: int,
    slot_capacity: int,
    avg_procurement_minutes: float = 12.0,
) -> int:
    """Estimate waiting time based on congestion level.

    Uses a simple model: wait ≈ booking_count * avg_procurement_minutes * 0.5
    (assuming roughly half the people ahead of you are still being served).

    Capped at slot_capacity * avg_procurement_minutes as a hard upper bound.
    """
    if slot_capacity <= 0:
        slot_capacity = 10  # fallback default
    estimated = booking_count * avg_procurement_minutes * 0.5
    max_wait = slot_capacity * avg_procurement_minutes
    return min(int(round(estimated)), int(round(max_wait)))


# ---------------------------------------------------------------------------
# Full data preparation pipeline
# ---------------------------------------------------------------------------

def prepare_training_data(
    csv_path: str | pathlib.Path | None = None,
) -> tuple[pd.DataFrame, dict]:
    """End-to-end data preparation.

    Returns:
        features_df: DataFrame with engineered features ready for training.
        metadata: dict with thresholds, unique values, etc.
    """
    df = load_bookings_csv(csv_path)
    slots_df = aggregate_to_slots(df)

    # Compute congestion thresholds
    low_thresh, high_thresh = compute_congestion_thresholds(
        slots_df["booking_count"]
    )

    # Add congestion label
    slots_df["congestion_level"] = slots_df["booking_count"].apply(
        lambda bc: classify_congestion(bc, low_thresh, high_thresh)
    )

    # Estimated wait time
    slots_df["estimated_wait_minutes"] = slots_df["booking_count"].apply(
        lambda bc: estimate_wait_minutes(bc, slot_capacity=10)
    )

    # Collect unique categorical values for encoding at prediction time
    metadata = {
        "low_threshold": low_thresh,
        "high_threshold": high_thresh,
        "unique_centres": sorted(slots_df["centre_id"].unique().tolist()),
        "unique_crops": sorted(df["crop"].unique().tolist()),
        "unique_seasons": sorted(slots_df["season"].unique().tolist()),
        "max_booking_count": int(slots_df["booking_count"].max()),
        "total_training_rows": len(slots_df),
        "total_bookings": len(df),
    }

    return slots_df, metadata


if __name__ == "__main__":
    slots_df, meta = prepare_training_data()
    print(f"Training rows: {meta['total_training_rows']}")
    print(f"Total bookings: {meta['total_bookings']}")
    print(f"Thresholds: LOW<={meta['low_threshold']}, MODERATE<={meta['high_threshold']}, HIGH>{meta['high_threshold']}")
    print(f"Congestion distribution:")
    print(slots_df["congestion_level"].value_counts().to_string())
    print(f"\nBooking count stats:")
    print(slots_df["booking_count"].describe().to_string())
