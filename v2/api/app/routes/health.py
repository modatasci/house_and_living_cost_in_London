from fastapi import APIRouter

from app.config import settings
from app.services.postcode import get_postcode_service

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict:
    pc = get_postcode_service()
    return {
        "status": "ok",
        "postcodes_loaded": len(pc.df),
        "has_coords_index": pc.has_coords(),
        "tfl_key_configured": bool(settings.tfl_app_key),
    }
