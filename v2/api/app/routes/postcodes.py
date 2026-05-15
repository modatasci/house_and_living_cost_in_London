from fastapi import APIRouter, HTTPException, Query

from app.schemas import PostcodeHit
from app.services.postcode import get_postcode_service

router = APIRouter(prefix="/postcodes", tags=["postcodes"])


@router.get("/search", response_model=list[PostcodeHit])
def search(q: str = Query(..., min_length=1, max_length=8), limit: int = 10) -> list[PostcodeHit]:
    return [PostcodeHit(**hit) for hit in get_postcode_service().search(q, limit=limit)]


@router.get("/lookup", response_model=PostcodeHit)
def lookup(postcode: str) -> PostcodeHit:
    hit = get_postcode_service().lookup(postcode)
    if not hit:
        raise HTTPException(404, f"Postcode {postcode!r} not found in London")
    return PostcodeHit(**hit)


@router.get("/nearest", response_model=PostcodeHit)
def nearest(lat: float, lng: float) -> PostcodeHit:
    pc = get_postcode_service()
    if not pc.has_coords():
        raise HTTPException(
            503,
            "Postcode coordinate index not built. Run scripts/build_postcode_index.py first.",
        )
    hit = pc.nearest(lat, lng)
    if not hit:
        raise HTTPException(404, "No postcode near that point")
    return PostcodeHit(**hit)
