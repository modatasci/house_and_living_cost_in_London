from fastapi import APIRouter

from app.schemas import CompareRequest, CompareResponse
from app.services.compare import run_compare

router = APIRouter(tags=["compare"])


@router.post("/compare", response_model=CompareResponse)
async def compare(req: CompareRequest) -> CompareResponse:
    return await run_compare(req)
