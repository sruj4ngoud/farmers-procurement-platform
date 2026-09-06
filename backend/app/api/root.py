"""Root and health check endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["root"])


@router.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Farmer Procurement Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@router.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "farmer-procurement-api"}
