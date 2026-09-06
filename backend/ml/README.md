# ML-Based Procurement Queue / Congestion Prediction

## Problem

Farmers visiting procurement centres often face unexpected long waiting times because they don't know which time slot is likely to be crowded. This leads to:

- Wasted time waiting in long queues
- Missed work hours
- Frustration and poor experience
- Inefficient crowd distribution across time slots

## Solution

Use historical booking and queue data to predict slot congestion levels and estimated waiting times. This helps farmers choose the best time slot before arriving at the centre.

## How It Works

### Data Pipeline

```
Historical Bookings (CSV/Database)
        ↓
Feature Engineering
  - Centre ID
  - Day of week
  - Hour of day
  - Month / Season
  - Crop type
  - Average quantity
        ↓
Aggregate by (centre, date, hour)
        ↓
Classify congestion level:
  - LOW: booking_count <= threshold_low
  - MODERATE: threshold_low < booking_count <= threshold_high
  - HIGH: booking_count > threshold_high
        ↓
Train/Test Split (80/20, stratified)
        ↓
RandomForestClassifier Training
        ↓
Model Evaluation
        ↓
Save Model (joblib)
```

### Features Used

| Feature | Type | Description |
|---------|------|-------------|
| centre_id | Categorical | Procurement centre identifier |
| hour | Numeric | Time slot hour (9, 10, 11, 14, 15, 16) |
| day_of_week | Numeric | Day of week (0=Mon, 6=Sun) |
| month | Numeric | Month of year |
| dominant_crop | Categorical | Most common crop in the slot |
| season | Categorical | Agricultural season (Kharif/Rabi/Zaid) |
| avg_quantity | Numeric | Average quantity per booking |

### Model

- **Algorithm**: RandomForestClassifier (100 trees, max_depth=10)
- **Why**: Simple, explainable, handles mixed feature types well, no deep learning needed
- **Class weights**: Balanced to handle class imbalance in training data
- **Reproducibility**: Fixed random_state=42

### Prediction Output

```json
{
  "centre_id": "PPC001",
  "slot_date": "2026-09-01",
  "slot_hour": 9,
  "congestion_level": "LOW",
  "predicted_wait_minutes": 6,
  "current_bookings": 1,
  "slot_capacity": 10,
  "confidence": 0.95,
  "confidence_available": true,
  "model_available": true,
  "message": null
}
```

### Congestion Levels

| Level | Meaning | Color |
|-------|---------|-------|
| 🟢 LOW | Few bookings, short wait expected | Green |
| 🟡 MODERATE | Some bookings, moderate wait | Yellow |
| 🔴 HIGH | Many bookings, long wait expected | Red |

## API Endpoints

### GET /api/ml/slot-prediction

Predict congestion for a specific slot.

**Parameters:**
- `centre_id` (required): Procurement centre UUID
- `slot_date` (required): Date in YYYY-MM-DD format
- `slot_hour` (required): Hour (0-23)
- `crop` (optional): Crop type
- `slot_capacity` (optional): Maximum farmers
- `current_bookings` (optional): Current booking count

### GET /api/ml/model-info

Return metadata about the trained model.

## Usage

### Training the Model

```bash
cd backend
python -m ml.train
```

This will:
1. Load historical bookings from `data/bookings_queue.csv`
2. Engineer features and compute congestion thresholds
3. Train a RandomForestClassifier
4. Evaluate on test set (20% split)
5. Save model to `backend/ml/model/queue_congestion_model.joblib`
6. Save metadata to `backend/ml/model/model_metadata.json`

### Making Predictions

```python
from ml.predict import predict_congestion

result = predict_congestion(
    centre_id="PPC001",
    slot_date="2026-09-01",
    slot_hour=9,
    crop="Maize",
    slot_capacity=10,
    current_bookings=2,
)
print(result["congestion_level"])  # LOW, MODERATE, or HIGH
print(result["predicted_wait_minutes"])  # Estimated wait in minutes
```

## Fallback Behavior

If the ML model is unavailable or prediction fails:

1. The API returns a graceful fallback response
2. The frontend shows "AI prediction temporarily unavailable."
3. Booking count and slot capacity are still displayed
4. **ML failure NEVER blocks booking**

## Data Limitation

⚠️ **Important**: The current ML model is a prototype trained on project/demo historical data. Prediction quality will improve when real procurement and queue history becomes available.

The training data consists of:
- 500 synthetic booking records
- 50 procurement centres
- 5 crop types
- 7 time slots per day

Real production data will provide:
- More diverse booking patterns
- Actual queue wait times
- Seasonal variations
- Centre-specific demand patterns

## Files

```
backend/ml/
├── __init__.py              # Package init
├── data_preparation.py      # Data loading and feature engineering
├── train.py                 # Model training script
├── predict.py               # Prediction module (loaded by API)
├── model/
│   ├── queue_congestion_model.joblib   # Trained model
│   └── model_metadata.json             # Model metadata and thresholds
└── README.md                # This file
```

## Dependencies

Added to `requirements.txt`:
```
pandas>=2.0.0,<3
numpy>=1.24.0,<2
scikit-learn>=1.3.0,<2
joblib>=1.3.0,<2
```

## Evaluation Metrics

From the trained model:

| Metric | Value |
|--------|-------|
| Accuracy | ~95% |
| Precision (weighted) | ~95% |
| Recall (weighted) | ~95% |
| F1 Score (weighted) | ~95% |

Note: High accuracy is expected because most slots in demo data have low congestion. The model's real value emerges with production data showing more diverse patterns.
