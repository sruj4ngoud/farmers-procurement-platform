"""MSP (Minimum Support Price) API endpoint."""

from fastapi import APIRouter

from app.config.msp import get_all_msp, get_msp

router = APIRouter(prefix="/api", tags=["msp"])


@router.get("/msp")
def list_msp():
    """Get all MSP data."""
    return get_all_msp()


@router.get("/msp/{crop_name}")
def get_crop_msp(crop_name: str):
    """Get MSP for a specific crop."""
    msp = get_msp(crop_name)
    if msp is None:
        return {"crop": crop_name, "msp": None, "message": "MSP not available for this crop"}
    return {"crop": crop_name, "msp": msp, "unit": "INR per quintal"}
