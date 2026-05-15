from fastapi import APIRouter

from app.services.living_cost import get_living_cost_service

router = APIRouter(prefix="/boroughs", tags=["boroughs"])


@router.get("")
def list_boroughs() -> list[dict]:
    """Return all London boroughs with their codes (from council tax CSV)."""
    df = get_living_cost_service().council_tax[["Code", "Local authority"]]
    return [{"code": r["Code"], "name": r["Local authority"]} for _, r in df.iterrows()]
